#!/usr/bin/env python3
"""Corgi Híradó – napi hírgyűjtő.

Összegyűjti az elmúlt napok corgis híreit több hírforrásból (Google News,
Bing News, több nyelven), kiszűri az ismétlődéseket, lefordítja magyarra,
és elmenti:
  data/latest.json          – a mai lapszám
  data/YYYY-MM-DD.json      – archív lapszám
  data/index.json           – az archív lapszámok listája
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/Budapest")
UA = "Mozilla/5.0 (CorgiHirado; +https://github.com)"
MAX_AGE_HOURS = int(os.environ.get("MAX_AGE_HOURS", "48"))
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "40"))
ARCHIVE_DAYS = 60

QUERIES = ["corgi", '"Welsh Corgi"', "Pembroke corgi", "Cardigan corgi"]

GOOGLE_EDITIONS = [
    ("en-US", "US", "US:en"),
    ("en-GB", "GB", "GB:en"),
    ("hu", "HU", "HU:hu"),
    ("de", "DE", "DE:de"),
    ("fr", "FR", "FR:fr"),
    ("es", "ES", "ES:es"),
    ("it", "IT", "IT:it"),
    ("ja", "JP", "JP:ja"),
]

# Szavak, amelyek nem kutyás corgira utalnak (játékmárka, kriptopénz stb.)
EXCLUDE = re.compile(
    r"\b(corgi (toys?|diecast|die-cast|model cars?)|corgicoin|corgi ai|\$corgi|corgi token)\b",
    re.I,
)

CATEGORIES = [
    ("Királyi corgik", r"royal|queen|king|király|királynő|elizabeth|erzsébet|charles|károly"),
    ("Mentés és örökbefogadás", r"rescue|adopt|shelter|örökbe|menhely|mentett|lost|missing|found|eltűnt"),
    ("Egészség", r"health|vet|surgery|disease|állatorvos|betegség|egészség|műtét"),
    ("Események", r"festival|race|parade|meetup|beach day|corgi con|verseny|fesztivál|találkozó|show"),
    ("Hírességek és internet", r"viral|tiktok|instagram|famous|celebrity|video|internet|influencer|híres"),
]


def clean(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        d = parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def get(url: str) -> str | None:
    for attempt in range(3):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(1.5 * (attempt + 1))
    print(f"  ! nem sikerült: {url}", file=sys.stderr)
    return None


def parse_rss(xml_text: str, source_kind: str, lang: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for it in root.iter("item"):
        title = clean(it.findtext("title"))
        link = (it.findtext("link") or "").strip()
        desc = clean(it.findtext("description"))
        pub = parse_date(it.findtext("pubDate"))
        source = ""
        image = ""
        for child in it:
            tag = child.tag.split("}")[-1].lower()
            if tag == "source":
                source = clean(child.text)
            elif tag == "image" and child.text:
                image = child.text.strip()
            elif tag in ("content", "thumbnail") and child.get("url"):
                image = image or child.get("url")
        if source_kind == "google":
            # A Google News cím végén " - Forrás" szerepel
            if not source and " - " in title:
                source = title.rsplit(" - ", 1)[1]
            if source and title.endswith(" - " + source):
                title = title[: -len(" - " + source)]
            # A Google leírása csak a cím ismétlése – eldobjuk
            if desc.startswith(title[:30]):
                desc = ""
        if source_kind == "bing":
            q = parse_qs(urlparse(link).query)
            if "url" in q:
                link = q["url"][0]
            if not source:
                src = it.find("{*}Source")
                if src is not None:
                    source = clean(src.text)
            if image and image.startswith("/"):
                image = "https://www.bing.com" + image
        if not title or not link:
            continue
        items.append(
            {
                "title": title,
                "summary": desc,
                "link": link,
                "source": source or urlparse(link).netloc.replace("www.", ""),
                "published": pub.isoformat() if pub else None,
                "image": image,
                "lang": lang,
            }
        )
    return items


def collect() -> list[dict]:
    all_items: list[dict] = []
    for q in QUERIES:
        for hl, gl, ceid in GOOGLE_EDITIONS:
            url = (
                f"https://news.google.com/rss/search?q={quote_plus(q + ' when:2d')}"
                f"&hl={hl}&gl={gl}&ceid={ceid}"
            )
            xml_text = get(url)
            if xml_text:
                got = parse_rss(xml_text, "google", hl.split("-")[0])
                print(f"  Google {hl:6} {q!r}: {len(got)}")
                all_items += got
        for mkt in ("en-US", "en-GB", "hu-HU", "de-DE"):
            url = f"https://www.bing.com/news/search?q={quote_plus(q)}&format=rss&mkt={mkt}"
            xml_text = get(url)
            if xml_text:
                got = parse_rss(xml_text, "bing", mkt.split("-")[0])
                print(f"  Bing   {mkt:6} {q!r}: {len(got)}")
                all_items += got
    return all_items


def norm_key(title: str) -> str:
    t = re.sub(r"[^\w\s]", "", title.lower())
    words = [w for w in t.split() if len(w) > 2]
    return " ".join(words[:8])


def is_relevant(item: dict) -> bool:
    text = f"{item['title']} {item['summary']}"
    if "corgi" not in text.lower():
        return False
    return not EXCLUDE.search(text)


def filter_and_dedupe(items: list[dict], now: datetime) -> list[dict]:
    cutoff = now - timedelta(hours=MAX_AGE_HOURS)
    seen: dict[str, dict] = {}
    for it in items:
        if not is_relevant(it):
            continue
        if it["published"]:
            if datetime.fromisoformat(it["published"]) < cutoff:
                continue
        key = norm_key(it["title"])
        if not key:
            continue
        prev = seen.get(key)
        # A gazdagabb (leírással / képpel rendelkező) változatot tartjuk meg
        if prev is None or (len(it["summary"]) + bool(it["image"]) * 50) > (
            len(prev["summary"]) + bool(prev["image"]) * 50
        ):
            seen[key] = it
    out = list(seen.values())
    out.sort(key=lambda x: x["published"] or "", reverse=True)
    return out[:MAX_ITEMS]


class Translator:
    def __init__(self) -> None:
        self.cache: dict[str, str] = {}
        try:
            from deep_translator import GoogleTranslator

            self.gt = GoogleTranslator(source="auto", target="hu")
        except Exception as e:  # pragma: no cover
            print(f"  ! fordító nem elérhető: {e}", file=sys.stderr)
            self.gt = None

    def __call__(self, text: str, lang: str) -> str:
        if not text or lang == "hu" or self.gt is None:
            return text
        if text in self.cache:
            return self.cache[text]
        for attempt in range(3):
            try:
                res = self.gt.translate(text[:4500]) or text
                self.cache[text] = res
                time.sleep(0.3)
                return res
            except Exception:
                time.sleep(2 * (attempt + 1))
        return text


def categorize(item: dict) -> str:
    text = f"{item['title']} {item['summary']} {item.get('title_hu','')}"
    for name, pattern in CATEGORIES:
        if re.search(pattern, text, re.I):
            return name
    return "Corgi hírek"


def write_edition(items: list[dict], now_local: datetime) -> None:
    DATA.mkdir(exist_ok=True)
    day = now_local.strftime("%Y-%m-%d")
    edition = {
        "date": day,
        "generated_at": now_local.isoformat(timespec="minutes"),
        "count": len(items),
        "articles": items,
    }
    payload = json.dumps(edition, ensure_ascii=False, indent=1)
    (DATA / f"{day}.json").write_text(payload, encoding="utf-8")
    (DATA / "latest.json").write_text(payload, encoding="utf-8")

    # Régi lapszámok takarítása + index
    files = sorted(p.stem for p in DATA.glob("????-??-??.json"))
    limit = (now_local - timedelta(days=ARCHIVE_DAYS)).strftime("%Y-%m-%d")
    for stem in files:
        if stem < limit:
            (DATA / f"{stem}.json").unlink()
    files = sorted((p.stem for p in DATA.glob("????-??-??.json")), reverse=True)
    (DATA / "index.json").write_text(json.dumps({"editions": files}), encoding="utf-8")


def main() -> int:
    now = datetime.now(timezone.utc)
    now_local = now.astimezone(TZ)
    print(f"Corgi Híradó – {now_local:%Y-%m-%d %H:%M} (Budapest)")
    raw = collect()
    print(f"Összesen {len(raw)} nyers találat")
    items = filter_and_dedupe(raw, now)
    if len(items) < 5:
        # Csendes napokon szélesebb időablak
        global MAX_AGE_HOURS
        MAX_AGE_HOURS = 24 * 7
        items = filter_and_dedupe(raw, now)
    print(f"{len(items)} egyedi, releváns cikk")

    tr = Translator()
    for it in items:
        it["title_hu"] = tr(it["title"], it["lang"])
        it["summary_hu"] = tr(it["summary"], it["lang"]) if it["summary"] else ""
        it["category"] = categorize(it)

    write_edition(items, now_local)
    print("Kész.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

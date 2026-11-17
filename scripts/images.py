"""Napi 3 cuki corgis kép (Wikimedia Commons, szabad licenc) a kirakóshoz."""
from __future__ import annotations

import io
import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image, ImageOps

from fetch_news import DATA, clean

IMG_DIR = DATA / "img"
USED = DATA / "img_used.json"
UA = {"User-Agent": "CorgiHirado/1.0 (https://github.com/poovicsgyorgy/corgi-hirado; daily corgi puzzle)"}
GRIDS = [4, 6, 12]
SEARCHES = [
    'deepcat:"Welsh Corgi" filetype:bitmap',
    'deepcat:"Pembroke Welsh Corgi" filetype:bitmap',
    'deepcat:"Cardigan Welsh Corgi" filetype:bitmap',
    'deepcat:"Welsh Corgi" puppy filetype:bitmap',
]
CUTE = re.compile(r"pupp|kölyök|cute|smil|happy|tongue|playing|snow|sleep|face|portrait|head|sitting|beach|grass", re.I)
BAD = re.compile(r"drone|sculpture|bronze|light show|lantern|festival of|parade float|costume|mascot|plush|cake|cookie|tribune|times|newspaper|article|clipping|gazette|herald|journal|magazine|scan|^File:HK |walking with carts|stroller|R12S|statue|szobor|logo|map|drawing|illustration|stamp|coin|toy|diecast|car\b|skeleton|skull|svg", re.I)


BREAD_SEARCHES = [
    'deepcat:"Loaves of bread" filetype:bitmap', 'deepcat:"Brioche" filetype:bitmap', 'deepcat:"Bread rolls" filetype:bitmap',
    "sourdough loaf filetype:bitmap", "challah filetype:bitmap", "brioche filetype:bitmap",
]
BREAD_OK = re.compile(r"bread|loaf|loaves|brioche|bun\b|buns|roll|sourdough|challah|cipó|kenyér|pain|brot|pão|pan de", re.I)
BREAD_BAD = re.compile(r"ancient|egypt|museum|archae|fossil|carboni|pompeii|antique|tomb|\bBC\b|bce|excavat|exhibit|"
                       r"still|life|painting|stilleven|nature morte|museum|rijks|oil|canvas|plate|wine|glass|olive|shrimp|rooster|"
                       r"lemon|cheese|café|cafe|restaurant|menu|breakfast|dinner|lunch|meal|soup|butter|jam|egg|bacon|burger|hot dog|"
                       r"cover|stitch|embroider|knot|panel|cloth|textile|towel|basket only|sandwich|toast|slice|sliced|tree|fruit|map|logo|svg|drawing|advert|poster|shop|store|bakery interior|people|\bman\b|\bwoman\b", re.I)


def _commons_candidates(searches=None, must="corgi", bad=None, ok=None) -> list[dict]:
    searches = searches or SEARCHES
    bad = bad or BAD
    out = []
    for q in random.sample(searches, len(searches)):
        try:
            r = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query", "format": "json", "generator": "search",
                    "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 50,
                    "gsroffset": random.choice([0, 50, 100, 150, 200, 250]),
                    "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1400,
                },
                headers=UA, timeout=30,
            )
            pages = r.json().get("query", {}).get("pages", {})
        except Exception as e:
            print(f"  ! Commons: {e}", file=sys.stderr)
            continue
        for p in pages.values():
            ii = (p.get("imageinfo") or [{}])[0]
            title = p.get("title", "")
            if ii.get("mime") not in ("image/jpeg", "image/png") or bad.search(title):
                continue
            if (must and must not in title.lower()) or (ok and not ok.search(title)) or (ok and len(title) > 70):
                continue
            if min(ii.get("width", 0), ii.get("height", 0)) < 700:
                continue
            meta = ii.get("extmetadata", {})
            out.append({
                "id": title,
                "url": ii.get("thumburl") or ii.get("url"),
                "page": ii.get("descriptionurl", ""),
                "author": clean(meta.get("Artist", {}).get("value", ""))[:80] or "ismeretlen",
                "license": clean(meta.get("LicenseShortName", {}).get("value", "")) or "lásd a forrást",
            })
        if len(out) > 40:
            break
    return out


def _dogceo_candidates() -> list[dict]:
    out = []
    for breed in ("pembroke", "corgi/cardigan"):
        try:
            for u in requests.get(f"https://dog.ceo/api/breed/{breed}/images/random/5", timeout=20).json()["message"]:
                out.append({"id": u, "url": u, "page": "https://dog.ceo", "author": "Dog CEO / Stanford Dogs", "license": "kutatási adatbázis"})
        except Exception as e:
            print(f"  ! dog.ceo: {e}", file=sys.stderr)
    return out


def _save(cand: dict, path: Path, size: int = 1080) -> bool:
    try:
        r = requests.get(cand["url"], headers=UA, timeout=40)
        r.raise_for_status()
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(r.content))).convert("RGB")
        if min(im.size) < 350:
            return False
        # színtelen (fekete-fehér, szépia) képek kiszűrése
        sat = im.resize((64, 64)).convert("HSV").split()[1]
        if sum(sat.getdata()) / 4096 < 28:
            return False
        im = ImageOps.fit(im, (size, size), Image.LANCZOS, centering=(0.5, 0.45))
        im.save(path, "JPEG", quality=84, optimize=True, progressive=True)
        return True
    except Exception as e:
        print(f"  ! kép letöltés: {e}", file=sys.stderr)
        return False


def build_images(day: str) -> list[dict]:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        used = set(json.loads(USED.read_text()))
    except Exception:
        used = set()
    cands = [c for c in _commons_candidates() if c["id"] not in used]
    random.shuffle(cands)
    cands.sort(key=lambda c: 0 if CUTE.search(c["id"]) else 1)  # cuki címek előre
    cands += _dogceo_candidates()
    result = []
    for c in cands:
        if len(result) == 3:
            break
        n = len(result) + 1
        path = IMG_DIR / f"{day}-{n}.jpg"
        if _save(c, path):
            used.add(c["id"])
            result.append({
                "file": f"data/img/{path.name}", "grid": GRIDS[n - 1],
                "author": c["author"], "license": c["license"], "page": c["page"],
            })
    USED.write_text(json.dumps(sorted(used)), encoding="utf-8")
    print(f"  képek: {len(result)} db")
    return result


def build_bread(day: str) -> list[dict]:
    """Corgi vagy kenyér? – 3 corgi + 3 kenyér fotó."""
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        used = set(json.loads(USED.read_text()))
    except Exception:
        used = set()
    corgis = [c for c in _commons_candidates() if c["id"] not in used]
    random.shuffle(corgis)
    breads = [c for c in _commons_candidates(BREAD_SEARCHES, must=None, bad=BREAD_BAD, ok=BREAD_OK) if c["id"] not in used]
    random.shuffle(breads)
    out = []
    for kind, pool in (("corgi", corgis), ("kenyer", breads)):
        n = 0
        for c in pool:
            if n == 3:
                break
            path = IMG_DIR / f"{day}-{kind}{n + 1}.jpg"
            if _save(c, path, 720):
                used.add(c["id"])
                n += 1
                out.append({"file": f"data/img/{path.name}", "corgi": kind == "corgi",
                            "author": c["author"], "license": c["license"], "page": c["page"],
                            "zx": random.randint(35, 65), "zy": random.randint(40, 70)})
    USED.write_text(json.dumps(sorted(used)), encoding="utf-8")
    random.shuffle(out)
    print(f"  corgi vagy kenyér: {sum(o['corgi'] for o in out)} corgi + {sum(not o['corgi'] for o in out)} kenyér")
    return out


def prune_images(keep_after: str) -> None:
    for p in IMG_DIR.glob("*.jpg"):
        if p.name[:10] < keep_after:
            p.unlink()


if __name__ == "__main__":
    print(build_images(datetime.now().strftime("%Y-%m-%d")))

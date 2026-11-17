"""„Igaz vagy kamu?” – napi 3 hír: 2 valódi (1990-től), 1 kitalált."""
from __future__ import annotations

import json
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

from fetch_news import DATA, Translator, get, is_relevant, norm_key, parse_rss
from llm import ask_json

HERE = Path(__file__).resolve().parent
POOL = DATA / "quiz_pool.json"
USED = DATA / "quiz_used.json"

ARCHIVE_QUERIES = [
    ("corgi", "hl=hu&gl=HU&ceid=HU:hu", "hu"),
    ("corgik", "hl=hu&gl=HU&ceid=HU:hu", "hu"),
    ("corgi kutya", "hl=hu&gl=HU&ceid=HU:hu", "hu"),
    ("corgi", "hl=en-US&gl=US&ceid=US:en", "en"),
    ("corgis", "hl=en-GB&gl=GB&ceid=GB:en", "en"),
    ('"Welsh corgi"', "hl=en-US&gl=US&ceid=US:en", "en"),
    ("royal corgi", "hl=en-GB&gl=GB&ceid=GB:en", "en"),
    ("corgi rescue", "hl=en-US&gl=US&ceid=US:en", "en"),
    ("corgi race", "hl=en-US&gl=US&ceid=US:en", "en"),
]
HU_PLACES = re.compile(
    r"budapest|magyar|hazai|itthon|debrecen|szeged|pécs|győr|miskolc|balaton|kecskemét|"
    r"székesfehérvár|nyíregyháza|szombathely|eger|veszprém|sopron|kerület",
    re.I,
)
HU_MONTHS = ["január", "február", "március", "április", "május", "június", "július",
             "augusztus", "szeptember", "október", "november", "december"]


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def refresh_pool(now: datetime) -> list[dict]:
    """Az archív hírkészlet bővítése a Google News teljes (időkorlát nélküli) kereséséből."""
    pool: dict[str, dict] = {p["key"]: p for p in _load(POOL, [])}
    fresh: list[dict] = []
    for q, ed, lang in ARCHIVE_QUERIES:
        xml = get(f"https://news.google.com/rss/search?q={quote_plus(q)}&{ed}")
        if not xml:
            continue
        for it in parse_rss(xml, "google", lang):
            if not it["published"] or not is_relevant(it):
                continue
            key = norm_key(it["title"])
            if key and key not in pool:
                it["key"] = key
                pool[key] = it
                fresh.append(it)
    print(f"  archív készlet: {len(pool)} hír ({len(fresh)} új)")
    if fresh:
        classify(fresh)
    POOL.write_text(json.dumps(list(pool.values()), ensure_ascii=False, indent=0), encoding="utf-8")
    return list(pool.values())


def classify(items: list[dict]) -> None:
    """Relevancia, helyszín és magyar cím – lehetőleg MI-vel, különben szabályokkal."""
    tr = Translator()
    for start in range(0, len(items), 40):
        batch = items[start:start + 40]
        listing = "\n".join(f"{i}. [{b['lang']}] {b['title']} ({b['source']})" for i, b in enumerate(batch))
        res = ask_json(
            "Hírszerkesztő vagy. Csak érvényes JSON-t válaszolsz.",
            "Az alábbi hírcímek mindegyikéről döntsd el:\n"
            "- relevant: igaz, ha a hír corgi KUTYÁRÓL (vagy corgikról) szól; hamis, ha cégről, "
            "játékautóról, ETF-ről, termékről, hirdetésről, horoszkópról, vagy a corgi csak mellékes.\n"
            "- region: \"Magyarország\", ha az esemény Magyarországon történt, különben \"Világ\".\n"
            "- title_hu: természetes, újságcím stílusú magyar fordítás (a forrás neve nélkül).\n"
            'Válasz: [{"i":0,"relevant":true,"region":"Világ","title_hu":"..."}, ...]\n\n' + listing,
            temperature=0.2,
        )
        done = set()
        if isinstance(res, list):
            for r in res:
                try:
                    b = batch[int(r["i"])]
                    b["relevant"] = bool(r.get("relevant"))
                    b["region"] = "Magyarország" if r.get("region") == "Magyarország" else "Világ"
                    b["title_hu"] = (r.get("title_hu") or "").strip() or b["title"]
                    done.add(int(r["i"]))
                except Exception:
                    pass
        for i, b in enumerate(batch):
            if i in done:
                continue
            b["relevant"] = True
            b["title_hu"] = tr(b["title"], b["lang"])
            b["region"] = "Magyarország" if b["lang"] == "hu" and HU_PLACES.search(b["title"]) else "Világ"


def _ym(it: dict) -> str:
    return it["date"] if "date" in it else it["published"][:7]


def pick_real(pool: list[dict], now: datetime) -> list[dict]:
    seed = json.loads((HERE / "seed_pool.json").read_text(encoding="utf-8"))
    for s in seed:
        s["key"] = "seed:" + norm_key(s["title_hu"])
    recent = (now - timedelta(days=10)).isoformat()
    cands = seed + [p for p in pool if p.get("relevant") and p.get("title_hu") and p["published"] < recent]
    used = set(_load(USED, []))
    avail = [c for c in cands if c["key"] not in used]
    if len(avail) < 4:  # minden elfogyott: elölről kezdjük
        used, avail = set(), cands

    hu = [c for c in avail if c.get("region") == "Magyarország"]
    world = [c for c in avail if c.get("region") != "Magyarország"]
    random.shuffle(hu)
    # Régebbi hírek kicsit nagyobb eséllyel, hogy több évtized jöjjön elő
    world.sort(key=lambda c: random.random() * (1 + (int(_ym(c)[:4]) - 1990) / 20))
    chosen = []
    if hu and random.random() < 0.6:
        chosen.append(hu[0])
    for c in world + hu[1:]:
        if len(chosen) == 2:
            break
        if c not in chosen and (not chosen or _ym(c)[:4] != _ym(chosen[0])[:4]):
            chosen.append(c)
    for c in chosen:
        used.add(c["key"])
    USED.write_text(json.dumps(sorted(used), ensure_ascii=False), encoding="utf-8")
    return [
        {
            "date": _ym(c),
            "region": c.get("region", "Világ"),
            "title_hu": c["title_hu"],
            "title_orig": c.get("title", "") if c.get("lang") not in (None, "hu") else "",
            "summary_hu": c.get("summary_hu", ""),
            "source": c.get("source", ""),
            "link": c.get("link", ""),
            "fake": False,
        }
        for c in chosen
    ]


FAKE_TEMPLATES = [
    ("{town} polgármestere díszpolgári címet adományozott egy {name} nevű corginak",
     "A kutya a helyiek szerint hetente többször is elkísérte a postást a körútján. Az átadón külön, alacsony pulpitust építettek neki.",
     "Ilyen díszpolgári cím nem létezik; a történetet mi találtuk ki."),
    ("Corgiknak tervezett, rámpás lépcsőt építettek a {town}i könyvtárba",
     "Az ötlet egy olvasótábor után született, ahol a gyerekek kutyáknak olvastak fel. A rámpa a tervek szerint más kistestű kutyáknak is segít.",
     "Ez a beruházás sosem valósult meg – kamu hír."),
    ("Egy {name} nevű corgi hónapokon át minden reggel ugyanannál a pékségnél várta a nyitást",
     "A pék végül kis táblát tett ki „Törzsvendég” felirattal. A kutya gazdája szerint a corgi a vajas kifli illatát követte.",
     "Kedves, de kitalált történet."),
    ("Corgi-futóversenyt rendeztek a {town}i ügetőpályán, a győztes {name} lett",
     "A rövid távon húsz kutya indult, a célba érést sokan a lelátóról szurkolták végig. Több kutya félúton inkább a nézőkhöz szaladt simogatásért.",
     "Ilyen verseny ezen a helyen nem volt – kamu."),
    ("Egy {name} nevű corgi hívta fel a figyelmet a tűzre egy {town}i társasházban",
     "A kutya addig ugatott az ajtónál, amíg a szomszédok ki nem jöttek. A tűzoltók szerint a gyors jelzés megakadályozta a nagyobb kárt.",
     "Ezt a hőstettet mi találtuk ki."),
]
TOWNS_HU = ["Kecskemét", "Szentendre", "Eger", "Veszprém", "Sopron", "Gödöllő", "Tata", "Szekszárd"]
TOWNS_WORLD = ["Cardiff", "Bristol", "Kiotó", "Melbourne", "Portland", "Bergen", "Gent", "Salzburg"]
NAMES_HU = ["Bogyó", "Mázli", "Pötty", "Kekszi", "Mogyi", "Sajtos", "Pamacs", "Morzsi"]
NAMES_WORLD = ["Biscuit", "Pickles", "Mochi", "Waffles", "Nugget", "Toast", "Pudding", "Bramble"]


def make_fake(real: list[dict], now: datetime) -> dict:
    year = random.randint(1990, now.year)
    month = random.randint(1, 12 if year < now.year else now.month)
    date = f"{year}-{month:02d}"
    region = "Magyarország" if random.random() < 0.4 else "Világ"
    examples = "\n".join(f"- {r['title_hu']}" for r in real)
    res = ask_json(
        "Egy magyar kutyás hírlap játékrovatának szerkesztője vagy. Csak érvényes JSON-t válaszolsz.",
        "Írj EGY kitalált, de hihető corgis hírt a „Igaz vagy kamu?” játékhoz.\n"
        f"- Időpont: {year}. {HU_MONTHS[month - 1]}. Helyszín: {'Magyarország (konkrét település)' if region == 'Magyarország' else 'külföld (konkrét város)'}.\n"
        "- Legyen hétköznapi, kedves vagy meglepő, de ne abszurd; illeszkedjen a korszakhoz.\n"
        "- TILOS valós, létező személyt (pl. uralkodót, hírességet, politikust) vagy valódi szervezetet/céget/médiumot megnevezni; "
        "kitalált kutyanevek és keresztnevek rendben vannak.\n"
        "- Ne legyen benne tragédia, bűncselekmény vagy egészségügyi tanács.\n"
        "- A cím stílusa és hossza hasonlítson ezekhez a valódi címekhez:\n"
        f"{examples}\n\n"
        'Válasz: {"title_hu":"...","summary_hu":"2 rövid mondat","explanation":"1 mondat: mi árulhatta el, hogy kamu"}',
    )
    if isinstance(res, dict) and res.get("title_hu") and res.get("summary_hu"):
        return {"date": date, "region": region, "title_hu": res["title_hu"].strip(),
                "summary_hu": res["summary_hu"].strip(),
                "explanation": (res.get("explanation") or "Ezt a hírt mi találtuk ki.").strip(),
                "source": "", "link": "", "title_orig": "", "fake": True}
    t, s, e = random.choice(FAKE_TEMPLATES)
    town = random.choice(TOWNS_HU if region == "Magyarország" else TOWNS_WORLD)
    name = random.choice(NAMES_HU if region == "Magyarország" else NAMES_WORLD)
    return {"date": date, "region": region, "title_hu": t.format(town=town, name=name),
            "summary_hu": s, "explanation": e, "source": "", "link": "", "title_orig": "", "fake": True}


def build_quiz(now: datetime) -> list[dict]:
    pool = refresh_pool(now)
    real = pick_real(pool, now)
    fake = make_fake(real, now)
    items = real + [fake]
    random.shuffle(items)
    for i, it in enumerate(items):
        it["id"] = i
    print(f"  kvíz: {[('KAMU ' if i['fake'] else '') + i['date'] + ' ' + i['title_hu'][:50] for i in items]}")
    return items


if __name__ == "__main__":
    print(json.dumps(build_quiz(datetime.now(timezone.utc)), ensure_ascii=False, indent=1))

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
JUNK = re.compile(
    r"worth \$|billion|million|milliárd|valuation|unicorn|insurance|biztosít|startup|"
    r"\(tv movie|tv-film| - photos|^preview|pictures$|képgaléria|everything you need to know|"
    r"how smart|breed (guide|profile|information)|fajtaleírás|missense|variant|\bNDS\b|"
    r"coupon|kupon|for sale|eladó|horoszkóp|horoscope|recipe|recept|review:|teszt:",
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
            if not it["published"] or not is_relevant(it) or JUNK.search(it["title"]):
                continue
            key = norm_key(it["title"])
            if key and key not in pool:
                it["key"] = key
                pool[key] = it
                fresh.append(it)
    for k in [k for k, v in pool.items() if JUNK.search(v["title"])]:
        del pool[k]
    print(f"  archív készlet: {len(pool)} hír ({len(fresh)} új)")
    pending = [v for v in pool.values() if v.get("cls") != "ai"]
    if pending:
        classify(pending)
        print(f"  MI-vel besorolva: {sum(1 for v in pool.values() if v.get('cls') == 'ai')}/{len(pool)}")
    POOL.write_text(json.dumps(list(pool.values()), ensure_ascii=False, indent=0), encoding="utf-8")
    return list(pool.values())


def classify(items: list[dict], limit: int = 240) -> None:
    """Relevancia és helyszín MI-vel (ha elérhető), magyar cím fordítóval."""
    tr = Translator()
    todo = [b for b in items if b.get("cls") != "ai"][:limit]
    for start in range(0, len(todo), 60):
        batch = todo[start:start + 60]
        listing = "\n".join(f"{i}. {b['title']} ({b['source']})" for i, b in enumerate(batch))
        res = ask_json(
            "You are a careful news editor. Reply with valid JSON only.",
            "For each headline decide:\n"
            "- r (relevant): 1 if the story is genuinely ABOUT a corgi dog / corgi dogs (an event, a dog, "
            "royal corgis, races, rescues, viral corgi moments). 0 if it is about a company, toy cars, ETF, "
            "a product, an ad, a breed guide, a TV listing, a scientific paper, or corgis are only incidental.\n"
            "- h: 1 if the event happened in Hungary, else 0.\n"
            'Answer: [{"i":0,"r":1,"h":0}, ...]\n\n' + listing,
            temperature=0.1,
            providers=("github", "pollinations"),
        )
        if isinstance(res, list):
            for r in res:
                try:
                    b = batch[int(r["i"])]
                    b["relevant"] = bool(int(r.get("r", 1)))
                    b["region"] = "Magyarország" if int(r.get("h", 0)) else "Világ"
                    b["cls"] = "ai"
                except Exception:
                    pass
    for b in items:
        if "relevant" not in b:
            b["relevant"] = True
        if "region" not in b:
            b["region"] = "Magyarország" if b["lang"] == "hu" and HU_PLACES.search(b["title"]) else "Világ"
        if not b.get("title_hu"):
            b["title_hu"] = tr(b["title"], b["lang"])


def _ym(it: dict) -> str:
    return it["date"] if "date" in it else it["published"][:7]


def pick_real(pool: list[dict], now: datetime) -> list[dict]:
    seed = json.loads((HERE / "seed_pool.json").read_text(encoding="utf-8"))
    for s in seed:
        s["key"] = "seed:" + norm_key(s["title_hu"])
    recent = (now - timedelta(days=10)).isoformat()
    dyn = [p for p in pool if p.get("relevant") and p.get("title_hu") and p["published"] < recent]
    if sum(1 for p in dyn if p.get("cls") == "ai") >= 20:
        dyn = [p for p in dyn if p.get("cls") == "ai"]
    cands = seed + dyn
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


# (név, helyhatározó, melléknév)
TOWNS_HU = [("Kecskemét", "Kecskeméten", "kecskeméti"), ("Szentendre", "Szentendrén", "szentendrei"),
            ("Eger", "Egerben", "egri"), ("Veszprém", "Veszprémben", "veszprémi"), ("Sopron", "Sopronban", "soproni"),
            ("Gödöllő", "Gödöllőn", "gödöllői"), ("Tata", "Tatán", "tatai"), ("Szekszárd", "Szekszárdon", "szekszárdi"),
            ("Pécs", "Pécsen", "pécsi"), ("Debrecen", "Debrecenben", "debreceni"), ("Győr", "Győrben", "győri"),
            ("Szeged", "Szegeden", "szegedi"), ("Zalaegerszeg", "Zalaegerszegen", "zalaegerszegi"),
            ("Vác", "Vácon", "váci"), ("Keszthely", "Keszthelyen", "keszthelyi"), ("Budaörs", "Budaörsön", "budaörsi")]
TOWNS_WORLD = [("Cardiff", "Cardiffban", "cardiffi"), ("Bristol", "Bristolban", "bristoli"), ("Kiotó", "Kiotóban", "kiotói"),
               ("Melbourne", "Melbourne-ben", "melbourne-i"), ("Portland", "Portlandben", "portlandi"),
               ("Bergen", "Bergenben", "bergeni"), ("Gent", "Gentben", "genti"), ("Salzburg", "Salzburgban", "salzburgi"),
               ("Krakkó", "Krakkóban", "krakkói"), ("Tallinn", "Tallinnban", "tallinni"), ("Lyon", "Lyonban", "lyoni"),
               ("Denver", "Denverben", "denveri"), ("Vancouver", "Vancouverben", "vancouveri"), ("Swansea", "Swansea-ben", "swansea-i")]
NAMES_HU = ["Bogyó", "Mázli", "Pötty", "Kekszi", "Mogyi", "Sajtos", "Pamacs", "Morzsi", "Bendegúz", "Zsemle", "Fahéj", "Brumi"]
NAMES_WORLD = ["Biscuit", "Pickles", "Mochi", "Waffles", "Nugget", "Toast", "Pudding", "Bramble", "Teddy", "Maple", "Hazel", "Otis"]

# cím, összefoglaló, árulkodó jel – {loc} helyhatározó, {adj} melléknév, {name} kutyanév, {n} szám
FAKE_TEMPLATES = [
    ("Corgi-sétát rendeztek {loc}: {n} kutya vonult végig a főtéren",
     "A szervezők eredetileg húsz-harminc résztvevőre számítottak. A menet végén a kutyák közös fotón pózoltak a városháza előtt.",
     "Ilyen felvonulásról egyetlen helyi lap sem írt – kamu."),
    ("Egy {name} nevű corgi minden reggel elkíséri a postást a körútján {loc}",
     "A kutya a gazdája szerint pontosan tudja, melyik házba érkezik levél. A postás bevallotta: ha a corgi nem jön, hiányzik neki.",
     "Kedves, de kitalált történet."),
    ("Corgis falinaptárral gyűjtöttek pénzt egy {adj} állatmenhelynek – {n0} példány fogyott el",
     "A fotókat önkéntes gazdik corgijairól készítették. A bevételből a menhely új kennelajtókat vásárolt.",
     "A naptár sosem létezett – ez volt a kamu."),
    ("Egy {name} nevű corgi lett {a} {adj} vasútállomás nem hivatalos kabalája",
     "A kutya a pénztáros gazdájával jár be minden nap. Az utasok már név szerint köszöntik.",
     "Kitalált kabala, ilyen hírt nem közöltek."),
    ("Ötven corgi pózolt egyszerre egy csoportképhez {loc} – új helyi rekord",
     "A fotóst a legnagyobb kihívás az jelentette, hogy minden kutya egyszerre nézzen a gépbe. Tizenhét próbálkozásba került.",
     "Ilyen rekordkísérlet nem volt – kamu."),
    ("Tizenegy kölyök született egyetlen alomban egy {adj} corgitenyésztőnél",
     "A corgiknál az átlagos alom hat-hét kölyökből áll. Az anyakutya és a kicsik egészségesek.",
     "Ez a rekordalom kitaláció volt."),
    ("Egy {name} nevű corgi találta meg egy turista elveszett jegygyűrűjét {a} {adj} parkban",
     "A gyűrű egy pad melletti fűben lapult. A pár hálából egy zacskó jutalomfalatot küldött a kutyának.",
     "Szép történet, de mi találtuk ki."),
    ("Hóban ugráló corgiról készült kép nyerte {a} {adj} amatőr fotópályázatot",
     "A zsűri szerint a kép tökéletesen elkapta a pillanatot, amikor a kutya mind a négy lába a levegőben van. A díjazott fotót a könyvtárban állították ki.",
     "Ilyen fotópályázati eredmény nem született – kamu."),
    ("Corgi-úszóversenyt rendeztek egy {adj} strandon a szezon utolsó napján",
     "A rövid lábú versenyzők többsége mentőmellényben indult. A győztes egy {name} nevű kutya lett.",
     "Ez a verseny sosem volt."),
    ("Egy {name} nevű corgi segít {a} {adj} kórház gyermekosztályán a kis betegek felvidításában",
     "A terápiás kutya hetente kétszer látogat el az osztályra. Az ápolók szerint a gyerekek már napokkal előre várják.",
     "Ilyen terápiás corgiról nem szóltak a hírek – kitaláció."),
    ("Corgis futamot tartottak {a} {adj} lóversenypályán a szünetben – {name} nyert",
     "A nézők a lovak helyett a corgiknak szurkoltak a legjobban. Több kutya félúton inkább a közönséghez szaladt.",
     "Ezen a pályán nem volt corgi-futam – kamu."),
    ("Egy {name} nevű corgi lett {a} {adj} tűzoltóság kabalája",
     "A kutya kis egyenruhát is kapott a nyílt napra. A tűzoltók szerint a gyerekek miatta jönnek el a bemutatókra.",
     "Kitalált kabalatörténet."),
    ("Corgi-szobrot avattak {loc} egy helyi kutyabarát egyesület kezdeményezésére",
     "A bronzszobor egy padon ülő corgit ábrázol. Az alkotás az orra simogatásától fényesedik.",
     "Ez a szobor nem létezik – kamu."),
    ("Három napig kereste gazdáját egy corgi, végül {a} {adj} buszpályaudvaron találtak rá",
     "A kutyát egy sofőr ismerte fel a közösségi oldalon terjedő képről. A gazda és kedvence a pályaudvar irodájában találkozott újra.",
     "Megható, de kitalált történet."),
    ("Kertészetben „dolgozik” egy corgi {loc}: ő köszönti a vásárlókat",
     "A {name} nevű kutya reggelente végigjárja a palántasorokat. A törzsvásárlók külön jutalomfalatot hoznak neki.",
     "Ilyen kertészeti corgiról nem írtak."),
    ("Corgi-találkozót tartottak {loc}: a legtávolabbi résztvevő 400 kilométert utazott",
     "Az eseményen jelmezversenyt és ügyességi pályát is rendeztek. A szervezők jövőre még nagyobb helyszínt keresnek.",
     "Ez a találkozó kitaláció volt."),
    ("Egy {name} nevű corgi {a} {adj} könyvtár „olvasókutyája” lett",
     "A program során a gyerekek hangosan olvasnak fel a kutyának. A könyvtárosok szerint így bátrabban olvasnak.",
     "Ilyen könyvtári programról nem jelent meg hír."),
    ("{A} {adj} kisvasút egy napra corgis jegyet vezetett be",
     "A különleges napon a kutyák ingyen utazhattak, a gazdik kedvezményt kaptak. A szerelvényeket corgis zászlók díszítették.",
     "Ilyen corgis jegy sosem volt – kamu."),
    ("Egy {name} nevű corgi minden nap ugyanannál a pékségnél várja a nyitást {loc}",
     "A pék végül kis táblát tett ki „Törzsvendég” felirattal. A kutya gazdája szerint a corgi a friss kifli illatát követi.",
     "Kedves, de kitalált történet."),
    ("Iskolai csoportképen tűnt fel egy corgi {loc} – a diákok ragaszkodtak hozzá",
     "A kutya az egyik tanár kedvence, aki gyakran beviszi az órákra. A fotó végül az iskola évkönyvének borítójára került.",
     "Ez a kép csak a mi fantáziánkban létezik."),
]


def make_fake(real: list[dict], now: datetime) -> dict:
    year = random.randint(1992, now.year)
    month = random.randint(1, 12 if year < now.year else now.month)
    date = f"{year}-{month:02d}"
    region = "Magyarország" if random.random() < 0.45 else "Világ"
    town = random.choice(TOWNS_HU if region == "Magyarország" else TOWNS_WORLD)
    name = random.choice(NAMES_HU if region == "Magyarország" else NAMES_WORLD)
    # Ha a GitHub jó minőségű MI-modellje elérhető, az ír egyedi kamut
    examples = "\n".join(f"- {r['title_hu']}" for r in real)
    res = ask_json(
        "Egy magyar kutyás hírlap játékrovatának szerkesztője vagy. Csak érvényes JSON-t válaszolsz.",
        "Írj EGY kitalált, de hihető corgis hírt az „Igaz vagy kamu?” játékhoz, kifogástalan magyarsággal.\n"
        f"- Időpont: {year}. {HU_MONTHS[month - 1]}. Helyszín: {town[0]}.\n"
        "- Hétköznapi, kedves vagy meglepő, de ne abszurd; illeszkedjen a korszakhoz.\n"
        "- TILOS valós, létező személyt vagy valódi szervezetet, céget, médiumot megnevezni.\n"
        "- Ne legyen benne tragédia, bűncselekmény vagy egészségügyi tanács.\n"
        f"- A cím stílusa hasonlítson ezekhez:\n{examples}\n\n"
        'Válasz: {"title_hu":"...","summary_hu":"2 rövid mondat","explanation":"1 mondat"}',
        providers=("github",),
    )
    if isinstance(res, dict) and res.get("title_hu") and res.get("summary_hu"):
        t, sm, ex = res["title_hu"], res["summary_hu"], res.get("explanation") or "Ezt a hírt mi találtuk ki."
    else:
        recent = _load(DATA / "fake_used.json", [])[-12:]
        choices = [i for i in range(len(FAKE_TEMPLATES)) if i not in recent] or list(range(len(FAKE_TEMPLATES)))
        k = random.choice(choices)
        (DATA / "fake_used.json").write_text(json.dumps((recent + [k])[-12:]))
        art = "az" if town[2][0].lower() in "aáeéiíoóöőuúüű" else "a"
        fill = dict(loc=town[1], adj=town[2], a=art, A=art.capitalize(), name=name, n=random.choice([34, 41, 47, 52, 58, 63, 72]),
                    n0=random.choice([300, 450, 600, 800, 1200]))
        t, sm, ex = (x.format(**fill) for x in FAKE_TEMPLATES[k])
    return {"date": date, "region": region, "title_hu": t.strip(), "summary_hu": sm.strip(),
            "explanation": ex.strip(), "source": "", "link": "", "title_orig": "", "fake": True}


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

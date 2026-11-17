"""Napi vicces corgi-horoszkóp mind a 12 csillagjegynek."""
from __future__ import annotations

import random

SIGNS = [
    ("Kos", "♈", "márc. 21. – ápr. 19.", [
        "A Kos-corgi ma fejjel megy a falnak – pontosabban a kanapépárnának.",
        "A Kos-corgi energiája ma a csúcson van: a postás már előre fél.",
        "Ma a Kos-corgi úgy érzi, ő vezeti a falkát. A falka te vagy."]),
    ("Bika", "♉", "ápr. 20. – máj. 20.", [
        "A Bika-corgi ma a kényelem nagykövete: kanapé, takaró, ismétlés.",
        "A Bika-corgi ma rendíthetetlen – különösen, ha a vacsoráról van szó.",
        "A Bika-corgi ma nem siet. Soha nem siet. Kivéve, ha zörög a zacskó."]),
    ("Ikrek", "♊", "máj. 21. – jún. 20.", [
        "Az Ikrek-corgi ma két dolgot akar egyszerre: aludni és játszani.",
        "Az Ikrek-corgi ma beszédes kedvében van – minden mókusról lesz véleménye.",
        "Az Ikrek-corgi ma kétszer olyan kíváncsi, mint máskor. Ez sok."]),
    ("Rák", "♋", "jún. 21. – júl. 22.", [
        "A Rák-corgi ma nagyon érzékeny: egy leejtett sajtdarab is könnyeket csalhat a szemébe (az örömtől).",
        "A Rák-corgi ma fészket rak a frissen mosott ruhákból.",
        "A Rák-corgi ma ragaszkodóbb a szokásosnál – a fürdőszobába is elkísér."]),
    ("Oroszlán", "♌", "júl. 23. – aug. 22.", [
        "Az Oroszlán-corgi ma tudja, hogy ő a környék legszebbje. Igaza van.",
        "Az Oroszlán-corgi ma tapsot vár minden egyes „ül” után.",
        "Az Oroszlán-corgi királyi hangulatban ébred – a párnája ma trón."]),
    ("Szűz", "♍", "aug. 23. – szept. 22.", [
        "A Szűz-corgi ma rendet rak: minden játékát a te ágyadba hordja.",
        "A Szűz-corgi ma alaposan ellenőrzi a tál tisztaságát. Nyalással.",
        "A Szűz-corgi ma precíz: pontosan 17:59-kor jelzi, hogy 18:00-kor vacsora van."]),
    ("Mérleg", "♎", "szept. 23. – okt. 22.", [
        "A Mérleg-corgi ma a béke követe: a macskával is megosztaná a helyét (majdnem).",
        "A Mérleg-corgi ma nem tud dönteni: labda vagy kötél? Mindkettő.",
        "A Mérleg-corgi ma mindenkinek egyformán osztja a puszit."]),
    ("Skorpió", "♏", "okt. 23. – nov. 21.", [
        "A Skorpió-corgi ma titokzatos: elásott valamit, és nem árulja el, mit.",
        "A Skorpió-corgi ma átható tekintettel figyel – főleg, amikor eszel.",
        "A Skorpió-corgi ma rejtélyes hangulatban van. A fél pár zokni eltűnése nem véletlen."]),
    ("Nyilas", "♐", "nov. 22. – dec. 21.", [
        "A Nyilas-corgi ma kalandra vágyik: minden bokor mögött új világ vár.",
        "A Nyilas-corgi ma felfedező kedvében van – a szomszéd kertje is a térkép része.",
        "A Nyilas-corgi ma optimista: biztos benne, hogy egy sétából három lesz."]),
    ("Bak", "♑", "dec. 22. – jan. 19.", [
        "A Bak-corgi ma komoly és szorgalmas: a terelést nagyon komolyan veszi.",
        "A Bak-corgi ma minden családtagot összeterel a nappaliba.",
        "A Bak-corgi ma céltudatos. A cél: a hűtő."]),
    ("Vízöntő", "♒", "jan. 20. – febr. 18.", [
        "A Vízöntő-corgi ma eredeti: új alvópózt talál ki, fejjel lefelé, mancsokkal az ég felé.",
        "A Vízöntő-corgi ma kreatív: a vizestál neki medence.",
        "A Vízöntő-corgi ma a saját feje után megy. Mint mindig, csak most stílusosabban."]),
    ("Halak", "♓", "febr. 19. – márc. 20.", [
        "A Halak-corgi ma álmodozó: a mancsai álmában is futnak.",
        "A Halak-corgi ma együttérző: ha szomorú vagy, rád fekszik mind a tizenkét kilójával.",
        "A Halak-corgi ma romantikus hangulatban van – a kedvenc plüssét is mindenhová viszi."]),
]

PREDICTIONS = [
    "Egy váratlan mókus felbukkanása ma mindent megváltoztat.",
    "A csillagok szerint ma zörögni fog egy zacskó. Lehet, hogy csak bevásárlószatyor, de a remény hal meg utoljára.",
    "Ma valaki megkérdezi tőle: „Ki a jó kutya?” A válasz meglepő lesz: ő.",
    "Délután rövid, de heves zoomie-roham várható a nappaliban.",
    "A Hold állása kedvez a pocakvakarásnak – legalább tíz percig.",
    "Ma egy régi ismerős tér vissza az életébe: a kanapé alá gurult labda.",
    "Vigyázat: a porszívó ma is előbújhat a szekrényből.",
    "A Vénusz ma a kekszes doboz felé fordul.",
    "Ma minden csöngetésre úgy reagál, mintha királyi látogató érkezne.",
    "Egy idegen ma megsimogatja, és örök barátság születik. Legalább öt percre.",
    "A Jupiter szerencsét hoz: valami ma leesik az asztalról.",
    "Ma a tükörképével is barátságot köt.",
    "A nap folyamán legalább egyszer hangosan sóhajt, milyen nehéz az élet. Közben a legpuhább takarón fekszik.",
    "Ma ismét rájön, hogy a farkát nem éri el. Nem adja fel.",
    "Ma a cipőid különösen érdekesek lesznek számára. Tedd őket magasra.",
    "A csillagok szerint ma elkapja azt a legyet. Vagy legalábbis nagyon közel kerül hozzá.",
    "Az esti órákban hízelgési offenzíva várható a vacsora környékén.",
    "Ma minden lehulló falevél személyes kihívás lesz.",
    "Egy új szag nyomába ered, és a nap végére megfejti a környék összes rejtélyét.",
    "Ma kiderül, hogy a rövid láb nem akadály: a kanapéra is feljut. Egy kis segítséggel.",
    "Rövid szundi, hosszú szundi, majd egy közepes szundi – a csillagok szerint ez lesz a nap ritmusa.",
    "Ma bátran megugatja a postást. Utána farokcsóválással kér bocsánatot – vagyis popsiriszálással, mert farokból nem sok jutott.",
    "A Mars energiát ad: ma kétszer annyit ugrál, mint tegnap.",
    "Ma a kedvenc plüssét alaposan átvizsgálja, és elfogadhatatlannak találja a tölteléket.",
    "Váratlan pusziesőre számíthatsz.",
    "Ma a lépcső lesz a legnagyobb ellenfele, de diadalt arat.",
    "Valaki ma azt mondja rá: „Olyan, mint egy kenyér!” Ő ezt bóknak veszi. Jogosan.",
    "Ma nagyon sokat néz majd rád a nagy, barna szemeivel. Ennek nem lehet ellenállni.",
    "Egy pocsolya ma hívogatóbb lesz bármi másnál.",
    "A nap meglepetése: valaki hazahoz egy új játékot. Vagy csak egy kartondobozt. Az is ugyanolyan jó.",
    "Ma megtanul egy új trükköt. Valószínűleg azt, hogyan kell kinyitni a kamraajtót.",
    "Ma a szél felborzolja a bundáját. Ettől csak még cukibb lesz.",
    "Kedvező nap a barátkozásra: a szomszéd kutyával ma végre megbeszélik a kerítés-ügyet.",
    "Ma minden fotón tökéletesen mutat – kivéve, ha éppen pislog.",
    "A Szaturnusz figyelmeztet: a kanapé díszpárnái ma veszélyben vannak.",
    "Ma a sétán minden fát alaposan megszagol. Ez az ő reggeli hírolvasása.",
    "Délután leheveredik egy napfoltba, és addig nem mozdul, amíg a nap tovább nem vándorol.",
    "Ma úgy tesz, mintha nem hallaná a nevét. A „sajt” szót viszont a ház másik végéből is meghallja.",
    "A csillagok szerint ma kinézi magának a te helyedet a kanapén. És meg is kapja.",
    "Ma egész popsiriszálva jön üdvözölni – ez lesz a nap legjobb pillanata.",
    "Ma titkos küldetésen vesz részt: megtalálni a konyha utolsó morzsáját.",
    "Ma minden „séta” szóra felugrik – akkor is, ha csak betűzöd.",
    "Egy rejtélyes hang ma a fülét is felállítja – mindkettőt, egyszerre, teljes magasságban.",
    "Ma a rövid lábai hosszabbnak tűnnek. Csak a csillagállás miatt.",
    "Ma különösen fontos lesz neki, hogy pontosan a lábad előtt feküdjön, ahol a legjobban útban van.",
    "Egy kedves idegen ma megdicséri a fenekét. Büszke lesz rá egész nap.",
    "Ma a vizestál mellől is átfogó elemzést végez a lakás helyzetéről.",
    "Ma a fürdetésről szóló pletykák szerencsére alaptalannak bizonyulnak.",
]

TREATS = ["sajtkocka", "sárgarépa", "almaszelet (mag nélkül)", "főtt csirkefalat", "uborkakarika", "banánkarika",
          "egy szem áfonya", "rágócsont", "görögdinnye-kocka (mag nélkül)", "főtt tojásdarabka", "sütőtökkocka",
          "zöldbabszál", "jutalomfalat-morzsa", "főtt pulykafalat", "brokkolirózsa (egy kicsi)"]
ACTIVITIES = ["pocakvakarás", "labdakergetés", "szimatséta", "bújócska a takaró alatt", "kötélhúzás", "fülvakargatás",
              "délutáni szundi", "pacsi-gyakorlás", "zoomie a kertben", "ablakon kinézés", "kincskeresés jutalomfalattal",
              "terelés (lehetőleg nem a szomszéd gyerekeit)", "napozás", "plüssmentés"]
TIPS = [
    "Ma kérj tőle dupla adag puszit – bőkezű napja van.",
    "Tartsd kéznél a labdát, ma bármikor szükség lehet rá.",
    "A zoknikat ma tedd biztonságos magasságba.",
    "Fotózd le ma – különösen fotogén napja van.",
    "Egy extra sétakör ma csodákra képes.",
    "Ha sajtot eszel, ne az orra előtt tedd – vagy készülj az osztozkodásra.",
    "Dicsérd meg a füleit. Tudja, hogy szépek, de jólesik hallani.",
    "A fürdetést halaszd holnapra. Ma a csillagok ellene vannak.",
    "Rejts el egy jutalomfalatot – ma kiváló szimatoló napja van.",
    "Ma hagyd, hogy ő válassza a séta útvonalát.",
    "Ma egy ölelés többet ér bármilyen jutalomfalatnál. Majdnem.",
    "Vigyázz a vacsorádra: ma különösen meggyőző a tekintete.",
    "Nézzetek ki együtt az ablakon egy kicsit. Fontos megbeszélnivalótok van.",
    "Ma tanítsd meg egy új trükkre – fogékony napja van.",
    "Legyen ma egy kis plusz játékidő. Megérdemli. Mindig megérdemli.",
]
RATING_KEYS = ["Falánkság", "Sétakedv", "Csínytevés", "Bújós kedv"]


def build_horoscope(day: str) -> list[dict]:
    rng = random.Random("horoszkop-" + day)
    preds = rng.sample(PREDICTIONS, len(SIGNS))
    tips = [rng.choice(TIPS) for _ in SIGNS]
    out = []
    for i, (name, sym, dates, intros) in enumerate(SIGNS):
        out.append({
            "sign": name, "symbol": sym, "dates": dates,
            "text": f"{rng.choice(intros)} {preds[i]}",
            "treat": rng.choice(TREATS),
            "activity": rng.choice(ACTIVITIES),
            "tip": tips[i],
            # a falánkság sosem lehet 3-nál kevesebb – elvégre corgiról van szó
            "ratings": {k: rng.randint(3 if k == "Falánkság" else 1, 5) for k in RATING_KEYS},
        })
    return out


if __name__ == "__main__":
    import json, datetime
    print(json.dumps(build_horoscope(datetime.date.today().isoformat())[:2], ensure_ascii=False, indent=1))

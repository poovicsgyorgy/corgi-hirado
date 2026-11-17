/* Corgi Híradó – játékok, napi rovatok és a „Corgim” fül */
(function () {
"use strict";

/* ---------- Segédfüggvények ---------- */
function hash(s) { let h = 2166136261; for (const c of String(s)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
function rng(seed) { let a = hash(seed); return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const pick = (r, a) => a[Math.floor(r() * a.length)];
function shuffle(r, a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
const el = (id) => document.getElementById(id);
const prof = () => store.get("profile", {});
const dogName = () => (prof().name || "").trim();
let EDN = null; // az aktuálisan látott lapszám

/* ---------- IndexedDB (fotók, napló) ---------- */
const idb = (() => {
  let dbp;
  const open = () => dbp || (dbp = new Promise((res, rej) => {
    const r = indexedDB.open("corgi-hirado", 1);
    r.onupgradeneeded = () => { r.result.createObjectStore("kv"); r.result.createObjectStore("diary", { keyPath: "id", autoIncrement: true }); };
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  }));
  const tx = async (store, mode, fn) => { const db = await open(); return new Promise((res, rej) => {
    const t = db.transaction(store, mode), s = t.objectStore(store), out = fn(s);
    t.oncomplete = () => res(out && out.result !== undefined ? out.result : out); t.onerror = () => rej(t.error); }); };
  return {
    get: (k) => tx("kv", "readonly", s => s.get(k)),
    set: (k, v) => tx("kv", "readwrite", s => s.put(v, k)),
    del: (k) => tx("kv", "readwrite", s => s.delete(k)),
    all: () => tx("diary", "readonly", s => s.getAll()),
    add: (v) => tx("diary", "readwrite", s => s.add(v)),
    rm: (id) => tx("diary", "readwrite", s => s.delete(id)),
  };
})();

function resizeImage(file, max) {
  return new Promise((res, rej) => {
    const img = new Image(), url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, max / Math.max(img.width, img.height));
      const c = document.createElement("canvas"); c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
      c.toBlob(b => b ? res(b) : rej(new Error("kép")), "image/jpeg", 0.82);
    };
    img.onerror = () => { URL.revokeObjectURL(url); rej(new Error("kép")); };
    img.src = url;
  });
}

function confetti(n = 90) {
  const box = el("confetti"), cols = ["#d9772b", "#f0b429", "#c0392b", "#2f6b3a", "#5bb7d6", "#eba39b"];
  for (let i = 0; i < n; i++) {
    const c = document.createElement("i");
    c.style.left = Math.random() * 100 + "vw"; c.style.background = cols[i % cols.length];
    c.style.animationDuration = 2 + Math.random() * 2.5 + "s"; c.style.animationDelay = Math.random() * .8 + "s";
    box.appendChild(c); setTimeout(() => c.remove(), 5500);
  }
}

/* ---------- Fülek ---------- */
function showTab(t, scroll) {
  document.querySelectorAll(".tab").forEach(x => x.hidden = x.dataset.tab !== t);
  document.querySelectorAll("#tabbar button").forEach(b => b.classList.toggle("on", b.dataset.go === t));
  store.set("tab", t);
  if (scroll !== false) window.scrollTo({ top: 0 });
}
document.querySelectorAll("#tabbar button").forEach(b => b.addEventListener("click", () => showTab(b.dataset.go)));
showTab(store.get("tab", "ma"), false);

/* ---------- Corgi-arcok (tamagocsi, mini) ---------- */
function corgiFace(mood, withBody) {
  const O = "#d9772b", W = "#fffaf0", D = "#2a1d14", P = "#eba39b";
  const sulky = mood === "sulky", sleep = mood === "sleep", happy = mood === "happy";
  const earL = sulky ? "rotate(-14 60 60)" : "", earR = sulky ? "rotate(14 140 60)" : "";
  let g = "";
  if (withBody) g += `<ellipse cx="100" cy="182" rx="56" ry="46" fill="${O}"/><ellipse cx="100" cy="176" rx="28" ry="36" fill="${W}"/>
    <ellipse cx="80" cy="224" rx="14" ry="8" fill="${W}"/><ellipse cx="120" cy="224" rx="14" ry="8" fill="${W}"/>`;
  g += `<g transform="${earL}"><polygon points="52,74 38,10 94,50" fill="${O}"/><polygon points="58,66 48,26 84,52" fill="${P}"/></g>
    <g transform="${earR}"><polygon points="148,74 162,10 106,50" fill="${O}"/><polygon points="142,66 152,26 116,52" fill="${P}"/></g>
    <ellipse cx="100" cy="92" rx="62" ry="54" fill="${O}"/><path d="M100 46 L86 100 L114 100 Z" fill="${W}"/>
    <ellipse cx="100" cy="118" rx="38" ry="29" fill="${W}"/>
    <ellipse cx="70" cy="110" rx="10" ry="6" fill="#f08a6a" opacity="${happy ? .7 : .4}"/><ellipse cx="130" cy="110" rx="10" ry="6" fill="#f08a6a" opacity="${happy ? .7 : .4}"/>
    <ellipse cx="100" cy="108" rx="9" ry="7" fill="${D}"/>`;
  if (happy) g += `<path d="M70 90 q8 -10 16 0 M114 90 q8 -10 16 0" stroke="${D}" stroke-width="4.5" fill="none" stroke-linecap="round"/>
      <path d="M84 118 q16 22 32 0 Z" fill="${D}"/><path d="M93 126 q7 12 14 0" fill="#e86a6a"/>`;
  else if (sleep) g += `<path d="M70 92 q8 6 16 0 M114 92 q8 6 16 0" stroke="${D}" stroke-width="4" fill="none" stroke-linecap="round"/>
      <path d="M94 124 q6 4 12 0" stroke="${D}" stroke-width="3" fill="none" stroke-linecap="round"/>
      <text x="150" y="40" font-family="sans-serif" font-weight="700" font-size="22" fill="#5b6fb0">z</text><text x="168" y="22" font-family="sans-serif" font-weight="700" font-size="16" fill="#5b6fb0">z</text>`;
  else if (sulky) g += `<circle cx="78" cy="94" r="6.5" fill="${D}"/><circle cx="122" cy="94" r="6.5" fill="${D}"/>
      <path d="M66 82 L88 88 M134 82 L112 88" stroke="${D}" stroke-width="4" stroke-linecap="round"/>
      <path d="M88 130 q12 -10 24 0" stroke="${D}" stroke-width="3.5" fill="none" stroke-linecap="round"/>`;
  else g += `<circle cx="78" cy="92" r="7" fill="${D}"/><circle cx="122" cy="92" r="7" fill="${D}"/><circle cx="80" cy="89" r="2.4" fill="#fff"/><circle cx="124" cy="89" r="2.4" fill="#fff"/>
      <path d="M100 115 q-5 10 -14 6 M100 115 q5 10 14 6" stroke="${D}" stroke-width="3" fill="none" stroke-linecap="round"/>`;
  return `<svg viewBox="0 ${withBody ? "0 200 236" : "4 200 150"}" xmlns="http://www.w3.org/2000/svg"><g class="m-${mood}">${g}</g></svg>`;
}

/* ---------- Profil ---------- */
const SIGN_ENDS = [[120, "Bak"], [219, "Vízöntő"], [320, "Halak"], [420, "Kos"], [521, "Bika"], [621, "Ikrek"], [723, "Rák"],
  [823, "Oroszlán"], [923, "Szűz"], [1023, "Mérleg"], [1122, "Skorpió"], [1222, "Nyilas"], [1232, "Bak"]];
function signOf(iso) { if (!iso) return null; const md = +iso.slice(5, 7) * 100 + +iso.slice(8, 10); return SIGN_ENDS.find(([e]) => md < e)[1]; }
function ageText(iso) {
  if (!iso) return ""; const b = new Date(iso + "T12:00:00"), n = new Date();
  let m = (n.getFullYear() - b.getFullYear()) * 12 + n.getMonth() - b.getMonth(); if (n.getDate() < b.getDate()) m--;
  if (m < 0) return ""; const y = Math.floor(m / 12), mm = m % 12;
  return y ? `${y} éves${mm ? `, ${mm} hónapos` : ""}` : `${mm} hónapos`;
}
const isBirthday = () => { const b = prof().bday; return b && b.slice(5) === today().slice(5); };

async function renderProfile() {
  const p = prof(), box = el("profile");
  let photoUrl = "";
  try { const blob = await idb.get("photo"); if (blob) photoUrl = URL.createObjectURL(blob); } catch (e) {}
  const sign = signOf(p.bday);
  box.innerHTML = `<div class="card prof">
    <label class="ph" style="${photoUrl ? `background-image:url('${photoUrl}')` : ""}" title="Fotó">${photoUrl ? "" : "🐕"}
      <input id="pfphoto" type="file" accept="image/*" hidden></label>
    <div>
      ${p.name ? `<h3>${esc(p.name)}</h3><div class="small">${esc([ageText(p.bday), sign ? `csillagjegye: ${sign}` : "", p.sex || ""].filter(Boolean).join(" · "))}</div>`
               : `<div class="small">Add meg a corgitok adatait, és az egész app róla fog szólni! A fotóhoz koppints a körre.</div>`}
      <label for="pfname">Név</label><input id="pfname" value="${esc(p.name || "")}" placeholder="pl. Bogyó" maxlength="30">
      <label for="pfbday">Születésnap</label><input id="pfbday" type="date" value="${esc(p.bday || "")}">
      <label for="pfsex">Ő egy…</label><select id="pfsex">${["", "fiú", "lány"].map(x => `<option ${p.sex === x ? "selected" : ""} value="${x}">${x || "—"}</option>`).join("")}</select>
      <div class="row" style="margin-top:10px"><button class="btn" id="pfsave">Mentés</button><span class="small" id="pfmsg"></span></div>
    </div></div>`;
  el("pfsave").onclick = () => {
    const np = { name: el("pfname").value.trim(), bday: el("pfbday").value, sex: el("pfsex").value };
    store.set("profile", np);
    const s = signOf(np.bday); if (s) store.set("sign", s);
    el("pfmsg").textContent = "Elmentve! 🐾";
    personalize(); renderProfile(); if (EDN) renderHoroscope(EDN);
    if (isBirthday()) confetti();
  };
  el("pfphoto").onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    try { await idb.set("photo", await resizeImage(f, 480)); renderProfile(); personalize(); } catch (err) { el("pfmsg").textContent = "A fotót nem sikerült betölteni."; }
  };
}
window.FUN = { profileSign: () => signOf(prof().bday), onEdition };

function personalize() {
  const n = dogName(), h = new Date().getHours();
  const hello = h < 5 ? "Jó éjt" : h < 10 ? "Jó reggelt" : h < 18 ? "Szép napot" : h < 22 ? "Szép estét" : "Jó éjt";
  let g = n ? `${hello}, ${esc(n)} és gazdái! 🐾` : "";
  if (isBirthday()) {
    g = `<div class="bday">🎂 Boldog születésnapot, ${esc(n || "corgi")}! 🎉 Ma ${esc(ageText(prof().bday)) || "ünnep"} – dupla jutalomfalat jár!</div>`;
    if (store.get("bdayconf", "") !== today()) { store.set("bdayconf", today()); setTimeout(() => confetti(140), 400); }
  }
  el("greet").innerHTML = g;
  el("wxtitle").textContent = n ? `Mit vegyen fel ma ${n}?` : "Mit vegyen fel ma a corgi?";
  el("tamatitle").textContent = n ? `${n} – a tamagocsi` : "Corgi-tamagocsi";
  el("diarytitle").textContent = n ? `${n} naplója` : "Corgi-napló";
}

/* ---------- Napi rovatok ---------- */
const SAYINGS = [
  "Aki korán kel, előbb kap reggelit. Aki corgi, az kétszer.",
  "Nem a láb hossza számít, hanem a szív mérete. És a popsi bolyhossága.",
  "Ki mint veti ágyát, úgy fekszik benne. A corgi a te ágyadat veti.",
  "Lassan járj, tovább érsz – kivéve, ha mókust látsz.",
  "Minden zacskó zörgése egy új remény kezdete.",
  "Jobb ma egy keksz, mint holnap egy ígéret.",
  "A legjobb dolgok az asztal alá esnek.",
  "Kutyából nem lesz szalonna – de szalonnából lehet kutyajutalom.",
  "Aki másnak vermet ás, az valószínűleg corgi, és csontot keres.",
  "Ahol sajt van, ott corgi is van. Ahol corgi van, ott hamarosan nincs sajt.",
  "Egy simogatás nem simogatás. Kettő már kezdetnek jó.",
  "Rövid láb, hosszú séta, végtelen boldogság.",
  "Amit ma megehetsz, ne halaszd holnapra.",
  "A kanapé nem bútor, hanem életérzés.",
  "A türelem rózsát terem. A szép nézés kekszet.",
  "Nem az a corgi, aki sosem esik el, hanem aki felkel, és megrázza a fülét.",
  "Két dolog biztos az életben: a vacsora és az, hogy előtte még egyszer kérni kell.",
  "Ha az élet citromot ad, szagold meg, aztán hagyd ott. Nem kaja.",
  "Minden út a hűtőhöz vezet.",
  "Az álom a legjobb szundi előszobája.",
  "Aki szeret, az megosztja a pizzája szélét.",
  "A boldogság egy meleg napfolt a nappali padlóján.",
  "Ne ugass hiába – csak ha jön a postás. Akkor viszont nagyon.",
  "A pocak nem vakarja meg magát.",
  "Ma terelek, holnap pihenek, holnapután megint terelek.",
  "A fürdés csak egy rossz álom. Gyorsan rázd le magadról.",
  "Ha elveszíted az utat, kövesd a sajtszagot.",
  "A puszi gyógyít. A keksz is.",
  "Nem az számít, hányszor esel le a kanapéról, hanem hogy hányszor mászol vissza.",
  "Aki corgit tart, sosem lesz egyedül – a fürdőszobában sem.",
];
const FACTS = [
  "A „corgi” szót a walesi „cor” (törpe) és „ci” (kutya) szavakból szokták magyarázni: törpekutya.",
  "Két külön fajta létezik: a Pembroke Welsh Corgi és a Cardigan Welsh Corgi. Nevüket két walesi grófságról, Pembrokeshire-ről és Cardiganshire-ről kapták.",
  "A Cardigan corginak hosszú, bozontos farka van, a Pembroke-nak viszont gyakran csak egy kis csonkja.",
  "Egy walesi legenda szerint a tündérek corgin lovagoltak, és a vállukon látható világosabb rajzolat a „tündérnyereg” nyoma.",
  "A corgikat eredetileg szarvasmarhák terelésére tenyésztették: a csülkükbe csippentettek, az alacsony termetük miatt pedig a rúgások elkerülték őket.",
  "II. Erzsébet uralkodása alatt több mint 30 corgija volt.",
  "II. Erzsébet első saját corgija, Susan, a 18. születésnapjára érkezett, 1944-ben.",
  "A „dorgi” a corgi és a tacskó keveréke – II. Erzsébetnek is voltak dorgijai.",
  "A corgikölykök füle eleinte lóg, és csak néhány hónapos korukra áll fel.",
  "A corgik a legkisebb terelőkutyák közé tartoznak, marmagasságuk mindössze 25–30 cm körül van.",
  "Egy felnőtt Pembroke corgi jellemzően 10–14 kilogramm.",
  "A corgiknak dupla bundájuk van, ezért sokat vedlenek – a gazdik ezt viccesen „corgicsillámnak” hívják.",
  "A „sploot” az a jellegzetes fekvés, amikor a kutya hátsó lábait egyenesen hátranyújtja. A corgik a műfaj mesterei.",
  "A japán Cowboy Bebop animesorozat egyik szereplője, Ein, egy Pembroke corgi.",
  "2019-ben animációs film is készült a királyi corgikról „A királynő corgija” címmel.",
  "Egy corgi átlagosan 12–15 évig él.",
  "Stanley Coren pszichológus kutyaintelligencia-listáján a Pembroke corgi a 11. helyen végzett.",
  "A Pembroke corgi lehet vörös, homokszínű (sable), őzbarna vagy háromszínű. A Cardigannél a csíkos (brindle) és a kék márványos (blue merle) szín is előfordul.",
  "A hosszú hát miatt a corgiknál különösen fontos a megfelelő testsúly – a plusz kilók megterhelik a gerincüket.",
  "Az interneten népszerű tréfa, hogy a corgi popsija hátulról úgy néz ki, mint egy cipó.",
  "Az Egyesült Királyságban a 2010-es években annyira kevés Pembroke kölyök született, hogy a fajta felkerült a Kennel Club megfigyelési listájára.",
  "A Washington állambeli Emerald Downs lóversenypályán 2016 óta rendeznek corgi-futamot.",
  "A 2012-es londoni olimpia megnyitóján II. Erzsébet corgijai is szerepeltek a James Bond-os kisfilmben.",
  "A hagyomány szerint a Cardigan az ősibb fajta, a Pembroke ősei pedig flamand takácsokkal érkezhettek Walesbe a középkorban.",
  "A corgik nagyon szeretnek „beszélgetni”: morgással, nyüszögéssel és vicces hangokkal kommunikálnak.",
];
const GAUGES = [
  ["Zoomie-veszély", ["Nyugalom, csak szundi", "Enyhe izgalom", "Fél órán belül kitörés", "Zoomie-riadó!", "A nappali versenypályává alakul"]],
  ["Kajakoldulás-index", ["Szinte jóllakott (gyanús)", "Udvarias érdeklődés", "Nagy szemek bevetve", "Teljes kamra-ostrom", "Drámai éhhalál-színjáték"]],
  ["Kanapéfoglalási esély", ["A saját fekhelyét választja", "Félig a kanapén", "Bizonyosan a te helyed", "Elfoglalja a párnákat is", "A kanapé hivatalosan az övé"]],
  ["Postásriasztás", ["Békés nap", "Egy halk vakk", "Ablakon át figyelés", "Teljes ugatókoncert", "A postás nevét is tudja"]],
  ["Szőrhullás-előrejelzés", ["Alig egy-két szál", "Enyhe szőrzápor", "Seprű készenlétben", "Corgicsillám-vihar", "Építhetsz belőle még egy corgit"]],
];
function renderDaily(ed) {
  const r = rng("rovat-" + ed.date), n = dogName();
  const gauges = GAUGES.map(([name, lv]) => { const v = Math.round(10 + r() * 90); return { name, v, lbl: lv[Math.min(4, Math.floor(v / 20))] }; });
  el("daily").innerHTML = `
    <div class="card"><div class="kicker">A nap corgi-mondása</div><p class="quote">„${esc(pick(r, SAYINGS))}”</p></div>
    <div class="card"><div class="kicker">Corgi-tudásmorzsa</div><p style="font-size:17px;margin:6px 0 0">${esc(pick(r, FACTS))}</p></div>
    <div class="card gauges"><div class="kicker">${n ? esc(n) + " napi hangulatjelentése" : "Napi corgi-hangulatjelentés"}</div>
      ${gauges.map(g => `<div class="gauge"><span>${esc(g.name)}</span><span class="bar"><i style="width:${g.v}%"></i></span><span class="lbl">${g.v}% – ${esc(g.lbl)}</span></div>`).join("")}
    </div>`;
}

/* ---------- Corgi vagy kenyér? ---------- */
function renderBread(ed) {
  const items = ed.bread || [], box = el("bread");
  if (items.length < 2) { box.innerHTML = `<div class="empty">Ehhez a számhoz még nincs kenyeres játék. Holnap reggel már lesz!</div>`; return; }
  const key = "bread:" + ed.date;
  let st = store.get(key, { i: 0, ans: [] });
  const draw = (revealed) => {
    const done = st.i >= items.length, it = items[Math.min(st.i, items.length - 1)];
    const dots = items.map((_, k) => `<i class="${k < st.ans.length ? (st.ans[k] ? "ok" : "no") : k === st.i ? "cur" : ""}"></i>`).join("");
    if (done) {
      const sc = st.ans.filter(Boolean).length;
      const msg = sc === items.length ? "Hibátlan! Te vagy a corgi-pékmester! 🥖🐕" : sc >= items.length - 2 ? "Szép! Majdnem mindet kiszagoltad." : "Hát… a corgi is összekeverte volna. Holnap újra!";
      box.innerHTML = `<div class="card bread"><div class="dots">${dots}</div><div class="quote">${sc}/${items.length}</div><p>${msg}</p>
        <div class="small">Fotók: ${items.map(x => safeUrl(x.page) ? `<a href="${esc(x.page)}" target="_blank" rel="noopener">${esc(x.author)}</a>` : esc(x.author)).join(" · ")} (Wikimedia Commons)</div></div>`;
      return;
    }
    const zoomed = `background-image:url('${esc(it.file)}');background-size:${revealed ? 100 : 330}%;background-position:${revealed ? "50% 50%" : `${it.zx}% ${it.zy}%`}`;
    box.innerHTML = `<div class="card bread"><div class="dots">${dots}</div><div class="shot" style="${zoomed}"></div>
      <div class="res" id="brres"></div>
      <div class="ans" id="brans">${revealed ? `<button class="btn" id="brnext">${st.i + 1 < items.length ? "Következő →" : "Eredmény"}</button>`
        : `<button class="btn" data-a="1">🐕 Corgi</button><button class="btn" data-a="0">🍞 Kenyér</button>`}</div></div>`;
    if (revealed) {
      const ok = st.ans[st.i];
      el("brres").innerHTML = ok ? `✅ Talált! Ez ${it.corgi ? "egy corgi" : "egy kenyér"} volt.` : `❌ Nem talált – ez ${it.corgi ? "egy corgi" : "egy kenyér"} volt!`;
      el("brnext").onclick = () => { st.i++; store.set(key, st); draw(false); };
    } else {
      box.querySelectorAll("[data-a]").forEach(b => b.onclick = () => {
        st.ans[st.i] = (b.dataset.a === "1") === !!it.corgi; store.set(key, st); draw(true);
      });
    }
  };
  draw(st.ans.length > st.i);
}

/* ---------- Hol a corgi? ---------- */
function leafPath(x, y, s, rot, fill) {
  return `<ellipse cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" rx="${(s * .45).toFixed(1)}" ry="${s.toFixed(1)}" fill="${fill}" transform="rotate(${rot.toFixed(0)} ${x.toFixed(1)} ${y.toFixed(1)})"/>`;
}
function renderHide(ed) {
  const r = rng("rejtveny-" + ed.date), W = 360, H = 480;
  const LEAF = ["#d9772b", "#c0392b", "#e8a417", "#a8321e", "#e0661f", "#b5651d", "#f0b429"];
  let bg = `<defs><linearGradient id="hs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbe3bf"/><stop offset="1" stop-color="#f2c98a"/></linearGradient></defs>
    <rect width="${W}" height="${H}" fill="url(#hs)"/><circle cx="${60 + r() * 240}" cy="60" r="28" fill="#fff3d6"/>
    <path d="M0 210 Q90 180 180 205 T360 195 V480 H0 Z" fill="#a9b35d"/><path d="M0 300 Q120 280 240 300 T360 290 V480 H0 Z" fill="#94a24e"/>
    <path d="M150 480 Q170 380 200 300 Q215 260 260 210" stroke="#d8c49a" stroke-width="26" fill="none"/>`;
  const trees = [];
  for (let i = 0; i < 4; i++) {
    const x = 30 + i * 95 + r() * 30, y = 150 + r() * 70, s = 40 + r() * 20;
    let t = `<rect x="${x - 6}" y="${y}" width="12" height="${70 + r() * 30}" fill="#6b4226"/>`;
    for (let k = 0; k < 6; k++) t += `<circle cx="${x + (r() - .5) * s * 1.3}" cy="${y - r() * s}" r="${s * (.45 + r() * .3)}" fill="${pick(r, LEAF)}"/>`;
    trees.push(t);
  }
  const bench = `<g transform="translate(${200 + r() * 100} ${250 + r() * 40})"><rect x="-30" y="0" width="60" height="6" fill="#7a4a22"/><rect x="-30" y="-14" width="60" height="5" fill="#7a4a22"/><rect x="-26" y="6" width="4" height="14" fill="#4b2e16"/><rect x="22" y="6" width="4" height="14" fill="#4b2e16"/></g>`;
  // búvóhelyek: bokrok és levélkupacok
  const spots = [];
  for (let i = 0; i < 9; i++) spots.push({ x: 30 + r() * 300, y: 240 + r() * 215, w: 26 + r() * 24, kind: r() < .5 ? "bush" : "pile" });
  const hideAt = spots[Math.floor(r() * spots.length)];
  const cx = hideAt.x + (r() - .5) * hideAt.w * .5, cy = hideAt.y - hideAt.w * .5 - 12, sc = .2;
  const corgi = `<g transform="translate(${cx - 100 * sc} ${cy - 70 * sc}) scale(${sc})"><polygon points="52,74 38,10 94,50" fill="#d9772b"/><polygon points="148,74 162,10 106,50" fill="#d9772b"/>
    <polygon points="58,66 48,26 84,52" fill="#eba39b"/><polygon points="142,66 152,26 116,52" fill="#eba39b"/><ellipse cx="100" cy="92" rx="62" ry="54" fill="#d9772b"/>
    <path d="M100 46 L86 100 L114 100 Z" fill="#fffaf0"/><ellipse cx="100" cy="118" rx="38" ry="29" fill="#fffaf0"/><circle cx="78" cy="92" r="8" fill="#2a1d14"/><circle cx="122" cy="92" r="8" fill="#2a1d14"/>
    <ellipse cx="100" cy="108" rx="10" ry="8" fill="#2a1d14"/></g>`;
  let front = "";
  for (const s of spots) {
    if (s.kind === "bush") for (let k = 0; k < 5; k++) front += `<circle cx="${s.x + (k - 2) * s.w * .32}" cy="${s.y - Math.abs(k - 2) * -3 - (k % 2) * 8}" r="${s.w * .42}" fill="${pick(r, ["#5f7a32", "#6d8a3a", "#8a7a2e", "#7d8f3c"])}"/>`;
    else for (let k = 0; k < 26; k++) front += leafPath(s.x + (r() - .5) * s.w * 1.6, s.y - r() * s.w * .5, 6 + r() * 4, r() * 180, pick(r, LEAF));
  }
  let scatter = "";
  for (let i = 0; i < 170; i++) {
    const x = r() * W, y = 170 + r() * (H - 170);
    if (Math.hypot(x - cx, y - cy) < 16) continue; // a corgi szeme maradjon látható
    scatter += leafPath(x, y, 3 + r() * 4, r() * 180, pick(r, LEAF));
  }
  const key = "hide:" + ed.date, st = store.get(key, { found: false, taps: 0, secs: 0 });
  el("hide").innerHTML = `<div class="hide"><svg id="hsvg" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${bg}${trees.join("")}${bench}${corgi}${front}${scatter}<g id="hmarks"></g></svg>
    <div class="row"><span class="small" id="hinfo"></span><button class="btn alt" id="hhint">Súgás</button></div></div>`;
  const svg = el("hsvg"), marks = el("hmarks");
  const info = () => { el("hinfo").textContent = st.found ? `Megvan! 🎉 ${st.taps} koppintás, ${Math.floor(st.secs / 60)}:${String(st.secs % 60).padStart(2, "0")}` : `Koppintások: ${st.taps}`; };
  const showFound = () => { marks.innerHTML = `<circle cx="${cx}" cy="${cy}" r="22" fill="none" stroke="#2f6b3a" stroke-width="4"/>`; };
  if (st.found) showFound();
  info();
  const t0 = Date.now() - st.secs * 1000;
  svg.addEventListener("click", (e) => {
    if (st.found) return;
    const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM().inverse());
    st.taps++; st.secs = Math.round((Date.now() - t0) / 1000);
    if (Math.hypot(p.x - cx, p.y - cy) < 20) { st.found = true; showFound(); confetti(60); }
    else marks.insertAdjacentHTML("beforeend", `<text x="${p.x}" y="${p.y}" font-size="14" text-anchor="middle">❌</text>`);
    store.set(key, st); info();
  });
  el("hhint").onclick = () => {
    if (st.found) return;
    const qx = cx < W / 2 ? 0 : W / 2, qy = cy < 330 ? 170 : 330;
    marks.insertAdjacentHTML("beforeend", `<rect x="${qx}" y="${qy}" width="${W / 2}" height="${qy === 170 ? 160 : 150}" fill="#fff" opacity=".28" stroke="#d9531e" stroke-width="3" stroke-dasharray="8 6"/>`);
  };
}

/* ---------- Szókereső ---------- */
const WORDS = ["CORGI", "MANCS", "POPSI", "TERELÉS", "PEMBROKE", "CARDIGAN", "FÜLEK", "KEKSZ", "SÉTA", "LABDA", "BUNDA", "KÖLYÖK", "SZUNDI",
  "PÓRÁZ", "PUSZI", "KANAPÉ", "WALES", "JUTALOM", "MÓKUS", "CSONT", "SAJT", "VAKKANTÁS", "PIHE", "FAROK", "ZOOMIE", "TAKARÓ", "SIMI"];
function renderWS(ed) {
  const N = 10, r = rng("szo-" + ed.date), grid = Array.from({ length: N }, () => Array(N).fill(""));
  const dirs = [[0, 1], [1, 0], [1, 1], [-1, 1]];
  const placed = [];
  for (const w of shuffle(r, WORDS)) {
    if (placed.length === 7) break;
    const L = [...w];
    for (let t = 0; t < 120; t++) {
      const [dr, dc] = pick(r, dirs), r0 = Math.floor(r() * N), c0 = Math.floor(r() * N);
      const er = r0 + dr * (L.length - 1), ec = c0 + dc * (L.length - 1);
      if (er < 0 || er >= N || ec < 0 || ec >= N) continue;
      if (L.every((ch, k) => !grid[r0 + dr * k][c0 + dc * k] || grid[r0 + dr * k][c0 + dc * k] === ch)) {
        L.forEach((ch, k) => grid[r0 + dr * k][c0 + dc * k] = ch); placed.push(w); break;
      }
    }
  }
  const FILL = "AAAEEEKKLLMMNNOORRSSTTZZÁÉIÓÖÜGBDHPUVÍ";
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) if (!grid[i][j]) grid[i][j] = FILL[Math.floor(r() * FILL.length)];
  const key = "ws:" + ed.date, st = store.get(key, { found: [], cells: [] });
  let sel = null;
  const draw = () => {
    el("ws").innerHTML = `<div class="ws card"><div class="wsgrid" style="grid-template-columns:repeat(${N},1fr)">${grid.map((row, i) => row.map((ch, j) =>
      `<b data-i="${i}" data-j="${j}" class="${st.cells.includes(i * N + j) ? "found" : ""} ${sel && sel[0] === i && sel[1] === j ? "sel" : ""}">${ch}</b>`).join("")).join("")}</div>
      <div class="wswords">${placed.map(w => `<span class="${st.found.includes(w) ? "done" : ""}">${w}</span>`).join("")}</div>
      <div class="small">${st.found.length === placed.length ? "🎉 Mind megvan! Igazi corgi-szótudós vagy." : `${st.found.length}/${placed.length} szó megtalálva`}</div></div>`;
    el("ws").querySelectorAll(".wsgrid b").forEach(b => b.onclick = () => tap(+b.dataset.i, +b.dataset.j));
  };
  const tap = (i, j) => {
    if (!sel) { sel = [i, j]; return draw(); }
    const [a, b] = sel; sel = null;
    const dr = Math.sign(i - a), dc = Math.sign(j - b), len = Math.max(Math.abs(i - a), Math.abs(j - b)) + 1;
    if ((i - a) && (j - b) && Math.abs(i - a) !== Math.abs(j - b)) return draw();
    const cells = [], word = [];
    for (let k = 0; k < len; k++) { cells.push((a + dr * k) * N + (b + dc * k)); word.push(grid[a + dr * k][b + dc * k]); }
    const w = word.join(""), rw = [...word].reverse().join("");
    const hit = placed.find(p => (p === w || p === rw) && !st.found.includes(p));
    if (hit) { st.found.push(hit); st.cells.push(...cells); store.set(key, st); if (st.found.length === placed.length) confetti(70); }
    draw();
  };
  draw();
}

/* ---------- Memória ---------- */
function renderMemo(ed) {
  const imgs = [...(ed.images || []).map(x => x.file), ...(ed.bread || []).filter(x => x.corgi).map(x => x.file)].slice(0, 6);
  const EMO = ["🐕", "🦴", "🎾", "🧀", "🐾", "🍞"];
  const faces = imgs.map(f => ({ img: f })).concat(EMO.slice(0, 6 - imgs.length).map(e => ({ emo: e })));
  const r = rng("memo-" + ed.date + Math.random());
  let deck = shuffle(r, [...faces, ...faces].map((f, k) => ({ ...f, id: faces.indexOf(f) })));
  let open = [], gone = new Set(), moves = 0, lock = false;
  const best = store.get("memobest:" + ed.date, null);
  const draw = () => {
    el("memo").innerHTML = `<div class="memo">${deck.map((c, k) => `<button class="mc ${open.includes(k) || gone.has(k) ? "up" : ""} ${gone.has(k) ? "gone" : ""}" data-k="${k}" aria-label="kártya">
      <div class="back">🐾</div><div class="face" style="${c.img ? `background-image:url('${esc(c.img)}')` : "display:flex;align-items:center;justify-content:center;font-size:40px;background:var(--card)"}">${c.emo || ""}</div></button>`).join("")}</div>
      <div class="row" style="justify-content:space-between;max-width:480px;margin:8px auto 0"><span class="small">${gone.size === deck.length ? `🎉 Kész ${moves} lépésből!` : `${moves} lépés`}${best ? ` · mai legjobb: ${best}` : ""}</span>
      <button class="btn alt" id="memonew">Új játék</button></div>`;
    el("memo").querySelectorAll(".mc").forEach(b => b.onclick = () => flip(+b.dataset.k));
    el("memonew").onclick = () => renderMemo(ed);
  };
  const flip = (k) => {
    if (lock || open.includes(k) || gone.has(k)) return;
    open.push(k);
    if (open.length === 2) {
      moves++; const [a, b] = open;
      if (deck[a].id === deck[b].id) { gone.add(a); gone.add(b); open = [];
        if (gone.size === deck.length) { const bb = store.get("memobest:" + ed.date, null); if (!bb || moves < bb) store.set("memobest:" + ed.date, moves); confetti(50); } }
      else { lock = true; setTimeout(() => { open = []; lock = false; draw(); }, 900); }
    }
    draw();
  };
  draw();
}

/* ---------- Tamagocsi ---------- */
const DECAY = { food: 5, fun: 4, energy: 3, love: 4 }; // pont / óra
function tamaState() {
  const s = store.get("tama", null) || { food: 80, fun: 80, energy: 80, love: 80, t: Date.now(), sleepUntil: 0 };
  const h = Math.min(72, (Date.now() - s.t) / 36e5);
  for (const k in DECAY) s[k] = Math.max(0, Math.min(100, s[k] - DECAY[k] * h * (k === "energy" && s.sleepUntil > s.t ? -3 : 1)));
  s.t = Date.now();
  return s;
}
function tamaMood(s) {
  if (s.sleepUntil > Date.now()) return "sleep";
  const avg = (s.food + s.fun + s.energy + s.love) / 4, min = Math.min(s.food, s.fun, s.energy, s.love);
  return avg >= 68 && min >= 35 ? "happy" : avg >= 40 && min >= 15 ? "ok" : "sulky";
}
const NEEDS = { food: ["🍖", "Korog a pocakom… Valaki említette a vacsorát?"], fun: ["🎾", "Unatkozom. Unatkozom. UNATKOZOM. Labda?"],
  energy: ["😴", "Annyira fáradt vagyok, hogy a fülem is lekonyult."], love: ["💔", "Senki nem simogatott meg már ezer éve. (Fél órája.)"] };
const SAY = {
  happy: ["Ez a legjobb nap az életemben! (Mint tegnap is.)", "Popsiriszálás bekapcsolva! 🍑", "Szeretlek! Van nálad keksz?", "Minden rendben a birodalomban."],
  ok: ["Egész jó nap ez. Lehetne jobb is. Egy keksszel például.", "Figyellek. Csak hogy tudd.", "Mi lesz a mai program?"],
  sulky: ["Hmph. Nem szólok hozzád. …Na jó, de csak ha adsz valamit.", "Durcás vagyok. Hátat fordítok. Majdnem.", "Azt hiszem, valaki elfelejtett engem…"],
  sleep: ["Zzz… mókusokról álmodik…", "Zzz… a mancsai álmában is futnak…", "Pszt! A corgi szundít."],
};
const ACTIONS = [
  ["eat", "🍖 Etetés", s => { const full = s.food > 90; s.food = Math.min(100, s.food + 30); return full ? "Már nem fér belém… de azért megeszem. Corgi vagyok." : "Nyamm! A legjobb tál a világon!"; }],
  ["walk", "🦮 Séta", s => { if (s.energy < 12) return "Túl fáradt vagyok a sétához. Előbb szundi!"; s.fun = Math.min(100, s.fun + 25); s.energy -= 12; s.food -= 6; return "Szimat, szimat, szimat! Három fa, két bokor és egy mókus – remek séta volt!"; }],
  ["pet", "🤗 Simogatás", s => { s.love = Math.min(100, s.love + 25); return "Igen, pont ott, a fülem mögött! Ne hagyd abba!"; }],
  ["ball", "🎾 Labdázás", s => { if (s.energy < 10) return "Labda? Holnap. Ma már csak heverészni akarok."; s.fun = Math.min(100, s.fun + 20); s.energy -= 8; return "Hozom! Hozom! …Nem adom vissza! …Na jó, hozom!"; }],
  ["belly", "🐾 Pocakvakarás", s => { s.love = Math.min(100, s.love + 15); s.fun = Math.min(100, s.fun + 8); return "Hanyatt fekszik, mind a négy rövid lába az égnek mered. Boldogság."; }],
  ["nap", "😴 Szundi", s => { s.sleepUntil = Date.now() + 20 * 60e3; s.energy = Math.min(100, s.energy + 25); return "Összegömbölyödik a takarón. 20 perc szundi következik."; }],
];
let tamaMsg = "";
function renderTama() {
  const s = tamaState(); store.set("tama", s);
  const mood = tamaMood(s), n = dogName() || "A corgi";
  const low = Object.keys(NEEDS).filter(k => s[k] < 30).sort((a, b) => s[a] - s[b])[0];
  const say = tamaMsg || (mood === "sleep" ? pick(Math.random, SAY.sleep) : low ? NEEDS[low][1] : pick(Math.random, SAY[mood]));
  const LBL = { food: "Jóllakottság", fun: "Jókedv", energy: "Energia", love: "Szeretet" };
  const bar = v => `<span class="bar"><i class="${v < 30 ? "low" : v < 60 ? "mid" : ""}" style="width:${Math.round(v)}%"></i></span>`;
  el("tama").innerHTML = `<div class="card tama"><div>${corgiFace(mood, true)}</div><div>
    <p class="say"><b>${esc(n)}:</b> „${esc(say)}”</p>
    ${Object.keys(LBL).map(k => `<div class="stat"><span>${LBL[k]}</span>${bar(s[k])}</div>`).join("")}
    </div><div class="tbtns" style="grid-column:1/-1">${ACTIONS.map(([id, l]) => `<button class="btn" data-t="${id}" ${mood === "sleep" && id !== "pet" ? "disabled" : ""}>${l}</button>`).join("")}</div></div>
    <p class="small">A tamagocsi a valódi idővel együtt éhezik, fárad és unatkozik – nézz rá naponta többször! ${mood === "sleep" ? "Most alszik, csak simogatni lehet." : ""}</p>`;
  el("tama").querySelectorAll("[data-t]").forEach(b => b.onclick = () => {
    const st = tamaState(), a = ACTIONS.find(x => x[0] === b.dataset.t);
    if (st.sleepUntil > Date.now() && a[0] === "pet") { st.love = Math.min(100, st.love + 10); tamaMsg = "Álmában is csóválja a popsiját. 💤"; }
    else tamaMsg = a[2](st);
    for (const k in DECAY) st[k] = Math.max(0, Math.min(100, st[k]));
    store.set("tama", st); renderTama(); setTimeout(() => { tamaMsg = ""; }, 8000);
  });
  // az alsó menü „Corgim” ikonja maga a tamagocsi – látszik, ha valamire szüksége van
  const ico = document.querySelector('#tabbar [data-go="corgim"] b');
  if (ico) ico.innerHTML = `<span class="tico">${corgiFace(mood, false)}${low && mood !== "sleep" ? `<span class="bubble">${NEEDS[low][0]}</span>` : ""}</span>`;
}
setInterval(() => { if (document.visibilityState === "visible") renderTama(); }, 60000);

/* ---------- Popsi ---------- */
const POPSI_MSG = { 10: "Bemelegítés kész! 🍑", 50: "Ötven riszálás! A corgi elégedett.", 100: "SZÁZ! Popsi-mester vagy!", 250: "Ez már sport. Olimpiai szám lehetne.",
  500: "Félezer! A corgi kezd szédülni, de imádja.", 1000: "EZER! Legendás popsiriszáló lettél! 🏆" };
function renderPopsi() {
  const d = today(), st = store.get("popsi", { day: d, n: 0, total: 0, best: 0 });
  if (st.day !== d) { st.day = d; st.n = 0; store.set("popsi", st); }
  el("popsi").innerHTML = `<div class="card popsi">
    <svg id="butt" viewBox="0 0 240 230" xmlns="http://www.w3.org/2000/svg"><g id="buttg">
      <polygon points="58,52 66,4 98,40" fill="#d9772b"/><polygon points="182,52 174,4 142,40" fill="#d9772b"/>
      <ellipse cx="120" cy="110" rx="92" ry="78" fill="#d9772b"/>
      <path d="M120 200 C 70 200 44 160 52 128 C 58 100 92 96 120 122 C 148 96 182 100 188 128 C 196 160 170 200 120 200 Z" fill="#fffaf0"/>
      <path d="M120 128 C 118 150 120 170 120 196" stroke="#efe2c9" stroke-width="4" fill="none"/>
      <ellipse cx="120" cy="104" rx="9" ry="7" fill="#c7641f"/>
      <rect x="62" y="186" width="34" height="34" rx="14" fill="#d9772b"/><rect x="144" y="186" width="34" height="34" rx="14" fill="#d9772b"/>
      <ellipse cx="79" cy="220" rx="18" ry="8" fill="#fffaf0"/><ellipse cx="161" cy="220" rx="18" ry="8" fill="#fffaf0"/>
    </g></svg>
    <div class="cnt" id="pcnt">${st.n}</div><div class="small">riszálás ma · összesen: <span id="ptot">${st.total}</span> · legjobb nap: <span id="pbest">${st.best}</span></div>
    <div class="msg" id="pmsg"></div>
    <button class="btn alt" id="pshare">📤 Kihívás küldése</button></div>`;
  const g = el("buttg");
  el("butt").addEventListener("click", (e) => {
    st.n++; st.total++; st.best = Math.max(st.best, st.n); store.set("popsi", st);
    el("pcnt").textContent = st.n; el("ptot").textContent = st.total; el("pbest").textContent = st.best;
    g.classList.remove("wig"); void g.getBBox(); g.classList.add("wig");
    const h = document.createElement("span"); h.className = "heart"; h.textContent = pick(Math.random, ["💛", "🧡", "❤️", "🍑", "🐾"]);
    h.style.left = e.clientX - 12 + "px"; h.style.top = e.clientY - 20 + "px"; document.body.appendChild(h); setTimeout(() => h.remove(), 1000);
    if (POPSI_MSG[st.n]) { el("pmsg").textContent = POPSI_MSG[st.n]; if (st.n >= 100) confetti(40); }
    if (navigator.vibrate) try { navigator.vibrate(12); } catch (err) {}
  });
  el("pshare").onclick = async () => {
    const txt = `Ma ${st.n}-szor riszáltattam meg a corgi popsiját a Corgi Híradóban! 🍑 Megdöntöd? https://poovicsgyorgy.github.io/corgi-hirado/`;
    try { if (navigator.share) await navigator.share({ text: txt }); else { await navigator.clipboard.writeText(txt); el("pmsg").textContent = "Kimásolva – küldd el valakinek!"; } } catch (err) {}
  };
}

/* ---------- Névgenerátor ---------- */
const NG = {
  title: ["Sir", "Lady", "Gróf", "Grófnő", "Báró", "Bárónő", "Őfelsége", "Doktor", "Kapitány", "Herceg", "Hercegnő", "Professzor", "Főméltóságú"],
  first: ["Bogyó", "Kekszi", "Mogyi", "Pamacs", "Zsemle", "Fahéj", "Sajtos", "Brumi", "Pötty", "Morzsi", "Vajas", "Pogácsa", "Mazsola", "Bundi", "Csipesz", "Pihe", "Kakaó", "Muffin"],
  of: ["Kanapé", "Kekszes Doboz", "Hűtő", "Sajtpult", "Napfolt", "Takaróvár", "Hátsókert", "Kamra", "Pocakvakarás", "Walesi Dombok", "Teraszajtó", "Párnahegy"],
  epi: ["a Rettenthetetlen", "a Mindig Éhes", "a Rövid Lábú", "a Popsiriszáló", "a Postásrémisztő", "a Bolyhos", "a Mókusvadász", "a Szundikirály",
        "a Kekszvarázsló", "a Nagyfülű", "az Ügyes Terelő", "a Zoknitolvaj", "a Csodálatos", "a Kenyérképű"],
};
function genName() {
  const r = Math.random, f = pick(r, NG.first), t = pick(r, NG.title);
  return pick(r, [
    () => `${t} ${f} von ${pick(r, NG.of)}, ${pick(r, NG.epi)}`,
    () => `${f} ${pick(r, NG.epi).replace(/^az? /, "")}, a ${pick(r, NG.of)} ${pick(r, ["Hercege", "Őrzője", "Királya", "Úrnője", "Bajnoka"])}`,
    () => `${t} ${f} ${pick(r, NG.first.filter(x => x !== f))}, ${pick(r, NG.epi)}`,
    () => `Őkegyelmessége ${f}, a ${pick(r, NG.of)} ${pick(r, ["Grófja", "Bárója", "Lovagja"])}`,
  ])();
}
function renderNameGen() {
  const favs = store.get("namefavs", []);
  let cur = genName();
  const draw = () => {
    el("namegen").innerHTML = `<div class="card namegen"><div class="kicker">${dogName() ? `${esc(dogName())} teljes, hivatalos neve:` : "A corgid teljes, hivatalos neve:"}</div>
      <div class="nm">${esc(cur)}</div><div class="row"><button class="btn" id="ngnew">🎲 Új név</button><button class="btn alt" id="ngfav">⭐ Kedvenc</button></div>
      ${favs.length ? `<ul>${favs.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}</div>`;
    el("ngnew").onclick = () => { cur = genName(); draw(); };
    el("ngfav").onclick = () => { if (!favs.includes(cur)) { favs.unshift(cur); favs.splice(8); store.set("namefavs", favs); } draw(); };
  };
  draw();
}

/* ---------- Napló ---------- */
const urls = [];
async function renderDiary() {
  urls.splice(0).forEach(u => URL.revokeObjectURL(u));
  let entries = [];
  try { entries = (await idb.all()).sort((a, b) => (b.date + b.id).localeCompare(a.date + a.id, undefined, { numeric: true })); } catch (e) {}
  const n = dogName();
  el("diary").innerHTML = `<div class="card diary">
    <label class="small" for="dtext">Mi történt ma? Írd le, és ha van, csatolj egy fotót is!</label>
    <textarea id="dtext" placeholder="pl. Ma megette a fél zoknimat, aztán úgy tett, mintha semmi sem történt volna."></textarea>
    <div class="row" style="margin-top:8px"><input id="ddate" type="date" value="${today()}" style="width:auto;font:14px var(--sans);padding:6px;border:1px solid var(--muted);border-radius:8px;background:transparent;color:var(--ink)">
      <label class="btn alt">📷 Fotó<input id="dphoto" type="file" accept="image/*" hidden></label>
      <button class="btn" id="dsave">Mentés</button><span class="small" id="dmsg"></span></div></div>
    <div class="chron">${entries.length ? `<div class="mast">${esc(n || "Corgi")} Krónika</div>` : `<p class="empty">Még üres a napló. Írd be az első történetet!</p>`}<div id="dlist"></div></div>`;
  let photo = null;
  el("dphoto").onchange = async (e) => { const f = e.target.files[0]; if (!f) return; try { photo = await resizeImage(f, 1100); el("dmsg").textContent = "Fotó csatolva ✓"; } catch (err) { el("dmsg").textContent = "A fotót nem sikerült betölteni."; } };
  el("dsave").onclick = async () => {
    const text = el("dtext").value.trim(); if (!text && !photo) return;
    try { await idb.add({ date: el("ddate").value || today(), text, photo }); renderDiary(); } catch (err) { el("dmsg").textContent = "Nem sikerült menteni (kevés a hely?)."; }
  };
  const list = el("dlist");
  for (const e of entries) {
    const [head, ...rest] = (e.text || "").split(/(?<=[.!?])\s+/);
    let img = ""; if (e.photo) { const u = URL.createObjectURL(e.photo); urls.push(u); img = `<img src="${u}" alt="">`; }
    const d = new Date(e.date + "T12:00:00").toLocaleDateString("hu-HU", { year: "numeric", month: "long", day: "numeric" });
    list.insertAdjacentHTML("beforeend", `<article class="entry"><button class="x" data-id="${e.id}">törlés</button><div class="kicker">${esc(d)}</div>
      ${head ? `<h4>${esc(head)}</h4>` : ""}${img}${rest.length ? `<p style="margin:0">${esc(rest.join(" "))}</p>` : ""}</article>`);
  }
  list.querySelectorAll(".x").forEach(b => b.onclick = async () => {
    if (b.dataset.sure) { await idb.rm(+b.dataset.id); renderDiary(); } else { b.dataset.sure = 1; b.textContent = "biztosan törlöd?"; }
  });
}

/* ---------- Indítás ---------- */
function onEdition(ed) {
  EDN = ed;
  personalize();
  renderDaily(ed); renderBread(ed); renderHide(ed); renderWS(ed); renderMemo(ed);
}
personalize(); renderProfile(); renderTama(); renderPopsi(); renderNameGen(); renderDiary();
if (window.ED) onEdition(window.ED); else if (typeof ED !== "undefined" && ED) onEdition(ED);
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") { personalize(); renderTama(); } });
})();

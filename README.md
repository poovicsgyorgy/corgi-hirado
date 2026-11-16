# Corgi Híradó 🐕📰

Telefonra telepíthető webapp, ami minden reggel 6:00-kor (budapesti idő) összegyűjti a világ corgis híreit, lefordítja őket magyarra, és újságként jeleníti meg.

## Hogyan működik
- `.github/workflows/napi-lapszam.yml` – a GitHub minden reggel lefuttatja a hírgyűjtést, elmenti a lapszámot, és frissíti az oldalt.
- `scripts/fetch_news.py` – Google News és Bing News, 8 nyelven; ismétlődések kiszűrése, magyar fordítás.
- `data/` – a lapszámok (az utolsó 60 nap visszanézhető az appban).
- `index.html`, `sw.js`, `manifest.webmanifest`, `icons/` – maga az app.

## Kézi frissítés
Actions fül → „Napi lapszám” → **Run workflow**.

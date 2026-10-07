# Komunální volby v Praze 2026 — data a dashboard

Přehled kandidujících subjektů, jejich programů a kandidátů pro volby do
**Zastupitelstva hl. m. Prahy** a do zastupitelstev **57 městských částí**.

**Volby: pátek 9. 10. 2026 (14:00–22:00) a sobota 10. 10. 2026 (8:00–14:00).**

## Co v tom je

| | Počet |
|---|---:|
| Zastupitelstev (magistrát + 57 MČ) | 58 |
| Kandidátních listin | 330 |
| Kandidátů | 8 607 |
| Mandátů celkem (65 magistrát + 1 141 městské části) | 1 206 |
| Zastupitelů z roku 2022, kteří kandidují znovu | 983 |

Čísla v této tabulce pocházejí z `data/core/meta.json`; přegeneruje je
`scripts/build_core.py`. Needitujte je ručně — rozejdou se s daty.

Hloubka kvalitativní rešerše (`uroven_vyzkumu` v `assemblies.json`):
- **`full`** — magistrát a Praha 1–22: programy, profily lídrů a inkumbentů, doložené kauzy
- **`zakladni`** — 35 malých MČ: úplná data ČSÚ (kandidáti, listiny, výsledky 2022) bez kvalitativní rešerše

## Struktura

```
data/core/        ← generováno z otevřených dat ČSÚ. NEEDITOVAT.
data/research/    ← rešerše: parties/ people/ districts/ issues/. Zde se píše.
data/schema/      ← datový kontrakt (povinné čtení před editací research)
dashboard/        ← statická stránka + dashboard/data/ (generováno)
scripts/          ← pipeline
```

Oddělení `core` / `research` je záměrné: data ČSÚ se dají kdykoli přegenerovat
bez ztráty rešerše, a rešerše se dá rozšiřovat bez zasahování do oficiálních dat.
Párování jde přes `assembly_id` + `list_cislo` u listin a přes `name_key` u osob.

## Pipeline

```bash
bash scripts/fetch_csu.sh         # stáhne otevřená data ČSÚ do .cache/
python3 scripts/build_core.py     # .cache/ → data/core/*.json
python3 scripts/normalize.py --fix   # srovná volné hodnoty na číselníky
python3 scripts/check_cestina.py --fix  # typografie: pomlčky, uvozovky, mezery
python3 scripts/validate.py       # kontrola data/research/ proti kontraktu
python3 scripts/build_site.py     # data/core/ + data/research/ → dashboard/data/
bash scripts/serve.sh             # http://localhost:8765
```

`scripts/report_gaps.py` vypíše, co v rešerši chybí, seřazené podle toho, jak moc
to vadí (díra u listiny s mandátem váží víc než u mikro-listiny bez šance).
Přepínače `--detail` a `--asm <id>`.

`scripts/make_briefs.py <dir>` vygeneruje podklady pro rešerši — jeden markdown
na zastupitelstvo s ověřeným seznamem kandidátů. Používá se jako vstup pro
rešeršní práci, aby se pracovalo z oficiálních dat a ne z paměti.

## Hosting

Dashboard je **statická stránka** — HTML plus JSON soubory, žádný backend, žádná
databáze, žádné volání na cizí servery za běhu. Lokálně potřebuje server jen
proto, že prohlížeč nepustí `fetch()` z `file://`; na jakémkoli HTTP hostingu
běží rovnou.

### GitLab Pages

V repu je `.gitlab-ci.yml`, který při pushi do hlavní větve ověří data
(`validate.py`), vygeneruje `dashboard/data/` a publikuje výsledek:

```
https://<uživatel>.gitlab.io/<projekt>/
```

Běh v podadresáři funguje, protože všechny cesty v `index.html` jsou relativní
(`fetch("data/…")`). Nic se nemusí přenastavovat.

Vygenerovaná data se do gitu necommitují — `dashboard/data/` i `public/` jsou
v `.gitignore` a vznikají až v CI z `data/core/` a `data/research/`.

### Cokoli jiného

Stejně dobře poslouží GitHub Pages, Netlify, Cloudflare Pages, S3 i obyčejný
nginx. Jediný požadavek: vystavit obsah `dashboard/` (po `build_site.py`) jako
statické soubory. U GitHub Pages stačí workflow se stejnými třemi kroky.

### Velikost

| | |
|---|---:|
| Celý adresář `dashboard/` | 4,5 MB / 65 souborů |
| Načte se při otevření | 2,1 MB (gzip **~0,5 MB**) |
| Dotáhne se až podle potřeby | kandidátky jednotlivých zastupitelstev |

Hosting s gzipem (Pages ho zapíná sám) stáhne při prvním načtení kolem půl
megabajtu. Listiny kandidátů se načítají až při otevření konkrétního
zastupitelstva, ne předem.

## Pravidla pro rozšiřování rešerše

Plný kontrakt je v `data/schema/README.md`, metodika skóre v `data/research/METODIKA.md`.
Zkráceně:

1. **Každé faktické tvrzení má zdroj s URL a datem.** Bez URL to do dat nepatří.
2. **Kauzy jen doložené, vždy s polem `stav`** — zproštěn / odsouzen / probíhá /
   neprokázáno / bez závěru. Obvinění bez jeho výsledku se neuvádí.
3. **Co nevíte, je `null`** a patří do `mezery_v_datech[]`. Nikdy se nedomýšlí.
4. **Skóre jsou odvozená hodnocení, ne fakta** — každé má `oduvodneni`.
5. **Stejná měřítka na všechny subjekty** bez ohledu na ideologii.

`validate.py` tato pravidla vynucuje strojově: odmítne kauzu bez zdroje nebo bez
pole `stav`, neplatnou URL, `name_key`, který neodpovídá kandidátům ČSÚ, i odkaz
na listinu, která v oficiálních datech neexistuje.

## Zdroje dat

- **ČSÚ, otevřená data KV2026** (registrace kandidátů, stav k 23. 9. 2026) —
  <https://volby.gov.cz/opendata/kv2026/kv2026_opendata.htm>
- **ČSÚ, otevřená data KV2022** (výsledky a mandáty pro srovnání) —
  <https://volby.gov.cz/opendata/kv2022/kv2022_opendata.htm>
- Rešerše: programy stran, weby MČ, zápisy zastupitelstev, investigativní média.
  Konkrétní zdroj je u každého tvrzení v datech.

## Upozornění

Hodnocení konkrétnosti programů a důvěryhodnosti plnění slibů jsou **interpretace
podle zveřejněné metodiky**, ne objektivní měření. Údaje o kauzách uvádějí stav
k datu v poli `posledni_aktualizace`; neprokázané obvinění není důkaz viny.
Data ČSÚ jsou stavem k registraci kandidátních listin — v mezidobí mohlo dojít
ke změnám (např. úmrtí nebo odstoupení kandidáta).

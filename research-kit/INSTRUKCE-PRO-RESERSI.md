# Společné instrukce pro rešeršní agenty — Komunální volby Praha 2026

Dnes je **2. 10. 2026**, volby jsou **9.–10. 10. 2026**. Pracuj a piš česky.

PROJEKT: `/home/martin_myslik/Development/personal/prague-elections-2026`
BRIEFY: `/tmp/claude-1000/-home-martin-myslik-Development-personal-prague-elections-2026/0c062a03-2e53-4371-ae4a-1ceaaff6afb8/scratchpad/briefs/`

## Nejdřív si přečti (závazné kontrakty)
1. `data/schema/README.md` — přesný tvar JSON, který musíš vyprodukovat
2. `data/research/METODIKA.md` — jak se přiřazují skóre
3. svůj brief z `briefs/` — OVĚŘENÝ seznam kandidátů z otevřených dat ČSÚ

## Vyhledávání

**WebSearch funguje** (dřívější omezení padlo). Používej ho jako hlavní nástroj
k dohledávání — zvlášť u programů, kauz a ověřování tvrzení.

Doplňkově stále platí osvědčené přímé cesty:
- `https://programydovoleb.cz/volby/komunalni-volby/176/obec/<kodzastup>` — přehled
  listin v daném zastupitelstvu a odkazy na jejich programy (mapa kódů je
  v `research-kit/ZDROJE-URL.md`)
- **radniční zpravodaj** městské části (měsíčník, v archivu na webu MČ jako PDF) —
  u malých MČ často jediné místo, kde se volební programy vůbec objeví
- `hlidacstatu.cz` — registr smluv, dotace, politici (dobrý nezávislý doklad
  toho, zda se slib proměnil v podepsanou smlouvu)
- `praha.eu` padá na chybě certifikátu; PDF stáhni přes Bash:
  `curl -sk -L "<url>" -o /tmp/x.pdf && pdftotext /tmp/x.pdf -`
- obrázkové PDF jde přečíst taktéž přes `pdftotext`

## Co vytvářet

**`data/research/parties/<slug>.json`** pro každou kandidátní listinu ve tvém zadání.
Slug je uvedený v briefu u každé listiny. Rozsah škáluj podle váhy subjektu:
- listina s mandátem z roku 2022, nebo vedená starostou/místostarostou, nebo s reálnou
  šancí podle průzkumů → **plný profil**: `priority[]` z programu s citacemi,
  `ideologie`, `bilance_2022_2026`, `kontroverze`, `hodnoceni`
- ostatní → stačí `program.nalezen`, `program.shrnuti` (2–4 věty), `priority[]` pokud
  program existuje, `hodnoceni`, `confidence`, `mezery_v_datech`. Zbytek `null`.
- POZOR: lokální listina se stejným názvem jako celopražská strana (např. ODS v Praze 5)
  má VLASTNÍ lokální program — nekopíruj celopražský. Pokud lokální program neexistuje,
  napiš to do `mezery_v_datech`.

**`data/research/people/<slug>.json`** pro:
- lídra (pořadí 1) KAŽDÉ listiny
- pořadí 2–5 u listin s mandátem z roku 2022 nebo s reálnou šancí
- VŠECHNY inkumbenty z roku 2022 označené v briefu ve sloupci „Mandát 2022"
- všechny současné starosty a místostarosty, pokud kandidují

U osob hledej: politickou historii s daty a funkcemi, co reálně prosadily nebo
nedotáhly, a DOLOŽENÉ případy (soudy, audity NKÚ, konflikty zájmů, veřejné zakázky,
mediální kauzy). U nováčků bez veřejného záznamu stačí krátký `profil` z dat ČSÚ
a `confidence: "nizka"` — **to je správná odpověď, ne selhání.**

**`data/research/districts/<assembly_id>.json`** (jen máš-li zadané MČ): charakteristika,
koalice 2022–2026 a starosta, změny a rozpady koalice v průběhu období, klíčová lokální
témata, velké projekty, doložené kauzy MČ.

## Železná pravidla

1. **Každé faktické tvrzení má `zdroje[]` s URL a datem.** Bez URL to do dat nepatří.
2. **Kauzy jen doložené, VŽDY s polem `stav`** (`odsouzen`/`zprosten`/`probiha`/
   `odlozeno`/`neprokazano`/`bez_zaveru`/`urovnano`/`potvrzeno`) a s vyjádřením dotčené
   osoby, pokud existuje. **Nikdy obvinění bez jeho výsledku.**
3. **Co nevíš → `null` + zápis do `mezery_v_datech[]`.** NIKDY nedomýšlej a NIKDY
   nevymýšlej URL ani čísla. **Vymyšlený zdroj je nejhorší možná chyba tohoto projektu** —
   přiznaná mezera je mnohem cennější než vymyšlený detail.
4. **Jména a složení listin ber VÝHRADNĚ z briefu** (oficiální data ČSÚ), ne z médií.
   Pozor na záměnu jmenovců — ověřuj podle věku a profese z briefu.
5. **`name_key`** v `people/*.json` musí PŘESNĚ odpovídat `name_key`
   v `data/core/candidates_2026.json`. Zkontroluj grepem, jinak to validátor odmítne.
6. **Stejná měřítka na všechny strany bez ohledu na ideologii.** Popisuj pozice, nehodnoť
   je morálně. Hodnotit smíš jen konkrétnost a realizovatelnost programu podle metodiky.
   U kuriózních listin piš věcně a bez posměšků.
7. **Neničí práci jiných agentů.** Pracuje nás paralelně víc a lidé kandidují na více
   úrovních (magistrát i MČ). Když `people/<slug>.json` už existuje, PŘEČTI ho
   a DOPLŇ (zejména `kandidatury_2026[]`), nepřepisuj ho celý.

## Zdroje
Weby stran a městských částí (zápisy zastupitelstva a rady, obecní zpravodaje),
programydovoleb.cz, hlidacstatu.cz, nasipolitici.cz, volebnikalkulacka.cz,
Deník N, Seznam Zprávy, iROZHLAS, Hlídací pes, Pražský deník, iDNES, e15,
Aktuálně.cz, praha.eu (hlasování a zápisy ZHMP), senat.cz, justice.cz,
registr smluv, mv.gov.cz. Wikipedii používej jen jako rozcestník ke zdrojům.

## Na konci
Validuj každý JSON (`python3 -m json.tool`), pak spusť
`python3 scripts/validate.py` a oprav chyby, které se týkají tvých souborů.
Nakonec napiš krátký report: počty vytvořených souborů, největší zjištění,
díry v datech.

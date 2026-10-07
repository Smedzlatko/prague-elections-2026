# Datový kontrakt

Dva oddělené světy. **Nikdy je nemíchejte.**

| Adresář | Původ | Editace |
|---|---|---|
| `data/core/` | generováno z otevřených dat ČSÚ přes `scripts/build_core.py` | ❌ nikdy ručně — přepíše se |
| `data/research/` | rešerše (agenti / člověk) | ✅ zde se píše |
| `dashboard/data/` | sloučený výstup `scripts/build_site.py` | ❌ generováno |

Párování research → core probíhá přes `assembly_id` + `list_cislo` (listiny)
a u osob přes **`assembly_id` + `list_cislo` + `poradi`** z `kandidatury_2026`.

> **`poradi` je povinné.** `name_key` (příjmení + jméno) není jedinečný: v Praze
> ho sdílí 201 různých lidí a ve 25 případech i uvnitř jednoho zastupitelstva —
> na jedné listině v Praze 11 kandidují dva Ing. Ladislavové Kosovi (68 a 40 let).
> Bez `poradi` se dossier nepropojí vůbec, aby se kauza nepřiřadila jmenovci.
> `name_key` slouží jen jako kontrola a jako záloha tam, kde je jméno jedinečné.

## Povinná pravidla pro rešerši

1. **Každé tvrzení o faktu má zdroj.** Pole `zdroje[]` s `url` a `datum`. Bez URL to do dat nepatří.
2. **Kontroverze jen doložené**, s uvedeným *stavem* (`stav`) — zproštěn / odsouzen / probíhá /
   neprokázáno / bez závěru. Nikdy neuvádějte obvinění bez jeho výsledku.
3. **Nevíte-li, napište `null`** a doplňte do `mezery_v_datech[]`. Nikdy nedomýšlejte.
4. **Odlišujte citaci od parafráze.** Doslovný text programu → `citace`. Vlastní souhrn → `popis`.
5. **Hodnocení je odvozené, ne zjištěné.** Každé skóre má `oduvodneni` a odkaz na metodiku.

## `parties/<slug>.json` — kandidátní listina

```jsonc
{
  "slug": "magistrat-12-spolu-pro-prahu",   // <assembly_id>-<cislo>-<slug nazvu>
  "assembly_id": "magistrat",
  "list_cislo": 12,
  "nazev": "SPOLU pro Prahu",
  "zkratka": "SPOLU",
  "typ": "koalice",
  "slozeni": ["ODS", "TOP 09"],
  "web": "https://...",
  "program": {
    "nalezen": true,
    "zdroje": [{"nazev": "Program SPOLU pro Prahu 2026", "url": "https://...", "datum": "2026-10-02"}],
    "shrnuti": "2–4 věty, co strana slibuje a čím se odlišuje.",
    "priority": [
      {
        "oblast": "bydleni",            // bydleni|doprava|zivotni_prostredi|skolstvi|socialni|
                                        // bezpecnost|kultura|hospodareni|transparentnost|
                                        // uzemni_rozvoj|zdravotnictvi|sport|digitalizace|
                                        // verejny_prostor|energetika|jine
                                        // Jiná hodnota je chyba — číselník je uzavřený.
        "nazev": "Výstavba 10 000 městských bytů",
        "popis": "Vlastní souhrn slibu.",
        "citace": "Doslovný text z programu, pokud je k dispozici.",
        "merytelne": true,              // je slib kvantifikovaný / ověřitelný?
        "konkretnost": "vysoka",        // vysoka|stredni|nizka — jak konkrétní slib je
        "realizovatelnost": {
          "hodnoceni": "stredni",       // vysoka|stredni|nizka|neoveritelne
          "oduvodneni": "Závisí na změně územního plánu, kterou město nekontroluje samo."
        },
        "zdroj_url": "https://..."
      }
    ],
    "oblasti": {"bydleni": "...", "doprava": "..."}   // volitelný textový rozpad
  },
  "ideologie": {
    "ekonomicka_osa": 1.5,     // -3 (levice) … +3 (pravice), null když nelze určit
    "hodnotova_osa": 0.5,      // -3 (progresivní) … +3 (konzervativní)
    "oduvodneni": "...",
    "zdroje": []
  },
  "bilance_2022_2026": {
    "byla_v_koalici": true,
    "role": "Vedla koalici, primátor Bohuslav Svoboda.",
    "splnene_sliby":  [{"slib": "...", "dukaz": "...", "zdroj_url": "..."}],
    "castecne":       [{"slib": "...", "dukaz": "...", "zdroj_url": "..."}],
    "nesplnene_sliby":[{"slib": "...", "dukaz": "...", "zdroj_url": "..."}],
    "shrnuti": "..."
  },
  "kontroverze": [ /* stejný tvar jako people[].pripady */ ],
  "hodnoceni": {
    "konkretnost_programu": 3,      // 0–5
    "doveryhodnost_plneni": 2,      // 0–5, jen pokud existuje historický záznam; jinak null
    "transparentnost": 3,           // 0–5
    "oduvodneni": "Proč právě tato čísla.",
    "metodika": "data/research/METODIKA.md"
  },
  "lidri": ["adam-scheinherr"],      // slugy do people/
  "mezery_v_datech": ["Program nezveřejnil rozpočtové krytí."],
  "confidence": "vysoka",            // vysoka|stredni|nizka
  "posledni_aktualizace": "2026-10-02"
}
```

## `people/<slug>.json` — osoba

```jsonc
{
  "slug": "adam-scheinherr",
  "name_key": "scheinherr-adam",     // MUSÍ odpovídat core/candidates_2026.json
  "cele_jmeno": "Ing. Adam Scheinherr, MSc., Ph.D.",
  "rok_narozeni": 1986,
  "strana": "PRAHA SOBĚ",
  "kandidatury_2026": [{"assembly_id": "magistrat", "list_cislo": 5, "poradi": 1}],
  "role": "lidr",                    // lidr|top5|inkumbent|jiny
  "profil": "3–6 vět: kdo to je, odkud přišel, čím je v pražské politice významný.",
  "vzdelani": "...",
  "profese": "...",
  "politicka_historie": [
    {"od": "2018-11", "do": "2022-11", "funkce": "náměstek primátora pro dopravu",
     "organizace": "Hlavní město Praha", "zdroj_url": "https://..."}
  ],
  "vysledky": [                      // co reálně dotáhl / nedotáhl
    {"nazev": "Rekonstrukce Libeňského most", "popis": "...",
     "stav": "dokonceno",            // dokonceno|rozpracovano|zastaveno|zpozdeno|selhalo
     "hodnoceni": "...", "zdroje": []}
  ],
  "pripady": [                       // kontroverze / soudy / audity — JEN DOLOŽENÉ
    {
      "nazev": "...",
      "typ": "medialni",             // soudni|policejni|audit_nku|konflikt_zajmu|
                                     // medialni|stranicky|verejna_zakazka|jine
      "obdobi": "2021–2023",
      "popis": "Věcně, bez hodnotících adjektiv.",
      "stav": "neprokazano",         // odsouzen|zprosten|probiha|odlozeno|neprokazano|
                                     // bez_zaveru|urovnano|potvrzeno
      "zavaznost": "stredni",        // nizka|stredni|vysoka
      "reakce_dotcene_osoby": "...", // pokud se vyjádřila
      "zdroje": [{"nazev": "Deník N", "url": "https://...", "datum": "2023-04-11"}]
    }
  ],
  "plneni_slibu": {
    "skore": 3,                      // 0–5; null bez historického záznamu
    "oduvodneni": "...",
    "priklady": [{"slib": "...", "vysledek": "...", "zdroj_url": "..."}]
  },
  "zajmy_a_majetek": {
    "firmy": [], "registr_oznameni_url": null, "poznamka": null
  },
  "citace": [{"text": "...", "kontext": "...", "zdroj_url": "...", "datum": "..."}],
  "zdroje": [{"nazev": "...", "url": "...", "datum": "..."}],
  "mezery_v_datech": [],
  "confidence": "vysoka",
  "posledni_aktualizace": "2026-10-02"
}
```

## `districts/<assembly_id>.json` — kontext městské části

```jsonc
{
  "assembly_id": "mc-praha-11",
  "nazev": "Praha 11",
  "charakteristika": "Chodov a Háje, největší pražské panelové sídliště. ...",
  "soucasna_koalice": {"obdobi": "2022–2026", "strany": ["..."],
                       "starosta": {"jmeno": "...", "strana": "...", "slug": "..."},
                       "zdroj_url": "..."},
  "zmeny_v_obdobi": ["Rozpad koalice v roce 2024 ...'"],
  "klicova_temata": [
    {"nazev": "Regenerace sídliště", "popis": "...", "proc_zalezi": "...", "zdroje": []}
  ],
  "velke_projekty": [{"nazev": "...", "stav": "...", "popis": "...", "zdroje": []}],
  "kontroverze_mc": [ /* tvar pripady */ ],
  "zdroje": [],
  "mezery_v_datech": [],
  "confidence": "stredni",
  "posledni_aktualizace": "2026-10-02"
}
```

## `issues/<slug>.json` — celopražské téma

```jsonc
{
  "slug": "bydleni",
  "nazev": "Dostupnost bydlení",
  "popis": "Stav problému v číslech.",
  "fakta": [{"tvrzeni": "...", "hodnota": "...", "zdroj_url": "...", "datum": "..."}],
  "pozice_stran": [{"list_slug": "magistrat-12-spolu-pro-prahu", "pozice": "...",
                    "citace": "...", "zdroj_url": "..."}],
  "zdroje": [], "posledni_aktualizace": "2026-10-02"
}
```

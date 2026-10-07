# Rešeršní sada

Podklady, ze kterých vznikla data v `data/research/`. Slouží k tomu, aby se dala
rešerše kdykoli dodělat nebo zopakovat — i jiným člověkem nebo jiným modelem.

| Soubor | K čemu |
|---|---|
| `INSTRUKCE-PRO-RESERSI.md` | zadání pro rešeršéra: co vytvářet a podle jakých pravidel |
| `ZDROJE-URL.md` | kde co hledat — pro každé z 58 zastupitelstev odkaz na přehled listin a jejich programů |
| `briefy/<assembly_id>.md` | ověřený seznam listin a kandidátů z dat ČSÚ, jeden soubor na zastupitelstvo |

Briefy se dají kdykoli přegenerovat:

```bash
python3 scripts/make_briefs.py research-kit/briefy
```

## Proč briefy

Rešeršér (člověk i model) má silnou tendenci psát jména a složení listin
z paměti nebo z novinových článků, kde bývají nepřesné. Brief obsahuje úplný
a ověřený seznam z registrace ČSÚ včetně věku, uvedeného povolání, členství
a informace, kdo byl zastupitelem už v roce 2022. Pravidlo zní: **jména a složení
listin výhradně z briefu, nikdy z médií.** `scripts/validate.py` to pak strojově
kontroluje proti `data/core/candidates_2026.json`.

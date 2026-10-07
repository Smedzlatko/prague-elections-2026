#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Srovná volné hodnoty v data/research/ na uzavřené číselníky.

Rešeršér (člověk i model) přirozeně sahá po názvu oblasti, který dává smysl
v jeho kontextu — „veřejný prostor", „energetika", „sociální oblast". Místo
odmítnutí se známé varianty mapují na kanonickou hodnotu; co se namapovat
nedá, se vypíše, aby se buď doplnilo do číselníku, nebo opravilo ručně.

    python3 scripts/normalize.py          # jen vypíše, co by změnil
    python3 scripts/normalize.py --fix
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "data" / "research"

OBLASTI = ["bezpecnost", "bydleni", "digitalizace", "doprava", "energetika",
           "hospodareni", "jine", "kultura", "skolstvi", "socialni", "sport",
           "transparentnost", "uzemni_rozvoj", "verejny_prostor",
           "zdravotnictvi", "zivotni_prostredi"]

ALIAS = {
    "socialni_oblast": "socialni", "socialni_politika": "socialni",
    "socialni_sluzby": "socialni", "seniori": "socialni",
    "obchod_sluzby": "hospodareni", "podnikani": "hospodareni",
    "finance": "hospodareni", "rozpocet": "hospodareni", "majetek": "hospodareni",
    "bydleni_a_vystavba": "bydleni", "byty": "bydleni",
    "vystavba": "uzemni_rozvoj", "rozvoj": "uzemni_rozvoj", "uzemni_plan": "uzemni_rozvoj",
    "doprava_a_parkovani": "doprava", "parkovani": "doprava", "mhd": "doprava",
    "skolstvi_a_vzdelavani": "skolstvi", "vzdelavani": "skolstvi", "skoly": "skolstvi",
    "sport_a_volny_cas": "sport", "volny_cas": "sport",
    "kultura_a_spolky": "kultura", "spolky": "kultura",
    "zelen": "zivetni_prostredi" if False else "zivotni_prostredi",
    "zivotni_prostredi_a_zelen": "zivotni_prostredi", "odpady": "zivotni_prostredi",
    "klima": "zivotni_prostredi",
    "verejna_prostranstvi": "verejny_prostor", "verejne_prostory": "verejny_prostor",
    "uklid": "verejny_prostor",
    "zdravotni_pece": "zdravotnictvi",
    "otevrenost": "transparentnost", "participace": "transparentnost",
    "radnice": "transparentnost", "sprava": "transparentnost",
    "it": "digitalizace", "smart_city": "digitalizace",
    "energie": "energetika", "uspory_energie": "energetika",
}


def main():
    do_fix = "--fix" in sys.argv
    changed, unknown = Counter(), Counter()
    touched = 0
    for f in sorted((RES / "parties").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        dirty = False
        for pr in ((d.get("program") or {}).get("priority") or []):
            ob = pr.get("oblast")
            if not ob or ob in OBLASTI:
                continue
            new = ALIAS.get(ob)
            if new:
                changed[f"{ob} → {new}"] += 1
                if do_fix:
                    pr["oblast"] = new; dirty = True
            else:
                unknown[ob] += 1
        if dirty:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
            touched += 1

    if changed:
        print("Mapováno na kanonickou hodnotu:")
        for k, n in changed.most_common():
            print(f"  {n:>4}×  {k}")
    if unknown:
        print("\nNeznámé hodnoty — doplň do ALIAS, nebo do číselníku OBLASTI:")
        for k, n in unknown.most_common():
            print(f"  {n:>4}×  {k!r}")
    if not changed and not unknown:
        print("Vše odpovídá číselníku.")
    if do_fix:
        print(f"\nUpraveno souborů: {touched}")
    else:
        print("\n(zkušební běh — spusť s --fix pro zápis)")


if __name__ == "__main__":
    main()

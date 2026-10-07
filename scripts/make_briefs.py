#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generuje podkladové brief soubory pro rešeršní agenty z data/core/."""
import json, sys, unicodedata, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data" / "core"
OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".briefs"
OUTDIR.mkdir(parents=True, exist_ok=True)

A = {a["id"]: a for a in json.loads((CORE / "assemblies.json").read_text(encoding="utf-8"))}
L = json.loads((CORE / "lists_2026.json").read_text(encoding="utf-8"))
C = json.loads((CORE / "candidates_2026.json").read_text(encoding="utf-8"))
R22 = json.loads((CORE / "results_2022.json").read_text(encoding="utf-8"))

lists_by_asm = defaultdict(list)
for l in L:
    lists_by_asm[l["assembly_id"]].append(l)
cand_by_list = defaultdict(list)
for c in C:
    cand_by_list[c["list_id"]].append(c)
r22_by_asm = defaultdict(list)
for r in R22:
    r22_by_asm[r["assembly_id"]].append(r)


def slug(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower())


def short(name, n=90):
    name = " ".join(name.split())
    return name if len(name) <= n else name[:n].rstrip() + "…"


def brief(asm_id, top=8):
    a = A[asm_id]
    out = [f"# {a['nazev']} — podklad z otevřených dat ČSÚ",
           "",
           f"- `assembly_id`: **{asm_id}**",
           f"- Mandátů: **{a['mandaty']}** | obyvatel: {a['pocet_obyvatel']:,}".replace(",", " "),
           f"- Kandidátních listin 2026: **{a['pocet_listin']}** | kandidátů: {a['pocet_kandidatu']}",
           ""]
    if r22_by_asm[asm_id]:
        out += ["## Výsledky 2022 (ČSÚ)", "",
                "| Strana | % | Mandáty |", "|---|---:|---:|"]
        for r in sorted(r22_by_asm[asm_id], key=lambda x: -(x["procent"] or 0)):
            if (r["procent"] or 0) < 1 and r["mandaty"] == 0:
                continue
            out.append(f"| {short(r['nazev'], 60)} | {r['procent']:.2f} | {r['mandaty']} |")
        out.append("")
    out += ["## Kandidátní listiny 2026 (úplný, ověřený seznam)", ""]
    for l in sorted(lists_by_asm[asm_id], key=lambda x: x["cislo"]):
        cs = sorted(cand_by_list[l["id"]], key=lambda x: x["poradi"])
        comp = ", ".join(s["zkratka"] for s in l["slozeni"])
        out += [f"### [{l['cislo']}] {short(l['nazev'], 160)}",
                f"- `list_cislo`: {l['cislo']} | typ: {l['typ']} | složení: {comp}"
                f" | kandidátů: {len(cs)}",
                f"- navrhovaný `slug`: `{asm_id}-{l['cislo']}-{slug(short(l['nazev'],40))}`",
                "",
                "| # | Jméno | Věk | Uvedené povolání (vlastní text kandidáta) | Členství | Mandát 2022 |",
                "|---:|---|---:|---|---|---|"]
        inc_extra = [c for c in cs[top:] if c["inkumbent_2022"]]
        for c in cs[:top] + inc_extra:
            inc = f"ano (č. {c['inkumbent_2022']['poradi_2022']}, "\
                  f"{c['inkumbent_2022']['preferencni_hlasy_2022']} pref. hl.)" \
                  if c["inkumbent_2022"] else "—"
            out.append(f"| {c['poradi']} | **{c['cele_jmeno']}** | {c['vek'] or '?'} | "
                       f"{short(c['povolani'] or '—', 150)} | {c['prislusnost_zkratka'] or '—'} | {inc} |")
            out[-1] += ""
        if inc_extra:
            out.append(f"\n> Řádky nad #{top} jsou inkumbenti z roku 2022 (nutno pokrýt).")
        out.append("")
    return "\n".join(out)


targets = sys.argv[2:] or list(A)
for t in targets:
    if t not in A:
        print(f"!! neznámé: {t}"); continue
    p = OUTDIR / f"{t}.md"
    p.write_text(brief(t), encoding="utf-8")
    print(f"  ✓ {p}")

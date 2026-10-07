#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Co v rešerši chybí — tříděno podle toho, jak moc to vadí.

Priorita se neodvíjí od toho, kolik polí je prázdných, ale od váhy subjektu:
díra u listiny, která v roce 2022 získala mandát, je vážná; stejná díra
u mikro-listiny bez šance na mandát je v pořádku a jen se eviduje.

    python3 scripts/report_gaps.py             # souhrn podle priorit
    python3 scripts/report_gaps.py --detail    # úplný výpis
    python3 scripts/report_gaps.py --asm magistrat
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data" / "core"
RES = ROOT / "data" / "research"


def rd(p, d=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d


asms = {a["id"]: a for a in rd(CORE / "assemblies.json", [])}
lists = rd(CORE / "lists_2026.json", [])
cands = rd(CORE / "candidates_2026.json", [])
res22 = rd(CORE / "results_2022.json", [])

parties, people, districts = {}, {}, {}
for p in (RES / "parties").glob("*.json"):
    d = rd(p)
    if d: parties[(d.get("assembly_id"), d.get("list_cislo"))] = (p.stem, d)
for p in (RES / "people").glob("*.json"):
    d = rd(p)
    if d: people[d.get("slug") or p.stem] = d
for p in (RES / "districts").glob("*.json"):
    d = rd(p)
    if d: districts[d.get("assembly_id")] = d

namekey_to_person = defaultdict(list)
for slug, d in people.items():
    if d.get("name_key"):
        namekey_to_person[d["name_key"]].append(slug)

leader_of = {}
for c in cands:
    if c["poradi"] == 1 and c["list_id"]:
        leader_of[c["list_id"]] = c

mand22 = {(r["assembly_id"], r["zkratka"]): r["mandaty"] for r in res22}

P1, P2, P3 = [], [], []   # vysoká / střední / nízká priorita
only_asm = None
if "--asm" in sys.argv:
    only_asm = sys.argv[sys.argv.index("--asm") + 1]


def add(prio, asm, what, detail):
    (P1 if prio == 1 else P2 if prio == 2 else P3).append((asm, what, detail))


for l in lists:
    a = l["assembly_id"]
    if only_asm and a != only_asm:
        continue
    if asms[a]["uroven_vyzkumu"] != "full":
        continue
    key = (a, l["cislo"])
    name = l["zkratka30"] or l["nazev"][:40]
    ent = parties.get(key)
    # váha listiny: měla mandát v roce 2022?
    had = any(r["assembly_id"] == a and r["mandaty"] > 0 and
              (r["vstrana"] == l["vstrana"] or r["zkratka"] == l["zkratka"])
              for r in res22)
    big = had or a == "magistrat"

    if not ent:
        add(1 if big else 2, a, "chybí rešerše listiny", f"[{l['cislo']}] {name}")
        continue
    slug, d = ent
    prog = d.get("program") or {}
    if prog.get("nalezen") is False:
        add(1 if big else 3, a, "program nenalezen", f"[{l['cislo']}] {name}")
    elif not (prog.get("priority") or []):
        add(1 if big else 3, a, "program bez priorit", f"[{l['cislo']}] {name}")
    h = d.get("hodnoceni") or {}
    bil = d.get("bilance_2022_2026") or {}
    # Skóre plnění slibů má smysl jen u toho, kdo skutečně vládl. Mandát sám
    # o sobě nestačí — opoziční strana nemá co plnit a null je u ní správně.
    if bil.get("byla_v_koalici") and h.get("doveryhodnost_plneni") is None:
        add(1, a, "vládla, ale chybí skóre plnění slibů", f"[{l['cislo']}] {name}")
    if had and bil.get("byla_v_koalici") and not any(
            bil.get(k) for k in ("splnene_sliby", "castecne", "nesplnene_sliby")):
        add(1, a, "byla v koalici, ale bilance je prázdná", f"[{l['cislo']}] {name}")
    # lídr bez profilu
    lead = leader_of.get(l["id"])
    if lead and not namekey_to_person.get(lead["name_key"]):
        add(1 if big else 2, a, "lídr bez profilu",
            f"[{l['cislo']}] {name} — {lead['cele_jmeno']}")

# inkumbenti bez profilu
for c in cands:
    a = c["assembly_id"]
    if only_asm and a != only_asm: continue
    if asms[a]["uroven_vyzkumu"] != "full": continue
    if c["inkumbent_2022"] and not namekey_to_person.get(c["name_key"]):
        add(2, a, "zastupitel z 2022 bez profilu",
            f"{c['cele_jmeno']} ({c['list_nazev'][:34] if c['list_nazev'] else '?'})")

# slabé profily
for slug, d in people.items():
    a = (d.get("kandidatury_2026") or [{}])[0].get("assembly_id", "?")
    if only_asm and a != only_asm: continue
    if not (d.get("politicka_historie") or []) and d.get("role") in (None, "lidr"):
        add(2, a, "profil bez politické historie", f"{d.get('cele_jmeno')} ({slug})")
    if not (d.get("zdroje") or []):
        add(2, a, "profil bez zdrojů", f"{d.get('cele_jmeno')} ({slug})")

# MČ bez kontextu / bez zdrojů u témat
for aid, a in asms.items():
    if only_asm and aid != only_asm: continue
    if a["uroven_vyzkumu"] != "full" or a["typ"] == "magistrat": continue
    d = districts.get(aid)
    if not d:
        add(1, aid, "chybí kontext městské části", a["nazev"]); continue
    for i, t in enumerate(d.get("klicova_temata") or []):
        if not (t.get("zdroje") or []):
            add(2, aid, "téma MČ bez zdroje", t.get("nazev", f"#{i}"))

# přiznané mezery v datech
mez = []
for src, coll in (("listina", parties.values()), ("osoba", people.items()),
                  ("MČ", districts.items())):
    for item in coll:
        d = item[1] if isinstance(item, tuple) else item
        for m in (d.get("mezery_v_datech") or []):
            mez.append((src, d.get("slug") or d.get("assembly_id"), m))


def dump(title, rows, detail):
    if not rows: return
    print(f"\n{title} — {len(rows)}")
    by = defaultdict(list)
    for a, what, det in rows:
        by[what].append((a, det))
    for what, items in sorted(by.items(), key=lambda x: -len(x[1])):
        print(f"  {len(items):>4}×  {what}")
        if detail:
            for a, det in items[:200]:
                print(f"          {asms.get(a, {}).get('nazev', a)}: {det}")


detail = "--detail" in sys.argv
dump("PRIORITA 1 — vadí, patří doplnit", P1, detail)
dump("PRIORITA 2 — stojí za doplnění", P2, detail)
dump("PRIORITA 3 — v pořádku, jen evidence", P3, detail)
print(f"\nPřiznaných mezer v datech (mezery_v_datech): {len(mez)}")
if detail:
    for src, who, m in mez[:200]:
        print(f"    [{src}] {who}: {m}")
print("\nTip: python3 scripts/report_gaps.py --detail | --asm magistrat")

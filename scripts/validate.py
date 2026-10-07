#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kontrola souborů v data/research/ proti datovému kontraktu.

Chyby (✗) blokují build. Varování (⚠) jen informují.
Spuštění:  python3 scripts/validate.py [--strict]
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data" / "core"
RES = ROOT / "data" / "research"

ERR: list[str] = []
WARN: list[str] = []

def err(f, msg):  ERR.append(f"✗ {f}: {msg}")
def warn(f, msg): WARN.append(f"⚠ {f}: {msg}")

OBLASTI = {"bydleni","doprava","zivotni_prostredi","skolstvi","socialni","bezpecnost",
           "kultura","hospodareni","transparentnost","uzemni_rozvoj","zdravotnictvi",
           "sport","digitalizace","verejny_prostor","energetika","jine"}
STAVY = {"odsouzen","zprosten","probiha","odlozeno","neprokazano","bez_zaveru",
         "urovnano","potvrzeno"}
TYPY_PRIPADU = {"soudni","policejni","audit_nku","konflikt_zajmu","medialni",
                "stranicky","verejna_zakazka","jine"}
ZAVAZNOST = {"nizka","stredni","vysoka"}
CONFIDENCE = {"vysoka","stredni","nizka"}
URL_RE = re.compile(r"^https?://[^\s\"<>]+$")
PARTY_DOMAIN_RE = re.compile(
    r"(pirati|ods\.cz|top09|topka|stan-|starostove|ano2011|anobudelip|"
    r"motoriste|praha-?sobe|prahasobe|jsmepraha|senpro|levice|svobodni|"
    r"patrioti|zeleni|kdu|kscm|cssd|tempoplan|janhusbauer)", re.I)

# ------------------------------------------------------------------ core
core = {}
for n in ["assemblies","lists_2026","candidates_2026"]:
    p = CORE / f"{n}.json"
    if not p.exists():
        print(f"✗ chybí {p} — spusť nejdřív scripts/build_core.py"); sys.exit(2)
    core[n] = json.loads(p.read_text(encoding="utf-8"))

ASM = {a["id"] for a in core["assemblies"]}
LIST_KEYS = {(l["assembly_id"], l["cislo"]) for l in core["lists_2026"]}
NAME_KEYS = defaultdict(set)
for c in core["candidates_2026"]:
    NAME_KEYS[c["name_key"]].add(c["assembly_id"])
# kolik kandidátů v daném zastupitelstvu sdílí totéž jméno
NK_COUNT = defaultdict(int)
POS = set()
LIST_CISLO = {l["id"]: l["cislo"] for l in core["lists_2026"]}
for c in core["candidates_2026"]:
    NK_COUNT[(c["assembly_id"], c["name_key"])] += 1
    if c["list_id"]:
        POS.add((c["assembly_id"], LIST_CISLO[c["list_id"]], c["poradi"]))


def load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(p.name, f"nevalidní JSON — {e}")
        return None


def check_sources(f, srcs, where, required=True):
    """Zdroje musí být seznam objektů s použitelnou URL."""
    if not srcs:
        if required:
            warn(f, f"{where}: bez zdrojů")
        return
    if not isinstance(srcs, list):
        err(f, f"{where}: zdroje musí být seznam"); return
    for i, s in enumerate(srcs):
        if not isinstance(s, dict):
            err(f, f"{where}.zdroje[{i}]: musí být objekt s nazev/url/datum"); continue
        u = s.get("url")
        if not u:
            err(f, f"{where}.zdroje[{i}]: chybí url")
        elif not URL_RE.match(str(u)):
            err(f, f"{where}.zdroje[{i}]: url není platná adresa — {u!r}")
        elif "example.com" in str(u) or "priklad" in str(u):
            err(f, f"{where}.zdroje[{i}]: zástupná url — {u!r}")
        if not s.get("datum"):
            warn(f, f"{where}.zdroje[{i}]: chybí datum")


def check_pripady(f, items, where):
    if items is None: return
    if not isinstance(items, list):
        err(f, f"{where}: musí být seznam"); return
    for i, c in enumerate(items):
        w = f"{where}[{i}]"
        if not isinstance(c, dict):
            err(f, f"{w}: musí být objekt"); continue
        if not c.get("nazev"): err(f, f"{w}: chybí nazev")
        st = c.get("stav")
        if not st:
            err(f, f"{w}: chybí povinné pole 'stav' — obvinění bez výsledku se neuvádí")
        elif st not in STAVY:
            err(f, f"{w}: neznámý stav {st!r}, povolené: {sorted(STAVY)}")
        t = c.get("typ")
        if t and t not in TYPY_PRIPADU:
            warn(f, f"{w}: neznámý typ {t!r}")
        z = c.get("zavaznost")
        if z and z not in ZAVAZNOST:
            warn(f, f"{w}: neznámá zavaznost {z!r}")
        check_sources(f, c.get("zdroje"), w)
        if not c.get("zdroje"):
            err(f, f"{w}: kauza BEZ zdroje — nesmí být v datech")


def check_score(f, val, where, lo=0, hi=5):
    if val is None: return
    if not isinstance(val, (int, float)):
        err(f, f"{where}: skóre musí být číslo nebo null, je {val!r}")
    elif not lo <= val <= hi:
        err(f, f"{where}: skóre {val} mimo rozsah {lo}–{hi}")


# ------------------------------------------------------------------ parties
def validate_party(p: Path):
    d = load(p)
    if d is None: return
    f = p.name
    for k in ["slug","assembly_id","list_cislo","nazev"]:
        if not d.get(k) and d.get(k) != 0:
            err(f, f"chybí povinné pole {k}")
    a, c = d.get("assembly_id"), d.get("list_cislo")
    if a and a not in ASM:
        err(f, f"neznámé assembly_id {a!r} — není v data/core/assemblies.json")
    if a and isinstance(c, int) and (a, c) not in LIST_KEYS:
        err(f, f"listina {a} č.{c} neexistuje v oficiálních datech ČSÚ")
    if d.get("slug") and p.stem != d["slug"]:
        warn(f, f"slug {d['slug']!r} ≠ název souboru {p.stem!r}")

    prog = d.get("program") or {}
    if prog.get("nalezen") is None:
        warn(f, "program.nalezen neuvedeno")
    if prog.get("nalezen"):
        check_sources(f, prog.get("zdroje"), "program")
        if not prog.get("shrnuti"): warn(f, "program.nalezen=true, ale chybí shrnuti")
        prio = prog.get("priority") or []
        if not prio:
            warn(f, "program.nalezen=true, ale žádné priority[]")
        for i, pr in enumerate(prio):
            w = f"program.priority[{i}]"
            if not isinstance(pr, dict):
                err(f, f"{w}: musí být objekt"); continue
            if not pr.get("nazev"): err(f, f"{w}: chybí nazev")
            ob = pr.get("oblast")
            if not ob: err(f, f"{w}: chybí oblast")
            elif ob not in OBLASTI:
                err(f, f"{w}: neznámá oblast {ob!r}, povolené: {sorted(OBLASTI)}")
            if pr.get("konkretnost") not in {None,"vysoka","stredni","nizka"}:
                warn(f, f"{w}: neznámá konkretnost {pr.get('konkretnost')!r}")
            u = pr.get("zdroj_url")
            if u and not URL_RE.match(str(u)):
                err(f, f"{w}.zdroj_url není platná adresa — {u!r}")

    h = d.get("hodnoceni") or {}
    for k in ["konkretnost_programu","doveryhodnost_plneni","transparentnost"]:
        check_score(f, h.get(k), f"hodnoceni.{k}")
    if any(h.get(k) is not None for k in h) and not h.get("oduvodneni"):
        warn(f, "hodnoceni bez oduvodneni")

    check_pripady(f, d.get("kontroverze"), "kontroverze")

    bil = d.get("bilance_2022_2026") or {}
    self_sourced = 0
    for key in ["splnene_sliby","castecne","nesplnene_sliby"]:
        for i, s in enumerate(bil.get(key) or []):
            if isinstance(s, dict) and s.get("zdroj_url"):
                u = str(s["zdroj_url"])
                if not URL_RE.match(u):
                    err(f, f"bilance_2022_2026.{key}[{i}].zdroj_url neplatná — {u!r}")
                elif PARTY_DOMAIN_RE.search(u):
                    self_sourced += 1
            elif isinstance(s, dict):
                warn(f, f"bilance_2022_2026.{key}[{i}]: bez zdroj_url")
    # strana si nesmí vysoké skóre doložit jen vlastním webem
    if self_sourced and (h.get("doveryhodnost_plneni") or 0) >= 4:
        warn(f, f"doveryhodnost_plneni={h.get('doveryhodnost_plneni')} se opírá "
                f"o {self_sourced}× stranický zdroj — pro 4–5 je potřeba nezávislé doložení")

    if d.get("confidence") not in CONFIDENCE:
        warn(f, f"confidence {d.get('confidence')!r} není z {sorted(CONFIDENCE)}")
    if not d.get("posledni_aktualizace"):
        warn(f, "chybí posledni_aktualizace")


# ------------------------------------------------------------------ people
def validate_person(p: Path):
    d = load(p)
    if d is None: return
    f = p.name
    for k in ["slug","name_key","cele_jmeno"]:
        if not d.get(k):
            err(f, f"chybí povinné pole {k}")
    nk = d.get("name_key")
    if nk and nk not in NAME_KEYS:
        err(f, f"name_key {nk!r} NENÍ mezi kandidáty ČSÚ — buď je chybně zapsaný, "
               f"nebo ta osoba nekandiduje")
    kand = d.get("kandidatury_2026") or []
    if not kand:
        warn(f, "chybí kandidatury_2026[]")
    for i, k in enumerate(kand):
        if not isinstance(k, dict): continue
        a, c = k.get("assembly_id"), k.get("list_cislo")
        if a and a not in ASM:
            err(f, f"kandidatury_2026[{i}]: neznámé assembly_id {a!r}")
        if a and isinstance(c, int) and (a, c) not in LIST_KEYS:
            err(f, f"kandidatury_2026[{i}]: listina {a} č.{c} neexistuje v datech ČSÚ")
        if nk and a and a not in NAME_KEYS.get(nk, set()):
            err(f, f"kandidatury_2026[{i}]: {nk} nekandiduje v {a} podle dat ČSÚ")
        por = k.get("poradi")
        if not por:
            # bez pořadí jde dossier propojit jen u jedinečného jména
            n = NK_COUNT.get((a, nk), 0)
            if n > 1:
                err(f, f"kandidatury_2026[{i}]: chybí 'poradi' a jméno {nk!r} "
                       f"má v {a} {n} kandidátů — dossier by se mohl přiřadit "
                       f"jmenovci. Doplň pořadí na listině.")
            else:
                warn(f, f"kandidatury_2026[{i}]: chybí 'poradi'")
        elif a and isinstance(c, int) and (a, c, por) not in POS:
            err(f, f"kandidatury_2026[{i}]: na listině {a} č.{c} není pořadí {por}")

    for i, h in enumerate(d.get("politicka_historie") or []):
        if isinstance(h, dict):
            if not h.get("funkce"): warn(f, f"politicka_historie[{i}]: chybí funkce")
            u = h.get("zdroj_url")
            if u and not URL_RE.match(str(u)):
                err(f, f"politicka_historie[{i}].zdroj_url neplatná — {u!r}")

    for i, v in enumerate(d.get("vysledky") or []):
        if isinstance(v, dict):
            if v.get("stav") not in {None,"dokonceno","rozpracovano","zastaveno",
                                     "zpozdeno","selhalo"}:
                warn(f, f"vysledky[{i}]: neznámý stav {v.get('stav')!r}")
            check_sources(f, v.get("zdroje"), f"vysledky[{i}]")

    check_pripady(f, d.get("pripady"), "pripady")
    ps = d.get("plneni_slibu") or {}
    check_score(f, ps.get("skore"), "plneni_slibu.skore")
    if ps.get("skore") is not None and not ps.get("oduvodneni"):
        warn(f, "plneni_slibu.skore bez oduvodneni")
    check_sources(f, d.get("zdroje"), "zdroje", required=False)
    if d.get("confidence") not in CONFIDENCE:
        warn(f, f"confidence {d.get('confidence')!r} není z {sorted(CONFIDENCE)}")


# ------------------------------------------------------------------ districts
def validate_district(p: Path):
    d = load(p)
    if d is None: return
    f = p.name
    a = d.get("assembly_id")
    if not a: err(f, "chybí assembly_id")
    elif a not in ASM: err(f, f"neznámé assembly_id {a!r}")
    elif p.stem != a: warn(f, f"název souboru {p.stem!r} ≠ assembly_id {a!r}")
    if not d.get("charakteristika"): warn(f, "chybí charakteristika")
    check_pripady(f, d.get("kontroverze_mc"), "kontroverze_mc")
    for i, t in enumerate(d.get("klicova_temata") or []):
        if isinstance(t, dict):
            check_sources(f, t.get("zdroje"), f"klicova_temata[{i}]")
    if d.get("confidence") not in CONFIDENCE:
        warn(f, f"confidence {d.get('confidence')!r} není z {sorted(CONFIDENCE)}")


def validate_issue(p: Path):
    d = load(p)
    if d is None: return
    f = p.name
    if not d.get("nazev"): warn(f, "chybí nazev")
    for i, x in enumerate(d.get("fakta") or []):
        if isinstance(x, dict):
            u = x.get("zdroj_url")
            if not u: err(f, f"fakta[{i}]: chybí zdroj_url — fakt bez zdroje nepatří do dat")
            elif not URL_RE.match(str(u)):
                err(f, f"fakta[{i}].zdroj_url neplatná — {u!r}")
    for i, x in enumerate(d.get("pozice_stran") or []):
        if isinstance(x, dict) and x.get("list_slug"):
            if not (RES / "parties" / f"{x['list_slug']}.json").exists():
                warn(f, f"pozice_stran[{i}]: odkaz na neexistující listinu {x['list_slug']!r}")


def main():
    counts = {}
    for sub, fn in [("parties", validate_party), ("people", validate_person),
                    ("districts", validate_district), ("issues", validate_issue)]:
        files = sorted((RES / sub).glob("*.json"))
        counts[sub] = len(files)
        for p in files:
            fn(p)

    print("Zkontrolováno: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    print()
    for w in WARN: print(w)
    if WARN: print()
    for e in ERR: print(e)
    print()
    print(f"Výsledek: {len(ERR)} chyb, {len(WARN)} varování")
    if ERR:
        print("\nChyby je nutné opravit — blokují build dashboardu.")
    strict = "--strict" in sys.argv
    sys.exit(1 if (ERR or (strict and WARN)) else 0)


if __name__ == "__main__":
    main()

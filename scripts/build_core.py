#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staví data/core/*.json z otevřených dat ČSÚ (komunální volby 2026 + 2022).
Vygenerovaná data se NEUPRAVUJÍ ručně — ruční/agentní obsah patří do data/research/.
"""
from __future__ import annotations
import csv, json, os, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
OUT = ROOT / "data" / "core"
PRAHA_KRAJ = "1100"
MAGISTRAT = "554782"
ENC = "cp1250"


def rows(path: Path):
    with open(path, encoding=ENC, newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            yield {k: (v.strip() if isinstance(v, str) else v) for k, v in r.items() if k}


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-{2,}", "-", s)


def norm_name(first: str, last: str) -> str:
    return slugify(f"{last} {first}")


def i(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def f(v, default=None):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- číselníky
def load_codebooks(year: str):
    base = CACHE / f"kv{year}_cis" / "csv"
    nstrana = {r["NSTRANA"]: r["NAZEV_STRN"] for r in rows(base / "cns.csv")}
    nstrana_abbr = {r["NSTRANA"]: r["ZKRATKAN8"] for r in rows(base / "cns.csv")}
    pstrana = {r["PSTRANA"]: r["NAZEV_STRP"] for r in rows(base / "cpp.csv")}
    pstrana_abbr = {r["PSTRANA"]: r["ZKRATKAP8"] for r in rows(base / "cpp.csv")}
    vstrana = {r["VSTRANA"]: r for r in rows(base / "cvs.csv")}
    slozeni = defaultdict(list)
    for r in rows(base / "cvs_slozeni.csv"):
        slozeni[r["VSTRANA"]].append(r["NSTRANA"])
    return dict(nstrana=nstrana, nstrana_abbr=nstrana_abbr, pstrana=pstrana,
                pstrana_abbr=pstrana_abbr, vstrana=vstrana, slozeni=dict(slozeni))


# ---------------------------------------------------------------- zastupitelstva
def build_assemblies(cb):
    src = CACHE / "kv2026_reg" / "csv" / "kvrzcoco.csv"
    seen, out = set(), []
    for r in rows(src):
        if r["KRAJ"] != PRAHA_KRAJ or r["KODZASTUP"] in seen:
            continue
        seen.add(r["KODZASTUP"])
        kod, name = r["KODZASTUP"], r["NAZEVZAST"]
        is_mag = kod == MAGISTRAT
        display = "Magistrát hl. m. Prahy" if is_mag else name
        num = None
        m = re.fullmatch(r"Praha (\d+)", name)
        if m:
            num = int(m.group(1))
        out.append({
            "id": "magistrat" if is_mag else f"mc-{slugify(name)}",
            "kodzastup": kod,
            "nazev": display,
            "nazev_csu": name,
            "typ": "magistrat" if is_mag else "mestska_cast",
            "cislo_mc": num,
            "mandaty": i(r["MANDATY"]),
            "pocet_obyvatel": i(r["POCOBYV"]),
            # hloubka kvalitativního výzkumu: magistrát + Praha 1-22 = "full"
            "uroven_vyzkumu": "full" if (is_mag or num is not None) else "zakladni",
        })
    out.sort(key=lambda a: (a["typ"] != "magistrat", a["cislo_mc"] is None,
                            a["cislo_mc"] or 0, a["nazev"]))
    return out


# ---------------------------------------------------------------- kandidátní listiny
def build_lists(cb, assemblies):
    by_kod = {a["kodzastup"]: a for a in assemblies}
    src = CACHE / "kv2026_reg" / "csv" / "kvros.csv"
    out = []
    for r in rows(src):
        if r["KRAJ"] if "KRAJ" in r else None:
            pass
        kod = r["KODZASTUP"]
        if kod not in by_kod:
            continue
        v = r["VSTRANA"]
        members = cb["slozeni"].get(v, [])
        vinfo = cb["vstrana"].get(v, {})
        typ_vs = vinfo.get("TYPVS", "")
        out.append({
            "id": f"{by_kod[kod]['id']}::{r['POR_STR_HL']}",
            "assembly_id": by_kod[kod]["id"],
            "kodzastup": kod,
            "cislo": i(r["POR_STR_HL"]),           # číslo na hlasovacím lístku
            "nazev": r["NAZEVCELK"],
            "zkratka": r["ZKRATKAO8"],
            "zkratka30": r["ZKRATKAO30"],
            "vstrana": v,
            "typ": {"S": "strana", "K": "koalice", "N": "nezavisly",
                    "H": "sdruzeni"}.get(typ_vs, typ_vs or "jine"),
            "pocet_subjektu": i(r["POCSTR_SLO"]),
            "slozeni": [{"kod": m, "nazev": cb["nstrana"].get(m, m),
                         "zkratka": cb["nstrana_abbr"].get(m, m)} for m in members],
            "research_slug": None,                  # doplní build_site.py párováním
        })
    out.sort(key=lambda x: (x["assembly_id"] != "magistrat", x["assembly_id"], x["cislo"]))
    return out


# ---------------------------------------------------------------- kandidáti
def build_candidates(cb, assemblies, lists):
    by_kod = {a["kodzastup"]: a for a in assemblies}
    list_by_key = {(l["kodzastup"], l["cislo"]): l for l in lists}
    src = CACHE / "kv2026_reg" / "csv" / "kvrk.csv"
    out = []
    for r in rows(src):
        kod = r["KODZASTUP"]
        if kod not in by_kod:
            continue
        lst = list_by_key.get((kod, i(r["POR_STR_HL"])))
        first, last = r["JMENO"], r["PRIJMENI"]
        out.append({
            "id": f"{kod}-{r['POR_STR_HL']}-{r['PORCISLO']}",
            "assembly_id": by_kod[kod]["id"],
            "list_id": lst["id"] if lst else None,
            "list_nazev": lst["nazev"] if lst else None,
            "poradi": i(r["PORCISLO"]),
            "jmeno": first,
            "prijmeni": last,
            "cele_jmeno": " ".join(x for x in [r["TITULPRED"], first, last] if x)
                          + (f", {r['TITULZA']}" if r["TITULZA"] else ""),
            "name_key": norm_name(first, last),
            "titul_pred": r["TITULPRED"] or None,
            "titul_za": r["TITULZA"] or None,
            "vek": i(r["VEK"], None),
            "povolani": r["POVOLANI"] or None,
            "bydliste": r["BYDLISTEN"] or None,
            "prislusnost": cb["pstrana"].get(r["PSTRANA"]),       # členství ve straně
            "prislusnost_zkratka": cb["pstrana_abbr"].get(r["PSTRANA"]),
            "navrhujici": cb["nstrana"].get(r["NSTRANA"]),        # navrhující strana
            "navrhujici_zkratka": cb["nstrana_abbr"].get(r["NSTRANA"]),
            "platnost": r["PLATNOST"] == "A",
            "dossier_slug": None,                                  # doplní build_site.py
        })
    out.sort(key=lambda c: (c["assembly_id"] != "magistrat", c["assembly_id"],
                            c["list_id"] or "", c["poradi"]))
    return out


# ---------------------------------------------------------------- 2022: výsledky + mandáty
def build_2022(cb22, assemblies):
    by_kod = {a["kodzastup"]: a for a in assemblies}
    res_src = CACHE / "kv2022_reg" / "csv" / "kvros.csv"
    kand_src = CACHE / "kv2022_reg" / "csv" / "kvrk.csv"

    results = []
    for r in rows(res_src):
        kod = r["KODZASTUP"]
        if kod not in by_kod:
            continue
        v = r["VSTRANA"]
        results.append({
            "assembly_id": by_kod[kod]["id"],
            "kodzastup": kod,
            "cislo": i(r["POR_STR_HL"]),
            "nazev": r["NAZEVCELK"],
            "zkratka": r["ZKRATKAO8"],
            "vstrana": v,
            "slozeni": [{"kod": m, "nazev": cb22["nstrana"].get(m, m),
                         "zkratka": cb22["nstrana_abbr"].get(m, m)}
                        for m in cb22["slozeni"].get(v, [])],
            "hlasy": i(r["HLASY_STR"], None),
            "procent": f(r["PROCHLSTR"]),
            "mandaty": i(r["MAND_STR"], 0),
        })

    elected = []
    for r in rows(kand_src):
        kod = r["KODZASTUP"]
        if kod not in by_kod or r["MANDAT"] != "A":
            continue
        first, last = r["JMENO"], r["PRIJMENI"]
        elected.append({
            "assembly_id": by_kod[kod]["id"],
            "kodzastup": kod,
            "name_key": norm_name(first, last),
            "cele_jmeno": " ".join(x for x in [r["TITULPRED"], first, last] if x),
            "jmeno": first, "prijmeni": last,
            "vek_2022": i(r["VEK"], None),
            "zvolen_za": r["NAZEVCELK"] if "NAZEVCELK" in r else None,
            "navrhujici_2022": cb22["nstrana"].get(r["NSTRANA"]),
            "prislusnost_2022": cb22["pstrana"].get(r["PSTRANA"]),
            "poradi_2022": i(r["PORCISLO"]),
            "preferencni_hlasy_2022": i(r["POCHLASU"], None),
            "procent_hlasu_2022": f(r["POCPROCVSE"]),
        })
    results.sort(key=lambda x: (x["assembly_id"] != "magistrat", x["assembly_id"],
                               -(x["procent"] or 0)))
    return results, elected


def mark_incumbents(candidates, elected_2022):
    """Spáruje kandidáty 2026 se zvolenými 2022 (stejné zastupitelstvo, jméno, věk +4±1)."""
    idx = defaultdict(list)
    for e in elected_2022:
        idx[(e["assembly_id"], e["name_key"])].append(e)
    matched = 0
    for c in candidates:
        hits = idx.get((c["assembly_id"], c["name_key"]), [])
        hit = None
        for h in hits:
            if c["vek"] and h["vek_2022"] and abs((c["vek"] - h["vek_2022"]) - 4) <= 1:
                hit = h
                break
        if hit is None and len(hits) == 1:
            hit = hits[0]
        if hit:
            matched += 1
            c["inkumbent_2022"] = {
                "zvolen_za": hit["navrhujici_2022"],
                "poradi_2022": hit["poradi_2022"],
                "preferencni_hlasy_2022": hit["preferencni_hlasy_2022"],
                "procent_hlasu_2022": hit["procent_hlasu_2022"],
            }
        else:
            c["inkumbent_2022"] = None
    return matched


def main():
    cb26 = load_codebooks("2026")
    cb22 = load_codebooks("2022")
    OUT.mkdir(parents=True, exist_ok=True)

    assemblies = build_assemblies(cb26)
    lists = build_lists(cb26, assemblies)
    candidates = build_candidates(cb26, assemblies, lists)
    res22, elected22 = build_2022(cb22, assemblies)
    n_inc = mark_incumbents(candidates, elected22)

    # doplň do zastupitelstev souhrnné počty
    cnt_l, cnt_c = defaultdict(int), defaultdict(int)
    for l in lists:
        cnt_l[l["assembly_id"]] += 1
    for c in candidates:
        cnt_c[c["assembly_id"]] += 1
    for a in assemblies:
        a["pocet_listin"] = cnt_l[a["id"]]
        a["pocet_kandidatu"] = cnt_c[a["id"]]

    meta = {
        "schema_version": 1,
        "nazev": "Komunální volby v Praze 2026",
        "volby": {
            "datum": ["2026-10-09", "2026-10-10"],
            "hodiny": {"2026-10-09": "14:00–22:00", "2026-10-10": "08:00–14:00"},
            "poznamka": "Souběžně probíhá 1. kolo senátních voleb ve vybraných obvodech.",
        },
        "zdroje_dat": [
            {"nazev": "ČSÚ – otevřená data KV2026 (registrace, stav k 23. 9. 2026)",
             "url": "https://volby.gov.cz/opendata/kv2026/kv2026_opendata.htm"},
            {"nazev": "ČSÚ – otevřená data KV2022 (výsledky a mandáty)",
             "url": "https://volby.gov.cz/opendata/kv2022/kv2022_opendata.htm"},
        ],
        "souhrn": {
            "pocet_zastupitelstev": len(assemblies),
            "pocet_listin": len(lists),
            "pocet_kandidatu": len(candidates),
            "mandatu_celkem": sum(a["mandaty"] for a in assemblies),
            "inkumbentu_2022_znovu_kandiduje": n_inc,
        },
    }

    files = {
        "meta.json": meta,
        "assemblies.json": assemblies,
        "lists_2026.json": lists,
        "candidates_2026.json": candidates,
        "results_2022.json": res22,
        "elected_2022.json": elected22,
    }
    for name, payload in files.items():
        (OUT / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  ✓ data/core/{name}")

    print(f"\nZastupitelstva: {len(assemblies)} | listiny: {len(lists)} | "
          f"kandidáti: {len(candidates)} | inkumbenti 2022 znovu na listině: {n_inc}")


if __name__ == "__main__":
    main()

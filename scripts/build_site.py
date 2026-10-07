#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slučuje data/core/ (ČSÚ) + data/research/ (rešerše) do dashboard/data/.
Výstup je optimalizovaný pro načítání v prohlížeči: malý index + líně
dotahované soubory kandidátů po zastupitelstvech.
"""
from __future__ import annotations
import json, re, shutil, sys, unicodedata
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "data" / "core"
RES = ROOT / "data" / "research"
OUT = ROOT / "dashboard" / "data"


def rd(p: Path, default=None):
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  !! nevalidní JSON, přeskakuji: {p.name} ({e})")
        return default


def wr(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
                 encoding="utf-8")
    return p.stat().st_size


def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower())



PARTY_DOMAIN_RE = re.compile(
    r"(pirati|\bods\b|ods\.cz|top09|topka|stan-|starostove|ano2011|anobudelip|spd\.|"
    r"motoriste|praha-?sobe|prahasobe|jsmepraha|senpro|levice|svobodni|patrioti|"
    r"zeleni|kdu|kscm|cssd|tempoplan|janhusbauer)", re.I)


def _host(u):
    try:
        return (urlparse(u).hostname or "").replace("www.", "")
    except Exception:
        return ""


def mark_self_sourced(bil, web):
    """Označí sliby doložené webem samotné strany.

    Strana, která si na vlastním webu napíše, že slib splnila, není nestranný
    důkaz. Nevyřazujeme to — u lokální politiky je to často jediný dostupný
    zdroj — ale čtenář to musí vidět, aby si tvrzení mohl zvážit sám.
    """
    own = _host(web or "")
    for key in ("splnene_sliby", "castecne", "nesplnene_sliby"):
        for item in (bil.get(key) or []):
            if not isinstance(item, dict):
                continue
            h = _host(item.get("zdroj_url") or "")
            item["zdroj_strana"] = bool(h and ((own and h == own)
                                               or PARTY_DOMAIN_RE.search(h)))
    return bil


def _members(x):
    """Množina zkratek členských stran, podle nichž se páruje napříč roky."""
    return {(m.get("zkratka") or "").strip().upper()
            for m in (x.get("slozeni") or []) if m.get("zkratka")} - {"NK", ""}


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def match_2022(l, prev_rows):
    """Spáruje letošní listinu s výsledkem 2022 téhož subjektu.

    Kódy voleb. stran se mezi roky mění, a koalice mění složení i název, takže
    se páruje v pořadí: shodný kód → překryv členských stran → shodný
    normalizovaný název → shodná zkratka. Překryv se počítá Jaccardovou mírou
    a vyžaduje aspoň polovinu, aby se SPOLU (ODS+TOP 09) nespárovalo s listinou,
    kde je ODS jen jedním z mnoha členů.
    """
    for p in prev_rows:
        if p["vstrana"] == l["vstrana"]:
            return p
    mine = _members(l)
    if mine:
        best, best_j = None, 0.0
        for p in prev_rows:
            theirs = _members(p)
            if not theirs:
                continue
            j = len(mine & theirs) / len(mine | theirs)
            if j > best_j:
                best, best_j = p, j
        if best is not None and best_j >= 0.5:
            return best
    ln = _norm(l["nazev"])
    for p in prev_rows:
        if ln and _norm(p["nazev"]) == ln:
            return p
    for p in prev_rows:
        if l["zkratka"] and p["zkratka"] == l["zkratka"]:
            return p
    return None


def main():
    meta = rd(CORE / "meta.json", {})
    assemblies = rd(CORE / "assemblies.json", [])
    lists = rd(CORE / "lists_2026.json", [])
    candidates = rd(CORE / "candidates_2026.json", [])
    res22 = rd(CORE / "results_2022.json", [])
    if not assemblies:
        print("✗ chybí data/core — spusť scripts/build_core.py"); sys.exit(2)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # ---------------------------------------------------------- rešerše
    parties_res = {}
    for p in sorted((RES / "parties").glob("*.json")):
        d = rd(p)
        if isinstance(d, dict) and d.get("assembly_id") is not None \
                and d.get("list_cislo") is not None:
            parties_res[(d["assembly_id"], d["list_cislo"])] = d

    people_res = {}
    for p in sorted((RES / "people").glob("*.json")):
        d = rd(p)
        if isinstance(d, dict) and d.get("slug"):
            people_res[d["slug"]] = d

    districts_res = {}
    for p in sorted((RES / "districts").glob("*.json")):
        d = rd(p)
        if isinstance(d, dict) and d.get("assembly_id"):
            districts_res[d["assembly_id"]] = d

    issues = {}
    for p in sorted((RES / "issues").glob("*.json")):
        d = rd(p)
        if isinstance(d, dict):
            issues[d.get("slug") or p.stem] = d

    # ------------------------------------------------------------------
    # Propojení dossierů s konkrétními kandidáty.
    #
    # name_key (příjmení+jméno) NENÍ jedinečný: v Praze ho sdílí 201 různých
    # lidí a ve 25 případech i uvnitř jednoho zastupitelstva — na kandidátce
    # Prahy 11 jsou dokonce dva Ladislavové Kosovi na téže listině. Propojovat
    # podle jména by znamenalo riskovat, že se kauza přiřadí nesprávné osobě.
    #
    # Proto se páruje primárně přes (assembly_id, list_cislo, poradi)
    # z `kandidatury_2026`, což kandidáta určuje jednoznačně. Jméno slouží
    # jen jako záloha, a to výhradně tam, kde je v daném zastupitelstvu
    # jediné — jinak se nepropojí nic a případ se vypíše jako nejednoznačný.
    # ------------------------------------------------------------------
    cand_by_pos = {(c["assembly_id"], c["list_id"], c["poradi"]): c
                   for c in candidates if c["list_id"]}
    list_cislo_by_id = {l["id"]: l["cislo"] for l in lists}
    pos_index = {}
    for c in candidates:
        if c["list_id"]:
            pos_index[(c["assembly_id"], list_cislo_by_id[c["list_id"]],
                       c["poradi"])] = c["id"]
    namekey_count = defaultdict(list)
    for c in candidates:
        namekey_count[(c["assembly_id"], c["name_key"])].append(c["id"])

    by_candidate = defaultdict(list)      # candidate id -> [person slug]
    ambiguous, unmatched = [], []
    for slug, d in people_res.items():
        nk = d.get("name_key")
        hits = []
        for k in (d.get("kandidatury_2026") or []):
            a, cis, por = k.get("assembly_id"), k.get("list_cislo"), k.get("poradi")
            cid = pos_index.get((a, cis, por)) if por else None
            if cid:
                hits.append(cid); continue
            # bez pořadí: zkus jméno, ale jen když je v tom zastupitelstvu jediné
            same = namekey_count.get((a, nk), [])
            if len(same) == 1:
                hits.append(same[0])
            elif len(same) > 1:
                ambiguous.append((slug, a, nk, len(same)))
        if not hits and nk:
            # úplná záloha: jméno jedinečné v rámci celé Prahy
            everywhere = [cid for (a, k), ids in namekey_count.items()
                          if k == nk for cid in ids]
            if len(everywhere) == 1:
                hits = everywhere
            else:
                unmatched.append((slug, nk, len(everywhere)))
        for cid in dict.fromkeys(hits):
            by_candidate[cid].append(slug)

    # zpětně: name_key -> slugy, jen pro lídry v přehledu listin
    by_namekey = defaultdict(list)
    for slug, d in people_res.items():
        if d.get("name_key"):
            by_namekey[d["name_key"]].append(slug)

    # ---------------------------------------------------------- listiny
    r22_by_asm = defaultdict(list)
    for r in res22:
        r22_by_asm[r["assembly_id"]].append(r)

    cand_by_list = defaultdict(list)
    cand_by_asm = defaultdict(list)
    for c in candidates:
        cand_by_list[c["list_id"]].append(c)
        cand_by_asm[c["assembly_id"]].append(c)

    lists_by_asm = defaultdict(list)
    merged_lists = []
    for l in lists:
        key = (l["assembly_id"], l["cislo"])
        r = parties_res.get(key)
        cs = sorted(cand_by_list[l["id"]], key=lambda x: x["poradi"])
        lead = cs[0] if cs else None
        # 2022 výsledek téhož subjektu (párování podle VSTRANA, pak podle zkratky)
        prev = match_2022(l, r22_by_asm[l["assembly_id"]])
        item = {
            **{k: l[k] for k in ["id","assembly_id","cislo","nazev","zkratka",
                                 "zkratka30","typ","pocet_subjektu","slozeni"]},
            "pocet_kandidatu": len(cs),
            "lidr": ({"cele_jmeno": lead["cele_jmeno"], "vek": lead["vek"],
                      "povolani": lead["povolani"], "name_key": lead["name_key"],
                      "person_slugy": by_candidate.get(lead["id"], []),
                      "inkumbent_2022": bool(lead["inkumbent_2022"])}
                     if lead else None),
            "inkumbentu_2022": sum(1 for c in cs if c["inkumbent_2022"]),
            "vysledek_2022": ({"procent": prev["procent"], "mandaty": prev["mandaty"],
                               "hlasy": prev["hlasy"], "nazev": prev["nazev"]}
                              if prev else None),
            "research": None,
        }
        if r:
            item["research"] = {
                "slug": r.get("slug"),
                "web": r.get("web"),
                "program": r.get("program"),
                "ideologie": r.get("ideologie"),
                "bilance_2022_2026": mark_self_sourced(
                    r.get("bilance_2022_2026") or {}, r.get("web")),
                "kontroverze": r.get("kontroverze") or [],
                "hodnoceni": r.get("hodnoceni"),
                "lidri": r.get("lidri") or [],
                "mezery_v_datech": r.get("mezery_v_datech") or [],
                "confidence": r.get("confidence"),
                "posledni_aktualizace": r.get("posledni_aktualizace"),
            }
        merged_lists.append(item)
        lists_by_asm[l["assembly_id"]].append(item)

    # ---------------------------------------------------------- zastupitelstva
    asm_index = []
    for a in assemblies:
        ls = lists_by_asm[a["id"]]
        researched = sum(1 for x in ls if x["research"])
        asm_index.append({
            **a,
            "pocet_listin": len(ls),
            "listin_s_resersi": researched,
            "ma_kontext_mc": a["id"] in districts_res,
            "mandaty_2022_celkem": sum(r["mandaty"] for r in r22_by_asm[a["id"]]),
        })

    # per-assembly soubory: kandidáti (líné načtení)
    sizes = {}
    for a in assemblies:
        cs = sorted(cand_by_asm[a["id"]], key=lambda c: (c["list_id"] or "", c["poradi"]))
        rows = []
        for c in cs:
            rows.append({
                "id": c["id"], "list_id": c["list_id"], "poradi": c["poradi"],
                "cele_jmeno": c["cele_jmeno"], "name_key": c["name_key"],
                "vek": c["vek"], "povolani": c["povolani"],
                "prislusnost": c["prislusnost_zkratka"],
                "navrhujici": c["navrhujici_zkratka"],
                "inkumbent_2022": c["inkumbent_2022"],
                "person_slugy": by_candidate.get(c["id"], []),
            })
        sizes[a["id"]] = wr(OUT / "candidates" / f"{a['id']}.json", rows)

    # ---------------------------------------------------------- výstupy

    # ------------------------------------------------------------------
    # Rejstřík osob pro filtrování.
    #
    # Stranická příslušnost se bere z dat ČSÚ, ne z textového pole `strana`
    # v rešerši: tam vzniklo 70 různých zápisů pro necelou třicítku stran
    # („ODS“ i „Občanská demokratická strana“, „BEZPP“ i „Bez politické
    # příslušnosti“, „AUTO“ i „Motoristé sobě“). Číselník ČSÚ je normalizovaný,
    # takže filtr podle něj dává smysluplné a úplné skupiny.
    # ------------------------------------------------------------------
    cand_by_id = {c["id"]: c for c in candidates}
    slug_to_cands = defaultdict(list)
    for cid, slugs in by_candidate.items():
        for sl in slugs:
            slug_to_cands[sl].append(cand_by_id[cid])

    HARD = {"odsouzen", "potvrzeno"}

    def people_index():
        rows = []
        for sl, d in people_res.items():
            cs = slug_to_cands.get(sl, [])
            strany = [c["prislusnost_zkratka"] for c in cs if c.get("prislusnost_zkratka")]
            strana = strany[0] if strany else None
            pripady = d.get("pripady") or []
            stavy = [c.get("stav") for c in pripady]
            rows.append({
                "slug": sl,
                "cele_jmeno": d.get("cele_jmeno"),
                "name_key": d.get("name_key"),
                # kanonická zkratka z ČSÚ pro filtr…
                "strana": strana or "—",
                # …a původní text z rešerše pro zobrazení v profilu
                "strana_text": d.get("strana"),
                "role": d.get("role"),
                "kauz": len(pripady),
                "kauz_potvrzenych": sum(1 for x in stavy if x in HARD),
                "kauz_probiha": sum(1 for x in stavy if x == "probiha"),
                "kandidatur": len(d.get("kandidatury_2026") or []),
                "_sort": d.get("name_key") or d.get("cele_jmeno") or "",
            })
        return rows

    stats = {
        **(meta.get("souhrn") or {}),
        "listin_s_resersi": sum(1 for x in merged_lists if x["research"]),
        "osobnich_dossieru": len(people_res),
        "dossieru_propojenych": len({s2 for v in by_candidate.values() for s2 in v}),
        "mc_s_kontextem": len(districts_res),
        "temat": len(issues),
        "doloz_kauz_celkem": sum(len(d.get("pripady") or []) for d in people_res.values())
                             + sum(len(d.get("kontroverze") or [])
                                   for d in parties_res.values()),
    }

    wr(OUT / "index.json", {
        "meta": meta, "statistiky": stats, "zastupitelstva": asm_index,
        "temata": [{"slug": k, "nazev": v.get("nazev") or k,
                    "popis": v.get("popis")} for k, v in sorted(issues.items())],
        # Řadí se podle name_key = "prijmeni-jmeno". Řadit podle `cele_jmeno`
        # by seřadilo podle akademického titulu, takže by se k sobě slepili
        # všichni „Bc.“, pak všichni „Ing.“ atd.
        "osoby_index": sorted(people_index(), key=lambda x: x["_sort"]),
    })
    wr(OUT / "lists.json", merged_lists)
    wr(OUT / "people.json", people_res)
    wr(OUT / "districts.json", districts_res)
    wr(OUT / "issues.json", issues)
    wr(OUT / "results_2022.json", res22)

    total = sum(p.stat().st_size for p in OUT.rglob("*.json"))
    print(f"  ✓ dashboard/data/ — {len(list(OUT.rglob('*.json')))} souborů, "
          f"{total/1024/1024:.2f} MB")
    print(f"    listiny: {len(merged_lists)} (s rešerší {stats['listin_s_resersi']}) | "
          f"osoby: {len(people_res)} | MČ kontext: {len(districts_res)} | "
          f"témata: {len(issues)}")
    if ambiguous:
        print(f"    ⚠ nejednoznačné jméno (dossier nepropojen, chybí pořadí "
              f"v kandidatury_2026): {len(ambiguous)}")
        for slug, a, nk, n in ambiguous[:6]:
            print(f"        {slug}: {nk} v {a} odpovídá {n} kandidátům")
    if unmatched:
        print(f"    ⚠ dossier bez kandidáta v datech ČSÚ: {len(unmatched)}")
        for slug, nk, n in unmatched[:6]:
            print(f"        {slug} ({nk}) — nalezeno {n} shod")
    miss = [a["nazev"] for a in asm_index
            if a["uroven_vyzkumu"] == "full" and a["listin_s_resersi"] == 0]
    if miss:
        print(f"    ⚠ bez rešerše (úroveň full): {', '.join(miss)}")


if __name__ == "__main__":
    main()

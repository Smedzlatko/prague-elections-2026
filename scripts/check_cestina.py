#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Typografická a jazyková kontrola textů v data/research/.

Nehledá pravopis (na to je potřeba slovník), ale mechanické prohřešky, kterých
se modely i lidé dopouštějí opakovaně: dvojité mezery, mezera před interpunkcí,
rovné uvozovky, tři tečky místo výpustky, spojovník místo pomlčky, chybějící
tečka na konci odstavce, nezlomitelné mezery u zkratek.

    python3 scripts/check_cestina.py            # souhrn
    python3 scripts/check_cestina.py --fix      # opraví, co lze opravit bezpečně
    python3 scripts/check_cestina.py --show 40  # vypíše konkrétní nálezy
"""
from __future__ import annotations
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "data" / "research"

# Pole, která jsou skutečně prózou a mají se kontrolovat.
PROSE_KEYS = {
    "popis", "shrnuti", "profil", "oduvodneni", "charakteristika", "role",
    "dukaz", "hodnoceni", "poznamka", "kontext", "pozice", "tvrzeni",
    "reakce_dotcene_osoby", "proc_zalezi", "slib", "vysledek", "nazev",
    "text", "dusledek", "chyba", "zavazek",
}
# Pole, která prózou nejsou (URL, slugy, kódy) — ty se nikdy nekontrolují.
SRC_KEYS = {"zdroje", "citace"}
SKIP_KEYS = {"url", "slug", "name_key", "zdroj_url", "list_slug", "assembly_id",
             "web", "registr_oznameni_url", "metodika", "id"}

CHECKS = [
    ("dvojitá mezera",        re.compile(r"[^\S\n]{2,}")),
    ("mezera před interpunkcí", re.compile(r"\s+[,.;:!?](?:\s|$)")),
    ("chybí mezera po čárce", re.compile(r",(?=[A-Za-zÁ-Žá-ž])")),
    ("tři tečky místo …",     re.compile(r"\.\.\.")),
    ("rovné uvozovky",        re.compile(r"[\"']")),
    ("spojovník místo pomlčky", re.compile(r"\s-\s")),
    ("mezera před závorkou",  re.compile(r"\(\s|\s\)")),
    ("zdvojená interpunkce",  re.compile(r"(,,|;;|::|\.\.(?!\.)|,\.)")),
]

# Bezpečné opravy: jednoznačné, nemohou změnit význam.
FIXES = [
    (re.compile(r"[^\S\n]{2,}"), " "),
    (re.compile(r"\s+([,.;:!?])"), r"\1"),
    (re.compile(r"\.\.\."), "…"),
    (re.compile(r"(?<=\s)-(?=\s)"), "–"),   # česká pomlčka je en dash
    (re.compile(r"\(\s+"), "("),
    (re.compile(r"\s+\)"), ")"),
    (re.compile(r",(?=[A-Za-zÁ-Žá-ž])"), ", "),
    # Párové rovné uvozovky → české „…". Jen párové a jen do 160 znaků, aby se
    # nespojily dvě nesouvisející uvozovky přes půl odstavce; apostrof stojící
    # samostatně se nechytí, protože chybí uzavírací protějšek.
    (re.compile(r'"([^"\n]{1,160})"'), r"„\1“"),
    (re.compile(r"(?<![A-Za-zÁ-Žá-ž])'([^'\n]{1,160})'(?![A-Za-zÁ-Žá-ž])"), r"„\1“"),
]


def walk(node, path="", in_src=False):
    """Projde JSON a vrátí (cesta, klíč, text) pro každé prozaické pole.

    `in_src` hlídá, že jsme uvnitř `zdroje[]` / `citace[]` — tam je `nazev`
    titulek článku nebo doslovná citace, do které se nesmí sahat.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            if k in SKIP_KEYS:
                continue
            if in_src and k in {"nazev", "text"}:
                continue
            if isinstance(v, str):
                if k in PROSE_KEYS and len(v) > 12:
                    yield f"{path}.{k}", k, v
            else:
                yield from walk(v, f"{path}.{k}", in_src or k in SRC_KEYS)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]", in_src)


def fix_text(t: str, is_title: bool = False) -> str:
    for rx, rep in FIXES:
        t = rx.sub(rep, t)
    # Tečku doplň jen u delších odstavců, nikdy u titulků.
    if not is_title and len(t) > 60 and t[-1] not in ".!?…:)\"”":
        t += "."
    return t


def apply_fix(node, in_src=False):
    changed = 0
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if k in SKIP_KEYS or (in_src and k in {"nazev", "text"}):
                continue
            if isinstance(v, str) and k in PROSE_KEYS and len(v) > 12:
                nv = fix_text(v, is_title=(k == "nazev"))
                if nv != v:
                    node[k] = nv; changed += 1
            else:
                changed += apply_fix(v, in_src or k in SRC_KEYS)
    elif isinstance(node, list):
        for v in node:
            changed += apply_fix(v, in_src)
    return changed


def main():
    do_fix = "--fix" in sys.argv
    show = 0
    if "--show" in sys.argv:
        i = sys.argv.index("--show")
        show = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 20

    skip = set()
    if "--skip" in sys.argv:
        skip = {x.strip() for x in sys.argv[sys.argv.index("--skip") + 1].split(",")}
    files = [f for f in sorted(RES.rglob("*.json")) if f.name not in skip]
    if skip:
        print(f"(přeskočeno: {', '.join(sorted(skip))})")
    tally = Counter()
    examples = defaultdict(list)
    touched = 0

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"✗ nevalidní JSON: {f.relative_to(ROOT)}")
            continue

        for path, key, text in walk(data):
            for name, rx in CHECKS:
                for m in rx.finditer(text):
                    tally[name] += 1
                    if len(examples[name]) < 6:
                        a, b = max(0, m.start() - 35), m.end() + 35
                        examples[name].append(
                            f"{f.stem}{path}: …{text[a:b].strip()}…")

        if do_fix:
            n = apply_fix(data)
            if n:
                f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
                touched += 1

    print(f"Zkontrolováno souborů: {len(files)}\n")
    if not tally:
        print("Žádné typografické nálezy.")
    for name, n in tally.most_common():
        print(f"  {n:>5}×  {name}")
        if show:
            for ex in examples[name][:show]:
                print(f"           {ex}")
    if do_fix:
        print(f"\nOpraveno v {touched} souborech.")
        print("Pozn.: rovné uvozovky a chybějící čárky ve větách se automaticky "
              "neopravují — to vyžaduje posouzení významu.")


if __name__ == "__main__":
    main()

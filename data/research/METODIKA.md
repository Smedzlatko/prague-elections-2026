# Metodika hodnocení

Všechna skóre jsou **odvozená hodnocení, ne naměřená fakta.** Každé má v datech
povinné `oduvodneni`. Kde chybí podklad, je hodnota `null` — nikdy se nehádá.

## `konkretnost_programu` (0–5)
Jak ověřitelné jsou sliby, ne jak se nám zamlouvají.

| Skóre | Kritérium |
|---|---|
| 0 | Program nenalezen nebo jen slogany. |
| 1 | Obecná přání bez opatření („chceme lepší Prahu“). |
| 2 | Pojmenovaná opatření bez čísel a termínů. |
| 3 | Většina priorit má konkrétní opatření, část i čísla. |
| 4 | Většina slibů kvantifikovaná (počty, termíny). |
| 5 | Kvantifikováno **a** s uvedeným rozpočtovým krytím či zdrojem financí. |

## `doveryhodnost_plneni` (0–5)
Jen pro subjekty s dohledatelným záznamem z let 2022–2026 (vládly v magistrátu
nebo v dané MČ). Nový subjekt bez historie = `null`, ne nula.

| Skóre | Kritérium |
|---|---|
| 0 | Prokazatelně porušila klíčové sliby, obrat o 180°. |
| 1 | Většina měřitelných slibů nesplněna. |
| 2 | Menšina splněna; vlastní priority odloženy. |
| 3 | Smíšeno — splněna přibližně polovina měřitelných slibů. |
| 4 | Většina měřitelných slibů splněna či rozpracována. |
| 5 | Splněny prakticky všechny měřitelné sliby. |

Pozn. Nesplnění kvůli pozici v opozici či vnějšímu vetu se **nepočítá proti** —
uvede se do `oduvodneni` jako polehčující kontext.

## `transparentnost` (0–5)
Sčítá se: zveřejněný program (+1), dohledatelné financování kampaně (+1),
transparentní účet (+1), zveřejněné smlouvy / hlasování zastupitelů (+1),
dohledatelní lidé na listině s životopisy (+1).

## `plneni_slibu` u osoby (0–5)
Stejná stupnice jako `doveryhodnost_plneni`, ale vztažená k tomu, co daný člověk
osobně prosazoval ve své funkci. Bez výkonné funkce = `null`.

## `zavaznost` u případu
- `nizka` — procedurální pochybení, spor o výklad, bez škody.
- `stredni` — doložený konflikt zájmů, pochybení v zakázce, pokuta.
- `vysoka` — obvinění/odsouzení v trestní věci, škoda ve desítkách milionů a více,
  opakované porušení zákona.

Závažnost se hodnotí **podle povahy věci, ne podle hlasitosti medií**, a vždy
spolu s polem `stav` (zproštěn / probíhá / neprokázáno / …).

## Zdroj u splněných slibů

Tvrzení „slib jsme splnili" doložené **webem samotné strany** není nestranný důkaz.
Takový zdroj se nevyřazuje — u lokální politiky bývá jediný dostupný — ale:

1. označí se (`zdroj_strana: true`, doplňuje build automaticky podle domény),
2. v textu se formuluje jako tvrzení strany („podle vlastní bilance strany…"),
3. **sám o sobě neopravňuje k vysokému skóre** `doveryhodnost_plneni`. Pro skóre 4–5
   je potřeba nezávislé doložení (úřad, dodavatel, rejstřík, médium).

Jinak by vyšší skóre dostaly strany s lepším PR, ne strany s lepšími výsledky.

## Společné měřítko u koaličních partnerů

Vládly-li strany spolu, musí se měřit **týmž dokumentem** — jinak skóre neměří
výkon, ale schopnost o sobě dobře psát.

Pro Prahu 2022–2026 je závazným měřítkem **Programové prohlášení Rady hl. m. Prahy
(červen 2023)**, které koalice SPOLU–Piráti–STAN sama podepsala:
<https://www.praha.eu/documents/d/praha/programove_prohlaseni_2023_3600794>

Každý z partnerů se hodnotí podle kapitol odpovídajících **jeho vlastním gescím**:

| Strana | Gesce v Radě 2023–2026 |
|---|---|
| SPOLU (ODS, TOP 09) | primátor, bezpečnost, energetika; sociální politika, bydlení, zdravotnictví (Udženija); finance a podpora podnikání (Kovářík); infrastruktura, životní prostředí, kultura (Hroza, Pospíšil) |
| Piráti | doprava (Hřib, od 12/2025 Beránek); majetek, transparentnost a legislativa (Zábranský); životní prostředí a klimatický plán (Komrsková, do 6/2026) |
| STAN | územní a strategický rozvoj (Hlaváček); školství, sport a volný čas (Klecanda) |

Kampaňová stránka typu „co jsme pro Prahu udělali“ je **tvrzení strany**, ne doklad
splnění. Smí se citovat, ale splněný slib z ní sám o sobě neplyne.

## Pravidla férovosti
1. Stejná měřítka na všechny subjekty bez ohledu na ideologii.
2. U obvinění vždy uvést výsledek a vyjádření dotčené osoby, pokud existuje.
3. Neprokázané = neprokázané. Nepíše se tónem, který vinu předjímá.
4. Chybějící informace se přiznává v `mezery_v_datech`, nenahrazuje dohadem.

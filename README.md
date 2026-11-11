# Konfliktklauseln lernen – aus jedem Fehlschlag eine Regel – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-konfliktlernen-demo.streamlit.app/)**

Stück der **Linie „SAT und Constraint Programming“** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ und **Wurzel ihres SAT-Arms**. Die Demo zeigt, was ein SAT-Löser tut, wenn eine Suche in eine Sackgasse läuft: Er **lernt aus dem Konflikt eine neue Klausel** und springt bis zu der Entscheidung zurück, die den Konflikt verursacht hat (Konfliktlernen, *conflict-driven clause learning*, CDCL). Verglichen wird er mit einer Suche **ohne Gedächtnis** (DPLL), die denselben Fehler in vielen Ästen wiederholen kann. Das Vehikel der Linie ist die **Zuordnung von Aufträgen zu Rampen** (Färbung eines Konfliktgraphen); dazu kommen Zufalls-3-SAT als Wachstumsmaß sowie Schur-Zahlen und das Schubfach als Grenzfälle. Verwandt: `sat-phasenuebergang-demo` (DPLL und Phasenübergang der Komplexitätsklassen-Reihe; das Klausellernen ist dort ausdrücklich nicht gebaut) und `graph-coloring-demo` (gleiches Kernmodell wie die Rampen-Aufgabe, andere Frage: die Reihenfolge).

## Warum dieses Problem

DPLL belegt Variablen, folgert per Einheitspropagation und kehrt bei einem Widerspruch nur **eine** Stufe zurück. Ob dieselbe Ursache in einem anderen Ast wiederkehrt, weiß die Suche nicht. Der CDCL hält die Ursache als Klausel fest. Die Kernfrage der Demo: **Wann bringt dieses Gedächtnis etwas?** Die Antwort fällt differenziert aus: bei wachsenden Zufallsformeln am Phasenübergang (m/n = 4,26 und 4,5) ja, bei m/n = 4,0 und bei kleinen Formeln nein, beim Schubfach nur sehr spät.

## Modell

- **Formel.** Konjunktive Normalform über n Variablen; Literale sind ganze Zahlen (−5 steht für „nicht x5“). Formelerzeuger und Zufallsgenerator (SplitMix64, ganzzahlig, auf jeder Plattform derselbe Strom) sind wörtliche Kopien aus dem Kern-Paket der Linie (siehe Methodik); Python-`random` und `hash()` kommen nirgends vor.
- **Konflikt, Analyse, Lernen.** Wird eine Klausel falsch, löst der CDCL rückwärts entlang der Belegungsreihenfolge auf, bis auf der Konfliktstufe genau ein Literal übrig ist (1-UIP, erste eindeutige Implikationsstelle); das Ergebnis ist die gelernte Klausel. Der Rücksprung geht auf die zweithöchste Stufe der gelernten Klausel; die Stufen dazwischen werden übersprungen. Formeln im 📐-Expander der App.
- **Aufwand.** Gezählt werden **CDCL-Konflikte** und **DPLL-Widersprüche**, nie Sekunden. Ein *Widerspruch* ist ein Blatt der DPLL-Suche, an dem die Einheitspropagation eine leere Klausel erzeugt; er entspricht einem CDCL-Konflikt. Die *Sackgassen* des DPLL (Blätter und innere Knoten, deren beide Zweige scheitern) stehen nur als Nebenzahl da. Bei unerfüllbaren Formeln hat im Suchbaum jeder Knoten null oder zwei Kinder: Sackgassen = 2 × Widersprüche − 1 (im 📐-Expander begründet, an allen unerfüllbaren Messzeilen geprüft). Wer CDCL-Konflikte gegen DPLL-Sackgassen stellt, überzeichnet den Vorsprung bei unerfüllbaren Formeln etwa um den Faktor 2; die Demo tut das nicht.
- **Standardlöser der Messreihen.** CDCL mit Aktivität je Variable (VSIDS in der MiniSat-Variante), Phasenspeicher, Luby-Neustarts mit Einheit 32, ohne Minimieren, mit zwei beobachteten Literalen. DPLL mit Einheitspropagation und der Regel „häufigste Variable, erst wahr“. In Experiment 1 gilt für beide die feste Reihenfolge x1, x2, … mit „wahr zuerst“, damit sich jeder Schritt von Hand nachrechnen lässt.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| CDCL, DPLL, Instanzen, SplitMix64 | `kfl_cdcl.py`, `kfl_dpll.py`, `kfl_instanzen.py`, `kfl_rng.py` | **Kopien** der Module des Kern-Pakets `sat-cp-planung/kern/`; die erste Zeile jeder Datei nennt die Kern-Version (Hash), `tests/test_kern_kopien.py` prüft, dass der Rest wortgleich ist. Importe nur aus den Kopien, nie aus anderen Demos. |
| CDCL mit Spur und Analyseprotokoll, DPLL mit Suchbaum | `kfl_algorithm.py` | Eigener Code über dem Kern: der Suchbaum benutzt dieselben Einheiten wie der Kern-DPLL (Zähler stimmen überein, Test); das Analyseprotokoll hält je Konflikt Konfliktstufe, Rücksprungstufe, Länge und LBD fest, ohne den Ablauf zu ändern. |
| Schritt-für-Schritt-Ansicht | `kfl_trace.py` | Zustände, Stufentabelle, Implikationsgraph und 1-UIP-Schnitt aus der Ereignisspur des CDCL; der Schnitt wird aus dem Graphen gelesen und stimmt mit der gelernten Klausel überein (Test). |
| Messzellen | `kfl_messung.py`, `tools/messe_vorgerechnet.py`, `kfl_vorgerechnet.json` | Je Zelle feste Formeln, CDCL-Konflikte gegen DPLL-Widersprüche. **Vorgerechnet, nicht live**: das Skript schreibt alle 39 Zellen in die JSON-Datei, die App liest sie. Zellen bis Zufall n = 70, Rampen n ≤ 60, Schur, Schubfach h ≤ 6 und Experiment 4 mit n = 50 lassen sich in der App per Knopf neu rechnen und mit den gespeicherten Zeilen vergleichen; größere dauern dort zu lange. |
| Auswertung und Verdikte | `kfl_evaluation.py` | Zusammenfassungen und alle Verdikte als reine Funktionen `(Art, Text)`; jede Zahl im Text stammt aus den Zellen. |

Experimente in der App: **🔍 Eine Formel von Hand** (Schritt-für-Schritt-Ansicht mit Implikationsgraph, Stufentabelle, gelernten Klauseln und dem DPLL-Baum derselben Formel), **🔬 Wächst der Vorsprung mit der Größe?** (Zufalls-3-SAT, n = 30 bis 110, m/n = 4,0 / 4,26 / 4,5), **🔬 Wo das Lernen hilft und wo nicht** (Rampen-Färbung, Schur, Schubfach, Zufall) und **🔬 Was wird gelernt?** (Längen der gelernten Klauseln, Sprungweiten, mit und ohne Minimieren). Presets („Schnellstart“) und der Zufalls-Seed stehen in der Seitenleiste, die experimentbezogenen Regler im Hauptbereich.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (Zuordnung im Kopf der Datei). Messzellen: je 20 feste Formeln (Zufalls-Seeds 1 bis 20; Schur und Schubfach je eine Formel); Experiment 4 je 12 feste Formeln. Aufwand in Konflikten und Widersprüchen; Quotient = Median der DPLL-Widersprüche durch Median der CDCL-Konflikte (Verhältnis der Mediane). Kein Lauf brach am Budget ab (CDCL-Budget 200.000 Konflikte, DPLL-Budget 50.000 Knoten, beim Schubfach 200.000).

| Frage | Befund |
|---|---|
| **Handbeispiel F1** (fünf Klauseln über x1 bis x6, feste Reihenfolge, wahr zuerst) | DPLL: 14 Knoten, **6 Widersprüche**, 11 Sackgassen. CDCL: **2 Konflikte**. Konflikt 1 auf Stufe 5 in K2: gelernt (¬x1 ∨ ¬x5), Sprung auf Stufe 1 (überspringt die Stufen 2, 3, 4); Konflikt 2 auf Stufe 1 in K4: gelernt (¬x1), Sprung auf Stufe 0. Von Hand nachgerechnet und im Test gegen einen unabhängigen DPLL-Zähler geprüft (`test_claim_handbeispiel_f1`). Schubfach h = 2 (3 Tauben, 2 Löcher): DPLL 3 Knoten, 2 Widersprüche (`test_claim_handbeispiel_schubfach_h2`). |
| **Zählweise: Widerspruch oder Sackgasse?** | In allen 228 unerfüllbaren Messzeilen (Zufall, Rampen, Schur, Schubfach) ist die Zahl der Sackgassen genau 2 × Widersprüche − 1. Bei m/n = 4,26 liegt der Median der Sackgassen je Widerspruch (über die 20 Formeln einer Zelle) bei n = 50 / 70 / 90 / 110 bei 1,94 / 1,98 / 1,98 / 1,99 (`test_claim_zaehlweise_*`). |
| **Wächst der Vorsprung mit n?** (Zufalls-3-SAT, m/n = 4,26, 20 Formeln) | Median CDCL-Konflikte / DPLL-Widersprüche (Quotient DPLL-Widersprüche durch CDCL-Konflikte; erfüllbar von 20), n = 30: 14,5 / 6,5 (0,45; 12), n = 50: 35 / 39,5 (1,13; 13), n = 70: 89 / 104 (1,17; 11), n = 90: 159 / 343,5 (**2,16**; 13), n = 110: 287 / 1.014,5 (**3,53**; 13). Der Quotient wächst in allen vier Schritten; unter 1,2 (Verdikt „kein Vorsprung“) liegt er bei n = 30 bis 70. DPLL-Sackgassen im Median: 10 / 75,5 / 205 / 680 / 2.024,5 (`test_claim_wachstum_zufall_4_26`, `test_claim_wachstum_vorsprung_erst_ab_n_90`). |
| **Wie fest ist diese Grenze?** | Mit zwei anderen Formelmengen (Zufalls-Seeds 21 bis 40 und 41 bis 60, m/n = 4,26) lautet der Quotient bei n = 30 0,88 und 0,84, bei n = 50 0,81 und 1,18, bei n = 70 1,45 und 0,90 (`test_claim_wachstum_streuung_mit_der_formelmenge`). Bei n = 90 lag er in einer Nachprüfung mit denselben beiden Formelmengen bei 2,34 und 1,71 (nicht Teil der Tests). „Ab etwa n = 90 zahlt sich das Lernen aus“ gilt also für diese Instanzfamilie und ist **unscharf**: Zwischen n = 50 und 70 streut der Quotient um mehrere Zehntel. |
| **Hängt das am Verhältnis m/n?** | Ja. Bei m/n = 4,5 wächst der Quotient ebenfalls in allen vier Schritten (0,68 / 1,05 / 1,24 / 1,42 / 2,17 für n = 30 bis 110). Bei **m/n = 4,0 nicht**: 0,24 / 0,97 / 0,80 / 1,52 / 0,84; dort sind bei n = 90 19 von 20 und bei n = 110 alle 20 Formeln erfüllbar, und das Lernen hat gegenüber dem DPLL bei n = 110 keinen Vorsprung (`test_claim_verhaeltnis_quotienten_und_monotonie`). Erfüllbare Formeln von 20 bei m/n = 4,5: 11 / 9 / 5 / 5 / 5. |
| **Aufträge auf Rampen** (Färbung des Konfliktgraphen, 3 Rampen, 20 Formeln) | Mittlerer Grad 4,5, n = 30 / 60 / 90: CDCL 15 / 19,5 / 29,5, DPLL 15 / 31,5 / 53 Konflikte beziehungsweise Widersprüche; Quotient 1,00 / 1,62 / 1,8 (erfüllbar 2 / 7 / 9 von 20). Grad 5,0: 1,11 / 1,23 / 1,5 (fast alle unerfüllbar: 1 / 0 / 0 erfüllbar). Grad 4,0 (meist erfüllbar, 14 / 19 / 18 von 20): 1,83 / 0,86 / 0,86 (`test_claim_rampen_drei_rampen`). |
| **Schur-Zahlen** (3 Mengen) | n = 14 (unerfüllbar): CDCL 148 Konflikte gegen DPLL 147 Widersprüche (Quotient 0,99; 293 Sackgassen); n = 13 (erfüllbar): 18 gegen 10 (`test_claim_schur_k3`). |
| **Schubfach** (h + 1 Tauben, h Löcher, unerfüllbar) | CDCL-Konflikte für h = 3 bis 8: 7 / 28 / 159 / 1.004 / 4.811 / 27.932; DPLL-Widersprüche 6 / 24 / 120 / 720 / 5.040 / 40.320, **gemessen genau h!**. Quotient 0,86 / 0,86 / 0,75 / 0,72 / 1,05 / 1,44: **gegen diesen DPLL hat der CDCL beim Schubfach bis h = 7 keinen Vorsprung** in der Zählung (Quotient unter 1,2; Verdikt „gegenüber diesem DPLL kein Vorsprung“), bei h = 8 liegt der DPLL darüber. Von Zelle zu Zelle wächst der CDCL-Median um das 4,0- bis 6,3-Fache, der DPLL-Median um das 4,0- bis 8,0-Fache. Beide Zähler wachsen mit jedem Loch weiter (`test_claim_schubfach_zaehler_und_quotienten`). |
| **Minimieren der gelernten Klausel** (Zufall, m/n = 4,26, je 12 Formeln, Mediane) | n = 50: 22 gegen 22 Konflikte, mittlere Länge 5,1 gegen 4,4 Literale; mit Minimieren bei 3 Formeln weniger, bei 6 gleich viele, bei 3 mehr Konflikte. n = 150: 3.370 gegen 2.845,5 Konflikte (**15,6 % weniger**, Bezug ohne Minimieren), Länge 11,9 gegen 9,5; bei 7 Formeln weniger, bei 5 mehr (`test_claim_lernen_n50_und_n150`). Die Länge sinkt in beiden Größen; die Konfliktzahl nur bei n = 150 im Median, aber bei 5 von 12 Formeln steigt sie dort: mit 12 Formeln ist das keine gesicherte Wirkung. |
| **Wie weit springt der Löser?** | Die mittlere Sprungweite (Konfliktstufe minus Rücksprungstufe) liegt bei 1,2; nur 14,8 % (n = 50, ohne Minimieren; mit Minimieren 12,2 %) beziehungsweise 13,3 % (n = 150; 12,8 %) der Sprünge gehen über mehr als eine Stufe. Das Überspringen mehrerer Stufen ist in diesen Läufen die Ausnahme (`test_claim_lernen_n50_und_n150`). |
| **Presets** | „Rampen“ zeigt die Zelle Rampen-Färbung n = 30, Grad 4,5 (Quotient 1,00, also kein Vorsprung), „Schubfach h = 5“ die Zelle mit 159 CDCL-Konflikten (`test_claim_presets_zeigen_diese_zellen`). |

## Befunde und Korrekturen gegenüber dem Plan

- **Zählweise übernommen und gemessen.** Der Plan korrigierte die Vormessung (Konflikte gegen *Sackgassen*) auf *Widersprüche*; die Demo zeigt beide Zahlen, nennt den Widerspruch als Maß und belegt die Beziehung Sackgassen = 2 × Widersprüche − 1 an allen unerfüllbaren Messzeilen (oben).
- **Zahlen der Vormessung gelten als überholt.** Die Vormessung nutzte Python-Zufallsformeln, die Demo SplitMix64-Formeln. Statt 0,87 / 1,1 / 2,1 / 2,6 (n = 50 / 70 / 90 / 110) misst die Demo 1,13 / 1,17 / 2,16 / 3,53; der Plan-Wert 2,6 bei n = 110 wird nicht reproduziert (3,53). Das Muster „kein Vorsprung bei kleinem n, ab etwa n = 90 ein Vielfaches“ bleibt, ist aber unscharf (Befund „Wie fest ist diese Grenze?“).
- **Neu gegenüber dem Plan: Das Wachsen hängt am Verhältnis m/n.** Bei m/n = 4,0 (fast alle Formeln erfüllbar) fehlt es; der Plan nannte nur m/n = 4,26.
- **Schubfach: „kein Vorsprung“ gilt bis h = 7, nicht für h = 8.** Der Plan schrieb, der Vorsprung „bleibt beim Schubfach aus“; bei h = 8 braucht der DPLL das 1,44-Fache an Widersprüchen. Beide Zähler wachsen mit jedem Loch weiter. Neu: die DPLL-Widersprüche sind in dieser Messung genau h!.
- **Rampen-Färbung nachgemessen.** Der Plan schätzte die Färbung nur aus dem Verhältnis 2 (etwa 1,6 bis 2,4); gemessen sind 1,0 bis 1,8 (Grad 4,5) und 1,11 bis 1,5 (Grad 5,0), bei Grad 4,0 sogar 0,86 für n = 60 und 90.
- **Minimieren: Plan-Wert nicht reproduziert.** Der Plan nannte bei n = 150 11,6 → 9,3 Literale und etwa ein Fünftel weniger Konflikte; gemessen sind 11,9 → 9,5 und 15,6 % weniger im Median, mit 5 von 12 Formeln, bei denen es *mehr* Konflikte gibt.
- **Neu: Sprünge über mehrere Stufen sind selten** (12 bis 15 % der Sprünge in diesen Läufen). Der Rücksprung ist im Handbeispiel eindrucksvoll (5 → 1), in der Messung aber meist ein Schritt.
- **Quellenlage.** Der Plan schreibt „1-UIP wie GRASP“. Im Leseprotokoll ist die Zuschreibung des First UIP an GRASP nicht bestätigt (GRASP ist für Konfliktklauseln aus dem Implikationsgraphen und das nichtchronologische Zurückspringen gelesen, „First UIP“ steht im Glucose-Papier). Text und 📐-Expander folgen dem Leseprotokoll. Haken (1985) ist nur über die Einleitung von Beame, Pitassi und Impagliazzo (1993) belegt und steht mit diesem Vermerk im Expander.
- **Kern-Besonderheit.** `startphase=True` wirkt im Kern nur zusammen mit dem Phasenspeicher; mit `phase_saving=False` ignoriert `waehle_literal` die Startphase und wählt falsch zuerst. Das Handbeispiel läuft deshalb mit Phasenspeicher (Voreinstellung des Kerns). Die Kopie bleibt unverändert; das ist eine Meldung an das Kern-Paket.
- **Lateinische Quadrate** kommen wie im Plan nicht vor (zu leicht für Konfliktlernen). Experiment 3 ist eine Auswahl vorgerechneter Zellen mit Leiter der Größen statt eines Reglers je Familie; dadurch gibt es keine Regler, die unter einer anderen Auswahl wirkungslos wären.

## Ehrliche Grenzen

- **Ein DPLL, nicht „die Suche ohne Gedächtnis“.** Verglichen wird mit der Rekursion mit Listenkopie, Einheitspropagation und der Regel „häufigste Variable“; mit einer anderen Verzweigungsregel ändern sich die Widerspruchszahlen. Das Verhältnis gilt für dieses Paar. Der Quotient vermischt außerdem das Lernen mit Verzweigungsregel, Phasenspeicher und Neustarts: In einer Nachprüfung (nicht Teil der Tests) braucht ein Löser mit denselben Aktivitäten ohne Lernen bei Zufalls-3-SAT (m/n = 4,26) und n = 90 im Median 6.611,5 Konflikte statt 159, am Schubfach 52 / 375 / 3.246 statt 28 / 159 / 1.004 bei h = 4 / 5 / 6. Die Quotienten messen daher nicht den Gewinn durch das Lernen allein.
- **Instanzfamilien und Größen.** Zufalls-3-SAT bis n = 110 (je 20 Formeln; in den Zellen eine Formelmenge), Rampen bis n = 90, Schur nur k = 3, Schubfach bis h = 8. Aussagen über größere n, Industrieformeln oder andere Löser (Kissat, CaDiCaL) macht die Demo nicht. „Wächst mit n“ gilt nur für die gemessenen n.
- **Konflikte sind keine Zeit.** Ein CDCL-Konflikt (Analyse, Lernen) kostet mehr Arbeit als ein DPLL-Widerspruch; die Zeit je Konflikt ist nicht gemessen, die Demo macht keine Aussage über Laufzeiten.
- **Medianvergleiche mit 20 Formeln.** Der Quotient ist ein Verhältnis der Mediane (nicht der Median der Verhältnisse); die Grenze 1,2 des Verdikts ist eine Festlegung der Demo. Bei n = 50 bis 70 streut der Quotient mit der Formelmenge um mehrere Zehntel (siehe Befunde).
- **Ursachen sind Deutungen.** Warum der Vorsprung bei m/n = 4,0 ausbleibt oder die DPLL-Widersprüche beim Schubfach h! betragen, ist nicht untersucht; die Demo zeigt nur die Messung.
- **Schritt-für-Schritt-Ansicht nur für kleine Formeln** (höchstens 12 Variablen und 60 Klauseln, Spur höchstens 5.000 Ereignisse); die Spur zeigt den Lauf mit fester Reihenfolge, nicht den Standardlöser der Messreihen.
- **Plotly-Interaktion.** Die Diagramme sind nicht anklickbar (alle Achsen gesperrt); es gibt keine Auswahl per Mausklick.

## Verifikation

- **Kern-Kopien:** `tests/test_kern_kopien.py` (Kopfzeile = Kern-Version, Rest wortgleich, gegen den Kern-Ordner, sofern er daneben liegt); die Regressionstests des Kerns (`tests/test_kern_*.py`: SplitMix64-Referenzwerte, Instanzerzeuger, DPLL-Knotenzahlen 11 / 47 / 239 / 1.439 für Schubfach h = 3 bis 6, jede CDCL-Einheit von Hand).
- **Einheiten dieser Demo von Hand:** Handbeispiel F1 (DPLL 14 / 6 / 11, CDCL 2 Konflikte, gelernte Klauseln, Sprungstufen), Schubfach h = 2, Suchbaum, Analyseprotokoll (`tests/test_algorithm.py`), Ereignisfolge, Stufentabelle, Implikationsgraph und 1-UIP-Schnitt (`tests/test_trace.py`).
- **Orakel** (`tests/test_oracle_konfliktlernen.py`, unabhängige Rechenwege im Test): Brute Force über alle Belegungen (n ≤ 12, fünf Löserkonfigurationen), eigener mengenbasierter DPLL-Zähler für Widersprüche und Sackgassen (60 Formeln), OR-Tools CP-SAT auf 40 Zufallsformeln n = 30 bis 60 und Schubfach h = 5 und 6 (überspringt sich ohne OR-Tools), eigener RUP-Prüfer für jede gelernte Klausel (mit und ohne Minimieren), 1-UIP-Eigenschaft und Sprungstufe an jedem Konflikt, Umbenennen der Variablen und Vertauschen der Klauseln ändern die Antwort nie, mehr Klauseln machen Unerfüllbares nicht erfüllbar, Randfälle (leere Formel, leere Klausel, Einheitsklauseln, Tautologie, doppelte Literale, Konflikt auf Stufe 0, Budget gibt „unbekannt“).
- **Messzellen** (`tests/test_messung.py`): die Datei enthält jede Zelle der App; CDCL und DPLL widersprechen sich in keiner der 491 Zeilen; die kleinen Zellen (Zufall n ≤ 70, Rampen n = 30, Schur, Schubfach h ≤ 6, Experiment 4 mit n = 50) werden frisch gerechnet und mit den gespeicherten Zeilen verglichen; Seeds, Budgets und Kern-Versionen in der Datei stimmen mit den Modulen überein.
- **Verdikte** (`tests/test_verdicts.py`): Schwellen, Randfälle (null Konflikte, null Widersprüche, Abbrüche) und jede Zahl im Text an handgesetzten Zeilen. **Claims:** `tests/test_claims.py` rechnet jede Zahl der Befunde nach.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an den Grenzen), jede Beispielformel, jede Familie, jede Auswahl der Zufallsreihe, Schritt-Schalter, Live-Knöpfe, Permalink, Presets (`tests/test_app.py`, `tests/test_app_interaktion.py`); Layout (Schnellstart in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben, jede Änderung eines Reglers hebt die Markierung auf: `tests/test_layout.py`), Abbildungen (`tests/test_visualization.py`), Footer, Laufzeit-Importe.
- **Gesamtzahl: 235 Tests.**

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: vier Experimente, Kernfrage, Annahmentabelle, Mathematik |
| `kfl_cdcl.py`, `kfl_dpll.py`, `kfl_instanzen.py`, `kfl_rng.py` | Kopien der Kern-Module (Kern-Version in der ersten Zeile) |
| `kfl_algorithm.py` | CDCL mit Spur und Analyseprotokoll, DPLL-Suchbaum |
| `kfl_trace.py` | Zustände, Stufentabelle, Implikationsgraph, 1-UIP-Schnitt |
| `kfl_messung.py` | Messzellen und ihre Schlüssel, Laden der vorgerechneten Datei |
| `kfl_vorgerechnet.json` | alle Messzellen, vorgerechnet (nicht live) |
| `kfl_evaluation.py` | Zusammenfassungen, Verdikte, Formatierung |
| `kfl_constants.py`, `kfl_presets.py`, `kfl_scenario.py`, `kfl_layout.py` | Regler und Zellen, Presets und Permalink, Beispielformeln und Namen, fester Kopf |
| `kfl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tools/messe_vorgerechnet.py` | rechnet alle Zellen und schreibt die JSON-Datei |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur Gegenprobe im Test) |
| `tests/` | Kern-Regressionstests, Handwerte, Orakel, Messzellen, Verdikte, Claims, Oberfläche, Layout, Abbildungen |

## Bewusst nicht umgesetzt

- **PDF-Export** der Ansichten: die Ansichten sind interaktive Schrittfolgen, ein Export bringt wenig.
- **Eigene Verzweigungsregeln, Neustarts, Löschen gelernter Klauseln, Datenstrukturen** des Lösers: sie sind Gegenstand der Folgestücke der Linie; hier gibt es nur die Schalter „Minimieren“ und die feste Reihenfolge in Experiment 1.
- **Beweisprotokoll und Prüfer** als Demo-Inhalt: die Folgerichtigkeit der gelernten Klauseln wird nur im Test geprüft.
- **Zeitmessungen:** Aufwand wird gezählt, nie als Zeit gemessen.
- **Lateinische Quadrate** als Instanzfamilie (Konfliktlernen braucht dort 0 bis 4 Konflikte in der Vormessung, keine Hürde).
- **Live-Rechnung der großen Zellen** (Zufall n ≥ 90, Schubfach h ≥ 7, Experiment 4 mit n = 150): vorgerechnet, weil sie in der App zu lange dauern.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Die vorgerechneten Zellen neu erzeugen (kein Teil der App): `python tools/messe_vorgerechnet.py --gruppe zufall --out teil_zufall.json`, `python tools/messe_vorgerechnet.py --gruppe rest --out teil_rest.json`, dann `python tools/messe_vorgerechnet.py --zusammenfuehren teil_zufall.json teil_rest.json`.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).

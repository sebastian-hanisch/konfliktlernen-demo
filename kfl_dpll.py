# Kern-Version 7e82270e3e4fb0e7: Kopie von sat-cp-planung/kern/dpll.py; geändert nur die Importzeile(n) auf das Präfix kfl_ und diese Kopfzeile (tests/test_kern_kopien.py prüft das).
"""DPLL des Kern-Pakets: Erfüllbarkeit durch Suche mit Einheitspropagation.

Herkunft: `propagate` und `choose_variable` sind in Logik und Reihenfolge aus `sat-phasenuebergang-demo/sph_dpll.py`
(Kopie von `reduktionskette-demo/red_dpll.py`, Commit ba24648) übernommen und deutsch benannt; neu sind nur die Zähler
`sackgassen` und `einheitsschritte` sowie das Knotenbudget. Die Knotenzahlen stimmen mit dem Original überein
(Schubfach h = 3…6: 11 / 47 / 239 / 1 439 Knoten, Regressionstest).

Ein *Knoten* ist ein Aufruf der Suche. Regeln: (1) Einheitsklausel: eine Klausel mit genau einem freien Literal erzwingt es;
(2) Verzweigung auf der Variablen, die in den meisten noch offenen Klauseln vorkommt (Gleichstand: kleinere Nummer), erst wahr,
dann falsch. Eine leere Klausel ist ein Widerspruch (Sackgasse).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DpllErgebnis:
    erfuellbar: bool | None     # None bei Knotenbudget
    belegung: dict | None       # erfüllende (teilweise) Belegung bei Erfolg
    knoten: int                 # Aufrufe der Suche
    widersprueche: int          # Blätter: Einheitspropagation endet in einer leeren Klausel
    sackgassen: int             # Blätter plus innere Knoten, deren beide Zweige scheitern (Knoten ohne Lösung darunter)
    einheitsschritte: int       # erzwungene Literale


def propagiere(klauseln, belegung, zaehler=None):
    """Einheitspropagation bis zum Fixpunkt. Rückgabe (offene Klauseln, Belegung) oder None bei Widerspruch.
    Erfüllte Klauseln fallen weg, falsche Literale werden gestrichen."""
    klauseln = list(klauseln)
    while True:
        einheit = None
        uebrig = []
        for klausel in klauseln:
            if any(belegung.get(abs(l)) is not None and belegung[abs(l)] == (l > 0) for l in klausel):
                continue
            rest = tuple(l for l in klausel if belegung.get(abs(l)) is None)
            if not rest:
                return None
            if len(rest) == 1 and einheit is None:
                einheit = rest[0]
            uebrig.append(rest)
        klauseln = uebrig
        if einheit is None:
            return klauseln, belegung
        belegung = dict(belegung)
        belegung[abs(einheit)] = einheit > 0
        if zaehler is not None:
            zaehler[0] += 1


def waehle_variable(klauseln, regel: str = "haeufigste") -> int:
    """Verzweigungsvariable. `regel="haeufigste"`: die häufigste in den offenen Klauseln, bei Gleichstand die kleinere Nummer.
    `regel="erste"`: die kleinste Nummer unter den Variablen der offenen Klauseln."""
    anzahl: dict[int, int] = {}
    for klausel in klauseln:
        for l in klausel:
            anzahl[abs(l)] = anzahl.get(abs(l), 0) + 1
    if regel == "erste":
        return min(anzahl)
    if regel != "haeufigste":
        raise ValueError("regel muss 'erste' oder 'haeufigste' sein")
    return max(anzahl, key=lambda v: (anzahl[v], -v))


class _Budget(Exception):
    pass


def dpll(formel, knoten_budget: int | None = None, regel: str = "haeufigste") -> DpllErgebnis:
    if regel not in ("erste", "haeufigste"):
        raise ValueError("regel muss 'erste' oder 'haeufigste' sein")
    knoten = [0]
    sackgassen = [0]
    widersprueche = [0]
    einheiten = [0]

    def suche(klauseln, belegung):
        knoten[0] += 1
        if knoten_budget is not None and knoten[0] > knoten_budget:
            raise _Budget
        schritt = propagiere(klauseln, belegung, einheiten)
        if schritt is None:
            widersprueche[0] += 1
            sackgassen[0] += 1
            return None
        klauseln, belegung = schritt
        if not klauseln:
            return belegung
        v = waehle_variable(klauseln, regel)
        for wert in (True, False):
            versuch = dict(belegung)
            versuch[v] = wert
            gefunden = suche(klauseln, versuch)
            if gefunden is not None:
                return gefunden
        sackgassen[0] += 1
        return None

    try:
        gefunden = suche([tuple(c) for c in formel], {})
    except _Budget:
        return DpllErgebnis(None, None, knoten[0], widersprueche[0], sackgassen[0], einheiten[0])
    return DpllErgebnis(gefunden is not None, gefunden, knoten[0], widersprueche[0], sackgassen[0], einheiten[0])

"""Bausteine über dem kopierten Kern: CDCL mit Spur und Analyseprotokoll, DPLL mit Suchbaum.

Alles Eigene dieser Demo liegt hier; `kfl_cdcl`, `kfl_dpll`, `kfl_instanzen`, `kfl_rng` sind wörtliche Kopien (siehe deren Kopfzeile)."""

from dataclasses import dataclass, field

from kfl_cdcl import Ergebnis, Loeser
from kfl_dpll import propagiere, waehle_variable

# Voreinstellung des Handbeispiels und der Schritt-für-Schritt-Ansicht: feste Reihenfolge x1, x2, ..., wahr zuerst, ohne Neustarts.
# (`startphase` wirkt im Kern nur mit Phasenspeicher; deshalb bleibt `phase_saving` an.)
HAND = dict(vsids=False, startphase=True, phase_saving=True, restarts="none")


def cdcl_spur(n, klauseln, *, minimieren=False, **optionen) -> Ergebnis:
    """CDCL mit Ereignisspur (`trace=True`, höchstens 5 000 Ereignisse), Standard: die Handbeispiel-Regeln."""
    opt = dict(HAND)
    opt.update(optionen)
    return Loeser(n, klauseln, trace=True, minimize=minimieren, **opt).loese()


class MessLoeser(Loeser):
    """CDCL, der bei jeder Konfliktanalyse (Konfliktstufe, Rücksprungstufe, Länge, LBD) mitschreibt.
    Das ist unabhängig von der auf 5 000 Ereignisse begrenzten Spur und ändert nichts am Ablauf."""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.protokoll = []

    def analysiere(self, konflikt):
        stufe = len(self.grenzen)
        klausel, rueck, lbd = super().analysiere(konflikt)
        self.protokoll.append((stufe, rueck, len(klausel), lbd))
        return klausel, rueck, lbd


# ------------------------------------------------------------------------------------------------------------ DPLL-Suchbaum
@dataclass
class DpllKnoten:
    id: int
    eltern: int | None
    wahl: int | None            # das Literal, auf das verzweigt wurde, um hierher zu kommen (None bei der Wurzel)
    tiefe: int
    art: str = "offen"          # "widerspruch" (Blatt), "loesung", "sackgasse" (innerer Knoten ohne Lösung darunter)
    kinder: list = field(default_factory=list)


@dataclass
class DpllBaum:
    knoten: list
    erfuellbar: bool | None
    widersprueche: int
    sackgassen: int


class _Abbruch(Exception):
    pass


def dpll_baum(klauseln, regel="erste", knoten_budget=None) -> DpllBaum:
    """Die Suche des Kerns (`kfl_dpll.dpll`) mit aufgezeichnetem Baum. Gleiche Einheiten (`propagiere`, `waehle_variable`),
    gleiche Reihenfolge (erst wahr, dann falsch); die Zähler stimmen mit `kfl_dpll.dpll` überein (Test)."""
    knoten: list[DpllKnoten] = []
    zaehler = {"w": 0, "s": 0}

    def suche(kl, belegung, eltern, wahl, tiefe):
        k = DpllKnoten(len(knoten), eltern, wahl, tiefe)
        knoten.append(k)
        if eltern is not None:
            knoten[eltern].kinder.append(k.id)
        if knoten_budget is not None and len(knoten) > knoten_budget:
            raise _Abbruch
        schritt = propagiere(kl, belegung)
        if schritt is None:
            k.art = "widerspruch"
            zaehler["w"] += 1
            zaehler["s"] += 1
            return None
        kl, belegung = schritt
        if not kl:
            k.art = "loesung"
            return belegung
        v = waehle_variable(kl, regel)
        for wert in (True, False):
            versuch = dict(belegung)
            versuch[v] = wert
            gefunden = suche(kl, versuch, k.id, v if wert else -v, tiefe + 1)
            if gefunden is not None:
                return gefunden
        k.art = "sackgasse"
        zaehler["s"] += 1
        return None

    try:
        gefunden = suche([tuple(c) for c in klauseln], {}, None, None, 0)
    except _Abbruch:
        return DpllBaum(knoten, None, zaehler["w"], zaehler["s"])
    return DpllBaum(knoten, gefunden is not None, zaehler["w"], zaehler["s"])

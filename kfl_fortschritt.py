"""Live-Nachrechnen einer Messzelle mit Fortschrittsanzeige und Zwischenspeicher (nur Bedienung, keine Rechnung).

Jede Formel einer Zelle ist eine Aufgabe: `formel_zeile` rechnet sie mit denselben Aufrufen wie `kfl_messung.messe_zelle` und wird einzeln
zwischengespeichert (`st.cache_data`, höchstens 64 Einträge: gut drei Zellen zu 20 Formeln). Der Fortschrittsbalken zählt die fertigen Formeln;
klickt jemand mit derselben Zelle erneut, kommen alle Zeilen aus dem Zwischenspeicher. Das Ergebnis ist gleich dem von `messe_zelle`
(`tests/test_fortschritt.py`)."""

from contextlib import contextmanager

import streamlit as st

import kfl_constants as C
import kfl_messung as M

_ZAEHLER = {"gerechnet": 0}


def gerechnet() -> int:
    """Wie viele Formeln in diesem Prozess tatsächlich gerechnet (nicht aus dem Zwischenspeicher geholt) wurden; dient der Anzeige und dem Test."""
    return _ZAEHLER["gerechnet"]


@st.cache_data(show_spinner=False, max_entries=64)
def formel_zeile(art: str, parameter: tuple, nr: int) -> dict:
    """Zeile der Formel Nr. `nr` (ab 0) der Zelle (`parameter`: sortierte Paare der Zellenparameter); gleiche Rechnung wie in `messe_zelle`."""
    _ZAEHLER["gerechnet"] += 1
    kennung, inst = M.formeln(art, **dict(parameter))[nr]
    z = M.messe_formel(inst.n, inst.klauseln, C.DPLL_BUDGET[art])
    z["formel"] = kennung
    return z


def zelle(art: str, params: dict, melde=None) -> dict:
    """Die Zelle wie `M.messe_zelle(art, **params)`; `melde(fertig, gesamt)` wird nach jeder Formel aufgerufen."""
    parameter = tuple(sorted(params.items()))
    gesamt = len(M.formeln(art, **params))
    zeilen = []
    for nr in range(gesamt):
        zeilen.append(formel_zeile(art, parameter, nr))
        if melde:
            melde(nr + 1, gesamt)
    return {"art": art, "params": params, "zeilen": zeilen}


@contextmanager
def fortschrittsbalken(text: str):
    """Fortschrittsbalken mit Beschriftung; liefert `melde(fertig, gesamt)` und räumt den Balken am Ende weg."""
    balken = st.progress(0.0, text=text)

    def melde(fertig: int, gesamt: int) -> None:
        balken.progress(fertig / gesamt, text=f"{text}: {fertig} von {gesamt}")

    try:
        yield melde
    finally:
        balken.empty()

"""Abbildungen: Achsen gesperrt, Beschriftungen vollständig (kein Farbcode allein), Implikationsgraph und Suchbaum am Handbeispiel von Hand."""

import pytest

import kfl_algorithm as A
import kfl_constants as C
import kfl_evaluation as E
import kfl_messung as M
import kfl_scenario as S
import kfl_trace as T
import kfl_visualization as V
from kfl_cdcl import Loeser


def _zs(inst):
    n_orig = len(Loeser(inst.n, inst.klauseln).klauseln)
    return T.zustaende(A.cdcl_spur(inst.n, inst.klauseln).spur, n_orig)


def _gesperrt(fig):
    assert fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True


@pytest.mark.parametrize("name", C.BEISPIELE)
def test_jeder_zustand_jedes_beispiels_laesst_sich_zeichnen(name):
    inst = S.beispiel(name, 3)
    for z in _zs(inst):
        _gesperrt(V.build_graph(inst, z))
    _gesperrt(V.build_dpll_baum(inst, A.dpll_baum(inst.klauseln, "erste")))


def test_graph_beim_ersten_konflikt_von_hand(f1):
    z = _zs(f1)[7]                                          # nach „lerne“: Konflikt in K2, 1-UIP x5, Sprung von 5 auf 1
    fig = V.build_graph(f1, z)
    namen = {t.name for t in fig.data}
    assert {"Entscheidung", "erzwungen", "Konflikt", "1-UIP"} <= namen
    texte = [a.text for a in fig.layout.annotations]
    for s in range(0, 6):
        assert f"Stufe {s}" in texte                        # alle Stufen sind beschriftet
    assert any("Sprung von Stufe 5 auf Stufe 1 (überspringt 2, 3, 4)" in t for t in texte)
    assert any("Konfliktseite" in t for t in texte)
    assert len(fig.layout.shapes) == 1 and fig.layout.shapes[0].line.dash == "dash"       # gestrichelter Schnitt
    # Pfeile: Begründungen von x6 (zwei), Konflikt (drei Literale)
    pfeile = [a for a in fig.layout.annotations if a.showarrow]
    assert len(pfeile) == 2 + 3 + 1                         # zwei Folgepfeile, drei zum Konflikt, ein Sprungpfeil


def test_graph_ohne_konflikt_hat_keinen_schnitt(f1):
    z = _zs(f1)[2]
    fig = V.build_graph(f1, z)
    assert not fig.layout.shapes and {t.name for t in fig.data} == {"Entscheidung"}


def test_graph_nach_dem_sprung_zeigt_den_pfeil(f1):
    fig = V.build_graph(f1, _zs(f1)[8])
    assert any("Sprung von Stufe 5 auf Stufe 1" in a.text for a in fig.layout.annotations)


def test_dpll_baum_zeichnet_alle_knoten_von_hand(f1):
    fig = V.build_dpll_baum(f1, A.dpll_baum(f1.klauseln, "erste"))
    anzahl = {t.name: len(t.x) for t in fig.data if t.name}
    assert anzahl["Widerspruch (Blatt)"] == 6 and anzahl["Sackgasse (innerer Knoten, beide Zweige scheitern)"] == 5
    assert anzahl["Lösung"] == 1 and anzahl["Knoten auf dem Weg zur Lösung"] == 2


def test_wachstum_figur_hat_drei_serien_mit_beschriftung():
    reihe = E.wachstum_serie(M.lade_vorgerechnet(), 4.26)
    fig = V.build_wachstum(reihe)
    namen = [t.name for t in fig.data if t.name]
    assert namen == ["CDCL: Konflikte", "DPLL: Widersprüche (Vergleichsmaß)", "DPLL: Sackgassen (Nebenzahl)"]
    assert list(fig.data[1].x) == list(C.N_ZUFALL)
    assert fig.layout.yaxis.type == "log" and all(y > 0 for t in fig.data for y in t.y)
    _gesperrt(fig)


def test_familie_und_verteilung():
    vorg = M.lade_vorgerechnet()
    zeilen = [(f"Schubfach h = {h}", E.zusammenfassung(vorg[M.schluessel("schubfach", h=h)]["zeilen"])) for h in C.SCHUBFACH_H]
    fig = V.build_familie(zeilen, "Schubfach h = 5")
    assert list(fig.data[0].x)[2].startswith("▶ ") and not list(fig.data[0].x)[0].startswith("▶")
    assert list(fig.data[0].y) == [7, 28, 159, 1004, 4811, 27932] and list(fig.data[1].y) == [6, 24, 120, 720, 5040, 40320]
    _gesperrt(fig)
    v = V.build_verteilung({1: 5, 2: 3}, {1: 6, 3: 1}, "Länge")
    assert [t.name for t in v.data] == ["ohne Minimieren", "mit Minimieren"] and list(v.data[0].x) == [1, 2]
    _gesperrt(v)

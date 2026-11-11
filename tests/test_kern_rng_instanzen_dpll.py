"""Regressionstests der kopierten Kern-Module rng, instanzen, dpll (aus sat-cp-planung/kern/tests, Importe auf das Präfix kfl_ umgestellt).
Vergleiche mit Originalen in anderen Demo-Ordnern überspringen sich, wenn diese nicht neben dem Repo liegen."""
import sys
from pathlib import Path

import pytest

import kfl_instanzen as I
from kfl_cdcl import solve
from kfl_dpll import dpll
from kfl_rng import SplitMix64

PROJEKTE = Path(__file__).resolve().parents[2]   # Projects-Ordner (Originale nur, wenn sie dort liegen)


def lade_original(ordner, modul):
    pfad = PROJEKTE / ordner
    if not (pfad / f"{modul}.py").exists():
        pytest.skip(f"{ordner}/{modul}.py nicht vorhanden")
    sys.path.insert(0, str(pfad))
    try:
        return __import__(modul)
    finally:
        sys.path.remove(str(pfad))


def test_splitmix_bekannte_werte():
    # Veröffentlichte Referenzwerte der SplitMix64-Konvention für Seed 0 (Vigna)
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    assert SplitMix64(12345).next() == 2454886589211414944


def test_splitmix_gleich_dem_original():
    red = lade_original("reduktionskette-demo", "red_scenario")
    a, b = SplitMix64(99), red.SplitMix64(99)
    for _ in range(50):
        assert a.next() == b.next()
    assert [SplitMix64(7).below(10) for _ in range(1)] == [red.SplitMix64(7).below(10)]


def test_hilfsmethoden():
    g = SplitMix64(5)
    xs = [g.random() for _ in range(1000)]
    assert all(0 <= x < 1 for x in xs) and 0.45 < sum(xs) / 1000 < 0.55
    liste = list(range(20))
    SplitMix64(3).shuffle(liste)
    assert sorted(liste) == list(range(20)) and liste != list(range(20))
    probe = SplitMix64(3).sample(range(50), 7)
    assert len(set(probe)) == 7
    assert SplitMix64(3).sample(range(50), 7) == probe          # deterministisch
    assert SplitMix64(1).randrange(10) == SplitMix64(1).below(10)


def test_rand3_gleich_dem_original_und_praefix():
    red = lade_original("reduktionskette-demo", "red_scenario")
    for n, m, seed in [(5, 3, 7), (30, 128, 11), (60, 270, 4)]:
        assert I.rand3(n, m, seed).klauseln == red.random_formula(n, m, seed)
    kurz, lang = I.rand3(20, 30, 1).klauseln, I.rand3(20, 40, 1).klauseln
    assert lang[:30] == kurz                                      # wächst m, bleiben die früheren Klauseln
    assert all(len({abs(l) for l in c}) == 3 for c in lang)


def test_schubfach_handwerte():
    inst = I.pigeonhole(2)                      # 3 Tauben, 2 Löcher
    assert inst.n == 6
    assert len(inst.klauseln) == 3 + 2 * 3     # 3 Taubenklauseln, je Loch 3 Paare
    assert (1, 2) in inst.klauseln and (-1, -3) in inst.klauseln
    assert solve(inst.n, inst.klauseln).antwort is False


def test_schur_grenze():
    assert solve(*I.schur(13, 3)[:2]).antwort is True
    assert solve(*I.schur(14, 3)[:2]).antwort is False           # S(3) = 13
    inst = I.schur(13, 3)
    erg = solve(inst.n, inst.klauseln)
    for menge in I.schur_mengen(inst, erg.modell):
        for a in menge:
            for b in menge:
                assert a + b not in menge


def test_faerbung_dreieck():
    dreieck = I.faerbung(3, [(0, 1), (1, 2), (0, 2)], 2)
    assert solve(dreieck.n, dreieck.klauseln).antwort is False
    drei = I.faerbung(3, [(0, 1), (1, 2), (0, 2)], 3)
    erg = solve(drei.n, drei.klauseln)
    assert erg.antwort is True
    farben = I.faerbung_aus_modell(drei, erg.modell)
    assert len(set(farben)) == 3


def test_flat_graph_und_rampen_deterministisch():
    a, b = I.flat_graph(40, 4.0, 3), I.flat_graph(40, 4.0, 3)
    assert a.klauseln == b.klauseln and len(a.meta["kanten"]) == 80
    assert a.klauseln != I.flat_graph(40, 4.0, 4).klauseln
    r = I.rampen_instanz(30, 3.0, 2, 4)
    assert r.meta["einkleidung"] == "rampen" and r.meta["rampen"] == 4
    with pytest.raises(ValueError):
        I.zufallskanten(4, 7, 0)


def test_pruefe_modell():
    assert I.pruefe_modell([(1, 2), (-1, 2)], {1: True, 2: True})
    assert not I.pruefe_modell([(1, 2), (-1, -2)], {1: True, 2: True})


def test_dpll_regression_schubfach():
    # Phasenübergang-Demo (Komplexitätsklassen 4): 11 / 47 / 239 / 1 439 Knoten; bei unerfüllbaren Formeln ist jeder Knoten eine Sackgasse
    erwartet = {3: 11, 4: 47, 5: 239, 6: 1439}
    for h, knoten in erwartet.items():
        r = dpll(I.pigeonhole(h).klauseln)
        assert r.erfuellbar is False and r.knoten == knoten and r.sackgassen == knoten


def test_dpll_gleich_dem_original_auf_zufallsformeln():
    orig = lade_original("sat-phasenuebergang-demo", "sph_dpll")
    for seed in range(12):
        f = I.rand3(25, 107, seed).klauseln
        mein, alt = dpll(f), orig.dpll(f)
        assert mein.erfuellbar == alt.satisfiable and mein.knoten == alt.nodes


def test_dpll_handbeispiel_und_budget():
    # (x1)(¬x1 ∨ x2)(¬x2 ∨ x3): drei Einheitsschritte, kein Verzweigen, ein Knoten
    r = dpll([(1,), (-1, 2), (-2, 3)])
    assert r.erfuellbar and r.knoten == 1 and r.sackgassen == 0 and r.einheitsschritte == 3
    assert r.belegung == {1: True, 2: True, 3: True}
    assert dpll(I.pigeonhole(6).klauseln, knoten_budget=100).erfuellbar is None

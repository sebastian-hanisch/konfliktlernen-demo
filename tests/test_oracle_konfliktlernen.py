"""Orakel-Tests Konfliktlernen: CDCL und DPLL gegen unabhängige Rechenwege (alles in diesem Test geschrieben, kein Kern-Code).

Orakel: (1) Brute Force über alle Belegungen (n ≤ 12), (2) OR-Tools CP-SAT für Erfüllbarkeit (nur Test, überspringt sich ohne OR-Tools),
(3) ein eigener, mengenbasierter DPLL-Zähler für Widersprüche und Sackgassen, (4) ein eigener RUP-Prüfer für jede gelernte Klausel,
(5) Handwerte (Handbeispiel F1, Schubfach h = 2). Dazu Eigenschaften: Umbenennen der Variablen und Vertauschen der Klauseln ändern die Antwort nie,
ein Modell erfüllt jede Klausel, mehr Klauseln machen eine unerfüllbare Formel nicht erfüllbar, 1-UIP und Sprungstufe."""

import itertools

import pytest

import kfl_algorithm as A
import kfl_instanzen as I
import kfl_scenario as S
import kfl_trace as T
from kfl_cdcl import Loeser, solve
from kfl_dpll import dpll
from kfl_rng import SplitMix64


# ---------------------------------------------------------------------------------------------------------------- unabhängige Orakel
def brute_force(n, klauseln):
    for bits in itertools.product([False, True], repeat=n):
        if all(any(bits[abs(l) - 1] == (l > 0) for l in c) for c in klauseln):
            return True
    return False


def hat_modell(klauseln, modell):
    return all(any(modell[abs(l)] == (l > 0) for l in c) for c in klauseln)


def rup(klauseln, c):
    """Folgt c aus den Klauseln durch Einheitspropagation unter der Verneinung von c? (eigene Schleife, nicht der Prüfer des Kerns)"""
    wert = {abs(l): l < 0 for l in c}
    aenderung = True
    while aenderung:
        aenderung = False
        for k in klauseln:
            if any(wert.get(abs(l)) == (l > 0) for l in k):
                continue
            frei = [l for l in k if abs(l) not in wert]
            if not frei:
                return True
            if len(frei) == 1:
                wert[abs(frei[0])] = frei[0] > 0
                aenderung = True
    return False


def dpll_zaehler(klauseln):
    """Eigene Fassung der Suche mit kleinster Variablennummer zuerst, wahr zuerst: liefert (Widersprüche, Sackgassen, erfüllbar)."""
    z = {"w": 0, "s": 0}

    def propagiere(kl, bel):
        bel = dict(bel)
        while True:
            offen = []
            einheit = None
            for c in kl:
                if any(bel.get(abs(l)) == (l > 0) for l in c):
                    continue
                rest = [l for l in c if abs(l) not in bel]
                if not rest:
                    return None, bel
                if len(rest) == 1 and einheit is None:
                    einheit = rest[0]
                offen.append(rest)
            if einheit is None:
                return offen, bel
            bel[abs(einheit)] = einheit > 0
            kl = offen

    def suche(kl, bel):
        offen, bel = propagiere(kl, bel)
        if offen is None:
            z["w"] += 1
            z["s"] += 1
            return False
        if not offen:
            return True
        v = min(abs(l) for c in offen for l in c)
        for wert in (True, False):
            if suche(offen, {**bel, v: wert}):
                return True
        z["s"] += 1
        return False

    erf = suche([list(c) for c in klauseln], {})
    return z["w"], z["s"], erf


# ------------------------------------------------------------------------------------------------------------------------ Handwerte
def test_handwerte_f1_gegen_den_unabhaengigen_zaehler(f1):
    assert dpll_zaehler(f1.klauseln) == (6, 11, True)
    erg = solve(f1.n, f1.klauseln, vsids=False, startphase=True, restarts="none")
    assert erg.antwort is True and erg.stat["konflikte"] == 2


def test_handwert_schubfach_h2():
    """3 Tauben, 2 Löcher: DPLL 3 Knoten (Wurzel, zwei Kinder), 2 Widersprüche, 3 Sackgassen; unerfüllbar."""
    inst = I.pigeonhole(2)
    assert dpll_zaehler(inst.klauseln) == (2, 3, False)
    assert solve(inst.n, inst.klauseln).antwort is False
    assert brute_force(inst.n, inst.klauseln) is False


# --------------------------------------------------------------------------------------------------- Antworten gegen Brute Force und DPLL
def test_antwort_gleich_brute_force_bis_n_12():
    erf = unerf = 0
    for seed in range(60):
        n = 6 + seed % 7
        inst = I.rand3(n, round(4.26 * n), seed)
        erwartet = brute_force(inst.n, inst.klauseln)
        erf += erwartet
        unerf += not erwartet
        for opt in ({}, {"learn": False}, {"minimize": True}, {"vsids": False, "startphase": True}, {"watch": False}):
            erg = solve(inst.n, inst.klauseln, **opt)
            assert erg.antwort is erwartet, (seed, opt)
            if erwartet:
                assert hat_modell(inst.klauseln, erg.modell)
    assert erf >= 10 and unerf >= 10


def test_antwort_gleich_dpll_bis_n_30():
    for seed in range(40):
        n = 20 + seed % 11
        inst = I.rand3(n, round(4.26 * n), seed)
        _, _, erf = dpll_zaehler(inst.klauseln)
        assert solve(inst.n, inst.klauseln).antwort is erf, seed
        assert dpll(inst.klauseln).erfuellbar is erf


def test_widersprueche_und_sackgassen_gleich_dem_eigenen_zaehler():
    """Der Kern-DPLL mit Regel „erste“ und der Suchbaum der Demo zählen wie der unabhängige Zähler (60 Formeln)."""
    for seed in range(60):
        n = 8 + seed % 9
        kl = I.rand3(n, round(4.26 * n), seed).klauseln
        w, s, erf = dpll_zaehler(kl)
        kern = dpll(kl, regel="erste")
        baum = A.dpll_baum(kl, "erste")
        assert (kern.widersprueche, kern.sackgassen, kern.erfuellbar) == (w, s, erf), seed
        assert (baum.widersprueche, baum.sackgassen, baum.erfuellbar) == (w, s, erf), seed


def test_unerfuellbar_sackgassen_sind_zwei_mal_widersprueche_minus_eins():
    """Mathematik der Zählweise: der Suchbaum ist binär, bei unerfüllbaren Formeln sind alle Blätter Widersprüche: Knoten N = 2W − 1 = S."""
    gesehen = 0
    for seed in range(150):
        kl = I.rand3(14, 60, seed).klauseln
        w, s, erf = dpll_zaehler(kl)
        if not erf:
            assert s == 2 * w - 1
            gesehen += 1
    assert gesehen >= 20
    for h in (2, 3, 4, 5):
        w, s, _ = dpll_zaehler(I.pigeonhole(h).klauseln)
        assert s == 2 * w - 1


# ----------------------------------------------------------------------------------------------------------------------------- CP-SAT
def cpsat(n, klauseln):
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")
    m = cp_model.CpModel()
    x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, n + 1)]
    for c in klauseln:
        m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in c])
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    s.parameters.max_time_in_seconds = 60
    return {cp_model.OPTIMAL: True, cp_model.INFEASIBLE: False}[s.Solve(m)]


def test_antwort_gleich_cpsat_auf_40_zufallsformeln_und_schubfach():
    for seed in range(40):
        n = 30 + (seed * 3) % 31
        inst = I.rand3(n, round(4.26 * n), seed)
        erwartet = cpsat(inst.n, inst.klauseln)
        erg = solve(inst.n, inst.klauseln)
        assert erg.antwort is erwartet, seed
        if erwartet:
            assert hat_modell(inst.klauseln, erg.modell)
    for h in (5, 6):
        inst = I.pigeonhole(h)
        assert cpsat(inst.n, inst.klauseln) is False and solve(inst.n, inst.klauseln).antwort is False


# --------------------------------------------------------------------------------------------------------------- Eigenschaften je Konflikt
def test_jede_gelernte_klausel_folgt_per_rup_aus_den_klauseln_davor():
    pruefungen = 0
    for inst in [I.rand3(40, 170, 1), I.rand3(50, 213, 2), I.pigeonhole(4), I.pigeonhole(5), I.schur(13, 3), I.flat_graph(40, 4.5, 3)]:
        for minimieren in (False, True):
            erg = solve(inst.n, inst.klauseln, proof=True, minimize=minimieren)
            db = [list(c) for c in inst.klauseln]
            for art, c in erg.beweis:
                if art != "a":
                    continue
                assert rup(db, c), (inst.meta, c)
                db.append(list(c))
                pruefungen += 1
            if erg.antwort is False:
                assert erg.beweis[-1] == ("a", [])
    assert pruefungen > 200


def test_gelernte_klausel_ist_falsch_unter_der_belegung_des_konflikts_und_1uip():
    """Je Konflikt: die gelernte Klausel enthält genau ein Literal der Konfliktstufe, alle ihre Literale sind unter der Belegung falsch, die Sprungstufe liegt darunter."""
    n_konflikte = 0
    for inst in [S.beispiel("Zufalls-3-SAT, n = 12", s) for s in range(1, 11)] + [I.pigeonhole(3), S.beispiel("Handbeispiel F1")]:
        n_orig = len(Loeser(inst.n, inst.klauseln).klauseln)
        erg = A.cdcl_spur(inst.n, inst.klauseln)
        for z in T.zustaende(erg.spur, n_orig):
            if z.ereignis[0] != "lerne":
                continue
            klausel, rueck, _lbd, stufe = z.gelernt
            wahr = {x.lit: x.stufe for x in z.trail}
            assert all(-q in wahr for q in klausel)                                  # unter der Belegung falsch
            assert sum(1 for q in klausel if wahr[-q] == stufe) == 1
            assert rueck < stufe
            assert rueck == max([wahr[-q] for q in klausel if wahr[-q] < stufe] + [0])
            n_konflikte += 1
    assert n_konflikte >= 20


def test_konflikt_in_stufe_0_ist_unerfuellbar_ohne_lernen():
    erg = solve(2, [(1,), (-1, 2), (-1, -2)])
    assert erg.antwort is False and erg.stat["gelernt"] == 0


# ----------------------------------------------------------------------------------------------------------------------- Invarianzen
def _umbenennen(klauseln, n, seed):
    perm = list(range(1, n + 1))
    SplitMix64(seed).shuffle(perm)
    return [tuple((perm[abs(l) - 1]) * (1 if l > 0 else -1) for l in c) for c in klauseln]


def test_umbenennen_und_vertauschen_aendern_die_antwort_nie():
    for seed in range(30):
        n = 25 + seed % 10
        inst = I.rand3(n, round(4.26 * n), seed)
        antwort = solve(inst.n, inst.klauseln).antwort
        umbenannt = _umbenennen(inst.klauseln, n, seed + 100)
        assert solve(n, umbenannt).antwort is antwort, seed
        gemischt = list(inst.klauseln)
        SplitMix64(seed + 7).shuffle(gemischt)
        assert solve(n, gemischt).antwort is antwort, seed


def test_mehr_klauseln_machen_unerfuellbares_nicht_erfuellbar():
    for seed in range(40):
        n = 20 + seed % 10
        inst = I.rand3(n, round(4.8 * n), seed)
        if solve(n, inst.klauseln).antwort is False:
            plus = list(inst.klauseln) + [(1, -2, 3), (-1, 2, -3), (4, 5, 6)]
            assert solve(n, plus).antwort is False


def test_modell_erfuellt_jede_klausel_auf_strukturierten_instanzen():
    for inst in [I.schur(13, 3), I.flat_graph(40, 4.0, 2), I.rampen_instanz(30, 4.0, 1, 3)]:
        erg = solve(inst.n, inst.klauseln)
        assert erg.antwort is True and hat_modell(inst.klauseln, erg.modell)
    assert solve(*I.schur(14, 3)[:2]).antwort is False        # S(3) = 13


# ------------------------------------------------------------------------------------------------------------------------- Randfälle
def test_randfaelle():
    assert solve(3, []).antwort is True                                  # leere Formel
    assert solve(3, [()]).antwort is False                               # leere Klausel
    assert solve(1, [(1,)]).antwort is True and solve(1, [(1,), (-1,)]).antwort is False
    assert solve(2, [(1, -1), (2,)]).antwort is True                     # Tautologie
    assert solve(2, [(1, 1, 2), (-1, -1), (-2, -2)]).antwort is False    # doppelte Literale
    erg = solve(3, [(1,), (-1, 2), (-2, 3)])                             # Einheitsklauseln auf Stufe 0
    assert erg.antwort is True and erg.modell == {1: True, 2: True, 3: True} and erg.stat["entscheidungen"] == 0
    inst = I.pigeonhole(6)
    knapp = solve(inst.n, inst.klauseln, conflict_budget=20)
    assert knapp.antwort is None and knapp.modell is None             # Budget: unbekannt, nie als unerfüllbar gemeldet
    assert dpll(inst.klauseln, knoten_budget=30).erfuellbar is None

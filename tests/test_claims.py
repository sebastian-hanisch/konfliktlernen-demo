"""Jede Zahl der README („Befunde“) wird hier nachgerechnet: aus den vorgerechneten Zellen (`kfl_vorgerechnet.json`, Skript `tools/messe_vorgerechnet.py`)
mit denselben Auswertungsfunktionen wie in der App, als Median über die festen Formeln. Die Handwerte (Handbeispiel F1, Schubfach h = 2) rechnet der Test frisch.
Die Zeilen der kleinen Zellen vergleicht `tests/test_messung.py` mit frisch gerechneten; für die großen (n ≥ 90) steht die Messung nur in der Datei.

Zuordnung README-Zeile → Test: Handbeispiel (test_claim_handbeispiel_*), Zählweise (test_claim_zaehlweise_*), Wachstum (test_claim_wachstum_*),
Verhältnis m/n (test_claim_verhaeltnis_*), Rampen (test_claim_rampen_*), Schur (test_claim_schur_*), Schubfach (test_claim_schubfach_*),
Was wird gelernt (test_claim_lernen_*), Presets (test_claim_presets_*), Testzahl (test_claim_testzahl)."""

import math
from statistics import median
import re
import subprocess
import sys
from pathlib import Path

import pytest

import kfl_algorithm as A
import kfl_constants as C
import kfl_evaluation as E
import kfl_messung as M
import kfl_presets as P
import kfl_scenario as S
from kfl_dpll import dpll
from kfl_instanzen import rand3

ROOT = Path(__file__).resolve().parent.parent
VORG = M.lade_vorgerechnet()


def zelle(art, **p):
    return E.zusammenfassung(VORG[M.schluessel(art, **p)]["zeilen"])


def q2(s):
    return round(E.quotient(s), 2)


# ------------------------------------------------------------------------------------------------------------------------ Handbeispiel
def test_claim_handbeispiel_f1():
    f1 = S.beispiel(C.BEISPIEL_F1)
    r = dpll(f1.klauseln, regel="erste")
    assert (r.knoten, r.widersprueche, r.sackgassen) == (14, 6, 11)
    erg = A.cdcl_spur(f1.n, f1.klauseln)
    assert erg.stat["konflikte"] == 2
    lerne = [e for e in erg.spur if e[0] == "lerne"]
    assert [sorted(e[1], key=abs) for e in lerne] == [[-1, -5], [-1]] and [e[2] for e in lerne] == [1, 0]
    konflikte = [e for e in erg.spur if e[0] == "konflikt"]
    assert [sorted(e[1], key=abs) for e in konflikte] == [[-1, -5, -6], [-1, 5, -6]]       # K2 und K4 verletzt
    assert [e[2] for e in konflikte] == [5, 1]                                             # Konfliktstufen: Sprung 5 → 1 überspringt die Stufen 2, 3, 4; dann 1 → 0


def test_claim_handbeispiel_schubfach_h2():
    r = dpll(S.beispiel(C.BEISPIEL_PHP2).klauseln, regel="haeufigste")
    assert (r.knoten, r.widersprueche, r.sackgassen) == (3, 2, 3)


# --------------------------------------------------------------------------------------------------------------------------- Zählweise
def test_claim_zaehlweise_unerfuellbar_sackgassen_zwei_w_minus_eins():
    zeilen = [r for k, z in VORG.items() if z["art"] != "lernen" for r in z["zeilen"] if r["antwort"] is False]
    assert len(zeilen) == 228
    assert all(r["sackgassen"] == 2 * r["widersprueche"] - 1 for r in zeilen)


def test_claim_zaehlweise_median_sackgassen_je_widerspruch_bei_4_26():
    werte = {n: round(zelle("zufall", n=n, v=4.26)["sack_je_wid"], 2) for n in (50, 70, 90, 110)}
    assert werte == {50: 1.94, 70: 1.98, 90: 1.98, 110: 1.99}


# ----------------------------------------------------------------------------------------------------------------------------- Wachstum
WACHS_426 = {30: (14.5, 6.5, 0.45, 12, 10), 50: (35, 39.5, 1.13, 13, 75.5), 70: (89, 104, 1.17, 11, 205), 90: (159, 343.5, 2.16, 13, 680), 110: (287, 1014.5, 3.53, 13, 2024.5)}


@pytest.mark.parametrize("n", C.N_ZUFALL)
def test_claim_wachstum_zufall_4_26(n):
    s = zelle("zufall", n=n, v=4.26)
    k, w, q, erf, sg = WACHS_426[n]
    assert (s["konflikte"]["median"], s["widersprueche"]["median"], q2(s), s["erfuellbar"], s["sackgassen"]["median"]) == (k, w, q, erf, sg)
    assert s["formeln"] == 20 and s["abbruch_cdcl"] == s["abbruch_dpll"] == 0


def test_claim_wachstum_streuung_mit_der_formelmenge():
    """Andere feste Formelmengen (Zufalls-Seeds 21 bis 40 und 41 bis 60, m/n = 4,26): der Quotient streut bei n = 30 bis 70 um mehrere Zehntel."""
    erwartet = {(21, 30): 0.88, (21, 50): 0.81, (21, 70): 1.45, (41, 30): 0.84, (41, 50): 1.18, (41, 70): 0.9}
    for (lo, n), q in erwartet.items():
        zeilen = [M.messe_formel(n, rand3(n, round(4.26 * n), seed).klauseln, C.DPLL_BUDGET["zufall"]) for seed in range(lo, lo + 20)]
        assert round(median(z["widersprueche"] for z in zeilen) / median(z["konflikte"] for z in zeilen), 2) == q, (lo, n)


def test_claim_wachstum_vorsprung_erst_ab_n_90():
    """Quotient unter 1,2 bei n = 30, 50, 70 („kein Vorsprung“ laut Verdikt), über 2 bei n = 90 und 110."""
    arten = {n: E.verdict_vergleich(zelle("zufall", n=n, v=4.26), "x")[0] for n in C.N_ZUFALL}
    assert arten == {30: "warning", 50: "info", 70: "info", 90: "success", 110: "success"}
    qs = [E.quotient(zelle("zufall", n=n, v=4.26)) for n in C.N_ZUFALL]
    assert qs == sorted(qs)                                                    # wächst in allen vier Schritten
    assert qs[3] > 2 and qs[4] > 3 and qs[2] < 1.2


# ---------------------------------------------------------------------------------------------------------------------- Verhältnis m/n
def test_claim_verhaeltnis_quotienten_und_monotonie():
    q40 = [q2(zelle("zufall", n=n, v=4.0)) for n in C.N_ZUFALL]
    q45 = [q2(zelle("zufall", n=n, v=4.5)) for n in C.N_ZUFALL]
    assert q40 == [0.24, 0.97, 0.8, 1.52, 0.84]
    assert q45 == [0.68, 1.05, 1.24, 1.42, 2.17]
    assert q45 == sorted(q45) and q40 != sorted(q40)                           # bei m/n = 4,0 kein monotones Wachsen
    assert [zelle("zufall", n=n, v=4.0)["erfuellbar"] for n in (90, 110)] == [19, 20]
    assert [zelle("zufall", n=n, v=4.5)["erfuellbar"] for n in C.N_ZUFALL] == [11, 9, 5, 5, 5]


# ------------------------------------------------------------------------------------------------------------------------------ Rampen
RAMPEN = {4.5: [(15, 15, 1.0, 2), (19.5, 31.5, 1.62, 7), (29.5, 53, 1.8, 9)], 5.0: [(13.5, 15, 1.11, 1), (24, 29.5, 1.23, 0), (40, 60, 1.5, 0)],
          4.0: [(3, 5.5, 1.83, 14), (3.5, 3, 0.86, 19), (7, 6, 0.86, 18)]}


@pytest.mark.parametrize("grad", list(RAMPEN))
def test_claim_rampen_drei_rampen(grad):
    for n, (k, w, q, erf) in zip(C.RAMPEN_N, RAMPEN[grad]):
        s = zelle("rampen", n=n, g=grad)
        assert (s["konflikte"]["median"], s["widersprueche"]["median"], q2(s), s["erfuellbar"]) == (k, w, q, erf), (n, grad)


# -------------------------------------------------------------------------------------------------------------------------------- Schur
def test_claim_schur_k3():
    n13, n14 = zelle("schur", k=3, n=13), zelle("schur", k=3, n=14)
    assert (n13["erfuellbar"], n13["konflikte"]["median"], n13["widersprueche"]["median"]) == (1, 18, 10)
    assert (n14["erfuellbar"], n14["konflikte"]["median"], n14["widersprueche"]["median"], n14["sackgassen"]["median"]) == (0, 148, 147, 293)
    assert q2(n14) == 0.99


# ---------------------------------------------------------------------------------------------------------------------------- Schubfach
def test_claim_schubfach_zaehler_und_quotienten():
    k = [zelle("schubfach", h=h)["konflikte"]["median"] for h in C.SCHUBFACH_H]
    w = [zelle("schubfach", h=h)["widersprueche"]["median"] for h in C.SCHUBFACH_H]
    assert k == [7, 28, 159, 1004, 4811, 27932]
    assert w == [6, 24, 120, 720, 5040, 40320] == [math.factorial(h) for h in C.SCHUBFACH_H]       # gemessen: genau h! Widersprüche
    assert [q2(zelle("schubfach", h=h)) for h in C.SCHUBFACH_H] == [0.86, 0.86, 0.75, 0.72, 1.05, 1.44]
    arten = [E.verdict_zelle("schubfach", {"h": h}, zelle("schubfach", h=h), "x")[0] for h in C.SCHUBFACH_H]
    assert arten == ["warning"] * 5 + ["success"]                                           # h = 3…7: „gegenüber diesem DPLL kein Vorsprung“ (Quotient unter 1,2), h = 8: Vorsprung 1,44
    assert [round(x, 1) for x in E.wachstumsfaktoren([(h, zelle("schubfach", h=h)) for h in C.SCHUBFACH_H])["konflikte"]] == [4.0, 5.7, 6.3, 4.8, 5.8]
    assert E.satz_wachstumsfaktoren([(h, zelle("schubfach", h=h)) for h in C.SCHUBFACH_H]) == \
        "Von Zelle zu Zelle wächst der CDCL-Median um das 4,0- bis 6,3-Fache, der DPLL-Median um das 4,0- bis 8,0-Fache."


# ---------------------------------------------------------------------------------------------------------------------------- Was gelernt
def test_claim_lernen_n50_und_n150():
    erwartet = {50: (22, 22, 5.1, 4.4, (3, 6, 3), 14.8, 12.2, 1.2, 1.2), 150: (3370, 2845.5, 11.9, 9.5, (7, 0, 5), 13.3, 12.8, 1.2, 1.2)}
    for n, (m0, m1, l0, l1, (wen, gl, meh), w0, w1, s0, s1) in erwartet.items():
        a = E.lern_summe(VORG[M.schluessel("lernen", n=n, min=0)]["zeilen"])
        b = E.lern_summe(VORG[M.schluessel("lernen", n=n, min=1)]["zeilen"])
        assert (a["median"], b["median"]) == (m0, m1) and a["formeln"] == 12 and a["abbrueche"] == b["abbrueche"] == 0
        assert (round(a["mittlere_laenge"], 1), round(b["mittlere_laenge"], 1)) == (l0, l1)
        paare = list(zip(a["konflikte"], b["konflikte"]))
        assert (sum(1 for x, y in paare if y < x), sum(1 for x, y in paare if y == x), sum(1 for x, y in paare if y > x)) == (wen, gl, meh)
        assert (round(a["anteil_weit"], 1), round(b["anteil_weit"], 1)) == (w0, w1)
        assert (round(a["mittel_sprung"], 1), round(b["mittel_sprung"], 1)) == (s0, s1)
    a, b = (E.lern_summe(VORG[M.schluessel("lernen", n=150, min=m)]["zeilen"]) for m in (0, 1))
    assert round(100 * (a["median"] - b["median"]) / a["median"], 1) == 15.6


def test_claim_lernen_n150_konflikte_je_formel():
    a = E.lern_summe(VORG[M.schluessel("lernen", n=150, min=0)]["zeilen"])
    assert a["konflikte"] == [627, 4924, 4302, 5586, 5928, 3390, 3350, 1195, 3623, 2353, 1348, 166]


# -------------------------------------------------------------------------------------------------------------------------------- Presets
def test_claim_presets_zeigen_diese_zellen():
    assert P.PRESETS[C.PRESET_RAMPEN]["familie"] == "Rampen-Färbung n = 30, Grad 4,5 (3 Rampen)"
    assert P.PRESETS[C.PRESET_SCHUBFACH]["familie"] == "Schubfach h = 5"
    assert zelle("schubfach", h=5)["konflikte"]["median"] == 159


# -------------------------------------------------------------------------------------------------------------------------- Zufallsquelle
def test_claim_kein_python_random_und_kein_hash_im_code():
    """README „Modell“: Python-`random` und `hash()` kommen nirgends vor (alle Quelldateien im Wurzelordner, per Syntaxbaum)."""
    import ast
    for pfad in sorted(ROOT.glob("*.py")) + sorted((ROOT / "tools").glob("*.py")):
        baum = ast.parse(pfad.read_text(encoding="utf-8"))
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Import):
                assert "random" not in [a.name for a in knoten.names], pfad.name
            if isinstance(knoten, ast.ImportFrom):
                assert knoten.module != "random", pfad.name
            if isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name):
                assert knoten.func.id != "hash", pfad.name


# ---------------------------------------------------------------------------------------------------------------------------- Testzahl
def test_claim_testzahl():
    """Die Gesamtzahl „N Tests“ der README stimmt mit der gesammelten Zahl überein (Teilzahlen vor einer Testdatei zählen nicht)."""
    ausgabe = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "tests", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True,
                             text=True, encoding="utf-8", timeout=300, check=False).stdout
    m = re.search(r"(\d+)(?:/\d+)? tests? collected", ausgabe)
    gesammelt = int(m.group(1)) if m else len([z for z in ausgabe.splitlines() if "::" in z])
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    zahlen = [int(x.replace(".", "")) for x in re.findall(r"(?<![\w.,/])(\d+(?:\.\d{3})*)[ \t ]+Tests\b", readme)]
    assert len(zahlen) == 1 and zahlen[0] == gesammelt, (zahlen, gesammelt)

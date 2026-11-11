"""Messzellen: die vorgerechnete Datei ist vollständig, stimmt mit den Modulen überein und gleicht frisch gerechneten Zellen; CDCL und DPLL widersprechen sich nie."""

import json

import pytest

import kfl_constants as C
import kfl_messung as M

VORG = M.lade_vorgerechnet()


def test_datei_enthaelt_jede_zelle_der_app():
    erwartet = {schl for schl, _ in M.alle_zellen()}
    assert set(VORG) == erwartet
    assert len(erwartet) == 15 + 9 + 5 + 6 + 4


def test_zeilenzahl_je_zelle():
    for schl, z in VORG.items():
        art = z["art"]
        erwartet = {"zufall": len(C.SWEEP_SEEDS), "rampen": len(C.SWEEP_SEEDS), "schur": 1, "schubfach": 1, "lernen": len(C.LERN_SEEDS)}[art]
        assert len(z["zeilen"]) == erwartet, schl


def test_meta_nennt_seeds_budgets_und_kern_versionen():
    meta = M.lade_meta()
    assert meta["seeds"] == list(C.SWEEP_SEEDS) and meta["lern_seeds"] == list(C.LERN_SEEDS)
    assert meta["cdcl_budget"] == C.CDCL_BUDGET and meta["dpll_budget"] == C.DPLL_BUDGET
    for modul, version in meta["kern"].items():
        kopf = (M.JSON_PFAD.parent / f"kfl_{modul}.py").read_text(encoding="utf-8").splitlines()[0]
        assert f"Kern-Version {version}:" in kopf, modul


def test_cdcl_und_dpll_widersprechen_sich_in_keiner_zeile():
    """In jeder vorgerechneten Zeile (ohne Abbrüche) stimmen die Antworten überein; bei unerfüllbar ist Sackgassen = 2·Widersprüche − 1."""
    geprueft = unerf = 0
    for schl, z in VORG.items():
        if z["art"] == "lernen":
            continue
        for r in z["zeilen"]:
            if r["antwort"] is None or r["dpll_antwort"] is None:
                continue
            assert r["antwort"] == r["dpll_antwort"], (schl, r["formel"])
            geprueft += 1
            if r["antwort"] is False:
                assert r["sackgassen"] == 2 * r["widersprueche"] - 1 == r["knoten"], (schl, r["formel"])
                unerf += 1
            else:
                assert r["widersprueche"] <= r["sackgassen"] < r["knoten"]
    assert geprueft == 15 * 20 + 9 * 20 + 5 + 6 and unerf > 150


def test_kein_abbruch_in_den_vorgerechneten_zellen():
    for schl, z in VORG.items():
        for r in z["zeilen"]:
            assert r["antwort"] is not None, schl
            if z["art"] != "lernen":
                assert r["dpll_antwort"] is not None, schl


def test_lernzellen_protokoll_ist_konsistent():
    for schl, z in VORG.items():
        if z["art"] != "lernen":
            continue
        for r in z["zeilen"]:
            assert sum(r["laengen"].values()) == sum(r["spruenge"].values()) == r["gelernt"]
            assert sum(int(k) * v for k, v in r["laengen"].items()) == r["literale"]
            assert r["gelernt"] in (r["konflikte"], r["konflikte"] - 1)
            assert min(int(k) for k in r["spruenge"]) >= 1


ZELLEN_LIVE = [("zufall", {"n": n, "v": v}) for n in (30, 50) for v in C.VERHAELTNISSE] + [("zufall", {"n": 70, "v": 4.26})] \
    + [("rampen", {"n": 30, "g": g}) for g in C.RAMPEN_GRAD] + [("schur", {"k": 3, "n": n}) for n in C.SCHUR_N] \
    + [("schubfach", {"h": h}) for h in (3, 4, 5, 6)]


@pytest.mark.parametrize("art,params", ZELLEN_LIVE, ids=[M.schluessel(a, **p) for a, p in ZELLEN_LIVE])
def test_vorgerechnete_zelle_gleicht_der_frisch_gerechneten(art, params):
    neu = M.messe_zelle(art, **params)
    alt = VORG[M.schluessel(art, **params)]
    assert json.loads(json.dumps(neu["zeilen"])) == alt["zeilen"]


@pytest.mark.parametrize("minimieren", [False, True])
def test_lernzelle_n50_gleicht_der_frisch_gerechneten(minimieren):
    neu = M.messe_lernzelle(50, minimieren)
    assert json.loads(json.dumps(neu["zeilen"])) == VORG[M.schluessel("lernen", n=50, min=int(minimieren))]["zeilen"]


def test_schluessel_und_live_regel():
    assert M.schluessel("zufall", n=70, v=4.26) == "zufall|n=70|v=4.26"
    assert M.schluessel("zufall", v=4.0, n=30) == "zufall|n=30|v=4"
    assert M.schluessel("schubfach", h=6) == "schubfach|h=6"
    assert M.live_moeglich("zufall", n=70, v=4.26) and not M.live_moeglich("zufall", n=90, v=4.26)
    assert not M.live_moeglich("schubfach", h=7) and not M.live_moeglich("lernen", n=150)


def test_formeln_deterministisch_und_zahl_der_klauseln():
    f = M.formeln("zufall", n=50, v=4.26)
    assert [s for s, _ in f] == list(C.SWEEP_SEEDS)
    assert all(len(i.klauseln) == 213 for _, i in f)                      # 4,26 · 50 = 213
    assert [i.klauseln for _, i in f] == [i.klauseln for _, i in M.formeln("zufall", n=50, v=4.26)]
    assert len(M.formeln("zufall", n=70, v=4.26)[0][1].klauseln) == 298   # 4,26 · 70 = 298,2 gerundet
    assert len(M.formeln("rampen", n=30, g=4.5)[0][1].meta["kanten"]) == round(30 * 4.5 / 2)

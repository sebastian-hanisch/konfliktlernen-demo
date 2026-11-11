"""DPLL-Regel und beide Zähler, startphase, Spur mit Gründen, Besuche nach Ergebnis, decay (aus sat-cp-planung/kern/tests, Importe auf kfl_ umgestellt)."""
import pytest

import kfl_instanzen as I
from kfl_cdcl import Loeser, solve
from kfl_dpll import dpll, waehle_variable


def test_dpll_regel_erste_gegen_haeufigste():
    # Variable 3 kommt zweimal vor (häufigste), Variable 1 ist die kleinste Nummer (erste)
    kl = [(3, 4), (1, 2, 3)]
    assert waehle_variable(kl, "haeufigste") == 3 and waehle_variable(kl, "erste") == 1
    with pytest.raises(ValueError):
        waehle_variable(kl, "zufall")
    for seed in range(8):
        f = I.rand3(20, 85, seed).klauseln
        a, b = dpll(f, regel="erste"), dpll(f, regel="haeufigste")
        assert a.erfuellbar == b.erfuellbar


def test_dpll_zwei_zaehler():
    # unerfüllbar: ein vollständiger Binärbaum ohne Einheitsschritte-Verzweigung; Blätter = Widersprüche, jeder Knoten ist eine Sackgasse
    for h in (3, 4, 5):
        r = dpll(I.pigeonhole(h).klauseln)
        assert r.sackgassen == r.knoten and r.widersprueche * 2 - 1 == r.knoten
    assert dpll(I.pigeonhole(3).klauseln).widersprueche == 6
    # erfüllbar: nur die gescheiterten Zweige zählen; Knoten auf dem Erfolgspfad sind keine Sackgassen
    r = dpll(I.rand3(25, 90, 1).klauseln)
    assert r.erfuellbar and r.sackgassen < r.knoten and r.widersprueche <= r.sackgassen


def test_startphase():
    s = Loeser(3, [(1, 2, 3)], vsids=False, startphase=True)
    assert s.waehle_literal(1) == 1
    erg = solve(3, [(1, 2, 3)], vsids=False, startphase=True)
    assert erg.modell == {1: True, 2: True, 3: True}
    erg = solve(3, [(1, 2, 3)], vsids=False)
    assert erg.modell == {1: False, 2: False, 3: True}          # zuerst falsch; erst die Klausel erzwingt 3
    t = Loeser(2, [], startphase=True)
    v = t.neue_variable()
    assert t.gemerkt[v] is True


def test_spur_entscheidung_mit_begruendung():
    erg = solve(3, [(1, 2, 3), (-1, 2), (-2, 3)], trace=True)
    art, lit, stufe, info = erg.spur[0]
    assert (art, lit, stufe) == ("entscheide", -1, 1)
    # alle Aktivitäten sind anfangs 0: drei offene Variablen gleichauf, Gleichstand 3, kleinste Nummer gewinnt
    assert info == {"art": "aktivitaet", "aktivitaet": 0.0, "gleichstand": 3, "phase_gespeichert": False, "wahl": "falsch"}
    ph = solve(3, [(1, 2, 3)], trace=True, startphase=True).spur[0][3]
    assert ph["phase_gespeichert"] is True and ph["wahl"] == "wahr"
    ann = solve(3, [(1, 2, 3)], trace=True, annahmen=[2]).spur[0]
    assert ann[:3] == ("entscheide", 2, 1) and ann[3] == {"art": "annahme"}


def test_spur_konflikt_gruende_und_beteiligte():
    inst = I.pigeonhole(3)
    erg = solve(inst.n, inst.klauseln, trace=True)
    arten = [e[0] for e in erg.spur]
    i = arten.index("konflikt")
    k = erg.spur[i]
    assert k[0] == "konflikt" and isinstance(k[3], int) and k[2] >= 1            # Klausel, Stufe, Index
    assert arten[i + 1] == "beteiligt" and arten[i + 2] == "lerne"
    beteiligt = erg.spur[i + 1][1]
    assert beteiligt and all(a > 0 for _, a in beteiligt)                         # nach dem Erhöhen ist jede Aktivität positiv
    lerne = erg.spur[i + 2]
    assert lerne[2] >= 0                                                          # Rücksprungstufe
    schliesse = [e for e in erg.spur if e[0] == "schliesse"]
    assert schliesse and all(len(e) == 5 for e in schliesse)                      # (art, lit, klausel, stufe, grund-index)


def test_schliesse_grund_ist_klauselindex():
    s = Loeser(3, [(-1, 2), (-2, 3)], trace=True)
    s.entscheide(1)
    s.propagiere()
    ereignisse = [e for e in s.ereignisse if e[0] == "schliesse"]
    assert [(e[1], e[4]) for e in ereignisse] == [(2, 0), (3, 1)]
    assert [sorted(s.klauseln[e[4]]) for e in ereignisse] == [sorted(e[2]) for e in ereignisse]


@pytest.mark.parametrize("watch", [True, False])
def test_besuche_nach_ergebnis_summe(watch):
    inst = I.rand3(50, 210, 4)
    erg = solve(inst.n, inst.klauseln, watch=watch)
    nach = erg.stat["besuche_nach"]
    assert sum(nach.values()) == erg.stat["besuche"] > 0
    if watch:
        assert nach["ohne_wirkung"] == 0 and nach["beobachter"] > 0
    else:
        assert nach["beobachter"] == 0 and nach["ohne_wirkung"] > 0
    assert nach["einheit"] > 0 and nach["erfuellt"] > 0 and nach["konflikt"] == erg.stat["konflikte"]


def test_gleicher_fixpunkt_beide_modi_und_zaehlweise():
    """Gleiche Zählweise: besuche = geprüfte Klauseln, lesezugriffe = gelesene Literale; beide Modi erreichen dieselbe Antwort."""
    for seed in range(5):
        inst = I.rand3(40, 160, seed)
        a, b = solve(inst.n, inst.klauseln, watch=True), solve(inst.n, inst.klauseln, watch=False)
        assert a.antwort == b.antwort
        assert b.stat["lesezugriffe"] >= b.stat["besuche"] and a.stat["lesezugriffe"] >= a.stat["besuche"]


def test_besuchs_spur_mit_beobachtern():
    s = Loeser(4, [(-1, 2, 3), (-2, 3), (1, 4)], trace="besuche")
    s.entscheide(1)
    s.propagiere()
    besuche = [e for e in s.ereignisse if e[0] == "besuch"]
    assert len(besuche) == s.stat["besuche"] and besuche
    # Klausel 2 = (1 ∨ 4) wird durch Entscheidung 1 nicht besucht (1 ist dort wahr); die Klausel (¬1 ∨ 2 ∨ 3) beobachtet ¬1 und 2
    erster = besuche[0]
    assert erster[0] == "besuch" and erster[1] == 0 and erster[2] == (2, -1) and erster[3] == "beobachter" and erster[4] == 3
    basis = Loeser(4, [(-1, 2, 3), (-2, 3), (1, 4)], trace=True)
    basis.entscheide(1)
    basis.propagiere()
    assert not [e for e in basis.ereignisse if e[0] == "besuch"]               # ohne "besuche" keine Besuchsereignisse
    naiv = Loeser(4, [(-1, 2, 3), (-2, 3), (1, 4)], watch=False, trace="besuche")
    naiv.entscheide(1)
    naiv.propagiere()
    assert all(e[2] is None for e in naiv.ereignisse if e[0] == "besuch")


def test_decay_parameter():
    inst = I.pigeonhole(3)
    for decay in (0.5, 0.95):
        s = Loeser(inst.n, inst.klauseln, decay=decay)
        erg = s.loese()
        assert erg.antwort is False
        assert s.zuwachs == pytest.approx((1 / decay) ** erg.stat["gelernt"])      # je gelernter Klausel einmal verfallen
    schnell = Loeser(inst.n, inst.klauseln, decay=0.5)
    schnell.loese()
    langsam = Loeser(inst.n, inst.klauseln, decay=0.95)
    langsam.loese()
    assert schnell.zuwachs > langsam.zuwachs                                   # stärkeres Vergessen: neuere Konflikte zählen mehr

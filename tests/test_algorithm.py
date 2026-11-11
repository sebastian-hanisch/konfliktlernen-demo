"""Einheiten dieser Demo gegen Handrechnung (Handbeispiel F1, Schubfach h = 2): DPLL-Baum, CDCL-Spur, Analyseprotokoll."""

import kfl_algorithm as A
import kfl_instanzen as I
from kfl_cdcl import Loeser
from kfl_dpll import dpll


def test_dpll_handbeispiel_f1(f1):
    """Von Hand: x1 = w, drei Zweige über (x2, x3, x4), je zwei Blätter (x5 w/f) = 6 Widersprüche; fünf innere Knoten ohne Lösung; 14 Knoten."""
    r = dpll(f1.klauseln, regel="erste")
    assert (r.knoten, r.widersprueche, r.sackgassen) == (14, 6, 11)
    assert r.erfuellbar is True and r.belegung[1] is False


def test_dpll_baum_zaehler_gleich_dem_kern(f1):
    for kl in [f1.klauseln, I.pigeonhole(3).klauseln, I.rand3(14, 60, 2).klauseln, I.rand3(20, 85, 5).klauseln]:
        for regel in ("erste", "haeufigste"):
            baum, kern = A.dpll_baum(kl, regel), dpll(kl, regel=regel)
            assert (len(baum.knoten), baum.widersprueche, baum.sackgassen, baum.erfuellbar) == (kern.knoten, kern.widersprueche, kern.sackgassen, kern.erfuellbar)


def test_dpll_baum_struktur_f1(f1):
    baum = A.dpll_baum(f1.klauseln, "erste")
    arten = [k.art for k in baum.knoten]
    assert arten.count("widerspruch") == 6 and arten.count("sackgasse") == 5
    assert arten.count("loesung") == 1
    wurzel = baum.knoten[0]
    assert wurzel.wahl is None and wurzel.tiefe == 0 and len(wurzel.kinder) == 2
    assert baum.knoten[wurzel.kinder[0]].wahl == 1 and baum.knoten[wurzel.kinder[1]].wahl == -1     # erst x1 = wahr
    assert all(len(k.kinder) == 2 for k in baum.knoten if k.art == "sackgasse")                      # Sackgasse = beide Zweige probiert
    einzel = [k for k in baum.knoten if len(k.kinder) == 1]                                            # von Hand: nur der Knoten x1 = f hat ein Kind (x2 = w ist die Lösung)
    assert [(k.art, k.wahl, k.tiefe) for k in einzel] == [("offen", -1, 1)]
    assert [k.art for k in baum.knoten].count("offen") == 2                                            # Wurzel und x1 = f liegen auf dem Weg zur Lösung


def test_dpll_baum_unerfuellbar_ist_voller_binaerbaum():
    """N = 2W − 1 und alle Knoten sind Sackgassen (Schubfach h = 2: 3 Knoten, 2 Widersprüche; h = 3: 11 Knoten, 6 Widersprüche)."""
    for h, (knoten, wid) in {2: (3, 2), 3: (11, 6)}.items():
        baum = A.dpll_baum(I.pigeonhole(h).klauseln, "haeufigste")
        assert (len(baum.knoten), baum.widersprueche, baum.sackgassen) == (knoten, wid, knoten)


def test_dpll_baum_budget():
    baum = A.dpll_baum(I.pigeonhole(6).klauseln, "haeufigste", knoten_budget=50)
    assert baum.erfuellbar is None and len(baum.knoten) <= 52


def test_cdcl_handbeispiel_f1(f1):
    """CDCL, feste Reihenfolge, wahr zuerst: Konflikt 1 in K2 auf Stufe 5 (gelernt (¬x1 ∨ ¬x5), Sprung auf Stufe 1), Konflikt 2 in K4 auf Stufe 1 (gelernt (¬x1), Stufe 0)."""
    erg = A.cdcl_spur(f1.n, f1.klauseln)
    assert erg.antwort is True and erg.stat["konflikte"] == 2
    lerne = [e for e in erg.spur if e[0] == "lerne"]
    assert [sorted(e[1]) for e in lerne] == [[-5, -1], [-1]]
    assert [e[2] for e in lerne] == [1, 0]                                                 # Rücksprungstufen
    konflikte = [e for e in erg.spur if e[0] == "konflikt"]
    assert [(e[2], e[3]) for e in konflikte] == [(5, 2), (1, 4)]                           # Stufe, Klauselindex (K2, K4)
    assert [e[1] for e in erg.spur if e[0] == "springe"] == [1, 0]
    assert erg.modell[1] is False and I.pruefe_modell(f1.klauseln, erg.modell)
    entscheidungen = [e[1] for e in erg.spur if e[0] == "entscheide"][:5]
    assert entscheidungen == [1, 2, 3, 4, 5]                                               # Stufen 1 bis 5: x1 bis x5 wahr


def test_cdcl_schubfach_h2_von_hand():
    """3 Tauben, 2 Löcher (Variablen T1L1 = 1, T1L2 = 2, T2L1 = 3, T2L2 = 4, T3L1 = 5, T3L2 = 6): unerfüllbar; von Hand: DPLL 3 Knoten, 2 Widersprüche."""
    inst = I.pigeonhole(2)
    assert dpll(inst.klauseln).widersprueche == 2
    erg = A.cdcl_spur(inst.n, inst.klauseln)
    assert erg.antwort is False and erg.stat["konflikte"] >= 2


def test_minimieren_aendert_die_antwort_nie_und_ist_nie_laenger(f1):
    for seed in range(15):
        inst = I.rand3(30, 128, seed)
        a = A.cdcl_spur(inst.n, inst.klauseln, vsids=True, restarts="luby", phase_saving=True, startphase=False)
        b = A.cdcl_spur(inst.n, inst.klauseln, minimieren=True, vsids=True, restarts="luby", phase_saving=True, startphase=False)
        assert a.antwort == b.antwort


def test_mess_loeser_protokoll_stimmt_mit_den_zaehlern():
    inst = I.rand3(50, 213, 3)
    s = A.MessLoeser(inst.n, inst.klauseln)
    erg = s.loese()
    assert len(s.protokoll) == erg.stat["gelernt"] and erg.stat["gelernt"] in (erg.stat["konflikte"], erg.stat["konflikte"] - 1)   # ein Konflikt auf Stufe 0 lernt nichts
    assert sum(p[2] for p in s.protokoll) == erg.stat["gelernte_literale"]
    for stufe, rueck, laenge, lbd in s.protokoll:
        assert 0 <= rueck < stufe and laenge >= 1 and 1 <= lbd <= laenge


def test_mess_loeser_aendert_den_ablauf_nicht():
    inst = I.rand3(50, 213, 3)
    a = A.MessLoeser(inst.n, inst.klauseln).loese()
    b = Loeser(inst.n, inst.klauseln).loese()
    assert (a.antwort, a.stat) == (b.antwort, b.stat)


def test_mess_loeser_f1_protokoll(f1):
    s = A.MessLoeser(f1.n, f1.klauseln, vsids=False, startphase=True, phase_saving=True, restarts="none")
    s.loese()
    assert s.protokoll == [(5, 1, 2, 2), (1, 0, 1, 1)]     # (Konfliktstufe, Rücksprung, Länge, LBD): Sprung 4 Stufen weit, dann 1

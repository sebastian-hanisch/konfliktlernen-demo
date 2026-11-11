"""Schritt-für-Schritt-Ansicht: Zustände, Beschreibungen, Stufentabelle, Implikationsgraph und 1-UIP-Schnitt, am Handbeispiel F1 von Hand und an allen Beispielen."""

import pytest

import kfl_algorithm as A
import kfl_constants as C
import kfl_scenario as S
import kfl_trace as T
from kfl_cdcl import Loeser


def _zustaende(inst, **kw):
    n_orig = len(Loeser(inst.n, inst.klauseln).klauseln)
    erg = A.cdcl_spur(inst.n, inst.klauseln, **kw)
    return erg, T.zustaende(erg.spur, n_orig)


def test_f1_ereignisfolge_von_hand(f1):
    """Handrechnung: fünf Entscheidungen, x6 erzwungen (K1), Konflikt in K2, lerne (¬x1 ∨ ¬x5), Sprung von 5 auf 1, ¬x5 (L1), x6 (K3), Konflikt in K4, lerne (¬x1), Sprung auf 0."""
    erg, zs = _zustaende(f1)
    arten = [z.ereignis[0] for z in zs[:15]]
    assert arten == ["entscheide"] * 5 + ["schliesse", "konflikt", "lerne", "springe", "schliesse", "schliesse", "konflikt", "lerne", "springe"] + ["entscheide"]
    assert [z.index for z in zs] == list(range(len(zs)))


def test_f1_beschreibungen(f1):
    _, zs = _zustaende(f1)
    text = [T.beschreibung(z, f1) for z in zs[:14]]
    assert text[0] == "Stufe 1: entscheide x1 = wahr (feste Reihenfolge)"
    assert text[5] == "Stufe 5: x6 wird erzwungen durch K1 (¬x1 ∨ ¬x5 ∨ x6)"
    assert text[6] == "Konflikt 1 auf Stufe 5: K2 (¬x1 ∨ ¬x5 ∨ ¬x6) ist verletzt"
    assert text[7] == "Lerne (¬x1 ∨ ¬x5) (Länge 2, LBD 2); Rücksprungstufe 1 (Konfliktstufe 5)"
    assert text[8] == "Springe von Stufe 5 auf Stufe 1 und überspringt dabei die Stufen 2, 3, 4"
    assert text[9] == "Stufe 1: ¬x5 wird erzwungen durch L1 (¬x1 ∨ ¬x5)"
    assert text[11] == "Konflikt 2 auf Stufe 1: K4 (¬x1 ∨ x5 ∨ ¬x6) ist verletzt"
    assert text[12] == "Lerne (¬x1) (Länge 1, LBD 1); Rücksprungstufe 0 (Konfliktstufe 1)"
    assert text[13] == "Springe von Stufe 1 auf Stufe 0"


def test_f1_zustand_beim_ersten_konflikt(f1):
    _, zs = _zustaende(f1)
    z = zs[6]
    assert [(x.lit, x.stufe) for x in z.trail] == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 5)]
    assert z.konflikt[1] == 5 and z.konflikt[2] == "K2" and z.konflikte == 1
    assert T.stufentabelle(z, f1) == [(1, "x1", "–"), (2, "x2", "–"), (3, "x3", "–"), (4, "x4", "–"), (5, "x5", "x6 (K1)")]
    g = T.implikationsgraph(z)
    assert set(g.kanten) == {(1, 6), (5, 6)}                      # x6 folgt aus K1 = (¬x1 ∨ ¬x5 ∨ x6): Vorgänger x1 und x5
    assert sorted(g.konflikt_von) == [1, 5, 6]


def test_f1_uip_und_schnitt(f1):
    """Konflikt 1: der 1-UIP ist die Entscheidung x5 (beide Wege zum Konflikt laufen über sie); die Konfliktseite ist {x6}; Klausel des Schnitts (¬x1 ∨ ¬x5)."""
    _, zs = _zustaende(f1)
    z = zs[7]                                                       # nach „lerne“, vor dem Sprung
    g = T.implikationsgraph(z)
    assert g.uip == 5 and g.seite == {6}
    assert T.schnitt_klausel(z) == {-1, -5}
    z2 = zs[11 + 1]                                                 # Konflikt 2 nach „lerne“: gelernt (¬x1)
    g2 = T.implikationsgraph(z2)
    assert g2.uip == 1 and T.schnitt_klausel(z2) == {-1}


def test_f1_sprung_und_trail_danach(f1):
    _, zs = _zustaende(f1)
    z = zs[8]
    assert z.sprung == (5, 1) and z.konflikt is None
    assert [(x.lit, x.stufe) for x in z.trail] == [(1, 1)]
    z = zs[10]                                                      # nach L1 und K3: x5 falsch, x6 wahr auf Stufe 1
    assert [(x.lit, x.art) for x in z.trail] == [(1, "entscheidung"), (-5, "folge"), (6, "folge")]
    z = zs[13]                                                      # Sprung auf Stufe 0: die gelernte Einheit ¬x1 steht auf Stufe 0
    assert z.sprung == (1, 0) and [(x.lit, x.stufe, x.art) for x in z.trail] == [(-1, 0, "einheit")]
    assert T.stufentabelle(z, f1) == [(0, "", "¬x1 (gelernte Einheit)")]
    assert [g[3] for g in zs[-1].gelernt_liste] == [2, 1]           # Längen der gelernten Klauseln


@pytest.mark.parametrize("name", C.BEISPIELE)
def test_schnitt_klausel_gleicht_der_gelernten_klausel(name):
    """Eigenschaft: aus dem Implikationsgraphen gelesen ergibt der Schnitt nach dem 1-UIP genau die gelernte Klausel (ohne Minimieren)."""
    inst = S.beispiel(name, 4)
    erg, zs = _zustaende(inst)
    gesehen = 0
    for z in zs:
        if z.ereignis[0] == "lerne":
            assert T.schnitt_klausel(z) == set(z.gelernt[0]), (name, z.index)
            g = T.implikationsgraph(z)
            assert g.uip is not None
            # genau ein Literal der Konfliktstufe in der gelernten Klausel (1-UIP)
            stufen = {x.lit: x.stufe for x in z.trail}
            assert sum(1 for q in z.gelernt[0] if stufen[-q] == z.konflikt[1]) == 1
            assert z.gelernt[1] < z.konflikt[1]
            gesehen += 1
    assert gesehen == erg.stat["konflikte"] or gesehen == erg.stat["gelernt"]


def test_stufentabelle_alle_stufen_aufsteigend(f1):
    _, zs = _zustaende(f1)
    for z in zs:
        stufen = [r[0] for r in T.stufentabelle(z, f1)]
        assert stufen == sorted(set(stufen))


def test_alle_beispiele_passen_in_die_spur_und_enden_mit_der_richtigen_antwort():
    erwartet = {C.BEISPIEL_F1: True, C.BEISPIEL_PHP2: False, C.BEISPIEL_PHP3: False, C.BEISPIEL_FAERBUNG: False}
    for name in C.BEISPIELE:
        inst = S.beispiel(name, 1)
        assert S.passt_in_spur(inst)
        erg = A.cdcl_spur(inst.n, inst.klauseln)
        assert not erg.spur_gekuerzt and len(erg.spur) < 5000
        if name in erwartet:
            assert erg.antwort is erwartet[name], name


def test_namen():
    assert S.variablenname(S.beispiel(C.BEISPIEL_PHP3), 5) == "T2L2"          # Variable p*h + l + 1 = 1*3 + 1 + 1
    assert S.variablenname(S.beispiel(C.BEISPIEL_FAERBUNG), 3) == "A2R1"      # i*k + c + 1 = 1*2 + 0 + 1
    assert S.literalname(S.beispiel(C.BEISPIEL_F1), -4) == "¬x4"
    assert S.klauseltext(S.beispiel(C.BEISPIEL_F1), (6, -5, -1)) == "(¬x1 ∨ ¬x5 ∨ x6)"
    assert S.klauseltext(S.beispiel(C.BEISPIEL_F1), ()) == "(leer)"

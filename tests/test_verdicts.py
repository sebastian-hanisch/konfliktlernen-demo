"""Verdikte (reine Funktionen in kfl_evaluation.py) an handgesetzten Zeilen: Schwellen, Randfälle und jede Zahl im Text."""

import pytest

import kfl_evaluation as E


def zeilen(paare, antwort=False, abbruch_dpll=0, abbruch_cdcl=0):
    """Je Paar (CDCL-Konflikte, DPLL-Widersprüche) eine Zeile; Sackgassen = 2·W − 1 (unerfüllbar)."""
    out = []
    for i, (k, w) in enumerate(paare):
        out.append({"antwort": None if i < abbruch_cdcl else antwort, "dpll_antwort": None if i < abbruch_dpll else antwort,
                    "konflikte": k, "widersprueche": w, "sackgassen": max(2 * w - 1, 0), "knoten": max(2 * w - 1, 0)})
    return out


def test_formatierung():
    assert E.fmt(1014.5) == "1.014,5" and E.fmt(1004) == "1.004" and E.fmt(22.0) == "22" and E.fmt(None) == "–" and E.fmt(0) == "0"
    assert E.fmt2(1.17) == "1,17" and E.fmt2(2.16) == "2,2" and E.fmt2(0.5) == "0,50"
    assert E.konflikte_text(1) == "1 Konflikt" and E.konflikte_text(2) == "2 Konflikte"


def test_zusammenfassung_von_hand():
    s = E.zusammenfassung(zeilen([(4, 10), (6, 20), (8, 30)]))
    assert s["konflikte"] == {"median": 6, "min": 4, "max": 8} and s["widersprueche"] == {"median": 20, "min": 10, "max": 30}
    assert s["sackgassen"]["median"] == 39 and s["unerfuellbar"] == 3 and s["erfuellbar"] == 0 and s["formeln"] == 3
    assert E.quotient(s) == pytest.approx(20 / 6)
    assert s["sack_je_wid"] == pytest.approx(39 / 20)          # Median von 19/10, 39/20, 59/30


def test_vorsprung_ab_der_schwelle_1_2():
    art, text = E.verdict_vergleich(E.zusammenfassung(zeilen([(10, 12)] * 5)), "Bei n = 90")      # 12 / 10 = 1,2 genau
    assert art == "success"
    art, text = E.verdict_vergleich(E.zusammenfassung(zeilen([(10, 11)] * 5)), "Bei n = 90")      # 1,1: kein Vorsprung
    assert art == "info" and "Kein Vorsprung bei dieser Größe" in text and "Quotient 1,10" in text


def test_text_nennt_jede_zahl_der_zelle():
    s = E.zusammenfassung(zeilen([(5, 12)] * 20))
    art, text = E.verdict_vergleich(s, "Bei n = 110")
    assert art == "success"
    assert "2,4-mal so viele Widersprüche" in text and "12 DPLL-Widersprüche gegen 5 CDCL-Konflikte" in text
    assert "20 feste Formeln, 0 erfüllbar" in text and "Sackgassen des DPLL im Median 23" in text and text.startswith("Bei n = 110:")


def test_nachteil_unter_dem_kehrwert():
    art, text = E.verdict_vergleich(E.zusammenfassung(zeilen([(10, 8)] * 3)), "Zelle")            # 0,8
    assert art == "warning" and "1,25-mal so viele Konflikte" in text and "8 DPLL-Widersprüche gegen 10 CDCL-Konflikte" in text
    art, _ = E.verdict_vergleich(E.zusammenfassung(zeilen([(10, 9)] * 3)), "Zelle")                # 0,9: noch kein Nachteil
    assert art == "info"


def test_randfaelle_null_konflikte_und_null_widersprueche():
    art, text = E.verdict_vergleich(E.zusammenfassung(zeilen([(0, 7)])), "Zelle")
    assert art == "info" and "keinen Konflikt" in text and "7 Widersprüche" in text
    art, text = E.verdict_vergleich(E.zusammenfassung(zeilen([(1, 0)], antwort=True)), "Schur")
    assert art == "warning" and "ohne Widerspruch" in text and "1 Konflikt " in text
    assert E.quotient(E.zusammenfassung(zeilen([(0, 7)]))) is None


def test_abbruchhinweis_steht_im_verdikt():
    s = E.zusammenfassung(zeilen([(10, 30)] * 4, abbruch_dpll=2, abbruch_cdcl=1))
    assert (s["abbruch_dpll"], s["abbruch_cdcl"]) == (2, 1)
    _, text = E.verdict_vergleich(s, "Zelle")
    assert "brach bei 2 von 4 Formeln am Knotenbudget ab" in text and "brach bei 1 von 4 Formeln am Konfliktbudget ab" in text


def test_schubfach_verdikt_nennt_h_und_beide_zahlen():
    s = E.zusammenfassung(zeilen([(1004, 720)]))
    art, text = E.verdict_zelle("schubfach", {"h": 6}, s, "Schubfach h = 6")
    assert art == "warning"
    assert text.startswith("Auf Schubfach h = 6 braucht der CDCL 1.004 Konflikte, der DPLL 720 Widersprüche: gegenüber diesem DPLL hat der CDCL hier keinen Vorsprung (Quotient 0,72).")
    art, text = E.verdict_zelle("schubfach", {"h": 8}, E.zusammenfassung(zeilen([(27932, 40320)])), "x")
    assert art == "success" and "1,44-mal so viele Widersprüche" in text


def test_wachstumsfaktoren_von_hand():
    z = [("a", E.zusammenfassung(zeilen([(10, 100)]))), ("b", E.zusammenfassung(zeilen([(40, 300)]))), ("c", E.zusammenfassung(zeilen([(240, 600)])))]
    f = E.wachstumsfaktoren(z)
    assert f["konflikte"] == [4, 6] and f["widersprueche"] == [3, 2]
    assert E.satz_wachstumsfaktoren(z) == "Von Zelle zu Zelle wächst der CDCL-Median um das 4,0- bis 6,0-Fache, der DPLL-Median um das 2,0- bis 3,0-Fache."


def test_verdikt_formel_drei_faelle():
    art, text = E.verdict_formel(6, 11, 2, True)
    assert art == "success" and "6 Widersprüchen (11 Sackgassen insgesamt)" in text and "2 Konflikte" in text and "spart hier 4 Konflikte" in text and "erfüllbar" in text
    art, text = E.verdict_formel(3, 5, 3, False)
    assert art == "info" and "unerfüllbar" in text and "kein Vorsprung" in text
    art, text = E.verdict_formel(6, 11, 7, False)
    assert art == "warning" and "mehr Konflikte als die Suche ohne Gedächtnis Widersprüche" in text
    assert "unbekannt (Budget)" in E.verdict_formel(1, 1, 1, None)[1]


def test_verdikt_minimieren_von_hand():
    ohne = {"formeln": 4, "konflikte": [10, 20, 30, 40], "median": 25.0, "mittlere_laenge": 8.0}
    mit = {"formeln": 4, "konflikte": [8, 20, 24, 50], "median": 22.0, "mittlere_laenge": 6.5}
    art, text = E.verdict_minimieren(ohne, mit)                          # weniger bei 2, gleich bei 1, mehr bei 1; Median 25 → 22 = 12 % weniger
    assert art == "success" and "spart im Median 12 % der Konflikte (Bezug: ohne Minimieren)" in text
    assert "im Median 25 Konflikte, mit Minimieren 22" in text and "8 gegen 6,5 Literale" in text
    assert "bei 2 Formeln weniger, bei 1 gleich viele und bei 1 mehr" in text
    art, text = E.verdict_minimieren(ohne, {**ohne})
    assert art == "info" and "ändert den Median nicht" in text
    art, text = E.verdict_minimieren(ohne, {"formeln": 4, "konflikte": [12, 25, 30, 41], "median": 27.5, "mittlere_laenge": 7.0})
    assert art == "warning" and "Kein verlässlicher Vorteil" in text


def test_lern_summe_von_hand():
    zeilen_ = [{"antwort": True, "konflikte": 3, "gelernt": 3, "literale": 9, "laengen": {"2": 1, "3": 2, "1": 0}, "spruenge": {"1": 2, "3": 1}},
               {"antwort": True, "konflikte": 1, "gelernt": 1, "literale": 4, "laengen": {"4": 1}, "spruenge": {"1": 1}}]
    s = E.lern_summe(zeilen_)
    assert s["median"] == 2.0 and s["mittlere_laenge"] == 13 / 4 and s["gelernt"] == 4
    assert s["spruenge"] == {1: 3, 3: 1} and s["mittel_sprung"] == 6 / 4 and s["anteil_weit"] == 25.0

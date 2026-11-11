"""Live-Nachrechnen mit Fortschrittsanzeige und Zwischenspeicher: das Ergebnis ist gleich dem ungepufferten, ein anderer Parameter kommt nicht aus dem Speicher."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import kfl_fortschritt as F
import kfl_messung as M

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))

ZELLEN = (("schubfach", {"h": 4}), ("schur", {"k": 3, "n": 12}), ("zufall", {"n": 30, "v": 4.0}), ("rampen", {"n": 30, "g": 4.5}))


def test_zwischengespeicherte_zelle_ist_gleich_der_ungepufferten():
    for art, params in ZELLEN:
        F.formel_zeile.clear()
        direkt = M.messe_zelle(art, **params)
        assert F.zelle(art, params) == direkt, (art, params)
        assert F.zelle(art, params) == direkt, (art, params, "zweiter Aufruf aus dem Zwischenspeicher")


def test_zweiter_aufruf_rechnet_nichts_neu_und_ein_anderer_parameter_schon():
    F.formel_zeile.clear()
    v0 = F.gerechnet()
    erste = F.zelle("zufall", {"n": 30, "v": 4.0})
    v1 = F.gerechnet()
    assert v1 - v0 == len(erste["zeilen"]) == 20
    assert F.zelle("zufall", {"n": 30, "v": 4.0}) == erste and F.gerechnet() == v1
    andere = F.zelle("zufall", {"n": 30, "v": 4.5})
    assert F.gerechnet() - v1 == 20, "ein anderes Verhältnis m/n darf nicht aus dem Zwischenspeicher kommen"
    assert andere != erste and andere == M.messe_zelle("zufall", n=30, v=4.5)
    gross = F.zelle("zufall", {"n": 50, "v": 4.0})
    assert gross != erste and gross == M.messe_zelle("zufall", n=50, v=4.0), "ein anderes n darf nicht aus dem Zwischenspeicher kommen"


def test_reihenfolge_der_parameter_ist_gleichgueltig():
    F.formel_zeile.clear()
    F.zelle("rampen", {"n": 30, "g": 4.0})
    v = F.gerechnet()
    F.zelle("rampen", {"g": 4.0, "n": 30})
    assert F.gerechnet() == v


def test_fortschritt_meldet_jede_formel_in_ordnung():
    F.formel_zeile.clear()
    meldungen = []
    F.zelle("zufall", {"n": 30, "v": 4.26}, lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(i, 20) for i in range(1, 21)]
    meldungen.clear()
    F.zelle("schubfach", {"h": 3}, lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(1, 1)]


def test_app_zweiter_klick_kommt_aus_dem_zwischenspeicher_und_zeigt_dasselbe():
    F.formel_zeile.clear()
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    at.select_slider(key="wachs_n").set_value(30).run()
    knopf = next(b for b in at.button if b.key == "live_w_30_4.26")
    knopf.click().run()
    assert not at.exception
    erste = [s.value for s in at.success]
    assert any("stimmen mit den vorgerechneten überein" in t and " in " in t and "Zwischenspeicher" not in t for t in erste)
    v = F.gerechnet()
    next(b for b in at.button if b.key == "live_w_30_4.26").click().run()
    assert not at.exception and F.gerechnet() == v
    zweite = [s.value for s in at.success]
    assert any("aus dem Zwischenspeicher" in t and "stimmen mit den vorgerechneten überein" in t for t in zweite)

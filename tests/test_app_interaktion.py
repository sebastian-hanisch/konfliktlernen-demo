"""Oberfläche: jede Beispielformel, jede Auswahl der Experimente, die Schritt-für-Schritt-Ansicht und die Live-Knöpfe laufen ohne Fehler und zeigen die erwarteten Zahlen."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import kfl_constants as C
import kfl_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at) -> str:
    teile = [m.value for m in at.markdown] + [i.value for i in at.info] + [s.value for s in at.success] + [w.value for w in at.warning] + [c.value for c in at.caption]
    return "\n".join(teile)


def test_handbeispiel_zeigt_die_handwerte():
    at = _app()
    metriken = {m.label: m.value for m in at.metric}
    assert metriken["DPLL: Widersprüche"] == "6" and metriken["DPLL: Sackgassen"] == "11" and metriken["CDCL: Konflikte"] == "2"
    assert metriken["Antwort"] == "erfüllbar"
    text = _texte(at)
    assert "**Schritt 1 von 19.** Stufe 1: entscheide x1 = wahr" in text
    assert "6 Widersprüchen (11 Sackgassen insgesamt)" in text


def test_schritt_slider_durch_alle_schritte_und_nachster_konflikt():
    at = _app()
    schluessel = next(s.key for s in at.slider if s.key.startswith("schritt_"))
    for k in range(19):
        at.slider(key=schluessel).set_value(k).run()
        assert not at.exception, (k, [str(e) for e in at.exception])
    at = _app()
    nach = next(b for b in at.button if b.label == "⏭ Nächster Konflikt")
    nach.click().run()
    assert "Schritt 7 von 19" in _texte(at) and "Konflikt 1 auf Stufe 5: K2" in _texte(at)
    at.button(key=next(b.key for b in at.button if b.label == "Vor ▶")).click().run()
    assert "Lerne (¬x1 ∨ ¬x5)" in _texte(at)
    at.button(key=next(b.key for b in at.button if b.label == "◀ Zurück")).click().run()
    assert "Schritt 7 von 19" in _texte(at)


@pytest.mark.parametrize("name", C.BEISPIELE)
def test_jede_beispielformel_laeuft(name):
    at = _app()
    at.selectbox(key="formel").set_value(name).run()
    assert not at.exception, [str(e) for e in at.exception]
    for minimieren in (True, False):
        at.toggle(key="minimieren1").set_value(minimieren).run()
        assert not at.exception, [str(e) for e in at.exception]
    assert at.metric[0].label == "Antwort"


def test_zufallsbeispiel_mit_seed_und_wuerfel():
    at = _app()
    at.selectbox(key="formel").set_value(C.BEISPIEL_ZUFALL).run()
    assert not at.sidebar.number_input(key="seed_input").proto.disabled
    at.sidebar.number_input(key="seed_input").set_value(5).run()
    erste = [m.value for m in at.metric]
    at.sidebar.button[-1].click().run()
    assert not at.exception and at.session_state["seed_input"] != 5
    assert at.session_state["wuerfel_zaehler"] == 1
    assert erste[0] in ("erfüllbar", "unerfüllbar")


def test_wuerfel_waehlt_das_zufallsbeispiel_und_der_seed_ist_sonst_gesperrt():
    at = _app()
    assert at.session_state["formel"] == C.BEISPIEL_F1 and at.sidebar.number_input(key="seed_input").proto.disabled
    knopf = next(b for b in at.sidebar.button if b.label == "🎲 Zufallsformel würfeln")
    assert not knopf.proto.disabled
    knopf.click().run()
    assert not at.exception and at.session_state["formel"] == C.BEISPIEL_ZUFALL and not at.sidebar.number_input(key="seed_input").proto.disabled


@pytest.mark.parametrize("familie", list(C.FAMILIEN))
def test_jede_familie_zeigt_verdikt_und_tabelle(familie):
    at = _app()
    at.selectbox(key="familie").set_value(familie).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert any("| Zelle |" in m.value and ("▶ " + familie) in m.value for m in at.markdown)      # die Tabelle markiert die gewählte Zelle


def test_wachstum_alle_auswahlen():
    at = _app()
    for n in C.N_ZUFALL:
        for v in C.VERHAELTNISSE:
            at.select_slider(key="wachs_n").set_value(n).run()
            at.select_slider(key="wachs_verh").set_value(v).run()
            assert not at.exception, (n, v, [str(e) for e in at.exception])
            assert any(f"Bei n = {n} (m/n = {C.zahl_de(v)})" in x.value for x in list(at.success) + list(at.info) + list(at.warning))


def test_lernen_beide_groessen_und_alle_formeln():
    at = _app()
    for n in C.LERN_N:
        at.select_slider(key="lern_n").set_value(n).run()
        for f in (1, len(C.LERN_SEEDS)):
            at.slider(key="lern_formel").set_value(f).run()
            assert not at.exception, (n, f)


def test_live_nachrechnen_stimmt_mit_den_gespeicherten_zeilen_ueberein():
    at = _app()
    at.select_slider(key="wachs_n").set_value(30).run()
    next(b for b in at.button if b.key == "live_w_30_4.26").click().run()
    assert not at.exception and any("stimmen mit den vorgerechneten überein" in s.value for s in at.success)
    at = _app()
    at.selectbox(key="familie").set_value("Schubfach h = 4").run()
    next(b for b in at.button if b.key.startswith("live_f_Schubfach h = 4")).click().run()
    assert any("stimmen mit den vorgerechneten überein" in s.value for s in at.success)
    at = _app()
    next(b for b in at.button if b.key == "live_lern_50").click().run()
    assert any("stimmen mit den vorgerechneten überein" in s.value for s in at.success)


def test_vorgerechnete_zellen_haben_keinen_live_knopf():
    at = _app()
    at.select_slider(key="wachs_n").set_value(110).run()
    assert not [b for b in at.button if b.key and b.key.startswith("live_w_")]
    assert any("vorgerechnet" in c.value and "dauert zu lange" in c.value for c in at.caption)


def test_permalink_uebernimmt_werte(monkeypatch):
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["fam"] = "Schubfach h = 8"
    at.query_params["wn"] = "110"
    at.query_params["wv"] = "4.5"
    at.query_params["lf"] = "99"
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state["familie"] == "Schubfach h = 8" and at.session_state["wachs_n"] == 110
    assert at.session_state["wachs_verh"] == 4.5 and at.session_state["lern_formel"] == len(C.LERN_SEEDS)
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["fam"] = "unbekannt"
    at.run()
    assert at.session_state["familie"] == C.DEFAULT_FAMILIE


@pytest.mark.parametrize("preset", list(P.PRESETS))
def test_preset_setzt_beispiel_und_zelle(preset):
    at = _app()
    at.sidebar.button(key=f"preset_{preset}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state["formel"] == P.PRESETS[preset]["formel"] and at.session_state["familie"] == P.PRESETS[preset]["familie"]

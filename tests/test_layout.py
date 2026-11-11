"""Layout (DEMO-PLAYBOOK §2): fester Kopf, Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben.

Die Hervorhebung ist zustandslos (`aktives_preset` vergleicht jeden Regler aus SETTING_SPECS mit dem Preset). Der Test unten stellt
sicher, dass wirklich JEDER Regler der Seitenleiste dort steht: sonst bliebe das Preset trotz Änderung markiert."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import kfl_constants as C
import kfl_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
REGLER_ARTEN = ("slider", "number_input", "select_slider", "selectbox", "radio", "toggle", "checkbox", "text_input")
BEREICHE = ("sidebar", "main")   # Presets und Zufalls-Seed stehen in der Seitenleiste, die Experiment-Regler im Hauptbereich


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _typen(at) -> dict:
    """Button-Typ je Preset-Name (die Preset-Buttons der Seitenleiste)."""
    return {b.label: b.proto.type for b in at.sidebar.button if b.label in P.PRESETS}


def _regler(at, key):
    for bereich in BEREICHE:
        for art in REGLER_ARTEN:
            try:
                return getattr(getattr(at, bereich), art)(key=key)
            except KeyError:
                continue
    raise AssertionError(f"Regler {key} steht weder in der Seitenleiste noch im Hauptbereich")


def test_presets_stehen_in_der_seitenleiste_und_nicht_im_hauptbereich():
    at = _app()
    assert [b.label for b in at.sidebar.button][: len(P.PRESETS)] == list(P.PRESETS)  # die ersten Buttons der Seitenleiste
    assert not [b for b in at.main.button if b.label in P.PRESETS]


def test_titel_steht_im_festen_kopf():
    at = _app()
    assert "st-key-kopf" in " ".join(h.proto.body for h in at.get("html"))  # das Stylesheet setzt an der Klasse des Containers an
    assert at.title[0].value


def test_beim_start_ist_genau_das_standard_preset_hervorgehoben():
    typen = _typen(_app())
    assert [name for name, typ in typen.items() if typ == "primary"] == [next(iter(P.PRESETS))]


@pytest.mark.parametrize("name", list(P.PRESETS))
def test_angeklicktes_preset_ist_hervorgehoben_und_bleibt_es_im_naechsten_lauf(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]
    at.run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]


def test_jeder_regler_der_seitenleiste_steht_in_setting_specs():
    at = _app()
    schluessel = {w.key for art in REGLER_ARTEN for w in getattr(at.sidebar, art) if w.key}
    fehlt = schluessel - set(P.SETTING_SPECS)
    assert not fehlt, f"Regler {sorted(fehlt)} fehlen in SETTING_SPECS: ihre Änderung hebt das aktive Preset nicht auf"


def test_jeder_eintrag_von_setting_specs_ist_ein_regler_der_app():
    at = _app()
    for state_key in P.SETTING_SPECS:
        _regler(at, state_key)


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
def test_jede_aenderung_eines_reglers_hebt_die_hervorhebung_auf(state_key):
    at = _app()
    spec = P.SETTING_SPECS[state_key]
    if state_key == "seed_input":        # der Zufalls-Seed ist nur beim Zufallsbeispiel wirksam (sonst gesperrt): erst das Preset mit diesem Beispiel laden
        at.sidebar.button(key=f"preset_{C.PRESET_ZUFALL}").click().run()
        assert _typen(at)[C.PRESET_ZUFALL] == "primary" and not _regler(at, state_key).proto.disabled
    regler = _regler(at, state_key)
    if spec.options is not None:
        neu = next(o for o in spec.options if o != regler.value)
    elif state_key in P.SCHALTER:
        neu = not regler.value
    else:
        neu = spec.hi if regler.value != spec.hi else spec.lo
    regler.set_value(neu).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "primary" not in _typen(at).values()
    # erneutes Anklicken markiert wieder
    name = next(iter(P.PRESETS))
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert _typen(at)[name] == "primary"

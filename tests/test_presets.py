"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Begrenzung."""

import kfl_constants as C
import kfl_presets as P


def test_every_preset_has_help_and_only_known_keys():
    assert set(P.PRESETS) == set(P.PRESET_HELP)
    for name, preset in P.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert P.PRESET_HELP[name]


def test_preset_values_are_valid():
    for name in P.PRESETS:
        for state_key, spec in P.SETTING_SPECS.items():
            wert = P.preset_wert(name, state_key)
            if state_key in P.SCHALTER:
                assert isinstance(wert, bool)
            elif spec.options is not None:
                assert wert in spec.options, (name, state_key)
            else:
                assert spec.lo <= wert <= spec.hi, (name, state_key)


def test_default_preset_equals_the_default_settings():
    erstes = next(iter(P.PRESETS))
    assert erstes == C.PRESET_HAND
    for state_key, spec in P.SETTING_SPECS.items():
        assert P.preset_wert(erstes, state_key) == P._fuer_state(state_key, spec.default)


def test_presets_unterscheiden_sich_paarweise():
    werte = [tuple(P.preset_wert(n, k) for k in P.SETTING_SPECS) for n in P.PRESETS]
    assert len(set(werte)) == len(werte)


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    urls = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(set(urls)) == len(urls)


def test_preset_zellen_existieren_in_den_messdaten():
    """Jedes Preset zeigt auf eine vorgerechnete Zelle (Familie) und auf eine Beispielformel."""
    import kfl_messung as M
    vorg = M.lade_vorgerechnet()
    for name in P.PRESETS:
        art, params = C.FAMILIEN[P.preset_wert(name, "familie")]
        assert M.schluessel(art, **params) in vorg
        assert P.preset_wert(name, "formel") in C.BEISPIELE


def test_begrenzen_von_permalink_werten():
    spec = P.SETTING_SPECS["lern_formel"]
    assert P._begrenzen(spec, 99) == len(C.LERN_SEEDS) and P._begrenzen(spec, -3) == 1
    assert P._begrenzen(P.SETTING_SPECS["wachs_n"], 71) is None and P._begrenzen(P.SETTING_SPECS["wachs_n"], 90) == 90
    assert P._begrenzen(P.SETTING_SPECS["familie"], "Quatsch") is None


def test_wuerfel_folge_ist_deterministisch_und_im_bereich():
    from kfl_rng import SplitMix64
    erste = [SplitMix64(z).below(C.SEED_MAX + 1) for z in (1, 2, 3)]
    assert all(0 <= s <= C.SEED_MAX for s in erste) and len(set(erste)) == 3

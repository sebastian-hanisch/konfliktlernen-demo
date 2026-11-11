"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Alle Einstellungen stehen in `SETTING_SPECS`; sie stehen teils in der Seitenleiste (Schnellstart, Zufalls-Seed), teils im Hauptbereich
(experimentbezogene Regler). Ein Preset setzt jeden Regler, der vom Standard abweicht; das aktive Preset ist hervorgehoben, solange alle Regler
seinen Werten entsprechen."""

from dataclasses import dataclass

import streamlit as st

import kfl_constants as C
from kfl_rng import SplitMix64


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None     # Auswahlliste (selectbox, select_slider, radio); der Wert muss darin stehen


SETTING_SPECS = {
    "formel": SettingSpec("formel", str, C.BEISPIEL_F1, options=C.BEISPIELE),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "minimieren1": SettingSpec("min1", int, 0, 0, 1),
    "wachs_n": SettingSpec("wn", int, C.DEFAULT_N, options=C.N_ZUFALL),
    "wachs_verh": SettingSpec("wv", float, C.DEFAULT_VERH, options=C.VERHAELTNISSE),
    "familie": SettingSpec("fam", str, C.DEFAULT_FAMILIE, options=tuple(C.FAMILIEN)),
    "lern_n": SettingSpec("ln", int, C.DEFAULT_LERN_N, options=C.LERN_N),
    "lern_formel": SettingSpec("lf", int, C.DEFAULT_LERN_FORMEL, 1, len(C.LERN_SEEDS)),
}
PRESET_KEYS = {
    "formel": "formel", "seed": "seed_input", "min1": "minimieren1", "wachs_n": "wachs_n", "wachs_verh": "wachs_verh", "familie": "familie",
    "lern_n": "lern_n", "lern_formel": "lern_formel",
}
# Bei Schaltern speichert der Session State einen Wahrheitswert; die Spezifikation rechnet in 0/1.
SCHALTER = ("minimieren1",)

PRESETS = {
    C.PRESET_HAND: {"formel": C.BEISPIEL_F1, "familie": C.DEFAULT_FAMILIE},
    C.PRESET_RAMPEN: {"formel": C.BEISPIEL_FAERBUNG, "familie": C.FAM_RAMPEN30},
    C.PRESET_ZUFALL: {"formel": C.BEISPIEL_ZUFALL, "wachs_n": 70, "familie": C.FAM_ZUFALL},
    C.PRESET_SCHUBFACH: {"formel": C.BEISPIEL_PHP3, "familie": C.FAM_SCHUBFACH5},
}
PRESET_HELP = {
    C.PRESET_HAND: "Die Formel F1 mit fünf Klauseln von Hand: sechs Widersprüche des DPLL gegen zwei Konflikte des CDCL, gelernte Klauseln (¬x1 ∨ ¬x5) und (¬x1).",
    C.PRESET_RAMPEN: "Fünf Aufträge im Kreis auf zwei Rampen (Färbung eines Konfliktgraphen): unerfüllbar. Darunter die Messzelle Rampen-Färbung n = 30, Grad 4,5.",
    C.PRESET_ZUFALL: "Eine Zufallsformel mit 12 Variablen als Beispiel und die Messreihe Zufalls-3-SAT bei n = 70 (m/n = 4,26, 20 feste Formeln).",
    C.PRESET_SCHUBFACH: "Vier Tauben in drei Löchern von Hand; darunter die Messzelle Schubfach h = 5, an der der CDCL gegenüber dem DPLL keinen Vorsprung hat.",
}


def _fuer_state(state_key, wert):
    return bool(wert) if state_key in SCHALTER else wert


def preset_wert(name, state_key):
    """Wert des Presets für einen Regler (Standard, wenn das Preset ihn nicht nennt), in der Form des Session States."""
    spec = SETTING_SPECS[state_key]
    key = next(k for k, s in PRESET_KEYS.items() if s == state_key)
    return _fuer_state(state_key, PRESETS[name].get(key, spec.default))


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = _fuer_state(state_key, spec.default)


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def _begrenzen(spec: SettingSpec, wert):
    if spec.options is not None:
        return wert if wert in spec.options else None
    if spec.lo is not None:
        wert = max(spec.lo, wert)
    if spec.hi is not None:
        wert = min(spec.hi, wert)
    return wert


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt (Auswahlen nur, wenn der Wert vorkommt)."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                wert = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            wert = _begrenzen(spec, wert)
            if wert is None:
                continue
            st.session_state[state_key] = _fuer_state(state_key, wert)
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            wert = int(value) if state_key in SCHALTER else value
            st.query_params[SETTING_SPECS[state_key].url_param] = str(wert)
    except Exception:
        pass


def apply_preset(name):
    for state_key in SETTING_SPECS:
        st.session_state[state_key] = preset_wert(name, state_key)


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None (zustandslos)."""
    for name in PRESETS:
        if all(st.session_state.get(state_key, _fuer_state(state_key, spec.default)) == preset_wert(name, state_key)
               for state_key, spec in SETTING_SPECS.items()):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    """Wählt das Zufallsbeispiel und würfelt einen neuen Zufalls-Seed, ohne Python-`random`: der n-te Wurf einer SplitMix64-Folge aus einem Zähler in der Sitzung."""
    zaehler = st.session_state.get("wuerfel_zaehler", 0) + 1
    st.session_state["wuerfel_zaehler"] = zaehler
    st.session_state["formel"] = C.BEISPIEL_ZUFALL
    st.session_state["seed_input"] = SplitMix64(zaehler).below(C.SEED_MAX + 1)

"""Konstanten: Regler-Grenzen, feste Messzellen, Farben und Presets."""

# --- Beispielformeln der Schritt-für-Schritt-Ansicht (Experiment 1) ---------------------------------------------------------
BEISPIEL_F1 = "Handbeispiel F1"
BEISPIEL_PHP2 = "Schubfach h = 2 (3 Tauben, 2 Löcher)"
BEISPIEL_PHP3 = "Schubfach h = 3 (4 Tauben, 3 Löcher)"
BEISPIEL_ZUFALL = "Zufalls-3-SAT, n = 12"
BEISPIEL_FAERBUNG = "Rampen: 5 Aufträge im Kreis, 2 Rampen"
BEISPIELE = (BEISPIEL_F1, BEISPIEL_PHP2, BEISPIEL_PHP3, BEISPIEL_ZUFALL, BEISPIEL_FAERBUNG)
ZUFALL_BEISPIEL_N = 12
SPUR_MAX_VARIABLEN = 12      # Schritt-für-Schritt-Ansicht nur für kleine Formeln (Spur höchstens 5 000 Ereignisse)
SPUR_MAX_KLAUSELN = 60

SEED_MAX, DEFAULT_SEED = 999999, 1

# --- feste Messzellen (Experimente 2 bis 4) ---------------------------------------------------------------------------------
SWEEP_SEEDS = tuple(range(1, 21))        # 20 feste Formeln je Zelle: nie ein einzelner Seed als Befund
LERN_SEEDS = tuple(range(1, 13))         # 12 feste Formeln für Experiment 4
N_ZUFALL = (30, 50, 70, 90, 110)
VERHAELTNISSE = (4.0, 4.26, 4.5)         # Klauseln je Variable m/n
DEFAULT_N, DEFAULT_VERH = 70, 4.26
LERN_N = (50, 150)
DEFAULT_LERN_N = 50
RAMPEN_N = (30, 60, 90)
RAMPEN_GRAD = (4.0, 4.5, 5.0)
RAMPEN_K = 3
SCHUR_K, SCHUR_N = 3, (10, 11, 12, 13, 14)
SCHUBFACH_H = (3, 4, 5, 6, 7, 8)
LIVE_N_MAX = 70                          # Zufallszellen bis n = 70 lassen sich in der App nachrechnen (n = 90: rund 40 s, n = 110: Minuten)

DPLL_BUDGET = {"zufall": 50000, "rampen": 50000, "schur": 50000, "schubfach": 200000}
CDCL_BUDGET = 200000

def zahl_de(x) -> str:
    """Dezimalzahl mit Komma (4,26; 4,5; 4)."""
    return f"{x:g}".replace(".", ",")


# Familien-Auswahl (Experiment 3): jede Messzelle ist ein Eintrag der Auswahlliste: Bezeichnung -> (Art, Parameter)
FAMILIEN = {}
for _n in N_ZUFALL:
    FAMILIEN[f"Zufalls-3-SAT n = {_n} (m/n = 4,26)"] = ("zufall", {"n": _n, "v": 4.26})
for _n in RAMPEN_N:
    for _g in RAMPEN_GRAD:
        FAMILIEN[f"Rampen-Färbung n = {_n}, Grad {zahl_de(_g)} (3 Rampen)"] = ("rampen", {"n": _n, "g": _g})
for _n in SCHUR_N:
    FAMILIEN[f"Schur k = {SCHUR_K}, n = {_n}"] = ("schur", {"k": SCHUR_K, "n": _n})
for _h in SCHUBFACH_H:
    FAMILIEN[f"Schubfach h = {_h}"] = ("schubfach", {"h": _h})
FAM_ZUFALL = "Zufalls-3-SAT n = 70 (m/n = 4,26)"
FAM_RAMPEN30 = "Rampen-Färbung n = 30, Grad 4,5 (3 Rampen)"
FAM_SCHUBFACH5 = "Schubfach h = 5"
DEFAULT_FAMILIE = FAM_ZUFALL
DEFAULT_LERN_FORMEL = 1

# --- Farben -----------------------------------------------------------------------------------------------------------------
COLOR_CDCL = "#2F6B65"
COLOR_DPLL = "#C0504D"
COLOR_SACKGASSE = "#8C8C8C"
COLOR_LINE = "#4c78a8"
COLOR_ENTSCHEIDUNG = "#4c78a8"
COLOR_FOLGE = "#7f7f7f"
COLOR_KONFLIKT = "#C0504D"
COLOR_LOESUNG = "#2F6B65"

PRESET_HAND = "Handbeispiel F1"
PRESET_RAMPEN = "Rampen (Färbung, n = 30)"
PRESET_ZUFALL = "Zufalls-3-SAT n = 70"
PRESET_SCHUBFACH = "Schubfach h = 5"

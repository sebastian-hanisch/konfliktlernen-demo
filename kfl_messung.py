"""Messzellen der Experimente 2 bis 4: je Zelle feste Formeln, CDCL-Konflikte gegen DPLL-Widersprüche und -Sackgassen.

Eine Zelle ist ein Dictionary {"art", "params", "zeilen"} mit einer Zeile je Formel. Alles ist deterministisch (SplitMix64, feste Seeds):
`tools/messe_vorgerechnet.py` schreibt alle Zellen nach `kfl_vorgerechnet.json`, die App liest sie von dort und kann kleine Zellen
(Zufall bis n = 70, Rampen, Schur, Schubfach bis h = 5, Experiment 4 mit n = 50) auf Knopfdruck neu rechnen; `tests/test_messung.py`
prüft, dass die gespeicherten Zeilen dieser kleinen Zellen den frisch gerechneten gleichen.

Maße: CDCL = `Ergebnis.stat["konflikte"]` des Standardlösers (VSIDS mit Phasenspeicher, Luby-Neustarts mit Einheit 32, ohne Minimieren);
DPLL = Suche des Kerns mit der Regel „häufigste Variable“, `widersprueche` (Blätter, an denen die Einheitspropagation eine leere Klausel erzeugt)
und `sackgassen` (Blätter plus innere Knoten ohne Lösung darunter). Ein Abbruch am Budget heißt: die Zahl ist eine untere Schranke."""

import json
from pathlib import Path

import kfl_constants as C
import kfl_instanzen as I
from kfl_algorithm import MessLoeser
from kfl_cdcl import solve
from kfl_dpll import dpll

JSON_PFAD = Path(__file__).resolve().parent / "kfl_vorgerechnet.json"


def schluessel(art: str, **p) -> str:
    """Eindeutiger Name einer Zelle, z. B. `zufall|n=70|v=4.26`."""
    return art + "".join(f"|{k}={v:g}" if isinstance(v, float) else f"|{k}={v}" for k, v in sorted(p.items()))


def messe_formel(n, klauseln, dpll_budget, cdcl_budget=C.CDCL_BUDGET) -> dict:
    c = solve(n, klauseln, conflict_budget=cdcl_budget)
    d = dpll(klauseln, knoten_budget=dpll_budget)
    return {"antwort": c.antwort, "konflikte": c.stat["konflikte"],
            "dpll_antwort": d.erfuellbar, "widersprueche": d.widersprueche, "sackgassen": d.sackgassen, "knoten": d.knoten}


def formeln(art: str, **p) -> list:
    """Die festen Formeln einer Zelle: Liste (Kennung, Instanz)."""
    if art == "zufall":
        n = p["n"]
        m = round(p["v"] * n)
        return [(s, I.rand3(n, m, s)) for s in C.SWEEP_SEEDS]
    if art == "rampen":
        return [(s, I.rampen_instanz(p["n"], p["g"], s, C.RAMPEN_K)) for s in C.SWEEP_SEEDS]
    if art == "schur":
        return [(0, I.schur(p["n"], p["k"]))]
    if art == "schubfach":
        return [(0, I.pigeonhole(p["h"]))]
    raise ValueError(art)


def messe_zelle(art: str, **p) -> dict:
    zeilen = []
    for kennung, inst in formeln(art, **p):
        z = messe_formel(inst.n, inst.klauseln, C.DPLL_BUDGET[art])
        z["formel"] = kennung
        zeilen.append(z)
    return {"art": art, "params": p, "zeilen": zeilen}


# ------------------------------------------------------------------------------------------------------- Experiment 4: was wird gelernt
def messe_lernformel(n, seed, minimieren, verh=4.26, budget=C.CDCL_BUDGET) -> dict:
    """Eine Zufallsformel mit Analyseprotokoll: Längen der gelernten Klauseln und Sprungweiten (Konfliktstufe minus Rücksprungstufe)."""
    inst = I.rand3(n, round(verh * n), seed)
    s = MessLoeser(inst.n, inst.klauseln, minimize=minimieren)
    erg = s.loese(conflict_budget=budget)
    laengen, spruenge = {}, {}
    for stufe, rueck, laenge, _lbd in s.protokoll:
        laengen[str(laenge)] = laengen.get(str(laenge), 0) + 1
        spruenge[str(stufe - rueck)] = spruenge.get(str(stufe - rueck), 0) + 1
    return {"formel": seed, "antwort": erg.antwort, "konflikte": erg.stat["konflikte"], "gelernt": erg.stat["gelernt"],
            "literale": erg.stat["gelernte_literale"], "laengen": laengen, "spruenge": spruenge}


def messe_lernzelle(n, minimieren) -> dict:
    return {"art": "lernen", "params": {"n": n, "min": int(minimieren)},
            "zeilen": [messe_lernformel(n, s, minimieren) for s in C.LERN_SEEDS]}


def alle_zellen() -> list:
    """Alle Zellen der App als (Schlüssel, Funktion ohne Argumente)."""
    z = []
    for n in C.N_ZUFALL:
        for v in C.VERHAELTNISSE:
            z.append((schluessel("zufall", n=n, v=v), lambda n=n, v=v: messe_zelle("zufall", n=n, v=v)))
    for n in C.RAMPEN_N:
        for g in C.RAMPEN_GRAD:
            z.append((schluessel("rampen", n=n, g=g), lambda n=n, g=g: messe_zelle("rampen", n=n, g=g)))
    for n in C.SCHUR_N:
        z.append((schluessel("schur", k=C.SCHUR_K, n=n), lambda n=n: messe_zelle("schur", k=C.SCHUR_K, n=n)))
    for h in C.SCHUBFACH_H:
        z.append((schluessel("schubfach", h=h), lambda h=h: messe_zelle("schubfach", h=h)))
    for n in C.LERN_N:
        for mn in (False, True):
            z.append((schluessel("lernen", n=n, min=int(mn)), lambda n=n, mn=mn: messe_lernzelle(n, mn)))
    return z


def lade_vorgerechnet() -> dict:
    """Die gespeicherten Zellen {Schlüssel: Zelle}; leer, wenn die Datei fehlt."""
    try:
        return json.loads(JSON_PFAD.read_text(encoding="utf-8")).get("zellen", {})
    except (OSError, ValueError):
        return {}


def lade_meta() -> dict:
    try:
        return json.loads(JSON_PFAD.read_text(encoding="utf-8")).get("meta", {})
    except (OSError, ValueError):
        return {}


def live_moeglich(art: str, **p) -> bool:
    """Zellen, die sich in der App in höchstens etwa einer halben Minute nachrechnen lassen."""
    if art == "zufall":
        return p["n"] <= C.LIVE_N_MAX
    if art == "schubfach":
        return p["h"] <= 6
    if art == "lernen":
        return p["n"] <= 50
    if art == "rampen":
        return p["n"] <= 60
    return art == "schur"

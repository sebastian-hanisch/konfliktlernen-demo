"""Beispielformeln der Schritt-für-Schritt-Ansicht und Namen für Variablen und Literale.

Der Instanzerzeuger (`kfl_instanzen`) und der Zufallsgenerator (`kfl_rng`, SplitMix64) sind wörtliche Kopien des Kern-Pakets."""

import kfl_constants as C
import kfl_instanzen as I

# Handbeispiel F1 (Literale als Ganzzahlen, -5 = nicht x5):
#   K0 (x2 ∨ x3 ∨ x4) · K1 (¬x1 ∨ ¬x5 ∨ x6) · K2 (¬x1 ∨ ¬x5 ∨ ¬x6) · K3 (¬x1 ∨ x5 ∨ x6) · K4 (¬x1 ∨ x5 ∨ ¬x6)
# Unter x1 = wahr verbieten K1 bis K4 alle vier Belegungen von (x5, x6); F1 ist nur mit x1 = falsch erfüllbar.
F1_KLAUSELN = [(2, 3, 4), (-1, -5, 6), (-1, -5, -6), (-1, 5, 6), (-1, 5, -6)]
F1_N = 6


def beispiel(name: str, seed: int = C.DEFAULT_SEED) -> I.Instanz:
    """Die Beispielformel der Schritt-für-Schritt-Ansicht. `seed` wirkt nur beim Zufalls-3-SAT-Beispiel."""
    if name == C.BEISPIEL_F1:
        return I.Instanz(F1_N, list(F1_KLAUSELN), {"art": "f1"})
    if name == C.BEISPIEL_PHP2:
        return I.pigeonhole(2)
    if name == C.BEISPIEL_PHP3:
        return I.pigeonhole(3)
    if name == C.BEISPIEL_ZUFALL:
        n = C.ZUFALL_BEISPIEL_N
        return I.rand3(n, round(4.26 * n), seed)
    if name == C.BEISPIEL_FAERBUNG:
        kreis = [(i, (i + 1) % 5) if i < 4 else (0, 4) for i in range(5)]   # fünf Aufträge im Kreis, je zwei benachbarte im Konflikt
        return I.faerbung(5, kreis, 2)
    raise ValueError(f"unbekanntes Beispiel: {name}")


def variablenname(inst: I.Instanz, v: int) -> str:
    """Anzeigename der Variablen v: x<v>, bei Schubfach „Taube p in Loch l“, bei Färbung „Auftrag i auf Rampe c“."""
    art = inst.meta.get("art")
    if art == "schubfach":
        h = inst.meta["h"]
        p, l = divmod(v - 1, h)
        return f"T{p + 1}L{l + 1}"
    if art == "faerbung":
        k = inst.meta["k"]
        i, c = divmod(v - 1, k)
        return f"A{i + 1}R{c + 1}"
    return f"x{v}"


def literalname(inst: I.Instanz, lit: int) -> str:
    return ("¬" if lit < 0 else "") + variablenname(inst, abs(lit))


def klauseltext(inst: I.Instanz, klausel) -> str:
    """Klausel als Text, Literale nach Variablennummer sortiert (der Kern vertauscht die Reihenfolge wegen der beobachteten Literale)."""
    if not len(klausel):
        return "(leer)"
    return "(" + " ∨ ".join(literalname(inst, l) for l in sorted(klausel, key=abs)) + ")"


def passt_in_spur(inst: I.Instanz) -> bool:
    return inst.n <= C.SPUR_MAX_VARIABLEN and len(inst.klauseln) <= C.SPUR_MAX_KLAUSELN

"""Gemeinsame Fixtures: das Handbeispiel F1, an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import kfl_scenario as S  # noqa: E402


@pytest.fixture
def f1():
    """Handbeispiel F1 über x1..x6 mit fünf Klauseln (Plan, `handbeispiele/hb_01.py`): K0 (x2 ∨ x3 ∨ x4), K1 (¬x1 ∨ ¬x5 ∨ x6), K2 (¬x1 ∨ ¬x5 ∨ ¬x6),
    K3 (¬x1 ∨ x5 ∨ x6), K4 (¬x1 ∨ x5 ∨ ¬x6). Von Hand: DPLL (feste Reihenfolge, wahr zuerst) 14 Knoten, 6 Widersprüche, 11 Sackgassen;
    CDCL 2 Konflikte, gelernt (¬x1 ∨ ¬x5) mit Sprung von Stufe 5 auf Stufe 1, dann (¬x1) mit Sprung auf Stufe 0."""
    return S.beispiel("Handbeispiel F1")

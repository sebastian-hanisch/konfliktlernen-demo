"""Rechnet alle Messzellen der App und schreibt sie nach `kfl_vorgerechnet.json` (vorgerechnet, nicht live).

    python tools/messe_vorgerechnet.py --gruppe zufall --out teil_zufall.json     # nur die Zufallszellen (die rechenintensivsten)
    python tools/messe_vorgerechnet.py --gruppe rest   --out teil_rest.json       # Rampen, Schur, Schubfach, Experiment 4
    python tools/messe_vorgerechnet.py --zusammenfuehren teil_zufall.json teil_rest.json   # schreibt kfl_vorgerechnet.json

Die Zahlen sind deterministisch (SplitMix64, feste Seeds); nie Sekunden, nur Zähler. Aufruf aus dem Repo-Ordner."""

import argparse
import json
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import kfl_constants as C  # noqa: E402
import kfl_messung as M  # noqa: E402


def kopfzeilen() -> dict:
    """Kern-Versionen aus den Kopfzeilen der kopierten Module."""
    kern = {}
    for modul in ("rng", "instanzen", "dpll", "cdcl"):
        erste = (HIER / f"kfl_{modul}.py").read_text(encoding="utf-8").splitlines()[0]
        kern[modul] = erste.split()[2].rstrip(":")
    return kern


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gruppe", choices=["zufall", "rest"])
    ap.add_argument("--out")
    ap.add_argument("--zusammenfuehren", nargs="+")
    a = ap.parse_args()
    if a.zusammenfuehren:
        zellen = {}
        for pfad in a.zusammenfuehren:
            zellen.update(json.loads(Path(pfad).read_text(encoding="utf-8"))["zellen"])
        meta = {"seeds": list(C.SWEEP_SEEDS), "lern_seeds": list(C.LERN_SEEDS), "dpll_budget": C.DPLL_BUDGET, "cdcl_budget": C.CDCL_BUDGET,
                "kern": kopfzeilen(), "skript": "tools/messe_vorgerechnet.py"}
        text = json.dumps({"meta": meta, "zellen": dict(sorted(zellen.items()))}, ensure_ascii=False, separators=(",", ":"))
        (HIER / "kfl_vorgerechnet.json").write_text(text, encoding="utf-8", newline="\n")
        print(f"{len(zellen)} Zellen geschrieben ({len(text) // 1024} KiB)")
        return
    zellen = {}
    for schluessel, fn in M.alle_zellen():
        ist_zufall = schluessel.startswith("zufall")
        if (a.gruppe == "zufall") != ist_zufall:
            continue
        t0 = time.perf_counter()
        zellen[schluessel] = fn()
        print(f"{schluessel}  fertig nach {time.perf_counter() - t0:.0f} s", flush=True)
        Path(a.out).write_text(json.dumps({"zellen": zellen}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()

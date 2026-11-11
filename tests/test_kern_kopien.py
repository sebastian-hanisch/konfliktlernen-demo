"""Die vier kopierten Kern-Module (rng, instanzen, dpll, cdcl): Kopfzeile nennt die Kern-Version, der Rest ist wörtlich das Kern-Modul.

Ohne den Kern-Ordner (CI) wird der Hash aus der Kopie zurückgerechnet (Kopfzeile entfernen, Präfix-Import zurücksetzen) und mit der Kopfzeile verglichen;
liegt der Kern-Ordner daneben, wird zusätzlich gegen `kern/HASHES.txt` und die Quelldatei verglichen."""

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
KERN = ROOT.parent / "sat-cp-planung" / "kern"
MODULE = ["rng", "instanzen", "dpll", "cdcl"]
KOPF = re.compile(r"^# Kern-Version ([0-9a-f]{16}): Kopie von sat-cp-planung/kern/(\w+)\.py; geändert nur die Importzeile")


def _zurueck(modul):
    """Die Kopie, zurückgesetzt auf den Wortlaut des Kern-Moduls."""
    text = (ROOT / f"kfl_{modul}.py").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    erste, rest = text.split("\n", 1)
    return erste, rest.replace("from kfl_rng import", "from rng import")


@pytest.mark.parametrize("modul", MODULE)
def test_kopfzeile_nennt_die_kern_version_und_der_rest_ist_wortgleich(modul):
    erste, original = _zurueck(modul)
    m = KOPF.match(erste)
    assert m and m.group(2) == modul, erste
    assert hashlib.sha256(original.encode("utf-8")).hexdigest()[:16] == m.group(1)


@pytest.mark.parametrize("modul", MODULE)
def test_gegen_den_kern_ordner(modul):
    if not (KERN / f"{modul}.py").exists():
        pytest.skip("Kern-Ordner liegt nicht neben dem Repo")
    erste, original = _zurueck(modul)
    quelle = (KERN / f"{modul}.py").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    assert original == quelle, "die Kopie weicht vom Kern ab: Änderungen gehören in den Kern, danach neu kopieren"
    hashes = dict(reversed(z.split()) for z in (KERN / "HASHES.txt").read_text(encoding="utf-8").splitlines() if z.strip())
    assert hashes[f"{modul}.py"] == KOPF.match(erste).group(1)


def test_kein_import_aus_anderen_demos_oder_dem_kern():
    for pfad in ROOT.glob("*.py"):
        text = pfad.read_text(encoding="utf-8")
        for zeile in text.splitlines():
            if re.match(r"\s*(from|import)\s+(rng|instanzen|dpll|cdcl|rup|kodierung|vorverarbeitung|probsat)\b", zeile):
                pytest.fail(f"{pfad.name}: Import aus dem Kern statt aus der Kopie: {zeile}")

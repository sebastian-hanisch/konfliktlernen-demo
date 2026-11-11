"""Schritt-für-Schritt-Ansicht: macht aus der Ereignisspur des CDCL (`Ergebnis.spur`) Zustände, Stufentabelle und Implikationsgraph.

Sichtbare Ereignisse: entscheide, schliesse, konflikt, lerne, springe. Der Zustand nach Ereignis k enthält die Belegungen (Trail), den
offenen Konflikt (zwischen `konflikt` und `springe`), die zuletzt gelernte Klausel und den Rücksprung."""

from dataclasses import dataclass, field

import kfl_scenario as S

SICHTBAR = ("entscheide", "schliesse", "konflikt", "lerne", "springe")


@dataclass(frozen=True)
class Eintrag:
    lit: int
    stufe: int
    grund: tuple | None      # Klausel (als Tupel), die das Literal erzwungen hat; None bei Entscheidung und gelernter Einheit
    art: str                 # "entscheidung", "folge", "einheit"
    klausel_name: str | None = None


@dataclass
class Zustand:
    index: int
    ereignis: tuple
    trail: list
    konflikt: tuple | None = None       # (Klausel, Stufe, Name)
    gelernt: tuple | None = None        # (Klausel, Rücksprungstufe, LBD, Konfliktstufe)
    sprung: tuple | None = None         # (von, nach): gerade ausgeführter Rücksprung
    gelernt_liste: list = field(default_factory=list)   # (Klausel, Konfliktstufe, Rücksprungstufe, Länge)
    konflikte: int = 0


def klauselname(index: int, n_orig: int) -> str:
    return f"K{index}" if index < n_orig else f"L{index - n_orig + 1}"


def sichtbare_ereignisse(spur) -> list:
    return [e for e in spur if e[0] in SICHTBAR]


def zustaende(spur, n_orig: int) -> list:
    """Ein Zustand je sichtbarem Ereignis (Index k = Zustand nach dem k-ten sichtbaren Ereignis)."""
    erg = []
    trail: list = []
    konflikt = None
    gelernt = None
    sprung = None
    liste: list = []
    zahl = 0
    for k, e in enumerate(sichtbare_ereignisse(spur)):
        art = e[0]
        sprung = None
        if art == "entscheide":
            trail = trail + [Eintrag(e[1], e[2], None, "entscheidung")]
        elif art == "schliesse":
            trail = trail + [Eintrag(e[1], e[3], tuple(e[2]), "folge", klauselname(e[4], n_orig))]
        elif art == "konflikt":
            konflikt = (tuple(e[1]), e[2], klauselname(e[3], n_orig))
            gelernt = None
            zahl += 1
        elif art == "lerne":
            gelernt = (tuple(e[1]), e[2], e[3], konflikt[1] if konflikt else 0)
            liste = liste + [(tuple(e[1]), gelernt[3], e[2], len(e[1]))]
        elif art == "springe":
            ziel = e[1]
            von = konflikt[1] if konflikt else (max((x.stufe for x in trail), default=0))
            trail = [x for x in trail if x.stufe <= ziel]
            if gelernt is not None and len(gelernt[0]) == 1 and konflikt is not None:
                trail = trail + [Eintrag(gelernt[0][0], 0, None, "einheit")]
            sprung = (von, ziel)
            konflikt = None
            gelernt = None
        erg.append(Zustand(k, e, trail, konflikt, gelernt, sprung, liste, zahl))
    return erg


# ----------------------------------------------------------------------------------------------------------------- Beschreibung
def beschreibung(z: Zustand, inst) -> str:
    e = z.ereignis
    ln = lambda l: S.literalname(inst, l)
    if e[0] == "entscheide":
        wahl = e[3].get("wahl") if isinstance(e[3], dict) else None
        wert = "wahr" if e[1] > 0 else "falsch"
        return f"Stufe {e[2]}: entscheide {S.variablenname(inst, abs(e[1]))} = {wert}" + ("" if wahl is None else " (feste Reihenfolge)")
    if e[0] == "schliesse":
        name = z.trail[-1].klausel_name
        return f"Stufe {e[3]}: {ln(e[1])} wird erzwungen durch {name} {S.klauseltext(inst, e[2])}"
    if e[0] == "konflikt":
        return f"Konflikt {z.konflikte} auf Stufe {e[2]}: {z.konflikt[2]} {S.klauseltext(inst, e[1])} ist verletzt"
    if e[0] == "lerne":
        return (f"Lerne {S.klauseltext(inst, e[1])} (Länge {len(e[1])}, LBD {e[3]}); "
                f"Rücksprungstufe {e[2]} (Konfliktstufe {z.gelernt[3]})")
    von, nach = z.sprung
    uebersprungen = list(range(nach + 1, von))
    zusatz = "" if not uebersprungen else f" und überspringt dabei die Stufe{'n' if len(uebersprungen) > 1 else ''} " + ", ".join(map(str, uebersprungen))
    return f"Springe von Stufe {von} auf Stufe {nach}{zusatz}"


# --------------------------------------------------------------------------------------------------------------- Stufentabelle
def stufentabelle(z: Zustand, inst) -> list:
    """Zeilen (Stufe, Entscheidung, erzwungene Literale mit Grund); Stufe 0 nur, wenn dort etwas steht."""
    stufen = sorted({x.stufe for x in z.trail} | ({z.konflikt[1]} if z.konflikt else set()))
    zeilen = []
    for s in stufen:
        eintr = [x for x in z.trail if x.stufe == s]
        dec = next((S.literalname(inst, x.lit) for x in eintr if x.art == "entscheidung"), "–" if s else "")
        folgen = []
        for x in eintr:
            if x.art == "folge":
                folgen.append(f"{S.literalname(inst, x.lit)} ({x.klausel_name})")
            elif x.art == "einheit":
                folgen.append(f"{S.literalname(inst, x.lit)} (gelernte Einheit)")
        zeilen.append((s, dec, ", ".join(folgen) if folgen else "–"))
    return zeilen


# ------------------------------------------------------------------------------------------------------------ Implikationsgraph
@dataclass
class Graph:
    knoten: list                 # Einträge des Trails
    kanten: list                 # (von_lit, nach_lit): von hat nach mit erzwungen
    konflikt_von: list           # Literale, deren Verneinung in der Konfliktklausel steht (Kanten zum Konfliktknoten)
    uip: int | None = None       # Literal des 1-UIP
    seite: set = field(default_factory=set)   # Literale auf der Konfliktseite des Schnitts (ohne UIP)
    gelernt: tuple | None = None


def vorgaenger(grund, lit):
    """Literale, die `lit` erzwungen haben: die Verneinung aller anderen Literale der Grundklausel."""
    return [-q for q in grund if q != lit] if grund else []


def implikationsgraph(z: Zustand) -> Graph:
    nach_lit = {x.lit: x for x in z.trail}
    kanten = []
    for x in z.trail:
        for a in vorgaenger(x.grund, x.lit):
            if a in nach_lit:
                kanten.append((a, x.lit))
    g = Graph(list(z.trail), kanten, [])
    if z.konflikt is None:
        return g
    klausel, stufe, _ = z.konflikt
    ante = [-q for q in klausel if -q in nach_lit]
    g.konflikt_von = ante
    if z.gelernt is not None:
        uip = -z.gelernt[0][0]
        g.gelernt = z.gelernt
        if uip in nach_lit:
            g.uip = uip
            seite: set = set()
            stapel = [a for a in ante if nach_lit[a].stufe == stufe]
            while stapel:
                x = stapel.pop()
                if x == uip or x in seite:
                    continue
                seite.add(x)
                stapel.extend(a for a in vorgaenger(nach_lit[x].grund, x) if a in nach_lit and nach_lit[a].stufe == stufe)
            g.seite = seite
    return g


def schnitt_klausel(z: Zustand) -> set:
    """Die Klausel des 1-UIP-Schnitts, direkt aus dem Graphen gelesen (Verneinung des UIP und aller Vorgänger der Konfliktseite
    auf niedrigeren Stufen > 0). Gleich der gelernten Klausel ohne Minimierung (Test)."""
    g = implikationsgraph(z)
    if g.uip is None:
        return set()
    nach_lit = {x.lit: x for x in z.trail}
    stufe = z.konflikt[1]
    klausel = {-g.uip}
    quellen = list(g.konflikt_von)
    for x in g.seite:
        quellen.extend(vorgaenger(nach_lit[x].grund, x))
    for a in quellen:
        if a in nach_lit and nach_lit[a].stufe < stufe and nach_lit[a].stufe > 0:
            klausel.add(-a)
    return klausel

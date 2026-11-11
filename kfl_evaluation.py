"""Kennzahlen, Zusammenfassungen der Messzellen und Verdikte (reine Funktionen: `(Art, Text)`; die App ruft `getattr(st, Art)(Text)`)."""

from statistics import mean, median

import kfl_constants as C
import kfl_messung as M

SCHWELLE_VORSPRUNG = 1.2      # ab diesem Quotienten (DPLL-Widersprüche durch CDCL-Konflikte) gilt „Vorsprung“
SCHWELLE_NACHTEIL = 1 / 1.2   # darunter braucht der CDCL deutlich mehr Konflikte als der DPLL Widersprüche


# ----------------------------------------------------------------------------------------------------------------- Formatierung
def fmt(x) -> str:
    """Zahl deutsch: Tausenderpunkt, Dezimalkomma, ganze Zahlen ohne Nachkommastelle, sonst eine Stelle."""
    if x is None:
        return "–"
    if float(x) == int(x):
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt2(x) -> str:
    """Quotient: zwei Nachkommastellen unter 1,5 (dort liegt die Schwelle 1,2), sonst eine."""
    s = f"{x:.2f}" if x < 1.5 else f"{x:.1f}"
    return s.replace(".", ",")


def konflikte_text(k) -> str:
    return "1 Konflikt" if k == 1 else f"{fmt(k)} Konflikte"


# ------------------------------------------------------------------------------------------------------------ Zusammenfassungen
def band(werte) -> dict:
    return {"median": median(werte), "min": min(werte), "max": max(werte)}


def zusammenfassung(zeilen) -> dict:
    """Median, Minimum und Maximum je Zähler über die Formeln einer Zelle, dazu Zahl der erfüllbaren Formeln und der Abbrüche."""
    erfuellbar = sum(1 for z in zeilen if z["antwort"] is True)
    unerfuellbar = sum(1 for z in zeilen if z["antwort"] is False)
    quot = [z["sackgassen"] / z["widersprueche"] for z in zeilen if z["widersprueche"] > 0]
    return {
        "formeln": len(zeilen), "erfuellbar": erfuellbar, "unerfuellbar": unerfuellbar,
        "abbruch_cdcl": sum(1 for z in zeilen if z["antwort"] is None),
        "abbruch_dpll": sum(1 for z in zeilen if z["dpll_antwort"] is None),
        "konflikte": band([z["konflikte"] for z in zeilen]),
        "widersprueche": band([z["widersprueche"] for z in zeilen]),
        "sackgassen": band([z["sackgassen"] for z in zeilen]),
        "sack_je_wid": median(quot) if quot else None,
    }


def quotient(s: dict):
    """Median der DPLL-Widersprüche durch Median der CDCL-Konflikte (Verhältnis der Mediane); None bei Median 0 Konflikte."""
    k = s["konflikte"]["median"]
    return None if k == 0 else s["widersprueche"]["median"] / k


def zelle_holen(schl: str, vorgerechnet: dict):
    return vorgerechnet.get(schl)


# ----------------------------------------------------------------------------------------------------------------------- Verdikte
def _abbruch_hinweis(s: dict) -> str:
    teile = []
    if s["abbruch_dpll"]:
        teile.append(f"Der DPLL brach bei {s['abbruch_dpll']} von {s['formeln']} Formeln am Knotenbudget ab (seine Zahlen sind dort untere Schranken).")
    if s["abbruch_cdcl"]:
        teile.append(f"Der CDCL brach bei {s['abbruch_cdcl']} von {s['formeln']} Formeln am Konfliktbudget ab.")
    return (" " + " ".join(teile)) if teile else ""


def verdict_vergleich(s: dict, name: str) -> tuple[str, str]:
    """Verdikt für eine Zelle: DPLL-Widersprüche gegen CDCL-Konflikte (Verhältnis der Mediane). `name`: z. B. „n = 110 (m/n = 4,26)“."""
    k, w, sg = s["konflikte"]["median"], s["widersprueche"]["median"], s["sackgassen"]["median"]
    anz = "im Median" if s["formeln"] > 1 else "bei dieser Formel"
    basis = (f"{s['formeln']} feste Formeln, {s['erfuellbar']} erfüllbar" if s["formeln"] > 1 else "eine Formel")
    q = quotient(s)
    if q is None:
        return "info", (f"{name}: Der CDCL braucht {anz} keinen Konflikt, der DPLL {fmt(w)} Widersprüche ({basis}).{_abbruch_hinweis(s)}")
    zahlen = f"{fmt(w)} DPLL-Widersprüche gegen {fmt(k)} CDCL-Konflikte ({basis}; Sackgassen des DPLL {anz} {fmt(sg)})"
    if w == 0:
        return "warning", f"{name}: Gegenüber diesem DPLL hat der CDCL hier keinen Vorsprung: der DPLL kommt {anz} ohne Widerspruch aus, der CDCL braucht {konflikte_text(k)} ({basis}).{_abbruch_hinweis(s)}"
    if q >= SCHWELLE_VORSPRUNG:
        return "success", f"{name}: Der DPLL braucht {anz} **{fmt2(q)}-mal so viele Widersprüche** wie der CDCL Konflikte: {zahlen}.{_abbruch_hinweis(s)}"
    if q > SCHWELLE_NACHTEIL:
        return "info", f"{name}: **Kein Vorsprung bei dieser Größe**: {zahlen}, Quotient {fmt2(q)}.{_abbruch_hinweis(s)}"
    return "warning", (f"{name}: Gegenüber diesem DPLL hat der CDCL hier keinen Vorsprung: er braucht {anz} **{fmt2(1 / q)}-mal so viele Konflikte** wie der DPLL "
                       f"Widersprüche: {zahlen}.{_abbruch_hinweis(s)}")


def verdict_schubfach(s: dict, h: int) -> tuple[str, str]:
    """Verdikt für das Schubfach (eine Formel): unter der Schwelle „gegenüber diesem DPLL kein Vorsprung“, sonst der allgemeine Vergleich."""
    k, w = s["konflikte"]["median"], s["widersprueche"]["median"]
    q = quotient(s)
    if q is not None and q < SCHWELLE_VORSPRUNG:
        return "warning", (f"Auf Schubfach h = {h} braucht der CDCL {fmt(k)} Konflikte, der DPLL {fmt(w)} Widersprüche: gegenüber diesem DPLL hat der CDCL hier keinen Vorsprung "
                           f"(Quotient {fmt2(q)}).{_abbruch_hinweis(s)}")
    return verdict_vergleich(s, f"Schubfach h = {h}")


def wachstumsfaktoren(zeilen: list) -> dict:
    """Faktoren zwischen aufeinanderfolgenden Zellen einer Leiter (z. B. Schubfach h = 3…8) für CDCL-Konflikte und DPLL-Widersprüche (Mediane)."""
    out = {}
    for schl in ("konflikte", "widersprueche"):
        w = [s[schl]["median"] for _, s in zeilen]
        out[schl] = [b / a for a, b in zip(w, w[1:]) if a > 0]
    return out


def satz_wachstumsfaktoren(zeilen: list) -> str:
    """Satz unter der Schubfach-Tabelle: kleinster bis größter Faktor je zusätzlichem Loch, für beide Zähler."""
    f = wachstumsfaktoren(zeilen)
    if not f["konflikte"] or not f["widersprueche"]:
        return ""
    return (f"Von Zelle zu Zelle wächst der CDCL-Median um das {fmt2(min(f['konflikte']))}- bis {fmt2(max(f['konflikte']))}-Fache, "
            f"der DPLL-Median um das {fmt2(min(f['widersprueche']))}- bis {fmt2(max(f['widersprueche']))}-Fache.")


def verdict_zelle(art: str, params: dict, s: dict, label: str) -> tuple[str, str]:
    if art == "schubfach":
        return verdict_schubfach(s, params["h"])
    return verdict_vergleich(s, label)


def wachstum_serie(zellen: dict, verh: float) -> list:
    """Zeilen {n, konflikte, widersprueche, sackgassen (je Band), erfuellbar, formeln} über die vorhandenen n bei Verhältnis `verh`."""
    reihe = []
    for n in C.N_ZUFALL:
        z = zellen.get(M.schluessel("zufall", n=n, v=verh))
        if z is None:
            continue
        s = zusammenfassung(z["zeilen"])
        s["n"] = n
        reihe.append(s)
    return reihe


def verdict_wachstum(reihe: list, n: int, verh: float) -> tuple[str, str]:
    for s in reihe:
        if s["n"] == n:
            return verdict_vergleich(s, f"Bei n = {n} (m/n = {C.zahl_de(verh)})")
    return "warning", "Für diese Einstellung liegt keine Messung vor."


def verdict_wachstum_trend(reihe: list) -> str:
    """Satz unter dem Diagramm: Quotienten aller gemessenen n nebeneinander (keine Aussage über nicht gemessene n)."""
    teile = []
    for s in reihe:
        q = quotient(s)
        teile.append(f"n = {s['n']}: {fmt2(q) if q is not None else '–'}")
    return "Quotient aus DPLL-Widersprüchen und CDCL-Konflikten (Verhältnis der Mediane) bei " + "; ".join(teile) + "."


# --------------------------------------------------------------------------------------------------------------- Experiment 4
def lern_summe(zeilen) -> dict:
    """Zusammenfassung einer Lernzelle (12 Formeln): Konflikte, mittlere Länge der gelernten Klauseln, Verteilungen (summiert)."""
    laengen: dict = {}
    spruenge: dict = {}
    for z in zeilen:
        for k, v in z["laengen"].items():
            laengen[int(k)] = laengen.get(int(k), 0) + v
        for k, v in z["spruenge"].items():
            spruenge[int(k)] = spruenge.get(int(k), 0) + v
    gelernt = sum(z["gelernt"] for z in zeilen)
    literale = sum(z["literale"] for z in zeilen)
    return {"formeln": len(zeilen), "konflikte": [z["konflikte"] for z in zeilen], "median": median(z["konflikte"] for z in zeilen),
            "mittlere_laenge": (literale / gelernt) if gelernt else None, "gelernt": gelernt, "laengen": laengen, "spruenge": spruenge,
            "abbrueche": sum(1 for z in zeilen if z["antwort"] is None), "mittel_sprung": _mittel(spruenge),
            "anteil_weit": (100.0 * sum(v for k, v in spruenge.items() if k > 1) / sum(spruenge.values())) if spruenge else None}


def _mittel(verteilung: dict):
    zahl = sum(verteilung.values())
    return (sum(k * v for k, v in verteilung.items()) / zahl) if zahl else None


def verdict_minimieren(ohne: dict, mit: dict) -> tuple[str, str]:
    """Konfliktzahl mit und ohne Minimieren über dieselben Formeln: Mediane, Zahl der Formeln mit weniger Konflikten, mittlere Länge."""
    paare = list(zip(ohne["konflikte"], mit["konflikte"]))
    weniger = sum(1 for a, b in paare if b < a)
    gleich = sum(1 for a, b in paare if b == a)
    mehr = sum(1 for a, b in paare if b > a)
    text = (f"Über {ohne['formeln']} feste Formeln: ohne Minimieren im Median {fmt(ohne['median'])} Konflikte, mit Minimieren {fmt(mit['median'])}; "
            f"die gelernten Klauseln sind im Mittel {fmt(ohne['mittlere_laenge'])} gegen {fmt(mit['mittlere_laenge'])} Literale lang. "
            f"Mit Minimieren braucht es bei {weniger} Formeln weniger, bei {gleich} gleich viele und bei {mehr} mehr Konflikte.")
    if ohne["median"] > 0 and mit["median"] < ohne["median"] and weniger > mehr:
        proz = 100 * (ohne["median"] - mit["median"]) / ohne["median"]
        return "success", f"Minimieren spart im Median {fmt(proz)} % der Konflikte (Bezug: ohne Minimieren). " + text
    if mit["median"] == ohne["median"] and weniger == mehr:
        return "info", "Minimieren ändert den Median nicht. " + text
    return "warning", "Kein verlässlicher Vorteil durch Minimieren bei dieser Formelmenge. " + text


# --------------------------------------------------------------------------------------------------------- Experiment 1 (Formel)
def verdict_formel(n_widerspruch: int, n_sackgassen: int, n_konflikte: int, antwort) -> tuple[str, str]:
    """Verdikt der Kernfrage für die gewählte Beispielformel (aus den Zählern des Laufs)."""
    wort = {True: "erfüllbar", False: "unerfüllbar", None: "unbekannt (Budget)"}[antwort]
    zahlen = (f"Die Formel ist {wort}. Der DPLL (feste Reihenfolge, wahr zuerst) endet in {n_widerspruch} Widersprüchen "
              f"({n_sackgassen} Sackgassen insgesamt), der CDCL mit Lernen braucht {n_konflikte} Konflikte.")
    if n_konflikte < n_widerspruch:
        return "success", zahlen + f" Das Lernen spart hier {n_widerspruch - n_konflikte} Konflikte gegenüber den Widersprüchen."
    if n_konflikte == n_widerspruch:
        return "info", zahlen + " Hier gleichen sich beide Zähler: kein Vorsprung des Lernens."
    return "warning", zahlen + " Hier braucht das Lernen mehr Konflikte als die Suche ohne Gedächtnis Widersprüche."


def sicher_median(werte):
    return median(werte)


def mittel(werte):
    return mean(werte)

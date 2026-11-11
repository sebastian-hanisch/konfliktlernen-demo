"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.
Jede Unterscheidung steht doppelt: Farbe und Form beziehungsweise Beschriftung (kein Farbcode allein)."""

import plotly.graph_objects as go

import kfl_constants as C
import kfl_scenario as S
import kfl_trace as T


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", y=-0.18))
    return lock_axes(fig)


# ----------------------------------------------------------------------------------------------------------------- Implikationsgraph
YABSTAND = 1.6     # senkrechter Abstand der Reihen: genug Platz, dass Pfeile nicht über fremde Knoten laufen


def positionen(z: T.Zustand) -> tuple[dict, int]:
    """Position (x = Stufe, y = Reihe in der Stufe, Entscheidung oben) je Literal; zweiter Wert: höchste Stufe der Anzeige."""
    pos = {}
    zeile: dict[int, int] = {}
    for x in z.trail:
        r = zeile.get(x.stufe, 0)
        pos[x.lit] = (x.stufe, -YABSTAND * r)
        zeile[x.stufe] = r + 1
    hoechste = max([x.stufe for x in z.trail] + ([z.konflikt[1]] if z.konflikt else []) + ([z.sprung[0]] if z.sprung else []), default=0)
    return pos, hoechste


def build_graph(inst, z: T.Zustand):
    """Implikationsgraph des Zustands: Spalten = Entscheidungsstufen, Entscheidungen oben, Pfeile von der Begründung zur Folge.
    Mit Konflikt: Konfliktknoten (Kreuz), der 1-UIP (Stern), die Konfliktseite des Schnitts gestrichelt; mit Rücksprung ein Pfeil über den Stufen."""
    g = T.implikationsgraph(z)
    pos, hoechste = positionen(z)
    fig = go.Figure()
    if z.konflikt is not None:
        kx, ky = hoechste + 0.9, -max(YABSTAND * 0.5, (max((-p[1] for p in pos.values()), default=0)) * 0.6)
    else:
        kx = ky = None
    # Pfeile (Annotationen mit Pfeilspitze)
    for a, b in g.kanten:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        fig.add_annotation(x=x2, y=y2, ax=x1, ay=y1, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1,
                           arrowwidth=1.2, arrowcolor="rgba(120,120,120,0.9)", standoff=9, startstandoff=9, text="")
    for a in g.konflikt_von:
        x1, y1 = pos[a]
        fig.add_annotation(x=kx, y=ky, ax=x1, ay=y1, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowwidth=1.4,
                           arrowcolor=C.COLOR_KONFLIKT, standoff=10, startstandoff=9, text="")
    # Knoten nach Art
    arten = {"entscheidung": ("diamond", C.COLOR_ENTSCHEIDUNG, "Entscheidung"), "folge": ("circle", C.COLOR_FOLGE, "erzwungen"),
             "einheit": ("square", C.COLOR_FOLGE, "gelernte Einheit")}
    for art, (symbol, farbe, name) in arten.items():
        xs = [x for x in z.trail if x.art == art]
        if not xs:
            continue
        fig.add_trace(go.Scatter(
            x=[pos[x.lit][0] for x in xs], y=[pos[x.lit][1] for x in xs], mode="markers+text", name=name,
            marker=dict(symbol=symbol, size=26, color=farbe, line=dict(width=2, color="rgba(255,255,255,0.0)")),
            text=[S.literalname(inst, x.lit) for x in xs], textposition="bottom center",
            hovertext=[f"{S.literalname(inst, x.lit)} auf Stufe {x.stufe}" + (f", erzwungen durch {x.klausel_name} {S.klauseltext(inst, x.grund)}" if x.grund else "")
                       for x in xs], hoverinfo="text"))
    if g.uip is not None:
        fig.add_trace(go.Scatter(x=[pos[g.uip][0]], y=[pos[g.uip][1]], mode="markers+text", name="1-UIP",
                                 marker=dict(symbol="star", size=34, color="rgba(0,0,0,0)", line=dict(width=2.5, color=C.COLOR_KONFLIKT)),
                                 text=["1-UIP"], textposition="top center", hoverinfo="skip"))
    if z.konflikt is not None:
        fig.add_trace(go.Scatter(x=[kx], y=[ky], mode="markers+text", name="Konflikt", marker=dict(symbol="x", size=30, color=C.COLOR_KONFLIKT,
                                 line=dict(width=3, color=C.COLOR_KONFLIKT)), text=[f"Konflikt {z.konflikt[2]}"], textposition="bottom center",
                                 hovertext=[f"verletzte Klausel {z.konflikt[2]} {S.klauseltext(inst, z.konflikt[0])}"], hoverinfo="text"))
        if g.uip is not None:
            xs = [pos[l][0] for l in g.seite] + [kx]
            ys = [pos[l][1] for l in g.seite] + [ky]
            fig.add_shape(type="rect", x0=min(xs) - 0.4, x1=max(xs) + 0.45, y0=min(ys) - 0.55, y1=max(ys) + 0.45, xref="x", yref="y",
                          line=dict(color=C.COLOR_KONFLIKT, width=2, dash="dash"), fillcolor="rgba(192,80,77,0.06)")
            fig.add_annotation(x=(min(xs) + max(xs)) / 2, y=min(ys) - 0.55, text="Konfliktseite (Schnitt nach dem 1-UIP)", showarrow=False,
                               yanchor="top", font=dict(size=11, color=C.COLOR_KONFLIKT))
    # Stufenüberschriften, alle Stufen
    for s in range(0, hoechste + 1):
        fig.add_annotation(x=s, y=1.1, text=f"Stufe {s}", showarrow=False, font=dict(size=12))
    # Rücksprung
    ziel = von = None
    if z.gelernt is not None and z.konflikt is not None:
        von, ziel = z.konflikt[1], z.gelernt[1]
    elif z.sprung is not None:
        von, ziel = z.sprung
    if von is not None and ziel is not None and von != ziel:
        uebersprungen = list(range(ziel + 1, von))
        text = f"Sprung von Stufe {von} auf Stufe {ziel}" + (f" (überspringt {', '.join(map(str, uebersprungen))})" if uebersprungen else "")
        fig.add_annotation(x=ziel, y=1.85, ax=von, ay=1.85, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowwidth=2.2,
                           arrowcolor=C.COLOR_CDCL, text="")
        fig.add_annotation(x=(von + ziel) / 2, y=2.1, text=text, showarrow=False, font=dict(size=12, color=C.COLOR_CDCL))
    tief = max([-p[1] for p in pos.values()] + [YABSTAND])
    fig.update_xaxes(range=[-0.7, hoechste + (1.7 if z.konflikt else 0.8)], showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(range=[-tief - 1.3, 2.5], showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, height=int(150 + 68 * (tief + 3.8)))


# ----------------------------------------------------------------------------------------------------------------------- DPLL-Baum
def build_dpll_baum(inst, baum):
    """Suchbaum des DPLL: Blätter mit Widerspruch rot (Kreuz), innere Knoten ohne Lösung grau, der Weg zur Lösung grün."""
    knoten = baum.knoten
    xpos: dict[int, float] = {}
    zaehler = [0]

    def lege(i):
        k = knoten[i]
        if not k.kinder:
            xpos[i] = zaehler[0]
            zaehler[0] += 1
        else:
            for c in k.kinder:
                lege(c)
            xpos[i] = sum(xpos[c] for c in k.kinder) / len(k.kinder)

    lege(0)
    fig = go.Figure()
    kx, ky = [], []
    for k in knoten:
        if k.eltern is not None:
            kx += [xpos[k.eltern], xpos[k.id], None]
            ky += [-knoten[k.eltern].tiefe, -k.tiefe, None]
    fig.add_trace(go.Scatter(x=kx, y=ky, mode="lines", line=dict(color="rgba(120,120,120,0.7)", width=1.5), hoverinfo="skip", showlegend=False))
    stile = {"widerspruch": ("Widerspruch (Blatt)", "x", C.COLOR_DPLL), "sackgasse": ("Sackgasse (innerer Knoten, beide Zweige scheitern)", "circle", C.COLOR_SACKGASSE),
             "loesung": ("Lösung", "star", C.COLOR_LOESUNG), "offen": ("Knoten auf dem Weg zur Lösung", "diamond", C.COLOR_LOESUNG)}
    for art, (name, symbol, farbe) in stile.items():
        ks = [k for k in knoten if k.art == art]
        if not ks:
            continue
        fig.add_trace(go.Scatter(
            x=[xpos[k.id] for k in ks], y=[-k.tiefe for k in ks], mode="markers+text", name=name,
            marker=dict(symbol=symbol, size=15, color=farbe, line=dict(width=2, color=farbe)),
            text=["" if k.wahl is None else S.literalname(inst, k.wahl) for k in ks], textposition="top center", textfont=dict(size=10),
            hovertext=[("Wurzel" if k.wahl is None else f"Verzweigung auf {S.literalname(inst, k.wahl)}") + f", Tiefe {k.tiefe}" for k in ks], hoverinfo="text"))
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, range=[-0.7, max(xpos.values()) + 0.7])
    tiefe = max(k.tiefe for k in knoten)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, range=[-tiefe - 0.6, 0.7])
    return _base(fig, height=190 + 45 * tiefe)


# ---------------------------------------------------------------------------------------------------------------- Bänder und Balken
def _geklemmt(werte):
    return [max(v, 0.5) for v in werte]


def build_wachstum(reihe):
    """Median mit Band (Minimum bis Maximum) über die festen Formeln je n: CDCL-Konflikte, DPLL-Widersprüche, DPLL-Sackgassen (Nebenzahl)."""
    xs = [s["n"] for s in reihe]
    fig = go.Figure()
    serien = [("konflikte", "CDCL: Konflikte", C.COLOR_CDCL, "solid", "circle", "rgba(47,107,101,0.15)"),
              ("widersprueche", "DPLL: Widersprüche (Vergleichsmaß)", C.COLOR_DPLL, "solid", "square", "rgba(192,80,77,0.15)"),
              ("sackgassen", "DPLL: Sackgassen (Nebenzahl)", C.COLOR_SACKGASSE, "dot", "triangle-up", None)]
    for schl, name, farbe, dash, symbol, fuell in serien:
        if fuell:
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=_geklemmt([s[schl]["max"] for s in reihe]) + _geklemmt([s[schl]["min"] for s in reihe])[::-1],
                                     fill="toself", fillcolor=fuell, mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=xs, y=_geklemmt([s[schl]["median"] for s in reihe]), mode="lines+markers", name=name,
                                 line=dict(color=farbe, width=3, dash=dash), marker=dict(symbol=symbol, size=9),
                                 customdata=[[s[schl]["min"], s[schl]["max"], s[schl]["median"]] for s in reihe],
                                 hovertemplate="n = %{x}: Median %{customdata[2]}, Minimum %{customdata[0]}, Maximum %{customdata[1]}<extra>" + name + "</extra>"))
    fig.update_xaxes(title_text="Variablen n", tickvals=xs)
    fig.update_yaxes(title_text="Zähler (Median, Band Minimum bis Maximum; logarithmisch, 0 bei 0,5)", type="log")
    return _base(fig)


def build_familie(zeilen, gewaehlt):
    """Balken je Zelle der Familie: CDCL-Konflikte gegen DPLL-Widersprüche (Median; logarithmisch). `zeilen`: [(Beschriftung, Zusammenfassung)];
    die gewählte Zelle ist in der Beschriftung markiert."""
    namen = [("▶ " if b == gewaehlt else "") + b.split(" (")[0] for b, _ in zeilen]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=namen, y=_geklemmt([s["konflikte"]["median"] for _, s in zeilen]), name="CDCL: Konflikte", marker_color=C.COLOR_CDCL,
                         customdata=[s["konflikte"]["median"] for _, s in zeilen], hovertemplate="%{x}: %{customdata}<extra>CDCL-Konflikte</extra>"))
    fig.add_trace(go.Bar(x=namen, y=_geklemmt([s["widersprueche"]["median"] for _, s in zeilen]), name="DPLL: Widersprüche", marker_color=C.COLOR_DPLL,
                         marker_pattern_shape="/", customdata=[s["widersprueche"]["median"] for _, s in zeilen],
                         hovertemplate="%{x}: %{customdata}<extra>DPLL-Widersprüche</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Zähler (Median; logarithmisch)", type="log")
    fig.update_xaxes(tickangle=-30)
    return _base(fig)


def build_verteilung(ohne: dict, mit: dict, xtitel: str):
    """Histogramm einer Verteilung (Längen der gelernten Klauseln, Sprungweiten) ohne und mit Minimieren: {Wert: Anzahl}."""
    fig = go.Figure()
    for daten, name, farbe, muster in ((ohne, "ohne Minimieren", C.COLOR_LINE, ""), (mit, "mit Minimieren", C.COLOR_CDCL, "x")):
        xs = sorted(daten)
        fig.add_trace(go.Bar(x=xs, y=[daten[k] for k in xs], name=name, marker_color=farbe, marker_pattern_shape=muster,
                             hovertemplate=xtitel + " %{x}: %{y} Klauseln<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text=xtitel, dtick=1 if max(list(ohne) + list(mit) + [1]) <= 20 else None)
    fig.update_yaxes(title_text="Zahl gelernter Klauseln")
    return _base(fig, height=300)

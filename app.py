"""Konfliktklauseln lernen – aus jedem Fehlschlag eine Regel - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück der Linie „SAT und Constraint Programming“ (Wurzel des SAT-Arms): wie ein Löser aus einem Fehlschlag eine Klausel lernt und bis zur
verursachenden Entscheidung zurückspringt, und was das gegenüber einer Suche ohne Gedächtnis bringt. Aufwand in Konflikten und Widersprüchen,
nie in Sekunden. Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import kfl_algorithm as A
import kfl_constants as C
import kfl_messung as M
import kfl_scenario as S
import kfl_trace as T
from kfl_cdcl import Loeser
from kfl_evaluation import (
    fmt,
    fmt2,
    lern_summe,
    satz_wachstumsfaktoren,
    quotient,
    verdict_formel,
    verdict_minimieren,
    verdict_wachstum,
    verdict_wachstum_trend,
    verdict_zelle,
    wachstum_serie,
    zusammenfassung,
)
from kfl_layout import dunkles_design, kopf_css
from kfl_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kfl_visualization import build_dpll_baum, build_familie, build_graph, build_verteilung, build_wachstum

st.set_page_config(page_title="Konfliktklauseln lernen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _vorgerechnet():
    return M.lade_vorgerechnet(), M.lade_meta()


@st.cache_data(show_spinner=False)
def _lauf(name, seed, minimieren):
    """Beispielformel: CDCL mit Spur (Handbeispiel-Regeln), Zustände je Ereignis und der DPLL-Baum derselben Regeln."""
    inst = S.beispiel(name, seed)
    n_orig = len(Loeser(inst.n, inst.klauseln).klauseln)
    erg = A.cdcl_spur(inst.n, inst.klauseln, minimieren=minimieren)
    zs = T.zustaende(erg.spur, n_orig)
    baum = A.dpll_baum(inst.klauseln, regel="erste")
    return {"inst": inst, "antwort": erg.antwort, "konflikte": erg.stat["konflikte"], "zustaende": zs, "baum": baum,
            "gekuerzt": erg.spur_gekuerzt}


def _md_table(kopf, zeilen):
    z = ["| " + " | ".join(kopf) + " |", "|" + "---|" * len(kopf)]
    z += ["| " + " | ".join(str(c) for c in r) + " |" for r in zeilen]
    return "\n".join(z)


def _live(art, params):
    """Rechnet eine Zelle neu (deterministisch) und gibt (Zelle, Sekunden) zurück."""
    t0 = time.perf_counter()
    zelle = M.messe_lernzelle(params["n"], bool(params["min"])) if art == "lernen" else M.messe_zelle(art, **params)
    return zelle, time.perf_counter() - t0


def _live_knopf(schl, art, params, vorg, taste):
    """Knopf „live nachrechnen“ mit Spinner; zeigt, ob das Ergebnis den vorgerechneten Zeilen gleicht."""
    if not M.live_moeglich(art, **params):
        st.caption("Diese Zelle ist **vorgerechnet** (Skript `tools/messe_vorgerechnet.py`, nicht live): das Nachrechnen in der App dauert zu lange.")
        return
    gespeichert = vorg.get(schl)
    st.caption("Die Zahlen oben sind **vorgerechnet** (nicht live). Diese Zelle lässt sich hier neu rechnen und mit den gespeicherten Zeilen vergleichen.")
    if st.button("🔁 Diese Zelle jetzt live nachrechnen", key=f"live_{taste}"):
        with st.spinner("Rechnet alle Formeln der Zelle neu (kleine Zellen brauchen Sekunden)…"):
            zelle, sek = _live(art, params)
        gleich = gespeichert is not None and zelle["zeilen"] == gespeichert["zeilen"]
        if gleich:
            st.success(f"Live nachgerechnet in {sek:.1f} s: alle {len(zelle['zeilen'])} Zeilen stimmen mit den vorgerechneten überein.")
        else:
            st.warning(f"Live nachgerechnet in {sek:.1f} s: die Zeilen weichen von den vorgerechneten ab oder diese fehlen.")


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kfl_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧠 Konfliktklauseln lernen – aus jedem Fehlschlag eine Regel")
st.markdown(
    """
Eine Suche **ohne Gedächtnis** (DPLL) kann denselben Fehler in vielen Ästen wiederholen. Ein Löser mit **Konfliktlernen** (CDCL) leitet aus dem Fehlschlag
eine neue **Klausel** ab und **springt** bis zur Entscheidung zurück, die ihn verursacht hat; die Äste dazwischen entfallen. Die Demo zeigt das an einer Formel von Hand,
**zählt** dann **Konflikte gegen Widersprüche** und fragt, wann das Lernen etwas bringt. Die Messungen zeigen: Gegen diesen DPLL zahlt sich der CDCL bei Zufalls-3-SAT (m/n = 4,26 und 4,5) ab n = 90
und bei Zuordnungen von Aufträgen zu Rampen (Färbung eines Konfliktgraphen) mit Grad 4,5 und 5,0 ab n = 60 aus, beim Schubfach erst bei h = 8. Der Aufwand wird gezählt, nie als Zeit gemessen.

Weiter unten: die Experimente **🔍 Eine Formel von Hand**, **🔬 Wächst der Vorsprung mit der Größe?**, **🔬 Wo das Lernen hilft und wo nicht** und
**🔬 Was wird gelernt?**, dann **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/konfliktlernen-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Stellen Sie sich eine Planung mit vielen Ja-Nein-Entscheidungen und festen Regeln vor. Läuft die Suche in eine Sackgasse, geht ein einfaches Verfahren nur einen Schritt zurück und kann denselben Fehler in vielen anderen Zweigen wiederholen. Ein Löser mit **Konfliktlernen** fragt stattdessen, welche seiner Entscheidungen den Fehlschlag verursacht haben, hält das als **neue Regel** fest und **springt** zur früheren dieser Entscheidungen zurück. Die neue Regel folgt aus den alten, sie spricht nur aus, was dort schon steckte.

Die Demo zeigt das an einer kleinen Formel von Hand und **zählt** dann Fehlschläge: Sie fragt, bei welchen Aufgaben das Gedächtnis weniger kostet. Das Ergebnis fällt gemischt aus: erst bei größeren Zufallsformeln, beim Schubfach lange gar nicht. Gezählt werden Konflikte, keine Sekunden.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/konfliktlernen-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert Konfliktlernen", expanded=True):
    st.markdown(
        """
1. **Entscheiden und folgern.** Der Löser belegt eine Variable (eine *Entscheidung*, eine neue *Stufe*) und erzwingt daraus alles, was die Klauseln zwingend verlangen (*Einheitspropagation*).
2. **Konflikt.** Wird eine Klausel ganz falsch, ist das ein *Konflikt*: die Entscheidungen bis hierher passen nicht zusammen. Die DPLL-Suche kehrt nur eine Stufe zurück und probiert die Gegenwahl.
3. **Analyse.** Der *Implikationsgraph* zeigt, welche Belegung welche erzwungen hat. Rückwärts vom Konflikt wird so lange aufgelöst, bis auf der Konfliktstufe nur noch **ein** Literal übrig ist (der *1-UIP*, erste eindeutige Implikationsstelle). Das Ergebnis ist die **gelernte Klausel**.
4. **Lernen und Rücksprung.** Die gelernte Klausel folgt aus den Klauseln davor und verbietet die Belegung, die zu diesem Konflikt geführt hat; nach dem Rücksprung ist sie sofort eine Einheit. Der Löser **springt** auf die zweithöchste Stufe in der gelernten Klausel zurück; die Stufen dazwischen waren am Konflikt unbeteiligt.
5. **Warum das funktioniert:** Jede gelernte Klausel folgt aus den Klauseln davor (RUP, im Test geprüft); sie fasst einen ganzen Teilbaum von Fehlschlägen zusammen, den die Suche ohne Gedächtnis in vielen Ästen wiederholen kann.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Beispielformel**")
    ist_zufall = st.session_state["formel"] == C.BEISPIEL_ZUFALL
    seed = st.number_input("Zufalls-Seed der Zufallsformel", *bounds("seed_input"), key="seed_input", step=1, disabled=not ist_zufall,
                           help="Wirkt nur auf das Beispiel „Zufalls-3-SAT, n = 12“ in Experiment 1; die Messreihen haben feste Seeds.")
    st.button("🎲 Zufallsformel würfeln", width="stretch", on_click=randomize_seed,
              help="Wählt das Beispiel „Zufalls-3-SAT, n = 12“ und würfelt einen neuen Zufalls-Seed.")
    if not ist_zufall:
        st.caption("Der Zufalls-Seed ist nur beim Beispiel „Zufalls-3-SAT, n = 12“ wirksam.")

vorg, meta = _vorgerechnet()

# --- Experiment 1: eine Formel von Hand -----------------------------------------------------------------------------------------

st.subheader("🔍 Eine Formel von Hand: Schritt für Schritt")
st.caption("Feste Reihenfolge x1, x2, …, wahr zuerst, ohne Neustarts: so lässt sich jeder Schritt nachrechnen. Der CDCL ist der Löser des Kern-Pakets, der DPLL die Suche ohne Gedächtnis (gleiche Regel).")
c1, c2 = st.columns([3, 1])
with c1:
    name = st.selectbox("Beispielformel", C.BEISPIELE, key="formel", help="F1 ist das Handbeispiel; die übrigen sind klein genug (höchstens 12 Variablen, 60 Klauseln) für die Schritt-für-Schritt-Ansicht.")
with c2:
    minimieren = st.toggle("Klausel minimieren", key="minimieren1", help="Streicht überflüssige Literale aus der gelernten Klausel (lokale Minimierung des Kerns).")
seed_eff = int(st.session_state["seed_input"]) if name == C.BEISPIEL_ZUFALL else C.DEFAULT_SEED
lauf = _lauf(name, seed_eff, bool(minimieren))
inst, zs, baum = lauf["inst"], lauf["zustaende"], lauf["baum"]
schritt_key = f"schritt_{name}_{int(minimieren)}_{seed_eff}"

st.markdown("**Klauseln:** " + " · ".join(f"K{i} {S.klauseltext(inst, k)}" for i, k in enumerate(inst.klauseln)))

m1, m2, m3, m4 = st.columns(4)
antwort_text = {True: "erfüllbar", False: "unerfüllbar", None: "unbekannt"}[lauf["antwort"]]
m1.metric("Antwort", antwort_text)
m2.metric("DPLL: Widersprüche", baum.widersprueche, delta="Vergleichsmaß", delta_color="off")
m3.metric("DPLL: Sackgassen", baum.sackgassen, delta="Nebenzahl", delta_color="off")
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
m4.metric("CDCL: Konflikte", lauf["konflikte"], delta=f"{lauf['konflikte'] - baum.widersprueche:+d} gegen DPLL-Widersprüche", delta_color="inverse")

if lauf["gekuerzt"] or not zs:
    st.warning("Die Spur dieser Formel ist zu lang für die Schritt-für-Schritt-Ansicht.")
else:
    if schritt_key not in st.session_state:
        st.session_state[schritt_key] = 0
    letzter = len(zs) - 1

    def _springe(delta=None, naechster_konflikt=False):
        k = st.session_state[schritt_key]
        if naechster_konflikt:
            nach = [z.index for z in zs if z.index > k and z.ereignis[0] == "konflikt"]
            st.session_state[schritt_key] = nach[0] if nach else k
        else:
            st.session_state[schritt_key] = max(0, min(letzter, k + delta))

    b1, b2, b3 = st.columns(3)
    b1.button("◀ Zurück", key=f"zur_{schritt_key}", on_click=_springe, kwargs={"delta": -1}, width="stretch")
    b2.button("Vor ▶", key=f"vor_{schritt_key}", on_click=_springe, kwargs={"delta": 1}, width="stretch")
    b3.button("⏭ Nächster Konflikt", key=f"konf_{schritt_key}", on_click=_springe, kwargs={"naechster_konflikt": True}, width="stretch")
    k = st.slider("Schritt", 0, letzter, key=schritt_key, help="Ereignisse des CDCL: entscheide, schließe (erzwungen), Konflikt, lerne, springe.") if letzter > 0 else 0
    z = zs[k]
    st.info(f"**Schritt {k + 1} von {letzter + 1}.** " + T.beschreibung(z, inst))

    links, rechts = st.columns([2, 3])
    with links:
        aktuell = z.konflikt[1] if z.konflikt else (z.trail[-1].stufe if z.trail else 0)
        if z.sprung is not None:
            aktuell = z.sprung[1]
        zeilen = [(s, d, f, "◀ aktuell" if s == aktuell else "") for s, d, f in T.stufentabelle(z, inst)]
        st.markdown("**Entscheidungsstufen**")
        if zeilen:
            st.markdown(_md_table(["Stufe", "Entscheidung", "erzwungen (Grund)", ""], zeilen))
        else:
            st.caption("Noch nichts belegt.")
        if z.gelernt_liste:
            st.markdown("**Gelernte Klauseln bisher**")
            for i, (kl, stufe, rueck, laenge) in enumerate(z.gelernt_liste, start=1):
                st.markdown(f"- L{i} {S.klauseltext(inst, kl)}: Länge {laenge}, Konfliktstufe {stufe}, Rücksprung auf Stufe {rueck}")
    with rechts:
        st.plotly_chart(build_graph(inst, z), width="stretch", key=f"graph_{schritt_key}_{k}")
        if z.gelernt is not None:
            st.markdown(f"**Gelernte Klausel:** {S.klauseltext(inst, z.gelernt[0])}, Rücksprung auf Stufe {z.gelernt[1]}.")
        st.caption("Pfeile: von der Begründung zur Folge. Raute: Entscheidung, Kreis: erzwungen, Kreuz: Konflikt, Stern: 1-UIP; gestrichelt: Konfliktseite des Schnitts.")

    st.markdown("**Nebeneinander: Suche ohne Gedächtnis und Konfliktlernen für dieselbe Formel**")
    d1, d2 = st.columns([3, 2])
    with d1:
        st.markdown(f"DPLL-Baum (feste Reihenfolge, wahr zuerst): {len(baum.knoten)} Knoten, **{baum.widersprueche} Widersprüche**, {baum.sackgassen} Sackgassen")
        st.plotly_chart(build_dpll_baum(inst, baum), width="stretch", key=f"dpll_{schritt_key}")
        st.caption("Kreuz: Widerspruch (Blatt); Kreis: innerer Knoten, dessen beide Zweige scheitern (Sackgasse); Stern oder Raute: Lösung beziehungsweise Weg dorthin.")
    with d2:
        st.markdown(f"CDCL: **{lauf['konflikte']} Konflikte**")
        letzte = zs[-1].gelernt_liste
        if letzte:
            st.markdown(_md_table(["Konflikt", "gelernte Klausel", "Stufe → Sprung"],
                                  [(i, S.klauseltext(inst, kl), f"{s} → {r}") for i, (kl, s, r, _) in enumerate(letzte, start=1)]))
        else:
            st.caption("Der CDCL kam ohne Konflikt aus.")

st.markdown("---")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel spart das Lernen gegenüber der Suche ohne Gedächtnis?")
kind, text = verdict_formel(baum.widersprueche, baum.sackgassen, lauf["konflikte"], lauf["antwort"])
getattr(st, kind)(text)
st.caption("**Zählweise:** Das Vergleichsmaß ist der DPLL-**Widerspruch** (ein Blatt, an dem die Einheitspropagation eine leere Klausel erzeugt), denn er entspricht einem CDCL-Konflikt. "
           "Die **Sackgassen** des DPLL (Blätter und innere Knoten ohne Lösung darunter) sind bei unerfüllbaren Formeln 2 × Widersprüche − 1; wer Konflikte gegen Sackgassen stellt, überzeichnet den Vorsprung bei unerfüllbaren Formeln deshalb etwa um den Faktor 2. Sie stehen nur als Nebenzahl da.")

st.markdown("---")

# --- Experiment 2: Wachstum ----------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wächst der Vorsprung mit der Größe?")
st.caption(f"Zufalls-3-SAT: je Zelle {len(C.SWEEP_SEEDS)} feste Formeln (Zufalls-Seeds 1 bis {len(C.SWEEP_SEEDS)}), Klauseln je Variable m/n wählbar. "
           "Median mit Band (Minimum bis Maximum); die Zellen sind vorgerechnet, kleine lassen sich live nachrechnen.")
e1, e2 = st.columns(2)
n_w = e1.select_slider("Variablen n (für das Verdikt)", C.N_ZUFALL, key="wachs_n", help="Das Diagramm zeigt alle n; das Verdikt nennt das gewählte.")
verh = e2.select_slider("Klauseln je Variable m/n", C.VERHAELTNISSE, key="wachs_verh", format_func=C.zahl_de,
                        help="4,26 liegt am Phasenübergang von Zufalls-3-SAT bei großem n; 4,0 ist leichter, 4,5 meist unerfüllbar.")
reihe = wachstum_serie(vorg, verh)
if not reihe:
    st.warning("Die vorgerechneten Messzellen fehlen (`kfl_vorgerechnet.json`).")
else:
    st.plotly_chart(build_wachstum(reihe), width="stretch", key="wachs_chart")
    kind, text = verdict_wachstum(reihe, n_w, verh)
    getattr(st, kind)(text)
    st.caption(verdict_wachstum_trend(reihe))
    st.caption("Eine einzelne Zelle ist keine Schwelle: mit anderen 20 Formeln verschiebt sich der Quotient bei kleinen n um mehrere Zehntel (README, Abschnitt Befunde); "
               "die Grenze 1,2 des Verdikts ist eine Festlegung dieser Demo.")
    _live_knopf(M.schluessel("zufall", n=n_w, v=verh), "zufall", {"n": n_w, "v": verh}, vorg, f"w_{n_w}_{verh}")

st.markdown("---")

# --- Experiment 3: Familien -------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wo das Lernen hilft und wo nicht")
st.caption("Aufträge auf Rampen (Färbung eines Konfliktgraphen mit 3 Rampen), Schur-Zahlen (3 Mengen) und Schubfach neben dem Zufall. Je Familie die ganze Leiter der Größen; die gewählte Zelle ist markiert (▶).")
fam = st.selectbox("Familie und Größe", list(C.FAMILIEN), key="familie")
art, params = C.FAMILIEN[fam]


def _leiter(art, params):
    """Alle Zellen derselben Familie (bei Rampen mit gleichem Grad), als [(Beschriftung, Schlüssel, Parameter)]."""
    aus = []
    for b, (a, p) in C.FAMILIEN.items():
        if a != art or (a == "rampen" and p["g"] != params["g"]):
            continue
        aus.append((b, M.schluessel(a, **p), p))
    return aus


leiter = _leiter(art, params)
zeilen_f = [(b, zusammenfassung(vorg[s]["zeilen"])) for b, s, _ in leiter if s in vorg]
if not zeilen_f:
    st.warning("Die vorgerechneten Messzellen fehlen (`kfl_vorgerechnet.json`).")
else:
    st.plotly_chart(build_familie(zeilen_f, fam), width="stretch", key="fam_chart")
    tab = []
    for b, s in zeilen_f:
        q = quotient(s)
        tab.append((("▶ " if b == fam else "") + b, f"{s['erfuellbar']} von {s['formeln']}", fmt(s["konflikte"]["median"]),
                    fmt(s["widersprueche"]["median"]) + (" (Abbruch, untere Schranke)" if s["abbruch_dpll"] else ""),
                    fmt(s["sackgassen"]["median"]), fmt2(q) if q is not None else "–"))
    st.markdown(_md_table(["Zelle", "erfüllbar", "CDCL-Konflikte", "DPLL-Widersprüche", "DPLL-Sackgassen", "Quotient"], tab))
    st.caption("Median über die festen Formeln der Zelle (Schur und Schubfach: eine Formel); Quotient = DPLL-Widersprüche geteilt durch CDCL-Konflikte.")
    aktuell = next(s for b, s in zeilen_f if b == fam)
    kind, text = verdict_zelle(art, params, aktuell, fam)
    getattr(st, kind)(text)
    if art == "schubfach" and len(zeilen_f) > 1:
        st.caption(satz_wachstumsfaktoren(zeilen_f))
    _live_knopf(M.schluessel(art, **params), art, params, vorg, f"f_{fam}")

st.markdown("---")

# --- Experiment 4: was wird gelernt ----------------------------------------------------------------------------------------------------

st.subheader("🔬 Was wird gelernt?")
st.caption(f"Zufalls-3-SAT (m/n = 4,26), {len(C.LERN_SEEDS)} feste Formeln: Längen der gelernten Klauseln und Sprungweiten (Konfliktstufe minus Rücksprungstufe), ohne und mit Klausel-Minimierung.")
f1, f2 = st.columns(2)
ln = f1.select_slider("Variablen n", C.LERN_N, key="lern_n", help="n = 50 lässt sich live nachrechnen; n = 150 ist vorgerechnet.")
lf = f2.slider("Formel (für die Verteilungen)", *bounds("lern_formel"), key="lern_formel", help="Welche der festen Formeln die beiden Diagramme zeigen; die Zusammenfassung gilt für alle.")
z_ohne, z_mit = vorg.get(M.schluessel("lernen", n=ln, min=0)), vorg.get(M.schluessel("lernen", n=ln, min=1))
if not (z_ohne and z_mit):
    st.warning("Die vorgerechneten Messzellen fehlen (`kfl_vorgerechnet.json`).")
else:
    s_ohne, s_mit = lern_summe(z_ohne["zeilen"]), lern_summe(z_mit["zeilen"])
    kind, text = verdict_minimieren(s_ohne, s_mit)
    getattr(st, kind)(text)
    zo, zm = z_ohne["zeilen"][lf - 1], z_mit["zeilen"][lf - 1]
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"**Länge der gelernten Klauseln, Formel {lf}** ({zo['konflikte']} Konflikte ohne, {zm['konflikte']} mit Minimieren)")
        st.plotly_chart(build_verteilung({int(a): b for a, b in zo["laengen"].items()}, {int(a): b for a, b in zm["laengen"].items()}, "Länge"),
                        width="stretch", key="lern_laenge")
    with g2:
        st.markdown(f"**Sprungweite, Formel {lf}** (Konfliktstufe minus Rücksprungstufe)")
        st.plotly_chart(build_verteilung({int(a): b for a, b in zo["spruenge"].items()}, {int(a): b for a, b in zm["spruenge"].items()}, "Sprungweite"),
                        width="stretch", key="lern_sprung")
    st.caption(f"Alle {s_ohne['formeln']} Formeln zusammen ohne Minimieren: mittlere Sprungweite {fmt(s_ohne['mittel_sprung'])}, "
               f"{fmt(s_ohne['anteil_weit'])} % der Sprünge gehen über mehr als eine Stufe (mit Minimieren: {fmt(s_mit['mittel_sprung'])} und {fmt(s_mit['anteil_weit'])} %). "
               "Sprungweite 1 heißt: der Löser kehrt nur eine Stufe zurück, wie die Suche ohne Gedächtnis.")
    if M.live_moeglich("lernen", n=ln):
        st.caption("Die Zahlen sind **vorgerechnet** (nicht live).")
        if st.button("🔁 Beide Zellen live nachrechnen", key=f"live_lern_{ln}"):
            with st.spinner("Rechnet 12 Formeln mit und ohne Minimieren neu (Sekunden)…"):
                (neu0, s0), (neu1, s1) = _live("lernen", {"n": ln, "min": 0}), _live("lernen", {"n": ln, "min": 1})
            if neu0["zeilen"] == z_ohne["zeilen"] and neu1["zeilen"] == z_mit["zeilen"]:
                st.success(f"Live nachgerechnet in {s0 + s1:.1f} s: alle Zeilen stimmen mit den vorgerechneten überein.")
            else:
                st.warning(f"Live nachgerechnet in {s0 + s1:.1f} s: die Zeilen weichen von den vorgerechneten ab.")
    else:
        st.caption("Diese Zelle ist **vorgerechnet** (Skript `tools/messe_vorgerechnet.py`, nicht live).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Vergleichsgegner ist dieser eine DPLL** (häufigste Variable, Einheitspropagation, Listenkopie). | Mit einer anderen Verzweigungsregel oder stärkerer Propagation ändern sich die Widerspruchszahlen; gemessen ist nur diese Variante. | Die Verzweigungsregel des CDCL selbst: Variablenwahl nach Aktivität. |
| **Konflikte sind ein Maß für Aufwand.** | Ein Konflikt des CDCL kostet mehr Arbeit als ein Widerspruch des DPLL (Analyse, Lernen); die Zeit je Konflikt ist nicht gemessen, es gibt hier keine Zeitangabe als Befund. | Datenstrukturen des Lösers: Watched Literals. |
| **Lernen lohnt bei jeder Formel.** | Bei den gemessenen kleinen Zufallsformeln und beim Schubfach bis h = 7 nicht (siehe Messzellen); der Vorteil zeigt sich erst bei wachsenden Zufallsformeln (und nicht bei jedem Verhältnis m/n). | Beim Schubfach: Symmetriebrechung. |
| **Alle gelernten Klauseln bleiben nützlich.** | Sie häufen sich an und verlangsamen die Propagation. | Löschen gelernter Klauseln. |
| **Eine Instanzfamilie steht für alle.** | Gemessen sind Zufalls-3-SAT (n bis 110), Rampen-Färbung, Schur (k = 3) und Schubfach; Industrieformeln und größere n sind nicht gemessen. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/konfliktlernen-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist eine Formel in konjunktiver Normalform über Variablen $x_1,\dots,x_n$. Gesucht ist eine erfüllende Belegung oder der Nachweis, dass es keine gibt. Gemessen wird der Aufwand in Konflikten und Widersprüchen, nie in Sekunden.

| Symbol | Bedeutung |
|---|---|
| $\mathrm{lvl}(\ell)$ | Entscheidungsstufe, auf der das Literal $\ell$ wahr wurde |
| $d$ | Konfliktstufe: die aktuelle Entscheidungsstufe beim Konflikt |
| $C_k$ | die verletzte Klausel (Konfliktklausel) |
| $u,\ R$ | gelernte Klausel $\neg u \vee R$: $u$ ist die erste eindeutige Implikationsstelle (ein Literal der Stufe $d$), $R$ der Rest auf niedrigeren Stufen |
| $\beta$ | Rücksprungstufe: die höchste Stufe der Literale in $R$ |
| $W,\ S,\ N$ | DPLL-Widersprüche, Sackgassen und Knoten des Suchbaums |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/konfliktlernen-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben ist eine Formel in konjunktiver Normalform $F = C_1 \wedge \dots \wedge C_m$ über Variablen $x_1,\dots,x_n$ (Klauseln $C_j$ sind Oder-Verknüpfungen von Literalen $x_i$ oder $\neg x_i$).
Gesucht ist eine erfüllende Belegung oder der Nachweis, dass es keine gibt.

| Symbol | Bedeutung |
|---|---|
| $\mathrm{lvl}(\ell)$ | Entscheidungsstufe, auf der das Literal $\ell$ wahr wurde |
| $d$ | Konfliktstufe: die aktuelle Entscheidungsstufe beim Konflikt |
| $C_k$ | die verletzte Klausel (Konfliktklausel) |
| $W$, $S$ | DPLL-Widersprüche (Blätter mit leerer Klausel) und Sackgassen (Blätter und innere Knoten ohne Lösung darunter) |

**Auflösung (Resolution).** Aus zwei Klauseln mit gegensätzlichem Literal folgt die Resolvente:
$$ (A \vee x) \wedge (B \vee \neg x) \;\Longrightarrow\; (A \vee B). $$

**Gelernte Klausel (1-UIP).** Ausgehend von der Konfliktklausel wird in umgekehrter Reihenfolge der Belegung jeweils das letzte Literal der Stufe $d$ mit seiner Begründung aufgelöst, bis genau ein Literal $u$ der Stufe $d$ übrig bleibt (die erste eindeutige Implikationsstelle):
$$ L = C_k \;\overset{\text{Auflösungen}}{\longrightarrow}\; \bigl(\neg u \vee R\bigr), \qquad \mathrm{lvl}(r) < d \text{ für alle } r \in R. $$

**Rücksprungstufe.** Die gelernte Klausel wird nach dem Rücksprung sofort zur Einheit:
$$ \beta = \max\{\mathrm{lvl}(r) : r \in R\} \quad (\beta = 0 \text{ bei } R = \emptyset). $$
Die Stufen $\beta+1,\dots,d-1$ werden übersprungen.

**Folgerichtigkeit.** Jede gelernte Klausel $L$ folgt aus den Klauseln davor durch Einheitspropagation unter der Verneinung von $L$ (RUP); der Test prüft das mit einem unabhängigen Prüfer.

**Zählweise der Suche ohne Gedächtnis.** Im Suchbaum des DPLL hat jeder Knoten null Kinder (ein Blatt mit Widerspruch) oder zwei. Ist die Formel unerfüllbar, sind alle Blätter Widersprüche, und der Baum hat
$$ N = 2W - 1 \quad \text{Knoten, und alle sind Sackgassen: } S = N. $$
Der Vergleich mit dem CDCL nimmt deshalb $W$ (der Widerspruch ist das Gegenstück zum Konflikt) und nicht $S$.

**Literatur.** Konfliktklauseln aus dem Implikationsgraphen und nichtchronologisches Zurückspringen: J. P. Marques-Silva, K. A. Sakallah, GRASP: A Search Algorithm for Propositional Satisfiability, IEEE Transactions on Computers 48(5), 1999, S. 506–521 (Einleitung und Abschnitte 2 und 3.1 gelesen). Die Wahl des *First UIP* nennen G. Audemard, L. Simon, Predicting learnt clauses quality in modern SAT solvers, IJCAI 2009 (Abschnitte 3, 4 und 6 gelesen); ob GRASP selbst den ersten UIP als Standard nimmt, wurde nicht geprüft.
Resolutionsbeweise des Schubfachprinzips sind nach A. Haken, The intractability of resolution, Theoretical Computer Science 39 (1985), 297–308, exponentiell lang (Haken selbst nur im Abstract gelesen; die Aussage nach P. Beame, T. Pitassi, R. Impagliazzo, Exponential lower bounds for the pigeonhole principle, Computational Complexity 3 (1993), 97–140, Einleitung gelesen). Gelernte Klauseln sind Resolventen; die Folgerung für den CDCL ist eine eigene, in den gelesenen Quellen nicht ausdrücklich genannte.
        """
    )

sync_query_params({k: st.session_state[k] for k in SETTING_SPECS})

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)

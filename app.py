import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import base64

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="QdC Dependència — Generalitat de Catalunya",
    page_icon="📊",
    layout="wide",
)

# --- Password gate ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    pwd = st.text_input("Contrasenya", type="password", placeholder="Introdueix la contrasenya")
    if pwd == st.secrets.get("password", "dependencia2026"):
        st.session_state.authenticated = True
        st.rerun()
    elif pwd:
        st.error("Contrasenya incorrecta")
    st.stop()

check_password()

DATA = Path(__file__).parent / "data"

# ---------------------------------------------------------------------------
# Palette — consistent across all charts
# ---------------------------------------------------------------------------
C_VAL = "#c4122f"           # Valoració = Generalitat red
C_VAL_LIGHT = "rgba(196,18,47,0.15)"
C_PIA = "#2563eb"           # PIA = blue
C_PIA_LIGHT = "rgba(37,99,235,0.15)"
C_PAPER = "#d1d5db"         # Paper = gray
C_DIGITAL = "#2563eb"       # Digital = same blue as PIA
C_PCT_LINE = "#c4122f"      # % lines = red
C_POS = "#16a34a"           # Positive / good
C_NEG = "#dc2626"           # Negative / bad
C_BLACK = "#1a1a1a"
C_GRAY_700 = "#4a4a4a"
C_GRAY_500 = "#8c8c8c"
C_GRAY_300 = "#d1d5db"
C_GRAY_200 = "#e5e7eb"
C_GRAY_100 = "#f3f4f6"
C_WHITE = "#ffffff"

FONT = "Open Sans, Helvetica Neue, Arial, sans-serif"

# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------
LOGO_PATH = Path(__file__).parent / "logo_gene.png"
if LOGO_PATH.exists():
    LOGO_B64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
else:
    LOGO_B64 = ""

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap');
    html, body, [class*="st-"] {{ font-family: {FONT}; }}

    /* intentionally blank — header uses st.logo + st.markdown */

    .stTabs [data-baseweb="tab-list"] {{ gap: 0; border-bottom: 2px solid {C_GRAY_200}; }}
    .stTabs [data-baseweb="tab"] {{
        padding: 0.7rem 1.4rem; font-weight: 600; font-size: 0.78rem;
        letter-spacing: 0.04em; text-transform: uppercase; color: {C_GRAY_500};
        border-bottom: 3px solid transparent;
    }}
    .stTabs [aria-selected="true"] {{
        color: {C_BLACK} !important;
        border-bottom: 3px solid {C_VAL} !important;
        background: transparent !important;
    }}

    [data-testid="stMetric"] {{
        background: {C_WHITE}; border: 1px solid {C_GRAY_200};
        border-radius: 8px; padding: 0.8rem 1rem;
    }}
    [data-testid="stMetricLabel"] p {{
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.05em; color: {C_GRAY_500};
    }}
    [data-testid="stMetricValue"] {{ font-size: 1.4rem; font-weight: 700; color: {C_BLACK}; }}

    h4 {{
        color: {C_BLACK}; font-weight: 700; font-size: 1rem;
        border-bottom: 1px solid {C_GRAY_200}; padding-bottom: 0.3rem; margin-top: 1.2rem;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .block-container {{ padding-top: 3rem; }}
    .stAlert {{ border-radius: 8px; }}
</style>
""", unsafe_allow_html=True)

# Header
logo_img = f'<img src="data:image/png;base64,{LOGO_B64}" style="height:44px" />' if LOGO_B64 else ""
st.markdown(f"""
<div style="display:flex;align-items:flex-end;gap:0.8rem;padding-bottom:0.6rem;
            border-bottom:2px solid {C_GRAY_200};margin-bottom:0.6rem">
    {logo_img}
    <div style="display:flex;flex-direction:column;justify-content:space-between;height:44px">
        <div style="font-size:1.1rem;font-weight:700;color:{C_BLACK};line-height:1.2">
            Quadre de Comandament — Dependència</div>
        <div style="font-size:0.82rem;color:{C_GRAY_500};line-height:1.2">
            Departament de Drets Socials i Inclusió</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_csv(name):
    return pd.read_csv(DATA / f"{name}.csv")


def load_volume():
    val = load_csv("val_entrats").merge(load_csv("val_resolts"), on="mes").merge(load_csv("val_pendents"), on="mes")
    pia = load_csv("pia_entrats").merge(load_csv("pia_resolts"), on="mes").merge(load_csv("pia_pendents"), on="mes")
    return val, pia


def load_formularis():
    df = load_csv("formularis")
    df["setmana"] = pd.to_datetime(df["setmana"])
    return df


def load_imserso():
    return (
        pd.read_csv(DATA / "imserso_temps.csv"),
        pd.read_csv(DATA / "imserso_pendents.csv"),
        pd.read_csv(DATA / "imserso_solicituds.csv"),
    )


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------
def base_layout(height=380):
    return dict(
        font=dict(family=FONT, size=12, color=C_BLACK),
        plot_bgcolor=C_WHITE, paper_bgcolor=C_WHITE,
        margin=dict(l=50, r=20, t=50, b=60),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=C_WHITE, font_size=12, bordercolor=C_GRAY_300),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0, font=dict(size=11)),
        height=height,
    )


def style_axes(fig):
    fig.update_xaxes(showgrid=False, linecolor=C_GRAY_200, tickfont=dict(size=11, color=C_GRAY_500))
    fig.update_yaxes(showgrid=True, gridcolor=C_GRAY_100, linecolor=C_GRAY_200, tickfont=dict(size=11, color=C_GRAY_500))
    return fig


def sfig(fig, height=380):
    fig.update_layout(**base_layout(height))
    return style_axes(fig)


def fmt(n):
    return f"{n:,.0f}".replace(",", ".") if abs(n) >= 1000 else str(int(n))


PC = dict(displayModeBar=False)  # plotly config


# ---------------------------------------------------------------------------
# P1 — Impacte
# ---------------------------------------------------------------------------
BASELINE = "2026-01"  # Baseline for all tabs. All deltas compare to this.
TEMPS_TOTAL = 372     # Internal median total time (sol → PIA), days

def render_p1():
    val, pia = load_volume()
    form = load_formularis()

    last = val["mes"].iloc[-1]
    # Find baseline index
    bl_candidates = val[val["mes"] == BASELINE].index
    bl = bl_candidates[0] if len(bl_candidates) > 0 else 0

    st.caption(f"Últimes dades: **{last}** · Baseline: **{BASELINE}**")

    # --- Row 1: headline KPI ---
    st.metric(
        label="TEMPS TOTAL SOL·LICITUD → PRESTACIÓ (mediana)",
        value=f"{TEMPS_TOTAL} dies",
        delta="—",  # Will show real delta when we have time series
        delta_color="off",
    )

    st.markdown("")

    # --- Row 2: operational KPIs ---
    c1, c2, c3, c4, c5 = st.columns(5)

    def dm(col, lbl, cur, prev, inv=False):
        d = cur - prev
        col.metric(lbl, fmt(cur), f"{d:+,.0f}".replace(",", "."),
                   delta_color="inverse" if inv else "normal")

    dm(c1, "Pendents VAL", val["pendents"].iloc[-1], val["pendents"].iloc[bl], inv=True)
    dm(c2, "Pendents PIA", pia["pendents"].iloc[-1], pia["pendents"].iloc[bl], inv=True)

    total_pend = val["pendents"].iloc[-1] + pia["pendents"].iloc[-1]
    total_pend_bl = val["pendents"].iloc[bl] + pia["pendents"].iloc[bl]
    dm(c3, "Bossa total", total_pend, total_pend_bl, inv=True)

    # Resolts this month (VAL + PIA)
    resolts_now = val["resolts"].iloc[-1] + pia["resolts"].iloc[-1]
    resolts_bl = val["resolts"].iloc[bl] + pia["resolts"].iloc[bl]
    dm(c4, "Resolts (VAL+PIA)", resolts_now, resolts_bl)

    # % Digital
    recent_f = form[form["setmana"] >= form["setmana"].max() - pd.Timedelta(days=14)]
    early_f = form[form["setmana"] <= form["setmana"].min() + pd.Timedelta(days=14)]
    pct_now = recent_f["pct_digital"].mean()
    c5.metric("% Digital", f"{pct_now:.0f}%",
              f"+{pct_now - early_f['pct_digital'].mean():.0f} pp vs inici")

    st.markdown("")

    # --- Charts ---
    col_a, col_b = st.columns(2)

    # Left: Stacked bars pendents (bossa)
    with col_a:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=val["mes"], y=val["pendents"], name="Bossa VAL",
            marker_color=C_VAL, marker_line_width=0, opacity=0.8,
            hovertemplate="%{y:,.0f}",
        ))
        fig.add_trace(go.Bar(
            x=pia["mes"], y=pia["pendents"], name="Bossa PIA",
            marker_color=C_PIA, marker_line_width=0, opacity=0.8,
            hovertemplate="%{y:,.0f}",
        ))
        sfig(fig, 340)
        fig.update_layout(
            title=dict(text="Bossa total (VAL + PIA)", font=dict(size=13)),
            barmode="stack",
        )
        st.plotly_chart(fig, use_container_width=True, config=PC)

    # Right: Entries over time (demand)
    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=val["mes"], y=val["entrats"], name="Entrats VAL",
            marker_color=C_GRAY_300, marker_line_width=0,
            hovertemplate="%{y:,.0f}",
        ))
        # Add a trend line (rolling 6-month average)
        rolling = val["entrats"].rolling(6, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=val["mes"], y=rolling, name="Tendència (6m)",
            line=dict(color=C_BLACK, width=2, dash="dot"),
            hovertemplate="%{y:,.0f}",
        ))
        sfig(fig, 340)
        fig.update_layout(title=dict(text="Sol·licituds entrades per mes", font=dict(size=13)))
        fig.update_yaxes(title_text="Sol·licituds")
        st.plotly_chart(fig, use_container_width=True, config=PC)

    # Row 3: Capacity net — VAL and PIA side by side
    col_v, col_p = st.columns(2)

    for col, label, df, color in [(col_v, "Valoració", val, C_VAL), (col_p, "PIA", pia, C_PIA)]:
        with col:
            net = df["resolts"] - df["entrats"]
            bar_colors = [C_POS if v >= 0 else C_GRAY_300 for v in net]

            fig = go.Figure(go.Bar(
                x=df["mes"], y=net,
                marker_color=bar_colors, marker_line_width=0,
                hovertemplate="%{y:+,.0f}<extra></extra>",
            ))
            fig.add_hline(y=0, line_color=C_BLACK, line_width=1.5)
            # Annotations to help interpretation
            fig.add_annotation(
                x=0.01, y=1, xref="paper", yref="paper",
                text="↑ Bossa baixa", showarrow=False,
                font=dict(size=10, color=C_POS), xanchor="left",
            )
            fig.add_annotation(
                x=0.01, y=0, xref="paper", yref="paper",
                text="↓ Bossa creix", showarrow=False,
                font=dict(size=10, color=C_GRAY_500), xanchor="left", yanchor="bottom",
            )
            sfig(fig, 280)
            fig.update_layout(
                title=dict(text=f"{label} — Capacitat neta (resolts − entrats)", font=dict(size=13)),
                showlegend=False,
                margin=dict(l=50, r=20, t=50, b=40),
            )
            st.plotly_chart(fig, use_container_width=True, config=PC)


# ---------------------------------------------------------------------------
# P2 — Volum
# ---------------------------------------------------------------------------
def render_p2():
    val, pia = load_volume()
    st.caption(f"Últimes dades: **{val['mes'].iloc[-1]}** · Baseline: **{BASELINE}**")

    for label, df, color in [("Valoració", val, C_VAL), ("PIA", pia, C_PIA)]:
        st.markdown(f"#### {label}")

        last = df.iloc[-1]
        bl_candidates = df[df["mes"] == BASELINE].index
        bl_idx = bl_candidates[0] if len(bl_candidates) > 0 else 0
        bl_row = df.iloc[bl_idx]

        c1, c2, c3 = st.columns(3)
        c1.metric("Entrats", fmt(last["entrats"]),
                  f"{last['entrats'] - bl_row['entrats']:+,.0f}".replace(",", "."))
        c2.metric("Resolts", fmt(last["resolts"]),
                  f"{last['resolts'] - bl_row['resolts']:+,.0f}".replace(",", "."))
        c3.metric("Pendents", fmt(last["pendents"]),
                  f"{last['pendents'] - bl_row['pendents']:+,.0f}".replace(",", "."),
                  delta_color="inverse")

        col_a, col_b = st.columns(2)

        with col_a:
            fig = go.Figure(go.Bar(
                x=df["mes"], y=df["pendents"], marker_color=color,
                marker_line_width=0, opacity=0.85, hovertemplate="%{y:,.0f}",
            ))
            sfig(fig, 300)
            fig.update_layout(title=dict(text="Pendents", font=dict(size=13)), showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config=PC)

        with col_b:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["mes"], y=df["entrats"], name="Entrats",
                                marker_color=C_GRAY_300, marker_line_width=0, hovertemplate="%{y:,.0f}"))
            fig.add_trace(go.Bar(x=df["mes"], y=df["resolts"], name="Resolts",
                                marker_color=color, marker_line_width=0, opacity=0.85, hovertemplate="%{y:,.0f}"))
            sfig(fig, 300)
            fig.update_layout(title=dict(text="Entrats vs Resolts", font=dict(size=13)), barmode="group")
            st.plotly_chart(fig, use_container_width=True, config=PC)

        st.markdown("")


# ---------------------------------------------------------------------------
# P3 — Terminis
# ---------------------------------------------------------------------------
def render_p3():
    st.info("Pendent de rebre les dades corregides de terminis per fase.", icon="⏳")
    st.caption(f"Baseline: **{BASELINE}**")

    phases_val = [("Sol·licitud → SEVAD", 24), ("Tramitació VAL", 20), ("Valoració", 128), ("Resolució VAL", 1)]
    phases_pia = [("CAPECON", 29), ("Tramitació PIA", 70), ("Resolució PIA", 198), ("Notificació PIA", 3)]
    total_val = sum(d for _, d in phases_val)
    total_pia = sum(d for _, d in phases_pia)
    total = total_val + total_pia

    # --- Grau selector ---
    grau_sel = st.radio("Grau", ["Tots", "Grau I", "Grau II", "Grau III"], horizontal=True)

    # Dummy data per grau (placeholder — s'actualitzarà amb dades reals)
    grau_factors = {"Tots": 1.0, "Grau I": 0.75, "Grau II": 1.0, "Grau III": 1.35}
    factor = grau_factors[grau_sel]
    adj_total = int(TEMPS_TOTAL * factor)

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Termini total (mediana)", f"{adj_total} dies", "Objectiu: 240 dies", delta_color="off")
    c2.metric("Fase valoració", f"{int(total_val * factor)} dies",
              f"{total_val/total*100:.0f}% del total", delta_color="off")
    c3.metric("Fase PIA", f"{int(total_pia * factor)} dies",
              f"{total_pia/total*100:.0f}% del total", delta_color="off")

    st.markdown("")
    st.markdown("#### Circuit complet — fases")

    val_colors = ["#fbbf24", "#f59e0b", "#ef4444", C_VAL]
    pia_colors = ["#93c5fd", "#60a5fa", C_PIA, "#1e3a5f"]
    all_phases = phases_val + phases_pia
    all_colors = val_colors + pia_colors

    phase_labels = []
    for i, (name, _) in enumerate(all_phases):
        prefix = "→ " if i > 0 else ""
        phase_labels.append(f"{prefix}{name}")

    fig = go.Figure()
    for i, (name, days) in enumerate(all_phases):
        adj_days = int(days * factor)
        fig.add_trace(go.Bar(
            x=[adj_days], y=[phase_labels[i]], orientation="h",
            marker_color=all_colors[i], marker_line_width=0,
            text=f"  {adj_days}d", textposition="outside",
            textfont=dict(size=11, color=C_BLACK),
            hovertemplate=f"<b>{name}</b><br>{adj_days} dies<extra></extra>",
            showlegend=False,
        ))

    sfig(fig, 380)
    fig.update_layout(
        margin=dict(l=180, r=80, t=10, b=30),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        xaxis=dict(title_text="Dies"),
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True, config=PC)

    # Summary with colored borders
    col_v, col_p = st.columns(2)
    with col_v:
        st.markdown(f'<div style="border-left:4px solid {C_VAL};padding-left:12px">'
                     f'<strong>Valoració: {int(total_val * factor)} dies</strong><br>'
                     f'<span style="color:{C_GRAY_500};font-size:0.85rem">'
                     f'Sol·licitud → resolució grau</span></div>',
                     unsafe_allow_html=True)
    with col_p:
        st.markdown(f'<div style="border-left:4px solid {C_PIA};padding-left:12px">'
                     f'<strong>PIA: {int(total_pia * factor)} dies</strong><br>'
                     f'<span style="color:{C_GRAY_500};font-size:0.85rem">'
                     f'Resolució grau → prestació</span></div>',
                     unsafe_allow_html=True)

    if grau_sel != "Tots":
        st.caption(f"⚠️ Dades per {grau_sel} són estimacions placeholder. S'actualitzaran amb dades reals.")

    st.markdown("")
    st.markdown("#### Metodologia")
    st.markdown(
        "- **Univers:** procediments tancats aquell mes · "
        "**Indicador:** mediana (no mitjana), excloent >P90 · "
        "**Filtre:** només inicials (sense revisions) · "
        "**Desglossament:** per grau (I, II, III)"
    )


# ---------------------------------------------------------------------------
# P4 — Digitalització
# ---------------------------------------------------------------------------
def render_p4():
    df = load_formularis()
    st.caption(f"Dades setmanals: **{df['setmana'].min().strftime('%Y-%m-%d')}** a **{df['setmana'].max().strftime('%Y-%m-%d')}**")
    recent, early = df.tail(4), df.head(4)

    c1, c2, c3 = st.columns(3)
    c1.metric("% Digital (últim mes)", f"{recent['pct_digital'].mean():.0f}%",
              f"+{recent['pct_digital'].mean() - early['pct_digital'].mean():.0f} pp vs inici")
    c2.metric("Digital / setmana", fmt(int(recent["digital"].mean())))
    c3.metric("Paper / setmana", fmt(int(recent["paper"].mean())))

    st.markdown("")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df["setmana"], y=df["paper"], name="Paper",
        marker_color=C_GRAY_300, marker_line_width=0, hovertemplate="%{y:,.0f}",
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df["setmana"], y=df["digital"], name="Digital",
        marker_color=C_PIA, marker_line_width=0, hovertemplate="%{y:,.0f}",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["setmana"], y=df["pct_digital"], name="% Digital",
        line=dict(color=C_VAL, width=2.5), hovertemplate="%{y:.1f}%",
    ), secondary_y=True)
    fig.add_hline(y=90, line_dash="dash", line_color=C_GRAY_500, line_width=1,
                  annotation_text="Objectiu 90 %", annotation_position="top right",
                  annotation_font=dict(size=10, color=C_GRAY_500), secondary_y=True)

    sfig(fig, 430)
    fig.update_layout(barmode="stack",
                      title=dict(text="Sol·licituds dependència: paper vs digital", font=dict(size=13)))
    fig.update_yaxes(title_text="Sol·licituds / setmana", secondary_y=False)
    fig.update_yaxes(title_text="% Digital", secondary_y=True, range=[0, 100], ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True, config=PC)


# ---------------------------------------------------------------------------
# P5 — IMSERSO (monitoring del relat: què veu el món exterior)
# ---------------------------------------------------------------------------
def render_p5():
    temps, pendents, solicituds = load_imserso()
    last_date = temps["fecha"].max()
    EXCLUDE = ["TOTAL", "Ceuta y Melilla"]

    st.caption(f"Dades públiques IMSERSO — últim mes disponible: **{last_date}**")
    st.markdown(
        "> Aquestes dades són les que publica l'IMSERSO i les que utilitzen premsa i oposició. "
        "**No coincideixen amb les dades internes** (SIDEP) per diferències metodològiques "
        "documentades. S'inclouen per monitorar el relat extern."
    )

    cat_t = temps[(temps["ccaa"] == "Cataluña") & (temps["fecha"] == last_date)].iloc[0]
    esp_t = temps[(temps["ccaa"] == "TOTAL") & (temps["fecha"] == last_date)].iloc[0]
    cat_p = pendents[(pendents["ccaa"] == "Cataluña") & (pendents["fecha"] == last_date)].iloc[0]

    tl = temps[(temps["fecha"] == last_date) & (~temps["ccaa"].isin(EXCLUDE))]
    rank = tl.sort_values("tiempo_sol_a_pia_dias")["ccaa"].tolist().index("Cataluña") + 1
    n_ccaa = len(tl)

    # --- KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temps total (IMSERSO)", f"{cat_t['tiempo_sol_a_pia_dias']:.0f}d",
              f"Posició {rank}/{n_ccaa}", delta_color="off")
    c2.metric("Sol → Grau", f"{cat_t['tiempo_sol_a_grado_dias']:.0f}d",
              f"{cat_t['tiempo_sol_a_grado_dias'] - esp_t['tiempo_sol_a_grado_dias']:+.0f} vs Espanya",
              delta_color="inverse")
    c3.metric("Grau → PIA", f"{cat_t['tiempo_grado_a_pia_dias']:.0f}d",
              f"{cat_t['tiempo_grado_a_pia_dias'] - esp_t['tiempo_grado_a_pia_dias']:+.0f} vs Espanya",
              delta_color="inverse")
    c4.metric("% Pendents", f"{cat_p['pct_total_pendents']:.1f}%",
              f"{fmt(int(cat_p['total_pendents']))} persones", delta_color="off")

    st.markdown("")

    # --- Chart 1: Time decomposition ranking ---
    st.markdown("#### Temps per CCAA — descomposició sol→grau i grau→PIA")
    r = tl.sort_values("tiempo_sol_a_pia_dias").copy()

    # Add total column for text labels
    r["total"] = r["tiempo_sol_a_pia_dias"]
    max_total = r["total"].max()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=r["ccaa"], x=r["tiempo_sol_a_grado_dias"],
        orientation="h", name="Sol → Grau",
        marker_color=[C_VAL if c == "Cataluña" else "rgba(196,18,47,0.30)" for c in r["ccaa"]],
        marker_line_width=0,
        customdata=r["ccaa"],
        hovertemplate="<b>%{customdata}</b><br>Sol → Grau: %{x:.0f} dies<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=r["ccaa"], x=r["tiempo_grado_a_pia_dias"],
        orientation="h", name="Grau → PIA",
        marker_color=[C_PIA if c == "Cataluña" else "rgba(37,99,235,0.30)" for c in r["ccaa"]],
        marker_line_width=0,
        customdata=r["ccaa"],
        text=r["total"].apply(lambda x: f"  {x:.0f}d"),
        textposition="outside",
        textfont=dict(size=10, color=C_BLACK),
        hovertemplate="<b>%{customdata}</b><br>Grau → PIA: %{x:.0f} dies<extra></extra>",
    ))

    sfig(fig, 500)
    fig.update_layout(
        barmode="stack", yaxis=dict(autorange="reversed"),
        margin=dict(l=180, r=20, t=10, b=60),
        hovermode="closest",
    )
    fig.update_xaxes(title_text="Dies", range=[0, max_total * 1.15])
    st.plotly_chart(fig, use_container_width=True, config=PC)

    # --- Chart 2: Evolution Catalunya decomposed ---
    st.markdown("#### Evolució temps — Catalunya segons IMSERSO")
    cat_e = temps[temps["ccaa"] == "Cataluña"].sort_values("fecha")
    esp_e = temps[temps["ccaa"] == "TOTAL"].sort_values("fecha")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cat_e["fecha"], y=cat_e["tiempo_sol_a_grado_dias"],
        name="CAT: Sol → Grau", mode="lines",
        line=dict(width=0.5, color=C_VAL), stackgroup="cat",
        fillcolor=C_VAL_LIGHT, hovertemplate="%{y:.0f}d",
    ))
    fig.add_trace(go.Scatter(
        x=cat_e["fecha"], y=cat_e["tiempo_grado_a_pia_dias"],
        name="CAT: Grau → PIA", mode="lines",
        line=dict(width=0.5, color=C_PIA), stackgroup="cat",
        fillcolor=C_PIA_LIGHT, hovertemplate="%{y:.0f}d",
    ))
    fig.add_trace(go.Scatter(
        x=esp_e["fecha"], y=esp_e["tiempo_sol_a_pia_dias"],
        name="Espanya (total)", mode="lines",
        line=dict(color=C_GRAY_500, width=2, dash="dash"),
        hovertemplate="%{y:.0f}d",
    ))
    sfig(fig, 370)
    fig.update_yaxes(title_text="Dies")
    st.plotly_chart(fig, use_container_width=True, config=PC)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
p1, p2, p3, p4, p5 = st.tabs(["IMPACTE", "VOLUM", "TERMINIS", "DIGITALITZACIÓ", "IMSERSO"])
with p1: render_p1()
with p2: render_p2()
with p3: render_p3()
with p4: render_p4()
with p5: render_p5()

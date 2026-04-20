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
    try:
        expected = st.secrets["password"]
    except (KeyError, FileNotFoundError, Exception):
        expected = "dependencia2026"
    if pwd == expected:
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
def render_p1():
    val, pia = load_volume()
    form = load_formularis()
    terminis = load_terminis()

    last = val["mes"].iloc[-1]
    # Find baseline index
    bl_candidates = val[val["mes"] == BASELINE].index
    bl = bl_candidates[0] if len(bl_candidates) > 0 else 0

    st.caption(f"Últimes dades: **{fmt_ym(last)}** · Baseline: **{BASELINE_LABEL}**")

    # --- Row 1: termini KPIs (Total · Valoració · PIA) ---
    df_tot = terminis["Tots"]
    row_t = _latest_complete(df_tot)
    bl_y, bl_m = int(BASELINE[:4]), int(BASELINE[5:7])
    bl_rows_t = df_tot[(df_tot["fecha"].dt.year == bl_y) & (df_tot["fecha"].dt.month == bl_m)]
    bl_t = bl_rows_t.iloc[0] if len(bl_rows_t) else None

    v_now, p_now, t_now = _phase_totals(row_t)
    if bl_t is not None:
        v_bl, p_bl, t_bl = _phase_totals(bl_t)
        d_total = f"{t_now - t_bl:+d}d"
        d_val = f"{v_now - v_bl:+d}d"
        d_pia = f"{p_now - p_bl:+d}d"
    else:
        d_total = d_val = d_pia = "—"

    t1, t2, t3 = st.columns(3)
    t1.metric("Temps total sol·licitud → prestació", f"{t_now} dies", d_total, delta_color="inverse")
    t2.metric("Fase valoració", f"{v_now} dies", d_val, delta_color="inverse")
    t3.metric("Fase PIA", f"{p_now} dies", d_pia, delta_color="inverse")

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
    st.caption(f"Últimes dades: **{fmt_ym(val['mes'].iloc[-1])}** · Baseline: **{BASELINE_LABEL}**")

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
@st.cache_data
def load_terminis():
    keys = {"Tots": "total", "Grau I": "g1", "Grau II": "g2", "Grau III": "g3"}
    out = {}
    for label, key in keys.items():
        df = pd.read_csv(DATA / f"terminis_{key}.csv")
        df["fecha"] = pd.to_datetime(df["fecha"])
        out[label] = df
    return out


def _latest_complete(df):
    """Return the latest row with full phase data (PIA phases non-null)."""
    complete = df.dropna(subset=["pia", "capecon", "creacio_pia", "res_pia"])
    return complete.sort_values("fecha").iloc[-1]


CAT_MONTHS = ["gener", "febrer", "març", "abril", "maig", "juny",
              "juliol", "agost", "setembre", "octubre", "novembre", "desembre"]


def fmt_ym(s):
    """'2026-03' or '2026-03-31' or datetime → 'Març 2026'."""
    if hasattr(s, "year") and hasattr(s, "month"):
        y, m = s.year, s.month
    else:
        s = str(s)
        y, m = int(s[:4]), int(s[5:7])
    return f"{CAT_MONTHS[m - 1].capitalize()} {y}"


BASELINE_LABEL = fmt_ym(BASELINE)


def _phase_totals(row):
    val = int(round(row["sol_grau"] + row["tram_grau"] + row["val_grau"]))
    pia = int(round(row["capecon"] + row["creacio_pia"] + row["res_pia"]))
    return val, pia, val + pia


def render_p3():
    terminis = load_terminis()

    df_tot = terminis["Tots"]
    row_tot = _latest_complete(df_tot)

    # Baseline row (2026-01)
    bl_year, bl_month = int(BASELINE[:4]), int(BASELINE[5:7])
    bl_rows = df_tot[(df_tot["fecha"].dt.year == bl_year) & (df_tot["fecha"].dt.month == bl_month)]
    bl_row = bl_rows.iloc[0] if len(bl_rows) else None

    st.caption(f"Últimes dades: **{fmt_ym(row_tot['fecha'])}** · Baseline: **{BASELINE_LABEL}**")

    val_now, pia_now, total_now = _phase_totals(row_tot)

    if bl_row is not None:
        val_bl, pia_bl, total_bl = _phase_totals(bl_row)
        delta_total = f"{total_now - total_bl:+d}d"
        delta_val = f"{val_now - val_bl:+d}d"
        delta_pia = f"{pia_now - pia_bl:+d}d"
    else:
        delta_total = delta_val = delta_pia = "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("Termini total", f"{total_now} dies", delta_total, delta_color="inverse")
    c2.metric("Fase valoració", f"{val_now} dies", delta_val, delta_color="inverse")
    c3.metric("Fase PIA", f"{pia_now} dies", delta_pia, delta_color="inverse")

    st.markdown("")
    st.markdown("#### Circuit complet — fases (per grau)")

    phase_spec = [
        ("Sol·licitud grau", "sol_grau", "#fca5a5"),
        ("Tramitació grau", "tram_grau", "#ef4444"),
        ("Valoració grau", "val_grau", C_VAL),
        ("CAPECON", "capecon", "#93c5fd"),
        ("Creació PIA", "creacio_pia", C_PIA),
        ("Resolució PIA", "res_pia", "#1e3a5f"),
    ]

    abbrev = {
        "Sol·licitud grau": "Sol·l.",
        "Tramitació grau": "Tram.",
        "Resolució PIA": "Res.",
    }

    def bar_label(name, d, big=False):
        if d < 8:
            return ""
        threshold = 50 if big else 40
        if d >= threshold:
            return f"<b>{name}</b><br>{d}d"
        return f"<b>{abbrev.get(name, name)}</b><br>{d}d"

    def grau_bar(row, height, big=False, grau_label=None):
        fig = go.Figure()
        tot = 0
        for phase_name, col, color in phase_spec:
            d = int(round(row[col]))
            tot += d
            fig.add_trace(go.Bar(
                x=[d], y=[""], orientation="h", name=phase_name,
                marker_color=color, marker_line_width=0,
                text=bar_label(phase_name, d, big=big),
                textposition="inside", insidetextanchor="middle",
                textfont=dict(size=14 if big else 11, color="white"),
                textangle=0, constraintext="inside",
                hovertemplate=f"<b>{phase_name}</b><br>{d} dies<extra></extra>",
                showlegend=False,
            ))
        fig.add_annotation(
            x=tot, y=0, text=f"  <b>{tot}d</b>",
            showarrow=False, xanchor="left",
            font=dict(size=16 if big else 13, color=C_BLACK),
        )
        if grau_label:
            fig.add_annotation(
                x=0, xref="paper", y=0, yref="y",
                text=f"<b>{grau_label}</b>",
                showarrow=False, xanchor="right",
                font=dict(size=12, color=C_BLACK),
                xshift=-8,
            )
        sfig(fig, height)
        fig.update_layout(
            barmode="stack",
            margin=dict(l=60, r=90, t=5 if big else 0, b=25 if big else 0),
            yaxis=dict(visible=False),
            xaxis=dict(
                title_text="Dies" if big else None,
                tickfont=dict(size=12 if big else 10),
                showticklabels=big,
            ),
            hovermode="closest",
            bargap=0.4,
        )
        return fig

    # Tots — big, full width
    st.plotly_chart(
        grau_bar(row_tot, height=200, big=True, grau_label="Tots"),
        use_container_width=True, config=PC,
    )

    # Grau I / II / III in a single figure with independent x-axes
    labels = ["Grau I", "Grau II", "Grau III"]
    rows_by_grau = {g: _latest_complete(terminis[g]) for g in labels}

    fig_g = make_subplots(
        rows=3, cols=1, shared_xaxes=False,
        vertical_spacing=0.02,
    )
    for row_idx, label in enumerate(labels, start=1):
        r = rows_by_grau[label]
        tot = 0
        for phase_name, col, color in phase_spec:
            d = int(round(r[col]))
            tot += d
            fig_g.add_trace(go.Bar(
                x=[d], y=[""], orientation="h", name=phase_name,
                marker_color=color, marker_line_width=0,
                text=bar_label(phase_name, d),
                textposition="inside", insidetextanchor="middle",
                textfont=dict(size=11, color="white"),
                textangle=0, constraintext="inside",
                hovertemplate=f"<b>{label} — {phase_name}</b><br>{d} dies<extra></extra>",
                showlegend=False,
            ), row=row_idx, col=1)
        # Total annotation on the right
        fig_g.add_annotation(
            xref=f"x{row_idx if row_idx > 1 else ''}", yref=f"y{row_idx if row_idx > 1 else ''}",
            x=tot, y=0, text=f"  <b>{tot}d</b>",
            showarrow=False, xanchor="left",
            font=dict(size=13, color=C_BLACK),
        )
        # Grau label on the left
        fig_g.add_annotation(
            xref="paper", yref=f"y{row_idx if row_idx > 1 else ''}",
            x=0, y=0, text=f"<b>{label}</b>",
            showarrow=False, xanchor="right", xshift=-8,
            font=dict(size=12, color=C_BLACK),
        )

    fig_g.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, showline=False, visible=False)
    fig_g.update_yaxes(visible=False)
    sfig(fig_g, 200)
    fig_g.update_layout(
        barmode="stack",
        margin=dict(l=60, r=90, t=0, b=0),
        bargap=0.4,
        hovermode="closest",
    )
    st.plotly_chart(fig_g, use_container_width=True, config=PC)

    st.markdown("")
    st.markdown("#### Metodologia")
    st.markdown(
        "- **Univers:** procediments tancats aquell mes · "
        "**Indicador:** mitjana, excloent el 10% més lent (P90) · "
        "**Filtre:** només inicials (sense revisions ni reclamacions) · "
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

    st.caption(f"Últimes dades: **{fmt_ym(last_date)}** · Font: **IMSERSO**")
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

    # --- Chart 2: Evolution (two panels) ---
    st.markdown("#### Evolució temporal")

    cat_e = temps[temps["ccaa"] == "Cataluña"].sort_values("fecha")
    esp_e = temps[temps["ccaa"] == "TOTAL"].sort_values("fecha")

    col_ev_a, col_ev_b = st.columns(2)

    # Left: Total time Catalunya vs Espanya
    with col_ev_a:
        st.caption("**Com estem** — Temps total sol·licitud → PIA")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cat_e["fecha"], y=cat_e["tiempo_sol_a_pia_dias"],
            name="Catalunya", mode="lines",
            line=dict(color=C_BLACK, width=2.5),
            hovertemplate="%{y:.0f}d",
        ))
        fig.add_trace(go.Scatter(
            x=esp_e["fecha"], y=esp_e["tiempo_sol_a_pia_dias"],
            name="Espanya (mitjana)", mode="lines",
            line=dict(color=C_GRAY_500, width=2, dash="dash"),
            hovertemplate="%{y:.0f}d",
        ))
        sfig(fig, 340)
        fig.update_yaxes(title_text="Dies")
        st.plotly_chart(fig, use_container_width=True, config=PC)

    # Right: Catalunya decomposition
    with col_ev_b:
        st.caption("**On és el coll d'ampolla** — Catalunya per fase")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cat_e["fecha"], y=cat_e["tiempo_sol_a_grado_dias"],
            name="Sol → Grau", mode="lines",
            line=dict(color=C_VAL, width=2.5),
            hovertemplate="%{y:.0f}d",
        ))
        fig.add_trace(go.Scatter(
            x=cat_e["fecha"], y=cat_e["tiempo_grado_a_pia_dias"],
            name="Grau → PIA", mode="lines",
            line=dict(color=C_PIA, width=2.5),
            hovertemplate="%{y:.0f}d",
        ))
        sfig(fig, 340)
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

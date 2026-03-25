"""
cptu_svg_animator.py  — v2 CSS-only
====================================
Génère une animation SVG scientifique à partir de données CPTU réelles.
CSS @keyframes UNIQUEMENT (zéro SMIL <animate>) :
  → Compatible Android, iOS Safari, Chrome, Firefox, Edge, WhatsApp.

4 panneaux animés :
  1. Colonne de sol colorée (Robertson 1990)
  2. Profil qc (MPa) — tracé animé
  3. Profil fs (kPa) — tracé animé
  4. Classification Robertson Ic

Fournit aussi generate_cptu_png() pour incorporation dans les rapports PDF.

Palette : BG=#16140e  ORANGE_D=#C1550F  ORANGE_M=#DA701C  ORANGE_L=#F59B3A  CREAM=#F0E1C3
"""

import io
import math
import numpy as np
import pandas as pd
from typing import Optional

# ─── Palette ──────────────────────────────────────────────────────────────────
BG       = "#16140e"
ORANGE_D = "#C1550F"
ORANGE_M = "#DA701C"
ORANGE_L = "#F59B3A"
CREAM    = "#F0E1C3"
GRID     = "#2a2018"
TEXT_DIM = "#a07840"

# Couleurs Robertson Ic par zone (1 → 8)
IC_COLORS = {
    1: "#8B4513",  # Graviers / sables très denses
    2: "#CD853F",  # Sables
    3: "#DAA520",  # Sables silteux
    4: "#6B8E23",  # Silts sableux
    5: "#556B2F",  # Argiles silteuses
    6: "#3CB371",  # Argiles
    7: "#2E8B57",  # Argiles organiques
    8: "#8FBC8F",  # Tourbes
}
IC_LABELS = {
    1: "Gravier / Sable dense",
    2: "Sable",
    3: "Sable silteux",
    4: "Silt sableux",
    5: "Silt argileux",
    6: "Argile",
    7: "Argile organique",
    8: "Tourbe / Sol organique",
}


# ─── Classification Robertson Ic ──────────────────────────────────────────────
def _robertson_zone(qc: float, fs: float) -> int:
    """Retourne la zone Robertson (1-8) à partir de qc (MPa) et fs (kPa)."""
    if qc <= 0:
        return 6
    fr = (fs / (qc * 1000)) * 100
    try:
        ic = math.sqrt(
            (3.47 - math.log10(max(qc, 0.01))) ** 2 +
            (math.log10(max(fr, 0.001)) + 1.22) ** 2
        )
    except Exception:
        ic = 3.0
    if ic < 1.31:   return 1
    if ic < 2.05:   return 2
    if ic < 2.60:   return 3
    if ic < 2.95:   return 4
    if ic < 3.60:   return 5
    if ic < 4.00:   return 6
    if ic < 4.50:   return 7
    return 8


def _detect_layers(df: pd.DataFrame) -> list:
    """
    Détecte les couches homogènes par glissement de zone Robertson.
    Retourne une liste de dicts : {start_m, end_m, zone, color, label, avg_qc, avg_fs}
    """
    depth_col = _depth_col(df)
    depths = df[depth_col].values
    qcs    = df["qc"].values
    fss    = df["fs"].values

    factor = 0.01 if depths.max() > 50 else 1.0
    zones  = [_robertson_zone(float(q), float(f)) for q, f in zip(qcs, fss)]

    layers        = []
    current_zone  = zones[0]
    start_idx     = 0

    def _flush(si, ei):
        d_start = float(depths[si]) * factor
        d_end   = float(depths[ei]) * factor
        z       = zones[si]
        layers.append({
            "start_m": round(d_start, 2),
            "end_m":   round(d_end,   2),
            "zone":    z,
            "color":   IC_COLORS.get(z, "#888888"),
            "label":   IC_LABELS.get(z, "Inconnu"),
            "avg_qc":  round(float(np.mean(qcs[si:ei + 1])), 2),
            "avg_fs":  round(float(np.mean(fss[si:ei + 1])), 2),
        })

    for i in range(1, len(zones)):
        if zones[i] != current_zone:
            _flush(start_idx, i - 1)
            current_zone = zones[i]
            start_idx    = i
    _flush(start_idx, len(zones) - 1)

    # Fusionner couches trop minces (< 0.3 m)
    merged = []
    for la in layers:
        if merged and la["end_m"] - la["start_m"] < 0.3 and la["zone"] == merged[-1]["zone"]:
            merged[-1]["end_m"] = la["end_m"]
        else:
            merged.append(la)
    return merged


def _depth_col(df: pd.DataFrame) -> str:
    for c in ["Depth", "depth", "Profondeur", "profondeur", "z"]:
        if c in df.columns:
            return c
    return df.columns[0]


def _pline(xs, ys):
    return " ".join(f"{x},{y:.1f}" for x, y in zip(xs, ys))


def _path_length(xs, ys):
    return sum(
        math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i])
        for i in range(len(xs) - 1)
    ) + 60


# ═══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATION SVG  (CSS animations — aucun SMIL)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_cptu_animation(
    df: pd.DataFrame,
    title: str = "CPTU SETRAF ANALYSE",
    width:  int = 1100,
    height: int = 640,
) -> str:
    """
    Retourne une chaîne SVG animée via CSS @keyframes (cross-platform).
    Compatible : Android, iOS, WhatsApp, Chrome, Firefox, Edge, Samsung Internet.
    """
    depth_col  = _depth_col(df)
    depths_raw = df[depth_col].values.astype(float)
    qcs        = df["qc"].values.astype(float)
    fss        = df["fs"].values.astype(float)

    # Normalise profondeur en mètres
    depths_m  = depths_raw * 0.01 if depths_raw.max() > 50 else depths_raw.copy()
    depth_max = float(depths_m.max()) or 1.0
    qc_max    = float(qcs.max()) or 1.0
    fs_max    = float(fss.max()) or 1.0

    # Ic Robertson par point
    ics = []
    for q, f in zip(qcs, fss):
        fr = (f / (q * 1000)) * 100 if q > 0 else 1.0
        try:
            ic = math.sqrt(
                (3.47 - math.log10(max(q, 0.01))) ** 2 +
                (math.log10(max(fr, 0.001)) + 1.22) ** 2
            )
        except Exception:
            ic = 3.0
        ics.append(min(ic, 6.0))
    ics = np.array(ics)

    layers = _detect_layers(df)
    n      = len(depths_m)

    # ── Layout ────────────────────────────────────────────────────────────────
    PAD_TOP  = 82
    PAD_BOT  = 44
    PAD_LEFT = 32     # pour les labels de profondeur
    CHART_H  = height - PAD_TOP - PAD_BOT
    PANEL_W  = (width - PAD_LEFT - 20) // 4 - 8
    GAP      = 10

    p1x       = PAD_LEFT
    p2x       = p1x + PANEL_W + GAP
    p3x       = p2x + PANEL_W + GAP
    p4x       = p3x + PANEL_W + GAP
    panel_top = PAD_TOP
    panel_bot = PAD_TOP + CHART_H

    def d2y(d):      return panel_top + (d / depth_max) * CHART_H
    def qc2x(q):     return int((q / qc_max) * PANEL_W)
    def fs2x(f):     return int((f / fs_max) * PANEL_W)
    def ic2x(ic):    return int(min(ic / 5.5, 1.0) * PANEL_W)

    ANIM_S = 5  # durée totale animation

    # ── Coordonnées polylignes ─────────────────────────────────────────────────
    qc_xs = [p2x + qc2x(q) for q in qcs]
    fs_xs = [p3x + fs2x(f) for f in fss]
    ys    = [d2y(d) for d in depths_m]

    len_qc = int(_path_length(qc_xs, ys))
    len_fs = int(_path_length(fs_xs, ys))

    # Cone
    cone_x      = p1x + PANEL_W // 2
    cone_y_from = panel_top - 12
    cone_y_to   = int(panel_bot) - 12

    # ── CSS ────────────────────────────────────────────────────────────────────
    css = f"""
    @keyframes solidFade {{ from {{ opacity:0; }} to {{ opacity:0.85; }} }}
    @keyframes textFade  {{ from {{ opacity:0; }} to {{ opacity:1.0;  }} }}
    @keyframes icFade    {{ from {{ opacity:0; }} to {{ opacity:0.82; }} }}
    @keyframes drawQc    {{ to   {{ stroke-dashoffset:0; }} }}
    @keyframes drawFs    {{ to   {{ stroke-dashoffset:0; }} }}
    @keyframes coneDrop  {{
      0%   {{ transform: translate({cone_x}px, {cone_y_from}px); }}
      100% {{ transform: translate({cone_x}px, {cone_y_to}px); }}
    }}
    .sl  {{ opacity:0;   animation: solidFade 0.45s forwards; }}
    .lt  {{ opacity:0;   animation: textFade  0.35s forwards; }}
    .ld  {{ opacity:0.7; }}
    .ic  {{ opacity:0;   animation: icFade    0.06s forwards; }}
    .qcl {{
      stroke-dasharray: {len_qc} {len_qc};
      stroke-dashoffset: {len_qc};
      animation: drawQc {ANIM_S}s linear 0.15s forwards;
    }}
    .fsl {{
      stroke-dasharray: {len_fs} {len_fs};
      stroke-dashoffset: {len_fs};
      animation: drawFs {ANIM_S}s linear 0.5s forwards;
    }}
    .cone-grp {{
      animation: coneDrop {ANIM_S}s ease-in 0s forwards;
    }}
    """

    # ── Defs ───────────────────────────────────────────────────────────────────
    defs = f"""
  <linearGradient id="rodgrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="{ORANGE_D}"/>
    <stop offset="100%" stop-color="{ORANGE_L}"/>
  </linearGradient>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="2.5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="cp1"><rect x="{p1x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}"/></clipPath>
  <clipPath id="cp2"><rect x="{p2x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}"/></clipPath>
  <clipPath id="cp3"><rect x="{p3x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}"/></clipPath>
  <clipPath id="cp4"><rect x="{p4x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}"/></clipPath>
"""

    # ── Axe profondeur ─────────────────────────────────────────────────────────
    depth_axis = ""
    n_ticks = min(10, int(depth_max) + 1)
    for k in range(n_ticks + 1):
        dm = k * (depth_max / n_ticks)
        y  = int(d2y(dm))
        depth_axis += (
            f'<line x1="{p1x}" y1="{y}" x2="{p4x + PANEL_W}" y2="{y}" '
            f'stroke="{GRID}" stroke-width="0.5" opacity="0.4"/>\n'
            f'<text x="{p1x - 4}" y="{y + 4}" text-anchor="end" '
            f'font-size="9" fill="{TEXT_DIM}">{dm:.1f}m</text>\n'
        )

    # ── Titres panneaux ────────────────────────────────────────────────────────
    panel_titles = (
        f'<text x="{p1x + PANEL_W // 2}" y="{panel_top - 9}" text-anchor="middle" '
        f'font-size="11" font-weight="bold" fill="{ORANGE_L}">Sol (Robertson)</text>\n'
        f'<text x="{p2x + PANEL_W // 2}" y="{panel_top - 9}" text-anchor="middle" '
        f'font-size="11" font-weight="bold" fill="{ORANGE_L}">qc (MPa)</text>\n'
        f'<text x="{p3x + PANEL_W // 2}" y="{panel_top - 9}" text-anchor="middle" '
        f'font-size="11" font-weight="bold" fill="#4ab8d8">fs (kPa)</text>\n'
        f'<text x="{p4x + PANEL_W // 2}" y="{panel_top - 9}" text-anchor="middle" '
        f'font-size="11" font-weight="bold" fill="#aaccaa">Ic Robertson</text>\n'
    )

    # ── PANNEAU 1 : Colonne sol ────────────────────────────────────────────────
    soil_parts = ""
    for i, la in enumerate(layers):
        y1    = d2y(la["start_m"])
        y2    = d2y(la["end_m"])
        h     = max(y2 - y1, 2)
        delay = i * 0.22
        soil_parts += (
            f'<rect class="sl" clip-path="url(#cp1)" '
            f'x="{p1x}" y="{y1:.1f}" width="{PANEL_W}" height="{h:.1f}" '
            f'fill="{la["color"]}" style="animation-delay:{delay:.2f}s"/>\n'
            f'<line x1="{p1x}" y1="{y2:.1f}" x2="{p1x + PANEL_W}" y2="{y2:.1f}" '
            f'stroke="#16140e" stroke-width="1.5" opacity="0.6"/>\n'
        )
        if h >= 14:
            mid_y = (y1 + y2) / 2
            lbl   = la["label"][:22]
            soil_parts += (
                f'<text class="lt" clip-path="url(#cp1)" '
                f'x="{p1x + 4}" y="{mid_y + 4:.1f}" font-size="9" fill="{CREAM}" '
                f'style="animation-delay:{delay + 0.3:.2f}s">{lbl}</text>\n'
                f'<text class="ld" clip-path="url(#cp1)" '
                f'x="{p1x + 4}" y="{mid_y + 14:.1f}" font-size="7.5" fill="{TEXT_DIM}">'
                f'qc={la["avg_qc"]} MPa</text>\n'
            )

    # ── PANNEAU 2 : qc profile ─────────────────────────────────────────────────
    pts2      = _pline(qc_xs, ys)
    fill_pts2 = (f"{p2x},{panel_bot} "
                 + " ".join(f"{x},{y:.1f}" for x, y in zip(qc_xs, ys))
                 + f" {qc_xs[-1]},{panel_bot}")
    qc_grid   = ""
    for k in range(1, 6):
        gx = p2x + int(k / 5 * PANEL_W)
        qv = round(k / 5 * qc_max, 1)
        qc_grid += (
            f'<line x1="{gx}" y1="{panel_top}" x2="{gx}" y2="{panel_bot}" '
            f'stroke="{GRID}" stroke-width="0.7"/>\n'
            f'<text x="{gx}" y="{panel_bot + 13}" text-anchor="middle" '
            f'font-size="8" fill="{TEXT_DIM}">{qv}</text>\n'
        )

    # ── PANNEAU 3 : fs profile ─────────────────────────────────────────────────
    pts3      = _pline(fs_xs, ys)
    fill_pts3 = (f"{p3x},{panel_bot} "
                 + " ".join(f"{x},{y:.1f}" for x, y in zip(fs_xs, ys))
                 + f" {fs_xs[-1]},{panel_bot}")
    fs_grid   = ""
    for k in range(1, 6):
        gx = p3x + int(k / 5 * PANEL_W)
        fv = int(k / 5 * fs_max)
        fs_grid += (
            f'<line x1="{gx}" y1="{panel_top}" x2="{gx}" y2="{panel_bot}" '
            f'stroke="{GRID}" stroke-width="0.7"/>\n'
            f'<text x="{gx}" y="{panel_bot + 13}" text-anchor="middle" '
            f'font-size="8" fill="{TEXT_DIM}">{fv}</text>\n'
        )

    # ── PANNEAU 4 : Robertson Ic ───────────────────────────────────────────────
    pt_h     = max(CHART_H / n, 1.5)
    ic_parts = ""
    for i, (ic, y_dep) in enumerate(zip(ics, ys)):
        zone  = _robertson_zone(float(qcs[i]), float(fss[i]))
        col   = IC_COLORS.get(zone, "#888")
        bar_w = ic2x(ic)
        delay = 0.7 + (i / n) * (ANIM_S - 1.0)
        ic_parts += (
            f'<rect class="ic" clip-path="url(#cp4)" '
            f'x="{p4x}" y="{y_dep:.1f}" width="{bar_w}" height="{pt_h:.1f}" '
            f'fill="{col}" style="animation-delay:{delay:.3f}s"/>\n'
        )

    ic_205_x = p4x + ic2x(2.05)
    ic_260_x = p4x + ic2x(2.60)
    ic_360_x = p4x + ic2x(3.60)
    ic_lines = (
        f'<line x1="{ic_205_x}" y1="{panel_top}" x2="{ic_205_x}" y2="{panel_bot}" '
        f'stroke="#DAA520" stroke-width="1" stroke-dasharray="4,3" opacity="0.7"/>\n'
        f'<text x="{ic_205_x + 2}" y="{panel_top + 10}" font-size="8" fill="#DAA520">2.05</text>\n'
        f'<line x1="{ic_260_x}" y1="{panel_top}" x2="{ic_260_x}" y2="{panel_bot}" '
        f'stroke="#6B8E23" stroke-width="1" stroke-dasharray="4,3" opacity="0.7"/>\n'
        f'<text x="{ic_260_x + 2}" y="{panel_top + 10}" font-size="8" fill="#6B8E23">2.60</text>\n'
        f'<line x1="{ic_360_x}" y1="{panel_top}" x2="{ic_360_x}" y2="{panel_bot}" '
        f'stroke="#3CB371" stroke-width="1" stroke-dasharray="4,3" opacity="0.7"/>\n'
        f'<text x="{ic_360_x + 2}" y="{panel_top + 10}" font-size="8" fill="#3CB371">3.60</text>\n'
    )

    # ── Légende zones ──────────────────────────────────────────────────────────
    legend_y     = panel_bot + 20
    present_zones = sorted({la["zone"] for la in layers})
    legend_parts  = ""
    lx            = p1x
    for z in present_zones[:6]:
        col = IC_COLORS.get(z, "#888")
        lbl = IC_LABELS.get(z, "")[:18]
        legend_parts += (
            f'<rect x="{lx}" y="{legend_y}" width="10" height="10" fill="{col}"/>\n'
            f'<text x="{lx + 13}" y="{legend_y + 9}" font-size="8" fill="{CREAM}">{lbl}</text>\n'
        )
        lx += 105

    # ── Sonde CPT animée (CSS transform) ──────────────────────────────────────
    cone_svg = (
        f'<g class="cone-grp">\n'
        f'  <line x1="0" y1="0" x2="0" y2="-18" stroke="url(#rodgrad)" stroke-width="4"/>\n'
        f'  <polygon points="-7,0 7,0 0,14" fill="{ORANGE_D}" filter="url(#glow)"/>\n'
        f'</g>\n'
    )

    stats_txt = (
        f"qc max={qc_max:.1f} MPa  |  fs max={int(fs_max)} kPa  |  "
        f"Prof. max={depth_max:.1f} m  |  {n} points  |  {len(layers)} couches"
    )

    # ── Assemblage final ───────────────────────────────────────────────────────
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {width} {height}"
     width="{width}" height="{height}"
     preserveAspectRatio="xMidYMid meet"
     style="background:{BG};font-family:Arial,sans-serif;">
<defs>{defs}</defs>
<style>{css}</style>

<!-- Fond -->
<rect width="{width}" height="{height}" fill="{BG}"/>

<!-- Séparateurs panneaux -->
<g stroke="{GRID}" stroke-width="1" opacity="0.6">
  <line x1="{p2x - 5}" y1="{panel_top - 22}" x2="{p2x - 5}" y2="{panel_bot + 30}"/>
  <line x1="{p3x - 5}" y1="{panel_top - 22}" x2="{p3x - 5}" y2="{panel_bot + 30}"/>
  <line x1="{p4x - 5}" y1="{panel_top - 22}" x2="{p4x - 5}" y2="{panel_bot + 30}"/>
</g>

<!-- Titre -->
<text x="{width // 2}" y="28" text-anchor="middle"
  font-size="20" font-weight="900" fill="{ORANGE_L}" letter-spacing="3">{title}</text>
<text x="{width // 2}" y="46" text-anchor="middle"
  font-size="10" fill="{TEXT_DIM}" letter-spacing="2">ANALYSE GÉOTECHNIQUE — DONNÉES RÉELLES</text>
<rect x="80" y="52" width="{width - 160}" height="1.5" rx="1"
  fill="{ORANGE_M}" opacity="0.5"/>

<!-- Titres panneaux -->
{panel_titles}

<!-- Axe profondeur -->
{depth_axis}

<!-- Fonds panneaux -->
<rect x="{p1x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}" fill="#1a1208" rx="2"/>
<rect x="{p2x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}" fill="#1a1208" rx="2"/>
<rect x="{p3x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}" fill="#1a1208" rx="2"/>
<rect x="{p4x}" y="{panel_top}" width="{PANEL_W}" height="{CHART_H}" fill="#1a1208" rx="2"/>

<!-- PANNEAU 1 : Sol Robertson -->
{soil_parts}

<!-- PANNEAU 2 : qc -->
{qc_grid}
<polygon points="{fill_pts2}" fill="{ORANGE_D}" opacity="0.14" clip-path="url(#cp2)"/>
<polyline class="qcl" points="{pts2}" fill="none"
  stroke="{ORANGE_L}" stroke-width="2" clip-path="url(#cp2)"/>

<!-- PANNEAU 3 : fs -->
{fs_grid}
<polygon points="{fill_pts3}" fill="#4ab8d8" opacity="0.12" clip-path="url(#cp3)"/>
<polyline class="fsl" points="{pts3}" fill="none"
  stroke="#4ab8d8" stroke-width="2" clip-path="url(#cp3)"/>

<!-- PANNEAU 4 : Ic Robertson -->
{ic_parts}
{ic_lines}

<!-- Sonde CPT (CSS animée) -->
{cone_svg}

<!-- Légende -->
{legend_parts}

<!-- Statistiques -->
<text x="{p1x}" y="{height - 8}" font-size="8" fill="{TEXT_DIM}">{stats_txt}</text>
<text x="{width - 8}" y="{height - 8}" text-anchor="end"
  font-size="8" fill="{TEXT_DIM}">SETRAF CPT Analysis Studio © 2026</text>

</svg>"""

    return svg


# ═══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATION PNG STATIQUE  (pour PDF via matplotlib)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_cptu_png(
    df: pd.DataFrame,
    title: str = "CPTU SETRAF",
    figsize: tuple = (14, 8),
) -> bytes:
    """
    Génère une image PNG statique (4 panneaux) via matplotlib.
    Retourne les bytes PNG — à incorporer directement dans un PDF avec reportlab.
    Retourne b"" si matplotlib est absent.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.gridspec import GridSpec
    except ImportError:
        return b""

    depth_col  = _depth_col(df)
    depths_raw = df[depth_col].values.astype(float)
    qcs        = df["qc"].values.astype(float)
    fss        = df["fs"].values.astype(float)

    depths_m  = depths_raw * 0.01 if depths_raw.max() > 50 else depths_raw.copy()
    layers    = _detect_layers(df)

    ics = []
    zone_colors_list = []
    for q, f in zip(qcs, fss):
        fr = (f / (q * 1000)) * 100 if q > 0 else 1.0
        try:
            ic = math.sqrt(
                (3.47 - math.log10(max(q, 0.01))) ** 2 +
                (math.log10(max(fr, 0.001)) + 1.22) ** 2
            )
        except Exception:
            ic = 3.0
        ics.append(min(ic, 6.0))
        zone_colors_list.append(IC_COLORS.get(_robertson_zone(float(q), float(f)), "#888"))
    ics = np.array(ics)

    fig = plt.figure(figsize=figsize, facecolor="#16140e")
    fig.suptitle(title, color="#F59B3A", fontsize=15, fontweight="bold", y=0.98)

    gs  = GridSpec(1, 4, figure=fig, wspace=0.04,
                   left=0.07, right=0.99, top=0.91, bottom=0.09)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharey=ax1)
    ax3 = fig.add_subplot(gs[2], sharey=ax1)
    ax4 = fig.add_subplot(gs[3], sharey=ax1)

    _dark_ax = "#16140e"
    _panel   = "#1a1208"

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_facecolor(_panel)
        ax.tick_params(colors="#a07840", labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#2a2018")
        ax.invert_yaxis()

    # Panel 1 — colonnes sol
    ax1.set_xlim(0, 1)
    ax1.set_xticks([])
    for la in layers:
        h = la["end_m"] - la["start_m"]
        ax1.barh(la["start_m"] + h / 2, 1.0, height=h, left=0,
                 color=la["color"], alpha=0.85, linewidth=0)
        if h > depths_m.max() * 0.04:
            ax1.text(0.03, la["start_m"] + h / 2, la["label"][:18],
                     va="center", ha="left", fontsize=6, color="#F0E1C3")
    ax1.set_title("Sol Robertson", color="#F59B3A", fontsize=9, fontweight="bold")
    ax1.set_ylabel("Profondeur (m)", color="#a07840", fontsize=8)
    ax1.yaxis.set_tick_params(labelcolor="#a07840")

    # Panel 2 — qc
    ax2.plot(qcs, depths_m, color="#F59B3A", linewidth=1.5)
    ax2.fill_betweenx(depths_m, 0, qcs, color="#C1550F", alpha=0.15)
    ax2.set_title("qc (MPa)", color="#F59B3A", fontsize=9, fontweight="bold")
    ax2.set_xlabel("MPa", color="#a07840", fontsize=7)
    ax2.tick_params(labelleft=False)
    ax2.set_xlim(left=0)
    ax2.xaxis.set_tick_params(labelcolor="#a07840")

    # Panel 3 — fs
    ax3.plot(fss, depths_m, color="#4ab8d8", linewidth=1.5)
    ax3.fill_betweenx(depths_m, 0, fss, color="#4ab8d8", alpha=0.12)
    ax3.set_title("fs (kPa)", color="#4ab8d8", fontsize=9, fontweight="bold")
    ax3.set_xlabel("kPa", color="#a07840", fontsize=7)
    ax3.tick_params(labelleft=False)
    ax3.set_xlim(left=0)
    ax3.xaxis.set_tick_params(labelcolor="#a07840")

    # Panel 4 — Ic Robertson
    pt_h = depths_m[1] - depths_m[0] if len(depths_m) > 1 else 0.5
    for ic, d, col in zip(ics, depths_m, zone_colors_list):
        ax4.barh(d, ic, height=pt_h * 0.9, left=0,
                 color=col, alpha=0.82, linewidth=0)
    ax4.axvline(2.05, color="#DAA520", linewidth=0.8, linestyle="--", alpha=0.7)
    ax4.axvline(2.60, color="#6B8E23", linewidth=0.8, linestyle="--", alpha=0.7)
    ax4.axvline(3.60, color="#3CB371", linewidth=0.8, linestyle="--", alpha=0.7)
    ax4.set_title("Ic Robertson", color="#aaccaa", fontsize=9, fontweight="bold")
    ax4.set_xlabel("Ic", color="#a07840", fontsize=7)
    ax4.tick_params(labelleft=False)
    ax4.set_xlim(left=0)
    ax4.xaxis.set_tick_params(labelcolor="#a07840")

    # Légende zones
    present_zones = sorted({la["zone"] for la in layers})
    patches = [
        mpatches.Patch(color=IC_COLORS.get(z, "#888"),
                       label=IC_LABELS.get(z, "")[:20])
        for z in present_zones
    ]
    fig.legend(
        handles=patches, loc="lower center",
        ncol=min(len(patches), 5),
        fontsize=6.5, facecolor="#1a1208",
        labelcolor="#F0E1C3", framealpha=0.6,
        bbox_to_anchor=(0.5, 0.0),
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#16140e")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

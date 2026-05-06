"""
Barkley Canine Cognition Lab — Shared Visualization Utilities
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Barkley brand palette ──────────────────────────────────────────────────
BARKLEY_COLORS = {
    "primary":    "#1A1A2E",   # deep navy
    "accent":     "#7B61FF",   # violet
    "signal":     "#FF4F6D",   # alert red-pink
    "stable":     "#00C9A7",   # teal
    "neutral":    "#B0B3C1",   # grey
    "bg":         "#F8F9FC",   # off-white
    "breed_band": "#D0D3E8",   # soft blue-grey for breed band
}

FONT_TITLE  = {"fontsize": 14, "fontweight": "bold", "color": BARKLEY_COLORS["primary"]}
FONT_LABEL  = {"fontsize": 11, "color": BARKLEY_COLORS["primary"]}
FONT_SMALL  = {"fontsize": 9,  "color": "#6B6F82"}


def apply_barkley_style(ax, fig):
    fig.patch.set_facecolor(BARKLEY_COLORS["bg"])
    ax.set_facecolor(BARKLEY_COLORS["bg"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BARKLEY_COLORS["neutral"])
    ax.spines["bottom"].set_color(BARKLEY_COLORS["neutral"])
    ax.tick_params(colors=BARKLEY_COLORS["primary"], labelsize=9)


def add_barkley_footnote(fig, text=None):
    default = (
        "Synthetic data only. Research demonstrator — not a clinical tool. "
        "© Barkley AI 2026 · getbarkley.com"
    )
    fig.text(
        0.5, 0.01, text or default,
        ha="center", fontsize=7.5,
        color=BARKLEY_COLORS["neutral"],
        style="italic"
    )

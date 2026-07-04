"""
make_brand_figures.py — v9-branded figures for the DogGraph demo.

Generates, from the canonical seed structure (seed_synthetic.cypher):
  screenshots/doggraph_schema.png     the schema, Barkley v9 style
  screenshots/graph_render.png        Kikoo's neighborhood (honest to the seed)

Brand fonts: set BARKLEY_FONT_DIR to a folder containing
  InstrumentSerif-Regular.ttf / InstrumentSerif-Italic.ttf /
  JetBrainsMono-Regular.ttf / JetBrainsMono-Medium.ttf / InterTight-SemiBold.ttf
otherwise falls back to matplotlib defaults (layout identical, fonts generic).

Synthetic data only. Not a diagnostic tool.
"""
from __future__ import annotations

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BG, PANEL, INK = "#06070a", "#0d0f14", "#edebe4"
BLUE, PINK, TEAL, VIOLET = "#7b9fff", "#c97bff", "#3fd6bc", "#a884ff"
def ink(a): return (0.929, 0.922, 0.894, a)

FD = os.environ.get("BARKLEY_FONT_DIR", "")
def _fp(name, fallback_family="monospace"):
    p = os.path.join(FD, name)
    return FontProperties(fname=p) if FD and os.path.exists(p) else FontProperties(family=fallback_family)

SERIF   = _fp("InstrumentSerif-Regular.ttf", "serif")
SERIF_I = _fp("InstrumentSerif-Italic.ttf", "serif")
MONO    = _fp("JetBrainsMono-Regular.ttf")
MONO_M  = _fp("JetBrainsMono-Medium.ttf")
DISP    = _fp("InterTight-SemiBold.ttf", "sans-serif")


def node(ax, x, y, tag, label, accent, w=0.185, big=False):
    h = 0.11 if big else 0.095
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.012,rounding_size=0.028",
                         facecolor=PANEL, edgecolor=accent,
                         linewidth=1.6 if big else 1.1, zorder=3)
    ax.add_patch(box)
    ax.text(x, y + 0.020, tag, fontproperties=MONO_M, fontsize=7.2,
            color=accent, ha="center", va="center", zorder=4)
    ax.text(x, y - 0.020, label, fontproperties=MONO, fontsize=8.6,
            color=INK, ha="center", va="center", zorder=4)


def edge(ax, x1, y1, x2, y2, label="", rad=0.0, color=None, lx=None, ly=None):
    color = color or ink(0.30)
    ar = FancyArrowPatch((x1, y1), (x2, y2), connectionstyle=f"arc3,rad={rad}",
                         arrowstyle="-|>,head_length=5,head_width=3",
                         linewidth=1.0, color=color, zorder=2,
                         shrinkA=14, shrinkB=14)
    ax.add_patch(ar)
    if label:
        ax.text(lx if lx is not None else (x1+x2)/2,
                ly if ly is not None else (y1+y2)/2 + 0.028,
                label, fontproperties=MONO, fontsize=6.6,
                color=ink(0.45), ha="center", va="center", zorder=4)


def canvas(w=12, h=6.4):
    fig = plt.figure(figsize=(w, h), dpi=200)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); ax.set_facecolor(BG)
    return fig, ax


def chrome(fig, title, subtitle, footer_right):
    fig.text(0.045, 0.935, title, fontproperties=SERIF, fontsize=21, color=INK, va="center")
    fig.text(0.045, 0.872, subtitle, fontproperties=MONO, fontsize=8.5, color=ink(0.42), va="center")
    fig.text(0.045, 0.052, " ".join("BARKLEY AI"), fontproperties=MONO_M, fontsize=9, color=INK, va="center")
    fig.text(0.955, 0.052, footer_right, fontproperties=MONO, fontsize=7.5, color=ink(0.30),
             va="center", ha="right")


# ── Figure 1 · schema ──────────────────────────────────────────────────────
def schema():
    fig, ax = canvas()
    chrome(fig, "The DogGraph schema",
           "8 node labels · the relationships are the product",
           "synthetic data · not a diagnostic tool")

    node(ax, 0.135, 0.500, "// THE INDIVIDUAL", "Dog", BLUE, big=True)
    node(ax, 0.435, 0.760, "// ICF", "Baseline", BLUE)
    node(ax, 0.435, 0.570, "// OBSERVED", "BehaviorEvent", INK if False else "#9aa7c7")
    node(ax, 0.760, 0.570, "// RESOLUTION", "TemporalBin", "#9aa7c7")
    node(ax, 0.435, 0.360, "// CHANGE", "DriftEvent", PINK)
    node(ax, 0.760, 0.300, "// EXPLANATION", "ContextEvent", TEAL)
    node(ax, 0.435, 0.145, "// ACTION", "Route", VIOLET)
    node(ax, 0.760, 0.145, "// PLACE", "Location", "#8b8fa3")
    node(ax, 0.135, 0.180, "// SOCIAL", "Dog", "#8b8fa3")

    edge(ax, 0.135, 0.500, 0.435, 0.760, "HAS_BASELINE", rad=-0.15, lx=0.235, ly=0.700)
    edge(ax, 0.135, 0.500, 0.435, 0.570, "GENERATED", rad=-0.05, lx=0.268, ly=0.575)
    edge(ax, 0.435, 0.570, 0.760, 0.570, "FALLS_IN")
    edge(ax, 0.135, 0.500, 0.435, 0.360, "HAS_DRIFT", rad=0.05, lx=0.256, ly=0.396)
    edge(ax, 0.435, 0.360, 0.435, 0.760, "DRIFTED_FROM", rad=-0.42, lx=0.317, ly=0.833)
    edge(ax, 0.435, 0.360, 0.760, 0.300, "MODULATED_BY", rad=0.05, lx=0.592, ly=0.290)
    edge(ax, 0.135, 0.500, 0.435, 0.145, "RECOMMENDED_ROUTE {reason}", rad=0.16, lx=0.238, ly=0.176)
    edge(ax, 0.435, 0.145, 0.760, 0.145, "LOCATED_NEAR")
    edge(ax, 0.135, 0.500, 0.135, 0.180, "COMPATIBLE_WITH {score, reason}", rad=0.55, lx=0.132, ly=0.328)

    fig.savefig("screenshots/doggraph_schema.png", dpi=200, facecolor=BG)
    print("saved screenshots/doggraph_schema.png")


# ── Figure 2 · Kikoo's neighborhood (honest to seed_synthetic.cypher) ─────
def neighborhood():
    fig, ax = canvas()
    chrome(fig, "One dog's behavioral memory",
           "Kikoo · seeded graph · every edge is a fact the app can retrieve",
           "synthetic data · seed structure, verbatim")

    node(ax, 0.200, 0.480, "// DOG", "Kikoo · JRT", BLUE, big=True, w=0.20)
    node(ax, 0.470, 0.760, "// BASELINE (ICF)", "established 2024-03-01", BLUE, w=0.235)
    node(ax, 0.470, 0.470, "// DRIFT", "rate 0.62 · high", PINK, w=0.20)
    node(ax, 0.790, 0.600, "// CONTEXT", "low-activity period", TEAL, w=0.225)
    node(ax, 0.470, 0.170, "// ROUTE", "River Path · flat · int 2", VIOLET, w=0.24)
    node(ax, 0.800, 0.170, "// LOCATION", "Riverside Park", "#8b8fa3", w=0.20)
    node(ax, 0.130, 0.800, "// DOG", "Ollie · Cavalier", "#8b8fa3", w=0.195)
    node(ax, 0.130, 0.155, "// DOG", "Sable · Malinois", "#8b8fa3", w=0.20)

    edge(ax, 0.200, 0.480, 0.470, 0.760, "HAS_BASELINE", rad=-0.18, lx=0.278, ly=0.690)
    edge(ax, 0.200, 0.480, 0.470, 0.470, "HAS_DRIFT", lx=0.335, ly=0.505)
    edge(ax, 0.470, 0.470, 0.470, 0.760, "DRIFTED_FROM", rad=-0.35, lx=0.375, ly=0.622)
    edge(ax, 0.470, 0.470, 0.790, 0.600, "MODULATED_BY", rad=-0.10, lx=0.634, ly=0.578,
         color=(0.247, 0.839, 0.737, 0.55))
    edge(ax, 0.200, 0.480, 0.470, 0.170, "RECOMMENDED_ROUTE · reason attached", rad=0.18,
         lx=0.318, ly=0.262)
    edge(ax, 0.470, 0.170, 0.800, 0.170, "LOCATED_NEAR")
    edge(ax, 0.200, 0.480, 0.130, 0.800, "COMPATIBLE_WITH · 0.86", rad=-0.25, lx=0.055, ly=0.652,
         color=(0.247, 0.839, 0.737, 0.55))
    edge(ax, 0.200, 0.480, 0.130, 0.155, "COMPATIBLE_WITH · 0.34", rad=0.25, lx=0.052, ly=0.310,
         color=(0.788, 0.482, 1.0, 0.45))

    fig.text(0.790, 0.870,
             "drift explained by context —\ncalm, no alarm",
             fontproperties=SERIF_I, fontsize=11.5, color=ink(0.55), ha="center", va="center")

    fig.savefig("screenshots/graph_render.png", dpi=200, facecolor=BG)
    print("saved screenshots/graph_render.png")


if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    schema()
    neighborhood()

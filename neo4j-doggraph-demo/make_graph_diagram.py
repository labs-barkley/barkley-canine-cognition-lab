"""Render the DogGraph schema as a clean node-link diagram for the README."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Ellipse

INK = "#1f2430"; MUTED = "#5b6472"
DOG = "#2f6f7e"; SUPPORT = "#eef2f4"; ACCENT = "#d98a2b"; EDGE = "#9fb3bb"
plt.rcParams.update({"font.family": "DejaVu Sans"})

# node positions (x, y) on a 0..16 x 0..10 canvas
N = {
    "Dog":          (5.6, 5.0, DOG,     "white"),
    "Baseline":     (9.4, 5.0, SUPPORT, INK),
    "DriftEvent":   (9.4, 7.6, "#fbf0e0", INK),
    "ContextEvent": (13.2, 7.6, SUPPORT, INK),
    "BehaviorEvent":(9.4, 2.4, SUPPORT, INK),
    "TemporalBin":  (13.2, 2.4, SUPPORT, INK),
    "Route":        (2.0, 7.4, SUPPORT, INK),
    "Location":     (2.0, 9.2, SUPPORT, INK),
    "Dog ":         (2.0, 2.6, DOG,     "white"),   # a second Dog (compatibility)
}
# edges: (from, to, label, curve)
E = [
    ("Dog", "Baseline", "HAS_BASELINE", 0.0),
    ("Dog", "DriftEvent", "HAS_DRIFT", 0.0),
    ("DriftEvent", "Baseline", "DRIFTED_FROM", 0.0),
    ("DriftEvent", "ContextEvent", "MODULATED_BY", 0.0),
    ("Dog", "BehaviorEvent", "GENERATED", 0.0),
    ("BehaviorEvent", "TemporalBin", "FALLS_IN", 0.0),
    ("Dog", "Route", "RECOMMENDED_ROUTE", 0.0),
    ("Route", "Location", "LOCATED_NEAR", 0.0),
    ("Dog", "Dog ", "COMPATIBLE_WITH {score}", 0.0),
]

fig, ax = plt.subplots(figsize=(12, 7))
ax.set_xlim(0, 16); ax.set_ylim(0.5, 10.4); ax.axis("off")
ax.text(0.2, 10.0, "Barkley DogGraph — schema", fontsize=17, fontweight="bold", color=INK)
ax.text(0.2, 9.55, "behavioral intelligence as relationships  ·  synthetic data  ·  not a diagnostic tool",
        fontsize=10.5, color=MUTED)

def center(name): return N[name][0], N[name][1]

# draw edges first
for a, b, label, _ in E:
    xa, ya = center(a); xb, yb = center(b)
    ax.add_patch(FancyArrowPatch((xa, ya), (xb, yb), arrowstyle="-|>", mutation_scale=13,
                 lw=1.5, color=EDGE, shrinkA=26, shrinkB=26,
                 connectionstyle="arc3,rad=0"))
    mx, my = (xa + xb) / 2, (ya + yb) / 2
    ax.text(mx, my + 0.18, label, fontsize=8.2, color=MUTED, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.85))

# draw nodes
for name, (x, y, fill, tcolor) in N.items():
    ax.add_patch(Ellipse((x, y), 2.5, 1.15, facecolor=fill, edgecolor=DOG, lw=1.6))
    ax.text(x, y, name.strip(), ha="center", va="center", fontsize=10.5,
            color=tcolor, fontweight="bold" if fill == DOG else "normal")

fig.tight_layout()
fig.savefig("screenshots/doggraph_schema.png", dpi=150, bbox_inches="tight", facecolor="white")
print("screenshots/doggraph_schema.png written")

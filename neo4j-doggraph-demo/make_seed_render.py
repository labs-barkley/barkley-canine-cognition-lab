"""
make_seed_render.py
-------------------
Renders the seeded DogGraph (six synthetic dogs and their behavioral context)
as a single publication-quality PNG. The structure mirrors what Neo4j Browser
or Bloom shows when you run `MATCH (n) RETURN n LIMIT 50`, but laid out for
print/figure use.

Synthetic data only. No real animals. Not a diagnostic tool.

Run:
    pip install networkx matplotlib
    python3 make_seed_render.py
"""
from __future__ import annotations

import math
import matplotlib.pyplot as plt
import networkx as nx

# --------------------------------------------------------------------------- #
# Canonical seed structure (mirrors seed_synthetic.cypher)
# --------------------------------------------------------------------------- #
DOGS = [
    ("d_kikoo",  "Kikoo",  "Jack Russell"),
    ("d_juno",   "Juno",   "Border Collie"),
    ("d_pixel",  "Pixel",  "Whippet"),
    ("d_marlow", "Marlow", "Labrador"),
    ("d_sable",  "Sable",  "Belgian Malinois"),
    ("d_ollie",  "Ollie",  "Cavalier Spaniel"),
]

DRIFTS = [
    # (dog_id, drift_id, rate, severity)
    ("d_kikoo",  "drift_d_kikoo",  0.62, "high"),
    ("d_juno",   "drift_d_juno",   0.41, "moderate"),  # unexplained — no modulation
    ("d_marlow", "drift_d_marlow", 0.55, "high"),
]

CONTEXTS = [
    ("ctx_low_activity_period",    "low_activity\nperiod"),
    ("ctx_post_surgery_recovery",  "post-surgery\nrecovery"),
]

MODULATED_BY = [
    ("drift_d_kikoo",  "ctx_low_activity_period"),
    ("drift_d_marlow", "ctx_post_surgery_recovery"),
]

ROUTES = [
    ("r_river", "River Path"),
    ("r_ridge", "Ridge Loop"),
    ("r_quiet", "Quiet Lane"),
]

LOCATIONS = [
    ("loc_riverside", "Riverside Park"),
    ("loc_oakhill",   "Oak Hill Meadow"),
    ("loc_quiet",     "Quiet Lane (loc)"),
]

ROUTE_LOCATED_NEAR = [
    ("r_river", "loc_riverside"),
    ("r_ridge", "loc_oakhill"),
    ("r_quiet", "loc_quiet"),
]

RECOMMENDED = [
    ("d_kikoo",  "r_river"),
    ("d_marlow", "r_quiet"),
    ("d_sable",  "r_ridge"),
    ("d_pixel",  "r_ridge"),
]

COMPATIBLE = [
    # (a, b, score) — directional COMPATIBLE_WITH
    ("d_kikoo",  "d_ollie", 0.86),
    ("d_kikoo",  "d_sable", 0.34),
    ("d_juno",   "d_sable", 0.78),
    ("d_pixel",  "d_ollie", 0.71),
    ("d_marlow", "d_ollie", 0.69),
]

# --------------------------------------------------------------------------- #
# Build the graph
# --------------------------------------------------------------------------- #
G = nx.DiGraph()

LABELS_FOR = {}     # node_id -> short display label
LABEL_OF = {}       # node_id -> Neo4j label (for coloring)

for did, name, _breed in DOGS:
    G.add_node(did); LABELS_FOR[did] = name; LABEL_OF[did] = "Dog"
    bid = f"base_{did}"
    G.add_node(bid); LABELS_FOR[bid] = f"Baseline\n({name})"; LABEL_OF[bid] = "Baseline"
    G.add_edge(did, bid, rel="HAS_BASELINE")

for did, drift_id, rate, sev in DRIFTS:
    G.add_node(drift_id); LABELS_FOR[drift_id] = f"Drift\nrate={rate}\n({sev})"
    LABEL_OF[drift_id] = "DriftEvent"
    G.add_edge(did, drift_id, rel="HAS_DRIFT")
    G.add_edge(drift_id, f"base_{did}", rel="DRIFTED_FROM")

for cid, label in CONTEXTS:
    G.add_node(cid); LABELS_FOR[cid] = label; LABEL_OF[cid] = "ContextEvent"

for dr, ctx in MODULATED_BY:
    G.add_edge(dr, ctx, rel="MODULATED_BY")

for rid, name in ROUTES:
    G.add_node(rid); LABELS_FOR[rid] = f"Route\n{name}"; LABEL_OF[rid] = "Route"

for lid, name in LOCATIONS:
    G.add_node(lid); LABELS_FOR[lid] = name; LABEL_OF[lid] = "Location"

for r, l in ROUTE_LOCATED_NEAR:
    G.add_edge(r, l, rel="LOCATED_NEAR")

for d, r in RECOMMENDED:
    G.add_edge(d, r, rel="RECOMMENDED_ROUTE")

for a, b, score in COMPATIBLE:
    G.add_edge(a, b, rel=f"COMPATIBLE_WITH\n({score})", _compat=True)


# --------------------------------------------------------------------------- #
# Manual layout — dogs in a circle, satellites placed around each
# --------------------------------------------------------------------------- #
def polar(cx, cy, r, theta_deg):
    t = math.radians(theta_deg)
    return (cx + r * math.cos(t), cy + r * math.sin(t))


pos = {}

# Place the six dogs on a regular hexagon, Kikoo at the top.
DOG_ORDER = ["d_kikoo", "d_juno", "d_marlow", "d_sable", "d_pixel", "d_ollie"]
RING_R = 3.2
for i, did in enumerate(DOG_ORDER):
    theta = 90 - i * 60                       # start at top, rotate clockwise
    pos[did] = polar(0, 0, RING_R, theta)

# Each dog's baseline is placed *tangentially* (along the ring direction), not
# radially outward — this prevents them from leaving the figure at the poles.
TANGENT_OFFSET = 1.05
for i, did in enumerate(DOG_ORDER):
    theta_d = 90 - i * 60
    # tangent vector rotates 90° from radial; choose the direction that keeps it inside
    tx, ty = polar(0, 0, 1.0, theta_d - 90)
    pos[f"base_{did}"] = (pos[did][0] + tx * TANGENT_OFFSET,
                          pos[did][1] + ty * TANGENT_OFFSET)

# Drift events between each drifting dog and the center, slightly offset
# inward so they cluster visually near the "drift" core of the graph.
DRIFT_PLACEMENT = {
    "drift_d_kikoo":  (-0.4,  1.5),
    "drift_d_juno":   ( 1.7,  0.3),
    "drift_d_marlow": ( 1.0, -1.7),
}
for k, v in DRIFT_PLACEMENT.items():
    pos[k] = v

# Context events: top-left and bottom-right, away from the dog ring.
pos["ctx_low_activity_period"]   = (-3.6,  3.0)
pos["ctx_post_surgery_recovery"] = ( 3.6, -3.0)

# Routes: outside on the right, in a small column.
pos["r_river"] = ( 5.6,  1.8)
pos["r_ridge"] = ( 5.6,  0.0)
pos["r_quiet"] = ( 5.6, -1.8)

# Locations: even further right, paired with their routes.
pos["loc_riverside"] = ( 7.4,  1.8)
pos["loc_oakhill"]   = ( 7.4,  0.0)
pos["loc_quiet"]     = ( 7.4, -1.8)


# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
COLOR = {
    "Dog":          "#4F8EF7",
    "Baseline":     "#7BC47F",
    "DriftEvent":   "#E2554B",
    "ContextEvent": "#A26DD9",
    "Route":        "#2EBFB5",
    "Location":     "#9AA0A6",
}
KIKOO_COLOR = "#F2A93B"                # highlight Kikoo distinctly

NODE_SIZE = {
    "Dog":          2400,
    "Baseline":     1000,
    "DriftEvent":   1400,
    "ContextEvent": 1300,
    "Route":        1200,
    "Location":     900,
}


def node_color(n):
    if n == "d_kikoo":
        return KIKOO_COLOR
    return COLOR[LABEL_OF[n]]


def node_size(n):
    if n == "d_kikoo":
        return NODE_SIZE["Dog"] + 600
    return NODE_SIZE[LABEL_OF[n]]


# --------------------------------------------------------------------------- #
# Draw
# --------------------------------------------------------------------------- #
fig, ax = plt.subplots(figsize=(15, 10), dpi=180)
ax.set_axis_off()
ax.set_xlim(-5.5, 9.0)
ax.set_ylim(-5.2, 5.2)

# Background title strip
ax.text(1.75, 4.7, "Barkley DogGraph — seeded subgraph",
        ha="center", va="bottom",
        fontsize=17, fontweight="bold", color="#222")
ax.text(1.75, 4.35,
        "6 dogs · 3 drifts · 2 context events · 3 routes · 5 compatibility edges  ·  synthetic",
        ha="center", va="bottom", fontsize=10, color="#666", style="italic")

# Edges — split by type for differentiated styling
def edges_with(rel_predicate):
    return [(u, v) for u, v, d in G.edges(data=True) if rel_predicate(d.get("rel", ""))]


# Solid structural edges (baseline, drift, modulation)
structural = edges_with(lambda r: r.startswith(("HAS_BASELINE", "HAS_DRIFT", "DRIFTED_FROM", "MODULATED_BY")))
nx.draw_networkx_edges(
    G, pos, ax=ax, edgelist=structural,
    edge_color="#888", width=1.4, arrows=True, arrowsize=14,
    node_size=2400,
)

# Routes & locations (dotted-style for spatial relations)
route_edges = edges_with(lambda r: r in ("LOCATED_NEAR",))
nx.draw_networkx_edges(
    G, pos, ax=ax, edgelist=route_edges,
    edge_color="#888", style="dashed", width=1.2, arrows=True, arrowsize=12,
    node_size=2400,
)

# Recommendation edges (Dog -> Route): teal
rec_edges = edges_with(lambda r: r == "RECOMMENDED_ROUTE")
nx.draw_networkx_edges(
    G, pos, ax=ax, edgelist=rec_edges,
    edge_color="#2EBFB5", width=1.8, arrows=True, arrowsize=14,
    node_size=2400,
)

# Compatibility edges (Dog -> Dog): curved + colored by score
for u, v, d in G.edges(data=True):
    if not d.get("_compat"):
        continue
    score = float(d["rel"].split("(")[1].rstrip(")"))
    col = "#2EBE6F" if score >= 0.70 else ("#F2A93B" if score >= 0.50 else "#E2554B")
    nx.draw_networkx_edges(
        G, pos, ax=ax, edgelist=[(u, v)],
        edge_color=col, width=1.5 + score * 1.6,
        arrows=True, arrowsize=12,
        connectionstyle="arc3,rad=0.22",
        node_size=2400, alpha=0.85,
    )

# Nodes by label class (so legend is meaningful)
for lab in COLOR:
    nodes_in = [n for n in G.nodes if LABEL_OF[n] == lab]
    nx.draw_networkx_nodes(
        G, pos, ax=ax, nodelist=nodes_in,
        node_color=[node_color(n) for n in nodes_in],
        node_size=[node_size(n) for n in nodes_in],
        edgecolors="white", linewidths=1.6,
    )

# Labels
def label_color(n):
    return "white" if LABEL_OF[n] in ("Dog", "DriftEvent", "ContextEvent", "Route") else "#222"


# Two passes so we can change font weight for dogs
for n in G.nodes:
    fw = "bold" if LABEL_OF[n] == "Dog" else "normal"
    fs = 10 if LABEL_OF[n] == "Dog" else 8
    ax.text(*pos[n], LABELS_FOR[n], ha="center", va="center",
            color=label_color(n), fontsize=fs, fontweight=fw, zorder=10)

# Edge labels — only for the most semantically interesting edges
edge_labels = {}
for u, v, d in G.edges(data=True):
    rel = d.get("rel", "")
    if rel.startswith("COMPATIBLE_WITH"):
        edge_labels[(u, v)] = rel
    elif rel in ("MODULATED_BY", "RECOMMENDED_ROUTE", "HAS_DRIFT"):
        edge_labels[(u, v)] = rel

nx.draw_networkx_edge_labels(
    G, pos, ax=ax, edge_labels=edge_labels,
    font_size=7, font_color="#444",
    bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1),
)

# Legend
import matplotlib.patches as mpatches
legend_items = [
    mpatches.Patch(color=KIKOO_COLOR,        label="Dog (Kikoo)"),
    mpatches.Patch(color=COLOR["Dog"],       label="Dog"),
    mpatches.Patch(color=COLOR["Baseline"],  label="Baseline"),
    mpatches.Patch(color=COLOR["DriftEvent"],label="DriftEvent"),
    mpatches.Patch(color=COLOR["ContextEvent"], label="ContextEvent"),
    mpatches.Patch(color=COLOR["Route"],     label="Route"),
    mpatches.Patch(color=COLOR["Location"],  label="Location"),
]
ax.legend(handles=legend_items, loc="lower left", frameon=False, fontsize=9)

# Footer
ax.text(1.75, -4.95,
        "Compatibility edge color: green ≥ 0.70 (good fit) · amber 0.50–0.69 · red < 0.50 (mismatch).  "
        "Edge thickness scales with score.",
        ha="center", va="center", fontsize=8.5, color="#666", style="italic")

plt.tight_layout()
out = "screenshots/graph_render.png"
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
print(f"wrote {out}")

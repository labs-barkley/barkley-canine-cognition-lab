#!/usr/bin/env python3
"""
ask.py — tiny CLI over the DogGraph natural-language layer.

    python ask.py "Why is River Path recommended for Kikoo today?"

Needs NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD in the environment (see .env.example)
and `pip install neo4j`. Synthetic data only; not a diagnostic tool.
"""
import sys
from graph_query import answer

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python ask.py "your question about the DogGraph"')
        raise SystemExit(1)
    print(answer(" ".join(sys.argv[1:])))

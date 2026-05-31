#!/usr/bin/env python3
"""
ask.py — tiny CLI over the DogGraph natural-language layer.

Two modes
---------
Deterministic (default):
    python ask.py "Why is River Path recommended for Kikoo today?"

LLM + GraphRAG (schema-constrained, read-only validated):
    python ask.py --llm "Which dog has the highest unexplained drift?"

Needs `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` in the environment.
`--llm` additionally needs `ANTHROPIC_API_KEY`. See .env.example.

Synthetic data only; not a diagnostic tool.
"""
import sys


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print('Usage: python ask.py [--llm] "your question about the DogGraph"')
        return 1

    use_llm = False
    if args[0] == "--llm":
        use_llm = True
        args = args[1:]
        if not args:
            print('Usage: python ask.py --llm "your question about the DogGraph"')
            return 1

    question = " ".join(args)

    if use_llm:
        from graph_query_llm import answer_llm
        a = answer_llm(question, prefer_llm=True)
        print(f"[mode={a.mode}]\n")
        if a.cypher:
            print("Cypher:")
            print("  " + a.cypher.replace("\n", "\n  "))
            print()
        if a.rows:
            print(f"Rows ({len(a.rows)}):")
            for r in a.rows[:25]:
                print("  " + ", ".join(f"{k}={v}" for k, v in r.items()))
            print()
        print("Answer:")
        print(a.answer or a.note or "(no answer)")
    else:
        from graph_query import answer
        print(answer(question))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

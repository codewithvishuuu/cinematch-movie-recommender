"""CineMatch V2 benchmark runner.

Usage:
    python benchmarks/run_benchmark.py --module ml.recommender --out benchmarks/results/before.json
    python benchmarks/run_benchmark.py --module ml.recommender_v2 --out benchmarks/results/after.json

Also prints a readable text report alongside (--out .txt). Never modifies
application code or artifacts.
"""
import argparse
import importlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.common import BENCHMARK_MOVIES, run_queries  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="ml.recommender")
    ap.add_argument("--out", default="benchmarks/results/before.json")
    ap.add_argument("--movies", default=None, help="comma-separated override list")
    args = ap.parse_args()

    movies = [m.strip() for m in args.movies.split(",")] if args.movies else BENCHMARK_MOVIES

    t_cold = time.perf_counter()
    mod = importlib.import_module(args.module)
    cold_s = time.perf_counter() - t_cold

    report = {
        "module": args.module,
        "cold_load_seconds": round(cold_s, 3),
        "df_shape": list(mod.df.shape),
        "df_columns": list(mod.df.columns),
        "movies": movies,
    }
    report.update(run_queries(mod, movies))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2, default=str)

    txt_path = os.path.splitext(args.out)[0] + ".txt"
    with open(txt_path, "w") as f:
        f.write(f"Module: {report['module']}  |  cold load: {report['cold_load_seconds']}s\n")
        f.write(f"df shape: {report['df_shape']}  cols: {report['df_columns']}\n")
        f.write(f"Repeated titles across queries: {report['total_repeated_titles_across_queries']}\n\n")
        for q in report["queries"]:
            r = q["recs"]
            f.write(f"== {q['query']} -> matched: {q['matched_title']!r} "
                    f"(rows={q['resolved_row_count']}, first_row={q['resolved_first_row']}) "
                    f"| {q['elapsed_ms']}ms\n")
            f.write(f"   self_included={r['self_included']} dupes={r['duplicate_titles']} "
                    f"avg_sim={r['avg_similarity']} genre_jaccard={r['avg_genre_jaccard']} "
                    f"pct_shared_genres={r['pct_shared_genres']} unique_genres={r['diversity_unique_genres']} "
                    f"pairwise_jaccard={r['avg_pairwise_genre_jaccard_pct']}%\n")
            for i, t in enumerate(r["titles"], 1):
                f.write(f"   {i:>2}. {t}\n")
            f.write("\n")
    print(f"Wrote {args.out} and {txt_path}")


if __name__ == "__main__":
    main()
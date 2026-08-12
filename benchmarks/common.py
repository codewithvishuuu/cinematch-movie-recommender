"""Shared benchmark utilities for CineMatch V2 evaluation.

Fully standalone: must NOT import any application code, so BEFORE and AFTER
runs are measured with identical, deterministic metric code.
"""
import re
import time
from collections import Counter

# Canonical multi-word genres present in the dataset (space-joined storage
# format splits them into junk tokens when using str.split()).
MULTI_WORD_GENRES = ["Science Fiction", "TV Movie"]


def parse_genres(genres_val):
    """Deterministically parses a raw genre string into canonical genre names.

    ''/None -> []. Unknown single tokens are kept as-is (never fabricated).
    """
    if not genres_val or not isinstance(genres_val, str):
        return []
    s = genres_val.strip()
    if not s:
        return []
    for mw in MULTI_WORD_GENRES:
        s = re.sub(re.escape(mw), mw.replace(" ", "_"), s)
    out = []
    for tok in s.split():
        out.append(tok.replace("_", " "))
    return [g for g in out if g]


def genre_jaccard(a_genres, b_genres):
    """Jaccard similarity between two canonical genre sets (0..1)."""
    a = set(parse_genres(a_genres))
    b = set(parse_genres(b_genres))
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def genre_overlap_pair(a_genres, b_genres):
    """Raw count of shared canonical genres."""
    a = set(parse_genres(a_genres))
    b = set(parse_genres(b_genres))
    return len(a & b)


BENCHMARK_MOVIES = [
    "The Matrix",
    "Toy Story",
    "The Godfather",
    "Inception",
    "The Dark Knight",
    "Interstellar",
    "Avatar",
    "The Shawshank Redemption",
    "Pulp Fiction",
    "Forrest Gump",
]


def analyze_recommendations(source_title, results, lookup_titles):
    """Computes metrics for one recommendation run.

    ``lookup_titles(title)`` maps a result title to a canonical genre string.
    Returns a dict with all recorded metrics.
    """
    titles = [r["title"] for r in results]
    n = len(results)

    lower_counts = Counter(t.lower() for t in titles)
    duplicates = sorted(t for t, c in lower_counts.items() if c > 1)

    self_included = any(t.lower().strip() == (source_title or "").lower().strip() for t in titles)

    sims = [float(r.get("relevance_score") or 0.0) for r in results]
    avg_sim = sum(sims) / n if n else 0.0

    src_genres = lookup_titles(source_title)
    src_canon = set(parse_genres(src_genres))
    jaccards = []
    shared = []
    rec_genres_all = set()
    pairwise = []
    for i, r in enumerate(results):
        g = lookup_titles(r["title"])
        jaccards.append(genre_jaccard(src_genres, g))
        shared.append(genre_overlap_pair(src_genres, g))
        rec_genres_all.update(parse_genres(g))
        for j in range(i + 1, len(results)):
            pairwise.append(genre_jaccard(g, lookup_titles(results[j]["title"])))

    diversity_unique_genres = len(rec_genres_all)
    avg_pairwise_jaccard_pct = (sum(pairwise) / len(pairwise) * 100.0) if pairwise else 0.0
    shared_nontrivial = sum(1 for s in shared if s > 0) / n if n else 0.0

    return {
        "n": n,
        "titles": titles,
        "duplicate_titles": duplicates,
        "duplicate_count": len(duplicates),
        "self_included": self_included,
        "avg_similarity": round(avg_sim, 4),
        "avg_genre_jaccard": round(sum(jaccards) / n, 4) if n else 0.0,
        "pct_shared_genres": round(shared_nontrivial, 4),
        "diversity_unique_genres": diversity_unique_genres,
        "avg_pairwise_genre_jaccard_pct": round(avg_pairwise_jaccard_pct, 2),
    }


def run_queries(module, movies, n_recommendations=10):
    """Runs get_recommendations for each movie and returns per-query stats.

    ``module`` must expose: df (DataFrame), fuzzy_find_movie(title), and
    get_recommendations(title, n_recommendations=...).
    """
    df = module.df

    def lookup_titles(t):
        if df is None or df.empty:
            return ""
        m = df[df["title"].astype(str).str.lower().str.strip() == str(t).lower().strip()]
        if m.empty:
            return ""
        return m.iloc[0].get("genres", "")

    rows = []
    repeated = Counter()

    for movie in movies:
        t0 = time.perf_counter()
        recs = module.get_recommendations(movie, n_recommendations=n_recommendations)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        row = {
            "query": movie,
            "matched_title": None,
            "resolved_row_count": 0,
            "resolved_first_row": None,
        }
        try:
            matched = module.fuzzy_find_movie(movie)
            row["matched_title"] = matched
            if df is not None and not df.empty and matched:
                matches = df[df["title"].astype(str).str.lower().str.strip() == str(matched).lower().strip()]
                row["resolved_row_count"] = len(matches)
                if len(matches):
                    row["resolved_first_row"] = int(matches.index[0])
        except Exception:
            pass
        row["recs"] = analyze_recommendations(movie, recs or [], lookup_titles)
        row["elapsed_ms"] = round(elapsed_ms, 1)
        row["error"] = None if recs is not None else "None returned"
        rows.append(row)
        for t in (r["title"] for r in (recs or [])):
            repeated[t.lower()] += 1

    repeats_across_queries = {t: c for t, c in repeated.items() if c > 1}
    return {
        "movie_count": len(movies),
        "total_repeated_titles_across_queries": len(repeats_across_queries),
        "repeated_titles": repeats_across_queries,
        "queries": rows,
    }
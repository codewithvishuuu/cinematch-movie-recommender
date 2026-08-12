"""CineMatch dataset build script (Phase 3A/3B/3C).

Deterministic, reproducible pipeline that transforms the raw bundled dataset
(ml/df.pkl) into the cleaned canonical dataset + regenerated model artifacts.
It NEVER edits pickles in place; it writes a fresh set into ``--out-dir``.

Pipeline:
  1. Load raw df.pkl.
  2. Build a canonical title key (lowercase, trailing-year stripped,
     punctuation->space, whitespace collapsed).
  3. Group rows by canonical title. Within each group rank every row by a
     deterministic metadata-quality score and pick the best record.
  4. Merge the strongest available metadata across the group into the chosen
     record (never inventing new values).
  5. Rebuild the ``tags`` text column from real fields (overview + tagline +
     genres) and refit a TfidfVectorizer (ngram 1-2, english stopwords) over
     the cleaned rows -> sparse CSR matrix.
  6. Write df.pkl, indices.pkl, tfidf_matrix.pkl, tfidf.pkl and a full
     human-readable/machine-readable dataset_report.json documenting every
     merge/drop decision.

Usage:
    python scripts/build_dataset.py --input ml/df.pkl --out-dir ml_next
"""
import argparse
import json
import os
import re
import sys
import time

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.common import MULTI_WORD_GENRES  # noqa: E402


def canonical_title_key(title):
    """Deterministic canonical title key used ONLY for duplicate grouping."""
    if not isinstance(title, str):
        return ""
    s = re.sub(r"\s*\(\d{4}\)\s*$", "", title.strip().lower())
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _nonempty_len(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0
    s = str(v).strip()
    return len(s)


def _valid_rating(v):
    try:
        f = float(v)
        return not np.isnan(f) and 0.0 < f <= 10.0
    except (TypeError, ValueError):
        return False


def _valid_popularity(v):
    try:
        f = float(v)
        return not np.isnan(f) and f > 0.0
    except (TypeError, ValueError):
        return False


def _best_rating(rows):
    vals = [float(r["vote_average"]) for _, r in rows if _valid_rating(r["vote_average"])]
    return max(vals) if vals else 0.0


def _best_popularity(rows):
    vals = [float(r["popularity"]) for _, r in rows if _valid_popularity(r["popularity"])]
    return max(vals) if vals else 0.0


def _best_field(rows, col, prefer_longest=False):
    """First non-empty value in deterministic quality order."""
    for _, r in rows:
        v = r[col]
        if _nonempty_len(v) > 0:
            return v
    return ""


def quality_score(row):
    """Deterministic metadata quality ranking score (documented rule).

    +2 non-empty overview (>=10 chars)
    +2 non-empty genres
    +1 non-empty tagline
    +1 valid rating (0 < vote_average <= 10)
    +1 valid popularity (> 0)
    Tie-breaks: longer overview wins, then lower original row position.
    """
    q = 0
    q += 2 if _nonempty_len(row["overview"]) >= 10 else 0
    q += 2 if _nonempty_len(row["genres"]) > 0 else 0
    q += 1 if _nonempty_len(row["tagline"]) > 0 else 0
    q += 1 if _valid_rating(row["vote_average"]) else 0
    q += 1 if _valid_popularity(row["popularity"]) else 0
    return q


def build_tags(overview, tagline, genres):
    """Builds the TF-IDF text column from real fields only (never invented).

    Lowercased token soup of overview + tagline + genres with punctuation
    replaced by spaces; duplicate tokens removed while preserving first-seen
    order (deterministic).
    """
    raw = []
    for field in (overview, tagline, genres):
        s = str(field or "")
        if s:
            s = re.sub(r"[^\w\s]", " ", s.lower())
            s = re.sub(r"\s+", " ", s).strip()
            if s:
                raw.append(s)
    full = " ".join(raw)
    if not full.strip():
        return ""
    seen, out = set(), []
    for tok in full.split():
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return " ".join(out)


def build_dataset(raw_df):
    """Core pipeline. Returns (clean_df, report_dict)."""
    report = {
        "input_rows": len(raw_df),
        "input_distinct_titles": raw_df["title"].nunique(),
        "canonicalized_title_keys": raw_df["title"].apply(canonical_title_key),
        "groups": [],
    }
    keys = report["canonicalized_title_keys"]

    dup_keys = keys[keys.duplicated(keep=False)]
    report["rows_in_duplicate_groups"] = int(len(dup_keys))
    report["distinct_canonical_titles"] = int(keys.nunique())
    report["distinct_titles_with_multiple_rows"] = int(dup_keys.nunique())

    cleaned_rows = []
    dropped = []

    grouped = raw_df.assign(_key=keys).groupby("_key", sort=True)
    group_count = 0
    for key, grp in grouped:
        members = [(int(pos), grp.loc[pos]) for pos in grp.index]

        # deterministic rank: quality score desc, overview len desc, pos asc
        members.sort(
            key=lambda mp: (
                -quality_score(mp[1]),
                -_nonempty_len(mp[1]["overview"]),
                mp[0],
            )
        )
        win_pos, winner = members[0]
        losers = members[1:]

        # -- merge: preserve the strongest available metadata -------------
        def take(col, prefer_longest=False):
            v = winner[col]
            if _nonempty_len(v) > 0 and not (col == "vote_average" and not _valid_rating(v)):
                return v
            if col == "vote_average":
                return _best_rating(members)
            if col == "popularity":
                return _best_popularity(members)
            if prefer_longest:
                return max((_nonempty_len(r[col]), str(r[col]), r[col]) for _, r in members)[2]
            return _best_field(members, col)

        merged = {
            "title": str(winner["title"]),
            "overview": take("overview", prefer_longest=True),
            "genres": take("genres"),
            "tagline": take("tagline"),
            "vote_average": float(take("vote_average")),
            "popularity": float(take("popularity")),
        }
        merged["tags"] = build_tags(merged["overview"], merged["tagline"], merged["genres"])
        merged["_key"] = key
        cleaned_rows.append(merged)

        if losers:
            group_count += 1
            report["groups"].append({
                "canonical_title": key,
                "winner_row": win_pos,
                "winner_title": merged["title"],
                "winner_quality": quality_score(winner),
                "members": [
                    {
                        "row": pos,
                        "title": str(r["title"]),
                        "quality": quality_score(r),
                        "overview_len": _nonempty_len(r["overview"]),
                        "genres": str(r["genres"] or ""),
                        "tagline_len": _nonempty_len(r["tagline"]),
                        "vote_average": float(r["vote_average"]) if not pd.isna(r["vote_average"]) else None,
                        "popularity": float(r["popularity"]) if not pd.isna(r["popularity"]) else None,
                    }
                    for pos, r in members
                ],
                "merged_from_loser_rows": [pos for pos, _ in losers],
                "selection_rule": (
                    "Ranked by metadata quality score (overview>=10:+2, genres:+2, "
                    "tagline:+1, valid rating:+1, valid popularity:+1); tie-break by "
                    "overview length then original row position. Winner takes every "
                    "non-empty field; missing fields are filled from the highest-ranked "
                    "group member that has a value. No values are invented."
                ),
            })
            for pos, r in losers:
                dropped.append({
                    "row": pos,
                    "title": str(r["title"]),
                    "canonical_title": key,
                    "reason": (
                        f"Duplicate of canonical title '{key}'; absorbed into winner row "
                        f"{win_pos}: rating={float(r['vote_average']) if not pd.isna(r['vote_average']) else None}, "
                        f"popularity={float(r['popularity']) if not pd.isna(r['popularity']) else None}, "
                        f"genres={str(r['genres'] or '')!r}, overview_len={_nonempty_len(r['overview'])}, "
                        f"tagline_len={_nonempty_len(r['tagline'])}"
                    ),
                })

    clean_df = pd.DataFrame(cleaned_rows).drop(columns=["_key"])
    report["output_rows"] = len(clean_df)
    report["rows_dropped"] = len(dropped)
    report["duplicate_groups_resolved"] = group_count
    report["dropped_rows"] = dropped
    report["genre_multi_word_tokens"] = MULTI_WORD_GENRES
    return clean_df, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="ml/df.pkl")
    ap.add_argument("--out-dir", default="ml_next")
    args = ap.parse_args()

    t0 = time.perf_counter()
    with open(args.input, "rb") as f:
        import pickle
        raw = pickle.load(f)
    print(f"loaded {args.input}: {raw.shape} in {time.perf_counter()-t0:.1f}s")

    clean_df, report = build_dataset(raw)

    # --- Phase 3C: regenerate model artifacts ----------------------------
    vectorizer = TfidfVectorizer(
        max_features=50000,
        ngram_range=(1, 2),
        stop_words="english",
    )
    t1 = time.perf_counter()
    tfidf_matrix = vectorizer.fit_transform(clean_df["tags"].fillna(""))
    tfidf_matrix = csr_matrix(tfidf_matrix)
    print(f"tfidf fit: {tfidf_matrix.shape} in {time.perf_counter()-t1:.1f}s")

    indices = pd.Series(np.arange(len(clean_df)), index=clean_df["title"])

    os.makedirs(args.out_dir, exist_ok=True)
    import pickle

    paths = {}
    for name, obj in [
        ("df.pkl", clean_df),
        ("indices.pkl", indices),
        ("tfidf_matrix.pkl", tfidf_matrix),
        ("tfidf.pkl", vectorizer),
    ]:
        p = os.path.join(args.out_dir, name)
        with open(p, "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        paths[name] = os.path.getsize(p)

    report["artifacts_bytes"] = paths
    report["build_tool"] = {
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "sklearn": __import__("sklearn").__version__,
        "scipy": __import__("scipy").__version__,
    }
    with open(os.path.join(args.out_dir, "dataset_report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)

    print("\n=== DATASET BUILD REPORT ===")
    print(f"rows: {report['input_rows']} -> {report['output_rows']} (dropped {report['rows_dropped']})")
    print(f"distinct canonical titles: {report['distinct_canonical_titles']}")
    print(f"duplicate groups resolved: {report['duplicate_groups_resolved']}")
    for name, size in paths.items():
        print(f"  {name}: {size/1e6:.2f} MB")
    print(f"\nwritten to {args.out_dir}/")


if __name__ == "__main__":
    main()
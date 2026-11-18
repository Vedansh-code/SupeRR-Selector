"""Which pressure estimate best predicts pressure performance in UNSEEN matches?

For many random 50/50 splits of matches: compute each candidate estimate on half A, then
correlate it with the player's actual opposition-adjusted pressure value in half B
(ball-weighted, players with >= 40 pressure balls in both halves).

Candidates (per 100 / 120 balls):
  p_lg      pressure record shrunk to the league mean            (current 'value' component)
  p_shrunk  pressure record shrunk to a prior predicted by the player's own baseline
  b_shrunk  baseline (non-pressure) quality only
  blend     0.5 x p_lg + 0.5 x p_shrunk
  rating    the full Phase 5 Pressure Rating (value component = p_lg)
  rating_v2 the same rating with value component = p_shrunk

Random splits mix seasons, so they cannot judge the evidence weights. Part 2 (forward in time)
does: for several cut-off dates, rate players on matches BEFORE the cut-off with each weighting
setup, then correlate with what they did under pressure in the following 12 months - in all
matches, and in the IPL only (the competition being selected for).

Usage: .venv/Scripts/python -I src/predictive_check.py [n_splits]
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import RATING_TIERS, WEIGHTING, adjusted_per_match, player_ratings  # noqa: E402
from rating import rate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
SCALE = {"bat": 100, "bowl": 120}
MIN_P = 40
SETUPS = {
    "no weighting": None,
    "recency only": {**WEIGHTING, "comp": None, "opponent": None},
    "IPL tilt only": {**WEIGHTING, "recency_decay": None, "opponent": None},
    "opponent only": {**WEIGHTING, "recency_decay": None, "comp": None},
    "all three (in use)": WEIGHTING,
}
CUTOFFS = ["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01"]
FWD_MIN_TRAIN, FWD_MIN_TEST, FWD_MIN_TEST_IPL = 60, 30, 20
# the weights the Phase 5 rating actually uses (incl. clutch redistribution for batters)
_P5 = ROOT / "outputs" / "tables" / "phase5_info.json"
WEIGHTS = ({r: {k: v / 100 for k, v in i["weights"].items()} for r, i in json.loads(_P5.read_text()).items()}
           if _P5.exists() else
           {"bat": {"value": 0.5625, "consistency": 0.25, "clutch": 0.0, "impact": 0.1875},
            "bowl": {"value": 0.45, "consistency": 0.20, "clutch": 0.20, "impact": 0.15}})


def wcorr(x, y, w):
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    return np.average((x - mx) * (y - my), weights=w) / np.sqrt(
        np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))


def main() -> None:
    n_splits = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    b = pd.read_csv(ROOT / "outputs" / "ball_adjusted.csv.gz", low_memory=False)
    b = b[b["comp_tier"].isin(RATING_TIERS)].reset_index(drop=True)
    weights = WEIGHTS
    rng = np.random.default_rng(11)
    mids = b["match_id"].unique()
    rows = []
    for i in range(n_splits):
        half = set(rng.choice(mids, size=len(mids) // 2, replace=False))
        m = b["match_id"].isin(half)
        for role in ("bat", "bowl"):
            s = SCALE[role]
            # unweighted: random halves mix seasons, so this part compares estimators only
            ra, _ = player_ratings(b[m], role, weighting=None)
            pm_a = adjusted_per_match(b[m], role, weighting=None)
            rated, _ = rate(ra, pm_a, role, weights=weights[role], value_source="p_lg")
            rated2, _ = rate(ra, pm_a, role, weights=weights[role], value_source="p_shrunk")
            rb, _ = player_ratings(b[~m], role, weighting=None)
            a = rated.set_index("player_id")
            a["rating_v2"] = rated2.set_index("player_id")["rating"]
            a["blend"] = 0.5 * a[f"p_lg{s}"] + 0.5 * a[f"p_shrunk{s}"]
            j = a.join(rb.set_index("player_id")[["p_n", f"p_adj{s}"]].add_suffix("_B"), how="inner")
            j = j[(j["p_n"] >= MIN_P) & (j["p_n_B"] >= MIN_P)]
            y, w = j[f"p_adj{s}_B"], j["p_n_B"]
            for name, col in [("p_lg", f"p_lg{s}"), ("p_shrunk", f"p_shrunk{s}"), ("b_shrunk", f"b_shrunk{s}"),
                              ("blend", "blend"), ("rating", "rating"), ("rating_v2", "rating_v2")]:
                rows.append({"split": i, "role": role, "estimate": name, "n": len(j), "r": wcorr(j[col], y, w)})
    res = pd.DataFrame(rows)
    res.to_csv(TAB / "p6_predictive_check.csv", index=False)
    summ = res.groupby(["role", "estimate"])["r"].agg(["mean", "std"]).round(3)
    summ["share_of_splits_best"] = (res.loc[res.groupby(["split", "role"])["r"].idxmax()]
                                    .groupby(["role", "estimate"]).size() / n_splits).reindex(summ.index).fillna(0)
    txt = (f"# Predictive check: correlation of half-A estimate with half-B pressure value ({n_splits} splits, "
           f"players >= {MIN_P} pressure balls in both halves)\n\n" + summ.to_string())
    txt += "\n\n" + forward_weighting_check(b)
    (TAB / "p6_predictive_check.md").write_text(txt, encoding="utf-8")
    print(txt)


def forward_weighting_check(b: pd.DataFrame) -> str:
    """Rate on matches before each cut-off (recency measured back from the cut-off) with each
    weighting setup, and correlate the rating with opposition-adjusted pressure value in the next
    12 months: all matches, and IPL matches only."""
    dates = pd.to_datetime(b["match_date"])
    rows = []
    for cut in CUTOFFS:
        c0 = pd.Timestamp(cut)
        train, test = b[dates < c0], b[(dates >= c0) & (dates < c0 + pd.Timedelta(days=365))]
        for role in ("bat", "bowl"):
            s = SCALE[role]
            targets = {}
            for tname, tb, min_t in (("all matches", test, FWD_MIN_TEST),
                                     ("IPL only", test[test["comp_tier"].eq("IPL")], FWD_MIN_TEST_IPL)):
                rt, _ = player_ratings(tb, role, weighting=None)
                targets[tname] = (rt.set_index("player_id")[["p_n", f"p_adj{s}"]].add_suffix("_T"), min_t)
            for setup, wt in SETUPS.items():
                ra, _ = player_ratings(train, role, weighting=wt, ref_date=cut)
                ra["active"] = ra["last_year"] >= c0.year - 1   # "active" relative to the cut-off
                rated, _ = rate(ra, adjusted_per_match(train, role, weighting=wt, ref_date=cut), role,
                                weights=WEIGHTS[role])
                for tname, (rt, min_t) in targets.items():
                    j = rated.set_index("player_id").join(rt, how="inner")
                    j = j[j["in_pool"] & (j["p_n"] >= FWD_MIN_TRAIN) & (j["p_n_T"] >= min_t)]
                    rows.append({"cutoff": cut, "role": role, "setup": setup, "target": tname, "n": len(j),
                                 "r": wcorr(j["rating"], j[f"p_adj{s}_T"], j["p_n_T"])})
    res = pd.DataFrame(rows)
    res.to_csv(TAB / "p6_weighting_check.csv", index=False)
    summ = res.groupby(["role", "target", "setup"])["r"].mean().unstack("setup")[list(SETUPS)].round(3)
    n = res.groupby(["role", "target"])["n"].median()
    return (f"# Forward check: evidence weights\n\nRating built on matches before each cut-off ({', '.join(CUTOFFS)}), "
            f"correlated with opposition-adjusted pressure value in the following 12 months (ball-weighted; "
            f">= {FWD_MIN_TRAIN} pressure balls before; after: >= {FWD_MIN_TEST} in all matches or >= {FWD_MIN_TEST_IPL} "
            f"in the IPL). Median players per cut-off: "
            + ", ".join(f"{a} {b_}: {int(v)}" for (a, b_), v in n.items()) + ". Mean correlation across cut-offs:\n\n"
            + summ.to_string() + f"\n\nWeighting in use: {WEIGHTING}")


if __name__ == "__main__":
    main()

"""Does the Pressure Rating beat the simple stats a selector would otherwise use?

For five cut-off dates (2024-01 to 2026-01), every predictor is computed from matches BEFORE the
cut-off, for the same players (in that cut-off's ranking pool, >= 60 pressure balls), and compared
with what those players did under pressure in the following 12 months.

Predictors
  rating            the full Pressure Rating (evidence weights, track record, recent-data nerf)
  rating_plain      the same rating with no evidence weights and no recent-data nerf
  value, baseline   the rating's value component alone, and the player's normal-form (non-pressure) value
  batters: pressure strike rate, pressure average, overall strike rate, overall average
  bowlers: pressure economy, pressure wickets per ball, overall economy, overall wickets per ball

Targets (next 12 months, pressure balls only)
  value     opposition-adjusted runs above par per ball (our measure)
  simple    plain pressure strike rate (batters) or economy (bowlers; lower is better), which does
            not depend on any of our modelling

Scores: the ball-weighted correlation between predictor and target, and how good the next-year
target was for each predictor's top 10 picks (difference from the average of all players compared).

Usage: .venv/Scripts/python -I src/benchmark_check.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import RATING_TIERS, adjusted_per_match, player_ratings  # noqa: E402
from predictive_check import WEIGHTS, wcorr  # noqa: E402
from rating import rate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"
CUTOFFS = ["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01", "2026-01-01"]
MIN_TRAIN, MIN_TEST = 60, 30
SCALE = {"bat": 100, "bowl": 120}


def load() -> pd.DataFrame:
    b = pd.read_csv(OUT / "ball_adjusted.csv.gz", low_memory=False)
    s = pd.read_csv(OUT / "ball_state.csv.gz", usecols=["bat_runs", "striker_out", "bowler_runs", "bowler_wicket"],
                    low_memory=False)
    b = pd.concat([b, s], axis=1)
    return b[b["comp_tier"].isin(RATING_TIERS)].reset_index(drop=True)


def simple_stats(d: pd.DataFrame, role: str) -> pd.DataFrame:
    """Traditional stats per player: on pressure balls (p_) and on all balls (a_). Higher = better."""
    out = {}
    for pre, part in (("p_", d[d["is_pressure"]]), ("a_", d)):
        if role == "bat":
            x = part[part["is_batter_ball"]]
            g = x.groupby("striker_id")
            n, runs, outs = g.size(), g["bat_runs"].sum(), g["striker_out"].sum()
            out[pre + "balls"] = n
            out[pre + "sr"] = 100 * runs / n
            out[pre + "avg"] = runs / outs.clip(lower=1)
        else:
            g = part.groupby("bowler_id")
            n, runs, wk = g["is_legal"].sum(), g["bowler_runs"].sum(), g["bowler_wicket"].sum()
            out[pre + "balls"] = n
            out[pre + "econ_neg"] = -6 * runs / n.replace(0, np.nan)         # negated: higher = better
            out[pre + "wkt_rate"] = wk / n.replace(0, np.nan)
    return pd.DataFrame(out)


PREDICTORS = {
    "bat": [("rating", "Pressure Rating (full method)"), ("value", "Value component alone"), ("baseline", "Normal-form quality (non-pressure value)"), ("rating_plain", "Pressure Rating, no weights or nerf"),
            ("p_sr", "Pressure strike rate"), ("p_avg", "Pressure batting average"),
            ("a_sr", "Overall strike rate"), ("a_avg", "Overall batting average")],
    "bowl": [("rating", "Pressure Rating (full method)"), ("value", "Value component alone"), ("baseline", "Normal-form quality (non-pressure value)"), ("rating_plain", "Pressure Rating, no weights or nerf"),
             ("p_econ_neg", "Pressure economy"), ("p_wkt_rate", "Pressure wickets per ball"),
             ("a_econ_neg", "Overall economy"), ("a_wkt_rate", "Overall wickets per ball")],
}


def main() -> None:
    b = load()
    dates = pd.to_datetime(b["match_date"])
    rows = []
    for cut in CUTOFFS:
        c0 = pd.Timestamp(cut)
        train, test = b[dates < c0], b[(dates >= c0) & (dates < c0 + pd.Timedelta(days=365))]
        for role in ("bat", "bowl"):
            s = SCALE[role]
            # predictors on the training window
            ra, _ = player_ratings(train, role, ref_date=cut)
            ra["active"] = ra["last_year"] >= c0.year - 1
            full, _ = rate(ra, adjusted_per_match(train, role, ref_date=cut), role, weights=WEIGHTS[role])
            rp, _ = player_ratings(train, role, weighting=None, ref_date=cut)
            rp["active"] = rp["last_year"] >= c0.year - 1
            plain, _ = rate(rp, adjusted_per_match(train, role, weighting=None, ref_date=cut), role,
                            weights=WEIGHTS[role], nerf=None)
            X = full.set_index("player_id")[["in_pool", "p_n", "rating", "value", f"b_shrunk{s}"]].rename(
                columns={f"b_shrunk{s}": "baseline"}).join(
                plain.set_index("player_id")["rating"].rename("rating_plain")).join(simple_stats(train, role))
            X = X[X["in_pool"] & (X["p_n"] >= MIN_TRAIN)]
            # targets on the next 12 months
            rt, _ = player_ratings(test, role, weighting=None)
            T = rt.set_index("player_id")[["p_n", f"p_adj{s}"]].rename(columns={"p_n": "t_n", f"p_adj{s}": "t_value"})
            st = simple_stats(test, role)
            T["t_simple"] = st["p_sr"] if role == "bat" else st["p_econ_neg"]
            j = X.join(T, how="inner")
            j = j[j["t_n"] >= MIN_TEST]
            for target in ("t_value", "t_simple"):
                base = np.average(j[target], weights=j["t_n"])
                for col, lab in PREDICTORS[role]:
                    ok = j[col].notna()
                    top = j[ok].nlargest(10, col)
                    rows.append({"cutoff": cut, "role": role, "target": target, "predictor": lab, "n": int(ok.sum()),
                                 "r": wcorr(j.loc[ok, col], j.loc[ok, target], j.loc[ok, "t_n"]),
                                 "top10_vs_avg": np.average(top[target], weights=top["t_n"]) - base})
    res = pd.DataFrame(rows)
    res.to_csv(TAB / "p7_benchmark.csv", index=False)
    summ = (res.groupby(["role", "target", "predictor"], sort=False)[["r", "top10_vs_avg"]].mean().round(3))
    n = res.groupby(["role", "target"])["n"].median()
    lines = ["# Benchmark: Pressure Rating vs simple stats (forward in time)", "",
             f"Cut-offs {', '.join(CUTOFFS)}; predictors from matches before each cut-off, targets from the next "
             f"12 months (>= {MIN_TRAIN} pressure balls before, >= {MIN_TEST} after). Median players per cut-off: "
             + ", ".join(f"{a} {b_}: {int(v)}" for (a, b_), v in n.items()) + ".",
             "t_value = opposition-adjusted pressure value per ball (our measure); t_simple = plain pressure strike "
             "rate (batters) or economy, sign flipped so higher = better (bowlers).",
             "r = ball-weighted correlation; top10_vs_avg = next-year target of each predictor's top 10 minus the "
             "average of all players compared (runs per ball for t_value; strike-rate points or runs per over for t_simple).",
             "", summ.to_string()]
    (TAB / "p7_benchmark.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    main()

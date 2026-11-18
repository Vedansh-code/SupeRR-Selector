"""Phase 5: final Pressure Rating and top-10 lists.

Usage (from the project root, after Phase 4):
    .venv/Scripts/python -I src/build_phase5.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import WEIGHTING  # noqa: E402
from rating import REQUIRE_ACTIVE, ROLE_WEIGHTS, USE_CV_WEIGHTS, rate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
RAW = ROOT / "data" / "raw"


def match_labels() -> pd.Series:
    m = pd.read_csv(RAW / "matches.csv").merge(pd.read_csv(RAW / "competitions.csv")[["comp_id", "comp_name"]], on="comp_id")
    return (m["home_team"] + " v " + m["away_team"] + ", " + m["comp_name"] + " (" + m["match_date"] + ")").set_axis(m["match_id"])


def best_matches(matches: pd.DataFrame, ids, labels: pd.Series, n: int = 2) -> pd.Series:
    m = matches[matches["player_id"].isin(ids)].sort_values("value_adj", ascending=False)
    top = m.groupby("player_id").head(n)
    top = top.assign(txt=top["match_id"].map(labels) + " [" + top["value_adj"].round(1).astype(str) + " runs]")
    return top.groupby("player_id")["txt"].apply(" | ".join)


def main() -> None:
    labels = match_labels()
    out_lines = ["# Phase 5: final Pressure Ratings", "",
                 ("Weights (cross-validated, src/weight_cv.py): " if USE_CV_WEIGHTS else "Weights (judgement): ")
                 + " | ".join(f"{r}: " + ", ".join(f"{k} {v:.2%}" for k, v in w.items()) for r, w in ROLE_WEIGHTS.items()),
                 f"Pool: eligible players{' active in 2025-26' if REQUIRE_ACTIVE else ''}",
                 f"Evidence weighting (all four components): {WEIGHTING}"]
    pd.set_option("display.width", 300)
    pd.set_option("display.max_colwidth", 200)
    info_out = {}

    spec = {
        "bat": ("batters", "batter", 100,
                ["p_inns", "p_n", "p_runs", "p_sr", "p_exp_sr", "p_avg", "p_out_ratio"]),
        "bowl": ("bowlers", "bowler", 120,
                 ["p_matches", "p_n", "p_wkts", "p_econ", "p_exp_econ", "p_wkt_ratio"]),
    }
    for role, (plural, single, scale, trad) in spec.items():
        r = pd.read_csv(TAB / f"p4_{plural}.csv")
        pm = pd.read_csv(TAB / f"p4_{single}_pressure_matches.csv")
        r, info = rate(r, pm, role)
        r.to_csv(TAB / f"p5_{single}_ratings.csv", index=False)
        info_out[role] = {"weights": {k: round(v * 100, 2) for k, v in info["weights_used"].items()},
                          "clutch_observed": round(info["clutch_var_observed"], 1),
                          "clutch_noise": round(info["clutch_var_noise"], 1),
                          "pool_success": round(info["pool_success_rate"], 3),
                          "value_source": info["value_source"],
                          "recent_years": info["recent_years"]}

        pool = r[r["in_pool"]]
        top = pool.head(10).copy()
        top["best_pressure_matches"] = top["player_id"].map(best_matches(pm, top["player_id"], labels))
        top.to_csv(TAB / f"p5_top10_{plural}.csv", index=False)

        rank_cols = ["rank", "name", "teams", "rating", "p_evidence_share", "p_share_IPL", "value", "consistency", "clutch", "impact",
                     "contrib_value", "contrib_consistency", "contrib_clutch", "contrib_impact", "p_n_w", "contrib_volume", "recent_avg", "recent_target", "recent_balls_0", "recent_balls_1", "recent_balls_2", "contrib_recent"]
        evid_cols = ["rank", "name"] + trad + [f"p_adj{scale}", f"p_lg{scale}", f"p_shrunk{scale}", f"b_adj{scale}", "clutch_raw",
                                               "clutch_t", "pm_n", "success_rate", "p_wpa_total", "p_share_IPL", "p_share_T20I"]
        lab = "Batters" if role == "bat" else "Bowlers"
        inactive = r[r["eligible"] & ~r["active"]]
        out_lines += [
            "", f"## {lab}",
            f"Pool size: {len(pool)} | pool success rate per pressure match: {info['pool_success_rate']:.3f}",
            f"Clutch (pressure minus own baseline, per {scale}): observed variance {info['clutch_var_observed']:.1f}, "
            f"expected from noise alone {info['clutch_var_noise']:.1f} -> true variance {info['clutch_tau2']:.1f}"
            + ("  => NOT distinguishable from noise; clutch weight redistributed" if info['clutch_tau2'] <= 0 else ""),
            "Weights used: " + ", ".join(f"{k} {v:.0%}" for k, v in info['weights_used'].items())
            + f" | value component = {info['value_source']}{scale}",
            f"Excluded as inactive (eligible, last played before 2025): {', '.join(inactive['name']) or 'none'}",
            "", "### Top 20 by Pressure Rating", pool.head(20)[rank_cols].round(3).to_string(index=False),
            "", "### Evidence for the top 10 (pressure balls only)", top[evid_cols].round(2).to_string(index=False),
            "", "### Best pressure matches (opposition-adjusted runs above average)",
            top[["rank", "name", "best_pressure_matches"]].to_string(index=False),
        ]
    (TAB / "phase5_info.json").write_text(json.dumps(info_out, indent=2), encoding="utf-8")
    (TAB / "phase5_summary.md").write_text("\n".join(out_lines), encoding="utf-8")
    print("\n".join(out_lines))


if __name__ == "__main__":
    main()

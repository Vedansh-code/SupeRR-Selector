"""Phase 4: fair comparison - opposition adjustment, shrinkage, eligibility.

Usage (from the project root, after Phase 3):
    .venv/Scripts/python -I src/build_phase4.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import (ELIG, WEIGHTING, adjusted_per_match, apply_opposition, opponent_strength, opposition_model,
                       season_par_adjust,  # noqa: E402
                      player_ratings, team_tier)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"
CTX_COLS = ["match_id", "innings", "batting_team_id", "bowling_team_id", "striker_id", "bowler_id", "is_batter_ball",
            "is_legal", "is_pressure", "comp_tier", "year", "match_date", "is_knockout",
            "stakes_pct", "stress_pct", "pressure_score"]


def load() -> pd.DataFrame:
    ctx = pd.read_csv(OUT / "ball_pressure.csv.gz", usecols=CTX_COLS, low_memory=False)
    val = pd.read_csv(OUT / "ball_values.csv.gz", usecols=["match_id", "striker_id", "bat_value", "bowl_value", "wpa_all"])
    assert (ctx["match_id"].values == val["match_id"].values).all() and (ctx["striker_id"].values == val["striker_id"].values).all()
    return pd.concat([ctx, val[["bat_value", "bowl_value", "wpa_all"]]], axis=1)


def format_consistency(b: pd.DataFrame, id_col: str, val: str, mask: pd.Series, players: pd.Index, min_n: int = 40):
    d = b[mask & b["is_pressure"] & b["comp_tier"].isin(["IPL", "T20I"]) & b[id_col].isin(players)]
    t = d.groupby([id_col, "comp_tier"])[val].agg(["mean", "size"]).unstack("comp_tier")
    t = t[(t[("size", "IPL")] >= min_n) & (t[("size", "T20I")] >= min_n)]
    return len(t), t[("mean", "IPL")].corr(t[("mean", "T20I")])


def main() -> None:
    b = load()
    # measure every ball against its own competition-season par (removes scoring-rate drift)
    b, season_par = season_par_adjust(b)
    teams = pd.read_csv(ROOT / "data" / "raw" / "teams.csv").drop_duplicates("team_id").set_index("team_id")["team_name"]
    ipl_teams = set(teams.reindex(b.loc[b.comp_tier.eq("IPL"), "batting_team_id"].unique()))
    tier = {tid: team_tier(name, ipl_teams) for tid, name in teams.items()}
    b["bat_tier"] = b["batting_team_id"].map(tier)
    b["bowl_tier"] = b["bowling_team_id"].map(tier)

    om = opposition_model(b)
    b = apply_opposition(b, om)
    # opponent strength on a 0-1 scale (1 = average IPL side, 0 = average associate side), per ball
    strength = opponent_strength(b)
    b["opp_str_bat"] = b["bowling_team_id"].map(strength["bat"]["strength"])
    b["opp_str_bowl"] = b["batting_team_id"].map(strength["bowl"]["strength"])
    # T20Is against the named strong nations count like IPL (WEIGHTING["comp"]["T20I_strong"])
    strong_ids = {tid for tid, name in teams.items() if name in WEIGHTING["strong_t20i_teams"]}
    b["strong_opp_bat"] = b["bowling_team_id"].isin(strong_ids)
    b["strong_opp_bowl"] = b["batting_team_id"].isin(strong_ids)
    b.to_csv(OUT / "ball_adjusted.csv.gz", index=False)  # input for Phase 6 reliability checks

    p3 = {"bat": pd.read_csv(TAB / "p3_batters.csv"), "bowl": pd.read_csv(TAB / "p3_bowlers.csv")}
    keep3 = {
        "bat": ["player_id", "name", "teams", "a_balls", "p_inns", "p_runs", "p_sr", "p_exp_sr", "p_avg", "p_out_ratio",
                "p_dot_pct", "p_bnd_pct", "p_value100", "p_levw_value100", "p_wpa"],
        "bowl": ["player_id", "name", "teams", "type", "a_balls", "p_matches", "p_wkts", "p_econ", "p_exp_econ",
                 "p_wkt_ratio", "p_sr", "p_dot_pct", "p_value120", "p_levw_value120", "p_wpa"],
    }
    res, info = {}, {}
    for role in ("bat", "bowl"):
        r, info[role] = player_ratings(b, role)
        r = p3[role][keep3[role]].merge(r, on="player_id", how="right")
        res[role] = r
        r.to_csv(TAB / f"p4_{'batters' if role == 'bat' else 'bowlers'}.csv", index=False)
        adjusted_per_match(b, role).to_csv(
            TAB / f"p4_{'batter' if role == 'bat' else 'bowler'}_pressure_matches.csv", index=False)

    # ---------- checks ----------
    lines = ["# Phase 4 summary", "",
             "## Season par removed (average value of each competition-season, before adjustment)",
             "Every ball is measured against its own competition-season par, so an average batter or bowler in any",
             "competition-season is worth 0. Offsets removed (runs per 100 balls batting, per 120 legal balls bowling):",
             season_par.to_string(), "",
             "## Opponent strength used for evidence weights (1 = average IPL side, 0 = average associate side)"]
    for role, lab in (("bat", "Bowling attacks faced by batters"), ("bowl", "Batting line-ups faced by bowlers")):
        t = strength[role][strength[role]["n"] >= 300].sort_values("strength", ascending=False)
        lines += [f"### {lab}", t.assign(team=t.index.map(teams))[["team", "tier", "n", "strength"]].round(3).to_string(index=False)]
    lines += ["", "## Opposition model (ridge: batter + bowler + team tier)",
             f"alpha chosen by 5-fold match-grouped CV: {om['alpha']} (CV MSE: "
             + ", ".join(f"{a}: {m:.4f}" for a, m in om["cv_mse"].items()) + ")",
             "Team-tier effects on batting value (runs per ball; + = easier for the batter):",
             om["tier_effect"].round(4).to_string()]

    names_bat = res["bat"].set_index("player_id")["name"]
    names_bowl = res["bowl"].set_index("player_id")["name"]
    nballs_bowl = b[b.is_legal].groupby("bowler_id").size()
    nballs_bat = b[b.is_batter_ball].groupby("striker_id").size()
    be = om["bowler_effect"][nballs_bowl.reindex(om["bowler_effect"].index).fillna(0) >= 600]
    bt = om["batter_effect"][nballs_bat.reindex(om["batter_effect"].index).fillna(0) >= 600]
    lines += ["", "## Toughest bowlers to face (runs per 100 balls vs average, >= 600 balls)",
              (be.nsmallest(12) * 100).round(2).rename(index=names_bowl).to_string(),
              "", "## Most dangerous batters (runs per 100 balls vs average, >= 600 balls)",
              (bt.nlargest(12) * 100).round(2).rename(index=names_bat).to_string()]

    for role, scale in (("bat", 100), ("bowl", 120)):
        r, i = res[role], info[role]
        e = r[r.eligible]
        lab = "Batters" if role == "bat" else "Bowlers"
        mix = e[[f"p_share_{c}" for c in ("IPL", "T20I", "Emerging")]].mean().round(3)
        id_col, val = ("striker_id", "bat_value_adj") if role == "bat" else ("bowler_id", "bowl_value_adj")
        mask = b["is_batter_ball"] if role == "bat" else b["is_legal"]
        n_both, corr_fmt = format_consistency(b, id_col, val, mask, pd.Index(e["player_id"]))
        rank_raw = e[f"p_raw{scale}"].rank(ascending=False)
        rank_new = e[f"p_lg{scale}"].rank(ascending=False)
        movers = e.assign(rank_raw=rank_raw, rank_shrunk=rank_new, move=rank_raw - rank_new)
        cols = ["name", "teams", "p_n", "p_n_w", "p_evidence_share", "p_opp_strength", "p_games", f"p_raw{scale}", f"p_opp{scale}", f"p_adj{scale}", "p_weight_lg",
                f"p_lg{scale}", f"p_shrunk{scale}", f"b_shrunk{scale}", "p_share_T20I", "p_share_Emerging", "active"]
        rs = e["p_evidence_share"]
        lines += [
            "", f"## {lab}",
            f"Evidence weighting {WEIGHTING} (recency measured back from {i['ref_date']}). "
            f"Eligible players' pressure records count at {rs.median():.0%} of their raw size (median; "
            f"range {rs.min():.0%}-{rs.max():.0%})",
            f"Players: {len(r)} | eligible (>= {ELIG[role]['min_p_balls']} pressure balls, >= {ELIG[role]['min_p_games']} games): "
            f"{int(r.eligible.sum())} | eligible & active since 2025: {int((r.eligible & r.active).sum())}",
            f"Shrinkage: baseline k = {i['b_k']:.0f} balls, pressure k = {i['p_k']:.0f} balls "
            f"(a player with k pressure balls gets 50% weight on their own record)",
            f"Pressure shrunk towards league mean: k = {i['p_k_lg']:.0f} balls",
            f"Pressure prior = {i['prior_alpha'] * scale:.2f} + {i['prior_beta']:.2f} x shrunk baseline (per {scale})",
            f"Eligible players' pressure-ball mix: IPL {mix.iloc[0]:.0%}, T20I {mix.iloc[1]:.0%}, Emerging {mix.iloc[2]:.0%}",
            f"IPL vs T20I consistency: {n_both} eligible players with >= 40 pressure balls in both; "
            f"correlation of adjusted pressure value = {corr_fmt:.2f}",
            "", f"### Preview: eligible {lab.lower()} by pressure value shrunk to league mean (p_lg, per {scale}); "
                f"p_shrunk = shrunk to own-baseline prior",
            e.sort_values(f"p_lg{scale}", ascending=False).head(25)[cols].round(2).to_string(index=False),
            "", "### Biggest movers vs raw pressure value (rank among eligible)",
            movers.reindex(movers["move"].abs().sort_values(ascending=False).index).head(10)[
                ["name", "p_n", f"p_raw{scale}", f"p_opp{scale}", f"p_lg{scale}", "rank_raw", "rank_shrunk"]
            ].round(2).to_string(index=False),
        ]

    # machine-readable hyperparameters for the dashboard
    (TAB / "phase4_info.json").write_text(json.dumps({
        "alpha": int(om["alpha"]),
        "weighting": WEIGHTING,
        **{role: {"k_lg": round(i["p_k_lg"]), "k_prior": round(i["p_k"]), "k_baseline": round(i["b_k"]),
                  "ref_date": i["ref_date"],
                  "evidence_share_median": round(float(res[role].loc[res[role].eligible, "p_evidence_share"].median()), 3),
                  "opponents": [{"team": teams.get(tid, str(tid)), "tier": row["tier"], "balls": int(row["n"]),
                                 "strength": round(float(row["strength"]), 3),
                                 "weight": round(WEIGHTING["opponent"][0] + (WEIGHTING["opponent"][1] - WEIGHTING["opponent"][0])
                                                 * float(row["strength"]), 3)}
                                for tid, row in strength[role].sort_values("strength", ascending=False).iterrows()
                                if row["n"] >= 300]}
           for role, i in info.items()},
    }, indent=2), encoding="utf-8")
    (TAB / "phase4_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    main()

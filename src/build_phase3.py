"""Phase 3: context-adjusted player metrics, pressure vs baseline.

Usage (from the project root, after Phase 2):
    .venv/Scripts/python -I src/build_phase3.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from expected import add_expectations  # noqa: E402
from metrics import batting, bowling, per_match  # noqa: E402
from pressure import realised_delta  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"
PREVIEW_MIN = 120  # pressure balls, for the preview list only (eligibility is set in Phase 4)


def team_labels(b: pd.DataFrame, id_col: str, team_col: str, teams: pd.DataFrame) -> pd.Series:
    names = teams.drop_duplicates("team_id").set_index("team_id")["team_name"]
    c = b.groupby([id_col, team_col]).size().rename("n").reset_index().sort_values("n", ascending=False)
    c["team"] = c[team_col].map(names)
    return c.groupby(id_col)["team"].apply(lambda s: ", ".join(s.head(2)))


def main() -> None:
    b = pd.read_csv(OUT / "ball_pressure.csv.gz", low_memory=False)
    b["wpa_all"] = realised_delta(b, b["wp_before"])
    b["wpa"] = b["wpa_all"].where(b["is_batter_ball"])
    b = add_expectations(b)

    teams = pd.read_csv(ROOT / "data" / "raw" / "teams.csv")
    bat_names = b.groupby("striker_id")["striker_name"].first()
    bowl_names = b.groupby("bowler_id")["bowler_name"].first()

    # Ratings scope = IPL + T20I (the brief's scope). A-team "Emerging" events stay in model
    # training above (more context) but are excluded from player aggregates.
    full_b = b
    b = b[b["comp_tier"].ne("Emerging")]
    bat = batting(b)
    bat.insert(1, "name", bat["player_id"].map(bat_names))
    bat.insert(2, "teams", bat["player_id"].map(team_labels(b, "striker_id", "batting_team_id", teams)))
    bowl = bowling(b)
    bowl.insert(1, "name", bowl["player_id"].map(bowl_names))
    bowl.insert(2, "teams", bowl["player_id"].map(team_labels(b, "bowler_id", "bowling_team_id", teams)))
    bowl.insert(3, "type", bowl["player_id"].map(b.groupby("bowler_id")["bowling_type"].agg(lambda s: s.mode().iat[0])))

    bat_m = per_match(b, "bat")
    bowl_m = per_match(b, "bowl")
    b = full_b  # model checks and the ball-level file use all deliveries

    # ---------- checks ----------
    bb = b[b["is_batter_ball"]]
    calib = pd.DataFrame({
        "bat_runs": bb.groupby("pressure_band")["bat_runs"].sum(),
        "exp_bat_runs": bb.groupby("pressure_band")["exp_bat_runs"].sum(),
        "striker_outs": bb.groupby("pressure_band")["striker_out"].sum(),
        "exp_striker_outs": bb.groupby("pressure_band")["p_striker_out"].sum(),
        "bowler_runs": b.groupby("pressure_band")["bowler_runs"].sum(),
        "exp_bowler_runs": b.groupby("pressure_band")["exp_bowler_runs"].sum(),
        "bowler_wkts": b.groupby("pressure_band")["bowler_wicket"].sum(),
        "exp_bowler_wkts": b.groupby("pressure_band")["p_bowler_wkt"].sum(),
    }).round(1)
    wv = b.pivot_table(index="overid", columns="innings", values="wicket_value", aggfunc="mean").round(1)
    wv_w = b[b.innings.eq(1)].pivot_table(index="wkts_before", columns="phase", values="wicket_value").round(1)

    bat_cols = ["name", "teams", "p_balls", "p_inns", "p_sr", "p_exp_sr", "p_avg", "p_out_ratio", "p_value100",
                "b_value100", "delta_value100", "p_levw_value100", "p_wpa"]
    bowl_cols = ["name", "teams", "type", "p_balls", "p_matches", "p_econ", "p_exp_econ", "p_wkts", "p_wkt_ratio",
                 "p_value120", "b_value120", "delta_value120", "p_levw_value120", "p_wpa"]
    bat_prev = bat[bat["p_balls"] >= PREVIEW_MIN].nlargest(20, "p_value100")[bat_cols]
    bowl_prev = bowl[bowl["p_balls"] >= PREVIEW_MIN].nlargest(20, "p_value120")[bowl_cols]
    corr_bat = bat.loc[bat.p_balls >= PREVIEW_MIN, ["p_value100", "b_value100"]].corr().iat[0, 1]
    corr_bowl = bowl.loc[bowl.p_balls >= PREVIEW_MIN, ["p_value120", "b_value120"]].corr().iat[0, 1]

    # ---------- write ----------
    keep = ["match_id", "innings", "overid", "over_ball_num", "striker_id", "bowler_id", "is_pressure", "pressure_band",
            "pressure_pct", "leverage_index", "wicket_value", "exp_bat_runs", "p_striker_out", "exp_bowler_runs",
            "p_bowler_wkt", "bat_value", "bowl_value", "wpa_all"]
    b[keep].to_csv(OUT / "ball_values.csv.gz", index=False)
    bat.to_csv(TAB / "p3_batters.csv", index=False)
    bowl.to_csv(TAB / "p3_bowlers.csv", index=False)
    bat_m.to_csv(TAB / "p3_batter_pressure_matches.csv", index=False)
    bowl_m.to_csv(TAB / "p3_bowler_pressure_matches.csv", index=False)

    pd.set_option("display.width", 250)
    lines = [
        "# Phase 3 summary", "",
        "## Expectation models: actual vs expected totals by pressure band (should be close)", calib.to_string(),
        "", f"League totals: batting value {b['bat_value'].sum():.1f} runs, bowling value {b['bowl_value'].sum():.1f} runs "
            "(both should be ~0 by construction)",
        "", "## Wicket value (runs) by over", wv.to_string(),
        "", "## Wicket value, innings 1, by wickets down x phase", wv_w.to_string(),
        "", f"## Players: {len(bat)} batters, {len(bowl)} bowlers",
        f"Correlation of pressure value with baseline value (>= {PREVIEW_MIN} pressure balls): "
        f"batters {corr_bat:.2f}, bowlers {corr_bowl:.2f}",
        "", f"## PREVIEW (unadjusted, no shrinkage/opposition): batters, >= {PREVIEW_MIN} pressure balls, by value per 100",
        bat_prev.round(2).to_string(index=False),
        "", f"## PREVIEW: bowlers, >= {PREVIEW_MIN} pressure balls, by runs saved per 20 overs",
        bowl_prev.round(2).to_string(index=False),
    ]
    (TAB / "phase3_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

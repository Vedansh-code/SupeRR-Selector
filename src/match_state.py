"""Build the pre-delivery match state for every ball.

Every "_before" column describes the situation the batter/bowler faced *as the ball was
bowled*, i.e. it excludes the outcome of the ball itself. That is what a pressure index
must be built on.
"""
import numpy as np
import pandas as pd

from load import BOWLER_WICKETS, NO_BALL, NOT_LEGAL

FULL_INNINGS_BALLS = 120


def _clean_balls(b: pd.DataFrame) -> pd.DataFrame:
    b = b[b["innings"].isin([1, 2])].copy()  # innings 3/4 are super overs
    b = b.sort_values(["match_id", "innings", "overid", "over_ball_num"], kind="stable").reset_index(drop=True)

    b["extras_type"] = b["extras_type"].fillna("None")
    b["is_wide"] = b["extras_type"].eq("wide")
    b["is_noball"] = b["extras_type"].isin(NO_BALL)
    b["is_legal"] = ~b["extras_type"].isin(NOT_LEGAL)
    b["is_batter_ball"] = ~b["is_wide"]  # balls faced: everything except wides

    # `runs` = runs off the bat; extras are held separately.
    b["bat_runs"] = b["runs"]
    b["total_runs"] = b["runs"] + b["extras1_runs"] + b["extras_2_runs"]
    # Charged to the bowler: bat runs + wide/no-ball extras (not byes/leg-byes/penalties).
    b["bowler_runs"] = b["runs"] + np.where(b["is_wide"] | b["is_noball"], b["extras1_runs"], 0)

    b["is_wicket"] = b["is_wicket"].astype(bool)
    b["bowler_wicket"] = b["is_wicket"] & b["dismissal_type"].isin(BOWLER_WICKETS)
    b["striker_out"] = b["is_wicket"] & b["dismissed_player_id"].eq(b["striker_id"])
    b["is_dot"] = b["is_batter_ball"] & b["total_runs"].eq(0)
    b["is_boundary"] = b["is_four"].astype(bool) | b["is_six"].astype(bool)
    return b


def _consecutive_count(flag: pd.Series, group: pd.Series) -> pd.Series:
    """Length of the current run of True values, reset on False and at group change."""
    reset = (~flag).astype(int).groupby(group).cumsum()
    return flag.astype(int).groupby([group, reset]).cumsum()


def build_match_state(balls: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    b = _clean_balls(balls)
    b = b.merge(ctx, on="match_id", how="left", validate="many_to_one")

    inn = ["match_id", "innings"]
    g = b.groupby(inn, sort=False)

    # --- running team state (before this delivery) ---
    b["runs_before"] = g["total_runs"].cumsum() - b["total_runs"]
    b["wkts_before"] = g["is_wicket"].cumsum() - b["is_wicket"].astype(int)
    b["legal_before"] = g["is_legal"].cumsum() - b["is_legal"].astype(int)
    b["wkts_in_hand"] = 10 - b["wkts_before"]

    # balls available (DLS revised overs are stored in balls, e.g. 114 = 19 overs)
    b["balls_avail"] = np.where(
        b["innings"].eq(1),
        b["first_inn_revised_overs"].fillna(FULL_INNINGS_BALLS),
        b["second_inn_revised_overs"].fillna(FULL_INNINGS_BALLS),
    ).astype(int)
    b["balls_left"] = (b["balls_avail"] - b["legal_before"]).clip(lower=1)
    b["over_num"] = b["overid"]  # 1-based over number
    b["phase"] = pd.cut(b["overid"], [0, 6, 15, 20], labels=["powerplay", "middle", "death"]).astype(str)
    b["crr"] = np.where(b["legal_before"] > 0, b["runs_before"] * 6 / b["legal_before"].clip(lower=1), np.nan)

    # --- innings totals ---
    tot = g.agg(
        inn_runs=("total_runs", "sum"),
        inn_wkts=("is_wicket", "sum"),
        inn_legal=("is_legal", "sum"),
        batting_team_id=("batting_team_id", "first"),
    ).reset_index()
    first = tot[tot["innings"].eq(1)].set_index("match_id")
    b["inn1_runs"] = b["match_id"].map(first["inn_runs"])
    b = b.merge(tot[inn + ["inn_runs", "inn_wkts", "inn_legal"]], on=inn, how="left")

    # --- chase state (innings 2) ---
    is2 = b["innings"].eq(2)
    b["target"] = np.where(is2, b["revised_target"].fillna(b["inn1_runs"] + 1), np.nan)
    b["runs_needed"] = b["target"] - b["runs_before"]
    b["rrr"] = b["runs_needed"] * 6 / b["balls_left"]
    b["rrr_minus_crr"] = b["rrr"] - b["crr"]

    # --- momentum / recent context (rolling over previous deliveries in the innings) ---
    key = b["match_id"].astype(str) + "_" + b["innings"].astype(str)
    for col, src in [("wkts_last_24", "is_wicket"), ("runs_last_24", "total_runs")]:
        s = b[src].astype(int)
        b[col] = s.groupby(key).transform(lambda x: x.shift(1).rolling(24, min_periods=1).sum()).fillna(0)
    b["team_dot_streak"] = (
        _consecutive_count(b["is_dot"], key).groupby(key).shift(1).fillna(0).astype(int)
    )

    # --- batter / partnership state ---
    bk = key + "_" + b["striker_id"].astype(str)
    b["batter_balls_before"] = b["is_batter_ball"].astype(int).groupby(bk).cumsum() - b["is_batter_ball"].astype(int)
    b["batter_runs_before"] = b["bat_runs"].groupby(bk).cumsum() - b["bat_runs"]
    part_id = b.groupby(key)["is_wicket"].transform(lambda x: x.astype(int).shift(1).fillna(0).cumsum())
    pk = key + "_" + part_id.astype(int).astype(str)
    b["partnership_runs_before"] = b["total_runs"].groupby(pk).cumsum() - b["total_runs"]
    b["partnership_balls_before"] = b["is_legal"].astype(int).groupby(pk).cumsum() - b["is_legal"].astype(int)

    # --- outcome labels for later models ---
    # 1 = batting side won, 0 = lost, 0.5 = tied in regulation (super over), NaN = no result
    won = (b["win_team_id"] == b["batting_team_id"]).astype(float)
    b["batting_team_won"] = np.where(b["no_result"], np.nan, np.where(b["is_tie"], 0.5, won))
    b["bowler_spell_ball"] = b.groupby(inn + ["bowler_id"]).cumcount() + 1
    return b

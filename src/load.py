"""Load the raw data pack and attach match / competition context to every delivery."""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

# Extras types that are NOT legal deliveries (ball must be re-bowled).
# "Overstep" and "other" both carry a 1-run penalty in extras1_runs with bat runs in `runs`,
# i.e. they behave like no-balls.
NOT_LEGAL = {"wide", "Overstep", "other"}
NO_BALL = {"Overstep", "other"}

# Dismissals credited to the bowler.
BOWLER_WICKETS = {"Bowled", "Caught", "LBW", "Stump", "Hit Wicket"}


def load_raw(raw_dir: Path = RAW) -> dict[str, pd.DataFrame]:
    return {
        "balls": pd.read_csv(raw_dir / "ball_by_ball.csv"),
        "matches": pd.read_csv(raw_dir / "matches.csv"),
        "competitions": pd.read_csv(raw_dir / "competitions.csv"),
        "playing_xi": pd.read_csv(raw_dir / "playing_eleven.csv"),
        "teams": pd.read_csv(raw_dir / "teams.csv"),
        "ctp": pd.read_csv(raw_dir / "competition_team_player_mapping.csv"),
    }


def match_context(matches: pd.DataFrame, comps: pd.DataFrame) -> pd.DataFrame:
    """One row per match with format, season, stage and DLS info."""
    m = matches.merge(comps[["comp_id", "comp_name", "match_format", "season"]], on="comp_id", how="left")
    m["match_date"] = pd.to_datetime(m["match_date"])
    m["year"] = m["match_date"].dt.year
    # match_format "T20" also covers two A-team events (Emerging Teams Asia Cup 2024, Asia Cup
    # Rising Stars 2025), so IPL is identified by competition name.
    m["comp_tier"] = np.select(
        [m["comp_name"].str.startswith("IPL"), m["match_format"].eq("T20I")], ["IPL", "T20I"], "Emerging"
    )
    m["is_ipl"] = m["comp_tier"].eq("IPL")
    m["is_emerging"] = m["comp_tier"].eq("Emerging")
    m["is_knockout"] = m["knock_out"].eq(1) | m["stage"].isin(
        ["Final", "Semi Final", "Qualifier", "Eliminator"]
    )
    m["is_dls"] = m["revised_target"].notna() | m["result"].str.contains(r"D/?L", case=False, na=False)
    m["no_result"] = m["result"].str.contains("No Result|Abandoned", case=False, na=False) | m["win_team_id"].isna()
    m["is_tie"] = m["result"].str.contains(r"super over|tied|one over eliminator", case=False, na=False)
    return m[
        [
            "match_id", "comp_id", "comp_name", "match_format", "season", "year", "match_date",
            "stage", "is_knockout", "comp_tier", "is_ipl", "is_emerging", "venue_id", "venue_country",
            "home_team_id", "home_team", "away_team_id", "away_team",
            "first_inn_revised_overs", "second_inn_revised_overs", "revised_target", "is_dls",
            "win_team_id", "result", "no_result", "is_tie",
        ]
    ]

"""Player-level batting and bowling metrics, split into pressure vs baseline.

Segments:  "pressure" = high-pressure band (top 20%)
           "baseline" = everything else (the player's usual level)
           "all"      = every ball
Value metrics are per 100 balls (batting) or per 120 balls = 20 overs (bowling), in runs
above the average player in the same situation, so they compare fairly across phases/roles.
"""
import numpy as np
import pandas as pd

LEV_CAP = 5.0  # cap leverage when used as a weight (last-ball finishes reach 40+)


def _seg(b: pd.DataFrame) -> pd.Series:
    return np.where(b["is_pressure"], "pressure", "baseline")


def _wide(t: pd.DataFrame, key: str, metric_cols: list[str]) -> pd.DataFrame:
    w = t.pivot_table(index=key, columns="segment", values=metric_cols)
    w.columns = [f"{seg[0]}_{m}" for m, seg in w.columns]  # p_ / b_ / a_
    return w


def batting(b: pd.DataFrame) -> pd.DataFrame:
    d = b[b["is_batter_ball"]].copy()
    d["levw"] = d["leverage_index"].clip(upper=LEV_CAP)
    d["levw_value"] = d["bat_value"] * d["levw"]
    frames = []
    for seg, part in [("all", d), *d.groupby(_seg(d))]:
        g = part.groupby("striker_id")
        t = pd.DataFrame({
            "inns": g["match_id"].nunique(),
            "balls": g.size(),
            "runs": g["bat_runs"].sum(),
            "outs": g["striker_out"].sum(),
            "dots": g["is_dot"].sum(),
            "bnd": g["is_boundary"].sum(),
            "exp_runs": g["exp_bat_runs"].sum(),
            "exp_outs": g["p_striker_out"].sum(),
            "value": g["bat_value"].sum(),
            "wpa": g["wpa"].sum(),
            "levw": g["levw"].sum(),
            "levw_value": g["levw_value"].sum(),
        })
        t["sr"] = 100 * t["runs"] / t["balls"]
        t["exp_sr"] = 100 * t["exp_runs"] / t["balls"]
        t["avg"] = t["runs"] / t["outs"].replace(0, np.nan)
        t["balls_per_out"] = t["balls"] / t["outs"].replace(0, np.nan)
        t["out_ratio"] = t["outs"] / t["exp_outs"]  # <1 = gets out less than average
        t["dot_pct"] = 100 * t["dots"] / t["balls"]
        t["bnd_pct"] = 100 * t["bnd"] / t["balls"]
        t["value100"] = 100 * t["value"] / t["balls"]
        t["levw_value100"] = 100 * t["levw_value"] / t["levw"]
        t["wpa100"] = 100 * t["wpa"] / t["balls"]
        frames.append(t.assign(segment=seg).reset_index())
    long = pd.concat(frames, ignore_index=True)
    w = _wide(long, "striker_id", [c for c in long.columns if c not in ("striker_id", "segment")])
    w["delta_value100"] = w["p_value100"] - w["b_value100"]
    w["delta_sr_vs_exp"] = (w["p_sr"] - w["p_exp_sr"]) - (w["b_sr"] - w["b_exp_sr"])
    w["pressure_share"] = w["p_balls"] / w["a_balls"]
    return w.reset_index().rename(columns={"striker_id": "player_id"})


def bowling(b: pd.DataFrame) -> pd.DataFrame:
    d = b.copy()
    d["levw"] = d["leverage_index"].clip(upper=LEV_CAP)
    d["levw_value"] = d["bowl_value"] * d["levw"]
    d["bwpa"] = -d["wpa_all"]
    d["bnd_conceded"] = d["is_boundary"]
    frames = []
    for seg, part in [("all", d), *d.groupby(_seg(d))]:
        g = part.groupby("bowler_id")
        t = pd.DataFrame({
            "matches": g["match_id"].nunique(),
            "deliveries": g.size(),
            "balls": g["is_legal"].sum(),
            "runs": g["bowler_runs"].sum(),
            "wkts": g["bowler_wicket"].sum(),
            "dots": g["is_dot"].sum(),
            "bnd": g["bnd_conceded"].sum(),
            "exp_runs": g["exp_bowler_runs"].sum(),
            "exp_wkts": g["p_bowler_wkt"].sum(),
            "value": g["bowl_value"].sum(),
            "wpa": g["bwpa"].sum(),
            "levw": g["levw"].sum(),
            "levw_value": g["levw_value"].sum(),
        })
        t["econ"] = 6 * t["runs"] / t["balls"]
        t["exp_econ"] = 6 * t["exp_runs"] / t["balls"]
        t["sr"] = t["balls"] / t["wkts"].replace(0, np.nan)
        t["avg"] = t["runs"] / t["wkts"].replace(0, np.nan)
        t["wkt_ratio"] = t["wkts"] / t["exp_wkts"]  # >1 = takes more wickets than average
        t["dot_pct"] = 100 * t["dots"] / t["deliveries"]
        t["bnd_pct"] = 100 * t["bnd"] / t["deliveries"]
        t["value120"] = 120 * t["value"] / t["balls"]
        t["levw_value120"] = 120 * t["levw_value"] / t["levw"]  # leverage-weighted value per ball x 120
        t["wpa120"] = 120 * t["wpa"] / t["balls"]
        frames.append(t.assign(segment=seg).reset_index())
    long = pd.concat(frames, ignore_index=True)
    w = _wide(long, "bowler_id", [c for c in long.columns if c not in ("bowler_id", "segment")])
    w["delta_value120"] = w["p_value120"] - w["b_value120"]
    w["delta_econ_vs_exp"] = (w["b_econ"] - w["b_exp_econ"]) - (w["p_econ"] - w["p_exp_econ"])
    w["pressure_share"] = w["p_balls"] / w["a_balls"]
    return w.reset_index().rename(columns={"bowler_id": "player_id"})


def per_match(b: pd.DataFrame, role: str) -> pd.DataFrame:
    """One row per player per match: pressure-ball performance (for consistency checks)."""
    if role == "bat":
        d = b[b["is_batter_ball"] & b["is_pressure"]]
        g = d.groupby(["striker_id", "match_id"])
        t = pd.DataFrame({"balls": g.size(), "runs": g["bat_runs"].sum(), "out": g["striker_out"].max(),
                          "exp_runs": g["exp_bat_runs"].sum(), "value": g["bat_value"].sum(), "wpa": g["wpa"].sum()})
        t.index = t.index.set_names(["player_id", "match_id"])
    else:
        d = b[b["is_pressure"]]
        g = d.groupby(["bowler_id", "match_id"])
        t = pd.DataFrame({"balls": g["is_legal"].sum(), "runs": g["bowler_runs"].sum(), "wkts": g["bowler_wicket"].sum(),
                          "exp_runs": g["exp_bowler_runs"].sum(), "value": g["bowl_value"].sum(), "wpa": -g["wpa_all"].sum()})
        t.index = t.index.set_names(["player_id", "match_id"])
    ctx = b.groupby("match_id")[["match_date", "comp_name", "is_ipl", "is_knockout", "stage"]].first()
    return t.reset_index().merge(ctx, on="match_id", how="left")

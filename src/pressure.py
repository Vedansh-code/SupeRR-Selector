"""Pressure definition: STAKES x STRESS, blended.

Component A - Stakes = Leverage Index (LI)
    How much the result of the match hangs on this delivery: the expected absolute swing in
    win probability across the possible outcomes of the ball, using league outcome rates for
    that innings and phase. Normalised so the average delivery has LI = 1. The same number
    applies to the batter and the bowler, who face the same ball from opposite sides.
    Peaks in close, late chases; low in decided games.

Component B - Situational stress (0-100, rule-based, no model)
    How hard the situation is for the players: required rate in the "tough but still
    achievable" zone, wickets lost (beyond par in innings 1), a recent collapse, and the
    stage of the innings. Captures collapse pressure that the WP model under-weights in
    innings 1 (it treats 30/5 as an already-decided game).

pressure_score = (0.65 x percentile(LI) + 0.35 x percentile(stress)) x 1.15 if knockout
High pressure  = top 20% of deliveries by pressure_score.
"""
import numpy as np
import pandas as pd

from win_prob import WinProb

# Outcomes of one delivery: (label, team runs, wicket, consumes a legal ball)
OUTCOMES = [
    ("dot", 0, 0, 1), ("1", 1, 0, 1), ("2", 2, 0, 1), ("3", 3, 0, 1),
    ("4", 4, 0, 1), ("6", 6, 0, 1), ("wicket", 0, 1, 1), ("extra", 1, 0, 0),
]
KNOCKOUT_MULT = 1.15
W_STAKES, W_STRESS = 0.65, 0.35
BANDS = {"low": (0, 0.50), "medium": (0.50, 0.80), "high": (0.80, 1.0)}


def outcome_label(b: pd.DataFrame) -> pd.Series:
    lab = np.select(
        [~b["is_legal"], b["is_wicket"], b["total_runs"].ge(6), b["total_runs"].ge(4)],
        ["extra", "wicket", "6", "4"],
        default=b["total_runs"].clip(upper=3).map({0: "dot", 1: "1", 2: "2", 3: "3"}).astype(str),
    )
    return pd.Series(lab, index=b.index)


def outcome_rates(b: pd.DataFrame) -> pd.DataFrame:
    """League probability of each outcome by innings x phase (rows sum to 1)."""
    lab = outcome_label(b)
    rates = pd.crosstab([b["innings"], b["phase"]], lab, normalize="index")
    return rates.reindex(columns=[o[0] for o in OUTCOMES], fill_value=0.0)


def leverage(b: pd.DataFrame, wp: WinProb) -> pd.DataFrame:
    rates = outcome_rates(b)
    out = pd.DataFrame(index=b.index, columns=["wp_before", "exp_abs_swing"], dtype=float)
    for inn in (1, 2):
        d = b[b["innings"].eq(inn)]
        args = dict(balls_avail=d["balls_avail"].values, target=d["target"].values, is_ipl=d["is_ipl"].values)
        wp0 = wp.predict(inn, d["runs_before"].values, d["wkts_in_hand"].values, d["balls_left"].values, **args)
        r = rates.loc[inn].reindex(d["phase"]).values  # per-ball outcome probabilities
        swing = np.zeros(len(d))
        for j, (_, runs, wkt, ball) in enumerate(OUTCOMES):
            wp1 = wp.predict(
                inn, d["runs_before"].values + runs, d["wkts_in_hand"].values - wkt,
                d["balls_left"].values - ball, **args,
            )
            swing += r[:, j] * np.abs(wp1 - wp0)
        out.loc[d.index, "wp_before"] = wp0
        out.loc[d.index, "exp_abs_swing"] = swing
    return out


def realised_swing(b: pd.DataFrame, wp_before: pd.Series) -> pd.Series:
    """|WP after - WP before| for what actually happened (used only for validation)."""
    return realised_delta(b, wp_before).abs()


def realised_delta(b: pd.DataFrame, wp_before: pd.Series) -> pd.Series:
    """WP after - WP before, from the batting side's point of view (= win probability added)."""
    nxt = wp_before.groupby([b["match_id"], b["innings"]]).shift(-1)
    # last ball of innings 1 -> WP at start of innings 2; last ball of a chase -> 1/0/0.5
    final = b["batting_team_won"]
    first_inn2 = wp_before[b["innings"].eq(2)].groupby(b["match_id"]).first()
    end1 = b["innings"].eq(1) & nxt.isna()
    nxt = nxt.where(~end1, 1 - b["match_id"].map(first_inn2))
    nxt = nxt.where(nxt.notna(), final)
    return nxt - wp_before


def stress_index(b: pd.DataFrame) -> pd.Series:
    """Transparent 0-100 situational-stress score (no model)."""
    stage = (b["legal_before"] / b["balls_avail"]).clip(0, 1)
    collapse = (b["wkts_last_24"] / 3).clip(0, 1)
    # wickets lost beyond what is normal at this point of an innings
    exp_wk = b.groupby([b["innings"], b["overid"]])["wkts_before"].transform("mean")
    wk_excess = ((b["wkts_before"] - exp_wk) / 3).clip(0, 1)

    # 2nd innings: difficulty rises with RRR up to ~12, then fades as the chase becomes a lost
    # cause (fully "dead" at RRR 18) - nobody is under pressure in a game already decided.
    difficulty = ((b["rrr"] - 6) / 6).clip(0, 1)
    alive = ((18 - b["rrr"]) / 5).clip(0, 1)
    wk2 = (b["wkts_before"] / 8).clip(0, 1)
    inn2 = (0.50 * difficulty + 0.30 * wk2 + 0.20 * collapse) * alive * (0.4 + 0.6 * stage)
    inn1 = (0.40 * wk_excess + 0.30 * collapse + 0.30 * stage) * 0.8  # setting a total: less direct pressure
    idx = np.where(b["innings"].eq(2), inn2, inn1)
    return pd.Series(100 * np.clip(idx, 0, 1), index=b.index)


def add_pressure(b: pd.DataFrame, wp: WinProb) -> pd.DataFrame:
    lev = leverage(b, wp)
    b = b.join(lev)
    b["leverage_index"] = b["exp_abs_swing"] / b["exp_abs_swing"].mean()
    b["stress_index"] = stress_index(b)
    b["stakes_pct"] = b["leverage_index"].rank(pct=True)
    b["stress_pct"] = b["stress_index"].rank(pct=True)
    b["pressure_score"] = (W_STAKES * b["stakes_pct"] + W_STRESS * b["stress_pct"]) * np.where(
        b["is_knockout"], KNOCKOUT_MULT, 1.0
    )
    b["pressure_pct"] = b["pressure_score"].rank(pct=True)
    b["pressure_band"] = pd.cut(b["pressure_pct"], [0, 0.5, 0.8, 1.0], labels=list(BANDS), include_lowest=True).astype(str)
    b["is_pressure"] = b["pressure_band"].eq("high")
    b["realised_swing"] = realised_swing(b, b["wp_before"])
    return b

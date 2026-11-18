"""Final Pressure Rating.

Five components, each z-scored within the ranking pool (eligible and active players). The weights in
brackets are the judgement weights; the weights actually used are ROLE_WEIGHTS below, set by
cross-validation (src/weight_cv.py): batters 53.75 / 23.75 / 0 / 17.5 / 5, bowlers 55 / 5 / 15 / 15 / 10.

  value        (43%)  Proven pressure performance: opposition-adjusted runs above average per
                      100 balls (batting) / per 120 balls (bowling), shrunk to the league mean
                      for sample size  [Phase 4: p_lg]
  consistency  (19%)  Share of pressure matches in which the player beat the average player
                      (opposition-adjusted value > 0), shrunk towards the pool rate
  clutch       (19%)  Rising above their own usual level: pressure minus baseline value,
                      empirical-Bayes shrunk using both standard errors
  impact       (14%)  Total win probability added in pressure situations (rewards repeatedly
                      deciding games, not just per-ball efficiency)
  volume        (5%)  Track record: how much pressure cricket the player has done, as the log of
                      weighted pressure balls (so doubling from 130 to 260 balls counts as much
                      as doubling from 260 to 520). A small bonus for having sustained a level
                      over many balls; its z-score is capped at +/-2 so no record dominates.

Recent-data nerf (outside the weights, in rating points): players with too little pressure cricket
in the last three seasons (2024, 2025, 2026) lose some rating. Each player's target per season is
the smaller of 50 pressure balls and their own average per season (total pressure balls divided by
the seasons from their first season in the data to the latest; e.g. 200 balls over 4 seasons -> 50).
In each recent season the shortfall below target (0 = at or above it, 1 = no pressure balls) is
squared, so a small dip costs little and an almost empty season costs a lot, then weighted
20% / 30% / 50%, so falling short in 2026 costs more than in 2025, and more than in 2024. Seasons
before a player's debut are not counted. The total deduction is at most RECENT_NERF["max_points"]
(0.40).

Data-driven rule: if the between-player spread of the clutch effect is not distinguishable
from noise (estimated true variance <= 0), the clutch component carries no information for
that role and its weight is redistributed proportionally to value, consistency and impact
(the track-record weight stays at 5%).
"""
import numpy as np
import pandas as pd

WEIGHTS = {"value": 0.43, "consistency": 0.19, "clutch": 0.19, "impact": 0.14, "volume": 0.05}


def _drop_clutch(w: dict) -> dict:
    """Share the clutch weight out to value, consistency and impact in proportion (track record keeps its weight)."""
    share = [k for k in w if k not in ("clutch", "volume")]
    total = sum(w[k] for k in share)
    out = {k: (v + w["clutch"] * v / total if k in share else v) for k, v in w.items()}
    out["clutch"] = 0.0
    return out


# Judgement weights per role, as used before cross-validation (batters: clutch failed the noise test).
JUDGEMENT_WEIGHTS = {"bat": _drop_clutch(WEIGHTS), "bowl": dict(WEIGHTS)}

# Cross-validated weights (src/weight_cv.py; 5-fold x 10 repeats grouped by match, scored on how well the rating
# picks out the players who perform under pressure in held-out matches; full results in
# outputs/tables/p8_weight_cv.md and phase8_weights.json):
#   batters  no weighting does clearly better than any other (held-out r 0.03 for the judgement weights, best
#            0.06, difference well inside one standard error), so the judgement weights stand.
#   bowlers  the judgement weights were clearly beaten by giving value more weight (r 0.154 v 0.198 for value
#            alone, about 1.5 standard errors). The weights below are the combination closest to the judgement
#            weights that is not clearly worse than the best: value up, consistency down.
CV_WEIGHTS = {
    "bat": dict(JUDGEMENT_WEIGHTS["bat"]),
    "bowl": {"value": 0.55, "consistency": 0.05, "clutch": 0.15, "impact": 0.15, "volume": 0.10},
}
USE_CV_WEIGHTS = True
ROLE_WEIGHTS = CV_WEIGHTS if USE_CV_WEIGHTS else JUDGEMENT_WEIGHTS
VOLUME_Z_CAP = 2.0
RECENT_NERF = {"max_points": 0.40, "year_weights": (0.2, 0.3, 0.5), "target_cap": 50, "power": 2}
REQUIRE_ACTIVE = True       # only players who appeared in 2025-26 (selection exercise)
MIN_MATCH_BALLS = {"bat": 5, "bowl": 6}   # a "pressure match" = at least this many pressure balls
CONSISTENCY_PRIOR_MATCHES = 10            # beta-prior strength for the success rate


def clutch_delta(r: pd.DataFrame, scale: int, info: dict, fixed: dict | None = None) -> pd.DataFrame:
    raw = r[f"p_adj{scale}"] - r[f"b_adj{scale}"]
    se2 = r[f"p_se{scale}"] ** 2 + r[f"b_se{scale}"] ** 2
    ok = (r["p_n"] >= 30) & raw.notna() & se2.notna()
    mu = np.average(raw[ok], weights=r.loc[ok, "p_n_w" if "p_n_w" in r else "p_n"])
    var_obs, noise = float(np.var(raw[ok])), float(se2[ok].mean())
    tau2 = var_obs - noise
    if fixed:  # hold hyperparameters at full-sample values (bootstrap)
        mu, tau2 = fixed["clutch_mean"], fixed["clutch_tau2"]
    info.update(clutch_var_observed=var_obs, clutch_var_noise=noise, clutch_tau2=tau2, clutch_mean=mu)
    w = tau2 / (tau2 + se2) if tau2 > 0 else 0.0 * se2
    r["clutch_raw"] = raw
    r["clutch_t"] = (raw - mu) / np.sqrt(se2)  # evidence of over-performing own baseline
    r["clutch_weight"] = w
    r["clutch"] = mu + w * (raw - mu)
    return r


def consistency(r: pd.DataFrame, matches: pd.DataFrame, role: str, pool_ids: pd.Series, info: dict,
                fixed: dict | None = None) -> pd.DataFrame:
    m = matches[matches["balls"] >= MIN_MATCH_BALLS[role]]
    w = m["match_w"] if "match_w" in m else pd.Series(1.0, index=m.index)
    win = (m["value_adj"] > 0).astype(int)
    m = m.assign(_s=win, _w=w, _sw=win * w)
    g = m.groupby("player_id")
    t = pd.DataFrame({"pm_n": g.size(), "pm_success": g["_s"].sum(),
                      "pm_n_w": g["_w"].sum(), "pm_success_w": g["_sw"].sum()})
    cols = list(t.columns)
    r = r.drop(columns=[c for c in cols if c in r]).merge(t, left_on="player_id", right_index=True, how="left")
    r[cols] = r[cols].fillna(0)
    in_pool = r["player_id"].isin(pool_ids)
    r0 = fixed["pool_success_rate"] if fixed else r.loc[in_pool, "pm_success_w"].sum() / r.loc[in_pool, "pm_n_w"].sum()
    M = CONSISTENCY_PRIOR_MATCHES
    r["success_rate"] = r["pm_success"] / r["pm_n"].replace(0, np.nan)          # raw, for display
    r["success_rate_w"] = r["pm_success_w"] / r["pm_n_w"].replace(0, np.nan)    # evidence-weighted
    # weighted successes, shrunk towards the pool rate with M pseudo-matches
    r["consistency"] = (r["pm_success_w"] + M * r0) / (r["pm_n_w"] + M)
    info["pool_success_rate"] = r0
    return r


def recent_nerf(r: pd.DataFrame, matches: pd.DataFrame, info: dict, fixed: dict | None = None,
                cfg: dict | None = RECENT_NERF) -> pd.DataFrame:
    """Small deduction when a player's pressure balls in the last three seasons fall short of their
    own average per season (see module docstring)."""
    ymax = int(matches["year"].max())
    years = [ymax - 2, ymax - 1, ymax]
    by_year = matches.groupby(["player_id", "year"])["balls"].sum().unstack(fill_value=0)
    first = by_year.gt(0).idxmax(axis=1)                       # first season with pressure balls
    seasons = (ymax - first + 1).clip(lower=1)
    own_avg = by_year.sum(axis=1) / seasons                      # own average pressure balls per season
    c = cfg or RECENT_NERF
    target = own_avg.clip(upper=c.get("target_cap", np.inf))      # never more than 50 a season
    r["recent_avg"] = r["player_id"].map(own_avg).fillna(0)
    r["recent_target"] = r["player_id"].map(target).fillna(0)
    r["recent_seasons"] = r["player_id"].map(seasons).fillna(0)
    short = pd.Series(0.0, index=r.index)
    for i, (y, yw) in enumerate(zip(years, (cfg or RECENT_NERF)["year_weights"])):
        balls = r["player_id"].map(by_year[y] if y in by_year else pd.Series(dtype=float)).fillna(0)
        r[f"recent_balls_{i}"] = balls                           # 0 = two seasons ago, 2 = latest season
        expected = r["player_id"].map(first).le(y) & (r["recent_target"] > 0)   # not before debut
        gap = (1 - balls / r["recent_target"].replace(0, np.nan)).clip(0, 1).fillna(0) ** c.get("power", 1)
        short += yw * gap.where(expected, 0.0)
    r["recent_shortfall"] = short
    r["contrib_recent"] = -(cfg["max_points"] if cfg else 0.0) * short
    info["recent_years"] = years
    return r


# Which Phase 4 pressure estimate feeds 'value'.
#   bowlers  p_shrunk: pressure record shrunk towards what the bowler's normal form predicts. The
#            Phase 6 predictive check found it predicts unseen pressure bowling about twice as well.
#   batters  "blend": 75% p_lg (pressure record shrunk to the league average), 25% p_shrunk (shrunk
#            towards what the batter's normal form predicts). For batters no estimate predicts
#            pressure batting well, so the pressure record alone (p_lg) let poor normal-form batters
#            with good pressure numbers rank highly; the 75/25 blend keeps the pressure record
#            central but counts normal form too. BLEND_SHARE is the p_shrunk share.
VALUE_SOURCE = {"bat": "blend", "bowl": "p_shrunk"}
BLEND_SHARE = 0.25


def rate(r: pd.DataFrame, matches: pd.DataFrame, role: str, weights: dict | None = None,
         value_source: str | None = None, fixed: dict | None = None,
         nerf: dict | None = RECENT_NERF) -> tuple[pd.DataFrame, dict]:
    """weights: if given, used as-is (no clutch redistribution) - for bootstrap / sensitivity runs.
    value_source: 'p_lg' (pressure record shrunk to league mean), 'p_shrunk' (shrunk towards a
    prior predicted from the player's own baseline) or 'blend' (BLEND_SHARE of p_shrunk, the rest
    p_lg); defaults to VALUE_SOURCE[role]."""
    scale = 100 if role == "bat" else 120
    info: dict = {}
    r = r.copy()
    r["in_pool"] = r["eligible"] & (r["active"] if REQUIRE_ACTIVE else True)
    r = clutch_delta(r, scale, info, fixed)
    r = consistency(r, matches, role, r.loc[r["in_pool"], "player_id"], info, fixed)
    src = value_source or VALUE_SOURCE[role]
    if src == "blend":
        r[f"blend{scale}"] = (1 - BLEND_SHARE) * r[f"p_lg{scale}"] + BLEND_SHARE * r[f"p_shrunk{scale}"]
    r["value"] = r[f"{src}{scale}"]
    info["value_source"] = src
    r["impact"] = r["p_wpa_w"] if "p_wpa_w" in r else r["p_wpa_total"]
    n_vol = r["p_n_w"] if "p_n_w" in r else r["p_n"]
    r["volume"] = np.log(n_vol.clip(lower=1))

    given = weights is not None
    weights = dict(weights if given else ROLE_WEIGHTS[role])
    if not given and info["clutch_tau2"] <= 0 and weights.get("clutch", 0) > 0:
        weights = _drop_clutch(weights)
    info["weights_used"] = weights

    pool = r[r["in_pool"]]
    for c in WEIGHTS:
        sd = pool[c].std()
        r[f"z_{c}"] = (r[c] - pool[c].mean()) / sd if sd > 1e-9 else 0.0
        if c == "volume":
            r[f"z_{c}"] = r[f"z_{c}"].clip(-VOLUME_Z_CAP, VOLUME_Z_CAP)
        r[f"contrib_{c}"] = weights.get(c, 0.0) * r[f"z_{c}"]
    r = recent_nerf(r, matches, info, fixed, nerf)
    r["rating"] = sum(r[f"contrib_{c}"] for c in WEIGHTS) + r["contrib_recent"]
    r["rank"] = r["rating"].where(r["in_pool"]).rank(ascending=False, method="first")
    return r.sort_values("rank"), info

"""Fair comparison: opposition quality, sample-size shrinkage and eligibility.

1. Opposition quality (ridge "batter vs bowler" model)
   Per-ball batting value (already context-adjusted) is modelled as
       value = batter effect + bowler effect + tier of bowling side + tier of batting side
   with ridge penalties on player effects (players with few balls are pulled to average) and
   team-tier dummies (Associate / A-team vs Full member / IPL) so that weak attacks are recognised
   even when their individual bowlers have small samples. Each ball's value is then corrected
   for the specific opponent: a batter facing Bumrah gets credit, one facing a debutant
   associate bowler gets less.

2. Empirical-Bayes shrinkage
   A player's adjusted pressure value per ball is shrunk towards a *prior* according to how
   many pressure balls they have:   shrunk = prior + n / (n + k) x (observed - prior)
   k = within-player ball variance / between-player true variance (method of moments).
   Prior for pressure = what their (shrunk) baseline predicts for pressure, so with little
   evidence we assume a player performs under pressure as they normally do.

3. Evidence weights (how much each ball counts towards a player's rating)
   Three mild factors, multiplied:
     recency      each year further back counts a little less (10% per year: 2022 ~ 0.62 of late 2026)
     competition  IPL balls count fully, and so do T20Is against the five strongest T20 nations
                  (India, Australia, England, South Africa, New Zealand); T20Is against any other
                  side count 0.8 (this is an IPL selection exercise)
     opponent     facing an IPL-standard attack / line-up counts fully, an associate-standard one
                  half; nations in between by their strength measured in the opposition model
   Volume needs no extra factor: aggregates are sums over balls, so a season with more balls
   carries proportionally more weight. All player aggregates (per-ball values, win probability
   added, match success rates) use the weights, and the sum of weights is the player's amount of
   relevant evidence for shrinkage: a record built mostly against weak sides or outside the IPL
   is trusted less and pulled further towards the prior. Eligibility still uses raw ball counts.

4. Eligibility: minimum pressure balls and innings/matches with pressure exposure.
"""
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

FULL_MEMBERS = {"India", "Australia", "England", "South Africa", "New Zealand", "Pakistan", "Sri Lanka",
                "West Indies", "Bangladesh", "Afghanistan", "Zimbabwe", "Ireland"}
ALPHAS = [30, 100, 300, 1000, 3000]

ELIG = {"bat": {"min_p_balls": 100, "min_p_games": 15}, "bowl": {"min_p_balls": 120, "min_p_games": 15}}
ACTIVE_FROM_YEAR = 2025

# Evidence weights (see 3. above). None anywhere switches that factor off; WEIGHTING = None
# switches all weighting off (every ball counts equally, the original method).
#   recency_decay  share of weight lost per year of age, measured back from the last match
#   comp           weight by competition; "T20I_strong" applies to T20Is against STRONG_T20I_TEAMS
#   opponent       (weight vs an associate-standard side, weight vs an IPL-standard side)
STRONG_T20I_TEAMS = ("India", "Australia", "England", "South Africa", "New Zealand")
WEIGHTING = {"recency_decay": 0.10, "comp": {"IPL": 1.0, "T20I": 0.80, "T20I_strong": 1.0},
             "strong_t20i_teams": STRONG_T20I_TEAMS, "opponent": (0.5, 1.0)}
OPP_MIN_BALLS = 600   # teams faced less often than this use their tier's average strength


def recency_factor(dates: pd.Series, decay: float | None, ref_date=None) -> pd.Series:
    """(1 - decay) ** age, age in years before ref_date (default: latest date in `dates`)."""
    if not decay:
        return pd.Series(1.0, index=dates.index)
    d = pd.to_datetime(dates, format="%Y-%m-%d")
    ref = pd.Timestamp(ref_date) if ref_date is not None else d.max()
    age = (ref - d).dt.days.clip(lower=0) / 365.25
    return (1 - decay) ** age


def opponent_strength(b: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Strength of every opposition side on a 0-1 scale, per role, from the opposition model.

    For batters the opposition is the bowling side: its average opp_help_batter (how much easier
    than average its bowlers made batting). For bowlers it is the batting side. 1 = the average
    IPL side, 0 = the average associate side, clipped to [0, 1]."""
    r = b[b["comp_tier"].isin(RATING_TIERS)]
    out = {}
    for role, team, tier, helpc, mask in (("bat", "bowling_team_id", "bowl_tier", "opp_help_batter", r["is_batter_ball"]),
                                          ("bowl", "batting_team_id", "bat_tier", "opp_help_bowler", r["is_legal"])):
        d = r[mask]
        t = d.groupby(team).agg(n=(helpc, "size"), help=(helpc, "mean"), tier=(tier, "first"))
        tier_mean = d.groupby(tier)[helpc].mean()
        t["help_used"] = t["help"].where(t["n"] >= OPP_MIN_BALLS, t["tier"].map(tier_mean))
        a_ipl, a_assoc = tier_mean["IPL"], tier_mean["Associate"]
        t["strength"] = ((a_assoc - t["help_used"]) / (a_assoc - a_ipl)).clip(0, 1)
        out[role] = t
    return out


def ball_weight(b: pd.DataFrame, role: str, weighting: dict | None = WEIGHTING, ref_date=None) -> pd.Series:
    """Evidence weight of each ball for `role` (see WEIGHTING). Needs opp_str_bat / opp_str_bowl
    (opponent factor) and strong_opp_bat / strong_opp_bowl (T20I against a strong nation) columns,
    written by Phase 4."""
    w = pd.Series(1.0, index=b.index)
    if not weighting:
        return w
    if weighting.get("recency_decay"):
        w = w * recency_factor(b["match_date"], weighting["recency_decay"], ref_date)
    col = f"opp_str_{role}"
    if weighting.get("comp"):
        comp = weighting["comp"]
        f = b["comp_tier"].map({k: v for k, v in comp.items() if k != "T20I_strong"}).fillna(1.0)
        flag = f"strong_opp_{role}"
        if "T20I_strong" in comp and flag in b:
            strong = b["comp_tier"].eq("T20I") & b[flag].fillna(False).astype(bool)
            f = f.where(~strong, comp["T20I_strong"])
        w = w * f
    if weighting.get("opponent") and col in b:
        lo, hi = weighting["opponent"]
        w = w * (lo + (hi - lo) * b[col].fillna(1.0))
    return w


def season_par_adjust(b: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Measure every ball against the par of its own competition and season.

    The Phase 3 expectation models are fitted on all seasons together, so league-wide scoring
    drift (e.g. IPL run rates rising after 2023) shows up as batters 'beating par' and bowlers
    'losing to par' in recent seasons. Subtracting each competition-season's average makes the
    average batter and bowler of every competition-season worth exactly 0:
      batting: mean bat_value per batter ball
      bowling: total bowl_value per legal ball (wides/no-balls are charged to the bowler but
               the per-ball rate is per legal delivery), subtracted on legal balls
    Returns (adjusted balls, table of the offsets removed)."""
    key = [b["comp_tier"], b["year"]]
    bat_par = b["bat_value"].where(b["is_batter_ball"]).groupby(key).transform("mean").fillna(0)
    bowl_tot = b["bowl_value"].groupby(key).transform("sum")
    legal_n = b["is_legal"].astype(int).groupby(key).transform("sum")
    bowl_par = (bowl_tot / legal_n.replace(0, np.nan)).fillna(0)
    b = b.assign(bat_value=b["bat_value"] - bat_par.where(b["is_batter_ball"], 0.0),
                 bowl_value=b["bowl_value"] - bowl_par.where(b["is_legal"], 0.0))
    offsets = pd.DataFrame({"bat_par_per100": bat_par * 100, "bowl_par_per120": bowl_par * 120,
                            "comp_tier": b["comp_tier"], "year": b["year"]}
                           ).groupby(["comp_tier", "year"]).first().round(2)
    return b, offsets


def team_tier(name: str, ipl_teams: set) -> str:
    if name in ipl_teams:
        return "IPL"
    if name in FULL_MEMBERS:
        return "Full"
    if name.endswith(" A"):
        return "A-team"
    return "Associate"


def _design(d: pd.DataFrame):
    bat_ids = pd.Index(d["striker_id"].unique())
    bowl_ids = pd.Index(d["bowler_id"].unique())
    n = len(d)
    rows = np.arange(n)
    Xb = sparse.csr_matrix((np.ones(n), (rows, bat_ids.get_indexer(d["striker_id"]))), shape=(n, len(bat_ids)))
    Xw = sparse.csr_matrix((np.ones(n), (rows, bowl_ids.get_indexer(d["bowler_id"]))), shape=(n, len(bowl_ids)))
    tiers = ["Associate", "A-team"]
    T = np.column_stack([d["bowl_tier"].eq(t).values for t in tiers] + [d["bat_tier"].eq(t).values for t in tiers])
    # Tier dummies get a larger scale so the shared ridge penalty barely shrinks them.
    Xt = sparse.csr_matrix(T.astype(float) * 10)
    tier_names = [f"bowling_side_{t}" for t in tiers] + [f"batting_side_{t}" for t in tiers]
    return sparse.hstack([Xb, Xw, Xt]).tocsr(), bat_ids, bowl_ids, tier_names


def opposition_model(b: pd.DataFrame) -> dict:
    d = b[b["is_batter_ball"]]
    X, bat_ids, bowl_ids, tier_names = _design(d)
    y = d["bat_value"].values
    cv = {}
    for a in ALPHAS:
        err = []
        for tr, te in GroupKFold(5).split(X, y, d["match_id"]):
            m = Ridge(alpha=a).fit(X[tr], y[tr])
            err.append(np.mean((y[te] - m.predict(X[te])) ** 2))
        cv[a] = np.mean(err)
    alpha = min(cv, key=cv.get)
    m = Ridge(alpha=alpha).fit(X, y)
    nb, nw = len(bat_ids), len(bowl_ids)
    coef = m.coef_
    return {
        "alpha": alpha, "cv_mse": cv,
        "batter_effect": pd.Series(coef[:nb], index=bat_ids),            # + = better batter
        "bowler_effect": pd.Series(coef[nb:nb + nw], index=bowl_ids),    # - = better bowler
        "tier_effect": pd.Series(coef[nb + nw:] * 10, index=tier_names),  # runs per ball
    }


def apply_opposition(b: pd.DataFrame, om: dict) -> pd.DataFrame:
    te = om["tier_effect"]
    bowl_side = b["bowl_tier"].map({"Associate": te["bowling_side_Associate"], "A-team": te["bowling_side_A-team"]}).fillna(0)
    bat_side = b["bat_tier"].map({"Associate": te["batting_side_Associate"], "A-team": te["batting_side_A-team"]}).fillna(0)
    # how much the opposition helped (+) or hurt (-) the batter on this ball
    b["opp_help_batter"] = b["bowler_id"].map(om["bowler_effect"]).fillna(0) + bowl_side
    # how much the opposition helped (+) or hurt (-) the bowler on this ball
    b["opp_help_bowler"] = -(b["striker_id"].map(om["batter_effect"]).fillna(0) + bat_side)
    b["bat_value_adj"] = b["bat_value"] - b["opp_help_batter"]
    b["bowl_value_adj"] = b["bowl_value"] - b["opp_help_bowler"]
    return b


def eb_shrink(n: pd.Series, mean: pd.Series, prior: pd.Series, sigma2: float, min_n: int = 30,
              k: float | None = None, n_var: pd.Series | None = None):
    """Empirical-Bayes shrinkage of per-ball means towards a prior. Returns (shrunk, weight, k).
    n: amount of evidence (sum of ball weights) - sets the weight on the player's own record.
    n_var: effective sample size of the weighted mean, for its sampling variance when estimating
    k (default n). If k is given (e.g. held fixed in a bootstrap), it is used instead."""
    if k is not None:
        weight = n / (n + k)
        return prior + weight * (mean - prior).fillna(0), weight, k
    n_var = n if n_var is None else n_var
    ok = n >= min_n
    resid = (mean - prior)[ok]
    w = n[ok]
    var_obs = np.average(resid ** 2, weights=w) - np.average(resid, weights=w) ** 2
    tau2 = max(var_obs - np.average(sigma2 / n_var[ok], weights=w), 1e-6)
    k = sigma2 / tau2
    weight = n / (n + k)
    return prior + weight * (mean - prior).fillna(0), weight, k


RATING_TIERS = ("IPL", "T20I")  # brief's scope; A-team "Emerging" events are used for models only


HYPER_KEYS = ("b_sigma2", "p_sigma2", "league_b", "b_k", "prior_alpha", "prior_beta", "p_k", "league_p", "p_k_lg",
              "ref_date")


def player_ratings(b: pd.DataFrame, role: str, hyper: dict | None = None,
                   weighting: dict | None = WEIGHTING, ref_date=None) -> tuple[pd.DataFrame, dict]:
    """hyper: shrinkage hyperparameters (HYPER_KEYS) to hold fixed instead of estimating them -
    used by the bootstrap, where re-estimating them on resampled data inflates the apparent
    between-player variance and so under-shrinks.
    weighting: evidence weights (WEIGHTING; None = every ball counts equally).
    ref_date: date that recency is measured back from (default: last match in `b`).

    Columns: {s}_n / {s}_games are raw counts (used for eligibility); {s}_n_w is the weighted
    ball count (sum of weights: the denominator of the per-ball values and the amount of evidence
    used for shrinkage); {s}_n_eff is the effective sample size of the weighted mean,
    (sum w)^2 / sum w^2, used for its standard error. All three equal {s}_n when weighting is off."""
    h = hyper or {}
    b = b[b["comp_tier"].isin(RATING_TIERS)]
    ref_date = ref_date if ref_date is not None else h.get("ref_date", b["match_date"].max())
    b = b.assign(_rw=ball_weight(b, role, weighting, ref_date))
    if role == "bat":
        d = b[b["is_batter_ball"]].assign(_opp=lambda x: x["opp_help_batter"], _wpa=lambda x: x["wpa_all"])
        id_col, val, games = "striker_id", "bat_value_adj", "match_id"
        n_mask = pd.Series(True, index=d.index)
    else:
        d = b.assign(_opp=lambda x: x["opp_help_bowler"], _wpa=lambda x: -x["wpa_all"])
        id_col, val, games = "bowler_id", "bowl_value_adj", "match_id"
        n_mask = d["is_legal"]
    w = d["_rw"]
    g = d.assign(seg=np.where(d["is_pressure"], "p", "b"), _n=n_mask.astype(int), _nw=n_mask * w, _nw2=n_mask * w * w,
                 _adj=d[val] * w, _raw=d[val.replace("_adj", "")] * w, _oppw=d["_opp"] * w,
                 _wpaw=d["_wpa"] * w).groupby([id_col, "seg"])
    t = pd.DataFrame({
        "n": g["_n"].sum(), "nw": g["_nw"].sum(), "nw2": g["_nw2"].sum(), "adj": g["_adj"].sum(), "raw": g["_raw"].sum(),
        "opp": g["_oppw"].sum(), "games": g[games].nunique(), "wpa": g["_wpa"].sum(), "wpaw": g["_wpaw"].sum(),
    }).unstack("seg").fillna(0)
    t.columns = [f"{s}_{c}" for c, s in t.columns]

    info = {}
    out = pd.DataFrame(index=t.index)
    for s in ("b", "p"):
        n = t[f"{s}_nw"].replace(0, np.nan)
        out[f"{s}_n"] = t[f"{s}_n"]
        out[f"{s}_n_w"] = t[f"{s}_nw"]
        out[f"{s}_n_eff"] = (t[f"{s}_nw"] ** 2 / t[f"{s}_nw2"].replace(0, np.nan)).fillna(0)
        out[f"{s}_games"] = t[f"{s}_games"]
        out[f"{s}_wpa_total"] = t[f"{s}_wpa"]      # raw total
        out[f"{s}_wpa_w"] = t[f"{s}_wpaw"]         # weighted (feeds the impact component)
        out[f"{s}_raw_pb"] = t[f"{s}_raw"] / n
        out[f"{s}_adj_pb"] = t[f"{s}_adj"] / n
        out[f"{s}_opp_pb"] = t[f"{s}_opp"] / n
        part = d[d["is_pressure"].eq(s == "p")]
        info[f"{s}_sigma2"] = h.get(f"{s}_sigma2", float(part[val].var()))

    # baseline: shrink towards the (ball-weighted) league mean
    league_b = h.get("league_b", np.average(out["b_adj_pb"].fillna(0), weights=out["b_n_w"]))
    out["b_shrunk_pb"], out["b_weight"], info["b_k"] = eb_shrink(
        out["b_n_w"], out["b_adj_pb"], pd.Series(league_b, index=out.index), info["b_sigma2"], k=h.get("b_k"),
        n_var=out["b_n_eff"])
    info["league_b"] = league_b

    # pressure: prior = linear prediction from shrunk baseline (fitted on players with >= 30 pressure balls)
    fit = out[out["p_n"] >= 30]
    if "prior_alpha" in h:
        alpha, beta = h["prior_alpha"], h["prior_beta"]
    else:
        beta, alpha = np.polyfit(fit["b_shrunk_pb"], fit["p_adj_pb"], 1, w=np.sqrt(fit["p_n_w"]))
    out["p_prior_pb"] = alpha + beta * out["b_shrunk_pb"]
    out["p_shrunk_pb"], out["p_weight"], info["p_k"] = eb_shrink(
        out["p_n_w"], out["p_adj_pb"], out["p_prior_pb"], info["p_sigma2"], k=h.get("p_k"), n_var=out["p_n_eff"])
    out["delta_shrunk_pb"] = out["p_shrunk_pb"] - out["b_shrunk_pb"]
    info.update(prior_alpha=alpha, prior_beta=beta)

    # pressure, shrunk towards the league pressure mean: the player's own pressure record drives
    # the estimate, discounted only for sample size (the primary input to the Phase 5 rating)
    league_p = h.get("league_p", np.average(out["p_adj_pb"].fillna(0), weights=out["p_n_w"]))
    out["p_lg_pb"], out["p_weight_lg"], info["p_k_lg"] = eb_shrink(
        out["p_n_w"], out["p_adj_pb"], pd.Series(league_p, index=out.index), info["p_sigma2"], k=h.get("p_k_lg"),
        n_var=out["p_n_eff"])
    info["league_p"] = league_p
    # standard error of the observed adjusted pressure mean (for significance of over-performance)
    out["p_se_pb"] = np.sqrt(info["p_sigma2"] / out["p_n_eff"].replace(0, np.nan))
    out["b_se_pb"] = np.sqrt(info["b_sigma2"] / out["b_n_eff"].replace(0, np.nan))
    # how much of the pressure record counts after weighting (1 = every ball recent, IPL, strong opponent)
    out["p_evidence_share"] = out["p_n_w"] / out["p_n"].replace(0, np.nan)
    info.update(ref_date=ref_date, weighting=weighting)

    # tier mix, IPL-only pressure record (unweighted), average opponent strength
    pd_ = d[d["is_pressure"] & n_mask]
    mix = pd.crosstab(pd_[id_col], pd_["comp_tier"], normalize="index")
    for c in ("IPL", "T20I", "Emerging"):
        out[f"p_share_{c}"] = mix.get(c, pd.Series(dtype=float)).reindex(out.index).fillna(0)
    dn = d.assign(_n=n_mask.astype(int))
    gi = dn[dn["is_pressure"] & dn["comp_tier"].eq("IPL")].groupby(id_col)
    out["p_ipl_n"] = gi["_n"].sum().reindex(out.index).fillna(0)
    out["p_ipl_adj_pb"] = gi[val].sum().reindex(out.index) / out["p_ipl_n"].replace(0, np.nan)
    if f"opp_str_{role}" in d:
        out["p_opp_strength"] = d[d["is_pressure"]].groupby(id_col)[f"opp_str_{role}"].mean().reindex(out.index)
    out["last_year"] = d.groupby(id_col)["year"].max()

    scale = 100 if role == "bat" else 120
    for c in [c for c in out.columns if c.endswith("_pb")]:
        out[c.replace("_pb", str(scale))] = out.pop(c) * scale

    e = ELIG[role]
    out["eligible"] = (out["p_n"] >= e["min_p_balls"]) & (out["p_games"] >= e["min_p_games"])
    out["active"] = out["last_year"] >= ACTIVE_FROM_YEAR
    return out.reset_index().rename(columns={id_col: "player_id"}), info


def adjusted_per_match(b: pd.DataFrame, role: str, weighting: dict | None = WEIGHTING,
                       ref_date=None) -> pd.DataFrame:
    """Opposition-adjusted pressure value per player per match, with the match's evidence weight
    (recency x competition x opponent: constant within a match for a given player)."""
    b = b[b["comp_tier"].isin(RATING_TIERS)]
    ref_date = ref_date if ref_date is not None else b["match_date"].max()
    b = b.assign(_w=ball_weight(b, role, weighting, ref_date))
    if role == "bat":
        d = b[b["is_batter_ball"] & b["is_pressure"]]
        g = d.groupby(["striker_id", "match_id"])
        t = pd.DataFrame({"balls": g.size(), "value_adj": g["bat_value_adj"].sum(), "wpa": g["wpa_all"].sum(),
                          "match_w": g["_w"].mean()})
    else:
        d = b[b["is_pressure"]]
        g = d.groupby(["bowler_id", "match_id"])
        t = pd.DataFrame({"balls": g["is_legal"].sum(), "value_adj": g["bowl_value_adj"].sum(), "wpa": -g["wpa_all"].sum(),
                          "match_w": g["_w"].mean()})
    t.index = t.index.set_names(["player_id", "match_id"])
    ctx = b.groupby("match_id")[["match_date", "year", "comp_tier", "is_knockout"]].first()
    return t.reset_index().merge(ctx, on="match_id", how="left")

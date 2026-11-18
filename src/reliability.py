"""Reliability checks for the Pressure Ratings.

All checks re-use the Phase 4 aggregation (fairness.player_ratings / adjusted_per_match) and the
Phase 5 rating (rating.rate) on modified ball-level data, so they test exactly the method used
for the final lists. Ball-level values and opposition effects are held fixed (the models are
not refitted), so the checks measure sampling and definitional uncertainty in the ratings.

1. Bootstrap by match   - resample matches with replacement, re-rate (shrinkage
                          hyperparameters held at full-sample values), collect rank ranges
2. Split-half           - random halves of matches: does pressure performance in one half
                          predict the other? (vs the same test for baseline performance)
3. Temporal split       - 2022-23 vs 2024-26
4. Sensitivity          - alternative pressure definitions, rating weights and recency half-lives

Split-half and temporal checks ask whether pressure performance is a stable trait, so they use
unweighted records (weighting=None); the bootstrap and sensitivity runs use the rating's own
evidence weights.
"""
import numpy as np
import pandas as pd

from fairness import WEIGHTING, adjusted_per_match, player_ratings
from rating import rate

SCALE = {"bat": 100, "bowl": 120}


def run_ratings(b: pd.DataFrame, weights: dict[str, dict], hyper: dict | None = None,
                weighting="default", ref_date=None) -> dict[str, pd.DataFrame]:
    """hyper: {role: {"fair": Phase 4 hyperparameters, "rate": Phase 5 hyperparameters}} to hold fixed.
    weighting: evidence weights to use instead of the rating's own (None = unweighted).
    ref_date: date recency is measured back from (default: hyper's, else the last match in b)."""
    out = {}
    for role in ("bat", "bowl"):
        h = (hyper or {}).get(role, {})
        wt = WEIGHTING if weighting == "default" else weighting
        ref = ref_date if ref_date is not None else (h.get("fair") or {}).get("ref_date")
        r, _ = player_ratings(b, role, hyper=h.get("fair"), weighting=wt, ref_date=ref)
        pm = adjusted_per_match(b, role, weighting=wt, ref_date=ref)
        out[role], _ = rate(r, pm, role, weights=weights[role], fixed=h.get("rate"))
    return out


def hyperparameters(info_fair: dict, info_rate: dict) -> dict:
    from fairness import HYPER_KEYS
    return {"fair": {k: info_fair[k] for k in HYPER_KEYS},
            "rate": {k: info_rate[k] for k in ("clutch_mean", "clutch_tau2", "pool_success_rate")}}


# ---------------------------------------------------------------- bootstrap
class MatchResampler:
    def __init__(self, b: pd.DataFrame, seed: int = 42):
        self.b = b.reset_index(drop=True)
        self.groups = self.b.groupby("match_id").indices
        self.mids = np.array(list(self.groups))
        self.rng = np.random.default_rng(seed)

    def sample(self) -> pd.DataFrame:
        draw = self.rng.choice(self.mids, size=len(self.mids), replace=True)
        idx = [self.groups[m] for m in draw]
        rows = np.concatenate(idx)
        new_id = np.repeat(np.arange(len(draw)), [len(i) for i in idx])  # repeated matches count separately
        return self.b.iloc[rows].assign(match_id=new_id)


def bootstrap(b: pd.DataFrame, weights: dict, n_reps: int, hyper: dict | None = None, seed: int = 42,
              log_every: int = 25) -> dict[str, pd.DataFrame]:
    """Shrinkage hyperparameters should be held fixed (hyper): re-estimating them on resampled
    data adds the resampling noise to the apparent between-player variance, so replicates
    under-shrink and the rank ranges are biased towards raw pressure records."""
    rs = MatchResampler(b, seed)
    ranks = {"bat": [], "bowl": []}
    for i in range(n_reps):
        res = run_ratings(rs.sample(), weights, hyper)
        for role in ranks:
            ranks[role].append(res[role].set_index("player_id")["rank"].rename(i))
        if log_every and (i + 1) % log_every == 0:
            print(f"  bootstrap {i + 1}/{n_reps}", flush=True)
    out = {}
    for role, cols in ranks.items():
        R = pd.concat(cols, axis=1)  # NaN = not in the ranking pool in that replicate
        out[role] = pd.DataFrame({
            "median_rank": R.median(axis=1),
            "rank_p05": R.quantile(0.05, axis=1),
            "rank_p95": R.quantile(0.95, axis=1),
            "p_top5": (R <= 5).sum(axis=1) / n_reps,
            "p_top10": (R <= 10).sum(axis=1) / n_reps,
            "p_top20": (R <= 20).sum(axis=1) / n_reps,
            "p_in_pool": R.notna().sum(axis=1) / n_reps,
        })
    return out


# ---------------------------------------------------------------- split-half
def _half_stats(b: pd.DataFrame, role: str) -> pd.DataFrame:
    r, _ = player_ratings(b, role, weighting=None)
    s = SCALE[role]
    return r.set_index("player_id")[["p_n", "b_n", f"p_adj{s}", f"b_adj{s}", f"p_lg{s}"]].rename(
        columns={f"p_adj{s}": "p_adj", f"b_adj{s}": "b_adj", f"p_lg{s}": "p_lg"})


def _half_corr(h1: pd.DataFrame, h2: pd.DataFrame, min_p: int, min_b: int) -> dict:
    j = h1.join(h2, lsuffix="_1", rsuffix="_2", how="inner")
    jp = j[(j.p_n_1 >= min_p) & (j.p_n_2 >= min_p)]
    jb = j[(j.b_n_1 >= min_b) & (j.b_n_2 >= min_b)]
    jc = j[(j.p_n_1 >= min_p) & (j.p_n_2 >= min_p) & (j.b_n_1 >= min_b) & (j.b_n_2 >= min_b)]
    return {
        "n_players_pressure": len(jp),
        "r_pressure": jp.p_adj_1.corr(jp.p_adj_2),
        "n_players_baseline": len(jb),
        "r_baseline": jb.b_adj_1.corr(jb.b_adj_2),
        "r_clutch": (jc.p_adj_1 - jc.b_adj_1).corr(jc.p_adj_2 - jc.b_adj_2),
        "r_pressure_vs_other_half_baseline": jc.p_adj_1.corr(jc.b_adj_2),
    }


def split_half(b: pd.DataFrame, n_splits: int, min_p: dict, min_b: dict, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mids = b["match_id"].unique()
    rows = []
    for i in range(n_splits):
        half = set(rng.choice(mids, size=len(mids) // 2, replace=False))
        m = b["match_id"].isin(half)
        for role in ("bat", "bowl"):
            c = _half_corr(_half_stats(b[m], role), _half_stats(b[~m], role), min_p[role], min_b[role])
            rows.append({"split": i, "role": role, **c})
    return pd.DataFrame(rows)


def temporal_split(b: pd.DataFrame, min_p: dict, min_b: dict, cut_year: int = 2024) -> pd.DataFrame:
    early, late = b["year"] < cut_year, b["year"] >= cut_year
    rows = []
    for role in ("bat", "bowl"):
        c = _half_corr(_half_stats(b[early], role), _half_stats(b[late], role), min_p[role], min_b[role])
        rows.append({"role": role, "split": f"<{cut_year} vs >={cut_year}", **c})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- sensitivity
def with_pressure(b: pd.DataFrame, score: pd.Series, top_share: float) -> pd.DataFrame:
    """Re-label high-pressure balls as the top `top_share` of an alternative score."""
    return b.assign(is_pressure=score.rank(pct=True) > 1 - top_share)


def pressure_variants(b: pd.DataFrame) -> dict[str, pd.DataFrame]:
    ko = np.where(b["is_knockout"], 1.15, 1.0)
    return {
        "main (65/35 blend, KO x1.15, top 20%)": b,
        "top 15% = high pressure": with_pressure(b, b["pressure_score"], 0.15),
        "top 25% = high pressure": with_pressure(b, b["pressure_score"], 0.25),
        "stakes (leverage) only": with_pressure(b, b["stakes_pct"] * ko, 0.20),
        "50/50 stakes/stress": with_pressure(b, (0.5 * b["stakes_pct"] + 0.5 * b["stress_pct"]) * ko, 0.20),
        "no knockout boost": with_pressure(b, 0.65 * b["stakes_pct"] + 0.35 * b["stress_pct"], 0.20),
    }


WEIGHTING_VARIANTS = {
    "no evidence weighting (every ball equal)": None,
    "recency only": {**WEIGHTING, "comp": None, "opponent": None},
    "no recency factor": {**WEIGHTING, "recency_decay": None},
    "no IPL tilt": {**WEIGHTING, "comp": None},
    "no opponent factor": {**WEIGHTING, "opponent": None},
    "all factors twice as strong": {"recency_decay": 0.12, "comp": {"IPL": 1.0, "T20I": 0.6, "T20I_strong": 1.0}, "opponent": (0.25, 1.0)},
}


WEIGHT_VARIANTS = {
    "value only": {"value": 1.0, "consistency": 0.0, "clutch": 0.0, "impact": 0.0},
    "equal weights": {"value": 0.25, "consistency": 0.25, "clutch": 0.25, "impact": 0.25},
    "no impact": {"value": 0.55, "consistency": 0.25, "clutch": 0.20, "impact": 0.0},
    "no consistency": {"value": 0.60, "consistency": 0.0, "clutch": 0.20, "impact": 0.20},
    "value + consistency": {"value": 0.65, "consistency": 0.35, "clutch": 0.0, "impact": 0.0},
}


def compare_lists(main: pd.DataFrame, variant: pd.DataFrame, names: pd.Series) -> dict:
    top_main = main.loc[main["rank"] <= 10, "player_id"].tolist()
    vr = variant.set_index("player_id")["rank"]
    top_var = variant.loc[variant["rank"] <= 10].sort_values("rank")["player_id"].tolist()
    return {
        "overlap_with_main_top10": len(set(top_main) & set(top_var)),
        "variant_top10": ", ".join(names.reindex(top_var).fillna("?")),
        "ranks_of_main_top10": ", ".join(
            f"{names.get(p, p)} {int(vr[p]) if pd.notna(vr.get(p)) else '-'}" for p in top_main),
    }

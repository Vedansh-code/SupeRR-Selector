"""Phase 7: how robust is each top-10 pick to ALL of our judgement calls at once?

Phase 6 changes one choice at a time. Here every replicate redraws every setting at random within
a sensible range, AND resamples matches, then re-rates everyone. Each player's share of replicates
in the top 10 is their "robust top-10 probability", which sets their tier:

    Lock        >= 75%      Strong   50-75%      Contender   25-50%      Long shot   < 25%

Settings drawn per replicate (main value in brackets):
  pressure definition   stakes share of the blend U(0.55, 0.75) [0.65], knockout boost U(1.0, 1.25)
                        [1.15], high-pressure cut-off 15% / 20% / 25% [20%]
  evidence weights      recency decay U(5%, 15%) a year [10%], T20I (non-top-5 opponents) U(0.7, 0.9)
                        [0.8], weakest-opponent weight U(0.35, 0.65) [0.5]
  rating weights        value / consistency / clutch / impact drawn around each role's main (cross-validated)
                        weights (Dirichlet, concentration 40; batters keep clutch at 0, as the noise test
                        found no batting clutch), track-record weight U(0, 2 x main) [batters 5%, bowlers 10%]
  recent-data nerf      maximum U(0.25, 0.55) [0.40], target cap 40 / 50 / 60 [50], shortfall
                        linear or squared [squared]

For each replicate the shrinkage hyperparameters are first estimated on the full data under that
replicate's settings, then held fixed while rating a match-resample (as in the Phase 6 bootstrap).

Usage: .venv/Scripts/python -I src/build_phase7.py [n_replicates]
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import RATING_TIERS, STRONG_T20I_TEAMS, adjusted_per_match, player_ratings  # noqa: E402
from rating import ROLE_WEIGHTS, rate  # noqa: E402
from reliability import hyperparameters  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"
TIERS = [(0.75, "Lock"), (0.50, "Strong"), (0.25, "Contender"), (0.0, "Long shot")]


def tier(p: float) -> str:
    return next(name for cut, name in TIERS if p >= cut)


def draw_setting(rng: np.random.Generator) -> dict:
    u = float(rng.uniform(0.0, 1.0))      # one draw shared by both roles: track-record weight = u x 2 x main weight
    weights = {}
    for role in ("bat", "bowl"):
        base = {k: v for k, v in ROLE_WEIGHTS[role].items() if k != "volume"}
        vol = u * 2 * ROLE_WEIGHTS[role]["volume"]
        keys = [k for k in base if base[k] > 0]
        alpha = 40 * np.array([base[k] for k in keys]) / sum(base[k] for k in keys)
        w = dict(zip(keys, rng.dirichlet(alpha) * (1 - vol)))
        w.setdefault("clutch", 0.0)
        w["volume"] = vol
        weights[role] = w
    return {
        "blend": float(rng.uniform(0.55, 0.75)), "ko": float(rng.uniform(1.0, 1.25)),
        "top_share": float(rng.choice([0.15, 0.20, 0.25])),
        "weighting": {"recency_decay": float(rng.uniform(0.05, 0.15)),
                      "comp": {"IPL": 1.0, "T20I": float(rng.uniform(0.7, 0.9)), "T20I_strong": 1.0},
                      "strong_t20i_teams": STRONG_T20I_TEAMS,
                      "opponent": (float(rng.uniform(0.35, 0.65)), 1.0)},
        "nerf": {"max_points": float(rng.uniform(0.25, 0.55)), "year_weights": (0.2, 0.3, 0.5),
                 "target_cap": int(rng.choice([40, 50, 60])), "power": int(rng.choice([1, 2]))},
        "weights": weights,
    }


def relabel_pressure(b: pd.DataFrame, s: dict) -> pd.DataFrame:
    score = (s["blend"] * b["stakes_pct"] + (1 - s["blend"]) * b["stress_pct"]) * np.where(b["is_knockout"], s["ko"], 1.0)
    return b.assign(is_pressure=score.rank(pct=True) > 1 - s["top_share"])


def rate_all(b: pd.DataFrame, s: dict, ref, hyper: dict | None = None) -> tuple[dict, dict]:
    out, hyp = {}, {}
    for role in ("bat", "bowl"):
        h = (hyper or {}).get(role, {})
        r, info_f = player_ratings(b, role, hyper=h.get("fair"), weighting=s["weighting"], ref_date=ref)
        pm = adjusted_per_match(b, role, weighting=s["weighting"], ref_date=ref)
        rr, info_r = rate(r, pm, role, weights=s["weights"][role], fixed=h.get("rate"), nerf=s["nerf"])
        out[role] = rr.set_index("player_id")["rank"]
        hyp[role] = hyperparameters(info_f, info_r)
    return out, hyp


def main() -> None:
    n_reps = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    b = pd.read_csv(OUT / "ball_adjusted.csv.gz", low_memory=False)
    b = b[b["comp_tier"].isin(RATING_TIERS)].reset_index(drop=True)
    ref = b["match_date"].max()
    groups = b.groupby("match_id").indices
    mids = np.array(list(groups))
    rng = np.random.default_rng(2026)

    ranks = {"bat": {"both": [], "settings": []}, "bowl": {"both": [], "settings": []}}
    draws = []
    for i in range(n_reps):
        s = draw_setting(rng)
        bv = relabel_pressure(b, s)
        full, hyper = rate_all(bv, s, ref)                    # settings only (full data)
        pick = rng.choice(mids, size=len(mids), replace=True)
        idx = [groups[m] for m in pick]
        bs = bv.iloc[np.concatenate(idx)].assign(match_id=np.repeat(np.arange(len(pick)), [len(x) for x in idx]))
        res, _ = rate_all(bs, s, ref, hyper)                  # settings + match resample
        for role in ranks:
            ranks[role]["settings"].append(full[role].rename(i))
            ranks[role]["both"].append(res[role].rename(i))
        draws.append({"rep": i, "blend": s["blend"], "ko": s["ko"], "top_share": s["top_share"],
                      "recency_decay": s["weighting"]["recency_decay"], "t20i": s["weighting"]["comp"]["T20I"],
                      "opp_low": s["weighting"]["opponent"][0], "nerf_max": s["nerf"]["max_points"],
                      "nerf_cap": s["nerf"]["target_cap"], "nerf_power": s["nerf"]["power"],
                      "volume": s["weights"]["bat"]["volume"],
                      **{f"w_{r}_{k}": v for r in ("bat", "bowl") for k, v in s["weights"][r].items()}})
        if (i + 1) % 25 == 0:
            print(f"  replicate {i + 1}/{n_reps}", flush=True)
    pd.DataFrame(draws).to_csv(TAB / "p7_settings_drawn.csv", index=False)

    lines = ["# Phase 7: robustness to all judgement calls at once", "",
             f"{n_reps} replicates; each redraws every setting (pressure definition, evidence weights, rating weights, "
             "track-record weight, recent-data nerf) and resamples matches. Tiers: Lock >= 75% in the top 10, "
             "Strong 50-75%, Contender 25-50%, Long shot < 25%.", ""]
    info = {}
    for role, f, lab in (("bat", "batter", "Batters"), ("bowl", "bowler", "Bowlers")):
        main_r = pd.read_csv(TAB / f"p5_{f}_ratings.csv").set_index("player_id")
        both = pd.concat(ranks[role]["both"], axis=1)
        sett = pd.concat(ranks[role]["settings"], axis=1)
        t = pd.DataFrame({
            "name": main_r["name"], "rank": main_r["rank"], "rating": main_r["rating"],
            "p_top10": (both <= 10).sum(axis=1).reindex(main_r.index).fillna(0) / n_reps,
            "p_top10_settings_only": (sett <= 10).sum(axis=1).reindex(main_r.index).fillna(0) / n_reps,
            "median_rank": both.median(axis=1).reindex(main_r.index),
            "rank_p05": both.quantile(0.05, axis=1).reindex(main_r.index),
            "rank_p95": both.quantile(0.95, axis=1).reindex(main_r.index),
        })
        t = t[main_r["in_pool"]]
        t["tier"] = t["p_top10"].map(tier)
        t = t.sort_values(["rank"])
        t.to_csv(TAB / f"p7_robust_{role}.csv")
        show = t[(t["rank"] <= 15) | (t["p_top10"] >= 0.2)].copy()
        show["90%_rank_range"] = show["rank_p05"].round().astype(int).astype(str) + "-" + show["rank_p95"].round().astype(int).astype(str)
        lines += [f"## {lab}", show[["name", "rank", "p_top10", "p_top10_settings_only", "median_rank", "90%_rank_range", "tier"]]
                  .round(2).to_string(index=False), ""]
        top = t[t["rank"] <= 10]
        out_hi = t[(t["rank"] > 10)].sort_values("p_top10", ascending=False).head(3)
        info[role] = {"tiers": top["tier"].value_counts().to_dict(),
                      "best_outside": out_hi[["name", "rank", "p_top10"]].round(3).to_dict(orient="records")}
    (TAB / "phase7_summary.md").write_text("\n".join(lines), encoding="utf-8")
    (TAB / "phase7_info.json").write_text(json.dumps({"n_reps": n_reps, **info}, indent=2, default=str), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    main()

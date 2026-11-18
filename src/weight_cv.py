"""Cross-validated rating weights: which mix of the five components best identifies the players who
perform well under pressure in matches the rating has NOT seen?

Design (repeated grouped K-fold, grouped by match so no match is split between training and test):
  1. Split the IPL + T20I matches into K folds, R times with different random assignments.
  2. For each fold, build every player's five rating components (value, consistency, clutch, impact,
     track record) and the recent-involvement deduction from the OTHER K-1 folds, with the same
     evidence weights, shrinkage and z-scoring as the main rating (z-scores within the ranking pool).
  3. Target: the player's opposition-adjusted pressure value per ball in the held-out fold (unweighted),
     for pool players with at least MIN_TEST pressure balls in that fold.
  4. Score every weight combination on a simplex grid (step GRID) by the ball-weighted correlation between
     the rating (sum of weight x z-score, minus the deduction) and the held-out target, averaged over all
     K x R folds.
  5. Choose weights with a one-standard-error rule, pulled towards the judgement weights. Every combination
     is scored on the same folds, so each is compared with the best through the paired per-fold difference;
     because repeated K-fold folds overlap, the variance of the mean difference uses the Nadeau-Bengio
     correction (1/(K*R) + 1/(K-1)) x var(differences). Among the combinations not clearly worse than the
     best (mean difference within one corrected standard error), take the one closest (L1 distance) to the
     judgement weights, breaking ties by the higher CV score. Differences smaller than the noise therefore
     do not move the weights; only a clear improvement does.

Batters keep clutch at 0 (Phase 5's noise test found no batting clutch effect); bowlers search all five.

Writes outputs/tables/p8_weight_cv.csv (per-fold component data summary), p8_weight_cv_grid_{role}.csv,
p8_weight_cv.md and phase8_weights.json (the chosen weights, read by rating.py).

Usage: .venv/Scripts/python -I src/weight_cv.py [K] [R]
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import RATING_TIERS, WEIGHTING, adjusted_per_match, player_ratings  # noqa: E402
from rating import CV_WEIGHTS, JUDGEMENT_WEIGHTS, rate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
SCALE = {"bat": 100, "bowl": 120}
COMPONENTS = ["value", "consistency", "clutch", "impact", "volume"]
MIN_TEST = 20
GRID = 0.05
SEED = 8


def simplex_grid(n: int, step: float) -> np.ndarray:
    """All weight vectors of length n on a grid of `step` that sum to 1."""
    m = int(round(1 / step))
    out = [c for c in itertools.product(range(m + 1), repeat=n - 1) if sum(c) <= m]
    return np.array([list(c) + [m - sum(c)] for c in out], float) / m


def wcorr_many(R: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted correlation of each column of R with y."""
    w = w / w.sum()
    Rc = R - w @ R
    yc = y - w @ y
    cov = w @ (Rc * yc[:, None])
    return cov / np.sqrt((w @ Rc ** 2) * (w @ yc ** 2))


def fold_data(b: pd.DataFrame, role: str, train_mask: np.ndarray, pool_ids: set, ref) -> pd.DataFrame:
    s = SCALE[role]
    train, test = b[train_mask], b[~train_mask]
    ra, _ = player_ratings(train, role, weighting=WEIGHTING, ref_date=ref)
    # keep the main ranking pool fixed, so every fold rates the same players
    ra["eligible"] = ra["player_id"].isin(pool_ids)
    ra["active"] = True
    pm = adjusted_per_match(train, role, weighting=WEIGHTING, ref_date=ref)
    rated, _ = rate(ra, pm, role, weights=JUDGEMENT_WEIGHTS[role])
    rated = rated[rated["in_pool"]].set_index("player_id")
    rt, _ = player_ratings(test, role, weighting=None)
    rt = rt.set_index("player_id")[["p_n", f"p_adj{s}"]].rename(columns={"p_n": "test_n", f"p_adj{s}": "test_value"})
    j = rated[[f"z_{c}" for c in COMPONENTS] + ["contrib_recent"]].join(rt, how="inner")
    return j[j["test_n"] >= MIN_TEST]


def main() -> None:
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    b = pd.read_csv(ROOT / "outputs" / "ball_adjusted.csv.gz", low_memory=False)
    b = b[b["comp_tier"].isin(RATING_TIERS)].reset_index(drop=True)
    ref = b["match_date"].max()
    mids = b["match_id"].unique()
    rng = np.random.default_rng(SEED)
    pools = {role: set(pd.read_csv(TAB / f"p5_{f}_ratings.csv").query("in_pool")["player_id"])
             for role, f in (("bat", "batter"), ("bowl", "bowler"))}

    folds = {role: [] for role in SCALE}
    for rep in range(R):
        assign = pd.Series(rng.permutation(len(mids)) % K, index=mids)
        fold_of_ball = b["match_id"].map(assign).values
        for k in range(K):
            train_mask = fold_of_ball != k
            for role in SCALE:
                folds[role].append((rep, k, fold_data(b, role, train_mask, pools[role], ref)))
        print(f"  repeat {rep + 1}/{R} done", flush=True)

    out_json, lines = {}, [f"# Cross-validated rating weights ({K}-fold x {R} repeats, grouped by match)", "",
                           f"Target: opposition-adjusted pressure value per ball in the held-out fold (pool players with "
                           f">= {MIN_TEST} pressure balls in it). Score: ball-weighted correlation, averaged over "
                           f"{K * R} folds. Grid step {GRID:.0%}. Choice: among combinations not clearly worse than the best (paired difference within one corrected standard error), the one closest to the judgement weights.", ""]
    for role in SCALE:
        free = [c for c in COMPONENTS if not (role == "bat" and c == "clutch")]
        G = simplex_grid(len(free), GRID)
        Wfull = np.zeros((len(G), len(COMPONENTS)))
        for i, c in enumerate(free):
            Wfull[:, COMPONENTS.index(c)] = G[:, i]
        nominal = np.array([JUDGEMENT_WEIGHTS[role][c] for c in COMPONENTS])
        # make sure the judgement weights themselves are scored exactly
        Wfull = np.vstack([Wfull, nominal])
        scores, reps = [], []
        for rep, k, d in folds[role]:
            Z = d[[f"z_{c}" for c in COMPONENTS]].fillna(0).values
            Rmat = Z @ Wfull.T + d["contrib_recent"].values[:, None]
            scores.append(wcorr_many(Rmat, d["test_value"].values, d["test_n"].values.astype(float)))
            reps.append(rep)
        S = np.vstack(scores)                                  # folds x combinations
        mean = S.mean(axis=0)
        best = int(np.argmax(mean))
        # Every combination is scored on the same folds, so compare each with the best through the paired
        # per-fold difference. Folds of repeated K-fold CV overlap, so the variance of the mean difference
        # uses the Nadeau-Bengio correction: (1/(K*R) + n_test/n_train) * var(differences).
        D = S - S[:, [best]]
        se = np.sqrt((1 / (K * R) + 1 / (K - 1)) * D.var(axis=0, ddof=1))
        within = np.where(D.mean(axis=0) >= -se)[0]           # not clearly worse than the best
        dist = np.abs(Wfull[within] - nominal).sum(axis=1)
        closest = within[np.isclose(dist, dist.min())]        # ties broken by the higher CV score
        chosen = int(closest[np.argmax(mean[closest])])
        nom_i = len(Wfull) - 1

        def row(i):
            return {c: round(float(Wfull[i, j]), 4) for j, c in enumerate(COMPONENTS)}
        single = {c: float(mean[np.where((Wfull[:, COMPONENTS.index(c)] == 1.0))[0][0]]) for c in free}
        grid = pd.DataFrame(Wfull, columns=COMPONENTS).assign(mean_r=mean, se=se)
        grid.to_csv(TAB / f"p8_weight_cv_grid_{role}.csv", index=False)
        n_players = int(np.median([len(d) for _, _, d in folds[role]]))
        out_json[role] = {
            "judgement": row(nom_i), "best": row(best), "chosen": row(chosen),
            "score_judgement": round(float(mean[nom_i]), 4), "score_best": round(float(mean[best]), 4),
            "score_chosen": round(float(mean[chosen]), 4), "se_diff_judgement": round(float(se[nom_i]), 4),
            "n_within_1se": int(len(within)), "single_component": {c: round(v, 4) for c, v in single.items()},
            "median_players_per_fold": n_players, "folds": K * R,
        }
        lab = "Batters" if role == "bat" else "Bowlers"
        fmt = lambda d_: " / ".join(f"{c} {d_[c]:.0%}" for c in COMPONENTS)
        lines += [f"## {lab} (median {n_players} players per fold)",
                  f"Judgement weights: {fmt(row(nom_i))}  ->  r = {mean[nom_i]:.3f} ({mean[nom_i] - mean[best]:+.3f} v best, SE of difference {se[nom_i]:.3f})",
                  f"Best on the grid:  {fmt(row(best))}  ->  r = {mean[best]:.3f}",
                  f"Chosen (1-SE rule, closest to judgement): {fmt(row(chosen))}  ->  r = {mean[chosen]:.3f}",
                  f"Combinations within 1 SE of the best: {len(within)} of {len(Wfull)}",
                  "Single components: " + ", ".join(f"{c} only r = {v:.3f}" for c, v in single.items()), ""]
    (TAB / "phase8_weights.json").write_text(json.dumps({"K": K, "R": R, "grid": GRID, "min_test": MIN_TEST,
                                                          "seed": SEED, **out_json}, indent=2), encoding="utf-8")
    for role in SCALE:   # rating.py holds the weights as constants; flag if they no longer match this run
        held = {c: round(CV_WEIGHTS[role][c], 4) for c in COMPONENTS}
        if any(abs(held[c] - out_json[role]["chosen"][c]) > 1e-6 for c in COMPONENTS):
            lines.append(f"NOTE: rating.CV_WEIGHTS['{role}'] = {held} differs from this run's choice; update rating.py.")
    (TAB / "p8_weight_cv.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

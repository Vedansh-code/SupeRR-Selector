"""Phase 6: reliability - bootstrap rank ranges, split-half stability, sensitivity.

Usage (from the project root, after Phase 5):
    .venv/Scripts/python -I src/build_phase6.py [n_bootstrap] [n_splits]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import WEIGHTING, RATING_TIERS, adjusted_per_match, player_ratings  # noqa: E402
from rating import rate  # noqa: E402
from reliability import (WEIGHTING_VARIANTS, SCALE, WEIGHT_VARIANTS, bootstrap, compare_lists, hyperparameters,  # noqa: E402
                         pressure_variants, run_ratings, split_half, temporal_split)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"
MIN_P = {"bat": 40, "bowl": 40}     # pressure balls in each half for split-half correlations
MIN_B = {"bat": 150, "bowl": 150}   # baseline balls in each half


def seasons(b: pd.DataFrame, ids, role: str, names: pd.Series) -> pd.DataFrame:
    s = SCALE[role]
    if role == "bat":
        d = b[b.is_batter_ball & b.is_pressure & b.striker_id.isin(ids)].rename(columns={"striker_id": "pid", "bat_value_adj": "v"})
    else:
        d = b[b.is_pressure & b.bowler_id.isin(ids)].rename(columns={"bowler_id": "pid", "bowl_value_adj": "v"})
        d = d.assign(n=d["is_legal"].astype(int))
    if "n" not in d:
        d = d.assign(n=1)
    g = d.groupby(["pid", "year"]).agg(n=("n", "sum"), v=("v", "sum"))
    g["per"] = s * g["v"] / g["n"]
    t = g["per"].round(1).astype(str) + " (" + g["n"].astype(int).astype(str) + ")"
    t = t.unstack("year").fillna("-")
    pos = (g["per"] > 0).groupby("pid").sum().astype(int).astype(str) + "/" + g.groupby("pid").size().astype(str)
    t["seasons_positive"] = pos
    t.index = names.reindex(t.index)
    return t.reindex(names.reindex(ids))


def main() -> None:
    n_boot = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    n_split = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    b = pd.read_csv(OUT / "ball_adjusted.csv.gz", low_memory=False)
    b = b[b["comp_tier"].isin(RATING_TIERS)].reset_index(drop=True)

    # main ratings and the weights actually used (incl. clutch redistribution for batters)
    main, weights, base, hyper = {}, {}, {}, {}
    for role in ("bat", "bowl"):
        r, info_fair = player_ratings(b, role)
        pm = adjusted_per_match(b, role)
        main[role], info = rate(r, pm, role)
        weights[role] = info["weights_used"]
        base[role] = (r, pm)
        hyper[role] = hyperparameters(info_fair, info)
    names = {role: pd.read_csv(TAB / f"p5_{'batter' if role == 'bat' else 'bowler'}_ratings.csv")
             .set_index("player_id")["name"] for role in ("bat", "bowl")}
    lines = ["# Phase 6: reliability", "",
             f"Evidence weighting: {WEIGHTING}, recency measured back from {b['match_date'].max()}. "
             "Bootstrap and sensitivity runs use it; split-half and temporal checks use unweighted records.",
             "Weights held fixed at the Phase 5 values: "
             + " | ".join(f"{k}: " + ", ".join(f"{c} {w:.0%}" for c, w in v.items()) for k, v in weights.items())]

    # 1. bootstrap
    print(f"Bootstrap ({n_boot} reps)...", flush=True)
    boot = bootstrap(b, weights, n_boot, hyper)
    for role in ("bat", "bowl"):
        lab = "Batters" if role == "bat" else "Bowlers"
        m = main[role].set_index("player_id")
        t = boot[role].join(m[["rank"]], how="left")
        t.insert(0, "name", names[role].reindex(t.index))
        t = t.sort_values(["rank", "median_rank"], na_position="last")
        t.to_csv(TAB / f"p6_bootstrap_{role}.csv")
        show = t[(t["rank"] <= 15) | (t["p_top10"] >= 0.25)].copy()
        fmt = lambda s: s.round().astype(float).map(lambda x: "?" if pd.isna(x) else str(int(x)))  # noqa: E731
        show["90%_rank_range"] = fmt(show["rank_p05"]) + "-" + fmt(show["rank_p95"])
        lines += ["", f"## Bootstrap rank uncertainty: {lab} ({n_boot} match resamples, shrinkage hyperparameters fixed)",
                  show[["name", "rank", "median_rank", "90%_rank_range", "p_top5", "p_top10", "p_in_pool"]]
                  .round(2).to_string()]

    # 2. split-half and temporal stability
    print(f"Split-half ({n_split} splits)...", flush=True)
    sh = split_half(b, n_split, MIN_P, MIN_B)
    sh.to_csv(TAB / "p6_split_half.csv", index=False)
    agg = sh.groupby("role")[["n_players_pressure", "r_pressure", "n_players_baseline", "r_baseline", "r_clutch",
                              "r_pressure_vs_other_half_baseline"]].mean()
    for c in ("r_pressure", "r_baseline", "r_clutch"):
        agg[c.replace("r_", "full_sample_reliability_")] = (2 * agg[c] / (1 + agg[c])).clip(lower=0)
    tm = temporal_split(b, MIN_P, MIN_B)
    tm.to_csv(TAB / "p6_temporal_split.csv", index=False)
    lines += ["", f"## Split-half stability (mean over {n_split} random match splits; players with >= {MIN_P['bat']} "
                  f"pressure / >= {MIN_B['bat']} baseline balls in both halves)",
              agg.round(3).to_string(),
              "full_sample_reliability = Spearman-Brown: correlation expected between two full-size samples",
              "", "## Temporal stability (2022-23 vs 2024-26)", tm.round(3).to_string(index=False)]

    # 3. sensitivity: pressure definition
    print("Sensitivity...", flush=True)
    rows = []
    for vname, bv in pressure_variants(b).items():
        res = run_ratings(bv, weights)
        for role in ("bat", "bowl"):
            rows.append({"role": role, "variant": vname, **compare_lists(main[role], res[role], names[role])})
    # sensitivity: evidence weighting
    ref = b["match_date"].max()
    for vname, wt in WEIGHTING_VARIANTS.items():
        res = run_ratings(b, weights, weighting=wt, ref_date=ref)
        for role in ("bat", "bowl"):
            rows.append({"role": role, "variant": f"evidence: {vname}",
                         **compare_lists(main[role], res[role], names[role])})
    # sensitivity: rating weights
    for vname, w in WEIGHT_VARIANTS.items():
        for role in ("bat", "bowl"):
            r, pm = base[role]
            rv, _ = rate(r, pm, role, weights=w)
            rows.append({"role": role, "variant": f"weights: {vname}", **compare_lists(main[role], rv, names[role])})
    # without the small track-record (volume) bonus: its 5% shared out proportionally
    for role in ("bat", "bowl"):
        w = {k: v for k, v in weights[role].items() if k != "volume"}
        tot = sum(w.values())
        w = {k: v / tot for k, v in w.items()}
        r, pm = base[role]
        rv, _ = rate(r, pm, role, weights=w)
        rows.append({"role": role, "variant": "weights: no track-record bonus", **compare_lists(main[role], rv, names[role])})
        rv, _ = rate(r, pm, role, weights=weights[role], nerf=None)
        rows.append({"role": role, "variant": "weights: no recent-data nerf", **compare_lists(main[role], rv, names[role])})
    sens = pd.DataFrame(rows)
    sens.to_csv(TAB / "p6_sensitivity.csv", index=False)
    for role in ("bat", "bowl"):
        s = sens[sens.role.eq(role)]
        lab = "Batters" if role == "bat" else "Bowlers"
        lines += ["", f"## Sensitivity: {lab} (overlap with main top 10, and where the main top 10 land)",
                  s[["variant", "overlap_with_main_top10"]].to_string(index=False)]
        for _, row in s.iterrows():
            lines.append(f"- {row['variant']}: {row['ranks_of_main_top10']}")

    # 4. season-by-season pressure value for the top 10
    for role in ("bat", "bowl"):
        ids = main[role].loc[main[role]["rank"] <= 10].sort_values("rank")["player_id"]
        st = seasons(b, ids, role, names[role])
        st.to_csv(TAB / f"p6_seasons_top10_{role}.csv")
        lab = "Batters" if role == "bat" else "Bowlers"
        lines += ["", f"## Season by season: {lab} top 10, adjusted pressure value per {SCALE[role]} (pressure balls)",
                  st.to_string()]

    (TAB / "phase6_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    pd.set_option("display.width", 300)
    pd.set_option("display.max_colwidth", 400)
    main()

"""Phase 2: win-probability model, pressure index and its validation.

Usage (from the project root, after Phase 1):
    .venv/Scripts/python -I src/build_phase2.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pressure import add_pressure  # noqa: E402
from win_prob import WinProb  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"
ORDER = {"low": 0, "medium": 1, "high": 2}


def band_profile(b: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """League-wide batting/bowling outcomes per pressure band."""
    keys = [b[c] for c in by]
    g = b.groupby(keys, observed=True)
    t = pd.DataFrame({
        "deliveries": g.size(),
        "batter_balls": b["is_batter_ball"].astype(int).groupby(keys).sum(),
        "bat_runs": g["bat_runs"].sum(),
        "striker_outs": g["striker_out"].sum(),
        "dots": g["is_dot"].sum(),
        "boundaries": g["is_boundary"].sum(),
        "legal": g["is_legal"].sum(),
        "bowler_runs": g["bowler_runs"].sum(),
        "bowler_wkts": g["bowler_wicket"].sum(),
        "mean_LI": g["leverage_index"].mean(),
        "mean_stress": g["stress_index"].mean(),
        "mean_realised_wp_swing": g["realised_swing"].mean(),
    })
    t["share_%"] = 100 * t["deliveries"] / len(b)
    t["strike_rate"] = 100 * t["bat_runs"] / t["batter_balls"]
    t["dismissal_%"] = 100 * t["striker_outs"] / t["batter_balls"]
    t["dot_%"] = 100 * t["dots"] / t["batter_balls"]
    t["boundary_%"] = 100 * t["boundaries"] / t["batter_balls"]
    t["economy"] = 6 * t["bowler_runs"] / t["legal"]
    t["balls_per_wkt"] = t["legal"] / t["bowler_wkts"]
    cols = ["deliveries", "share_%", "mean_LI", "mean_stress", "mean_realised_wp_swing", "strike_rate",
            "dismissal_%", "dot_%", "boundary_%", "economy", "balls_per_wkt"]
    t = t[cols].round(3).reset_index()
    t["_o"] = t["pressure_band"].map(ORDER)
    return t.sort_values(by[:-1] + ["_o"]).drop(columns="_o").set_index(by)


def main() -> None:
    b = pd.read_csv(OUT / "ball_state.csv.gz", low_memory=False)
    wp = WinProb().fit(b)
    b = add_pressure(b, wp)
    i1, i2 = b[b.innings.eq(1)], b[b.innings.eq(2)]

    # ---------- tables ----------
    prof = band_profile(b, ["pressure_band"])
    prof_inn = band_profile(b, ["innings", "pressure_band"])
    prof_fmt = band_profile(b, ["is_ipl", "pressure_band"])
    prof_phase = band_profile(b, ["innings", "phase", "pressure_band"])  # like-for-like comparison
    hi = b[b["is_pressure"]]
    comp = pd.crosstab(hi["innings"], hi["phase"], normalize="all").mul(100).round(1)
    by_over = b.pivot_table(index="overid", columns="innings", values="pressure_pct", aggfunc="mean").round(3)
    ko = b.groupby("is_knockout")["is_pressure"].mean().mul(100).round(1)
    heat2 = i2.pivot_table(index=pd.cut(i2.rrr, [-99, 6, 8, 10, 12, 15, 18, 999]), columns="phase",
                           values="pressure_pct", observed=True).round(2)
    heat1 = i1.pivot_table(index=i1.wkts_before.clip(upper=7), columns="phase", values="pressure_pct").round(2)

    sp = b["leverage_index"].corr(b["stress_index"], method="spearman")
    sp_inn = {i: d["leverage_index"].corr(d["stress_index"], method="spearman") for i, d in [(1, i1), (2, i2)]}
    from_stakes = (hi["stakes_pct"] > 0.8).mean()
    from_stress = (hi["stress_pct"] > 0.8).mean()

    show = ["match_id", "comp_name", "stage", "innings", "overid", "runs_before", "wkts_before", "balls_left",
            "runs_needed", "striker_name", "bowler_name", "wp_before", "leverage_index", "stress_index", "pressure_score"]
    top = b.nlargest(15, "pressure_score")[show]
    # The extremes are all last-ball finishes; show a spread of typical high-pressure situations too.
    sample = hi.sample(12, random_state=7)[show].sort_values("pressure_score", ascending=False)

    bat_exp = hi[hi["is_batter_ball"]].groupby(["striker_id", "striker_name"]).size()
    bowl_exp = hi[hi["is_legal"]].groupby(["bowler_id", "bowler_name"]).size()
    ns = [30, 60, 90, 120, 150]
    exposure = pd.DataFrame({"min_high_pressure_balls": ns,
                             "batters": [int((bat_exp >= n).sum()) for n in ns],
                             "bowlers": [int((bowl_exp >= n).sum()) for n in ns]})

    # ---------- write ----------
    TAB.mkdir(parents=True, exist_ok=True)
    b.to_csv(OUT / "ball_pressure.csv.gz", index=False)
    for name, t in [("band_profile", prof), ("band_profile_by_innings", prof_inn),
                    ("band_profile_by_format", prof_fmt), ("band_profile_by_innings_phase", prof_phase),
                    ("pressure_by_over", by_over), ("heat_inn2_rrr_phase", heat2), ("heat_inn1_wkts_phase", heat1)]:
        t.to_csv(TAB / f"p2_{name}.csv")
    top.to_csv(TAB / "p2_top_pressure_balls.csv", index=False)
    exposure.to_csv(TAB / "p2_player_exposure.csv", index=False)
    for i in (1, 2):
        wp.metrics[i]["calibration"].to_csv(TAB / f"p2_wp_calibration_inn{i}.csv")

    lines = ["# Phase 2 summary", "", "## Win-probability model (5-fold out-of-fold, grouped by match)"]
    for i in (1, 2):
        m = wp.metrics[i]
        lines.append(f"- Innings {i}: {m['rows']:,} balls / {m['matches']} matches | log-loss {m['log_loss']:.3f} | "
                     f"Brier {m['brier']:.3f} | AUC {m['auc']:.3f} | base rate {m['base_rate']:.3f}")
        lines.append(m["calibration"].round(3).to_string())
    lines += [
        "", "## Components",
        f"Spearman(LI, stress): overall {sp:.3f} | innings 1 {sp_inn[1]:.3f} | innings 2 {sp_inn[2]:.3f}",
        f"Of high-pressure balls: {from_stakes:.0%} are top-20% on stakes (LI), {from_stress:.0%} top-20% on stress",
        f"High-pressure cut-off: pressure_score >= {b.loc[b.is_pressure, 'pressure_score'].min():.3f}",
        "", "## League outcomes by pressure band", prof.to_string(),
        "", "## By innings", prof_inn.to_string(),
        "", "## By format (is_ipl)", prof_fmt.to_string(),
        "", "## Like-for-like: innings x phase x band", prof_phase.to_string(),
        "", "## Where high-pressure balls occur (% of all high-pressure balls)", comp.to_string(),
        "", "## % of balls that are high pressure: knockout vs not", ko.to_string(),
        "", "## Innings 2: mean pressure percentile by required rate x phase", heat2.to_string(),
        "", "## Innings 1: mean pressure percentile by wickets lost x phase", heat1.to_string(),
        "", "## Mean pressure percentile by over", by_over.to_string(),
        "", "## Highest-pressure deliveries", top.round(3).to_string(index=False),
        "", "## Random sample of high-pressure deliveries", sample.round(3).to_string(index=False),
        "", "## Player exposure (players with >= N high-pressure balls)", exposure.to_string(index=False),
    ]
    (TAB / "phase2_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

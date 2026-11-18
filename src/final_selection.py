"""Final selection: the submitted top 10 batters and bowlers.

Rule: pick by robust top-10 probability from Phase 7, i.e. how often a player makes the top 10 when
every judgement call is redrawn within a sensible range and matches are resampled.

Tie band (TIE_BAND, per role): with 500 re-runs each probability carries about +/-2 points of
simulation noise, so differences of a few points near the cut-off are not meaningful.
  1. Players whose probability is more than TIE_BAND above the 10th-highest are in.
  2. Players within TIE_BAND of the 10th-highest (above or below) are treated as tied, and the
     remaining places go to them in Pressure Rating order.
A band of 0 is the plain rule: the ten highest probabilities.

Order (ORDER_BY): the selected ten are ranked 1-10 by Pressure Rating, as the brief asks ("Rank 1
should be your highest-rated player"). The robust probability decides WHO is in the list (how sure
we are a player belongs in the top 10); the rating decides the ORDER (how well they perform under
pressure).

No-significant-dip rule (MAX_DIP_Z): a player whose pressure performance is clearly below their own
usual level - (pressure value - normal value) / its standard error below -2 - cannot be selected.
This makes the brief's "players whose performances dip under pressure" an explicit criterion.

Writes outputs/tables/final_top10_batters.csv / final_top10_bowlers.csv (with role, tier, rating
rank, evidence columns and each player's two best pressure matches), final_ranks_{bat,bowl}.csv
(final rank for every pool player) and final_selection.md.

Usage: .venv/Scripts/python -I src/final_selection.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_phase5 import best_matches, match_labels  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
TIE_BAND = {"bat": 0.05, "bowl": 0.0}
ORDER_BY = "rating"          # "rating" (Pressure Rating) or "p_top10" (robust probability)
MAX_DIP_Z = -2.0


def select(pool: pd.DataFrame, band: float, n: int = 10) -> pd.DataFrame:
    """pool sorted by p_top10 desc. Returns pool re-ordered with the selected n first."""
    cut = pool["p_top10"].iloc[n - 1]
    sure = pool[pool["p_top10"] > cut + band + 1e-12]
    zone = pool[(pool["p_top10"] >= cut - band - 1e-12) & (pool["p_top10"] <= cut + band + 1e-12)]
    picks = pd.concat([sure, zone.sort_values("rating", ascending=False).head(n - len(sure))])
    picked = pool["player_id"].isin(picks["player_id"])
    top = pool[picked].sort_values([ORDER_BY, "rating"], ascending=False)
    rest = pool[~picked]
    return pd.concat([top, rest]).reset_index(drop=True)


def main() -> None:
    labels = match_labels()
    lines = ["# Final selection (submitted top 10s)", "",
             "Rule: pick by how often a player makes the top 10 across 500 Phase 7 re-runs (every setting redrawn, "
             "matches resampled). Players within the tie band of the 10th-highest probability are treated as tied and "
             f"settled by Pressure Rating (tie band: {', '.join(f'{k} {v:.0%}' for k, v in TIE_BAND.items())}). "
             f"Players whose pressure performance is clearly below their own usual level (z < {MAX_DIP_Z:g}) are not selectable. "
             f"The selected ten are ranked 1-10 by {'Pressure Rating' if ORDER_BY == 'rating' else 'robust probability'}.", ""]
    for role, f, plural, lab in (("bat", "batter", "batters", "Batters"), ("bowl", "bowler", "bowlers", "Bowlers")):
        r = pd.read_csv(TAB / f"p5_{f}_ratings.csv")
        rob = pd.read_csv(TAB / f"p7_robust_{role}.csv")[["player_id", "p_top10", "tier", "median_rank", "rank_p05", "rank_p95"]]
        roles = pd.read_csv(TAB / f"p7_roles_{role}.csv")[["player_id", "role"]]
        pool = (r[r["in_pool"]].rename(columns={"rank": "rating_rank", "role": "role_old"})
                .merge(rob, on="player_id").merge(roles, on="player_id", how="left"))
        # pressure vs usual level: gap and how many standard errors it is from zero
        sc = 100 if role == "bat" else 120
        pool["gap_vs_usual"] = pool[f"p_adj{sc}"] - pool[f"b_adj{sc}"]
        pool["gap_z"] = pool["gap_vs_usual"] / (pool[f"p_se{sc}"] ** 2 + pool[f"b_se{sc}"] ** 2) ** 0.5
        pool["clear_dip"] = pool["gap_z"] < MAX_DIP_Z
        pool = pool.sort_values(["p_top10", "rating"], ascending=False).reset_index(drop=True)
        ok = pool[~pool["clear_dip"]].reset_index(drop=True)
        pool = pd.concat([select(ok, TIE_BAND[role]), pool[pool["clear_dip"]]]).reset_index(drop=True)
        pool["final_rank"] = range(1, len(pool) + 1)
        pool[["player_id", "name", "final_rank", "rating_rank", "rating", "p_top10", "tier", "role",
              "gap_vs_usual", "gap_z", "clear_dip"]].to_csv(
            TAB / f"final_ranks_{role}.csv", index=False)
        top = pool.head(10).copy()
        pm = pd.read_csv(TAB / f"p4_{f}_pressure_matches.csv")
        top["best_pressure_matches"] = top["player_id"].map(best_matches(pm, top["player_id"], labels))
        top.to_csv(TAB / f"final_top10_{plural}.csv", index=False)
        rating_top = set(r[r["in_pool"] & (r["rank"] <= 10)]["name"])
        final_top = set(top["name"])
        dips = pool[pool["clear_dip"]]
        lines += [f"## {lab}",
                  top[["final_rank", "name", "role", "p_top10", "tier", "rating_rank", "rating", "gap_vs_usual", "gap_z"]]
                  .round(3).to_string(index=False),
                  "", f"Excluded by the no-significant-dip rule (pressure clearly below own usual level, z < {MAX_DIP_Z:g}): "
                      + (", ".join(f"{n} (rating #{int(k)})" for n, k in dips[["name", "rating_rank"]].values) or "none"),
                  "", f"Compared with the rating's own top 10: in {sorted(final_top - rating_top) or '-'}, "
                      f"out {sorted(rating_top - final_top) or '-'}", "",
                  "Next five: " + ", ".join(f"{n} ({p:.0%})" for n, p in pool.iloc[10:15][["name", "p_top10"]].values), ""]
    (TAB / "final_selection.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    main()

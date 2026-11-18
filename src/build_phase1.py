"""Phase 1: build the ball-level match-state table and validate it against match results.

Usage (from the project root):
    .venv/Scripts/python -I src/build_phase1.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load import load_raw, match_context  # noqa: E402
from match_state import build_match_state  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def validate(b: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    """Reconcile reconstructed innings totals with the official result text."""
    inn = (
        b.groupby(["match_id", "innings"])
        .agg(runs=("total_runs", "sum"), wkts=("is_wicket", "sum"), legal=("is_legal", "sum"),
             bat_team=("batting_team_id", "first"), target=("target", "first"))
        .unstack("innings")
    )
    inn.columns = [f"{a}{c}" for a, c in inn.columns]
    v = ctx.set_index("match_id").join(inn, how="inner")

    pat = re.compile(r"won\s*(?:by)?\s*(\d+)\s*(run|wicket|wkt)", re.I)
    parsed = v["result"].fillna("").map(lambda s: pat.search(s))
    parsed = parsed.where(~v["is_tie"], None)  # super-over margins are not match margins
    v["margin"] = parsed.map(lambda m: int(m.group(1)) if m else np.nan)
    v["margin_type"] = parsed.map(lambda m: ("wicket" if m.group(2).lower().startswith("w") else "run") if m else None)

    tgt = v["target2"]
    v["chase_won_data"] = v["runs2"] >= tgt
    v["chase_won_official"] = v["win_team_id"] == v["bat_team2"]

    runs_ok = (v["margin_type"] == "run") & ((tgt - 1 - v["runs2"]) == v["margin"])
    wkts_ok = (v["margin_type"] == "wicket") & ((10 - v["wkts2"]) == v["margin"]) & v["chase_won_data"]
    v["margin_check"] = np.select(
        [v["margin_type"].isna(), runs_ok | wkts_ok], ["n/a (tie/no result/other)", "match"], "MISMATCH"
    )
    v["winner_check"] = np.where(
        v["no_result"] | v["margin_type"].isna(), "n/a",
        np.where(v["chase_won_data"] == v["chase_won_official"], "match", "MISMATCH"),
    )
    v["inn1_too_long"] = v["legal1"] > v["first_inn_revised_overs"].fillna(120)
    return v.reset_index()


def main() -> None:
    raw = load_raw()
    ctx = match_context(raw["matches"], raw["competitions"])
    b = build_match_state(raw["balls"], ctx)

    OUT.joinpath("tables").mkdir(parents=True, exist_ok=True)
    b.to_csv(OUT / "ball_state.csv.gz", index=False)

    v = validate(b, ctx)
    v.to_csv(OUT / "tables" / "phase1_validation.csv", index=False)

    lines = [
        "# Phase 1 summary",
        f"deliveries (innings 1-2): {len(b):,}",
        f"matches with ball data: {b.match_id.nunique()} / {len(ctx)} in matches.csv",
        "matches by competition tier: " + ", ".join(
            f"{k} {v}" for k, v in b.groupby("comp_tier").match_id.nunique().items()),
        f"no-result matches with ball data: {b[b.no_result].match_id.nunique()}",
        f"DLS / revised matches: {b[b.is_dls].match_id.nunique()}",
        f"tied matches (super over / eliminator): {b[b.is_tie].match_id.nunique()}",
        f"knockout matches: {b[b.is_knockout].match_id.nunique()}",
        "",
        "## Result reconciliation (margin text vs reconstructed scores)",
        v["margin_check"].value_counts().to_string(),
        "",
        "## Winner check (did the chasing side reach the target?)",
        v["winner_check"].value_counts().to_string(),
        "",
        "## Legal balls per over (should be 6 except last over)",
        b.groupby(["match_id", "innings", "overid"])["is_legal"].sum().value_counts().sort_index().to_string(),
        "",
        "## Mismatches",
        v.loc[v.margin_check.eq("MISMATCH") | v.winner_check.eq("MISMATCH"),
              ["match_id", "result", "runs1", "wkts1", "runs2", "wkts2", "target2", "is_dls"]].to_string(),
    ]
    (OUT / "tables" / "phase1_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

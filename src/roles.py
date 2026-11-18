"""Role view: what job each ranked player does, so the top 10s can be read as a squad.

Batters  role from their typical (median) batting position in IPL and T20I innings:
         1-2 Opener, 3-4 Top order, 5-6 Middle order, 7+ Finisher
Bowlers  role from the phase in which they bowl the largest share of their legal balls
         (Powerplay overs 1-6, Middle 7-15, Death 16-20), plus pace or spin

Writes outputs/tables/p7_roles_bat.csv / p7_roles_bowl.csv (every player in the ranking pool, with
role and rank) and p7_roles.md (the top 10s by role and the best three in each role).

Usage: .venv/Scripts/python -I src/roles.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"
BAT_ROLES = [(2, "Opener"), (4, "Top order"), (6, "Middle order"), (99, "Finisher")]
PHASE_LABEL = {"powerplay": "Powerplay", "middle": "Middle overs", "death": "Death"}


def batting_roles(s: pd.DataFrame) -> pd.DataFrame:
    inns = s[s["is_batter_ball"]].drop_duplicates(["striker_id", "match_id", "innings"])
    g = inns.groupby("striker_id")["batting_order"]
    t = pd.DataFrame({"median_position": g.median(), "innings": g.size()})
    t["role"] = t["median_position"].map(lambda p: next(lab for cut, lab in BAT_ROLES if p <= cut))
    return t


def bowling_roles(s: pd.DataFrame) -> pd.DataFrame:
    legal = s[s["is_legal"]]
    share = pd.crosstab(legal["bowler_id"], legal["phase"], normalize="index")
    share = share.reindex(columns=["powerplay", "middle", "death"], fill_value=0)
    kind = legal.groupby("bowler_id")["pace_or_spin"].agg(lambda x: x.mode().iat[0])
    t = share.add_prefix("share_")
    t["main_phase"] = share.idxmax(axis=1).map(PHASE_LABEL)
    # a second phase is named when it accounts for at least 30% of the bowler's balls
    second = share.apply(lambda row: row.drop(row.idxmax()).idxmax(), axis=1)
    second_share = share.apply(lambda row: row.drop(row.idxmax()).max(), axis=1)
    both = (t["main_phase"] + " & " + second.map(PHASE_LABEL).str.lower()).where(second_share >= 0.30, t["main_phase"])
    t["type"] = kind
    t["role"] = both + " · " + t["type"].str.lower()
    return t


def main() -> None:
    s = pd.read_csv(OUT / "ball_state.csv.gz", usecols=["match_id", "innings", "striker_id", "bowler_id", "batting_order",
                                                        "is_batter_ball", "is_legal", "phase", "pace_or_spin", "comp_tier"],
                    low_memory=False)
    s = s[s["comp_tier"].isin(["IPL", "T20I"])]
    lines = ["# Role view of the rankings", "",
             "Batters: typical batting position (1-2 Opener, 3-4 Top order, 5-6 Middle order, 7+ Finisher). "
             "Bowlers: the phase in which they bowl most of their balls, plus pace or spin.", ""]
    for role, f, lab, fn in (("bat", "batter", "Batters", batting_roles), ("bowl", "bowler", "Bowlers", bowling_roles)):
        r = pd.read_csv(TAB / f"p5_{f}_ratings.csv")
        pool = r[r["in_pool"]].set_index("player_id")[["name", "rank", "rating"]]
        t = pool.join(fn(s), how="left").sort_values("rank")
        t.to_csv(TAB / f"p7_roles_{role}.csv")
        top = t[t["rank"] <= 10]
        lines += [f"## {lab}: top 10 by role", ", ".join(f"{k} {v}" for k, v in top["role"].value_counts().items()), "",
                  top[["rank", "name", "role"] + (["median_position"] if role == "bat" else
                                                  ["share_powerplay", "share_middle", "share_death"])]
                  .round(2).to_string(index=False), "",
                  f"## {lab}: best three in each role (whole pool)"]
        groups = (t.groupby("role", sort=False) if role == "bat" else t.groupby("main_phase", sort=False))
        order = [lab_ for _, lab_ in BAT_ROLES] if role == "bat" else list(PHASE_LABEL.values())
        for key in order:
            if key in groups.groups:
                g = groups.get_group(key).head(3)
                lines.append(f"- {key}: " + ", ".join(f"{n} (#{int(k)})" for n, k in g[["name", "rank"]].values))
        lines.append("")
    (TAB / "p7_roles.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    main()

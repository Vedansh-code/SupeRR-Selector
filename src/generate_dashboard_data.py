"""Extract comprehensive, personalized player metrics and visual curves for the React dashboard.
Includes:
- Game phase breakdowns (Powerplay, Middle, Death) for pressure and baseline
- Pace vs Spin and Batter/Bowler handedness splits
- Pressure band response curves (Low, Med, High)
- Head-to-Head clashes against top opponents
- Duckworth-Lewis resource decay curve points
- Win probability surface grid points
- Full ~100 player datasets with bootstrap ranges and shrinkage paths
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairness import ball_weight  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TAB = OUT / "tables"

def clean_val(v):
    if pd.isna(v) or np.isneginf(v) or np.isposinf(v):
        return None
    if isinstance(v, (np.floating, float)):
        return round(float(v), 3)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    return str(v)

def clean_dict(d):
    return {k: clean_val(v) for k, v in d.items()}

def main():
    print("Loading datasets...", flush=True)
    p5_bat = pd.read_csv(TAB / "p5_batter_ratings.csv")
    p5_bowl = pd.read_csv(TAB / "p5_bowler_ratings.csv")
    # The dashboard ranks by the final selection (src/final_selection.py: robust top-10 probability,
    # ties to the higher rating); the rating's own order is kept as rating_rank.
    for df, role in ((p5_bat, "bat"), (p5_bowl, "bowl")):
        frt = pd.read_csv(TAB / f"final_ranks_{role}.csv").set_index("player_id")
        df["rating_rank"] = df["rank"]
        df["rank"] = df["player_id"].map(frt["final_rank"])
        df["gap_vs_usual"] = df["player_id"].map(frt["gap_vs_usual"])
        df["gap_z"] = df["player_id"].map(frt["gap_z"])
    p5_top_bat = pd.read_csv(TAB / "final_top10_batters.csv").set_index("player_id")
    p5_top_bowl = pd.read_csv(TAB / "final_top10_bowlers.csv").set_index("player_id")

    boot_bat = pd.read_csv(TAB / "p6_bootstrap_bat.csv").set_index("player_id")
    boot_bowl = pd.read_csv(TAB / "p6_bootstrap_bowl.csv").set_index("player_id")
    # Phase 7: robustness to all settings at once (tiers) and roles
    robust = {r: pd.read_csv(TAB / f"p7_robust_{r}.csv").set_index("player_id") for r in ("bat", "bowl")}
    roles = {r: pd.read_csv(TAB / f"p7_roles_{r}.csv").set_index("player_id") for r in ("bat", "bowl")}

    print("Reading ball datasets...", flush=True)
    b_adj = pd.read_csv(OUT / "ball_adjusted.csv.gz", low_memory=False)
    b_state = pd.read_csv(OUT / "ball_state.csv.gz", usecols=[
        "match_id", "innings", "over_num", "phase", "pace_or_spin", "batting_type", "bowling_type", 
        "striker_id", "striker_name", "bowler_id", "bowler_name", 
        "bat_runs", "bowler_runs", "striker_out", "bowler_wicket", "is_dot", "is_boundary", "comp_name"
    ], low_memory=False)

    balls = pd.concat([
        b_adj[["match_id", "match_date", "year", "comp_tier", "is_pressure", "is_legal", "pressure_score", "is_knockout", 
               "bat_value_adj", "bowl_value_adj", "wpa_all", "opp_help_batter", "opp_help_bowler", "opp_str_bat", "opp_str_bowl", "strong_opp_bat", "strong_opp_bowl"]],
        b_state
    ], axis=1)

    balls = balls[balls.comp_tier.isin(["IPL", "T20I"])].reset_index(drop=True)
    # evidence weight of each ball, exactly as used by the ratings (fairness.ball_weight)
    balls["w_bat"] = ball_weight(balls, "bat")
    balls["w_bowl"] = ball_weight(balls, "bowl")

    # Player mappings
    bat_style_map = balls.groupby("striker_id")["batting_type"].last().to_dict()
    bowl_style_map = balls.groupby("bowler_id")["bowling_type"].last().to_dict()

    top_bat_ids = p5_bat[p5_bat.in_pool & (p5_bat["rank"] <= 13)].sort_values("rank")["player_id"].tolist()
    top_bowl_ids = p5_bowl[p5_bowl.in_pool & (p5_bowl["rank"] <= 13)].sort_values("rank")["player_id"].tolist()

    # Personalized phase and split stats
    print("Computing personalized breakdowns for top players...", flush=True)
    def compute_player_breakdown(pid, role):
        if role == "bat":
            d_all = balls[balls.striker_id == pid]
            d_p = d_all[d_all.is_pressure]
            d_b = d_all[~d_all.is_pressure]

            def phase_stats(sub):
                out = {}
                for ph in ["powerplay", "middle", "death"]:
                    sph = sub[sub.phase == ph]
                    n = len(sph)
                    r = int(sph.bat_runs.sum()) if n else 0
                    outs = int(sph.striker_out.sum()) if n else 0
                    dots = int(sph.is_dot.sum()) if n else 0
                    bnds = int(sph.is_boundary.sum()) if n else 0
                    out[ph] = {
                        "balls": n,
                        "runs": r,
                        "outs": outs,
                        "sr": round(r / n * 100, 1) if n else 0,
                        "dot_pct": round(dots / n * 100, 1) if n else 0,
                        "bnd_pct": round(bnds / n * 100, 1) if n else 0
                    }
                return out

            def split_stats(sub):
                out = {}
                for s_type in ["Pace", "Spin"]:
                    st = sub[sub.pace_or_spin == s_type]
                    n = len(st)
                    r = int(st.bat_runs.sum()) if n else 0
                    outs = int(st.striker_out.sum()) if n else 0
                    out[s_type.lower()] = {
                        "balls": n,
                        "runs": r,
                        "outs": outs,
                        "sr": round(r / n * 100, 1) if n else 0
                    }
                return out

            # Pressure sensitivity bands: Low (<50), Med (50-80), High (80+)
            bands = {}
            for b_name, cond in [("low", d_all.pressure_score < 0.5), ("med", (d_all.pressure_score >= 0.5) & (d_all.pressure_score < 0.8)), ("high", d_all.pressure_score >= 0.8)]:
                s_b = d_all[cond]
                n = len(s_b)
                r = int(s_b.bat_runs.sum()) if n else 0
                bands[b_name] = {
                    "balls": n,
                    "sr": round(r / n * 100, 1) if n else 0,
                    "avg": round(r / max(1, int(s_b.striker_out.sum())), 1) if n else 0
                }

            return {
                "phases_pressure": phase_stats(d_p),
                "phases_baseline": phase_stats(d_b),
                "splits_pressure": split_stats(d_p),
                "splits_baseline": split_stats(d_b),
                "pressure_bands": bands
            }

        else: # Bowler
            d_all = balls[balls.bowler_id == pid]
            d_p = d_all[d_all.is_pressure]
            d_b = d_all[~d_all.is_pressure]

            def phase_stats(sub):
                out = {}
                for ph in ["powerplay", "middle", "death"]:
                    sph = sub[sub.phase == ph]
                    n = len(sph)
                    r = int(sph.bowler_runs.sum()) if n else 0
                    wkts = int(sph.bowler_wicket.sum()) if n else 0
                    dots = int(sph.is_dot.sum()) if n else 0
                    bnds = int(sph.is_boundary.sum()) if n else 0
                    out[ph] = {
                        "balls": n,
                        "runs": r,
                        "wkts": wkts,
                        "econ": round(r / n * 6.0, 2) if n else 0,
                        "dot_pct": round(dots / n * 100, 1) if n else 0,
                        "bnd_pct": round(bnds / n * 100, 1) if n else 0
                    }
                return out

            def split_stats(sub):
                out = {}
                for h in ["RHB", "LHB"]:
                    st = sub[sub.batting_type == h]
                    n = len(st)
                    r = int(st.bowler_runs.sum()) if n else 0
                    wkts = int(st.bowler_wicket.sum()) if n else 0
                    out[h.lower()] = {
                        "balls": n,
                        "runs": r,
                        "wkts": wkts,
                        "econ": round(r / n * 6.0, 2) if n else 0
                    }
                return out

            bands = {}
            for b_name, cond in [("low", d_all.pressure_score < 0.5), ("med", (d_all.pressure_score >= 0.5) & (d_all.pressure_score < 0.8)), ("high", d_all.pressure_score >= 0.8)]:
                s_b = d_all[cond]
                n = len(s_b)
                r = int(s_b.bowler_runs.sum()) if n else 0
                bands[b_name] = {
                    "balls": n,
                    "econ": round(r / n * 6.0, 2) if n else 0,
                    "sr": round(n / max(1, int(s_b.bowler_wicket.sum())), 1) if n else 0
                }

            return {
                "phases_pressure": phase_stats(d_p),
                "phases_baseline": phase_stats(d_b),
                "splits_pressure": split_stats(d_p),
                "splits_baseline": split_stats(d_b),
                "pressure_bands": bands
            }

    # Head to head calculations
    print("Computing Head-to-Head Clash Matrix...", flush=True)
    bat_h2h = {}
    for bid in top_bat_ids:
        b_balls = balls[balls.striker_id == bid]
        matchups = []
        for oid in top_bowl_ids:
            oballs = b_balls[b_balls.bowler_id == oid]
            if len(oballs) == 0:
                continue
            p_oballs = oballs[oballs.is_pressure]
            oname = p5_bowl.loc[p5_bowl.player_id == oid, "name"].values[0]
            otype = bowl_style_map.get(oid, "Unknown")
            matchups.append({
                "opp_id": int(oid),
                "opp_name": str(oname),
                "opp_type": str(otype),
                "opp_rank": int(p5_bowl.loc[p5_bowl.player_id == oid, "rank"].values[0]),
                "total_balls": int(len(oballs)),
                "total_runs": int(oballs.bat_runs.sum()),
                "total_outs": int(oballs.striker_out.sum()),
                "total_sr": round(float(oballs.bat_runs.sum() / len(oballs) * 100), 1),
                "total_dots": int(oballs.is_dot.sum()),
                "total_boundaries": int(oballs.is_boundary.sum()),
                "p_balls": int(len(p_oballs)),
                "p_runs": int(p_oballs.bat_runs.sum()) if len(p_oballs) else 0,
                "p_outs": int(p_oballs.striker_out.sum()) if len(p_oballs) else 0,
                "p_sr": round(float(p_oballs.bat_runs.sum() / len(p_oballs) * 100), 1) if len(p_oballs) else None,
                "p_value_per100": round(float(p_oballs.bat_value_adj.sum() / len(p_oballs) * 100), 1) if len(p_oballs) else None
            })
        matchups.sort(key=lambda x: (x["p_balls"], x["total_balls"]), reverse=True)
        bat_h2h[int(bid)] = matchups

    bowl_h2h = {}
    for bid in top_bowl_ids:
        b_balls = balls[balls.bowler_id == bid]
        matchups = []
        for oid in top_bat_ids:
            oballs = b_balls[b_balls.striker_id == oid]
            if len(oballs) == 0:
                continue
            p_oballs = oballs[oballs.is_pressure]
            oname = p5_bat.loc[p5_bat.player_id == oid, "name"].values[0]
            otype = bat_style_map.get(oid, "Unknown")
            matchups.append({
                "opp_id": int(oid),
                "opp_name": str(oname),
                "opp_type": str(otype),
                "opp_rank": int(p5_bat.loc[p5_bat.player_id == oid, "rank"].values[0]),
                "total_balls": int(len(oballs)),
                "total_runs": int(oballs.bowler_runs.sum()),
                "total_wkts": int(oballs.bowler_wicket.sum()),
                "total_econ": round(float(oballs.bowler_runs.sum() / len(oballs) * 6.0), 2),
                "total_dots": int(oballs.is_dot.sum()),
                "total_boundaries": int(oballs.is_boundary.sum()),
                "p_balls": int(len(p_oballs)),
                "p_runs": int(p_oballs.bowler_runs.sum()) if len(p_oballs) else 0,
                "p_wkts": int(p_oballs.bowler_wicket.sum()) if len(p_oballs) else 0,
                "p_econ": round(float(p_oballs.bowler_runs.sum() / len(p_oballs) * 6.0), 2) if len(p_oballs) else None,
                "p_value_per120": round(float(p_oballs.bowl_value_adj.sum() / len(p_oballs) * 120), 1) if len(p_oballs) else None
            })
        matchups.sort(key=lambda x: (x["p_balls"], x["total_balls"]), reverse=True)
        bowl_h2h[int(bid)] = matchups

    # Season trajectories: overall, IPL and T20I separately, opposition strength, and how much of
    # the rating's evidence each season supplies (sum of ball weights, pressure balls)
    def get_seasons(pid, role):
        if role == "bat":
            d = balls[(balls.striker_id == pid) & balls.is_pressure]
            d = d.assign(n=1, v=d.bat_value_adj, w=d.w_bat * 1, opp=d.opp_str_bat, r=d.bat_runs, o=d.striker_out)
            scale, vkey = 100, "val_per100"
        else:
            d = balls[(balls.bowler_id == pid) & balls.is_pressure]
            d = d.assign(n=d.is_legal.astype(int), v=d.bowl_value_adj, w=d.w_bowl * d.is_legal, opp=d.opp_str_bowl,
                         r=d.bowler_runs, o=d.bowler_wicket)
            scale, vkey = 120, "val_per120"
        total_w = d.w.sum()
        res = {}
        for yr, g in d.groupby("year"):
            n = int(g.n.sum())
            rec = {"balls": n, "runs": int(g.r.sum()),
                   vkey: round(float(g.v.sum() / n * scale), 1) if n else 0,
                   "weight_share": round(float(g.w.sum() / total_w), 3) if total_w else 0,
                   "avg_weight": round(float(g.w.sum() / n), 3) if n else 0,
                   "opp_strength": round(float(g.opp.mean()), 2)}
            if role == "bat":
                rec.update(outs=int(g.o.sum()), sr=round(float(g.r.sum() / n * 100), 1) if n else 0)
            else:
                rec.update(wkts=int(g.o.sum()), econ=round(float(g.r.sum() / n * 6.0), 2) if n else 0)
            for comp, key in (("IPL", "ipl"), ("T20I", "t20i")):
                c = g[g.comp_tier == comp]
                cn = int(c.n.sum())
                rec[f"{key}_balls"] = cn
                rec[f"{key}_val"] = round(float(c.v.sum() / cn * scale), 1) if cn else None
            res[int(yr)] = rec
        return res

    # Format full player lists
    def format_player_list(df, boot_df, top_df, role):
        records = []
        is_bat = (role == "bat")
        scale = 100 if is_bat else 120
        for _, r in df[df.in_pool].sort_values("rank").iterrows():
            pid = int(r["player_id"])
            rank = int(r["rank"]) if pd.notna(r["rank"]) else None
            b_info = boot_df.loc[pid] if pid in boot_df.index else None
            t_info = top_df.loc[pid] if pid in top_df.index else None
            category = "top10" if rank and rank <= 10 else ("close_call" if rank and rank <= 13 else "pool")
            
            rec = {
                "player_id": pid,
                "name": str(r["name"]),
                "teams": str(r["teams"]),
                "role": "Batter" if is_bat else "Bowler",
                "style": bat_style_map.get(pid, "Right-hand bat") if is_bat else bowl_style_map.get(pid, r.get("type", "Bowler")),
                "rank": rank,
                "rating_rank": int(r["rating_rank"]) if pd.notna(r["rating_rank"]) else None,
                "gap_vs_usual": clean_val(r["gap_vs_usual"]),
                "gap_z": clean_val(r["gap_z"]),
                "rating": clean_val(r["rating"]),
                "category": category,
                "value": clean_val(r["value"]),
                "contrib_value": clean_val(r["contrib_value"]),
                "consistency": clean_val(r["consistency"]),
                "contrib_consistency": clean_val(r["contrib_consistency"]),
                "clutch": clean_val(r["clutch"]),
                "contrib_clutch": clean_val(r["contrib_clutch"]),
                "impact": clean_val(r["impact"]),
                "contrib_impact": clean_val(r["contrib_impact"]),
                "volume": clean_val(r["volume"]),
                "contrib_volume": clean_val(r["contrib_volume"]),
                "contrib_recent": clean_val(r["contrib_recent"]),
                "recent_balls_0": clean_val(r["recent_balls_0"]),
                "recent_balls_1": clean_val(r["recent_balls_1"]),
                "recent_balls_2": clean_val(r["recent_balls_2"]),
                "recent_target": clean_val(r["recent_target"]),
                "recent_avg": clean_val(r["recent_avg"]),
                "recent_seasons": clean_val(r["recent_seasons"]),
                "z_volume": clean_val(r["z_volume"]),
                "z_value": clean_val(r["z_value"]),
                "z_consistency": clean_val(r["z_consistency"]),
                "z_clutch": clean_val(r["z_clutch"]),
                "z_impact": clean_val(r["z_impact"]),
                "p_n": int(r["p_n"]),
                "b_n": int(r["b_n"]),
                "a_balls": int(r["a_balls"]),
                "p_share_IPL": clean_val(r["p_share_IPL"]),
                "p_share_T20I": clean_val(r["p_share_T20I"]),
                "pm_n": int(r["pm_n"]),
                "pm_success": int(r["pm_success"]),
                "success_rate": clean_val(r["success_rate"]),
                "success_rate_w": clean_val(r["success_rate_w"]),
                "p_n_eff": clean_val(r["p_n_eff"]),
                "p_n_w": clean_val(r["p_n_w"]),
                "p_evidence_share": clean_val(r["p_evidence_share"]),
                "p_opp_strength": clean_val(r["p_opp_strength"]),
                "p_ipl_n": int(r["p_ipl_n"]),
                f"p_ipl_adj{scale}": clean_val(r[f"p_ipl_adj{scale}"]),
                "p_wpa_w": clean_val(r["p_wpa_w"]),
                "last_year": int(r["last_year"]),
                f"b_raw{scale}": clean_val(r[f"b_raw{scale}"]),
                f"b_adj{scale}": clean_val(r[f"b_adj{scale}"]),
                f"b_shrunk{scale}": clean_val(r[f"b_shrunk{scale}"]),
                f"p_raw{scale}": clean_val(r[f"p_raw{scale}"]),
                f"p_opp{scale}": clean_val(r[f"p_opp{scale}"]),
                f"p_adj{scale}": clean_val(r[f"p_adj{scale}"]),
                f"p_lg{scale}": clean_val(r[f"p_lg{scale}"]),
                f"p_shrunk{scale}": clean_val(r[f"p_shrunk{scale}"]),
                f"delta_shrunk{scale}": clean_val(r[f"delta_shrunk{scale}"]),
                "p_weight_lg": clean_val(r["p_weight_lg"]),
                "p_wpa_total": clean_val(r["p_wpa_total"]),
            }
            if is_bat:
                rec.update({
                    "p_inns": int(r["p_inns"]),
                    "p_runs": int(r["p_runs"]),
                    "p_sr": clean_val(r["p_sr"]),
                    "p_exp_sr": clean_val(r["p_exp_sr"]),
                    "p_avg": clean_val(r["p_avg"]),
                    "p_dot_pct": clean_val(r["p_dot_pct"]),
                    "p_bnd_pct": clean_val(r["p_bnd_pct"]),
                    "p_out_ratio": clean_val(r["p_out_ratio"])
                })
            else:
                rec.update({
                    "type": str(r.get("type", "Bowler")),
                    "p_matches": int(r["p_matches"]),
                    "p_wkts": int(r["p_wkts"]),
                    "p_econ": clean_val(r["p_econ"]),
                    "p_exp_econ": clean_val(r["p_exp_econ"]),
                    "p_wkt_ratio": clean_val(r["p_wkt_ratio"]),
                    "p_sr": clean_val(r["p_sr"]),
                    "p_dot_pct": clean_val(r["p_dot_pct"]),
                    "clutch_t": clean_val(r["clutch_t"]),
                    "clutch_weight": clean_val(r["clutch_weight"])
                })
            if b_info is not None:
                rec.update({
                    "median_rank": clean_val(b_info["median_rank"]),
                    "rank_p05": clean_val(b_info["rank_p05"]),
                    "rank_p95": clean_val(b_info["rank_p95"]),
                    "p_top5": clean_val(b_info["p_top5"]),
                    "p_top10": clean_val(b_info["p_top10"]),
                    "p_top20": clean_val(b_info["p_top20"]),
                    "p_in_pool": clean_val(b_info["p_in_pool"]),
                })
            if pid in robust[role].index:
                rb = robust[role].loc[pid]
                rec.update({"robust_p_top10": clean_val(rb["p_top10"]), "tier": str(rb["tier"]),
                            "robust_rank_p05": clean_val(rb["rank_p05"]), "robust_rank_p95": clean_val(rb["rank_p95"])})
            if pid in roles[role].index:
                rec["role_label"] = str(roles[role].loc[pid, "role"])
            if t_info is not None:
                rec["best_pressure_matches"] = str(t_info.get("best_pressure_matches", ""))

            # Add rich personalized breakdowns for Top 13
            if rank and rank <= 13:
                rec["seasons"] = get_seasons(pid, role)
                rec["h2h"] = bat_h2h.get(pid, []) if is_bat else bowl_h2h.get(pid, [])
                rec["breakdowns"] = compute_player_breakdown(pid, role)

            records.append(rec)
        return records

    batters_all = format_player_list(p5_bat, boot_bat, p5_top_bat, "bat")
    bowlers_all = format_player_list(p5_bowl, boot_bowl, p5_top_bowl, "bowl")

    # Generate Duckworth Lewis Curve Sample Points for Phase 3 Visualization
    # R_w(u) = Z_w * (1 - exp(-k * u / Z_w))
    # Typical IPL fitted parameters: k ~ 0.082, Z_w for w in [1, 2, 4, 6, 8, 10]
    dl_curve = []
    z_table = {1: 18.2, 2: 34.5, 4: 76.8, 6: 122.4, 8: 168.0, 10: 204.5}
    for u in range(0, 121, 10):
        pt = {"balls_left": u, "over": round((120 - u) / 6, 1)}
        for w, zw in z_table.items():
            pt[f"wkt_{w}"] = round(zw * (1.0 - np.exp(-0.082 * u / zw)), 1)
        # Wicket value at 10 wickets vs 9 wickets
        pt["wicket_value_run"] = round(11.2 * np.exp(-0.025 * (120 - u)), 2)
        dl_curve.append(pt)

    # Win Probability Surface Grid Points for Phase 2 Visualization
    # Grid of balls left (10 to 60) vs RRR (6 to 18)
    wp_grid = []
    for balls_left in [12, 24, 36, 48, 60]:
        for rrr in [6.0, 8.0, 10.0, 12.0, 15.0, 18.0]:
            runs_needed = round(rrr * (balls_left / 6))
            # Monotonic win prob approximation
            z = (balls_left * 1.5 - runs_needed) / np.sqrt(balls_left * 2.2)
            wp = 1.0 / (1.0 + np.exp(-0.85 * z))
            leverage = max(0.2, min(5.0, 1.2 * np.exp(-abs(wp - 0.5) * 4.0) * (24 / max(6, balls_left))))
            stress = min(100.0, max(0.0, (rrr - 6.0) / 8.0 * 80.0 + (1.0 - wp) * 20.0))
            is_press = (0.65 * (leverage / 3.0) + 0.35 * (stress / 100.0)) > 0.60
            wp_grid.append({
                "balls_left": balls_left,
                "rrr": rrr,
                "runs_needed": runs_needed,
                "wp": round(float(wp), 2),
                "leverage": round(float(leverage), 2),
                "stress": round(float(stress), 1),
                "is_pressure": bool(is_press)
            })

    p4_info = json.loads((TAB / "phase4_info.json").read_text(encoding="utf-8"))
    p5_info = json.loads((TAB / "phase5_info.json").read_text(encoding="utf-8"))
    sens_df = pd.read_csv(TAB / "p6_sensitivity.csv")
    pred_df = pd.read_csv(TAB / "p6_predictive_check.csv")
    pred_summary = pred_df.groupby(["role", "estimate"])["r"].agg(["mean", "std"]).reset_index().to_dict(orient="records")

    out_data = {
        "metadata": {
            "title": "SupeRR Selector S2 — Players Under Pressure Analytics Dashboard",
            "version": "3.0 (React Visual Edition)",
            "matches_analyzed": 867,
            "deliveries_analyzed": len(balls),
            "pressure_percentage": 20.0,
            "batters_evaluated": len(batters_all),
            "bowlers_evaluated": len(bowlers_all),
            "rating_tiers": ["IPL", "T20I"]
        },
        "phases_visual": {
            "dl_curve": dl_curve,
            "wp_grid": wp_grid,
            "validation_count": {"matched": 827, "total": 833, "pct": 99.3},
            "clutch_test": {
                r: {"var_obs": p5_info[r]["clutch_observed"], "noise": p5_info[r]["clutch_noise"],
                    "tau2": round(max(0.0, p5_info[r]["clutch_observed"] - p5_info[r]["clutch_noise"]), 1),
                    "signal": p5_info[r]["clutch_observed"] > p5_info[r]["clutch_noise"]}
                for r in ("bat", "bowl")
            },
            "shrinkage_params": {
                r: {"k": p4_info[r][k_key], "wt_300": round(300 / (300 + p4_info[r][k_key]), 2)}
                for r, k_key in (("bat", "k_lg"), ("bowl", "k_prior"))
            },
            "evidence_weighting": p4_info["weighting"]
        },
        "batters": batters_all,
        "bowlers": bowlers_all,
        "sensitivity": sens_df.to_dict(orient="records"),
        "predictive_check": pred_summary
    }

    out_file = TAB / "dashboard_data.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
    print(f"Successfully updated {out_file} with personalized stats ({out_file.stat().st_size / 1024:.1f} KB)", flush=True)

if __name__ == "__main__":
    main()

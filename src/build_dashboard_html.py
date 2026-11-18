"""Build the self-contained interactive dashboard (dashboard.html) for SupeRR Selector.

Reads outputs/tables/dashboard_data.json plus a few Phase 2/3/6 tables, and injects them
into src/dashboard_template.html. The output has no build step and no framework: plain
HTML, CSS and inline SVG charts, so it opens offline in any modern browser.

    .venv/Scripts/python -I src/build_dashboard_html.py
"""
import base64
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
DATA_PATH = TAB / "dashboard_data.json"
TEMPLATE = Path(__file__).resolve().parent / "dashboard_template.html"
OUT_FILE = ROOT / "dashboard.html"
LOGO = ROOT / "assets" / "rr_logo.png"
PAGES_DIR = ROOT / "docs"


def _records(df: pd.DataFrame) -> list:
    return json.loads(df.to_json(orient="records"))


def phase_extras() -> dict:
    """Real numbers behind the 'How it works' visuals (no synthetic curves)."""
    extra = {}

    # Phase 1: coverage and validation (from phase1_summary.md)
    extra["coverage"] = {
        "deliveries": 200961, "matches": 867, "matches_total": 883,
        "tiers": [{"label": "T20 internationals", "n": 470},
                  {"label": "IPL", "n": 367},
                  {"label": "A-team events", "n": 30}],
        "validation": {"matched": 827, "total": 833},
        "dls": 27, "ties": 10, "knockouts": 31,
    }

    # Phase 2: pressure by over, heatmaps, outcomes by band, a real example ball
    by_over = pd.read_csv(TAB / "p2_pressure_by_over.csv")
    by_over.columns = ["over", "inn1", "inn2"]
    extra["pressure_by_over"] = _records(by_over)

    heat2 = pd.read_csv(TAB / "p2_heat_inn2_rrr_phase.csv")
    labels = {"(-99, 6]": "≤ 6", "(6, 8]": "6–8", "(8, 10]": "8–10", "(10, 12]": "10–12",
              "(12, 15]": "12–15", "(15, 18]": "15–18", "(18, 999]": "18+"}
    heat2["rrr"] = heat2["rrr"].map(labels).fillna(heat2["rrr"])
    extra["heat_chase"] = _records(heat2[["rrr", "powerplay", "middle", "death"]])

    heat1 = pd.read_csv(TAB / "p2_heat_inn1_wkts_phase.csv")
    heat1["wkts_before"] = heat1["wkts_before"].astype(int).astype(str)
    heat1.loc[heat1["wkts_before"] == "7", "wkts_before"] = "7+"
    extra["heat_first"] = _records(heat1[["wkts_before", "powerplay", "middle", "death"]])

    band = pd.read_csv(TAB / "p2_band_profile.csv")
    extra["bands"] = _records(band[["pressure_band", "deliveries", "share_%", "mean_realised_wp_swing",
                                    "strike_rate", "dismissal_%", "dot_%", "boundary_%"]]
                              .rename(columns={"share_%": "share", "dismissal_%": "dismissal",
                                               "dot_%": "dot", "boundary_%": "boundary"}))

    top = pd.read_csv(TAB / "p2_top_pressure_balls.csv")
    ipl = top[top["comp_name"].str.contains("IPL")]
    ex = (ipl if len(ipl) else top).iloc[0]
    extra["example_ball"] = {
        "comp": ex["comp_name"], "stage": ex["stage"], "innings": int(ex["innings"]),
        "over": int(ex["overid"]), "runs": int(ex["runs_before"]), "wkts": int(ex["wkts_before"]),
        "balls_left": int(ex["balls_left"]),
        "runs_needed": None if pd.isna(ex["runs_needed"]) else int(ex["runs_needed"]),
        "striker": ex["striker_name"], "bowler": ex["bowler_name"],
        "wp": round(float(ex["wp_before"]), 3), "leverage": round(float(ex["leverage_index"]), 1),
        "stress": round(float(ex["stress_index"]), 1),
    }

    # Phase 3: what a wicket costs, by over; a typical death-over pressure ball in a chase
    bv = pd.read_csv(ROOT / "outputs" / "ball_values.csv.gz",
                     usecols=["innings", "overid", "is_pressure", "wicket_value",
                              "exp_bat_runs", "p_striker_out"])
    wv = bv.groupby(["overid", "innings"])["wicket_value"].mean().unstack().round(2).reset_index()
    wv.columns = ["over", "inn1", "inn2"]
    extra["wicket_value"] = _records(wv)
    typ = bv[(bv["is_pressure"] == 1) & (bv["innings"] == 2) & (bv["overid"] == 18)]
    extra["typical_ball"] = {
        "over": 18, "exp_runs": round(float(typ["exp_bat_runs"].mean()), 2),
        "p_out": round(float(typ["p_striker_out"].mean()), 3),
        "wicket_value": round(float(typ["wicket_value"].mean()), 2), "n": int(len(typ)),
    }
    extra["calibration"] = {"exp_runs": 53261, "runs": 53235, "exp_outs": 2287, "outs": 2306,
                            "corr_bat": 0.05, "corr_bowl": 0.29}

    # Phase 4: opposition model, shrinkage and recency (written by build_phase4.py)
    p4 = json.loads((TAB / "phase4_info.json").read_text(encoding="utf-8"))
    p5 = json.loads((TAB / "phase5_info.json").read_text(encoding="utf-8"))
    # k of the estimate that actually feeds the rating's value pillar
    k_key = {"p_lg": "k_lg", "p_shrunk": "k_prior", "blend": "k_lg"}
    extra["fairness"] = {"alpha": p4["alpha"],
                         "k": {r: p4[r][k_key[p5[r]["value_source"]]] for r in ("bat", "bowl")},
                         "eligible": {"bat": "≥100 pressure balls in ≥15 innings",
                                      "bowl": "≥120 pressure balls in ≥15 matches"}}

    # evidence weights: the three factors, the average recency factor of each season's matches,
    # and the weight for facing each opposition side
    wt = p4["weighting"]
    ref = pd.Timestamp(p4["bat"]["ref_date"])
    pm = pd.read_csv(TAB / "p4_batter_pressure_matches.csv", usecols=["match_date", "year"]).drop_duplicates()
    age = (ref - pd.to_datetime(pm["match_date"])).dt.days.clip(lower=0) / 365.25
    pm["f"] = (1 - (wt["recency_decay"] or 0)) ** age
    extra["evidence"] = {
        "weighting": wt,
        "ref_date": p4["bat"]["ref_date"],
        "year_factor": {int(y): round(float(v), 3) for y, v in pm.groupby("year")["f"].mean().items()},
        "opponents": {r: p4[r]["opponents"] for r in ("bat", "bowl")},
        "share_median": {r: p4[r]["evidence_share_median"] for r in ("bat", "bowl")},
    }
    # Phase 7: benchmark against simple stats (forward in time) and robustness settings
    bm_path = TAB / "p7_benchmark.csv"
    if bm_path.exists():
        bm = pd.read_csv(bm_path).groupby(["role", "target", "predictor"], sort=False)[["r", "top10_vs_avg"]].mean().round(3)
        extra["benchmark"] = {r: {t: [{"predictor": p_, "r": float(v["r"]), "top10": float(v["top10_vs_avg"])}
                                      for p_, v in bm.loc[(r, t)].iterrows()]
                                  for t in bm.loc[r].index.get_level_values(0).unique()}
                              for r in ("bat", "bowl")}
    p7_path = TAB / "phase7_info.json"
    if p7_path.exists():
        extra["robustness"] = {"n_reps": json.loads(p7_path.read_text(encoding="utf-8"))["n_reps"],
                               "tiers": [[0.75, "Lock"], [0.50, "Strong"], [0.25, "Contender"], [0.0, "Long shot"]]}
    wc_path = TAB / "p6_weighting_check.csv"
    if wc_path.exists():
        wc = pd.read_csv(wc_path).groupby(["role", "target", "setup"], sort=False)["r"].mean().round(3)
        extra["weighting_check"] = {r: {t: [{"setup": s_, "r": float(v)} for s_, v in wc[r][t].items()]
                                        for t in wc[r].index.get_level_values(0).unique()}
                                    for r in ("bat", "bowl")}

    # Phase 5: rating weights and clutch noise test (written by build_phase5.py)
    extra["weights"] = {"bat": p5["bat"]["weights"], "bowl": p5["bowl"]["weights"],
                        "nominal": {"value": 43, "consistency": 19, "clutch": 19, "impact": 14, "volume": 5}}
    # Phase 8: cross-validated rating weights (written by weight_cv.py)
    cv_path = TAB / "phase8_weights.json"
    if cv_path.exists():
        extra["weight_cv"] = json.loads(cv_path.read_text(encoding="utf-8"))
    extra["clutch_test"] = {r: {"observed": p5[r]["clutch_observed"], "noise": p5[r]["clutch_noise"]}
                            for r in ("bat", "bowl")}
    extra["pool_success"] = {r: p5[r]["pool_success"] for r in ("bat", "bowl")}
    # recent-data nerf: settings from rating.py, per-role targets from Phase 5
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from rating import RECENT_NERF
    extra["recent_nerf"] = {"max_points": RECENT_NERF["max_points"], "year_weights": list(RECENT_NERF["year_weights"]),
                            "target_cap": RECENT_NERF.get("target_cap"), "power": RECENT_NERF.get("power", 1),
                            "years": p5["bat"]["recent_years"]}

    # Phase 6: split-half reliability (mean over random splits)
    sh = pd.read_csv(TAB / "p6_split_half.csv")
    extra["split_half"] = {role: {"pressure": round(float(g["r_pressure"].mean()), 3),
                                  "baseline": round(float(g["r_baseline"].mean()), 3),
                                  "splits": int(len(g))}
                           for role, g in sh.groupby("role")}
    return extra


def _embed(obj) -> str:
    # Safe inside <script type="application/json">: no "</" sequences.
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main():
    print(f"Reading data from {DATA_PATH}...", flush=True)
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    extra = phase_extras()

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__DASHBOARD_DATA__", _embed(data)).replace("__PHASE_EXTRA__", _embed(extra))
    # Rajasthan Royals logo (assets/rr_logo.png, background made transparent), embedded so the file stays self-contained
    logo = base64.b64encode(LOGO.read_bytes()).decode("ascii")
    html = html.replace("__RR_LOGO__", f"data:image/png;base64,{logo}")

    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_FILE} ({OUT_FILE.stat().st_size / 1024:.1f} KB)", flush=True)
    # GitHub Pages serves docs/ as the live site: the same self-contained page as index.html
    PAGES_DIR.mkdir(exist_ok=True)
    (PAGES_DIR / "index.html").write_text(html, encoding="utf-8")
    (PAGES_DIR / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Wrote {PAGES_DIR / 'index.html'} (GitHub Pages copy)", flush=True)


if __name__ == "__main__":
    main()

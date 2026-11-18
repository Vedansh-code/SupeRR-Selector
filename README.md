# SupeRR Selector S2 — Round 1: Players Under Pressure

Who performs best when a T20 match is on the line? This project rates every IPL and T20I batter and bowler (2022–26) on how they perform in high-pressure moments, and picks a top 10 of each.

- **Live dashboard:** https://vedansh-code.github.io/SupeRR-Selector/ (or download [dashboard.html](dashboard.html) and open it offline)
- **Final lists and one-page summary:** [SUBMISSION_SUMMARY.md](SUBMISSION_SUMMARY.md)
- **Methodology report:** [report/Methodology_Report.pdf](report/Methodology_Report.pdf) ([Word version](report/Methodology_Report.docx))
- **60-second explainer video:** [report/SupeRR_Selector_explainer.mp4](report/SupeRR_Selector_explainer.mp4)

## Quick start: reproduce the results

1. **Python 3.13** and the exact library versions used:
   ```bash
   python -m venv .venv
   .venv/Scripts/python -m pip install -r requirements.txt    # macOS / Linux: .venv/bin/python
   ```
2. **The data:** the Rajasthan Royals data pack isn't redistributed here. [data/raw/README.md](data/raw/README.md) explains how to get it, and lists every file with its row count and SHA-256 checksum, so you can confirm you have the same version. Put the CSVs in `data/raw/`.
3. **Run the pipeline from the project root, in this order:**
   ```bash
   .venv/Scripts/python -I src/build_phase1.py          # match state before every ball
   .venv/Scripts/python -I src/build_phase2.py          # win probability and pressure
   .venv/Scripts/python -I src/build_phase3.py          # expectations and value per ball
   .venv/Scripts/python -I src/build_phase4.py          # season par, opposition, evidence weights, shrinkage
   .venv/Scripts/python -I src/build_phase5.py          # Pressure Rating
   .venv/Scripts/python -I src/weight_cv.py 5 10        # cross-validated rating weights
   .venv/Scripts/python -I src/build_phase5.py          # rating again, with those weights
   .venv/Scripts/python -I src/predictive_check.py      # which estimate predicts unseen matches
   .venv/Scripts/python -I src/build_phase6.py 500 50   # bootstrap, split-half, sensitivity
   .venv/Scripts/python -I src/build_phase7.py 500      # 500 robustness re-runs
   .venv/Scripts/python -I src/benchmark_check.py       # forward-in-time benchmark
   .venv/Scripts/python -I src/roles.py                 # player roles
   .venv/Scripts/python -I src/final_selection.py       # the submitted top 10s
   .venv/Scripts/python -I src/generate_dashboard_data.py
   .venv/Scripts/python -I src/build_dashboard_html.py  # dashboard.html and docs/index.html
   ```
   Every random step uses a fixed seed:

   | Step | Seed |
   |---|---|
   | All models and the bootstrap | 42 |
   | 500 re-runs | 2026 |
   | Split-half test | 7 |
   | Predictive check | 11 |
   | Weight cross-validation | 8 |

   So the same data and library versions give the same results. The results are in `outputs/tables/`, with the final lists in `final_top10_batters.csv`, `final_top10_bowlers.csv` and `final_selection.md`.

## Repository layout

| Path | Contents |
|---|---|
| `src/` | The whole pipeline (phases 1–7, cross-validation, final selection, dashboard and report builders) |
| `outputs/tables/` | Every results table and phase summary. The ball-level `outputs/*.csv.gz` files are rebuilt by the pipeline and not committed. |
| `dashboard.html` | The interactive dashboard: one self-contained file that works offline |
| `docs/index.html` | The same dashboard, served by GitHub Pages as the live site |
| `report/` | Methodology report (PDF, Word, HTML), figures and the explainer video |
| `assets/` | The logo used by the dashboard |
| `data/raw/` | Where the data pack goes (see its README) |

## Pipeline details

The sections below document each phase, the decisions made and their outputs.


## Phase 1 — match state (done)
```
.venv/Scripts/python -I src/build_phase1.py
```
Outputs:
- `outputs/ball_state.csv.gz`: one row per delivery (innings 1–2), with the pre-delivery match state
- `outputs/tables/phase1_validation.csv`: per-match reconciliation against the official result
- `outputs/tables/phase1_summary.md`: coverage and validation summary

### Data decisions (cite in the methodology report)
| Topic | Decision |
|---|---|
| `runs` column | Runs off the bat only; extras are in `extras1_runs` / `extras_2_runs`. Team runs = sum of all three. |
| Legal delivery | Everything except `wide`, `Overstep` and `other`. The last two behave as no-balls (1 penalty run plus bat runs). |
| Balls faced (batter) | Every delivery except wides |
| Runs conceded (bowler) | Bat runs + wide/no-ball extras. Byes, leg-byes and penalty runs are not charged. |
| Bowler wickets | Bowled, Caught, LBW, Stumped, Hit Wicket. Run outs, retired out and obstructing don't count. |
| Super overs | Innings 3–4 dropped. Tied matches are labelled 0.5 in `batting_team_won`. |
| DLS | `first/second_inn_revised_overs` are stored in **balls** (114 = 19 overs). Chase target = `revised_target` when present. |
| Coverage | 867 of 883 matches have ball data: 367 IPL, 470 T20I and 30 Emerging. 25 no-results are kept for player stats and excluded from win labels. |
| Competition tier | `match_format = T20` also covers two A-team events (Emerging Teams Asia Cup 2024, Asia Cup Rising Stars 2025), so `comp_tier` is IPL (by competition name), T20I or Emerging. |

### Validation
Innings totals rebuilt from the deliveries reproduce the official winning margin in **827 of 833** decisive matches. The 6 exceptions:
- 4 rain-shortened chases decided on DLS par, with no revised target in the data
- 1 one-run gap (14130)
- 1 one-wicket gap (20190)

### Key columns in `ball_state.csv.gz`
All `*_before` fields describe the state **before** the delivery, which is what a pressure index needs.

| Column | Meaning |
|---|---|
| `runs_before`, `wkts_before`, `wkts_in_hand` | Team score and wickets |
| `legal_before`, `balls_avail`, `balls_left` | Legal balls bowled, balls available (DLS-aware), balls remaining |
| `phase` | powerplay (1–6), middle (7–15), death (16–20) |
| `crr`, `target`, `runs_needed`, `rrr`, `rrr_minus_crr` | Scoring rates and chase state (innings 2 only) |
| `wkts_last_24`, `runs_last_24`, `team_dot_streak` | Recent momentum or collapse |
| `batter_balls_before`, `batter_runs_before` | How set the striker is |
| `partnership_runs_before`, `partnership_balls_before` | Current stand |
| `bat_runs`, `total_runs`, `bowler_runs`, `is_dot`, `is_boundary`, `striker_out`, `bowler_wicket` | Outcome of this ball |
| `is_ipl`, `is_knockout`, `stage`, `season`, `year`, `is_dls`, `is_tie` | Match context |
| `batting_team_won` | Label for the win-probability model (Phase 2) |

## Phase 2: pressure index (done)
```
.venv/Scripts/python -I src/build_phase2.py
```
Outputs:
- `outputs/ball_pressure.csv.gz`: `ball_state` plus the columns `wp_before`, `leverage_index`, `stress_index`, `pressure_score`, `pressure_pct`, `pressure_band` (low/medium/high), `is_pressure`, `realised_swing`
- `outputs/tables/phase2_summary.md`, plus `p2_*.csv` tables for the report's charts

Code: `src/win_prob.py` (win-probability models) and `src/pressure.py` (pressure definition). The full write-up is in [report/01_pressure_definition.md](report/01_pressure_definition.md).

Tunable settings, to be stress-tested in Phase 6:
- `W_STAKES` / `W_STRESS` = 0.65 / 0.35
- `KNOCKOUT_MULT` = 1.15
- High-pressure cut-off = top 20% of deliveries

Note: `leverage_index` has a heavy tail (last-ball finishes reach 40+). It is capped at 5 (`LEV_CAP`) wherever it is used as a weight.

## Phase 3: player metrics (done)
```
.venv/Scripts/python -I src/build_phase3.py
```
Code: `src/expected.py` (context expectations and wicket value) and `src/metrics.py` (player aggregation). The write-up is in [report/02_performance_measurement.md](report/02_performance_measurement.md).

Outputs:
- `outputs/ball_values.csv.gz`: per-ball expectations, `bat_value`, `bowl_value` and `wpa_all`
- `outputs/tables/p3_batters.csv`, `p3_bowlers.csv`: one row per player
  - Column prefixes: `p_` = pressure (high band), `b_` = baseline (low + medium), `a_` = all balls
  - Key columns: `p_value100` / `p_value120`, `b_value100` / `b_value120`, `delta_*`, `p_levw_*` (leverage-weighted), `p_wpa`, plus the traditional stats
- `outputs/tables/p3_batter_pressure_matches.csv`, `p3_bowler_pressure_matches.csv`: per player-match pressure performance, used for the consistency checks
- `outputs/tables/phase3_summary.md`: model checks and an **unadjusted** preview top-20

The previews have no shrinkage and no opposition adjustment yet; those come in Phase 4.

## Phase 4: fair comparison (done)
```
.venv/Scripts/python -I src/build_phase4.py
```
Code: `src/fairness.py`. The write-up is in [report/03_fair_comparison.md](report/03_fair_comparison.md).

Outputs:
- `outputs/tables/p4_batters.csv`, `p4_bowlers.csv`: one row per player. Values are per 100 balls (batting) or per 120 balls (bowling).

  | Column | Meaning |
  |---|---|
  | `p_raw` | Phase 3 value under pressure |
  | `p_opp` | Average help from the opposition faced |
  | `p_adj` | Pressure value, opposition-adjusted |
  | `p_lg` | `p_adj` shrunk towards the league mean. **Primary pressure estimate.** |
  | `p_shrunk` | `p_adj` shrunk towards a prior predicted from the player's own baseline |
  | `b_shrunk` | Baseline value, shrunk |
  | `delta_shrunk` | Pressure minus baseline |
  | `p_weight_lg`, `p_se` | Weight on the player's own record; standard error |
  | `p_share_*` | Mix of the player's pressure balls by competition tier |
  | `eligible`, `active` | Eligibility flags |

- `outputs/tables/p4_*_pressure_matches.csv`: opposition-adjusted pressure value per player per match
- `outputs/tables/phase4_summary.md`

**Season par:** before anything else, Phase 4 subtracts each competition-season's average batting and bowling value (`season_par_adjust`), so an average player in every competition-season is worth 0. This removes scoring drift such as the post-2023 rise in IPL run rates, which the Phase 3 models (fitted on all seasons together) would otherwise show as batters beating par. The offsets are listed at the top of `phase4_summary.md`.

Ratings scope (`RATING_TIERS`) is IPL and T20I only. Emerging (A-team) balls are used to train the models but are excluded from player ratings.

Settings in `fairness.py`:
- Eligibility: batters need ≥100 pressure balls in ≥15 innings; bowlers need ≥120 pressure balls in ≥15 matches. This uses raw, unweighted counts.
- `ACTIVE_FROM_YEAR` = 2025.
- `WEIGHTING`: evidence weights, i.e. how much each ball counts towards a player's rating. Ball weight = recency × competition × opponent. All three are slight tilts:
  - `recency_decay` = 0.10: each year back from the last match counts 10% less (2022 ≈ 0.63, 2026 ≈ 0.95)
  - `comp` = IPL 1.0; T20I 0.80, except T20Is against `STRONG_T20I_TEAMS` (India, Australia, England, South Africa, New Zealand), which count 1.0 like IPL (`T20I_strong`). Phase 4 flags those balls as `strong_opp_bat` / `strong_opp_bowl` in `ball_adjusted.csv.gz`.
  - `opponent` = (0.5, 1.0): facing an associate-standard side counts 0.5, an IPL-standard side 1.0, and nations in between by their strength from the opposition model (`opponent_strength()`)

  Volume is built in, because every aggregate is a sum over balls. The weights feed values, WPA, the consistency success rate and, as the amount of evidence, the shrinkage. Set `WEIGHTING = None`, or a single factor to `None`, to switch them off.

Phase 4 writes each ball's opponent strength to `ball_adjusted.csv.gz` (`opp_str_bat`, `opp_str_bowl`; 1 = average IPL side, 0 = average associate side). It also adds these columns to `p4_*.csv`:
- `p_n_w`: weighted ball count, the amount of evidence used for shrinkage
- `p_n_eff`: effective sample size (Σw)²/Σw², used for standard errors
- `p_evidence_share`: weighted ÷ raw balls
- `p_wpa_w`: weighted WPA
- `p_ipl_n`, `p_ipl_adj100/120`: IPL-only pressure record, unweighted
- `p_opp_strength`: average strength of the opposition faced

`p_n` and `p_wpa_total` stay raw.

Phases 4 and 5 also write `phase4_info.json` (shrinkage k, weighting, the opponent table) and `phase5_info.json` (rating weights, clutch test), which the dashboard reads.

## Phase 5: Pressure Rating and top 10s (done)
```
.venv/Scripts/python -I src/build_phase5.py
```
Code: `src/rating.py`. The write-up is in [report/04_rating_and_rankings.md](report/04_rating_and_rankings.md).

Outputs:
- `outputs/tables/p5_batter_ratings.csv`, `p5_bowler_ratings.csv`: every player's components, z-scores, contributions, rating and rank
- `outputs/tables/p5_top10_batters.csv`, `p5_top10_bowlers.csv`: the top 10 with evidence columns and each player's two best pressure matches
- `outputs/tables/phase5_summary.md`

Settings in `rating.py`:
- `WEIGHTS`: the judgement weights, value / consistency / clutch / impact / volume = 0.43 / 0.19 / 0.19 / 0.14 / 0.05.
- `CV_WEIGHTS` / `ROLE_WEIGHTS` (with `USE_CV_WEIGHTS` = True): the weights actually used, set by cross-validation (`src/weight_cv.py`, below). Batters keep the judgement weights with clutch shared out (53.75 / 23.75 / 0 / 17.5 / 5); bowlers use 55 / 5 / 15 / 15 / 10. `volume` is a small track-record bonus: the log of weighted pressure balls, with the z-score capped at ±`VOLUME_Z_CAP` (2), worth at most ±0.10 rating points.
- `RECENT_NERF`: a deduction, in rating points, for too little recent pressure data.
  - **Target:** each player's target per season is `min(target_cap, own average)`: the smaller of 50 pressure balls and their own average per season (total ÷ seasons from their first season to the latest; e.g. 200 over 4 seasons = 50).
  - **Shortfall:** for each of the last three seasons (2024, 2025, 2026), the shortfall below target is raised to `power` (2), so a small dip costs little and an almost empty season costs a lot.
  - **Year weights:** the shortfalls are weighted by `year_weights` (0.2 / 0.3 / 0.5).
  - **Cap:** the deduction is at most `max_points` (0.40). Seasons before a player's debut don't count.
  - **Switch off:** `rate(..., nerf=None)`.
  - **Per-player columns:** `recent_avg`, `recent_target`, `recent_seasons`, `recent_balls_0/1/2` (pressure balls in each of the three seasons), `recent_shortfall`, `contrib_recent`.
- `VALUE_SOURCE`: `p_shrunk` for bowlers (chosen by the Phase 6 predictive check). For batters it is `blend`: 75% `p_lg` (pressure record shrunk to the league mean) and 25% `p_shrunk` (shrunk towards what the batter's normal form predicts). The `p_shrunk` share is set by `BLEND_SHARE` (0.25). The blend counts normal form, so a poor batter with a good pressure record (e.g. Sam Curran, 104th of 105 on normal form) can't rank highly on the pressure record alone.
- `REQUIRE_ACTIVE` = True
- `MIN_MATCH_BALLS` = 5 for batters, 6 for bowlers
- `CONSISTENCY_PRIOR_MATCHES` = 10

If a role's clutch variance isn't distinguishable from noise, the clutch weight is redistributed automatically. This happens for batters, who use 53.75 / 23.75 / 0 / 17.5 plus 5% track record. Track record is never part of the redistribution. The consistency component and impact are evidence-weighted too (`success_rate_w`, `p_wpa_w`).

### Cross-validated weights
```
.venv/Scripts/python -I src/weight_cv.py 5 10
```
Run after Phase 5 (it reads the ranking pool from `p5_*_ratings.csv`), then rerun Phase 5. It tests which mix of the five components best picks out the players who perform under pressure in matches the rating hasn't seen:
- **Folds:** the IPL and T20I matches are split into 5 folds, 10 times over, keeping each match whole (50 folds).
- **Training:** for each fold, every player's components are built from the other four folds, with the same evidence weights, shrinkage and z-scoring as the main rating.
- **Target:** the player's opposition-adjusted pressure value per ball in the held-out fold (pool players with at least 20 pressure balls in it).
- **Scoring:** every weight mix on a 5% grid is scored by the ball-weighted correlation between rating and target, averaged over the 50 folds.
- **Choice:** mixes are compared with the best through the paired per-fold difference, with the Nadeau–Bengio correction for overlapping folds. Among the mixes not clearly worse than the best (within one corrected standard error), the one closest to the judgement weights is used, with ties broken by the higher score.

Result:
- **Batters:** no mix is clearly better (judgement weights r = 0.027, best 0.059, difference inside one standard error of 0.042), so the judgement weights stand.
- **Bowlers:** the judgement weights (r = 0.154) were clearly beaten by leaning on value (value alone 0.198, about 1.5 standard errors better). The rating now uses 55 / 5 / 15 / 15 / 10 (r = 0.177).

Outputs: `p8_weight_cv.md`, `p8_weight_cv_grid_{bat,bowl}.csv`, `phase8_weights.json`. `rating.py` holds the chosen weights as constants, and the script flags it if they no longer match.

## Phase 6: reliability (done)
```
.venv/Scripts/python -I src/build_phase6.py 500 50
```
The two arguments are the number of bootstrap replicates and the number of split-halves. Code: `src/reliability.py`. The write-up is in [report/05_reliability.md](report/05_reliability.md).

Every check reruns the exact Phase 4 aggregation and Phase 5 rating on modified ball-level data (`outputs/ball_adjusted.csv.gz`, written by Phase 4). The models aren't refitted, so the checks measure sampling and definitional uncertainty in the ratings. Weights are held at the Phase 5 (cross-validated) values. In the bootstrap, the shrinkage hyperparameters are also held at their full-sample values; re-estimating them on resampled data under-shrinks.

Predictive check, which chose the bowling value component:
```
.venv/Scripts/python -I src/predictive_check.py 40
```
Output: `outputs/tables/p6_predictive_check.md`. It found that for bowlers, `VALUE_SOURCE = p_shrunk` (in `rating.py`) predicts unseen pressure performance about twice as well as `p_lg`.

Part 2 of the same script is a forward-in-time check of the evidence weights. It rates players on matches before each of five cut-off dates, with and without each factor, then correlates the ratings with pressure performance in the next 12 months, overall and in the IPL alone. The weights help slightly for batters and are neutral for bowlers. Results are in `p6_weighting_check.csv`.

Phase 6 runs the split-half and temporal checks on unweighted records, because they test whether pressure skill is a stable trait. The bootstrap and sensitivity runs use the evidence weights. Sensitivity adds six weighting variants (no weighting, recency only, no recency, no IPL tilt, no opponent factor, all factors twice as strong), plus "no track-record bonus" and "no recent-data nerf".

Outputs in `outputs/tables/`:
- `p6_bootstrap_{bat,bowl}.csv`: median rank, 90% rank range, and P(top 5 / top 10 / in pool) from resampling matches
- `p6_split_half.csv`, `p6_temporal_split.csv`: stability of pressure, baseline and clutch values
- `p6_sensitivity.csv`: top-10 overlap under alternative pressure definitions and weights
- `p6_seasons_top10_{bat,bowl}.csv`: season-by-season pressure value for each top-10 player
- `phase6_summary.md`

## Phase 7: robustness, benchmark and roles (done)
```
.venv/Scripts/python -I src/build_phase7.py 500
.venv/Scripts/python -I src/benchmark_check.py
.venv/Scripts/python -I src/roles.py
```
- `build_phase7.py` measures how robust each pick is to all the judgement calls at once. Each of 500 replicates redraws every setting within a sensible range and resamples matches, then re-rates everyone:
  - the pressure definition: blend, knockout boost, cut-off;
  - the evidence weights;
  - the rating weights, drawn around each role's cross-validated weights;
  - the track-record weight, from 0 to twice its main value;
  - the recent-data nerf.

  A player's share of replicates in the top 10 sets their tier: Lock ≥ 75%, Strong 50–75%, Contender 25–50%, Long shot < 25%. Outputs: `p7_robust_{bat,bowl}.csv`, `p7_settings_drawn.csv`, `phase7_summary.md`.
- `benchmark_check.py` tests, forward in time, whether the rating predicts next-year pressure performance better than simple stats (pressure and overall strike rate, average, economy, wicket rate). It uses two targets: the context-adjusted value and the raw pressure strike rate or economy. Outputs: `p7_benchmark.csv`, `p7_benchmark.md`.
- `roles.py` labels every ranked player's role. Batters are labelled by typical batting position: 1–2 opener, 3–4 top order, 5–6 middle order, 7+ finisher. Bowlers are labelled by the phase where they bowl most (with a second phase if it is ≥ 30% of their balls), plus pace or spin. Outputs: `p7_roles_{bat,bowl}.csv`, `p7_roles.md`.

## Final selection
```
.venv/Scripts/python -I src/final_selection.py
```
The submitted top 10s are picked by the robust top-10 probability from Phase 7. With `TIE_BAND` (batters 5 points, bowlers 0), players within that distance of the 10th-highest probability are treated as tied, and the remaining places go to them in Pressure Rating order. The list is shown in probability order. Outputs: `final_top10_{batters,bowlers}.csv` (with role, tier, rating rank, evidence and best pressure matches), `final_ranks_{bat,bowl}.csv` and `final_selection.md`. The dashboard ranks by this order and shows each player's rating rank alongside. A one-page summary for judges is in [SUBMISSION_SUMMARY.md](SUBMISSION_SUMMARY.md).

> To rebuild everything: run `build_phase1.py` through `build_phase5.py`, then `weight_cv.py 5 10`, `build_phase5.py` again, `predictive_check.py`, `build_phase6.py 500 50`, `build_phase7.py 500`, `benchmark_check.py`, `roles.py`, `final_selection.py` and the two dashboard scripts.

## Dashboard
```
.venv/Scripts/python -I src/generate_dashboard_data.py
.venv/Scripts/python -I src/build_dashboard_html.py
```
Writes `dashboard.html`, a single self-contained file that opens offline. The page layout and styling live in `src/dashboard_template.html`. The builder fills it with `dashboard_data.json` plus a few Phase 2, 3 and 6 tables (pressure by over, chase heatmap, wicket value by over, split-half reliability) for the "How it works" walkthrough.

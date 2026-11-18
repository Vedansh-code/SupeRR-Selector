# Report draft, section 5: Reliability and limitations

*Numbers come from `outputs/tables/phase6_summary.md` and `p6_predictive_check.md`. Every check reruns the exact rating pipeline (`src/reliability.py`).*

## 5.1 How certain is each rank? Bootstrap by match
We resampled the 837 IPL and T20I matches with replacement 500 times and re-rated every player each time, with the same evidence weights as the main ratings (section 3.4). The shrinkage settings (league means, `k`, the baseline prior, the clutch variance) and the recency reference date were held at their full-sample values.

**Why hold them fixed.** Re-estimating them on resampled data counts the resampling noise as extra spread between players. Every replicate then under-shrinks, and the rank ranges drift towards raw pressure records. Our first run had exactly this problem: Bumrah's 90% range (11–71) didn't even contain his actual rank of 8. Holding the settings fixed removes the bias. The bootstrap then measures what we want: uncertainty from the limited matches each player has.

**Batters**

| Rank | Player | Median bootstrap rank | 90% range | P(top 10) |
|---|---|---|---|---|
| 1 | Shreyas Iyer | 2 | 1–14 | 93% |
| 2 | Suryakumar Yadav | 4 | 1–23 | 79% |
| 3 | Heinrich Klaasen | 4 | 1–22 | 78% |
| 4 | Virat Kohli | 8 | 2–38 | 62% |
| 5 | Tim David | 13 | 2–61 | 43% |
| 6 | Rohit Sharma | 12 | 2–57 | 42% |
| 7 | Ashutosh Sharma | 13 | 2–57 | 33% |
| 8 | Tilak Varma | 13 | 2–66 | 43% |
| 9 | Cameron Green | 16 | 3–55 | 34% |
| 10 | Sam Curran | 17 | 3–56 | 32% |
| *11* | *Yashasvi Jaiswal* | *17* | *4–61* | *32%* |
| *12* | *Shashank Singh* | *18* | *4–60* | *24%* |

**Bowlers**

| Rank | Player | Median bootstrap rank | 90% range | P(top 10) |
|---|---|---|---|---|
| 1 | Krunal Pandya | 4 | 1–19 | 82% |
| 2 | Varun Chakravarthy | 4 | 1–17 | 85% |
| 3 | Sunil Narine | 5 | 1–23 | 74% |
| 4 | Jasprit Bumrah | 6 | 1–21 | 76% |
| 5 | Kuldeep Yadav | 7.5 | 1–30 | 65% |
| 6 | Matheesha Pathirana | 9 | 2–27 | 61% |
| 7 | Josh Hazlewood | 8 | 1–39 | 58% |
| 8 | Mustafizur Rahman | 9 | 2–26 | 55% |
| 9 | Bhuvneshwar Kumar | 11 | 1–42 | 48% |
| 10 | Rashid Khan | 13 | 2–44 | 39% |
| *11* | *Trent Boult* | *17.5* | *4–49* | *25%* |
| *12* | *Nathan Ellis* | *17* | *5–43* | *24%* |

**Reading the tables:**
- **Batters:** the top four are clear: each makes the top 10 in about 60% or more of resamples, and Shreyas Iyer in 93%. From rank 5 down the odds are below even (32–43%), and ranks 7–11 are close to interchangeable. Jaiswal (11th) has the same 32% as Curran (10th).
- **Bowlers:** the top eight each make the top 10 in more than half the resamples, and Bhuvneshwar in 48%. Rashid Khan (10th, 39%) is clearly ahead of the next names, Boult (25%) and Ellis (24%).
- We keep the point-estimate order as the ranking and report these near-ties. The order within ranks 5–10 should be read as approximate.

## 5.2 Does pressure performance repeat? Split-half and temporal stability
Matches were split into two random halves 50 times. Each player's opposition-adjusted value was computed in each half, using players with at least 40 pressure balls and 150 baseline balls in both halves.

| Correlation between halves | Batters | Bowlers |
|---|---|---|
| Pressure value | 0.03 | 0.03 |
| Baseline (non-pressure) value | 0.32 | 0.17 |
| Clutch (pressure − baseline) | 0.11 | −0.10 |
| Pressure value vs **other half's baseline** | 0.02 | **0.18** |

The temporal split (2022–23 vs 2024–26) agrees. Batting pressure value has a correlation of 0.01 between eras. Bowlers' 2022–23 pressure value has a correlation of 0.09 with their 2024–26 pressure value, and their earlier baseline correlates 0.39 with their later pressure value.

These checks ask whether pressure performance is a stable trait, so they use **unweighted** records (each ball still measured against its own season's par). They are also why the recency factor in the evidence weights (3.4) is only a slight tilt. Old form is less informative for batters, but bowlers' earlier quality clearly carries forward, so discarding old seasons outright would throw away real signal.

**What this means:**
- With 100–700 pressure balls per player, a pressure record is a **noisy measure**. Most of the spread between players in any given sample is luck. This is why the method uses heavy shrinkage, eligibility thresholds and a consistency component rather than raw pressure averages.
- For **bowlers**, overall quality is a better guide to pressure performance than the pressure record itself. This motivated the predictive choice in section 4.2b, which nearly doubled the bowling rating's out-of-sample predictive power (0.093 → 0.171).
- For **batters**, nothing predicts pressure performance well, including overall quality. The batting list is best read as **who has delivered most under pressure in 2022–26**, tilted slightly towards recent, IPL and strong-opposition evidence, with the uncertainty in 5.1.

## 5.3 Consistency across seasons
For each top-10 player, the season-by-season opposition-adjusted pressure value (`p6_seasons_top10_*.csv`, and the IPL/T20I season chart in each dashboard profile) shows how evenly their performance is spread:
- **Positive in every season they had pressure balls:** Suryakumar (5/5), Ashutosh Sharma (3/3); and among bowlers Krunal Pandya, Kuldeep Yadav and Bhuvneshwar Kumar (5/5 each). Most others are positive in 4 of 5 seasons.
- **Less even:** Kohli, Tim David and Bumrah (3/5), and Josh Hazlewood (2/5).

## 5.4 Sensitivity to our choices
Overlap with the main top 10 when one choice is changed:

| Variant | Batters | Bowlers |
|---|---|---|
| High pressure = top 15% of balls | 9 | 9 |
| High pressure = top 25% of balls | 7 | 8 |
| Stakes (leverage) only, no stress component | 7 | 7 |
| 50/50 stakes and stress | 7 | 8 |
| No knockout boost | 9 | 10 |
| Evidence weights: none (every ball equal) | 7 | 10 |
| Evidence weights: recency only | 9 | 10 |
| Evidence weights: no recency factor | 9 | 9 |
| Evidence weights: no IPL tilt | 9 | 10 |
| Evidence weights: no opponent factor | 9 | 10 |
| Evidence weights: all factors twice as strong | 9 | 9 |
| Weights: value only | 8 | 8 |
| Weights: equal | 9 | 7 |
| Weights: no impact | 8 | 9 |
| Weights: no consistency | 8 | 9 |
| Weights: value and consistency only | 8 | 8 |
| Weights: no track-record bonus | 10 | 9 |
| Weights: no recent-data nerf | 9 | 9 |

The variants keep the rest of the final method fixed: season par, the rating weights, track-record bonus and recent-data nerf stay on unless the row says otherwise.

- **The adjustments added on top of the original method barely move the lists.** The overlaps are measured against the rating's own top 10. Every added-adjustment variant changes at most one name, with one exception: switching off the evidence weights entirely changes three batters.
- **Weights and thresholds** move one or two names at the margin.
- **How pressure is defined matters more.** Defining it by match stakes alone keeps only 4 to 6 of each top 10. This shows the definition is a substantive choice, not a technicality, and it's why section 1 justifies the blend. Stakes alone misses innings-1 collapses, and stress alone rewards lost causes.
- **A core is stable across the 18 variants** (number of variants each player stays in the top 10):
  - **Batters:** Shreyas Iyer (18), Suryakumar Yadav (18), Heinrich Klaasen (18), Tim David (18), Abhishek Sharma (18).
  - **Bowlers:** Varun Chakravarthy (18), Sunil Narine (18), Kuldeep Yadav (18), Matheesha Pathirana (18), Krunal Pandya (17), Jasprit Bumrah (17), Josh Hazlewood (17).
- **Caveat:** the pressure-definition variants relabel which balls count as high pressure, but don't retrain the expectation models, which use the original pressure percentile as an input. They are therefore an approximation.

## 5.5 Robustness to every judgement call at once (Phase 7)
Section 5.4 changes one choice at a time. Phase 7 (`src/build_phase7.py`) changes all of them together. Each of 500 re-runs redraws every setting at random within a sensible range, resamples the matches, and re-rates everyone. The settings redrawn are:
- **pressure definition:** stakes share 55–75%, knockout boost 1.00–1.25, cut-off top 15/20/25%;
- **recency decay:** 5–15% a year;
- **T20I weight:** 0.7–0.9 against non-top-5 opponents;
- **weakest-opponent weight:** 0.35–0.65;
- **rating weights:** drawn around the main weights;
- **track-record weight:** 0–10%;
- **recent-data nerf:** maximum 0.25–0.55, target cap 40/50/60, linear or squared shortfall.

A player's share of re-runs in the top 10 is their **robust top-10 probability**, which sets their tier: Lock ≥ 75%, Strong 50–75%, Contender 25–50%, Long shot < 25%.

| Batters (rating rank) | Robust odds | Tier | | Bowlers (rating rank) | Robust odds | Tier |
|---|---|---|---|---|---|---|
| Suryakumar Yadav (2) | 95% | Lock | | Varun Chakravarthy (2) | 89% | Lock |
| Heinrich Klaasen (3) | 90% | Lock | | Sunil Narine (3) | 83% | Lock |
| Shreyas Iyer (1) | 88% | Lock | | Jasprit Bumrah (4) | 73% | Strong |
| Tim David (4) | 85% | Lock | | Krunal Pandya (1) | 71% | Strong |
| Abhishek Sharma (5) | 73% | Strong | | Kuldeep Yadav (5) | 68% | Strong |
| Tilak Varma (8) | 57% | Strong | | Matheesha Pathirana (6) | 58% | Strong |
| Virat Kohli (6) | 40% | Contender | | Josh Hazlewood (7) | 55% | Strong |
| Ashutosh Sharma (7) | 31% | Contender | | Rashid Khan (10) | 54% | Strong |
| Nicholas Pooran (16) | 29% | Contender | | Bhuvneshwar Kumar (9) | 37% | Contender |
| Andre Russell (11) | 27% | Contender | | Noor Ahmad (15) | 35% | Contender |
| *Rovman Powell (22)* | *30%* | *Contender* | | *Mustafizur Rahman (8)* | *33%* | *Contender* |
| *Cameron Green (9)* | *22%* | *Long shot* | | *Axar Patel (13)* | *22%* | *Long shot* |
| *Yashasvi Jaiswal (10)* | *12%* | *Long shot* | | | | |

**Final selection rule** (`src/final_selection.py`): pick by robust odds. With 500 re-runs each probability carries about ±2 points of simulation noise. So, for batters, players within 5 points of the 10th-highest are treated as tied, and the remaining places go to them in rating order:
1. Players clearly above that band are in.
2. The remaining places go to tied players in rating order.

The list is shown in odds order.
- **Batters:** Ashutosh (31%), Powell (30%), Pooran (29%) and Russell (27%) fall in the band for the last three places. They go to Ashutosh (rating #7), Russell (#11) and Pooran (#16), ahead of Powell (#22). Compared with the rating order, Pooran and Russell come in for Cameron Green and Yashasvi Jaiswal.
- **Bowlers:** Noor Ahmad (35%) comes in for Mustafizur (33%), a near-tie.

The rule settles the close calls with one stated criterion rather than small differences in a single rating. Without the tie band, Rovman Powell, whose IPL pressure value is −22 per 100, would have taken a place on a 1-point odds margin.

## 5.6 Does the rating beat simple stats?
`src/benchmark_check.py` repeats the forward-in-time design. For five cut-offs (2024–26), every predictor is computed from matches before the cut-off for the same players, then compared with the following 12 months. Correlations are averaged across cut-offs:

| Next-year target | Our rating | Our value component | Pressure SR / economy | Overall SR / economy |
|---|---|---|---|---|
| Batters: context-adjusted pressure value | −0.10 | −0.11 | 0.01 | −0.12 |
| Batters: raw pressure strike rate | −0.03 | −0.04 | 0.05 | −0.01 |
| Bowlers: context-adjusted pressure value | 0.25 | **0.34** | 0.21 | 0.33 |
| Bowlers: raw pressure economy | 0.28 | 0.35 | 0.52 | 0.60 |

- **Bowlers:** our value component is the best forecaster of next-year context-adjusted pressure performance, level with overall economy. Its top-10 picks did best the following year: +15 runs per 120 balls above average, against +6 for the ten best economies. Raw economy predicts raw economy better, largely because it reflects role: a bowler's economy correlates 0.48 with their share of death overs. The full rating forecasts a little less than its value component, because consistency, clutch and impact describe what a bowler has done rather than predict it.
- **Batters:** no predictor forecasts next-year pressure batting, including strike rate and average. The batting list therefore ranks who has delivered most under pressure in 2022–26, which is what this data can support.

## 5.7 Limitations
1. **Small pressure samples.** This is the main limitation, as quantified above. Ranks 4–10 carry wide uncertainty.
2. **The innings-1 win-probability model** is only moderately predictive (AUC 0.68), so first-innings stakes are measured less precisely than chase stakes.
3. **Judgement calls** in the pressure definition (the 65/35 blend, the stress formula, ×1.15 for knockouts, the top-20% cut-off), in the rating weights and in the evidence weights (10% per year, T20I at 80% except against the five strongest nations, associate opposition at 50%) and the recent-data nerf (target capped at 50 balls a season, squared shortfall, at most 0.40 rating points). Their effect is shown in 5.4. The forward-in-time test of the evidence weights (section 3.4) has only about 30–40 players per cut-off, so it is noisy.
4. **Opposition model.** It uses all balls and ridge regression, so effects for associate players lean on the team-tier terms. A-team games are excluded from ratings.
5. **Not modelled:** venue is in the data but isn't used, and there is no pitch, weather or ball-tracking quality information. Byes and leg-byes, and non-striker run-outs, are attributed simply.
6. **Activity filter.** Retired or inactive players (last played before 2025) are excluded by design. This is a selection policy, not a finding.
7. **Name matching.** Player names come from the ball-by-ball file and must be matched to the Unstop dropdowns by hand.

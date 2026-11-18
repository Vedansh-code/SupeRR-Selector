# Report draft, section 4: The Pressure Rating and the top 10s

*Numbers come from `outputs/tables/phase5_summary.md`. The full tables are `p5_batter_ratings.csv` and `p5_bowler_ratings.csv`.*

## 4.1 Rating formula
Each component is z-scored within the ranking pool (eligible and active players: 105 batters, 96 bowlers), then combined with these weights. Every component uses the evidence weights from section 3.4: each ball counts slightly more if it is recent, in the IPL and against a strong side.

| Component | What it measures | Weight |
|---|---|---|
| **Value** | Opposition-adjusted runs above an average player under the same pressure, per 100 balls (batting) or per 120 balls (bowling), evidence-weighted and shrunk for sample size. Bowlers are shrunk towards what their own normal form predicts. For batters, value is 75% the pressure record shrunk to the league mean and 25% the same record shrunk towards their normal form (see 4.2b). | 43% |
| **Consistency** | Weighted share of pressure matches (at least 5 balls faced, or 6 balls bowled) in which the player beat the average player. Shrunk towards the pool rate with a 10-match prior. | 19% |
| **Clutch** | Pressure value minus the player's own baseline value, empirically shrunk using both standard errors | 19% |
| **Impact** | Weighted win probability added in pressure situations | 14% |
| **Track record** | How much pressure cricket the player has done: the log of their weighted pressure balls, with the z-score capped at ±2 | 5% |

**Why these weights.** Value is the most direct answer to the brief, so it gets the largest share. Consistency answers "delivers *consistently*". Clutch answers "compared with their usual level". Impact rewards players who have actually decided many games, not just played efficiently in a few. Section 5 tests how sensitive the rankings are to these weights.

**Why a track-record bonus.** Shrinkage (3.5) already discounts small samples, but it only pulls them towards average. It never credits a player for sustaining a level over a long record. Yet a player rated 1.4 over 500 pressure balls has shown more than one rated 1.5 over 130. The track-record component adds a deliberately small bonus for that:
- **Size:** across the whole pool it moves a rating by at most ±0.10. Ratings range from about −2 to +3, and the gaps between neighbouring ranks in the batting top 10 run from 0.02 to 0.7.
- **Log scale:** each doubling of the record counts the same, so 130 → 260 balls is worth as much as 260 → 520, and very long records don't run away with it.
- **Weighted balls:** recent IPL balls against strong sides count more here too.

In the example above, the 500-ball player now edges ahead by about 0.02.

**Recent-data nerf.** The opposite case is a player who has had too little pressure cricket lately. Their rating rests more on older evidence, so they lose some rating, in rating points, outside the weights:
- **Target per season:** the smaller of 50 pressure balls and the player's own average per season, from their first season in the data to 2026. For example, 200 pressure balls over 4 seasons gives a target of 50; 120 over 4 gives 30. The cap means regular players aren't penalised for dipping below an unusually high personal average. Seasons before a player's debut don't count against them.
- **Shortfall, squared:** for each of 2024, 2025 and 2026, how far below target the player fell (0 = at or above it, 1 = no pressure balls), squared. A small dip costs very little, while an almost empty season costs a lot.
- **Year weights increase towards the present:** 2024 counts 20%, 2025 30% and 2026 50%.
- **Deduction:** 0.40 × weighted, squared shortfall.
  - Half the target in 2026 costs 0.05.
  - Missing 2026 entirely costs 0.20.
  - Missing all three seasons costs the full 0.40.

Players who play regularly lose almost nothing. Half the pool loses less than 0.05. The heavy deductions, 0.20–0.33, fall on players whose pressure exposure has nearly dried up, such as Moeen Ali, R Ashwin, Deepak Hooda, Devon Conway, Obed McCoy and Anrich Nortje.

In the top 10s:
- **Rohit Sharma** (1 pressure ball in 2025) loses 0.11.
- **Mustafizur** (9 in 2026) loses 0.13.
- **Curran** (21 in 2026) loses 0.09, and **Pathirana** (20 in 2026) 0.07.
- **Just outside:** Boult (11 in 2026) loses 0.12 and is 11th. Shashank Singh (9 in 2026 against a target of 29) loses 0.10 and is 12th.

## 4.2 A data-driven rule for clutch
Before using clutch, we test whether it can tell players apart at all. If every player had the same true clutch effect, the observed spread would come from sampling noise alone.

| | Observed variance of (pressure − baseline) | Expected from noise alone | True between-player variance |
|---|---|---|---|
| Batters (per 100 balls) | 1,205 | 1,329 | **≤ 0: not detectable** |
| Bowlers (per 120 balls) | 1,646 | 1,529 | 116 (true SD ≈ 11 runs per 20 overs) |

- **Batters:** there is no detectable difference between batters in rising above their usual level. Their pressure deltas are what pure chance would produce. Ranking batters on that number would be ranking noise, so its 19% is redistributed proportionally to value, consistency and impact. Track record stays at 5%. **Batting weights used: value 54%, consistency 24%, impact 18%, track record 5%.** Batters are still rated *under pressure*, because value and consistency are measured on pressure balls only.
- **Bowlers:** a small but real clutch effect exists, so the component keeps its 19%. With heavy shrinkage, it only separates bowlers whose over-performance is large and well sampled.

This is a substantive finding for the report. For batters, "who performs best under pressure" is answered by sustained pressure performance and consistency, not by a special pressure-only gear. The same conclusion holds with and without evidence weighting.

## 4.2b Choosing the value estimate by out-of-sample prediction
A selector cares about the *next* pressure situation, so we tested which estimate of pressure value best predicts a player's opposition-adjusted pressure performance in matches it hasn't seen. Across 40 random 50/50 splits of matches, each estimate was computed on one half and correlated with actual pressure value in the other half. Players needed at least 40 pressure balls in each half. Random halves mix all seasons, so this test uses unweighted records. The forward-in-time test of the evidence weights is in section 3.4.

| Estimate computed on half A | Batters | Bowlers |
|---|---|---|
| Pressure record shrunk to league mean (`p_lg`) | **0.066** | 0.100 |
| Pressure record shrunk towards own baseline form (`p_shrunk`) | 0.026 | 0.209 |
| Baseline form only | 0.033 | 0.239 |
| Full rating with `p_lg` as value | 0.066 | 0.093 |
| Full rating with `p_shrunk` as value | 0.048 | **0.171** |

- **Bowlers:** a bowler's overall quality carries most of the signal about how they'll bowl under pressure. The baseline-informed estimate nearly doubles the rating's predictive power, from 0.093 to 0.171, so the bowling value component uses `p_shrunk`. With little pressure evidence, a bowler is assumed to bowl under pressure as their normal form predicts. A strong pressure record above or below that still moves them in proportion to its sample size. The forward test agrees: `p_shrunk` beats `p_lg` for bowlers.
- **Batters:** no estimate predicts well (all below 0.07). `p_lg` is marginally best, but using it alone ignores normal form completely. A batter who is poor in normal play but has a good pressure record could then rank as a top pressure player: Sam Curran is 104th of 105 on normal form yet was 10th on `p_lg`. Batting value therefore blends in normal form: 75% `p_lg` and 25% `p_shrunk`. We compared shares of 0%, 25%, 50%, 75% and 100%:
  - 25% is enough to drop Curran (to 14th) and Rohit Sharma (to 11th), whose normal form is very poor.
  - Higher shares start to lift strong all-round batters with thin or absent recent pressure records, such as Andre Russell (16th at 25%, 11th at 50%, 8th at 100%).
  - The predictive cost is negligible, because all the batting correlations are near zero.

The check is reproducible with `src/predictive_check.py`, and results are in `outputs/tables/p6_predictive_check.md`.

## 4.3 Top 10 batters
All values are measured against their own competition-season par (3.2). *Weight kept* is how much of the player's pressure record counts after evidence weighting (3.4). *IPL value* is their opposition-adjusted pressure value in IPL matches alone, unweighted. Value is weighted and opposition-adjusted before shrinkage, then rated after shrinkage. The success rate is weighted, shown with the raw count of pressure matches. *Recent balls* are pressure balls in 2024 / 2025 / 2026, with the player's target per season. *Track* and *Nerf* are the track-record bonus and the recent-data deduction, in rating points.

| # | Player | Pressure balls (IPL share) | Weight kept | Pressure SR (expected) | IPL value per 100 | Normal form per 100 | Value per 100 (adjusted → rated) | Success rate | Recent balls (target) | Track | Nerf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Shreyas Iyer | 416 (75%) | 78% | 167.5 (153.5) | +29.2 | +4.6 | +31.4 → +11.2 | 89% of 23 | 29 / 87 / 190 (target 50) | +0.09 | −0.01 |
| 2 | Suryakumar Yadav | 568 (59%) | 67% | 162.9 (146.0) | +37.0 | +20.6 | +29.8 → +14.9 | 68% of 40 | 66 / 99 / 41 (target 50) | +0.10 | −0.01 |
| 3 | Heinrich Klaasen | 298 (83%) | 76% | 169.8 (147.0) | +44.9 | +14.3 | +41.0 → +13.7 | 80% of 19 | 63 / 25 / 82 (target 50) | +0.05 | −0.03 |
| 4 | Tim David | 436 (53%) | 69% | 165.1 (143.5) | +18.3 | +24.4 | +17.4 → +11.7 | 73% of 34 | 63 / 112 / 23 (target 50) | +0.09 | −0.06 |
| 5 | Abhishek Sharma | 207 (74%) | 76% | 187.4 (160.2) | +16.1 | +26.3 | +24.6 → +12.5 | 80% of 14 | 34 / 70 / 57 (target 41) | +0.01 | 0 |
| 6 | Virat Kohli | 301 (82%) | 75% | 162.1 (156.0) | +41.4 | +4.4 | +33.7 → +9.9 | 82% of 16 | 62 / 84 / 55 (target 50) | +0.05 | 0 |
| 7 | Ashutosh Sharma | 128 (100%) | 82% | 166.4 (148.4) | +43.6 | +8.5 | +44.0 → +9.2 | 74% of 12 | 49 / 47 / 32 (target 43) | −0.03 | −0.01 |
| 8 | Tilak Varma | 673 (57%) | 70% | 143.7 (143.4) | +6.7 | +8.8 | +13.7 → +8.2 | 57% of 44 | 91 / 216 / 140 (target 50) | +0.10 | 0 |
| 9 | Cameron Green | 269 (57%) | 68% | 161.3 (142.5) | +12.6 | +4.4 | +26.5 → +7.8 | 80% of 20 | 52 / 61 / 57 (target 50) | +0.03 | 0 |
| 10 | Yashasvi Jaiswal | 210 (94%) | 73% | 174.8 (157.6) | +28.8 | +5.1 | +28.9 → +7.8 | 74% of 12 | 44 / 42 / 26 (target 42) | +0.01 | −0.03 |

Next five in rating order: Andre Russell, Shashank Singh, Glenn Phillips, Shubman Gill, Riyan Parag. *Normal form* is the shrunk non-pressure value; batting value is 25% anchored to it (4.2b).

**Tilak Varma's** pressure value is modest (+6.4 rated). He makes the top 10 on volume and consistency: the largest pressure record in the pool (673 balls, 216 of them in 2025), T20Is that are mostly against strong sides (which count like IPL), and a 57% success rate over 44 pressure matches.

## 4.4 Top 10 bowlers
| # | Player | Pressure balls (IPL share) | Weight kept | Econ (expected) | Wkts (× expected) | IPL value per 120 | Value per 120 (adjusted → rated) | Baseline per 120 | Success rate | Recent balls (target) | Track | Nerf |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Krunal Pandya | 275 (100%) | 76% | 6.39 (7.82) | 18 (1.44×) | +54.0 | +54.0 → +11.5 | +6.5 | 79% of 18 | 52 / 79 / 41 (target 50) | +0.03 | −0.01 |
| 2 | Varun Chakravarthy | 483 (63%) | 76% | 6.99 (7.69) | 33 (1.34×) | +34.4 | +37.3 → +24.3 | +17.9 | 61% of 38 | 117 / 176 / 69 (target 50) | +0.09 | 0 |
| 3 | Sunil Narine | 340 (100%) | 76% | 6.34 (7.73) | 20 (1.20×) | +38.3 | +41.5 → +22.5 | +16.4 | 52% of 24 | 88 / 56 / 60 (target 50) | +0.05 | 0 |
| 4 | Jasprit Bumrah | 375 (79%) | 76% | 8.03 (9.11) | 18 (0.81×) | +4.5 | +21.0 → +31.2 | +26.3 | 53% of 31 | 45 / 141 / 85 (target 50) | +0.07 | 0 |
| 5 | Kuldeep Yadav | 463 (74%) | 74% | 7.96 (8.43) | 31 (1.25×) | +33.1 | +26.9 → +16.7 | +12.6 | 64% of 33 | 68 / 154 / 93 (target 50) | +0.08 | 0 |
| 6 | Matheesha Pathirana | 282 (67%) | 72% | 9.40 (10.43) | 22 (1.09×) | +40.2 | +29.6 → +17.8 | +14.0 | 76% of 22 | 101 / 77 / 20 (target 50) | +0.03 | −0.07 |
| 7 | Josh Hazlewood | 295 (72%) | 74% | 8.68 (9.22) | 26 (1.42×) | +13.9 | +19.2 → +19.3 | +16.1 | 67% of 21 | 5 / 94 / 68 (target 50) | +0.04 | −0.06 |
| 8 | Mustafizur Rahman | 349 (25%) | 60% | 7.94 (9.14) | 28 (1.21×) | +16.4 | +40.3 → +15.6 | +11.1 | 80% of 24 | 67 / 129 / 9 (target 50) | +0.03 | −0.13 |
| 9 | Bhuvneshwar Kumar | 374 (77%) | 71% | 9.56 (10.14) | 27 (1.02×) | +37.8 | +28.3 → +19.8 | +15.5 | 51% of 29 | 50 / 80 / 56 (target 50) | +0.06 | 0 |
| 10 | Rashid Khan | 645 (61%) | 65% | 7.38 (7.90) | 38 (1.13×) | +13.0 | +16.2 → +18.6 | +15.9 | 48% of 40 | 110 / 127 / 72 (target 50) | +0.10 | 0 |

Next five: Trent Boult, Nathan Ellis, Axar Patel, Eshan Malinga, Noor Ahmad. Rashid Khan (0.86) and Boult (0.83) are close at 10th–11th.

**Krunal Pandya is #1 despite a modest rated value** (+11.5, because his normal form is only +6.5). He leads clearly on the pressure-specific components: 79% of pressure matches won, the biggest positive clutch effect in the pool, and strong win impact. His entire pressure record is in the IPL.

**Bumrah is the opposite case.** His pressure economy is still a run under expectation (8.03 vs 9.11), but he takes fewer wickets than expected under pressure (0.81×) and his clutch effect is negative. His elite baseline (+26.3, the best in the pool) is what places him 4th. On the predictive check, that baseline is the best available guide to how he'll bowl in the next pressure spell.

## 4.5 What changed compared with the original rating
The lists change only at the margins. 9 of 10 batters and 9 of 10 bowlers are the same as in the original rating, which had no season par, evidence weights, track-record bonus or recent-data nerf. Curran replaces Reeza Hendricks, and Rashid Khan replaces Nathan Ellis.

| Player | Rank original → now | Pressure balls in IPL | Why |
|---|---|---|---|
| Sam Curran | 12 → 10 | 57% | Improving form (+27 → +65 per 100), long record; a thin 2026 costs 0.09 |
| Rashid Khan (bowl) | 12 → 10 | 61% | Largest pressure record among bowlers (645 balls), mostly in the high-scoring recent IPL, now judged against its own par |
| Reeza Hendricks | 9 → 19 | 0% | Strong T20I numbers but no IPL record, a recent dip (+59 → +10) and no 2026 pressure balls (−0.20) |
| Nathan Ellis (bowl) | 9 → 12 | 48% | Over half his pressure balls are T20Is, his form dipped (+50 → +25), and his 2024 and 2026 were thin (−0.09) |
| Josh Hazlewood (bowl) | 4 → 7 | 72% | Only 5 pressure balls in 2024 (−0.06) |
| Shashank Singh | 13 → 12 | 100% | All recent IPL (lifted by the old par), and only 9 pressure balls in 2026 (−0.10) |

**Recency is a slight tilt, by design.** A player who was strong in 2022–24 and weaker since loses a little ground but isn't wiped out. Mohsin Khan (+67 → −15 per 120) drops from 13th to 21st. The track-record bonus and the recent-data nerf mostly reorder near-ties.

## 4.6 Roles and the submitted lists
The tables in 4.3–4.4 are in Pressure Rating order. The **submitted** top 10s use the robust selection rule in section 5.5: pick by how often a player makes the top 10 when every setting is redrawn, with batters within 5 points of the cut-off settled by rating.
- **Batters:** compared with the rating order, the rule brings in Nicholas Pooran (rating #16) and Andre Russell (#11) for Cameron Green (#9) and Yashasvi Jaiswal (#10).
- **Bowlers:** the rule brings in Noor Ahmad for Mustafizur Rahman.

Roles (`src/roles.py`) come from typical batting position, and for bowlers from the phase in which they bowl most.

| Submitted batters | Role | | Submitted bowlers | Role |
|---|---|---|---|---|
| Suryakumar Yadav | Top order | | Varun Chakravarthy | Middle overs · spin |
| Heinrich Klaasen | Middle order | | Sunil Narine | Middle overs · spin |
| Shreyas Iyer | Top order | | Jasprit Bumrah | Powerplay & death · pace |
| Tim David | Middle order | | Krunal Pandya | Middle overs · spin |
| Abhishek Sharma | Opener | | Kuldeep Yadav | Middle overs · spin |
| Tilak Varma | Middle order | | Matheesha Pathirana | Death & middle overs · pace |
| Virat Kohli | Opener | | Josh Hazlewood | Powerplay · pace |
| Ashutosh Sharma | Finisher | | Rashid Khan | Middle overs · spin |
| Nicholas Pooran | Top order | | Bhuvneshwar Kumar | Powerplay & death · pace |
| Andre Russell | Finisher | | Noor Ahmad | Middle overs · spin |

**Squad shape:**
- **Batters:** 2 openers (Kohli, Abhishek), 3 top-order players (Suryakumar, Iyer, Pooran), 3 middle-order players (Klaasen, David, Tilak) and 2 finishers (Ashutosh, Russell).
- **Bowlers:** 6 middle-overs spinners and 4 pacers, who between them cover the powerplay and the death.

**Why Russell rather than Rovman Powell.** Places 8–11 on odds are within a few points of each other: Ashutosh 31%, Powell 30%, Pooran 29%, Russell 27%. That is within the simulation noise, so the tie is settled by rating. Russell (rating #11) takes the place over Powell (#22). Two-thirds of Powell's pressure balls are T20Is, and his IPL pressure value is −22 per 100. Russell had no pressure balls in 2026; the recent-data deduction already counts that (−0.21), but his availability should be checked.

## 4.7 Reading the lists
- **Adjusted → rated:** the second value is after sample-size shrinkage. Large values on small or less relevant samples are pulled in hardest (Rohit Sharma: 147 balls, worth 104 after weighting, +61 → +13.4). For bowlers, the rated value is pulled towards the bowler's own baseline rather than the league mean.
- **The gaps between ranks 7 and 12 are small** in both lists. Section 5's bootstrap gives each player's rank range, and the final order should be read with those ranges.
- **Value and win impact can disagree.** Mustafizur concedes well below expectation under pressure, but his teams' results in those games give negative WPA. That's why impact has a limited weight.
- **Evidence per player:** each player's two best pressure matches are listed in `p5_top10_*.csv` for the report's case studies. One example is Shreyas Iyer's IPL 2025 Qualifier against Mumbai Indians (1 June 2025), worth +30 runs.

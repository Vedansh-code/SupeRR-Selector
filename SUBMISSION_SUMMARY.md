# SupeRR Selector S2: Players Under Pressure

**Data:** the RR data pack, IPL and T20I matches from 2022 to 2026 (837 rated matches, about 200,000 deliveries).

**Rule for the lists:** *who* is in each list is decided by robustness. A player's odds are how often they make the top 10 across 500 re-runs, in each of which every judgement call in the method is redrawn and the matches are resampled. Batters within 5 points of the cut-off are treated as tied and settled by Pressure Rating, and no player who clearly dips below their own usual level under pressure can be picked. The *order* 1–10 is by Pressure Rating, so Rank 1 is the highest-rated player.

## Top 10 batters

| # | Player | Role | Top-10 odds | Pressure evidence |
|---|---|---|---|---|
| 1 | Shreyas Iyer | Top order | 90% | 416 pressure balls (75% IPL); SR 167.5 vs 153.5 expected; beat par in 89% of pressure games |
| 2 | Suryakumar Yadav | Top order | 93% | 568 pressure balls (59% IPL); SR 162.9 vs 146.0 expected; beat par in 68% of pressure games |
| 3 | Heinrich Klaasen | Middle order | 88% | 298 pressure balls (83% IPL); SR 169.8 vs 147.0 expected; beat par in 80% of pressure games |
| 4 | Virat Kohli | Opener | 44% | 301 pressure balls (82% IPL); SR 162.1 vs 156.0 expected; beat par in 82% of pressure games |
| 5 | Tim David | Middle order | 70% | 436 pressure balls (53% IPL); SR 165.1 vs 143.5 expected; beat par in 73% of pressure games |
| 6 | Abhishek Sharma | Opener | 60% | 207 pressure balls (74% IPL); SR 187.4 vs 160.2 expected; beat par in 80% of pressure games |
| 7 | Ashutosh Sharma | Finisher | 30% | 128 pressure balls (100% IPL); SR 166.4 vs 148.4 expected; beat par in 74% of pressure games |
| 8 | Tilak Varma | Middle order | 58% | 673 pressure balls (57% IPL); SR 143.7 vs 143.4 expected; beat par in 57% of pressure games |
| 9 | Cameron Green | Top order | 25% | 269 pressure balls (57% IPL); SR 161.3 vs 142.5 expected; beat par in 80% of pressure games |
| 10 | Shashank Singh | Middle order | 24% | 145 pressure balls (100% IPL); SR 172.4 vs 156.7 expected; beat par in 82% of pressure games |

Next: Nicholas Pooran (27%), Rovman Powell (27%), Andre Russell (21%).

## Top 10 bowlers

| # | Player | Role | Top-10 odds | Pressure evidence |
|---|---|---|---|---|
| 1 | Varun Chakravarthy | Middle overs, spin | 94% | 483 pressure balls (63% IPL); econ 6.99 vs 7.69 expected; 33 wickets |
| 2 | Jasprit Bumrah | Powerplay & death, pace | 93% | 375 pressure balls (79% IPL); econ 8.03 vs 9.11 expected; 18 wickets |
| 3 | Sunil Narine | Middle overs, spin | 89% | 340 pressure balls (100% IPL); econ 6.34 vs 7.73 expected; 20 wickets |
| 4 | Krunal Pandya | Middle overs, spin | 54% | 275 pressure balls (100% IPL); econ 6.39 vs 7.82 expected; 18 wickets |
| 5 | Kuldeep Yadav | Middle overs, spin | 65% | 463 pressure balls (74% IPL); econ 7.96 vs 8.43 expected; 31 wickets |
| 6 | Josh Hazlewood | Powerplay, pace | 54% | 295 pressure balls (72% IPL); econ 8.68 vs 9.22 expected; 26 wickets |
| 7 | Rashid Khan | Middle overs, spin | 70% | 645 pressure balls (61% IPL); econ 7.38 vs 7.90 expected; 38 wickets |
| 8 | Bhuvneshwar Kumar | Powerplay & death, pace | 53% | 374 pressure balls (77% IPL); econ 9.56 vs 10.14 expected; 27 wickets |
| 9 | Matheesha Pathirana | Death & middle overs, pace | 49% | 282 pressure balls (67% IPL); econ 9.40 vs 10.43 expected; 22 wickets |
| 10 | Noor Ahmad | Middle overs, spin | 48% | 363 pressure balls (66% IPL); econ 8.31 vs 8.42 expected; 21 wickets |

Next: Mustafizur Rahman (23%), Axar Patel (21%), Mitchell Santner (21%).

## How the rating works
1. **Pressure.** Every ball gets a pressure score from a win-probability model: 65% match stakes plus 35% situation stress, with a knockout boost. The top 20% of balls count as high pressure. The rebuilt match states reproduce 827 of 833 official results.
2. **Performance vs par.** Runs and wickets are measured against what an average player would produce in the same situation and season, so scoring inflation across eras doesn't flatter recent players. Normal form counts too:
   - **Bowlers:** pressure records are anchored to their normal form.
   - **Batters:** value is 75% pressure record and 25% normal-form-anchored. A poor batter with a good pressure record can't rank as a top pressure player, while the pressure record still dominates.
3. **Fairness.**
   - Each ball is adjusted for opposition quality.
   - Small samples are shrunk towards average.
   - Each ball's weight tilts slightly towards recent seasons, IPL games (and T20Is against the top five nations) and strong opponents.
4. **One rating, five parts:** value under pressure, consistency, clutch (bowlers only; for batters it couldn't be told apart from luck), win impact, and a small track-record bonus. A recent-data deduction applies to players with little pressure cricket in 2024–26. The weights are checked by cross-validation (5 folds × 10 repeats, grouped by match): for batters no mix predicts held-out pressure batting better, so the judgement weights stay (53.75 / 23.75 / 0 / 17.5 / 5); for bowlers leaning on value was clearly better, so they use value 55 / consistency 5 / clutch 15 / impact 15 / track record 10.
5. **Selection.** Re-rate 500 times with every setting redrawn and matches resampled, then pick the ten most often in the top 10.

## Why it can be trusted
- **The core is settled.** 6 batters and 8 bowlers make the top 10 in more than half of the 500 re-runs, and the ten bowlers are also exactly the rating's own top 10. The last few places in each list are close calls, settled by stated rules rather than tiny rating differences.
- **Single choices move few names.** Across 18 one-at-a-time sensitivity variants (weights, pressure definition, recency, IPL tilt, track-record bonus, recent-data deduction), the added adjustments change at most one name. The one exception: switching off the evidence weights entirely changes three batters.
- **Tested against simple stats, forward in time.**
  - **Bowlers:** our value measure is the best forecaster of next-year context-adjusted pressure performance (r = 0.34, level with overall economy). Its top 10 did best the following year: +15 runs per 120 balls above average, vs +6 for the ten best economies.
  - **Batters:** no stat, ours included, forecasts pressure batting. The batting list therefore ranks *who has delivered most under pressure*, which is what the data can support.

## Limitations
- The data covers 2022–26 only.
- Pressure samples are small: 100–700 balls per player. The last few places in each list are close calls.
- Venue and pitch are not modelled, and fielding is not counted.
- Retirements, injuries and availability are outside the data. Shashank Singh (batting #10) had only 9 pressure balls in 2026.

## Name check
All 20 names map to a single player in the data pack and match its player list.

If a submission dropdown shows a shorter form, these are the same players:
- **"Tilak Varma"** is listed as *Namboori Tilak Varma* (id 7897).
- **"Varun Chakaravarthy"** (alternative spelling) is *Varun Chakravarthy* (id 6256).

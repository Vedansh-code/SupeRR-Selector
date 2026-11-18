# Report draft, section 3: Fair comparisons

*Numbers come from `outputs/tables/phase4_summary.md`.*

## 3.1 Competition tiers
The data covers three levels of cricket:

| Tier | Matches |
|---|---|
| IPL | 367 |
| T20I | 470 (full members and associates) |
| Emerging (A-team events: Emerging Teams Asia Cup 2024, Asia Cup Rising Stars 2025) | 30 |

The source file labels both IPL and the A-team events as `T20`, so we identify IPL by competition name.

**Scope decision:** the brief asks for IPL and T20I performance. A-team events are used to *train* the models (they add context about match situations) but are **excluded from player ratings**. This matters: one bowler was ranked #2 largely on A-team games and drops below eligibility once they are excluded.

For eligible players, pressure balls come 53% from IPL and 47% from T20Is, so both competitions feed the rankings about equally.

## 3.2 Measuring each season against its own par
The expectation models in section 2 are fitted on all five seasons together, with no season term. Scoring has not been constant, though. IPL run rates rose sharply after 2023, partly because of the impact-player rule. Left alone, that drift shows up as batters "beating par" and bowlers "losing to par" in recent IPL seasons, whatever their actual skill.

Before any other adjustment, the average batting and bowling value of every competition-season is therefore removed, so the average batter and bowler in each one is worth exactly 0:

| Average value removed | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|
| IPL batting, runs per 100 balls | −6.3 | −0.6 | +3.7 | +6.0 | +6.3 |
| IPL bowling, runs per 120 balls | +6.8 | −0.3 | −4.8 | −7.6 | −7.9 |
| T20I batting, runs per 100 balls | −1.4 | +0.2 | −1.9 | −0.2 | +6.1 |
| T20I bowling, runs per 120 balls | +1.6 | +0.2 | +2.2 | +0.4 | −7.9 |

Without this, a batter in the 2025–26 IPL got about +6 per 100 balls just for the era, and a bowler lost about 8 per 120. The evidence weights in 3.4 lean towards recent IPL seasons, so the drift would otherwise have been amplified. With it, a 2022 batter and a 2026 batter are each judged against their own season. (`season_par_adjust` in `src/fairness.py`; the offsets are listed in `phase4_summary.md`.)

The effect on the lists is modest (rank correlation with the uncorrected ratings: 0.99), but it moves the right players:
- Tim David's strong 2022–23 IPL seasons came when par was low, and are now credited fairly: he rises from 8th to 5th.
- Batters whose records are almost all 2024–26 IPL, such as Ashutosh Sharma and Shashank Singh, lose a little.
- Rashid Khan, who bowls a lot in the high-scoring recent IPL, enters the bowling top 10.

## 3.3 Adjusting for opposition quality
Context adjustment doesn't capture *who* the opponent was. A batter who faced Bumrah in a tight chase did something harder than one who faced a part-time bowler from an associate side. We fit a **ridge regression on every ball faced** (about 193k):

`batting value = batter effect + bowler effect + bowling-side tier + batting-side tier`

- The tier terms (Associate, A-team) let the model recognise a weak attack even when its individual bowlers have small samples.
- The ridge penalty, chosen by 5-fold cross-validation grouped by match (α = 300), pulls players with few balls towards average.
- Each ball's value is then corrected for that specific opponent:
  - Batter: `value − (bowler effect + bowling-side tier)`
  - Bowler: `value + (batter effect + batting-side tier)`

**The model's effects match cricket knowledge** (runs per 100 balls against an average opponent):
- **Toughest bowlers to face:** Bumrah −32, Narine −22, Mohsin Khan −22, Varun Chakravarthy −22, Pathirana −21, Hazlewood −19
- **Most dangerous batters:** Sooryavanshi +52, Tim David +35, Abhishek Sharma +35, Suryakumar +32, Klaasen +29, Russell +27
- **Bowling to an Associate batting line-up** is discounted by 0.19 runs per ball (23 runs per 20 overs).
- **Batting against an Associate attack** is discounted by 0.08 runs per ball.

## 3.4 Evidence weights: how much each ball counts
Not every ball is equally good evidence for an IPL selection. A run-out of form in 2022 matters less than one in 2026. An IPL pressure spell is more relevant than a T20I one. A big score against an associate attack proves less than one against an IPL attack. The opposition adjustment in 3.2 already corrects each ball's *value* for the opponent. The evidence weight decides how much each ball *counts* in a player's average.

`ball weight = recency × competition × opponent`

| Factor | Rule | Range |
|---|---|---|
| **Recency** | Each year further back counts 10% less, measured back from the last match in the data (1 Nov 2026) | Typical match: 2022 ≈ 63%, 2023 ≈ 70%, 2024 ≈ 78%, 2025 ≈ 87%, 2026 ≈ 95% |
| **Competition** | IPL balls count fully, and so do T20Is against the five strongest T20 nations: India, Australia, England, South Africa and New Zealand. T20Is against any other side count 80%. | IPL and T20I vs top 5: 100%; other T20Is: 80% |
| **Opponent** | Facing an IPL-standard side counts fully, an associate-standard side 50%. Nations in between are placed by their strength in the opposition model (the average opposition effect of their bowlers, or batters), on a scale where the average IPL side = 1 and the average associate side = 0. | 50–100% (e.g. bowling attacks: India, Pakistan 100%; England 86%; South Africa 77%; West Indies 72%; Ireland 68%; UAE 57%) |

**Volume** needs no factor of its own: every aggregate is a sum over balls, so a season with 300 pressure balls already carries three times the weight of one with 100.

**These are deliberately slight tilts.** After weighting, the typical eligible player's pressure record keeps about 70% of its raw size (batters 69%, bowlers 70%). The range runs from about 50% for international-only players who mostly faced weaker sides to over 80% for IPL regulars with recent records.

**How the weights enter the rating:**
- The per-ball pressure and baseline values, the success rate in pressure matches and the win-probability total are all weighted averages or sums.
- The sum of weights is the player's **amount of evidence** for shrinkage (3.5). A record built mostly outside the IPL, against weak sides or long ago therefore counts as weaker evidence and is pulled further towards the prior. This is what handles players like Reeza Hendricks, who has strong T20I pressure numbers but no IPL record at all.
- Eligibility (3.6) still uses raw, unweighted counts.

**Does it predict better?** A forward-in-time test (`src/predictive_check.py`, part 2) rated players only on matches before five cut-off dates in 2024–26, with and without each factor. Each rating was then correlated with pressure performance in the following 12 months, in all matches and in the IPL alone.

| Rating's correlation with the next 12 months | No weighting | Recency only | IPL tilt only | Opponent only | All three (in use) |
|---|---|---|---|---|---|
| Batters, all matches | −0.09 | −0.08 | −0.08 | −0.09 | **−0.07** |
| Batters, IPL only | −0.06 | −0.05 | −0.06 | −0.06 | **−0.04** |
| Bowlers, all matches | 0.24 | 0.23 | 0.25 | 0.24 | **0.25** |
| Bowlers, IPL only | 0.25 | 0.23 | 0.25 | 0.25 | **0.24** |

The weights cost little or nothing in forecasting accuracy. They help slightly for batters, whose pressure form is otherwise close to unpredictable (3.5's key finding), and are neutral for bowlers. Their main justification is the selection brief: recent, IPL-relevant evidence against strong opposition should count for a bit more.

All three settings are in `WEIGHTING` in `src/fairness.py`.

## 3.5 Sample size: empirical-Bayes shrinkage
Even the most exposed players have only 100–700 pressure balls, so raw pressure numbers are noisy. Each player's opposition-adjusted, weighted pressure value per ball is shrunk towards a prior:

`estimate = prior + n / (n + k) × (observed − prior)`

Here `n` is the player's weighted number of balls (3.4), and `k` = (ball-to-ball variance) ÷ (true between-player variance), estimated from the data by the method of moments. The sampling variance of each weighted mean uses its effective sample size, (Σw)² ÷ Σw².

| | Prior | k (weighted balls) | Weight on own record at 300 weighted pressure balls |
|---|---|---|---|
| Batters | 75% league mean, 25% own normal form (see 4.2b) | 855 (league-mean part) | 26% |
| Bowlers | own baseline form (see 4.2b) | 1,818 | 14% |

This is what moves the rankings most. For example, Rohit Sharma has 147 pressure balls, worth 105 after weighting. His +55 per 100 shrinks to +8.1. Players with big, sustained records keep their place, such as Suryakumar (568 balls) and Varun Chakravarthy (483 balls).

### Key finding: under pressure, batters are much harder to separate than bowlers
*This is a property of the data, so it was measured on unweighted records.* We also tried shrinking each player's pressure value towards **what their normal form predicts**, and asked how much players differ beyond that.
- **Bowlers:** a clear and persistent difference (k = 2,076).
- **Batters:** much less (k = 5,676). Once a batter's usual quality and the context are accounted for, how they do under pressure is mostly noise in a sample of a few hundred balls. On unweighted records, section 4.2's clutch test finds no detectable batting clutch effect at all.

The cross-format check agrees. For players with at least 40 pressure balls in both IPL and T20Is, their pressure value in one correlates only 0.19 (batters) and 0.12 (bowlers) with the other.

**What this means for the rankings:** batting pressure rankings should be read with wider uncertainty. Section 4 therefore rates players on proven pressure performance plus consistency across matches, rather than on one season's swing. Section 5 quantifies the uncertainty with bootstrap rank ranges.

## 3.6 Eligibility
All counts below use IPL and T20I balls only.
- **Batters:** at least 100 pressure balls faced, in at least 15 innings with pressure exposure. **110 batters qualify.**
- **Bowlers:** at least 120 legal pressure balls, in at least 15 matches with pressure exposure. **98 bowlers qualify.**
- **Why these thresholds:** they keep roughly the 100 most-exposed players in each role. At these sample sizes the shrinkage weight is still small, so the threshold guards against one-season flukes rather than doing the statistical work itself.
- **Activity requirement:** the player must have appeared in 2025 or 2026. This is a selection exercise, so retired or inactive players are left out. That leaves a final pool of **105 batters and 96 bowlers**. Excluded: Dinesh Karthik, David Warner, Matthew Wade, Mohammad Rizwan and Iftikhar Ahmed (batting); Naveen-ul-Haq and Luke Jongwe (bowling).

## 3.7 Limitations
- Opposition effects come from every ball a player bowled or faced, so a player's pressure balls and opposition rating aren't fully independent.
- The opposition model, and the team strengths used for the opponent weight, are fitted on all seasons. An opponent's strength is treated as fixed across 2022–26.
- The three evidence-weight settings (10% per year, T20I at 80% except against the five strongest nations, associate sides at 50%) are judgement calls. Section 5.4 shows how the lists change if each is switched off or doubled.
- Ridge regression pulls players with small samples, especially associates, towards average. The tier terms correct the average level but not individual players within a tier.
- A-team (Emerging) samples are small, and their tier effects have wide uncertainty.

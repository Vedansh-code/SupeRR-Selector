# Report draft, section 2: Measuring performance

*Numbers come from `outputs/tables/phase3_summary.md`.*

## 2.1 The problem with raw stats
Raw strike rate and economy mostly reflect a player's **role**, not their quality. A death-overs finisher always has a higher strike rate than an opener in a 3-down rebuild, and a death bowler's economy always looks worse than a middle-overs spinner's. Pressure balls cluster in particular phases (chase middle overs and death overs), so raw stats would reward or punish players for *when* they play, not *how well*.

## 2.2 Context-adjusted expectations
For every delivery we estimate what an **average player** would do in exactly that situation. We use gradient-boosted models on these inputs:
- innings, over, wickets down, balls left, score, required rate
- format (IPL or T20I), pace or spin
- how set the batter is
- **the pressure percentile itself**

| Model | Target | Deliveries used |
|---|---|---|
| Expected batter runs | runs off the bat | balls faced (no wides) |
| P(striker dismissed) | striker out | balls faced |
| Expected bowler runs | runs charged to bowler | all deliveries |
| P(bowler wicket) | bowler-credited wicket | all deliveries |

Because pressure is one of the inputs, a player's performance under pressure is judged against how the average player copes with the **same** pressure. Their baseline is judged against average players in ordinary situations.

**Check:** in each pressure band, actual and expected totals agree within 1% (e.g. high band: 53,438 actual vs 53,459 expected batter runs; 2,195 vs 2,187 bowler wickets).

## 2.3 Putting runs and wickets in one currency
A wicket's cost depends on when it falls. We refit a **Duckworth–Lewis-style resource curve** on this dataset:

`R_w(u) = Z_w (1 − e^(−k·u / Z_w))`

- `u` = balls left; `w` = wickets in hand.
- `Z_w` = the run ceiling with `w` wickets left (forced to rise with `w`).
- `k` = scoring rate when wickets are no constraint, shared across all `w`.
- Fitted separately for IPL and T20I, on complete first innings.

The **wicket value** is `R_w(u) − R_(w−1)(u)`: about 11 runs in over 1, 5 runs in over 15 and 0.5 runs in over 20. In a chase it is capped at the runs still needed.

**Per-ball value (runs above an average player in the same situation):**
- Batting: `(runs − expected runs) − (out − P(out)) × wicket value`
- Bowling: `(expected runs conceded − runs conceded) + (wicket − P(wicket)) × wicket value`

## 2.4 Metrics reported per player
Each metric is computed for **pressure** balls (top 20%) and **baseline** balls (the rest):

| | Batting | Bowling |
|---|---|---|
| Main value | value per 100 balls | runs saved per 120 balls (20 overs) |
| Leverage-weighted value | same, with each ball weighted by leverage, capped at 5 | same |
| Result impact | win probability added (WPA) | win probability denied |
| Traditional | strike rate vs expected strike rate, average, dismissals vs expected, dot %, boundary % | economy vs expected economy, wickets vs expected, strike rate, average, dot %, boundary % conceded |
| Change under pressure | Δ value per 100 (pressure − baseline) | Δ value per 120 |

Per-match pressure performance is stored separately for the consistency analysis.

## 2.5 First observations (before adjustments)
- About 100 batters and 100 bowlers have at least 120 high-pressure balls. Their median is about 33–35 innings or matches with pressure exposure.
- **Pressure value is only weakly linked to baseline value**: the correlation is 0.10 for batters and 0.38 for bowlers. This could mean pressure skill really differs from everyday skill, or that pressure samples are noisy. Section 3 (shrinkage) and section 5 (split-half reliability) separate the two.
- The unadjusted leaders include names you'd expect, such as Klaasen, Suryakumar, Karthik, Narine, Hazlewood and Bhuvneshwar. They also include several T20I players whose pressure balls came mostly against weaker sides, which is why the next step adjusts for opposition.

## 2.6 Limitations
- In a chase, wicket value is capped at the runs still needed. This is a simplification.
- A ball where the non-striker is run out is charged to the striker in WPA.
- Byes and leg-byes count toward WPA but not toward runs value.
- League value totals are close to zero but not exactly zero (+0.009 runs per ball for batting), because wicket value correlates with dismissal probability. This affects all players equally, so it doesn't change the rankings.

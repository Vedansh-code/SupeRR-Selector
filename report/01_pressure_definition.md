# Report draft, section 1: Defining pressure

*Numbers come from `outputs/tables/phase2_summary.md`. Regenerate them if the data or settings change.*

## 1.1 Idea
A delivery is high-pressure when **the match result hangs on it** (stakes) and **the situation is hard for the players** (stress). Neither idea alone is enough:
- Stakes alone ignores a top-order collapse in the first innings. The win-probability model treats 30/5 as an already-decided game, so the swing on the next ball looks small, but the batters are clearly under pressure.
- Stress alone rates near-hopeless chases (required rate 15+) as maximum pressure. Nobody's result really depends on those balls.

So each delivery gets both scores, which are then blended.

## 1.2 Component A: Stakes (Leverage Index)
1. **Win-probability models.** We train two gradient-boosted classifiers, one per innings, that estimate P(batting side wins) from the match state:
   - Innings 1: runs, wickets in hand, balls left, IPL/T20I.
   - Innings 2: runs needed, balls left, wickets in hand, required rate, IPL/T20I.

   The models have monotonic constraints, so losing a wicket or needing more runs can never raise win probability. They are trained only on decided, full-length matches, with no DLS games and no ties.
2. **Leverage.** For every delivery we compute the win probability after each possible outcome: dot, 1, 2, 3, 4, 6, wicket or extra. Each outcome is weighted by its league frequency in that innings and phase. The leverage is the expected absolute change in win probability, scaled so that the average delivery = 1.0.
3. The same number applies to the batter and to the bowler, which meets the brief's requirement that the method work for both.

| Model check (5-fold, grouped by match) | Innings 1 | Innings 2 |
|---|---|---|
| AUC | 0.68 | 0.90 |
| Brier score | 0.225 | 0.131 |

Innings 1 is less predictable by nature, because the target doesn't exist yet. As a result, leverage is flatter in innings 1, which is part of why the stress component is needed.

## 1.3 Component B: Situational stress (0–100, rule-based)
- **Innings 2:**

  `(0.50·difficulty + 0.30·wickets lost + 0.20·recent collapse) × alive × (0.4 + 0.6·stage)`

  - difficulty rises from a required rate of 6 to 12.
  - alive fades to 0 as the required rate goes from 13 to 18.
- **Innings 1:**

  `0.8 × (0.40·wickets lost beyond par for that over + 0.30·recent collapse + 0.30·stage)`

  - recent collapse = wickets in the last 24 balls ÷ 3.
  - The 0.8 factor reflects that setting a target carries less direct pressure than chasing one.

## 1.4 Final definition
`pressure_score = (0.65 × percentile(stakes) + 0.35 × percentile(stress)) × 1.15 if knockout`

The top 20% of deliveries are classed as **high pressure**, the next 30% as medium and the bottom 50% as low. Stakes gets the larger weight because it is measured from data rather than assumed.

## 1.5 Evidence that the definition separates pressure from ordinary play
- **High-pressure balls really decide matches.** The realised win-probability swing averages 0.033 per ball, against 0.006 for low-pressure balls (5.5×).
- **It matches cricket intuition.**
  - In chases, pressure peaks when the required rate is 8–12 in the death overs (96th percentile on average) and falls away for lost causes.
  - In the first innings, it rises with wickets lost and in the last 5 overs.
  - 33% of knockout deliveries are high pressure, against 19.5% of league deliveries.
- **Players behave differently under it, compared like for like within a phase.** In first-innings middle overs, strike rate falls from 141 (low) to 114 (high), boundary % falls from 16.6 to 11.8, and dot % rises from 29.3 to 35.5. In first-innings death overs, strike rate falls from 176 to 152. Across all pressure balls, dismissals per ball rise from 5.4% to 6.0%.
- **It covers both competition types in similar proportions:** 19.2% of T20I and Emerging-tier balls and 21.0% of IPL balls are high pressure. IPL games are closer on average, so a slightly higher share is expected.
- **Where it occurs:** of all high-pressure balls, 36% are in chase middle overs, 21% in first-innings death overs and 15% in chase death overs.

## 1.6 Known limitations (for the reliability section)
- The innings-1 win-probability model is only moderately predictive (AUC 0.68).
- The stress weights are judgement calls. Phase 6 tests how sensitive the rankings are to the 0.65/0.35 blend, the knockout multiplier and the 20% cut-off.
- Leverage has a heavy tail (last-ball finishes reach 40×), so player ratings should use bands or a capped leverage, never raw leverage.
- Opposition strength isn't part of pressure. The T20I data includes A-team and emerging-nations events, and those are handled in the fair-comparison step (Phase 4).

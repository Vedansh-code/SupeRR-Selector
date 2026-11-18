# Cross-validated rating weights (5-fold x 10 repeats, grouped by match)

Target: opposition-adjusted pressure value per ball in the held-out fold (pool players with >= 20 pressure balls in it). Score: ball-weighted correlation, averaged over 50 folds. Grid step 5%. Choice: among combinations not clearly worse than the best (paired difference within one corrected standard error), the one closest to the judgement weights.

## Batters (median 85 players per fold)
Judgement weights: value 54% / consistency 24% / clutch 0% / impact 18% / volume 5%  ->  r = 0.027 (-0.032 v best, SE of difference 0.042)
Best on the grid:  value 0% / consistency 100% / clutch 0% / impact 0% / volume 0%  ->  r = 0.059
Chosen (1-SE rule, closest to judgement): value 54% / consistency 24% / clutch 0% / impact 18% / volume 5%  ->  r = 0.027
Combinations within 1 SE of the best: 1406 of 1772
Single components: value only r = 0.017, consistency only r = 0.059, impact only r = 0.007, volume only r = -0.021

## Bowlers (median 84 players per fold)
Judgement weights: value 43% / consistency 19% / clutch 19% / impact 14% / volume 5%  ->  r = 0.154 (-0.044 v best, SE of difference 0.030)
Best on the grid:  value 100% / consistency 0% / clutch 0% / impact 0% / volume 0%  ->  r = 0.198
Chosen (1-SE rule, closest to judgement): value 55% / consistency 5% / clutch 15% / impact 15% / volume 10%  ->  r = 0.177
Combinations within 1 SE of the best: 506 of 10627
Single components: value only r = 0.198, consistency only r = 0.039, clutch only r = 0.004, impact only r = 0.094, volume only r = 0.073

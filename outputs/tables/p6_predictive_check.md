# Predictive check: correlation of half-A estimate with half-B pressure value (40 splits, players >= 40 pressure balls in both halves)

                 mean    std  share_of_splits_best
role estimate                                     
bat  b_shrunk   0.033  0.071                 0.200
     blend      0.029  0.064                 0.050
     p_lg       0.066  0.079                 0.350
     p_shrunk   0.026  0.066                 0.000
     rating     0.066  0.075                 0.250
     rating_v2  0.048  0.071                 0.150
bowl b_shrunk   0.239  0.064                 0.500
     blend      0.189  0.090                 0.075
     p_lg       0.100  0.077                 0.025
     p_shrunk   0.209  0.080                 0.125
     rating     0.108  0.079                 0.025
     rating_v2  0.194  0.085                 0.250

# Forward check: evidence weights

Rating built on matches before each cut-off (2024-01-01, 2024-07-01, 2025-01-01, 2025-07-01, 2026-01-01), correlated with opposition-adjusted pressure value in the following 12 months (ball-weighted; >= 60 pressure balls before; after: >= 30 in all matches or >= 20 in the IPL). Median players per cut-off: bat IPL only: 33, bat all matches: 40, bowl IPL only: 29, bowl all matches: 39. Mean correlation across cut-offs:

setup             no weighting  recency only  IPL tilt only  opponent only  all three (in use)
role target                                                                                   
bat  IPL only           -0.094        -0.077         -0.082         -0.073              -0.056
     all matches        -0.121        -0.108         -0.104         -0.104              -0.090
bowl IPL only            0.275         0.263          0.277          0.277               0.267
     all matches         0.268         0.260          0.280          0.269               0.280

Weighting in use: {'recency_decay': 0.1, 'comp': {'IPL': 1.0, 'T20I': 0.8, 'T20I_strong': 1.0}, 'strong_t20i_teams': ('India', 'Australia', 'England', 'South Africa', 'New Zealand'), 'opponent': (0.5, 1.0)}
# Benchmark: Pressure Rating vs simple stats (forward in time)

Cut-offs 2024-01-01, 2024-07-01, 2025-01-01, 2025-07-01, 2026-01-01; predictors from matches before each cut-off, targets from the next 12 months (>= 60 pressure balls before, >= 30 after). Median players per cut-off: bat t_simple: 40, bat t_value: 40, bowl t_simple: 39, bowl t_value: 39.
t_value = opposition-adjusted pressure value per ball (our measure); t_simple = plain pressure strike rate (batters) or economy, sign flipped so higher = better (bowlers).
r = ball-weighted correlation; top10_vs_avg = next-year target of each predictor's top 10 minus the average of all players compared (runs per ball for t_value; strike-rate points or runs per over for t_simple).

                                                            r  top10_vs_avg
role target   predictor                                                    
bat  t_value  Pressure Rating (full method)            -0.090        -0.646
              Value component alone                    -0.099        -4.428
              Normal-form quality (non-pressure value) -0.112        -4.323
              Pressure Rating, no weights or nerf      -0.114        -4.781
              Pressure strike rate                      0.009        -1.627
              Pressure batting average                 -0.149        -0.834
              Overall strike rate                      -0.123        -2.472
              Overall batting average                  -0.071         3.170
     t_simple Pressure Rating (full method)            -0.027         1.725
              Value component alone                    -0.041        -2.073
              Normal-form quality (non-pressure value) -0.041        -2.031
              Pressure Rating, no weights or nerf      -0.046        -3.292
              Pressure strike rate                      0.048         0.572
              Pressure batting average                 -0.103        -1.008
              Overall strike rate                      -0.013         0.336
              Overall batting average                  -0.037         1.522
bowl t_value  Pressure Rating (full method)             0.280         7.480
              Value component alone                     0.335        15.278
              Normal-form quality (non-pressure value)  0.318        11.655
              Pressure Rating, no weights or nerf       0.270         9.440
              Pressure economy                          0.207        12.746
              Pressure wickets per ball                 0.018        -2.175
              Overall economy                           0.332         6.384
              Overall wickets per ball                 -0.135        -4.336
     t_simple Pressure Rating (full method)             0.331         0.606
              Value component alone                     0.348         0.660
              Normal-form quality (non-pressure value)  0.329         0.583
              Pressure Rating, no weights or nerf       0.324         0.617
              Pressure economy                          0.519         1.117
              Pressure wickets per ball                -0.095        -0.339
              Overall economy                           0.597         0.811
              Overall wickets per ball                 -0.192        -0.242
# Phase 6: reliability

Evidence weighting: {'recency_decay': 0.1, 'comp': {'IPL': 1.0, 'T20I': 0.8, 'T20I_strong': 1.0}, 'strong_t20i_teams': ('India', 'Australia', 'England', 'South Africa', 'New Zealand'), 'opponent': (0.5, 1.0)}, recency measured back from 2026-11-01. Bootstrap and sensitivity runs use it; split-half and temporal checks use unweighted records.
Weights held fixed at the Phase 5 values: bat: value 54%, consistency 24%, clutch 0%, impact 18%, volume 5% | bowl: value 55%, consistency 5%, clutch 15%, impact 15%, volume 10%

## Bootstrap rank uncertainty: Batters (500 match resamples, shrinkage hyperparameters fixed)
                           name  rank  median_rank 90%_rank_range  p_top5  p_top10  p_in_pool
player_id                                                                                    
3647               Shreyas Iyer   1.0          2.0           1-14    0.82     0.92       1.00
1699           Suryakumar Yadav   2.0          3.0           1-18    0.70     0.86       1.00
4260           Heinrich Klaasen   3.0          4.0           1-19    0.63     0.83       1.00
47                  Virat Kohli   4.0          8.0           2-36    0.34     0.59       1.00
6396                  Tim David   5.0          8.0           2-45    0.37     0.59       1.00
6281            Abhishek Sharma   6.0         11.0           3-51    0.22     0.47       0.99
8101            Ashutosh Sharma   7.0         12.0           2-54    0.19     0.35       0.78
7897       Namboori Tilak Varma   8.0         12.0           2-65    0.23     0.45       1.00
5939              Cameron Green   9.0         16.0           4-55    0.11     0.32       1.00
6819           Yashasvi Jaiswal  10.0         18.0           4-60    0.11     0.31       0.98
126                Rohit Sharma  11.0         17.0           3-69    0.13     0.27       0.91
2756             Shashank Singh  12.0         19.0           5-58    0.08     0.23       0.91
25213             Dewald Brevis  13.0         23.0           4-68    0.09     0.21       0.86
4409                 Sam Curran  14.0         23.0           5-65    0.06     0.19       1.00
6423                Riyan Parag  15.0         24.0           5-75    0.07     0.22       1.00

## Bootstrap rank uncertainty: Bowlers (500 match resamples, shrinkage hyperparameters fixed)
                          name  rank  median_rank 90%_rank_range  p_top5  p_top10  p_in_pool
player_id                                                                                   
6256        Varun Chakravarthy   1.0          3.0           1-11    0.75     0.93       1.00
2933            Jasprit Bumrah   2.0          3.0           1-11    0.79     0.94       1.00
781               Sunil Narine   3.0          4.0           1-15    0.66     0.89       1.00
4219             Krunal Pandya   4.0          8.0           2-26    0.32     0.63       1.00
3644             Kuldeep Yadav   5.0          8.0           2-25    0.35     0.65       1.00
830             Josh Hazlewood   6.0          8.0           1-39    0.36     0.60       1.00
4722               Rashid Khan   7.0          8.0           2-27    0.32     0.62       1.00
360          Bhuvneshwar Kumar   8.0          8.0           1-30    0.35     0.63       1.00
8661       Matheesha Pathirana   9.0         11.0           4-27    0.15     0.50       1.00
7967                Noor Ahmad  10.0         12.0           2-42    0.22     0.45       1.00
4373         Mustafizur Rahman  11.0         13.0           5-33    0.07     0.34       1.00
7920              Nathan Ellis  12.0         17.0           5-37    0.06     0.22       1.00
39657            Eshan Malinga  13.0         16.0           4-43    0.06     0.15       0.52
2876                Axar Patel  14.0         18.0           6-41    0.03     0.19       1.00
4900         Wanindu Hasaranga  15.0         18.0           6-42    0.05     0.23       1.00

## Split-half stability (mean over 50 random match splits; players with >= 40 pressure / >= 150 baseline balls in both halves)
      n_players_pressure  r_pressure  n_players_baseline  r_baseline  r_clutch  r_pressure_vs_other_half_baseline  full_sample_reliability_pressure  full_sample_reliability_baseline  full_sample_reliability_clutch
role                                                                                                                                                                                                                 
bat               107.96       0.029              125.26       0.320     0.108                              0.018                             0.055                             0.485                           0.195
bowl              114.30       0.033              135.16       0.172    -0.100                              0.184                             0.065                             0.294                           0.000
full_sample_reliability = Spearman-Brown: correlation expected between two full-size samples

## Temporal stability (2022-23 vs 2024-26)
role           split  n_players_pressure  r_pressure  n_players_baseline  r_baseline  r_clutch  r_pressure_vs_other_half_baseline
 bat <2024 vs >=2024                  88       0.005                  79       0.316     0.194                              0.098
bowl <2024 vs >=2024                  84       0.087                  89       0.135    -0.080                              0.392

## Sensitivity: Batters (overlap with main top 10, and where the main top 10 land)
                                           variant  overlap_with_main_top10
             main (65/35 blend, KO x1.15, top 20%)                       10
                           top 15% = high pressure                        9
                           top 25% = high pressure                        7
                            stakes (leverage) only                        8
                               50/50 stakes/stress                        7
                                 no knockout boost                        9
evidence: no evidence weighting (every ball equal)                        8
                            evidence: recency only                        9
                       evidence: no recency factor                       10
                             evidence: no IPL tilt                       10
                      evidence: no opponent factor                       10
             evidence: all factors twice as strong                        8
                               weights: value only                        9
                            weights: equal weights                        9
                                weights: no impact                        8
                           weights: no consistency                        9
                      weights: value + consistency                        8
                    weights: no track-record bonus                       10
                      weights: no recent-data nerf                       10
- main (65/35 blend, KO x1.15, top 20%): Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 4, Tim David 5, Abhishek Sharma 6, Ashutosh Sharma 7, Namboori Tilak Varma 8, Cameron Green 9, Yashasvi Jaiswal 10
- top 15% = high pressure: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 8, Tim David 7, Abhishek Sharma 5, Ashutosh Sharma 6, Namboori Tilak Varma 4, Cameron Green 9, Yashasvi Jaiswal 26
- top 25% = high pressure: Shreyas Iyer 2, Suryakumar Yadav 1, Heinrich Klaasen 3, Virat Kohli 7, Tim David 5, Abhishek Sharma 8, Ashutosh Sharma 22, Namboori Tilak Varma 6, Cameron Green 11, Yashasvi Jaiswal 26
- stakes (leverage) only: Shreyas Iyer 3, Suryakumar Yadav 6, Heinrich Klaasen 7, Virat Kohli 9, Tim David 4, Abhishek Sharma 1, Ashutosh Sharma 19, Namboori Tilak Varma 8, Cameron Green 13, Yashasvi Jaiswal 10
- 50/50 stakes/stress: Shreyas Iyer 4, Suryakumar Yadav 1, Heinrich Klaasen 5, Virat Kohli 20, Tim David 2, Abhishek Sharma 3, Ashutosh Sharma 9, Namboori Tilak Varma 6, Cameron Green 36, Yashasvi Jaiswal 33
- no knockout boost: Shreyas Iyer 1, Suryakumar Yadav 3, Heinrich Klaasen 2, Virat Kohli 5, Tim David 4, Abhishek Sharma 6, Ashutosh Sharma 9, Namboori Tilak Varma 7, Cameron Green 8, Yashasvi Jaiswal 12
- evidence: no evidence weighting (every ball equal): Shreyas Iyer 4, Suryakumar Yadav 1, Heinrich Klaasen 3, Virat Kohli 8, Tim David 2, Abhishek Sharma 5, Ashutosh Sharma 10, Namboori Tilak Varma 6, Cameron Green 12, Yashasvi Jaiswal 13
- evidence: recency only: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 4, Virat Kohli 6, Tim David 3, Abhishek Sharma 5, Ashutosh Sharma 9, Namboori Tilak Varma 7, Cameron Green 8, Yashasvi Jaiswal 11
- evidence: no recency factor: Shreyas Iyer 2, Suryakumar Yadav 1, Heinrich Klaasen 3, Virat Kohli 5, Tim David 4, Abhishek Sharma 6, Ashutosh Sharma 7, Namboori Tilak Varma 9, Cameron Green 10, Yashasvi Jaiswal 8
- evidence: no IPL tilt: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 5, Tim David 4, Abhishek Sharma 6, Ashutosh Sharma 8, Namboori Tilak Varma 7, Cameron Green 9, Yashasvi Jaiswal 10
- evidence: no opponent factor: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 6, Tim David 4, Abhishek Sharma 5, Ashutosh Sharma 8, Namboori Tilak Varma 7, Cameron Green 9, Yashasvi Jaiswal 10
- evidence: all factors twice as strong: Shreyas Iyer 1, Suryakumar Yadav 3, Heinrich Klaasen 2, Virat Kohli 4, Tim David 5, Abhishek Sharma 7, Ashutosh Sharma 6, Namboori Tilak Varma 8, Cameron Green 12, Yashasvi Jaiswal 11
- weights: value only: Shreyas Iyer 3, Suryakumar Yadav 1, Heinrich Klaasen 2, Virat Kohli 4, Tim David 6, Abhishek Sharma 5, Ashutosh Sharma 7, Namboori Tilak Varma 9, Cameron Green 10, Yashasvi Jaiswal 13
- weights: equal weights: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 4, Tim David 5, Abhishek Sharma 8, Ashutosh Sharma 6, Namboori Tilak Varma 7, Cameron Green 11, Yashasvi Jaiswal 9
- weights: no impact: Shreyas Iyer 1, Suryakumar Yadav 3, Heinrich Klaasen 2, Virat Kohli 4, Tim David 6, Abhishek Sharma 5, Ashutosh Sharma 7, Namboori Tilak Varma 20, Cameron Green 8, Yashasvi Jaiswal 12
- weights: no consistency: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 4, Tim David 5, Abhishek Sharma 8, Ashutosh Sharma 7, Namboori Tilak Varma 6, Cameron Green 13, Yashasvi Jaiswal 10
- weights: value + consistency: Shreyas Iyer 1, Suryakumar Yadav 3, Heinrich Klaasen 2, Virat Kohli 4, Tim David 6, Abhishek Sharma 5, Ashutosh Sharma 8, Namboori Tilak Varma 23, Cameron Green 7, Yashasvi Jaiswal 12
- weights: no track-record bonus: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 4, Tim David 5, Abhishek Sharma 6, Ashutosh Sharma 7, Namboori Tilak Varma 8, Cameron Green 9, Yashasvi Jaiswal 10
- weights: no recent-data nerf: Shreyas Iyer 1, Suryakumar Yadav 2, Heinrich Klaasen 3, Virat Kohli 4, Tim David 5, Abhishek Sharma 6, Ashutosh Sharma 7, Namboori Tilak Varma 8, Cameron Green 9, Yashasvi Jaiswal 10

## Sensitivity: Bowlers (overlap with main top 10, and where the main top 10 land)
                                           variant  overlap_with_main_top10
             main (65/35 blend, KO x1.15, top 20%)                       10
                           top 15% = high pressure                        9
                           top 25% = high pressure                        9
                            stakes (leverage) only                        9
                               50/50 stakes/stress                        9
                                 no knockout boost                       10
evidence: no evidence weighting (every ball equal)                       10
                            evidence: recency only                        9
                       evidence: no recency factor                       10
                             evidence: no IPL tilt                       10
                      evidence: no opponent factor                        9
             evidence: all factors twice as strong                       10
                               weights: value only                        9
                            weights: equal weights                        6
                                weights: no impact                        8
                           weights: no consistency                        9
                      weights: value + consistency                        8
                    weights: no track-record bonus                        9
                      weights: no recent-data nerf                        9
- main (65/35 blend, KO x1.15, top 20%): Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 4, Kuldeep Yadav 5, Josh Hazlewood 6, Rashid Khan 7, Bhuvneshwar Kumar 8, Matheesha Pathirana 9, Noor Ahmad 10
- top 15% = high pressure: Varun Chakravarthy 1, Jasprit Bumrah 3, Sunil Narine 2, Krunal Pandya 4, Kuldeep Yadav 6, Josh Hazlewood 7, Rashid Khan 5, Bhuvneshwar Kumar 11, Matheesha Pathirana 8, Noor Ahmad 9
- top 25% = high pressure: Varun Chakravarthy 1, Jasprit Bumrah 3, Sunil Narine 2, Krunal Pandya 5, Kuldeep Yadav 6, Josh Hazlewood 4, Rashid Khan 7, Bhuvneshwar Kumar 8, Matheesha Pathirana 9, Noor Ahmad 11
- stakes (leverage) only: Varun Chakravarthy 5, Jasprit Bumrah 3, Sunil Narine 2, Krunal Pandya 4, Kuldeep Yadav 6, Josh Hazlewood 1, Rashid Khan 7, Bhuvneshwar Kumar 9, Matheesha Pathirana 11, Noor Ahmad 8
- 50/50 stakes/stress: Varun Chakravarthy 1, Jasprit Bumrah 4, Sunil Narine 2, Krunal Pandya 5, Kuldeep Yadav 3, Josh Hazlewood 10, Rashid Khan 6, Bhuvneshwar Kumar 14, Matheesha Pathirana 7, Noor Ahmad 9
- no knockout boost: Varun Chakravarthy 2, Jasprit Bumrah 1, Sunil Narine 3, Krunal Pandya 7, Kuldeep Yadav 6, Josh Hazlewood 8, Rashid Khan 4, Bhuvneshwar Kumar 5, Matheesha Pathirana 9, Noor Ahmad 10
- evidence: no evidence weighting (every ball equal): Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 5, Kuldeep Yadav 4, Josh Hazlewood 7, Rashid Khan 6, Bhuvneshwar Kumar 8, Matheesha Pathirana 9, Noor Ahmad 10
- evidence: recency only: Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 6, Kuldeep Yadav 4, Josh Hazlewood 7, Rashid Khan 5, Bhuvneshwar Kumar 8, Matheesha Pathirana 11, Noor Ahmad 10
- evidence: no recency factor: Varun Chakravarthy 1, Jasprit Bumrah 3, Sunil Narine 2, Krunal Pandya 4, Kuldeep Yadav 5, Josh Hazlewood 6, Rashid Khan 7, Bhuvneshwar Kumar 8, Matheesha Pathirana 9, Noor Ahmad 10
- evidence: no IPL tilt: Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 5, Kuldeep Yadav 6, Josh Hazlewood 7, Rashid Khan 4, Bhuvneshwar Kumar 8, Matheesha Pathirana 9, Noor Ahmad 10
- evidence: no opponent factor: Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 4, Kuldeep Yadav 5, Josh Hazlewood 7, Rashid Khan 6, Bhuvneshwar Kumar 8, Matheesha Pathirana 9, Noor Ahmad 11
- evidence: all factors twice as strong: Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 4, Kuldeep Yadav 7, Josh Hazlewood 5, Rashid Khan 8, Bhuvneshwar Kumar 6, Matheesha Pathirana 9, Noor Ahmad 10
- weights: value only: Varun Chakravarthy 2, Jasprit Bumrah 1, Sunil Narine 3, Krunal Pandya 20, Kuldeep Yadav 10, Josh Hazlewood 6, Rashid Khan 7, Bhuvneshwar Kumar 4, Matheesha Pathirana 9, Noor Ahmad 5
- weights: equal weights: Varun Chakravarthy 2, Jasprit Bumrah 13, Sunil Narine 3, Krunal Pandya 1, Kuldeep Yadav 6, Josh Hazlewood 5, Rashid Khan 20, Bhuvneshwar Kumar 14, Matheesha Pathirana 4, Noor Ahmad 32
- weights: no impact: Varun Chakravarthy 1, Jasprit Bumrah 4, Sunil Narine 6, Krunal Pandya 2, Kuldeep Yadav 7, Josh Hazlewood 8, Rashid Khan 14, Bhuvneshwar Kumar 9, Matheesha Pathirana 5, Noor Ahmad 13
- weights: no consistency: Varun Chakravarthy 2, Jasprit Bumrah 3, Sunil Narine 1, Krunal Pandya 4, Kuldeep Yadav 8, Josh Hazlewood 5, Rashid Khan 7, Bhuvneshwar Kumar 6, Matheesha Pathirana 9, Noor Ahmad 13
- weights: value + consistency: Varun Chakravarthy 2, Jasprit Bumrah 1, Sunil Narine 8, Krunal Pandya 9, Kuldeep Yadav 7, Josh Hazlewood 5, Rashid Khan 14, Bhuvneshwar Kumar 11, Matheesha Pathirana 3, Noor Ahmad 10
- weights: no track-record bonus: Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 4, Kuldeep Yadav 7, Josh Hazlewood 5, Rashid Khan 9, Bhuvneshwar Kumar 6, Matheesha Pathirana 8, Noor Ahmad 12
- weights: no recent-data nerf: Varun Chakravarthy 1, Jasprit Bumrah 2, Sunil Narine 3, Krunal Pandya 4, Kuldeep Yadav 6, Josh Hazlewood 5, Rashid Khan 7, Bhuvneshwar Kumar 8, Matheesha Pathirana 9, Noor Ahmad 11

## Season by season: Batters top 10, adjusted pressure value per 100 (pressure balls)
year                         2022        2023        2024        2025         2026 seasons_positive
name                                                                                               
Shreyas Iyer          -34.7 (103)    37.0 (7)   15.0 (29)   57.7 (87)   45.9 (190)              4/5
Suryakumar Yadav       19.9 (165)  48.3 (197)   13.4 (66)   31.8 (99)     5.3 (41)              5/5
Heinrich Klaasen        65.5 (33)   51.0 (95)  -16.0 (63)   70.5 (25)    49.1 (82)              4/5
Virat Kohli            -13.6 (67)   27.9 (33)   66.7 (62)   -0.4 (84)    81.9 (55)              3/5
Tim David              40.4 (113)  13.3 (125)  -25.7 (63)  64.6 (112)  -103.0 (23)              3/5
Abhishek Sharma         13.0 (20)   51.7 (26)  -35.3 (34)   51.0 (70)    24.6 (57)              4/5
Ashutosh Sharma                 -           -   21.5 (49)   56.0 (47)    59.3 (32)              3/3
Namboori Tilak Varma   21.5 (119)  25.2 (107)   -7.5 (91)   2.3 (216)   31.9 (140)              4/5
Cameron Green           142.9 (9)   23.1 (90)   -2.2 (52)   58.5 (61)    11.1 (57)              4/5
Yashasvi Jaiswal        30.9 (35)   41.0 (63)   98.9 (44)  -75.4 (42)    70.4 (26)              4/5

## Season by season: Bowlers top 10, adjusted pressure value per 120 (pressure balls)
year                       2022        2023        2024        2025        2026 seasons_positive
name                                                                                            
Varun Chakravarthy   -20.9 (40)   34.3 (81)  51.2 (117)  47.8 (176)   19.0 (69)              4/5
Jasprit Bumrah       -9.0 (101)   -75.2 (3)   80.9 (45)  21.8 (141)   20.8 (85)              3/5
Sunil Narine          15.4 (78)  -14.3 (58)   65.5 (88)   45.4 (56)   72.4 (60)              4/5
Krunal Pandya         61.7 (61)    6.3 (42)  104.0 (52)   41.8 (79)   51.3 (41)              5/5
Kuldeep Yadav         64.5 (47)  29.0 (101)   16.5 (68)  36.9 (154)    3.3 (93)              5/5
Josh Hazlewood       24.1 (124)   -40.8 (4)    -7.5 (5)   75.0 (94)  -49.1 (68)              2/5
Rashid Khan          47.5 (196)  -9.8 (140)  28.2 (110)   5.2 (127)   14.3 (72)              4/5
Bhuvneshwar Kumar    13.4 (150)   83.1 (38)   28.1 (50)    6.1 (80)   57.0 (56)              5/5
Matheesha Pathirana   -43.0 (8)   52.0 (76)  45.1 (101)    3.2 (77)    7.9 (20)              4/5
Noor Ahmad           446.2 (11)   12.3 (65)   39.0 (59)  -8.9 (140)   20.1 (88)              4/5
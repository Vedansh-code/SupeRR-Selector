# Phase 2 summary

## Win-probability model (5-fold out-of-fold, grouped by match)
- Innings 1: 100,101 balls / 805 matches | log-loss 0.642 | Brier 0.225 | AUC 0.684 | base rate 0.500
                   n  mean_pred  actual
bin                                    
(-0.001, 0.1]   2347      0.055   0.154
(0.1, 0.2]      5337      0.156   0.166
(0.2, 0.3]      7856      0.252   0.278
(0.3, 0.4]     11402      0.352   0.360
(0.4, 0.5]     19334      0.453   0.464
(0.5, 0.6]     23931      0.547   0.553
(0.6, 0.7]     16397      0.645   0.652
(0.7, 0.8]      8623      0.744   0.685
(0.8, 0.9]      3878      0.843   0.750
(0.9, 1.0]       996      0.935   0.824
- Innings 2: 92,066 balls / 807 matches | log-loss 0.402 | Brier 0.131 | AUC 0.897 | base rate 0.480
                   n  mean_pred  actual
bin                                    
(-0.001, 0.1]  21853      0.031   0.041
(0.1, 0.2]      7836      0.147   0.192
(0.2, 0.3]      6709      0.249   0.276
(0.3, 0.4]      6619      0.350   0.357
(0.4, 0.5]      5774      0.448   0.458
(0.5, 0.6]      4868      0.551   0.514
(0.6, 0.7]      5608      0.651   0.654
(0.7, 0.8]      6035      0.753   0.731
(0.8, 0.9]      8785      0.853   0.808
(0.9, 1.0]     17979      0.970   0.962

## Components
Spearman(LI, stress): overall 0.211 | innings 1 0.044 | innings 2 0.369
Of high-pressure balls: 74% are top-20% on stakes (LI), 44% top-20% on stress
High-pressure cut-off: pressure_score >= 0.714

## League outcomes by pressure band
               deliveries  share_%  mean_LI  mean_stress  mean_realised_wp_swing  strike_rate  dismissal_%   dot_%  boundary_%  economy  balls_per_wkt
pressure_band                                                                                                                                         
low                100480     50.0    0.400       18.165                   0.006      140.145        5.415  36.381      19.297    8.759         18.891
medium              60288     30.0    1.110       26.380                   0.016      139.153        5.236  34.923      18.585    8.683         19.679
high                40193     20.0    2.335       39.431                   0.033      138.197        6.020  32.624      17.243    8.659         17.209

## By innings
                       deliveries  share_%  mean_LI  mean_stress  mean_realised_wp_swing  strike_rate  dismissal_%   dot_%  boundary_%  economy  balls_per_wkt
innings pressure_band                                                                                                                                         
1       low                 52645   26.197    0.511       18.502                   0.008      143.106        5.134  35.433      19.808    8.938         20.018
        medium              37701   18.760    0.990       28.360                   0.015      139.962        5.324  33.453      18.111    8.733         19.420
        high                15381    7.654    1.629       40.366                   0.023      134.569        6.361  33.714      16.293    8.441         16.494
2       low                 47835   23.803    0.278       17.795                   0.004      136.890        5.724  37.422      18.736    8.561         17.790
        medium              22587   11.239    1.310       23.074                   0.019      137.807        5.090  37.371      19.374    8.599         20.127
        high                24812   12.347    2.773       38.851                   0.039      140.444        5.809  31.949      17.830    8.795         17.684

## By format (is_ipl)
                      deliveries  share_%  mean_LI  mean_stress  mean_realised_wp_swing  strike_rate  dismissal_%   dot_%  boundary_%  economy  balls_per_wkt
is_ipl pressure_band                                                                                                                                         
False  low                 57136   28.431    0.384       18.782                   0.006      135.074        5.757  37.490      18.117    8.441         17.773
       medium              34359   17.097    1.130       26.647                   0.017      133.174        5.465  36.094      17.258    8.308         18.964
       high                21793   10.844    2.323       39.076                   0.032      131.066        6.105  33.835      15.609    8.219         16.876
True   low                 43344   21.568    0.421       17.352                   0.006      146.848        4.963  34.915      20.858    9.178         20.607
       medium              25929   12.903    1.084       26.025                   0.016      147.109        4.932  33.364      20.350    9.181         20.720
       high                18400    9.156    2.350       39.851                   0.034      146.699        5.919  31.180      19.190    9.184         17.623

## Like-for-like: innings x phase x band
                                 deliveries  share_%  mean_LI  mean_stress  mean_realised_wp_swing  strike_rate  dismissal_%   dot_%  boundary_%  economy  balls_per_wkt
innings phase     pressure_band                                                                                                                                         
1       death     low                  7298    3.632    0.368       35.321                   0.008      176.449        8.083  26.988      24.541   11.172         13.441
                  medium              10356    5.153    0.841       37.424                   0.014      165.310        8.016  27.697      22.186   10.426         13.368
                  high                 8305    4.133    1.633       43.319                   0.024      152.499        8.114  29.658      19.267    9.629         13.152
        middle    low                 23296   11.592    0.476       22.503                   0.007      140.631        4.900  29.294      16.610    8.719         20.672
                  medium              18515    9.213    0.973       28.705                   0.014      128.171        4.304  31.635      14.322    7.947         23.352
                  high                 5580    2.777    1.583       37.765                   0.022      114.112        4.422  35.483      11.809    7.068         22.861
        powerplay low                 22051   10.973    0.595        8.708                   0.009      134.952        4.429  44.667      21.665    8.452         22.846
                  medium               8830    4.394    1.201       17.007                   0.018      135.728        4.387  43.858      21.409    8.455         23.174
                  high                 1496    0.744    1.777       33.672                   0.022      113.760        4.100  49.201      16.956    7.156         24.707
2       death     low                 10705    5.327    0.126       11.814                   0.002      148.148        8.522  34.108      20.049    9.349         12.059
                  medium               1660    0.826    2.403       26.961                   0.037      168.814        9.247  28.954      23.342   10.707         11.481
                  high                 6130    3.050    4.341       53.539                   0.060      155.550        8.312  29.593      20.173    9.868         12.591
        middle    low                 21056   10.478    0.226       23.121                   0.003      133.616        5.089  32.905      15.950    8.296         19.969
                  medium               9556    4.755    0.988       31.135                   0.014      129.992        4.860  30.865      14.775    8.058         20.862
                  high                14496    7.213    2.248       37.407                   0.032      133.772        5.014  30.246      15.477    8.327         20.337
        powerplay low                 16074    7.999    0.447       14.803                   0.006      133.824        4.726  45.542      21.544    8.395         21.364
                  medium              11371    5.658    1.420       15.733                   0.021      139.991        4.689  44.095      22.706    8.759         21.810
                  high                 4186    2.083    2.297       22.346                   0.033      141.943        4.983  41.225      22.633    8.887         20.196

## Where high-pressure balls occur (% of all high-pressure balls)
phase    death  middle  powerplay
innings                          
1         20.7    13.9        3.7
2         15.3    36.1       10.4

## % of balls that are high pressure: knockout vs not
is_knockout
False    19.5
True     33.3

## Innings 2: mean pressure percentile by required rate x phase
phase      death  middle  powerplay
rrr                                
(-99, 6]    0.18    0.13       0.15
(6, 8]      0.53    0.44       0.38
(8, 10]     0.92    0.76       0.60
(10, 12]    0.96    0.75       0.55
(12, 15]    0.82    0.51       0.32
(15, 18]    0.41    0.14       0.14
(18, 999]   0.08    0.03       0.22

## Innings 1: mean pressure percentile by wickets lost x phase
phase        death  middle  powerplay
wkts_before                          
0             0.53    0.33       0.29
1             0.33    0.36       0.43
2             0.43    0.45       0.59
3             0.53    0.62       0.67
4             0.63    0.56       0.50
5             0.72    0.62       0.42
6             0.78    0.74       0.42
7             0.66    0.51        NaN

## Mean pressure percentile by over
innings      1      2
overid               
1        0.201  0.426
2        0.356  0.452
3        0.412  0.476
4        0.433  0.491
5        0.477  0.509
6        0.467  0.520
7        0.464  0.519
8        0.480  0.521
9        0.455  0.531
10       0.502  0.537
11       0.519  0.550
12       0.512  0.541
13       0.549  0.539
14       0.530  0.518
15       0.550  0.507
16       0.654  0.497
17       0.661  0.482
18       0.635  0.433
19       0.641  0.393
20       0.631  0.315

## Highest-pressure deliveries
 match_id                  comp_name      stage  innings  overid  runs_before  wkts_before  balls_left  runs_needed     striker_name    bowler_name  wp_before  leverage_index  stress_index  pressure_score
    48029 Asia Cup Rising Stars 2025      Final        2      20          124            9           1          2.0    Abdul Saqlain  Ahmed Daniyal      0.097          31.349        86.233           1.150
    21586                   IPL 2023      Final        2      15          158            5           6         13.0      Shivam Dube   Mohit Sharma      0.628          12.840        85.200           1.149
    21586                   IPL 2023      Final        2      14          156            5           7         15.0  Ravindra Jadeja Mohammed Shami      0.631          11.464        84.608           1.149
    48028 Asia Cup Rising Stars 2025 Semi Final        2      20          146            8           4          8.0 Milan Rathnayake     Ubaid Shah      0.127          14.455        78.400           1.148
    48027 Asia Cup Rising Stars 2025 Semi Final        2      20          191            5           2          4.0  Ashutosh Sharma  Rakibul Hasan      0.931          14.804        74.662           1.146
    48027 Asia Cup Rising Stars 2025 Semi Final        2      19          176            5           9         19.0  Ashutosh Sharma   Ripon Mondol      0.493           8.473        78.390           1.146
    48028 Asia Cup Rising Stars 2025 Semi Final        2      20          142            8           6         12.0 Milan Rathnayake     Ubaid Shah      0.124           7.729        77.600           1.145
    21586                   IPL 2023      Final        2      14          155            5           8         16.0      Shivam Dube Mohammed Shami      0.650           6.677        84.017           1.145
    21586                   IPL 2023      Final        2      14          153            5           9         18.0      Shivam Dube Mohammed Shami      0.639           5.798        83.425           1.143
    21586                   IPL 2023      Final        2      14          151            5          10         20.0      Shivam Dube Mohammed Shami      0.566           5.784        82.833           1.143
    40766                   IPL 2025  Qualifier        2      19          181            5          12         23.0     Shreyas Iyer  Ashwani Kumar      0.669           7.786        73.242           1.143
    48028 Asia Cup Rising Stars 2025 Semi Final        2      20          141            8           6         13.0 Milan Rathnayake     Ubaid Shah      0.091           5.698        77.600           1.141
    21586                   IPL 2023      Final        2      14          151            5          11         20.0      Shivam Dube Mohammed Shami      0.719           6.529        73.817           1.141
    48027 Asia Cup Rising Stars 2025 Semi Final        2      19          177            5           8         18.0    Nehal Wadhera   Ripon Mondol      0.444           6.918        70.920           1.140
    40766                   IPL 2025  Qualifier        2      18          180            5          13         24.0     Shreyas Iyer Jasprit Bumrah      0.710           6.363        69.556           1.137

## Random sample of high-pressure deliveries
 match_id                                          comp_name  stage  innings  overid  runs_before  wkts_before  balls_left  runs_needed         striker_name        bowler_name  wp_before  leverage_index  stress_index  pressure_score
    37094              Mens T20 Emerging Teams Asia Cup 2024 League        2      16          116            6          25         46.0        Rakibul Hasan      Ramesh Mendis      0.201           3.565        68.104           0.976
    28958             Zimbabwe in Sri Lanka T20I Series 2024 Others        2      15          112            4          33         62.0            Ryan Burl Maheesh Theekshana      0.310           3.295        65.914           0.971
    40703                                           IPL 2025 League        1      19          161            8          12          NaN Pieter Willem Mulder     Mitchell Starc      0.320           2.877        58.369           0.953
    50390                                           IPL 2026 League        1      17          160            6          19          NaN        Shubham Dubey       Corbin Bosch      0.429           2.005        44.584           0.884
    50383                                           IPL 2026 League        1      19          187            6           8          NaN        Dasun Shanaka     Mitchell Starc      0.536           1.890        45.835           0.879
    35428 Netherlands Tri-Nation T20I Series [Aug 2024] 2024 League        1      20          161            6           2          NaN      Shayan Jahangir     Dilon Heyliger      0.533           1.815        41.646           0.859
    50945                                           IPL 2026  Final        1       6           39            2          89          NaN Nishant Kumar Sindhu       Rasikh Salam      0.348           1.483        27.961           0.859
    50341                  India in Ireland T20I Series 2026 Others        2      20          144            8           4         11.0         Harshit Rana       Harry Tector      0.061           3.049        29.400           0.853
    14163                                           IPL 2022 League        2      17          123            3          21         37.0            Tim David      Khaleel Ahmed      0.848           1.438        50.131           0.836
    50361                                           IPL 2026 League        2      11          118            2          55        105.0          Riyan Parag      Harpreet Brar      0.435           1.483        43.225           0.823
    29984          Australia in New Zealand T20I Series 2024 Others        2       2            8            0          54        118.0           Will Young      Matthew Short      0.229           2.901        22.489           0.802
    19960       West Indies in South Africa T20I Series 2023 League        2       6           92            0          90        167.0      Quinton de Kock       Jason Holder      0.273           1.505        23.528           0.720

## Player exposure (players with >= N high-pressure balls)
 min_high_pressure_balls  batters  bowlers
                      30      279      264
                      60      180      180
                      90      124      132
                     120      101       99
                     150       79       76
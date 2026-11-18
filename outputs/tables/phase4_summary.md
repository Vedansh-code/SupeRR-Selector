# Phase 4 summary

## Season par removed (average value of each competition-season, before adjustment)
Every ball is measured against its own competition-season par, so an average batter or bowler in any
competition-season is worth 0. Offsets removed (runs per 100 balls batting, per 120 legal balls bowling):
                bat_par_per100  bowl_par_per120
comp_tier year                                 
Emerging  2024           -0.13             1.51
          2025           -0.50             0.61
IPL       2022           -6.25             6.81
          2023           -0.64            -0.34
          2024            3.74            -4.78
          2025            5.95            -7.61
          2026            6.30            -7.88
T20I      2022           -1.42             1.60
          2023            0.21             0.17
          2024           -1.86             2.16
          2025           -0.16             0.39
          2026            6.12            -7.88

## Opponent strength used for evidence weights (1 = average IPL side, 0 = average associate side)
### Bowling attacks faced by batters
                       team      tier     n  strength
             Mumbai Indians       IPL  8496     1.000
             Delhi Capitals       IPL  8146     1.000
Royal Challengers Bengaluru       IPL  8670     1.000
      Kolkata Knight Riders       IPL  7838     1.000
                      India      Full 12899     1.000
             Gujarat Titans       IPL  8847     1.000
                Afghanistan      Full  5949     0.997
        Chennai Super Kings       IPL  8318     0.987
                   Pakistan      Full  9910     0.976
       Lucknow Super Giants       IPL  8247     0.911
           Rajasthan Royals       IPL  8923     0.891
        Sunrisers Hyderabad       IPL  8389     0.887
                  Sri Lanka      Full  7841     0.884
               Punjab Kings       IPL  8247     0.862
                   Zimbabwe      Full  5706     0.827
                  Australia      Full  6564     0.813
                New Zealand      Full  9094     0.766
                 Bangladesh      Full  8424     0.752
                    England      Full  7384     0.739
               South Africa      Full  5934     0.681
                    Ireland      Full  5164     0.576
                West Indies      Full 10150     0.561
       United Arab Emirates Associate  2294     0.081
                   Scotland Associate   606     0.028
                Netherlands Associate  1394     0.018
                     Canada Associate   338     0.000
                     Kuwait Associate   345     0.000
                  Hong Kong Associate   943     0.000
   United States Of America Associate   481     0.000
                       Oman Associate   360     0.000
### Batting line-ups faced by bowlers
                       team      tier     n  strength
             Mumbai Indians       IPL  8503     1.000
           Rajasthan Royals       IPL  8717     1.000
Royal Challengers Bengaluru       IPL  8632     1.000
                  Australia      Full  5994     1.000
                    England      Full  7113     1.000
                      India      Full 12735     1.000
        Sunrisers Hyderabad       IPL  8290     1.000
             Gujarat Titans       IPL  8959     1.000
       Lucknow Super Giants       IPL  8434     0.979
      Kolkata Knight Riders       IPL  7516     0.933
                West Indies      Full  9955     0.931
             Delhi Capitals       IPL  8035     0.927
               South Africa      Full  5908     0.927
                New Zealand      Full  9059     0.922
               Punjab Kings       IPL  8354     0.916
        Chennai Super Kings       IPL  8302     0.882
                   Pakistan      Full 10067     0.837
                  Sri Lanka      Full  8116     0.819
                 Bangladesh      Full  8617     0.748
                Afghanistan      Full  5990     0.704
                    Ireland      Full  4994     0.701
                   Zimbabwe      Full  5990     0.668
       United Arab Emirates Associate  2305     0.062
                  Hong Kong Associate   884     0.047
                Netherlands Associate  1368     0.000
                     Canada Associate   480     0.000
                   Scotland Associate   689     0.000
                  Singapore Associate   350     0.000
                      Nepal Associate   359     0.000
   United States Of America Associate   329     0.000
                       Oman Associate   332     0.000

## Opposition model (ridge: batter + bowler + team tier)
alpha chosen by 5-fold match-grouped CV: 1000 (CV MSE: 30: 7.1538, 100: 7.1421, 300: 7.1369, 1000: 7.1368, 3000: 7.1398)
Team-tier effects on batting value (runs per ball; + = easier for the batter):
bowling_side_Associate    0.0822
bowling_side_A-team      -0.0651
batting_side_Associate   -0.1751
batting_side_A-team       0.0960

## Toughest bowlers to face (runs per 100 balls vs average, >= 600 balls)
Jasprit Bumrah        -22.30
Varun Chakravarthy    -15.25
Sunil Narine          -14.34
Noor Ahmad            -13.18
Matheesha Pathirana   -12.93
Kuldeep Yadav         -12.68
Rashid Khan           -12.59
Josh Hazlewood        -11.92
Bhuvneshwar Kumar     -11.68
Mohsin Khan           -11.39
Blessing Muzarabani   -10.84
Nathan Ellis          -10.74

## Most dangerous batters (runs per 100 balls vs average, >= 600 balls)
Vaibhav Sooryavanshi    26.54
Abhishek Sharma         24.28
Suryakumar Yadav        23.03
Tim David               21.83
Heinrich Klaasen        16.66
Andre Russell           15.23
Rajat Patidar           12.65
Phil Salt               12.60
Nicholas Pooran         11.99
Dinesh Karthik          11.51
Romario Shepherd        10.74
Finn Allen              10.68

## Batters
Evidence weighting {'recency_decay': 0.1, 'comp': {'IPL': 1.0, 'T20I': 0.8, 'T20I_strong': 1.0}, 'strong_t20i_teams': ('India', 'Australia', 'England', 'South Africa', 'New Zealand'), 'opponent': (0.5, 1.0)} (recency measured back from 2026-11-01). Eligible players' pressure records count at 69% of their raw size (median; range 55%-86%)
Players: 824 | eligible (>= 100 pressure balls, >= 15 games): 110 | eligible & active since 2025: 105
Shrinkage: baseline k = 595 balls, pressure k = 1006 balls (a player with k pressure balls gets 50% weight on their own record)
Pressure shrunk towards league mean: k = 855 balls
Pressure prior = 3.22 + 0.57 x shrunk baseline (per 100)
Eligible players' pressure-ball mix: IPL 53%, T20I 47%, Emerging 0%
IPL vs T20I consistency: 39 eligible players with >= 40 pressure balls in both; correlation of adjusted pressure value = 0.20

### Preview: eligible batters by pressure value shrunk to league mean (p_lg, per 100); p_shrunk = shrunk to own-baseline prior
                name                              teams   p_n  p_n_w  p_evidence_share  p_opp_strength  p_games  p_raw100  p_opp100  p_adj100  p_weight_lg  p_lg100  p_shrunk100  b_shrunk100  p_share_T20I  p_share_Emerging  active
    Suryakumar Yadav              India, Mumbai Indians 568.0 377.87              0.67            0.86     82.0     27.75     -2.07     29.82         0.31    10.79        19.03        20.55          0.41               0.0    True
    Heinrich Klaasen  Sunrisers Hyderabad, South Africa 298.0 227.62              0.76            0.96     51.0     37.37     -3.63     41.00         0.21    10.50        16.87        14.30          0.17               0.0    True
        Shreyas Iyer                India, Punjab Kings 416.0 325.49              0.78            0.90     53.0     28.80     -2.62     31.42         0.28    10.39        12.09         4.56          0.25               0.0    True
         Virat Kohli Royal Challengers Bengaluru, India 301.0 226.34              0.75            0.93     37.0     30.80     -2.89     33.69         0.21     8.94        10.87         4.38          0.18               0.0    True
      Dinesh Karthik Royal Challengers Bengaluru, India 234.0 146.48              0.63            0.88     46.0     44.73     -2.18     46.91         0.15     8.90        12.50         7.46          0.25               0.0   False
        Rohit Sharma              Mumbai Indians, India 147.0 105.06              0.71            0.91     25.0     52.16     -2.90     55.06         0.11     8.15         4.13        -7.71          0.20               0.0    True
          Sam Curran              Punjab Kings, England 298.0 197.78              0.66            0.85     40.0     28.36     -2.98     31.34         0.19     7.82         4.34        -7.32          0.43               0.0    True
     Ashutosh Sharma       Delhi Capitals, Punjab Kings 128.0 105.32              0.82            0.96     21.0     39.49     -4.51     44.01         0.11     6.95        11.47         8.47          0.00               0.0    True
     Reeza Hendricks                       South Africa 152.0  87.80              0.58            0.77     19.0     48.62     -1.73     50.35         0.09     6.85         8.47         2.79          1.00               0.0    True
       Dewald Brevis  Chennai Super Kings, South Africa 145.0 109.44              0.75            0.92     23.0     36.53     -4.41     40.93         0.11     6.76         7.96         2.01          0.22               0.0    True
       Cameron Green          Australia, Mumbai Indians 269.0 182.65              0.68            0.81     43.0     23.95     -2.59     26.55         0.18     6.64         8.93         4.38          0.43               0.0    True
         Riyan Parag            Rajasthan Royals, India 295.0 220.34              0.75            0.93     43.0     19.43     -3.25     22.69         0.20     6.54         9.46         5.84          0.02               0.0    True
Namboori Tilak Varma              Mumbai Indians, India 673.0 471.73              0.70            0.85     82.0     11.28     -2.47     13.75         0.36     6.42         9.99         8.76          0.43               0.0    True
    Yashasvi Jaiswal            Rajasthan Royals, India 210.0 152.32              0.73            0.92     25.0     26.25     -2.63     28.88         0.15     6.39         9.13         5.10          0.06               0.0    True
           Tim David          Australia, Mumbai Indians 436.0 301.37              0.69            0.88     66.0     13.76     -3.60     17.36         0.26     6.29        17.21        24.37          0.47               0.0    True
     Nicholas Pooran  Lucknow Super Giants, West Indies 484.0 333.78              0.69            0.92     66.0     12.45     -3.43     15.88         0.28     6.17        11.34        11.57          0.38               0.0    True
  Azmatullah Omarzai          Afghanistan, Punjab Kings 144.0  97.92              0.68            0.79     33.0     36.71     -1.99     38.70         0.10     6.12         5.65        -1.39          0.78               0.0    True
     George Dockrell                            Ireland 164.0  99.16              0.60            0.84     25.0     36.10     -0.88     36.98         0.10     5.98         5.81        -0.85          1.00               0.0    True
     Abhishek Sharma         Sunrisers Hyderabad, India 207.0 158.03              0.76            0.88     44.0     22.02     -2.58     24.60         0.16     5.85        19.11        26.26          0.26               0.0    True
      Shashank Singh  Punjab Kings, Sunrisers Hyderabad 145.0 115.71              0.80            0.99     25.0     26.31     -5.05     31.36         0.12     5.84         8.83         5.27          0.00               0.0    True
       Andre Russell Kolkata Knight Riders, West Indies 247.0 166.66              0.67            0.91     40.0     20.68     -2.56     23.24         0.16     5.79        13.52        15.19          0.13               0.0    True
       Dasun Shanaka        Sri Lanka, Rajasthan Royals 275.0 174.20              0.63            0.86     47.0     20.28     -2.10     22.38         0.17     5.77         6.19         0.28          0.89               0.0    True
       Towhid Hridoy                         Bangladesh 190.0 130.69              0.69            0.83     28.0     24.83     -1.14     25.98         0.13     5.51         5.17        -1.32          1.00               0.0    True
         Harry Brook       England, Sunrisers Hyderabad 150.0  95.14              0.63            0.87     32.0     29.55     -3.03     32.58         0.10     5.41        10.35         8.79          0.94               0.0    True
   Washington Sundar              Gujarat Titans, India 213.0 158.89              0.75            0.88     31.0     17.71     -3.58     21.29         0.16     5.35         5.61        -0.15          0.41               0.0    True

### Biggest movers vs raw pressure value (rank among eligible)
                name   p_n  p_raw100  p_opp100  p_lg100  rank_raw  rank_shrunk
Namboori Tilak Varma 673.0     11.28     -2.47     6.42      48.0         13.0
     Nicholas Pooran 484.0     12.45     -3.43     6.17      44.0         16.0
   Bhanuka Rajapaksa 113.0     25.66     -1.69     4.16      18.0         42.0
        Kusal Perera 108.0     29.59     -1.05     4.65      10.0         34.0
     Rachin Ravindra 111.0     19.08     -1.48     3.78      30.0         53.0
           Tim David 436.0     13.76     -3.60     6.29      38.0         15.0
      Curtis Campher 117.0     12.48     -1.27     3.19      43.0         61.0
       Hardik Pandya 480.0      8.18     -2.01     4.47      55.0         37.0
      Tristan Stubbs 325.0     11.53     -2.83     5.09      47.0         29.0
      Shamim Hossain 132.0     19.30     -2.47     4.16      28.0         44.0

## Bowlers
Evidence weighting {'recency_decay': 0.1, 'comp': {'IPL': 1.0, 'T20I': 0.8, 'T20I_strong': 1.0}, 'strong_t20i_teams': ('India', 'Australia', 'England', 'South Africa', 'New Zealand'), 'opponent': (0.5, 1.0)} (recency measured back from 2026-11-01). Eligible players' pressure records count at 70% of their raw size (median; range 46%-89%)
Players: 596 | eligible (>= 120 pressure balls, >= 15 games): 98 | eligible & active since 2025: 96
Shrinkage: baseline k = 829 balls, pressure k = 1818 balls (a player with k pressure balls gets 50% weight on their own record)
Pressure shrunk towards league mean: k = 720 balls
Pressure prior = -1.94 + 1.32 x shrunk baseline (per 120)
Eligible players' pressure-ball mix: IPL 53%, T20I 47%, Emerging 0%
IPL vs T20I consistency: 44 eligible players with >= 40 pressure balls in both; correlation of adjusted pressure value = 0.13

### Preview: eligible bowlers by pressure value shrunk to league mean (p_lg, per 120); p_shrunk = shrunk to own-baseline prior
               name                                             teams   p_n  p_n_w  p_evidence_share  p_opp_strength  p_games  p_raw120  p_opp120  p_adj120  p_weight_lg  p_lg120  p_shrunk120  b_shrunk120  p_share_T20I  p_share_Emerging  active
 Varun Chakravarthy                      Kolkata Knight Riders, India 483.0 368.88              0.76            0.95     66.0     31.83     -5.52     37.35         0.34    14.47        24.32        17.89          0.37               0.0    True
      Krunal Pandya Lucknow Super Giants, Royal Challengers Bengaluru 275.0 209.38              0.76            0.97     37.0     49.03     -4.99     54.03         0.23    14.30        11.50         6.47          0.00               0.0    True
       Sunil Narine                             Kolkata Knight Riders 340.0 256.77              0.76            0.97     47.0     35.28     -6.26     41.54         0.26    12.95        22.47        16.45          0.00               0.0    True
  Mustafizur Rahman                        Bangladesh, Delhi Capitals 349.0 209.48              0.60            0.77     59.0     38.49     -1.86     40.34         0.23    11.23        15.56        11.09          0.75               0.0    True
      Kuldeep Yadav                             Delhi Capitals, India 463.0 340.45              0.74            0.91     67.0     22.84     -4.05     26.90         0.32    10.51        16.67        12.65          0.26               0.0    True
        Trent Boult                  Rajasthan Royals, Mumbai Indians 273.0 192.71              0.71            0.95     45.0     34.08     -5.35     39.43         0.21    10.50         7.24         4.37          0.13               0.0    True
  Bhuvneshwar Kumar  Sunrisers Hyderabad, Royal Challengers Bengaluru 374.0 266.18              0.71            0.94     61.0     21.93     -6.34     28.27         0.27     9.64        19.81        15.53          0.23               0.0    True
       Nathan Ellis                           Australia, Punjab Kings 281.0 199.21              0.71            0.95     36.0     26.95     -7.49     34.44         0.22     9.62        15.48        11.62          0.52               0.0    True
    Lockie Ferguson                       New Zealand, Gujarat Titans 224.0 153.51              0.69            0.93     34.0     32.71     -5.70     38.41         0.18     9.02         7.47         5.15          0.29               0.0    True
      Eshan Malinga                    Sunrisers Hyderabad, Sri Lanka 125.0  99.98              0.80            0.89     23.0     49.12     -3.90     53.02         0.12     8.88        11.81         8.70          0.50               0.0    True
   Mitchell Santner                       New Zealand, Mumbai Indians 303.0 211.01              0.70            0.83     54.0     24.79     -4.71     29.50         0.23     8.81        11.08         8.24          0.64               0.0    True
Matheesha Pathirana                    Chennai Super Kings, Sri Lanka 282.0 202.66              0.72            0.92     35.0     24.60     -4.96     29.56         0.22     8.64        17.80        13.96          0.33               0.0    True
     Mitchell Starc             Delhi Capitals, Kolkata Knight Riders 138.0 105.83              0.77            0.96     30.0     41.37     -4.16     45.53         0.13     8.24        -4.83        -4.41          0.20               0.0    True
     Jasprit Bumrah                             Mumbai Indians, India 375.0 286.59              0.76            0.93     56.0     16.39     -4.61     21.00         0.28     7.95        31.22        26.34          0.21               0.0    True
       Vyshak Kumar         Punjab Kings, Royal Challengers Bengaluru 128.0 100.80              0.79            0.98     18.0     39.47     -4.89     44.37         0.12     7.86        -3.17        -2.93          0.00               0.0    True
     Gudakesh Motie                                       West Indies 218.0 170.09              0.78            0.95     26.0     25.06     -4.11     29.17         0.19     7.80         0.16        -0.46          1.00               0.0    True
        Rashid Khan                       Gujarat Titans, Afghanistan 645.0 416.73              0.65            0.86     94.0     12.63     -3.61     16.24         0.37     7.70        18.57        15.94          0.39               0.0    True
     Mohammad Nawaz                                          Pakistan 243.0 152.89              0.63            0.79     35.0     28.20     -1.89     30.10         0.18     7.54         9.31         7.20          1.00               0.0    True
      Naveen ul Haq                 Afghanistan, Lucknow Super Giants 146.0  90.47              0.62            0.88     23.0     40.47     -4.34     44.80         0.11     7.45         8.57         6.59          0.52               0.0   False
     Mohammed Siraj       Royal Challengers Bengaluru, Gujarat Titans 302.0 227.55              0.75            0.96     60.0     16.44     -5.60     22.04         0.24     7.39         9.15         7.18          0.05               0.0    True
      Harpreet Brar                                      Punjab Kings 151.0 116.66              0.77            0.97     25.0     29.58     -4.95     34.53         0.14     7.18         5.27         4.04          0.00               0.0    True
         Noor Ahmad               Chennai Super Kings, Gujarat Titans 363.0 265.24              0.73            0.87     51.0     13.14     -4.67     17.82         0.27     6.81        19.68        16.58          0.34               0.0    True
   Mujeeb Ur Rahman                       Afghanistan, Mumbai Indians 132.0  70.15              0.53            0.66     23.0     49.58      1.62     47.95         0.09     6.77         6.99         5.57          1.00               0.0    True
         Axar Patel                             India, Delhi Capitals 506.0 364.80              0.72            0.91     86.0     10.10     -4.40     14.50         0.34     6.70         6.96         5.60          0.54               0.0    True
     Josh Hazlewood            Royal Challengers Bengaluru, Australia 295.0 217.51              0.74            0.94     45.0     14.72     -4.47     19.19         0.23     6.57        19.26        16.06          0.28               0.0    True

### Biggest movers vs raw pressure value (rank among eligible)
             name   p_n  p_raw120  p_opp120  p_lg120  rank_raw  rank_shrunk
 Mujeeb Ur Rahman 132.0     49.58      1.62     6.77       1.0         23.0
  Richard Ngarava 126.0     30.59     -1.74     5.59      13.0         31.0
    Kuldeep Yadav 463.0     22.84     -4.05    10.51      21.0          5.0
Michael Bracewell 127.0     31.23     -3.93     6.11      12.0         28.0
     Taskin Ahmed 173.0     18.24      0.46     4.51      25.0         41.0
     Tanzim Sakib 172.0     20.60      1.77     4.65      24.0         40.0
Bhuvneshwar Kumar 374.0     21.93     -6.34     9.64      23.0          7.0
      Rashid Khan 645.0     12.63     -3.61     7.70      32.0         17.0
    Naveen ul Haq 146.0     40.47     -4.34     7.45       5.0         19.0
   Jasprit Bumrah 375.0     16.39     -4.61     7.95      27.0         14.0
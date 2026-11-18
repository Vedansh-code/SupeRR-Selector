# Phase 3 summary

## Expectation models: actual vs expected totals by pressure band (should be close)
               bat_runs  exp_bat_runs  striker_outs  exp_striker_outs  bowler_runs  exp_bowler_runs  bowler_wkts  exp_bowler_wkts
pressure_band                                                                                                                    
high              53235       53260.8          2306            2286.5        55336          55345.8         2228           2211.8
low              135459      135481.8          5224            5229.7       140505         140408.3         5095           5093.2
medium            80812       80697.6          3029            3042.8        83670          83446.8         2938           2958.2

League totals: batting value 1578.9 runs, bowling value -1947.1 runs (both should be ~0 by construction)

## Wicket value (runs) by over
innings     1     2
overid             
1        10.9  11.0
2        10.7  10.9
3        10.6  10.8
4        10.6  10.7
5        10.2  10.5
6         9.8  10.1
7         9.3   9.8
8         8.9   9.4
9         8.5   8.9
10        8.0   8.3
11        7.4   8.0
12        6.9   7.5
13        6.2   6.8
14        5.5   6.1
15        4.9   5.5
16        4.1   4.9
17        3.2   4.1
18        2.3   3.2
19        1.5   2.5
20        0.5   1.0

## Wicket value, innings 1, by wickets down x phase
phase        death  middle  powerplay
wkts_before                          
0              0.7     5.2        9.6
1              0.8     5.5       10.2
2              1.0     6.9       13.4
3              1.2     6.4       11.5
4              1.4     7.7       15.1
5              2.8    13.1       27.6
6              2.6    11.3       20.6
7              2.1     9.2        NaN
8              4.1     7.4        NaN
9              8.7    13.6        NaN

## Players: 824 batters, 596 bowlers
Correlation of pressure value with baseline value (>= 120 pressure balls): batters 0.05, bowlers 0.29

## PREVIEW (unadjusted, no shrinkage/opposition): batters, >= 120 pressure balls, by value per 100
              name                                     teams  p_balls  p_inns   p_sr  p_exp_sr  p_avg  p_out_ratio  p_value100  b_value100  delta_value100  p_levw_value100  p_wpa
   Reeza Hendricks                              South Africa    152.0    19.0 192.76    164.54 146.50         0.23       47.96        7.46           40.51            46.71   1.37
      Rohit Sharma                     Mumbai Indians, India    147.0    25.0 189.12    163.95  69.50         0.49       47.22      -12.93           60.15            71.59   1.09
   Ashutosh Sharma              Delhi Capitals, Punjab Kings    128.0    21.0 166.41    148.40  30.43         0.78       44.30       33.92           10.39            59.33   1.63
    Dinesh Karthik        Royal Challengers Bengaluru, India    234.0    46.0 169.23    148.11  49.50         0.51       42.45       15.69           26.76            51.08   1.34
  Heinrich Klaasen         Sunrisers Hyderabad, South Africa    298.0    51.0 169.80    147.02  36.14         0.85       38.46       24.16           14.30            38.44   1.91
   George Dockrell                                   Ireland    164.0    25.0 156.71    132.57  51.40         0.49       36.43       -8.87           45.31            37.60   1.52
     Dewald Brevis         Chennai Super Kings, South Africa    145.0    23.0 166.21    136.14  24.10         1.49       35.78        0.55           35.22            24.25   0.20
    Shashank Singh         Punjab Kings, Sunrisers Hyderabad    145.0    25.0 172.41    156.71  50.00         0.57       31.40       11.11           20.29            41.73   1.23
Azmatullah Omarzai                 Afghanistan, Punjab Kings    144.0    33.0 159.03    132.45  25.44         1.05       31.33       -7.34           38.67            22.08   0.92
  Yashasvi Jaiswal                   Rajasthan Royals, India    210.0    25.0 174.76    157.57  36.70         0.93       30.66        7.43           23.24            34.17   1.62
       Virat Kohli        Royal Challengers Bengaluru, India    301.0    37.0 162.13    155.95  69.71         0.44       28.89        3.29           25.61            20.57   1.66
  Suryakumar Yadav                     India, Mumbai Indians    568.0    82.0 162.85    145.99  38.54         0.78       28.69       29.95           -1.27            22.25   3.13
        Sam Curran                     Punjab Kings, England    298.0    40.0 144.30    135.09  47.78         0.54       28.06      -21.31           49.37            29.69   2.23
         Phil Salt      England, Royal Challengers Bengaluru    142.0    24.0 164.08    153.48  46.60         0.69       27.83       18.80            9.03            23.08   1.07
     Cameron Green                 Australia, Mumbai Indians    269.0    43.0 161.34    142.52  36.17         0.89       27.00        7.90           19.10            38.59   0.72
       Abdul Samad Sunrisers Hyderabad, Lucknow Super Giants    128.0    26.0 153.91    139.18  21.89         1.14       26.84      -12.39           39.23            16.51  -0.28
      Shreyas Iyer                       India, Punjab Kings    416.0    53.0 167.55    153.45  49.79         0.63       26.66        5.94           20.72            31.48   4.26
     Towhid Hridoy                                Bangladesh    190.0    28.0 134.74    127.33  64.00         0.41       26.19       -6.25           32.44            23.85   1.43
   Abhishek Sharma                Sunrisers Hyderabad, India    207.0    44.0 187.44    160.17  35.27         1.07       26.18       33.69           -7.51            17.36   0.54
       Harry Brook              England, Sunrisers Hyderabad    150.0    32.0 166.00    132.38  24.90         1.20       26.03       11.59           14.44            29.69   1.14

## PREVIEW: bowlers, >= 120 pressure balls, by runs saved per 20 overs
              name                                             teams                   type  p_balls  p_matches  p_econ  p_exp_econ  p_wkts  p_wkt_ratio  p_value120  b_value120  delta_value120  p_levw_value120  p_wpa
  Mujeeb Ur Rahman                       Afghanistan, Mumbai Indians     Right-arm offbreak    132.0       23.0    6.41        7.56    11.0         1.52       51.32       12.18           39.15            58.00   1.03
     Naveen ul Haq                 Afghanistan, Lucknow Super Giants  Right-arm medium-fast    146.0       23.0    8.84        9.48    11.0         1.21       47.82       11.00           36.81            19.24  -0.53
     Krunal Pandya Lucknow Super Giants, Royal Challengers Bengaluru Slow left-arm orthodox    275.0       37.0    6.39        7.82    18.0         1.44       46.16        0.50           45.66            48.30   2.62
       Mohsin Khan                              Lucknow Super Giants   Left-arm medium-fast    128.0       21.0    8.95        9.59    12.0         1.57       40.65       25.85           14.80            52.71   0.69
   Lockie Ferguson                       New Zealand, Gujarat Titans         Right-arm Fast    224.0       34.0    8.22        8.96    15.0         1.24       37.54        3.17           34.37            37.75   0.67
 Mustafizur Rahman                        Bangladesh, Delhi Capitals        Left-arm medium    349.0       59.0    7.94        9.14    28.0         1.21       36.36       14.88           21.48            25.01  -0.29
     Eshan Malinga                    Sunrisers Hyderabad, Sri Lanka  Right-arm fast-medium    125.0       23.0    9.22       10.03    10.0         1.21       34.18        3.81           30.37            29.64   1.22
   Richard Ngarava                                          Zimbabwe   Left-arm fast-medium    126.0       22.0    7.38        8.71    10.0         1.16       33.05        0.60           32.45             9.46   0.06
    Mitchell Starc             Delhi Capitals, Kolkata Knight Riders          Left-arm Fast    138.0       30.0    8.83        9.09    16.0         1.82       32.99      -24.41           57.39            15.58   0.99
       Trent Boult                  Rajasthan Royals, Mumbai Indians   Left-arm fast-medium    273.0       45.0    8.46        9.34    21.0         1.30       32.47       -1.19           33.66            34.20   0.70
      Vyshak Kumar         Punjab Kings, Royal Challengers Bengaluru       Right-arm medium    128.0       18.0    8.16        9.97     7.0         0.95       31.50      -31.22           62.72            23.97  -0.03
      Nathan Ellis                           Australia, Punjab Kings       Right-arm medium    281.0       36.0    8.07        9.34    20.0         1.15       30.02       19.04           10.98            15.14  -0.05
    Gudakesh Motie                                       West Indies Slow left-arm orthodox    218.0       26.0    6.69        7.98    15.0         1.25       29.96      -13.91           43.87            31.47   0.50
      Sunil Narine                             Kolkata Knight Riders     Right-arm offbreak    340.0       47.0    6.34        7.73    20.0         1.20       29.53       18.84           10.70            37.23   2.02
 Michael Bracewell          New Zealand, Royal Challengers Bengaluru     Right-arm offbreak    127.0       24.0    7.32        7.69    10.0         1.50       29.00       12.14           16.86            27.61   0.67
Varun Chakravarthy                      Kolkata Knight Riders, India    Right-arm Leg-Break    483.0       66.0    6.99        7.69    33.0         1.34       28.86       19.41            9.44            27.86   1.40
    Shaheen Afridi                                          Pakistan          Left-arm Fast    164.0       28.0    8.78        9.19    14.0         1.28       27.16       10.11           17.05            30.02   0.12
    Mohammad Nawaz                                          Pakistan Slow left-arm orthodox    243.0       35.0    6.47        6.77    17.0         1.54       26.86       12.78           14.08            23.53   1.40
     Harpreet Brar                                      Punjab Kings Slow left-arm orthodox    151.0       25.0    7.51        7.81     8.0         1.16       24.43       -5.25           29.68            29.12   0.69
  Mitchell Santner                       New Zealand, Mumbai Indians Slow left-arm orthodox    303.0       54.0    6.87        7.94    19.0         1.20       24.30        3.51           20.79            23.38   0.42
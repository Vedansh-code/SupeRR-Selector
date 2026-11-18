# Phase 1 summary
deliveries (innings 1-2): 200,961
matches with ball data: 867 / 883 in matches.csv
matches by competition tier: Emerging 30, IPL 367, T20I 470
no-result matches with ball data: 25
DLS / revised matches: 27
tied matches (super over / eliminator): 10
knockout matches: 31

## Result reconciliation (margin text vs reconstructed scores)
margin_check
match                        827
n/a (tie/no result/other)     34
MISMATCH                       6

## Winner check (did the chasing side reach the target?)
winner_check
match       831
n/a          34
MISMATCH      2

## Legal balls per over (should be 6 except last over)
is_legal
0        1
1       98
2       99
3      106
4      131
5      145
6    31757
7        1

## Mismatches
     match_id                                  result  runs1  wkts1  runs2  wkts2  target2  is_dls
49      14130       Lucknow Super Giants Won 36  Runs  167.0    6.0  130.0    8.0    168.0   False
190     20182  Punjab Kings Won by 7 Runs(D/L Method)  191.0    5.0  146.0    7.0    192.0    True
198     20190   Lucknow Super Giants Won by 6 wickets  121.0    8.0  127.0    5.0    122.0   False
293     24822        India Won by 2 Runs (DLS method)  139.0    7.0   47.0    2.0    140.0    True
316     28334  New Zealand won by 17runs (DLS Method)  110.0   10.0   95.0    5.0    111.0    True
820     48610     England Won by 11 runs (DLS method)  133.0   10.0  125.0    4.0    115.0    True
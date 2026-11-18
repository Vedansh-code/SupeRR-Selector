# Phase 7: robustness to all judgement calls at once

500 replicates; each redraws every setting (pressure definition, evidence weights, rating weights, track-record weight, recent-data nerf) and resamples matches. Tiers: Lock >= 75% in the top 10, Strong 50-75%, Contender 25-50%, Long shot < 25%.

## Batters
                name  rank  p_top10  p_top10_settings_only  median_rank 90%_rank_range      tier
        Shreyas Iyer   1.0     0.90                   1.00          3.0           1-14      Lock
    Suryakumar Yadav   2.0     0.93                   1.00          3.0           1-12      Lock
    Heinrich Klaasen   3.0     0.88                   1.00          4.0           1-16      Lock
         Virat Kohli   4.0     0.44                   0.85         11.0           3-47 Contender
           Tim David   5.0     0.70                   1.00          6.0           1-32    Strong
     Abhishek Sharma   6.0     0.60                   0.98          7.0           1-43    Strong
     Ashutosh Sharma   7.0     0.30                   0.63         13.0           2-65 Contender
Namboori Tilak Varma   8.0     0.58                   0.99          8.0           1-38    Strong
       Cameron Green   9.0     0.25                   0.42         20.0           4-63 Contender
    Yashasvi Jaiswal  10.0     0.16                   0.17         25.0           6-76 Long shot
        Rohit Sharma  11.0     0.10                   0.04         33.0           7-99 Long shot
      Shashank Singh  12.0     0.24                   0.21         18.0           4-59 Long shot
       Dewald Brevis  13.0     0.18                   0.01         23.0           4-73 Long shot
          Sam Curran  14.0     0.11                   0.03         32.0           7-86 Long shot
         Riyan Parag  15.0     0.13                   0.00         30.0           7-77 Long shot
       Andre Russell  16.0     0.21                   0.19         23.0           4-74 Long shot
     Nicholas Pooran  20.0     0.27                   0.25         20.0           3-70 Contender
       Rovman Powell  29.0     0.27                   0.50         18.0           5-62 Contender

## Bowlers
               name  rank  p_top10  p_top10_settings_only  median_rank 90%_rank_range      tier
 Varun Chakravarthy   1.0     0.94                   1.00          3.0           1-11      Lock
     Jasprit Bumrah   2.0     0.93                   1.00          3.0           1-12      Lock
       Sunil Narine   3.0     0.89                   1.00          4.0           1-13      Lock
      Krunal Pandya   4.0     0.54                   0.86          9.0           2-33    Strong
      Kuldeep Yadav   5.0     0.65                   1.00          8.0           1-27    Strong
     Josh Hazlewood   6.0     0.54                   0.97          9.0           1-42    Strong
        Rashid Khan   7.0     0.70                   0.97          6.0           1-26    Strong
  Bhuvneshwar Kumar   8.0     0.53                   0.84         10.0           2-35    Strong
Matheesha Pathirana   9.0     0.49                   0.95         11.0           4-27 Contender
         Noor Ahmad  10.0     0.48                   0.74         11.0           2-42 Contender
  Mustafizur Rahman  11.0     0.23                   0.14         16.0           6-36 Long shot
       Nathan Ellis  12.0     0.20                   0.09         18.0           6-42 Long shot
      Eshan Malinga  13.0     0.13                   0.02         17.5           5-49 Long shot
         Axar Patel  14.0     0.21                   0.15         19.0           6-46 Long shot
  Wanindu Hasaranga  15.0     0.21                   0.08         18.0           6-42 Long shot
   Mitchell Santner  20.0     0.21                   0.05         20.0           5-55 Long shot

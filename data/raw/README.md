# Raw data: the Rajasthan Royals data pack

This project uses the ball-by-ball data pack that Rajasthan Royals provided to participants of **SupeRR Selector Season 2** (hosted on Unstop). The data isn't ours to redistribute, so it isn't included in this repository.

## How to get it

1. Register for the SupeRR Selector Season 2 challenge on Unstop and download the data pack from the challenge page.
2. Put the six CSV files below in this folder (`data/raw/`).
3. Check that you have the same version: the SHA-256 checksums should match the table.

```bash
sha256sum data/raw/*.csv
```

On Windows PowerShell: `Get-FileHash data\raw\*.csv -Algorithm SHA256`

## Files used

| File | Rows | Size (bytes) | SHA-256 |
|---|---:|---:|---|
| `ball_by_ball.csv` | 200,999 | 41,071,837 | `01e2b4379edfbab6a6e456d304cb3c70f554cb312ef93d9588f3f32a82cb396e` |
| `competition_team_player_mapping.csv` | 6,413 | 462,969 | `1ded4e42a933618572d6e2c3a521c3257eb1844fab4456d567d77cbb2d3bbb12` |
| `competitions.csv` | 141 | 7,624 | `507ceb7189f972d4e4f299ddcfc97f3c3247af1913f6291106f161fa8353fd9b` |
| `matches.csv` | 883 | 123,864 | `bb100ab84b8b9a15160c1f2315cf675210131a30e779ec5079fd5403dcf56eef` |
| `playing_eleven.csv` | 28,381 | 966,287 | `7517c73722a28d5d61c808ccf0cbed315a8780586d02e946eb9a7f5daf011c27` |
| `teams.csv` | 353 | 6,922 | `a65e5922a9b3bf49247b24fc9471782e700efb31f8dcc5042923238b87c50a5d` |

Row counts exclude the header line.

## What's in it

- **Coverage:** IPL and T20 international matches from 2022 to 2026, plus two A-team events (Emerging Teams Asia Cup 2024 and Asia Cup Rising Stars 2025).
- **Matches:** 883 are listed, and 867 have ball-by-ball data.
- **Deliveries:** 200,961 in innings 1 and 2; super overs are dropped.
- **Contents:** one row per delivery, with runs, extras, dismissals, batter and bowler, plus match, competition, team and playing-XI tables.

How each column is used, and the cleaning rules (wides, no-balls, DLS, ties, super overs), are in the main [README](../../README.md) under Phase 1.

## Without the data

You can still use everything in the repository that doesn't need the raw files:
- **Results tables:** `outputs/tables/`, including the final top 10s.
- **The dashboard:** `dashboard.html`, or the live link in the main README.
- **The report:** in `report/`.

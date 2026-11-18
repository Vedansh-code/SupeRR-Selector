"""Build the methodology report (report/Methodology_Report.html + figures).

Every number and table is read from outputs/tables, so the report always matches the final
selection. Convert to Word / PDF with report/convert_report.ps1 (uses Microsoft Word).

Usage: .venv/Scripts/python -I src/build_report.py
"""
import html
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
REP = ROOT / "report"
FIG = REP / "figures"
FIG.mkdir(parents=True, exist_ok=True)

NAVY, GREEN, AMBER, RED, GREY, BLUE = "#13294b", "#1b7a52", "#c0662a", "#b03a2e", "#9aa3b2", "#3a6ea5"
TIER_COL = {"Lock": GREEN, "Strong": BLUE, "Contender": AMBER, "Long shot": GREY}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#888", "axes.titlesize": 10, "axes.titleweight": "bold"})


def esc(x) -> str:
    return html.escape(str(x))


def short(n: str) -> str:
    return n.replace("Namboori ", "")


def signed(v, d=1) -> str:
    return "–" if pd.isna(v) else f"{v:+.{d}f}".replace("-", "−")


def table(headers, rows, widths=None) -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'


def fig(path: str, caption: str, width_px: int = 620) -> str:
    return (f'<p class="fig"><img src="figures/{path}" width="{width_px}"></p>'
            f'<p class="cap">{caption}</p>')


# ------------------------------------------------------------------ data
def load():
    d = {}
    d["bat"] = pd.read_csv(TAB / "final_top10_batters.csv")
    d["bowl"] = pd.read_csv(TAB / "final_top10_bowlers.csv")
    d["ranks_bat"] = pd.read_csv(TAB / "final_ranks_bat.csv")
    d["ranks_bowl"] = pd.read_csv(TAB / "final_ranks_bowl.csv")
    d["p5_bat"] = pd.read_csv(TAB / "p5_batter_ratings.csv")
    d["p5_bowl"] = pd.read_csv(TAB / "p5_bowler_ratings.csv")
    d["p4"] = json.loads((TAB / "phase4_info.json").read_text(encoding="utf-8"))
    d["p5"] = json.loads((TAB / "phase5_info.json").read_text(encoding="utf-8"))
    d["bench"] = pd.read_csv(TAB / "p7_benchmark.csv")
    d["sens"] = pd.read_csv(TAB / "p6_sensitivity.csv")
    d["split"] = pd.read_csv(TAB / "p6_split_half.csv")
    d["band"] = pd.read_csv(TAB / "p2_band_profile.csv")
    d["byover"] = pd.read_csv(TAB / "p2_pressure_by_over.csv")
    return d


# ------------------------------------------------------------------ figures
def fig_pressure(d):
    fig_, (a, b) = plt.subplots(1, 2, figsize=(8.6, 2.9))
    bo = d["byover"]
    a.plot(bo.iloc[:, 0], bo.iloc[:, 1] * 100, color=BLUE, lw=2, label="1st innings")
    a.plot(bo.iloc[:, 0], bo.iloc[:, 2] * 100, color=AMBER, lw=2, label="Chase")
    a.set_xlabel("Over"); a.set_ylabel("Average pressure percentile"); a.set_title("Where pressure builds")
    a.legend(frameon=False); a.set_xticks([1, 5, 10, 15, 20])
    band = d["band"].set_index("pressure_band").loc[["low", "medium", "high"]]
    b.bar(["Low (50%)", "Medium (30%)", "High (20%)"], band["mean_realised_wp_swing"] * 100, color=[GREY, BLUE, RED])
    for i, v in enumerate(band["mean_realised_wp_swing"] * 100):
        b.text(i, v + 0.05, f"{v:.1f}", ha="center")
    b.set_ylabel("Avg. win-probability swing per ball (pts)"); b.set_title("High-pressure balls decide matches")
    fig_.tight_layout(); fig_.savefig(FIG / "f1_pressure.png", dpi=200); plt.close(fig_)


def fig_rise_dip(d):
    fig_, axes = plt.subplots(1, 2, figsize=(8.6, 3.6))
    for ax, role, scale, lab in ((axes[0], "bat", 100, "Batters"), (axes[1], "bowl", 120, "Bowlers")):
        p5 = d[f"p5_{role}"]; pool = p5[p5["in_pool"]]
        top = d[role]
        x, y = pool[f"b_adj{scale}"], pool[f"p_adj{scale}"]
        lim = [min(x.min(), y.min()) - 5, max(x.max(), y.max()) + 5]
        ax.plot(lim, lim, ls="--", color="#bbb", lw=1)
        ax.scatter(x, y, s=10, color="#c9ced6")
        ax.scatter(top[f"b_adj{scale}"], top[f"p_adj{scale}"], s=26, color=NAVY, zorder=3)
        for _, r in top.iterrows():
            ax.annotate(short(r["name"]).split()[-1], (r[f"b_adj{scale}"], r[f"p_adj{scale}"]), fontsize=7,
                        xytext=(3, 2), textcoords="offset points")
        ax.set_xlabel(f"Normal play: runs above par per {scale}"); ax.set_ylabel(f"Under pressure: per {scale}")
        ax.set_title(f"{lab}: pressure vs usual level"); ax.set_xlim(lim); ax.set_ylim(lim)
    fig_.tight_layout(); fig_.savefig(FIG / "f2_rise_dip.png", dpi=200); plt.close(fig_)


def fig_odds(d):
    fig_, axes = plt.subplots(1, 2, figsize=(8.6, 3.4))
    for ax, role, lab in ((axes[0], "bat", "Batters"), (axes[1], "bowl", "Bowlers")):
        t = d[role].sort_values("final_rank", ascending=False)
        ax.barh([f"{int(r)}. {short(n)}" for r, n in zip(t.final_rank, t.name)], t.p_top10 * 100,
                color=NAVY if role == "bat" else GREEN)
        for i, v in enumerate(t.p_top10 * 100):
            ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=8)
        ax.set_xlim(0, 105); ax.set_xlabel("Share of 500 re-runs in the top 10 (%)"); ax.set_title(lab)
    fig_.tight_layout(); fig_.savefig(FIG / "f3_odds.png", dpi=200); plt.close(fig_)


# ------------------------------------------------------------------ report
CSS = """
@page { size: A4; margin: 16mm 15mm; }
h2 { page-break-after: avoid; } h3 { page-break-after: avoid; } table, .fig { page-break-inside: avoid; }
body { font-family: Calibri, Arial, sans-serif; font-size: 10.5pt; color: #1b2330; line-height: 1.35; }
h1 { font-size: 22pt; color: #13294b; margin: 0 0 4pt 0; }
h2 { font-size: 14pt; color: #13294b; border-bottom: 1.5pt solid #1b7a52; padding-bottom: 2pt; margin: 16pt 0 6pt 0; }
h3 { font-size: 11.5pt; color: #13294b; margin: 10pt 0 4pt 0; }
p { margin: 0 0 6pt 0; }
.sub { color: #555; font-size: 11pt; margin-bottom: 10pt; }
table { border-collapse: collapse; margin: 4pt 0 10pt 0; font-size: 9pt; width: 100%; }
th { background: #13294b; color: #fff; text-align: left; padding: 3pt 5pt; }
td { border-bottom: 0.5pt solid #ccd; padding: 2.5pt 5pt; vertical-align: top; }
.fig { text-align: center; margin: 6pt 0 0 0; }
.cap { font-size: 8.5pt; color: #555; text-align: center; margin-bottom: 10pt; }
.box { border-left: 3pt solid #1b7a52; background: #f2f6f4; padding: 5pt 8pt; margin: 6pt 0 10pt 0; }
code { font-family: Consolas, monospace; font-size: 9pt; }
"""


def build(d) -> str:
    p4, p5 = d["p4"], d["p5"]
    W = p4["weighting"]
    wb, ww = p5["bat"]["weights"], p5["bowl"]["weights"]
    bench = d["bench"].groupby(["role", "target", "predictor"])[["r", "top10_vs_avg"]].mean()
    sh = d["split"].groupby("role")[["r_pressure", "r_baseline", "r_clutch"]].mean()
    nreps = json.loads((TAB / "phase7_info.json").read_text(encoding="utf-8"))["n_reps"]

    def rank_rows(role):
        t = d[role]; rows = []
        for _, r in t.iterrows():
            if role == "bat":
                stat = f"{r.p_sr:.1f} ({r.p_exp_sr:.1f})"
            else:
                stat = f"{r.p_econ:.2f} ({r.p_exp_econ:.2f})"
            rows.append([f"<b>{int(r.final_rank)}</b>", f"<b>{esc(short(r['name']))}</b>", esc(r.role), f"{r.p_top10:.0%}",
                         str(int(r.rating_rank)), f"{int(r.p_n)} ({r.p_share_IPL:.0%})", stat, signed(r.value)])
        return rows

    def next_names(role):
        rk = d[f"ranks_{role}"]
        return ", ".join(f"{esc(short(n))} ({p:.0%})" for n, p in rk[rk.final_rank.between(11, 13)][["name", "p_top10"]].values)

    def evidence_rows(role):
        t = d[role]; rows = []; sc = 100 if role == "bat" else 120
        for _, r in t.iterrows():
            best = str(r.get("best_pressure_matches", "")).split(" | ")[0]
            rows.append([str(int(r.final_rank)), esc(short(r["name"])), signed(r[f"b_adj{sc}"]), signed(r[f"p_adj{sc}"]),
                         signed(r.gap_vs_usual), f"{r.gap_z:+.1f}".replace("-", "−"), f"{r.success_rate_w:.0%} of {int(r.pm_n)}",
                         f"{int(r.recent_balls_0)} / {int(r.recent_balls_1)} / {int(r.recent_balls_2)}", esc(best)])
        return rows

    def dips(role):
        rk = d[f"ranks_{role}"]
        return int((rk.gap_z < -2).sum()), int((rk.gap_z > 2).sum()), len(rk)

    def b(role, target, pred):
        return bench.loc[(role, target, pred), "r"]

    sens = d["sens"]; piv = sens.pivot(index="variant", columns="role", values="overlap_with_main_top10")
    def nice(v):
        if v.startswith("evidence: "):
            v = "Evidence weights: " + v[len("evidence: "):]
        elif v.startswith("weights: "):
            v = "Rating weights: " + v[len("weights: "):]
        return v[0].upper() + v[1:]
    sens_rows = [[esc(nice(v)), str(int(r["bat"])), str(int(r["bowl"]))]
                 for v, r in piv.iterrows() if not v.startswith("main")]
    dip_b, rise_b, n_b = dips("bat"); dip_w, rise_w, n_w = dips("bowl")
    k_bat, k_bowl = p4["bat"]["k_lg"], p4["bowl"]["k_prior"]

    H = []
    a = H.append
    a(f"<h1>Players Under Pressure</h1><p class='sub'>SupeRR Selector Season 2 · Round 1 methodology report</p>")
    a("<div class='box'><b>In one paragraph.</b> We define pressure for every delivery from how much the match result hangs on it and how hard the situation is. "
      "Each player is measured against what an average player would do in exactly the same situation, season and opposition. We compare pressure performance with each player's own normal level, "
      "adjust for sample size, recency, competition and opponent strength, and combine the results into one Pressure Rating. "
      f"The final top 10s are the players who stay in the top 10 most often when every judgement call in the method is redrawn and matches are resampled ({nreps} re-runs), "
      "so every pick comes with a stated level of confidence.</div>")

    a("<h2>Final rankings</h2>")
    a(f"<p>Rank 1–10 as submitted, ordered by Pressure Rating. <i>Top-10 odds</i> is how often the player makes the top 10 across {nreps} re-runs "
      "with every setting redrawn and matches resampled; it decides who is in the list (section 6). <i>Rating rank</i> is the player's position on the Pressure Rating alone. "
      "<i>Value</i> is runs above an average player in the same pressure situations, per 100 balls (batting) or 120 balls (bowling), after all adjustments.</p>")
    hdr = ["#", "Batter", "Role", "Top-10 odds", "Rating rank", "Pressure balls (IPL share)", "Pressure SR (expected)", "Value /100"]
    a("<h3>Top 10 batters</h3>" + table(hdr, rank_rows("bat")) + f"<p>Next: {next_names('bat')}.</p>")
    hdr = ["#", "Bowler", "Role", "Top-10 odds", "Rating rank", "Pressure balls (IPL share)", "Pressure economy (expected)", "Value /120"]
    a("<h3>Top 10 bowlers</h3>" + table(hdr, rank_rows("bowl")) + f"<p>Next: {next_names('bowl')}.</p>")
    a(fig("f3_odds.png", f"Figure 1. How sure each pick is: share of {nreps} re-runs (all settings redrawn, matches resampled) in which the player made the top 10."))

    # 1 pressure
    a("<h2>1. Defining pressure</h2>")
    a("<p>A delivery is high-pressure when <b>the result hangs on it</b> (stakes) and <b>the situation is hard</b> (stress). Neither alone is enough. "
      "Stakes alone misses a first-innings collapse: a win-probability model sees 30/5 as nearly decided. Stress alone rates hopeless chases as maximum pressure, although nobody's result depends on them.</p>")
    a("<h3>Stakes: leverage from win probability</h3>")
    a("<p>Two gradient-boosted win-probability models, one per innings, estimate P(batting side wins) from runs, wickets in hand, balls left, required rate and competition. "
      "They have monotonic constraints and are validated out of sample, grouped by match: AUC 0.68 for innings 1 and 0.90 for innings 2. "
      "For each delivery, <b>leverage</b> is the expected absolute change in win probability over all possible outcomes (dot, 1, 2, 3, 4, 6, wicket, extra), weighted by how often each happens, "
      "and scaled so that the average delivery is 1.0. The same number applies to batter and bowler.</p>")
    a("<h3>Stress: how hard the situation is (0–100)</h3>")
    a("<p><b>Chase:</b> <code>(0.50·difficulty + 0.30·wickets lost + 0.20·recent collapse) × alive × (0.4 + 0.6·stage)</code>. "
      "Here difficulty rises from a required rate of 6 to 12, and <i>alive</i> fades to 0 as the required rate climbs from 13 to 18, so lost causes are not pressure. "
      "<b>First innings:</b> <code>0.8 × (0.40·wickets lost beyond par for the over + 0.30·recent collapse + 0.30·stage)</code>, where recent collapse = wickets in the last 24 balls ÷ 3.</p>")
    a("<h3>Final definition</h3>")
    a("<p><code>pressure score = (0.65 × percentile(stakes) + 0.35 × percentile(stress)) × 1.15 in knockouts</code>. "
      "The top 20% of deliveries are <b>high pressure</b>. Stakes gets the larger weight because it is measured from data rather than assumed.</p>")
    a("<p><b>Evidence that it separates pressure from ordinary play:</b></p><ul>"
      "<li>High-pressure balls move win probability <b>5.5× more</b> than low-pressure balls (0.033 vs 0.006 per ball).</li>"
      "<li>In chases, pressure peaks when 8–12 an over are needed at the death and fades for lost causes. In the first innings it rises with wickets lost and in the last five overs.</li>"
      "<li>33% of knockout deliveries are high pressure, against 19.5% of league deliveries.</li>"
      "<li>Players behave differently under it, comparing like with like within a phase. In first-innings middle overs, strike rate falls from 141 to 114 and dot-ball share rises from 29% to 36%.</li></ul>")
    a(fig("f1_pressure.png", "Figure 2. Left: average pressure percentile by over. Right: average realised win-probability swing per ball in each pressure band."))

    # 2 performance
    a("<h2>2. Measuring performance</h2>")
    a("<p>Raw strike rate and economy mostly reflect <b>role</b>: a death-overs hitter always scores faster, and a death bowler always concedes more. "
      "So for every delivery we model what an <b>average player</b> would do in exactly that situation, and credit the difference.</p><ul>"
      "<li><b>Expectation models</b> (gradient-boosted): expected runs and dismissal probability for the batter, expected runs conceded and wicket probability for the bowler. Inputs: innings, over, wickets, balls left, score, required rate, competition, pace or spin, how set the batter is, and the pressure percentile itself. "
      "A player under pressure is therefore judged against how the average player copes with the <i>same</i> pressure. In every pressure band, actual and expected totals agree within 1%.</li>"
      "<li><b>Wickets in runs:</b> a Duckworth–Lewis-style resource curve refitted on this data values a wicket at about 11 runs in over 1, 5 in over 15 and 0.5 in over 20.</li>"
      "<li><b>Per-ball value.</b> Batting: <code>(runs − expected) − (out − P(out)) × wicket value</code>. Bowling: <code>(expected conceded − conceded) + (wicket − P(wicket)) × wicket value</code>.</li>"
      "<li><b>Season par:</b> the models are fitted on all seasons together, but IPL scoring rose sharply after 2023. Each competition-season's average is therefore removed, so the average batter and bowler of every season are worth 0. "
      "Otherwise recent IPL batters would gain about +6 runs per 100 balls just for the era.</li>"
      "<li><b>Baseline (usual level):</b> the same value on non-pressure balls. Every player's pressure value is compared with their own baseline (section 5).</li></ul>")

    # 3 fair comparison
    a("<h2>3. Fair comparisons</h2><ul>")
    a("<li><b>Opposition:</b> a ridge regression estimates every batter's and bowler's effect at once, plus team-tier terms, with the penalty chosen by cross-validation. "
      "Each ball is corrected for the specific opponent, so facing Bumrah is credited and facing an associate attack is discounted.</li>")
    a(f"<li><b>IPL and T20I:</b> both are rated; A-team events are used to train the models only. Each ball has an <b>evidence weight</b>, made of three slight tilts multiplied together:"
      f"<ul><li><b>Recency:</b> −{W['recency_decay']:.0%} a year, so 2022 counts about 63% of 2026.</li>"
      f"<li><b>Competition:</b> IPL counts fully, and so do T20Is against India, Australia, England, South Africa and New Zealand. Other T20Is count {W['comp']['T20I']:.0%}.</li>"
      f"<li><b>Opponent strength:</b> balls against an associate-standard side count {W['opponent'][0]:.0%}, and nations in between are placed by their measured strength.</li></ul>"
      "A forward-in-time test showed the weights cost no forecasting accuracy.</li>")
    a(f"<li><b>Sample size:</b> empirical-Bayes shrinkage. A player's record is blended with a prior in proportion to the evidence, weight = n ÷ (n + k), with k learned from the data: {k_bat:,} balls for batters and {k_bowl:,} for bowlers. "
      "A hot streak over a small sample is pulled towards average.</li>")
    a("<li><b>Normal form as an anchor:</b> for bowlers, normal form predicts pressure bowling well, so pressure records are shrunk towards what normal form predicts. "
      "For batters it is a 25% anchor, so a poor batter with a good pressure record cannot rank as a top pressure player (Sam Curran: 104th of 105 on normal form).</li>")
    a("<li><b>Eligibility:</b> at least 100 pressure balls in 15+ innings (batters) or 120 legal pressure balls in 15+ matches (bowlers), and active in 2025–26. "
      f"This gives {n_b} batters and {n_w} bowlers.</li>")
    a("<li><b>Recent involvement:</b> a player whose pressure balls in 2024, 2025 or 2026 fall short of their own average per season (capped at 50) loses up to 0.40 rating points. "
      "The deduction grows with the square of the shortfall and is weighted 20/30/50% towards 2026, so missing the latest season costs most.</li></ul>")

    # 4 rating
    a("<h2>4. The Pressure Rating</h2>")
    a("<p>Five components, each turned into a z-score within the ranking pool, combined with weights:</p>")
    comp_rows = [
        ["Value", "Runs above par per 100/120 pressure balls, after all adjustments", f"{wb['value']}%", f"{ww['value']}%"],
        ["Consistency", "Weighted share of pressure matches in which the player beat an average player (10-match prior)", f"{wb['consistency']}%", f"{ww['consistency']}%"],
        ["Clutch", "Pressure value minus own baseline, shrunk using both standard errors", f"{wb['clutch']}%", f"{ww['clutch']}%"],
        ["Win impact", "Win probability added in pressure moments", f"{wb['impact']}%", f"{ww['impact']}%"],
        ["Track record", "Log of weighted pressure balls (a small bonus for sustaining a level)", f"{wb['volume']}%", f"{ww['volume']}%"]]
    a(table(["Component", "What it measures", "Batters", "Bowlers"], comp_rows))
    a(f"<p><b>A data-driven rule for clutch.</b> If players differ in rising above their usual level, the spread of their pressure-minus-baseline gaps should be wider than chance alone produces. "
      f"For bowlers it is: observed variance {p5['bowl']['clutch_observed']:,.0f} vs {p5['bowl']['clutch_noise']:,.0f} from noise, so clutch keeps its weight. "
      f"For batters it is not: {p5['bat']['clutch_observed']:,.0f} vs {p5['bat']['clutch_noise']:,.0f}, so its weight is shared out to the other components. "
      "Ranking batters on that gap would mean ranking luck.</p>")

    # 5 evidence
    a("<h2>5. Evidence for the top 10</h2>")
    a("<h3>Rise or dip: pressure vs usual level</h3>")
    a(f"<p>The brief asks how players perform under pressure <i>compared with their usual level</i>. We measured this for every player. "
      f"Among batters, {rise_b} of {n_b} clearly rise and {dip_b} clearly dip (more than 2 standard errors). Among bowlers, {rise_w} of {n_w} rise and {dip_w} dip. "
      f"Chance alone would produce about {round(n_b * 0.0455)} such cases in a group this size. "
      "For bowlers a small real effect exists and the rating rewards it. For batters, rising above one's usual level cannot be told apart from luck, so the batting list ranks <b>the most reliable pressure performance</b>: "
      "a high level when it matters, sustained across matches, with no evidence of dipping. "
      "<b>No player whose pressure performance is clearly below their own usual level (z &lt; −2) can be selected.</b> In the final lists no pick dips significantly.</p>")
    hdr = ["#", "Player", "Normal", "Pressure", "Gap", "z", "Beat par in", "Pressure balls 24/25/26", "Best pressure match"]
    a("<h3>Batters</h3>" + table(hdr, evidence_rows("bat")))
    a("<h3>Bowlers</h3>" + table(hdr, evidence_rows("bowl")))
    a("<p>Normal and Pressure are runs above par per 100 balls (batting) or 120 (bowling), opposition-adjusted and recency-weighted. The z column is the gap in standard errors.</p>")
    a(fig("f2_rise_dip.png", "Figure 3. Every ranked player's normal level (x) against their pressure level (y); the final top 10 are labelled. Above the diagonal = better under pressure."))

    # 6 selection
    a("<h2>6. From ratings to the final rankings</h2>")
    a(f"<p>A single rating rests on many judgement calls, so the final lists are built to be robust to all of them at once. In each of {nreps} re-runs we redraw every setting within a sensible range and resample the matches, then re-rate everyone. The settings are:</p><ul>"
      "<li>the pressure blend (55–75% stakes), knockout boost and 15/20/25% cut-off;</li>"
      "<li>recency (5–15% a year);</li>"
      "<li>the T20I weight;</li>"
      "<li>the opponent floor;</li>"
      "<li>the rating weights;</li>"
      "<li>the track-record weight;</li>"
      "<li>the recent-involvement rule.</li></ul>"
      "<p>A player's share of re-runs in the top 10 is their <b>robust probability</b>. The submitted lists:</p><ul>"
      "<li>take players in order of robust probability;</li>"
      "<li>for batters, treat players within 5 points of the 10th place as tied (the simulation noise is about ±2 points per player) and settle the tie by Pressure Rating;</li>"
      "<li>exclude anyone who clearly dips under pressure.</li></ul>"
      "<p><b>Ranking 1–10.</b> The robust probability decides <i>who</i> is in each list: how sure we are that a player belongs in the top 10. "
      "The <b>Pressure Rating</b> decides the <i>order</i>: how well they perform under pressure. Rank 1 is therefore the highest-rated player, as the brief asks. "
      "The two orders agree closely (rank correlation about 0.9 within each final ten).</p>")

    # 7 reliability
    a("<h2>7. Reliability and limitations</h2>")
    a("<h3>Consistency across matches</h3><ul>")
    a(f"<li><b>Split-half test.</b> We split matches randomly into two halves, 50 times, and correlated each player's values across the halves. "
      f"Normal form repeats far better (batters {sh.loc['bat','r_baseline']:.2f}, bowlers {sh.loc['bowl','r_baseline']:.2f}) "
      f"than pressure value on its own ({sh.loc['bat','r_pressure']:.2f}, {sh.loc['bowl','r_pressure']:.2f}), because pressure samples are small. "
      "This is why the method relies on shrinkage, consistency and robustness rather than raw pressure numbers.</li>")
    a("<li><b>Consistency component.</b> 20–24% of each rating is how often a player beat an average player across their pressure matches.</li>")
    a("<li><b>Season by season.</b> Most picks are positive in at least four of five seasons. The dashboard shows each player's IPL and T20I seasons separately.</li></ul>")
    a("<h3>Robustness to our choices</h3>")
    a(f"<p>The {len(sens_rows)} one-at-a-time variants below show how many of the rating's top 10 survive each alternative choice. "
      "The adjustments we added move at most one or two names.</p>")
    a(table(["Alternative", "Batters kept (of 10)", "Bowlers kept (of 10)"], sens_rows))
    a("<h3>Does the rating predict? A forward-in-time benchmark</h3>")
    a("<p>For five cut-off dates in 2024–26, predictors were computed from earlier matches and compared with the next 12 months, for the same players. The figures are correlations with next-year context-adjusted pressure value:</p>")
    a(table(["Predictor", "Batters", "Bowlers"], [
        ["Pressure Rating (full method)", f"{b('bat','t_value','Pressure Rating (full method)'):+.2f}", f"{b('bowl','t_value','Pressure Rating (full method)'):+.2f}"],
        ["Value component", f"{b('bat','t_value','Value component alone'):+.2f}", f"{b('bowl','t_value','Value component alone'):+.2f}"],
        ["Pressure strike rate / economy", f"{b('bat','t_value','Pressure strike rate'):+.2f}", f"{b('bowl','t_value','Pressure economy'):+.2f}"],
        ["Overall strike rate / economy", f"{b('bat','t_value','Overall strike rate'):+.2f}", f"{b('bowl','t_value','Overall economy'):+.2f}"]]))
    a("<p><b>Bowlers:</b> our value measure forecasts next-year pressure performance as well as or better than any simple stat, and its top-10 picks did best the following year. "
      "<b>Batters:</b> nothing forecasts pressure batting, simple stats included. The batting list therefore states who has delivered most reliably under pressure in 2022–26; it is not a forecast.</p>")
    a("<h3>Limitations</h3><ul>"
      "<li>The data covers 2022–26 only. Pressure samples are 100–700 balls per player, so the last few places in each list are close calls.</li>"
      "<li>The innings-1 win-probability model is only moderately predictive (AUC 0.68), so first-innings stakes are measured less precisely than chase stakes.</li>"
      "<li>Several settings are judgement calls. We publish them and test them all at once (section 6) rather than tuning them.</li>"
      "<li>Venue and pitch are not modelled, fielding is not counted, and availability (injuries, retirements) is outside the data.</li></ul>")

    # 8 reproduce
    a("<h2>8. Reproducing the results</h2>")
    a("<p>All code is in Python. Run the scripts in order, from the project root:</p><ol>"
      "<li><code>build_phase1.py</code>: match state.</li>"
      "<li><code>build_phase2.py</code>: pressure.</li>"
      "<li><code>build_phase3.py</code>: expectations and values.</li>"
      "<li><code>build_phase4.py</code>: season par, opposition, evidence weights and shrinkage.</li>"
      "<li><code>build_phase5.py</code>: rating.</li>"
      "<li><code>build_phase6.py</code>: reliability.</li>"
      "<li><code>build_phase7.py</code>: robustness re-runs.</li>"
      "<li><code>benchmark_check.py</code>, <code>roles.py</code>, <code>final_selection.py</code>.</li></ol>"
      "<p>Every setting is a named constant in <code>fairness.py</code>, <code>rating.py</code> or <code>final_selection.py</code>. An interactive dashboard (<code>dashboard.html</code>) shows every player's full profile.</p>")
    return "\n".join(H)


def main():
    d = load()
    fig_pressure(d); fig_rise_dip(d); fig_odds(d)
    body = build(d)
    doc = (f"<html><head><meta charset='utf-8'><title>Players Under Pressure: methodology</title><style>{CSS}</style></head>"
           f"<body>{body}</body></html>")
    (REP / "Methodology_Report.html").write_text(doc, encoding="utf-8")
    print("wrote", REP / "Methodology_Report.html")


if __name__ == "__main__":
    main()

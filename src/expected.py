"""Context-adjusted expectations: what an *average* player does in exactly this situation.

Every delivery gets:
  exp_bat_runs, p_striker_out    - average batter facing this ball in this context
  exp_bowler_runs, p_bowler_wkt  - average bowler bowling this ball in this context
  wicket_value                   - runs a wicket costs at this point (DLS-style resources)

Context = innings, over, wickets down, balls left, required rate, score, format, pace/spin,
how set the batter is, and the pressure percentile itself. Because pressure is part of the
context, a player's value under pressure is measured against how average players perform
under the *same* pressure, and their baseline against average players in ordinary situations.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

CTX = ["innings", "overid", "wkts_before", "balls_left", "rrr_f", "runs_before", "is_ipl", "is_emerging",
       "is_spin", "batter_set", "pressure_pct"]


def add_context(b: pd.DataFrame) -> pd.DataFrame:
    b["is_spin"] = b["pace_or_spin"].eq("Spin").astype(float)
    b["batter_set"] = b["batter_balls_before"].clip(upper=40)
    b["rrr_f"] = b["rrr"].clip(upper=36)  # NaN in innings 1 (trees handle missing values)
    b["is_ipl"] = b["is_ipl"].astype(float)
    b["is_emerging"] = b["is_emerging"].astype(float)
    return b


def _reg(**kw):
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=300,
                                         l2_regularization=1.0, random_state=42, **kw)


def _clf(**kw):
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, min_samples_leaf=300,
                                          l2_regularization=1.0, random_state=42, **kw)


def resource_table(b: pd.DataFrame) -> dict[int, np.ndarray]:
    """DLS-style resource curves refitted on this data.

    Duckworth-Lewis "standard edition" form: expected remaining runs with u balls left and
    w wickets in hand is R_w(u) = Z_w * (1 - exp(-k * u / Z_w)), where k (runs per ball with
    no wicket constraint) is shared by all w and Z_w is the run ceiling with w wickets left.
    Fitted jointly per format on complete first innings (no DLS / no result). Z_w is made
    non-decreasing in w, so the curves nest and a wicket never has negative value.
    Returns {is_ipl: array[11, 121]} with R[w, u]; R[0, :] = 0.
    """
    from scipy.optimize import curve_fit

    d = b[b["innings"].eq(1) & b["balls_avail"].eq(120) & ~b["is_dls"] & ~b["no_result"]].copy()
    d["rem"] = d["inn_runs"] - d["runs_before"]
    u = np.arange(121)

    def f(X, k, *Z):
        w, uu = X
        z = np.asarray(Z)[w.astype(int) - 1]
        return z * (1 - np.exp(-k * uu / z))

    tables = {}
    for ipl in (0.0, 1.0):
        cell = (d[d["is_ipl"].eq(ipl)].groupby(["wkts_in_hand", "balls_left"])["rem"]
                .agg(["mean", "size"]).reset_index())
        cell = cell[cell["size"] >= 3]
        X = (cell["wkts_in_hand"].values, cell["balls_left"].values)
        p0 = [1.4] + list(np.linspace(10, 250, 10))
        params, _ = curve_fit(f, X, cell["mean"].values, p0=p0, sigma=1 / np.sqrt(cell["size"].values),
                              bounds=([0.1] + [1] * 10, [5] + [800] * 10), maxfev=50000)
        k, Z = params[0], np.maximum.accumulate(params[1:])
        R = np.zeros((11, 121))
        for w in range(1, 11):
            R[w] = Z[w - 1] * (1 - np.exp(-k * u / Z[w - 1]))
        tables[ipl] = R
    return tables


def wicket_value(b: pd.DataFrame) -> pd.Series:
    """Runs a wicket costs = R(w, u) - R(w-1, u), with u = balls left after this ball.

    In a chase it is capped at the runs still needed (a wicket can't cost more than the runs
    that remain to be scored).
    """
    tables = resource_table(b)
    u = (b["balls_left"] - 1).clip(0, 120).astype(int).values
    w = b["wkts_in_hand"].clip(1, 10).astype(int).values
    wv = np.zeros(len(b))
    for ipl, R in tables.items():
        m = b["is_ipl"].eq(ipl).values
        wv[m] = R[w[m], u[m]] - R[w[m] - 1, u[m]]
    wv = pd.Series(wv, index=b.index)
    return wv.where(~b["innings"].eq(2), np.minimum(wv, b["runs_needed"].clip(lower=0)))


def add_expectations(b: pd.DataFrame) -> pd.DataFrame:
    b = add_context(b)
    b["wicket_value"] = wicket_value(b)

    bat = b["is_batter_ball"]
    X = b[CTX]
    b["exp_bat_runs"] = np.nan
    b["p_striker_out"] = np.nan
    b.loc[bat, "exp_bat_runs"] = _reg(loss="poisson").fit(X[bat], b.loc[bat, "bat_runs"]).predict(X[bat])
    b.loc[bat, "p_striker_out"] = _clf().fit(X[bat], b.loc[bat, "striker_out"].astype(int)).predict_proba(X[bat])[:, 1]

    b["exp_bowler_runs"] = _reg(loss="poisson").fit(X, b["bowler_runs"]).predict(X)
    b["p_bowler_wkt"] = _clf().fit(X, b["bowler_wicket"].astype(int)).predict_proba(X)[:, 1]

    # Value in runs (positive = good for that player)
    b["bat_value"] = (b["bat_runs"] - b["exp_bat_runs"]) - (b["striker_out"] - b["p_striker_out"]) * b["wicket_value"]
    b["bowl_value"] = (b["exp_bowler_runs"] - b["bowler_runs"]) + (b["bowler_wicket"] - b["p_bowler_wkt"]) * b["wicket_value"]
    return b

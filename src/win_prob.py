"""Win-probability (WP) models: P(batting side wins | match state), one per innings.

Gradient-boosted trees with monotonic constraints, so the model can never say that losing a
wicket or needing more runs *helps* the batting side. Features are deliberately limited to
the game state so the model can be re-evaluated on hypothetical states (e.g. "what if this
ball were a wicket?"), which is how leverage is computed in pressure.py.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

# No run-rate feature in innings 1: early in an innings it jumps wildly (one boundary off
# ball 1 = 24 rpo), which produced spurious powerplay "pressure". Runs x balls_left carries it.
INN1_FEATS = ["runs", "wkts_in_hand", "balls_left", "is_ipl"]
INN1_MONO = [1, 1, 1, 0]
INN2_FEATS = ["runs_needed", "balls_left", "wkts_in_hand", "rrr", "is_ipl"]
INN2_MONO = [-1, 1, 1, -1, 0]


def features(innings: int, runs, wkts_in_hand, balls_left, balls_avail, target, is_ipl) -> pd.DataFrame:
    """Feature frame from raw state arrays (works for real or hypothetical states)."""
    runs = np.asarray(runs, float)
    balls_left = np.clip(np.asarray(balls_left, float), 0, None)
    legal = np.clip(np.asarray(balls_avail, float) - balls_left, 1, None)
    if innings == 1:
        return pd.DataFrame({
            "runs": runs, "wkts_in_hand": wkts_in_hand, "balls_left": balls_left,
            "run_rate": runs * 6 / legal, "is_ipl": np.asarray(is_ipl, float),
        })
    need = np.asarray(target, float) - runs
    return pd.DataFrame({
        "runs_needed": need, "balls_left": balls_left, "wkts_in_hand": wkts_in_hand,
        "rrr": need * 6 / np.clip(balls_left, 1, None), "is_ipl": np.asarray(is_ipl, float),
    })


def _model(mono):
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=200,
        l2_regularization=1.0, monotonic_cst=mono, random_state=42,
    )


def state_frame(b: pd.DataFrame, innings: int) -> pd.DataFrame:
    d = b[b["innings"].eq(innings)]
    return features(innings, d["runs_before"], d["wkts_in_hand"], d["balls_left"],
                    d["balls_avail"], d["target"], d["is_ipl"])


class WinProb:
    def __init__(self):
        self.models = {}
        self.metrics = {}

    @staticmethod
    def training_rows(b: pd.DataFrame) -> pd.Series:
        """Clean, decisive, full-length matches only (no ties, no-results or DLS)."""
        return b["batting_team_won"].isin([0.0, 1.0]) & ~b["is_dls"] & b["balls_avail"].eq(120)

    def fit(self, b: pd.DataFrame, n_splits: int = 5) -> "WinProb":
        ok = self.training_rows(b)
        for inn, feats, mono in [(1, INN1_FEATS, INN1_MONO), (2, INN2_FEATS, INN2_MONO)]:
            d = b[ok & b["innings"].eq(inn)]
            X, y, groups = state_frame(d, inn)[feats], d["batting_team_won"].astype(int), d["match_id"]
            # Out-of-fold predictions, grouped by match, give an honest accuracy estimate.
            oof = np.zeros(len(d))
            for tr, te in GroupKFold(n_splits).split(X, y, groups):
                oof[te] = _model(mono).fit(X.iloc[tr], y.iloc[tr]).predict_proba(X.iloc[te])[:, 1]
            self.metrics[inn] = {
                "rows": len(d), "matches": d["match_id"].nunique(),
                "log_loss": log_loss(y, oof), "brier": brier_score_loss(y, oof), "auc": roc_auc_score(y, oof),
                "base_rate": y.mean(),
                "calibration": pd.DataFrame({"pred": oof, "y": y.values})
                .assign(bin=lambda t: pd.cut(t["pred"], np.linspace(0, 1, 11), include_lowest=True))
                .groupby("bin", observed=True).agg(n=("y", "size"), mean_pred=("pred", "mean"), actual=("y", "mean")),
            }
            self.models[inn] = _model(mono).fit(X, y)
        return self

    def predict(self, innings: int, runs, wkts_in_hand, balls_left, balls_avail, target, is_ipl) -> np.ndarray:
        """WP for the batting side; handles terminal chase states exactly."""
        feats = INN1_FEATS if innings == 1 else INN2_FEATS
        X = features(innings, runs, wkts_in_hand, balls_left, balls_avail, target, is_ipl)
        p = self.models[innings].predict_proba(X[feats])[:, 1]
        if innings == 2:
            need = np.asarray(target, float) - np.asarray(runs, float)
            wk = np.asarray(wkts_in_hand)
            bl = np.asarray(balls_left)
            p = np.where(need <= 0, 1.0, p)
            out = (need > 0) & ((wk <= 0) | (bl <= 0))
            p = np.where(out, np.where(need == 1, 0.5, 0.0), p)  # one short at the end = tie
        return p

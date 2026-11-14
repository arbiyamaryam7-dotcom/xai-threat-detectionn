"""Anomaly detectors trained on BENIGN traffic only.

- IsolationForestDetector: sklearn Isolation Forest.
- AutoencoderDetector: a bottleneck neural autoencoder (sklearn MLPRegressor trained
  to reconstruct its input); anomaly score = reconstruction error.
Scores are mapped to 0-100 where 50 equals the 95th percentile of benign training error.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer, StandardScaler
from config import RANDOM_STATE


def _to_score(raw, threshold):
    r = np.asarray(raw) / max(threshold, 1e-12)
    return 100.0 * r / (1.0 + r)


class _Base:
    def fit(self, X_benign):
        self.prep = make_pipeline(QuantileTransformer(output_distribution="normal", n_quantiles=500,
                                                      random_state=RANDOM_STATE), StandardScaler())
        Z = self.prep.fit_transform(X_benign)
        self._fit(Z)
        self.threshold = float(np.percentile(self._raw(Z), 95))
        return self

    def raw_scores(self, X):
        return self._raw(self.prep.transform(X))

    def score(self, X):
        """Anomaly score in [0, 100]; >50 means more anomalous than 95% of benign training data."""
        return _to_score(self.raw_scores(X), self.threshold)


class IsolationForestDetector(_Base):
    def _fit(self, Z):
        self.m = IsolationForest(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1).fit(Z)
    def _raw(self, Z):
        return -self.m.score_samples(Z) + 1.0  # shift to positive


class AutoencoderDetector(_Base):
    def _fit(self, Z):
        d = Z.shape[1]
        self.m = MLPRegressor(hidden_layer_sizes=(max(d // 2, 8), max(d // 4, 4), max(d // 2, 8)),
                              activation="relu", max_iter=60, early_stopping=True,
                              random_state=RANDOM_STATE).fit(Z, Z)
    def _raw(self, Z):
        return np.mean((self.m.predict(Z) - Z) ** 2, axis=1)

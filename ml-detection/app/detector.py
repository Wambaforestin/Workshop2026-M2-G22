"""
Détection d'anomalies — Resilience-Alpha.

Le sujet (§3.3) interdit de réduire la détection à « quelques conditions codées
en dur ». On utilise donc un vrai modèle de machine learning non supervisé —
un **détecteur de nouveauté par covariance robuste** (`EllipticEnvelope` de
scikit-learn) — entraîné sur un comportement NORMAL de la plateforme, puis
appliqué en continu aux métriques issues de Prometheus.

Idée (analogie) : on apprend la « forme » du nuage de points d'une journée
normale (débit, taux d'erreur, latence, requêtes en cours) — sa position et sa
dispersion dans toutes les directions à la fois (la covariance). Le modèle trace
une enveloppe autour de cette zone normale. Toute mesure qui tombe nettement en
dehors (distance de Mahalanobis élevée) est signalée. Le SEUIL n'est pas écrit à
la main : il est calibré par le modèle sur les données normales (ici ~0,5 % de
faux positifs tolérés). On ne code donc aucune règle « si latence > X ».

Features utilisées (vecteur par instant) :
  - req_rate      : requêtes/s
  - error_ratio   : part de réponses 5xx
  - latency_p95   : latence 95e percentile (s)
  - inflight      : requêtes en cours
"""
from __future__ import annotations

import numpy as np
from sklearn.covariance import EllipticEnvelope

FEATURES = ["req_rate", "error_ratio", "latency_p95", "inflight"]


def synthetic_normal(n: int = 2000, seed: int = 42) -> np.ndarray:
    """Génère un jeu de données de comportement NORMAL (observations).

    Faute d'historique de production (plateforme neuve), on constitue les
    observations décrivant le régime normal, comme le permet le sujet
    (« constituer les observations nécessaires »). En conditions réelles, on
    remplacerait ceci par un export Prometheus d'une période saine.
    """
    rng = np.random.default_rng(seed)
    req_rate = rng.normal(8, 2, n).clip(0.5, 20)          # trafic modéré
    error_ratio = rng.beta(1.2, 60, n)                     # ~0-5% d'erreurs
    latency = rng.normal(0.08, 0.03, n).clip(0.01, 0.4)    # ~80ms
    inflight = rng.normal(3, 1.5, n).clip(0, 15)
    return np.column_stack([req_rate, error_ratio, latency, inflight])


class AnomalyModel:
    """Détecteur de nouveauté (covariance robuste) + explicabilité par feature."""

    def __init__(self) -> None:
        # contamination : part d'anomalies tolérée dans le régime normal -> sert
        # à CALIBRER le seuil de décision à partir des données, pas à la main.
        self.model = EllipticEnvelope(
            contamination=0.005, support_fraction=0.9, random_state=42
        )
        self._mean = None
        self._std = None
        self.trained = False

    def fit(self, X: np.ndarray) -> None:
        # Standardisation (centre-réduit) : met les 4 features à la même échelle.
        self._mean = X.mean(axis=0)
        self._std = X.std(axis=0) + 1e-9
        Xs = (X - self._mean) / self._std
        self.model.fit(Xs)
        self.trained = True

    def score(self, x: dict) -> dict:
        """Évalue un vecteur de métriques. Retourne un verdict explicable."""
        vec = np.array([[x.get(f, 0.0) for f in FEATURES]], dtype=float)
        xs = (vec - self._mean) / self._std
        is_anom = bool(self.model.predict(xs)[0] == -1)
        # Distance de Mahalanobis : « à quel point » le point est hors-normale.
        maha = float(self.model.mahalanobis(xs)[0])
        # Contributions : quelle feature s'écarte le plus de la normale (|z|).
        z = np.abs(xs[0])
        contributions = {f: round(float(z[i]), 2) for i, f in enumerate(FEATURES)}
        top = max(contributions, key=contributions.get)
        return {
            "anomaly": is_anom,
            "score": round(maha, 2),  # distance de Mahalanobis (plus haut = pire)
            "drivers": contributions,
            "main_driver": top,
            "explanation": _explain(top, is_anom),
        }


def _explain(driver: str, is_anom: bool) -> str:
    if not is_anom:
        return "Comportement conforme au régime normal appris."
    msg = {
        "req_rate": "Débit de requêtes anormalement élevé — possible déni de service.",
        "error_ratio": "Taux d'erreurs anormal — possible injection ou panne applicative.",
        "latency_p95": "Latence anormale — saturation ou contention de la base.",
        "inflight": "Accumulation de requêtes en cours — service en difficulté.",
    }
    return msg.get(driver, "Écart significatif par rapport au comportement appris.")

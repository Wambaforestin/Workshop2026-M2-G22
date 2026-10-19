"""Tests de la détection d'anomalies ML."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ml-detection"))

from app.detector import AnomalyModel, synthetic_normal  # noqa: E402


def _trained():
    m = AnomalyModel()
    m.fit(synthetic_normal())
    return m


def test_model_trains():
    assert _trained().trained is True


def test_normal_point_is_normal():
    m = _trained()
    v = m.score({"req_rate": 8, "error_ratio": 0.01, "latency_p95": 0.08, "inflight": 3})
    assert v["anomaly"] is False


def test_dos_point_is_anomaly_with_right_driver():
    m = _trained()
    # Débit massivement anormal -> anomalie, driver req_rate.
    v = m.score({"req_rate": 500, "error_ratio": 0.01, "latency_p95": 0.08, "inflight": 3})
    assert v["anomaly"] is True
    assert v["main_driver"] == "req_rate"


def test_latency_spike_detected():
    m = _trained()
    v = m.score({"req_rate": 8, "error_ratio": 0.01, "latency_p95": 5.0, "inflight": 3})
    assert v["anomaly"] is True
    assert v["main_driver"] == "latency_p95"

"""
Service de détection ML — Resilience-Alpha.

Boucle de surveillance : interroge Prometheus toutes les N secondes, construit
le vecteur de features, le soumet au modèle, et — si une anomalie est détectée —
notifie le moteur de remédiation. Expose aussi son état au dashboard et à
Prometheus (méta-métriques).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from starlette.responses import Response

from .detector import AnomalyModel, synthetic_normal

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s",'
    '"service":"ml-detection","msg":"%(message)s"}',
)
log = logging.getLogger("ml-detection")

PROM_URL = os.getenv("PROM_URL", "http://prometheus:9090")
REMEDIATION_URL = os.getenv("REMEDIATION_URL", "http://remediation:8300")
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "3"))

ANOMALIES = Counter("ml_anomalies_total", "Anomalies détectées", ["driver"])
LAST_SCORE = Gauge("ml_last_score", "Distance de Mahalanobis du dernier point (plus haut = pire)")
ANOM_STATE = Gauge("ml_anomaly_state", "1 si anomalie en cours, 0 sinon")

model = AnomalyModel()
STATE: dict = {"last": None, "history": []}


# Requêtes PromQL correspondant aux 4 features du modèle.
QUERIES = {
    "req_rate": "sum(rate(payment_requests_total[30s]))",
    "error_ratio": (
        'sum(rate(payment_requests_total{status=~"5.."}[30s])) '
        "/ clamp_min(sum(rate(payment_requests_total[30s])),1)"
    ),
    "latency_p95": (
        "histogram_quantile(0.95, sum(rate("
        "payment_request_latency_seconds_bucket[30s])) by (le))"
    ),
    "inflight": "sum(payment_inflight_requests)",
}


async def query_prom(client: httpx.AsyncClient, expr: str) -> float:
    try:
        r = await client.get(f"{PROM_URL}/api/v1/query", params={"query": expr})
        data = r.json()["data"]["result"]
        if not data:
            return 0.0
        val = float(data[0]["value"][1])
        return 0.0 if val != val else val  # NaN -> 0
    except Exception:  # noqa: BLE001
        return 0.0


async def surveillance_loop():
    await asyncio.sleep(5)  # laisse la plateforme démarrer
    async with httpx.AsyncClient(timeout=3.0) as client:
        while True:
            features = {}
            for name, expr in QUERIES.items():
                features[name] = await query_prom(client, expr)
            verdict = model.score(features)
            verdict["features"] = features
            verdict["ts"] = time.time()
            STATE["last"] = verdict
            STATE["history"] = (STATE["history"] + [verdict])[-120:]
            LAST_SCORE.set(verdict["score"])
            ANOM_STATE.set(1 if verdict["anomaly"] else 0)

            if verdict["anomaly"]:
                ANOMALIES.labels(driver=verdict["main_driver"]).inc()
                log.info(
                    f"ANOMALIE driver={verdict['main_driver']} "
                    f"score={verdict['score']} features={features}"
                )
                await notify_remediation(client, verdict)
            await asyncio.sleep(POLL_SECONDS)


async def notify_remediation(client: httpx.AsyncClient, verdict: dict):
    """Alimente la chaîne de remédiation (raccordement §3.3)."""
    try:
        await client.post(
            f"{REMEDIATION_URL}/incident",
            json={
                "source": "ml-detection",
                "driver": verdict["main_driver"],
                "score": verdict["score"],
                "explanation": verdict["explanation"],
                "features": verdict["features"],
            },
        )
    except httpx.HTTPError as exc:
        log.error(f"notification remédiation échouée: {exc}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("Entraînement du modèle sur le comportement normal…")
    model.fit(synthetic_normal())
    log.info("Modèle entraîné (covariance robuste). Démarrage de la surveillance.")
    task = asyncio.create_task(surveillance_loop())
    yield
    task.cancel()


app = FastAPI(title="Resilience-Alpha — ML Detection", lifespan=lifespan)


@app.get("/health")
def health():
    return {"service": "ml-detection", "status": "ok", "trained": model.trained}


@app.get("/state")
def state():
    """Dernier verdict + historique court, pour le dashboard."""
    return STATE


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

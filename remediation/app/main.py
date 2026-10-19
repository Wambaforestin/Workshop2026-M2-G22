"""
Moteur de remédiation autonome — Resilience-Alpha.

Reçoit les incidents (de la détection ML), décide d'une action corrective selon
une POLITIQUE explicite, l'exécute sur les conteneurs via le socket Docker, puis
VÉRIFIE que le service métier est réellement rétabli (santé profonde +
transaction fictive). Boucle fermée : détection -> décision -> action ->
vérification -> clôture.

Point sensible assumé (§3.4) : ce service a des droits élevés (socket Docker).
Il n'expose donc AUCUN shell distant générique — seulement une liste fermée
d'actions prédéfinies, toutes journalisées. Il n'est pas pilotable par le RAG.
"""
from __future__ import annotations

import logging
import os
import time
from collections import deque

import httpx
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel
from starlette.responses import Response

from .actions import DockerOps

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s",'
    '"service":"remediation","msg":"%(message)s"}',
)
log = logging.getLogger("remediation")

API_HEALTH = os.getenv("API_HEALTH_URL", "http://payment-api:8000/health/deep")
AUTH_URL = os.getenv("AUTH_URL", "http://auth:8100")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://payment-api:8000")
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "3"))

ACTIONS = Counter("remediation_actions_total", "Actions de remédiation", ["action"])
RECOVERIES = Counter("remediation_recoveries_total", "Reprises réussies")
STATE_G = Gauge("remediation_incident_active", "1 si incident en cours")

ops = DockerOps()
EVENTS: deque = deque(maxlen=200)
CURRENT: dict = {"active": False, "last_incident": None, "last_recovery": None}


# --- POLITIQUE de remédiation : driver d'anomalie -> plan d'action -------------
POLICY = {
    "latency_p95": ["restart_db", "restart_service:payment-api"],
    "req_rate": ["restart_service:payment-api"],
    "error_ratio": ["restart_service:payment-api", "flag_investigation"],
    "inflight": ["restart_service:payment-api"],
    "default": ["restart_service:payment-api"],
}


def log_event(kind: str, detail: dict):
    evt = {"ts": time.time(), "kind": kind, "detail": detail}
    EVENTS.appendleft(evt)
    log.info(f"{kind}: {detail}")


class Incident(BaseModel):
    source: str
    driver: str
    score: float | None = None
    explanation: str | None = None
    features: dict | None = None


app = FastAPI(title="Resilience-Alpha — Remediation")


@app.get("/health")
def health():
    return {"service": "remediation", "status": "ok", "docker": ops.available}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/events")
def events():
    return {"current": CURRENT, "events": list(EVENTS)}


@app.post("/incident")
def incident(inc: Incident):
    """Point d'entrée : un incident est signalé. Lance la boucle de reprise."""
    if CURRENT["active"]:
        log_event("incident_ignored", {"reason": "reprise déjà en cours"})
        return {"status": "busy"}

    CURRENT["active"] = True
    CURRENT["last_incident"] = inc.model_dump()
    STATE_G.set(1)
    log_event("incident", inc.model_dump())

    plan = POLICY.get(inc.driver, POLICY["default"])
    log_event("decision", {"driver": inc.driver, "plan": plan})

    recovered = False
    for attempt in range(1, MAX_ATTEMPTS + 1):
        for step in plan:
            _execute(step)
        if verify_recovery():
            recovered = True
            break
        log_event("verify_failed", {"attempt": attempt})
        time.sleep(2)

    STATE_G.set(0)
    CURRENT["active"] = False
    if recovered:
        RECOVERIES.inc()
        CURRENT["last_recovery"] = time.time()
        log_event("recovered", {"driver": inc.driver})
        return {"status": "recovered"}
    log_event("recovery_failed", {"driver": inc.driver})
    return {"status": "failed"}


def _execute(step: str):
    name, _, arg = step.partition(":")
    ACTIONS.labels(action=name).inc()
    if name == "restart_db":
        ops.restart("db")
        log_event("action", {"action": "restart_db"})
    elif name == "restart_service":
        ops.restart(arg)
        log_event("action", {"action": "restart_service", "target": arg})
    elif name == "isolate":
        ops.disconnect(arg)
        log_event("action", {"action": "isolate", "target": arg})
    elif name == "flag_investigation":
        # Ne confond pas reprise de disponibilité et traitement d'une
        # compromission : on ouvre un ticket d'investigation distinct (§2).
        log_event("investigation_flagged", {
            "note": "Erreurs anormales : investigation sécurité requise, "
                    "distincte de la restauration de disponibilité."
        })


def verify_recovery() -> bool:
    """Reprise RÉELLE : santé profonde + transaction fictive aboutie."""
    try:
        with httpx.Client(timeout=4.0) as client:
            h = client.get(API_HEALTH)
            if h.status_code != 200:
                return False
            tok = client.post(
                f"{AUTH_URL}/login",
                json={"username": "operator", "password": "operator-demo"},
            ).json()["access_token"]
            tx = client.post(
                f"{PAYMENT_URL}/transactions",
                headers={"Authorization": f"Bearer {tok}"},
                json={
                    "source": "acc-client-002",
                    "destination": "acc-merchant-001",
                    "amount": 1.00,
                },
            )
            ok = tx.status_code == 201
            log_event("verify", {"health": h.status_code, "tx": tx.status_code})
            return ok
    except Exception as exc:  # noqa: BLE001
        log_event("verify_error", {"error": str(exc)})
        return False

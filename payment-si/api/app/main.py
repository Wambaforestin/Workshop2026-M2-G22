"""
Project Resilience-Alpha — API métier de paiement (fictive).

Microservice FastAPI qui expose le cœur métier : création de comptes fictifs,
exécution de transactions simulées, consultation de soldes. Aucune donnée
bancaire réelle n'est utilisée — tout est fictif et confiné au laboratoire.

Expose aussi :
  - /metrics          : métriques Prometheus (compteurs, latences, erreurs)
  - /health           : sonde de vivacité utilisée par la remédiation
  - /health/deep      : sonde métier (vérifie la base ET une transaction test)
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from decimal import Decimal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from sqlalchemy import text
from starlette.responses import Response

from . import db, schemas

# --- Logs structurés (JSON) : exploitables par Promtail -> Loki ----------------
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s",'
    '"service":"payment-api","msg":"%(message)s"}',
)
log = logging.getLogger("payment-api")

AUTH_URL = os.getenv("AUTH_URL", "http://auth:8100")
SERVICE_NAME = "payment-api"

# --- Métriques Prometheus ------------------------------------------------------
REQS = Counter(
    "payment_requests_total",
    "Nombre total de requêtes HTTP",
    ["method", "endpoint", "status"],
)
LAT = Histogram(
    "payment_request_latency_seconds",
    "Latence des requêtes HTTP",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
TX_TOTAL = Counter(
    "payment_transactions_total",
    "Transactions traitées",
    ["result"],  # success | rejected | error
)
TX_AMOUNT = Histogram(
    "payment_transaction_amount_eur",
    "Montant des transactions (EUR fictifs)",
    buckets=(10, 50, 100, 500, 1000, 5000, 10000),
)
INFLIGHT = Gauge("payment_inflight_requests", "Requêtes en cours de traitement")
DB_UP = Gauge("payment_db_up", "1 si la base est joignable, 0 sinon")


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    log.info("API de paiement démarrée, schéma vérifié")
    yield
    log.info("Arrêt de l'API de paiement")


app = FastAPI(
    title="Resilience-Alpha — Payment API (fictive)",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observe(request: Request, call_next):
    endpoint = request.url.path
    INFLIGHT.inc()
    start = time.perf_counter()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:  # noqa: BLE001 — on compte aussi les 500
        status = 500
        raise
    finally:
        INFLIGHT.dec()
        elapsed = time.perf_counter() - start
        LAT.labels(endpoint=endpoint).observe(elapsed)
        REQS.labels(
            method=request.method, endpoint=endpoint, status=str(status)
        ).inc()
    return response


# --- Authentification : délègue au service auth (JWT) --------------------------
async def require_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Jeton manquant")
    token = authorization.split(" ", 1)[1]
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            r = await client.post(f"{AUTH_URL}/verify", json={"token": token})
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="Service auth indisponible")
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Jeton invalide")
    return r.json()


# --- Endpoints de santé --------------------------------------------------------
@app.get("/health")
def health():
    """Vivacité simple : le process répond."""
    return {"service": SERVICE_NAME, "status": "ok"}


@app.get("/health/deep")
def health_deep():
    """Santé métier : base joignable + lecture cohérente. Utilisée par la
    remédiation pour décider si le service est RÉELLEMENT rétabli."""
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            n = conn.execute(text("SELECT count(*) FROM accounts")).scalar()
        DB_UP.set(1)
        return {"service": SERVICE_NAME, "status": "ok", "accounts": n}
    except Exception as exc:  # noqa: BLE001
        DB_UP.set(0)
        log.error(f"health/deep KO: {exc}")
        raise HTTPException(status_code=503, detail="Base indisponible")


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# --- Cœur métier ---------------------------------------------------------------
@app.post("/accounts", response_model=schemas.Account, status_code=201)
def create_account(payload: schemas.AccountCreate):
    acc_id = str(uuid.uuid4())
    with db.engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO accounts (id, owner, balance) "
                "VALUES (:id, :owner, :balance)"
            ),
            {"id": acc_id, "owner": payload.owner, "balance": str(payload.balance)},
        )
    log.info(f"compte créé owner={payload.owner} id={acc_id}")
    return schemas.Account(id=acc_id, owner=payload.owner, balance=payload.balance)


@app.get("/accounts/{acc_id}", response_model=schemas.Account)
def get_account(acc_id: str):
    with db.engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, owner, balance FROM accounts WHERE id = :id"),
            {"id": acc_id},
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    return schemas.Account(id=row[0], owner=row[1], balance=Decimal(row[2]))


@app.post("/transactions", response_model=schemas.Transaction, status_code=201)
def create_transaction(
    payload: schemas.TransactionCreate, user: dict = Depends(require_user)
):
    """Débite un compte source et crédite un compte destination (atomique)."""
    tx_id = str(uuid.uuid4())
    amount = payload.amount
    try:
        with db.engine.begin() as conn:
            src = conn.execute(
                text("SELECT balance FROM accounts WHERE id = :id FOR UPDATE"),
                {"id": payload.source},
            ).fetchone()
            dst = conn.execute(
                text("SELECT balance FROM accounts WHERE id = :id FOR UPDATE"),
                {"id": payload.destination},
            ).fetchone()
            if not src or not dst:
                TX_TOTAL.labels(result="rejected").inc()
                raise HTTPException(status_code=404, detail="Compte inconnu")
            if Decimal(src[0]) < amount:
                TX_TOTAL.labels(result="rejected").inc()
                raise HTTPException(status_code=422, detail="Solde insuffisant")
            conn.execute(
                text("UPDATE accounts SET balance = balance - :a WHERE id = :id"),
                {"a": str(amount), "id": payload.source},
            )
            conn.execute(
                text("UPDATE accounts SET balance = balance + :a WHERE id = :id"),
                {"a": str(amount), "id": payload.destination},
            )
            conn.execute(
                text(
                    "INSERT INTO transactions (id, source, destination, amount, "
                    "status, created_by) VALUES (:id,:s,:d,:a,'settled',:u)"
                ),
                {
                    "id": tx_id,
                    "s": payload.source,
                    "d": payload.destination,
                    "a": str(amount),
                    "u": user.get("sub", "?"),
                },
            )
        TX_TOTAL.labels(result="success").inc()
        TX_AMOUNT.observe(float(amount))
        log.info(f"tx OK id={tx_id} montant={amount}")
        return schemas.Transaction(
            id=tx_id,
            source=payload.source,
            destination=payload.destination,
            amount=amount,
            status="settled",
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        TX_TOTAL.labels(result="error").inc()
        log.error(f"tx ERREUR: {exc}")
        raise HTTPException(status_code=500, detail="Échec du traitement")


@app.get("/transactions/{tx_id}", response_model=schemas.Transaction)
def get_transaction(tx_id: str):
    with db.engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, source, destination, amount, status "
                "FROM transactions WHERE id = :id"
            ),
            {"id": tx_id},
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    return schemas.Transaction(
        id=row[0],
        source=row[1],
        destination=row[2],
        amount=Decimal(row[3]),
        status=row[4],
    )


@app.exception_handler(HTTPException)
async def http_exc_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

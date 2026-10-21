"""
Service d'authentification — Resilience-Alpha.

Émet et vérifie des jetons JWT courts pour accéder à l'API métier. Les
utilisateurs sont fictifs. Le secret de signature est injecté par variable
d'environnement (fournie par Vault/SOPS en conditions réelles, cf. security/).
"""
from __future__ import annotations

import logging
import os
import time

import jwt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel
from starlette.responses import Response

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s",'
    '"service":"auth","msg":"%(message)s"}',
)
log = logging.getLogger("auth")

# En labo : secret par défaut, SURCHARGÉ par l'environnement. Jamais en clair
# dans le dépôt pour un vrai déploiement (cf. security/secrets.md).
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-vault")
JWT_ALG = "HS256"
TOKEN_TTL = int(os.getenv("TOKEN_TTL", "900"))  # 15 min

# Annuaire fictif (login -> mot de passe de démo). Fictif et confiné au labo.
USERS = {
    "operator": os.getenv("OP_PASSWORD", "operator-demo"),
    "merchant": os.getenv("MERCHANT_PASSWORD", "merchant-demo"),
}

LOGINS = Counter("auth_logins_total", "Tentatives de login", ["result"])

app = FastAPI(title="Resilience-Alpha — Auth", version="1.0.0")
# CORS : la vitrine (servie sur un autre port) doit pouvoir appeler /login.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class LoginReq(BaseModel):
    username: str
    password: str


class VerifyReq(BaseModel):
    token: str


@app.get("/health")
def health():
    return {"service": "auth", "status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/login")
def login(req: LoginReq):
    expected = USERS.get(req.username)
    if not expected or expected != req.password:
        LOGINS.labels(result="fail").inc()
        log.info(f"login refusé user={req.username}")
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    now = int(time.time())
    token = jwt.encode(
        {"sub": req.username, "iat": now, "exp": now + TOKEN_TTL},
        JWT_SECRET,
        algorithm=JWT_ALG,
    )
    LOGINS.labels(result="ok").inc()
    log.info(f"login OK user={req.username}")
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_TTL}


@app.post("/verify")
def verify(req: VerifyReq):
    try:
        payload = jwt.decode(req.token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Jeton expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Jeton invalide")
    return {"sub": payload["sub"], "exp": payload["exp"]}

"""Connexion base + initialisation du schéma (SI de paiement fictif)."""
from __future__ import annotations

import os

from sqlalchemy import create_engine, text

DB_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://payment:payment@db:5432/payment"
)

# pool_pre_ping : évite les connexions mortes après un redémarrage de la base,
# ce qui rend la reprise plus propre côté API.
engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id       TEXT PRIMARY KEY,
    owner    TEXT NOT NULL,
    balance  NUMERIC(14,2) NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS transactions (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    destination TEXT NOT NULL,
    amount      NUMERIC(14,2) NOT NULL,
    status      TEXT NOT NULL,
    created_by  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def init_db() -> None:
    with engine.begin() as conn:
        for stmt in SCHEMA.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))

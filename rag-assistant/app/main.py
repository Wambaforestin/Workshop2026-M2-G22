"""API de l'assistant RAG opérateur."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from .rag import RagIndex, generate

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rag")

index = RagIndex()


@asynccontextmanager
async def lifespan(_: FastAPI):
    n = index.build()
    log.info(f"Corpus indexé : {n} passages")
    yield


app = FastAPI(title="Resilience-Alpha — Assistant RAG", lifespan=lifespan)


class Ask(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"service": "rag-assistant", "status": "ok", "passages": len(index.passages)}


@app.post("/ask")
async def ask(req: Ask):
    passages = index.retrieve(req.question, k=3)
    result = await generate(req.question, passages)
    return result


@app.post("/reindex")
def reindex():
    n = index.build()
    return {"passages": n}

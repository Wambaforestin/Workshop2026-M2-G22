"""Tests de l'index RAG (récupération)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rag-assistant"))

import os  # noqa: E402

os.environ["CORPUS_DIR"] = str(ROOT / "rag-assistant" / "corpus")

from app.rag import RagIndex  # noqa: E402


def test_index_builds():
    idx = RagIndex()
    n = idx.build()
    assert n > 0


def test_retrieval_is_relevant():
    idx = RagIndex()
    idx.build()
    res = idx.retrieve("service de paiement indisponible", k=3)
    assert res
    # Le passage le plus pertinent doit venir des procédures.
    assert any("procedures" in r["source"] for r in res)

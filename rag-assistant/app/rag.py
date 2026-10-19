"""
Assistant RAG opérateur — Resilience-Alpha.

Objectif (§3.3) : un assistant local qui aide l'opérateur confronté à l'incident
à retrouver des informations utiles dans les procédures, descriptions
d'architecture et autres documents produits par l'équipe. Construit avec
**Ollama** (LLM local) + **LangChain** (orchestration RAG).

Contrainte respectée : le modèle local n'excède pas 8 milliards de paramètres
(par défaut `llama3.2:3b`), et l'assistant n'a **aucun accès privilégié** au
système — il lit seulement une base documentaire. Il ne se confond pas avec le
moteur de remédiation.

Chaîne RAG :
  question -> récupération des passages pertinents (TF-IDF sur le corpus)
           -> construction d'un prompt avec le contexte
           -> génération de la réponse par le LLM local (Ollama)

Dégradation gracieuse : si Ollama n'est pas joignable, l'assistant renvoie les
passages pertinents (mode extractif) pour que la démo reste fonctionnelle.
"""
from __future__ import annotations

import glob
import os
import re

import httpx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")  # ~3B params < 8B
CORPUS_DIR = os.getenv("CORPUS_DIR", "/srv/corpus")


def _split(text: str) -> list[str]:
    """Découpe un document en passages (par paragraphe, fusion des courts)."""
    chunks, buf = [], ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        buf = (buf + "\n" + para).strip() if buf else para
        if len(buf) > 400:
            chunks.append(buf)
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


class RagIndex:
    """Index TF-IDF du corpus documentaire (récupération)."""

    def __init__(self) -> None:
        self.passages: list[str] = []
        self.sources: list[str] = []
        self.vectorizer = TfidfVectorizer()
        self.matrix = None

    def build(self) -> int:
        self.passages, self.sources = [], []
        for path in sorted(glob.glob(f"{CORPUS_DIR}/**/*.md", recursive=True)):
            with open(path, encoding="utf-8") as f:
                for chunk in _split(f.read()):
                    self.passages.append(chunk)
                    self.sources.append(os.path.basename(path))
        if self.passages:
            self.matrix = self.vectorizer.fit_transform(self.passages)
        return len(self.passages)

    def retrieve(self, question: str, k: int = 3) -> list[dict]:
        if not self.passages:
            return []
        q = self.vectorizer.transform([question])
        sims = cosine_similarity(q, self.matrix)[0]
        top = sims.argsort()[::-1][:k]
        return [
            {"text": self.passages[i], "source": self.sources[i], "score": float(sims[i])}
            for i in top
            if sims[i] > 0.01
        ]


PROMPT = """Tu es l'assistant local des opérateurs de la plateforme de paiement \
Resilience-Alpha. Réponds UNIQUEMENT à partir du contexte fourni, en français, \
de façon concise et opérationnelle. Si le contexte ne suffit pas, dis-le.

Contexte :
{context}

Question : {question}

Réponse :"""


async def generate(question: str, passages: list[dict]) -> dict:
    context = "\n\n".join(f"[{p['source']}] {p['text']}" for p in passages)
    prompt = PROMPT.format(context=context or "(aucun passage pertinent)", question=question)
    sources = sorted({p["source"] for p in passages})
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            answer = r.json().get("response", "").strip()
            return {"answer": answer, "sources": sources, "mode": "ollama"}
    except Exception:  # noqa: BLE001 — dégradation gracieuse
        extractive = "\n\n".join(f"• ({p['source']}) {p['text']}" for p in passages)
        return {
            "answer": (
                "Modèle local (Ollama) indisponible — passages pertinents trouvés :\n\n"
                + (extractive or "Aucun passage pertinent dans le corpus.")
            ),
            "sources": sources,
            "mode": "extractif",
        }

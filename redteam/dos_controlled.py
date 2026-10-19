"""
Générateur de charge contrôlé — Resilience-Alpha (labo uniquement).

Produit une rafale de requêtes HTTP légitimes (GET /api/health) à débit élevé
mais BORNÉ, pour créer un pic de trafic observable et déclencher la chaîne
détection -> remédiation. Ce n'est pas un outil d'attaque : il n'exploite aucune
faille et ne fait qu'émettre du trafic applicatif normal en volume, contre votre
propre démonstrateur.

Plafonds de sécurité codés en dur : durée <= 60 s, cadence <= 200 req/s.
"""
from __future__ import annotations

import argparse
import asyncio
import time

import httpx

from _guard import DEFAULT_TARGET, ensure_authorized

MAX_DUREE = 60      # secondes
MAX_RPS = 200       # requêtes/seconde


async def worker(client, url, deadline, counters):
    while time.monotonic() < deadline:
        try:
            r = await client.get(url, timeout=3.0)
            counters[r.status_code] = counters.get(r.status_code, 0) + 1
        except Exception:  # noqa: BLE001
            counters["err"] = counters.get("err", 0) + 1


async def run(target: str, duree: int, rps: int):
    url = target.rstrip("/") + "/api/health"
    deadline = time.monotonic() + duree
    counters: dict = {}
    # Nombre de coroutines ~ cadence voulue (bornée).
    concurrency = min(rps, MAX_RPS)
    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(worker(client, url, deadline, counters))
            for _ in range(concurrency)
        ]
        await asyncio.gather(*tasks)
    total = sum(v for k, v in counters.items() if k != "err")
    print("\n--- Résultat de la charge contrôlée ---")
    print(f"Requêtes émises : ~{total} en {duree}s")
    for code, n in sorted(counters.items(), key=lambda x: str(x[0])):
        libelle = {429: " (limitées par le WAF — défense active)",
                   200: " (servies)"}.get(code, "")
        print(f"  {code}: {n}{libelle}")
    print("\nObservez le dashboard et Grafana : l'anomalie req_rate doit "
          "apparaître, puis la remédiation se déclencher.")


def main():
    p = argparse.ArgumentParser(description="DoS applicatif CONTRÔLÉ (labo).")
    p.add_argument("--target", default=DEFAULT_TARGET)
    p.add_argument("--duree", type=int, default=20, help=f"secondes (max {MAX_DUREE})")
    p.add_argument("--rps", type=int, default=60, help=f"cadence (max {MAX_RPS})")
    p.add_argument("--jaccepte-labo", action="store_true", dest="accepte")
    args = p.parse_args()

    target = ensure_authorized(args.target, args.accepte)
    duree = min(args.duree, MAX_DUREE)
    rps = min(args.rps, MAX_RPS)
    asyncio.run(run(target, duree, rps))


if __name__ == "__main__":
    main()

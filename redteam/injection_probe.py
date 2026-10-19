"""
Sonde d'injection bénigne — Resilience-Alpha (labo uniquement).

Envoie quelques requêtes contenant des motifs d'injection classiques dans un
paramètre d'URL, pour VÉRIFIER que vos défenses réagissent : le WAF doit
renvoyer 403 et journaliser la requête. L'API utilise des requêtes paramétrées :
elle n'est de toute façon pas vulnérable à ces motifs. La sonde constate la
défense ; elle ne contourne rien, n'exploite rien et n'exfiltre rien.
"""
from __future__ import annotations

import argparse

import httpx

from _guard import DEFAULT_TARGET, ensure_authorized

# Motifs de test classiques. Envoyés tels quels pour éprouver le filtrage WAF.
PROBES = [
    "' OR 1=1 --",
    "UNION SELECT null",
    "../../etc/passwd",
    "<script>alert(1)</script>",
]


def run(target: str):
    base = target.rstrip("/") + "/api/accounts/"
    print("--- Sonde d'injection (constat de défense) ---")
    bloques = 0
    with httpx.Client(timeout=4.0) as client:
        for payload in PROBES:
            try:
                r = client.get(base, params={"q": payload})
                etat = "BLOQUÉ par le WAF" if r.status_code == 403 else f"HTTP {r.status_code}"
                if r.status_code == 403:
                    bloques += 1
                print(f"  {payload[:30]:<32} -> {etat}")
            except Exception as exc:  # noqa: BLE001
                print(f"  {payload[:30]:<32} -> erreur réseau ({exc})")
    print(f"\n{bloques}/{len(PROBES)} motifs bloqués par le WAF.")
    print("Vérifiez les journaux WAF dans Grafana/Loki : les requêtes bloquées "
          "doivent y figurer (traçabilité pour l'investigation).")


def main():
    p = argparse.ArgumentParser(description="Sonde d'injection bénigne (labo).")
    p.add_argument("--target", default=DEFAULT_TARGET)
    p.add_argument("--jaccepte-labo", action="store_true", dest="accepte")
    args = p.parse_args()
    target = ensure_authorized(args.target, args.accepte)
    run(target)


if __name__ == "__main__":
    main()

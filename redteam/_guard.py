"""
Garde-fous communs aux scripts Red Team — Resilience-Alpha.

Interdit toute exécution hors du laboratoire du groupe. Ces vérifications sont
volontairement strictes : le sujet limite toute action offensive au SI fictif et
aux machines autorisées de l'équipe (§3.4, §9).
"""
from __future__ import annotations

import ipaddress
import socket
import sys
from urllib.parse import urlparse

# Cibles explicitement autorisées pour la démo locale.
DEFAULT_TARGET = "http://localhost:8080"


def _is_private_host(host: str) -> bool:
    """Autorise uniquement localhost et les adresses privées (labo)."""
    if host in ("localhost",):
        return True
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
    except (OSError, ValueError):
        return False
    return ip.is_private or ip.is_loopback


def ensure_authorized(target: str, accepted: bool) -> str:
    banner = (
        "\n=== Red Team — LABORATOIRE CONTRÔLÉ ===\n"
        "Périmètre autorisé : votre SI fictif, sur votre PC Hôte uniquement.\n"
        "Interdit : réseaux du campus, autres groupes, services tiers/Internet.\n"
        "========================================\n"
    )
    print(banner)
    host = urlparse(target).hostname or ""
    if not _is_private_host(host):
        sys.exit(
            f"[REFUS] Cible '{host}' hors périmètre : seuls localhost et les "
            "adresses privées du labo sont autorisés."
        )
    if not accepted:
        sys.exit(
            "[REFUS] Confirmez explicitement le cadre de labo avec "
            "--jaccepte-labo pour exécuter contre votre propre environnement."
        )
    print(f"[OK] Cible de labo autorisée : {target}\n")
    return target

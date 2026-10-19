"""
Actions Docker du moteur de remédiation.

Liste FERMÉE d'opérations. Pas de commande arbitraire : chaque méthode mappe une
action nommée vers une opération Docker précise. Le préfixe des conteneurs est
celui de docker-compose (projet). Dégrade proprement si le socket Docker n'est
pas monté (mode simulation, pour les tests).
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger("remediation.actions")

COMPOSE_PROJECT = os.getenv("COMPOSE_PROJECT_NAME", "resilience-alpha")
NETWORK = os.getenv("REMEDIATION_NETWORK", "resilience_net")


class DockerOps:
    def __init__(self) -> None:
        self.available = False
        self.client = None
        try:
            import docker  # import tardif : optionnel en mode simulation

            self.client = docker.from_env()
            self.client.ping()
            self.available = True
            log.info("Socket Docker disponible — remédiation active")
        except Exception as exc:  # noqa: BLE001
            log.warning(f"Docker indisponible, mode simulation: {exc}")

    def _find(self, service: str):
        """Retrouve le conteneur d'un service compose par son nom."""
        if not self.available:
            return None
        for c in self.client.containers.list(all=True):
            name = c.name
            if name == service or service in name:
                return c
        return None

    def restart(self, service: str) -> bool:
        if not self.available:
            log.info(f"[sim] restart {service}")
            return True
        c = self._find(service)
        if c:
            c.restart(timeout=10)
            log.info(f"conteneur redémarré: {c.name}")
            return True
        log.warning(f"conteneur introuvable: {service}")
        return False

    def disconnect(self, service: str) -> bool:
        """Confinement : coupe un conteneur du réseau applicatif."""
        if not self.available:
            log.info(f"[sim] isolate {service}")
            return True
        c = self._find(service)
        if not c:
            return False
        try:
            net = self.client.networks.get(NETWORK)
            net.disconnect(c, force=True)
            log.info(f"conteneur isolé du réseau: {c.name}")
            return True
        except Exception as exc:  # noqa: BLE001
            log.error(f"isolation échouée: {exc}")
            return False

# Durcissement — Resilience-Alpha

Mesures défensives appliquées, en réponse au pilier Cybersécurité (§3.4).

## 1. Surface d'exposition minimale

- **Seul le WAF est exposé** sur le réseau pédagogique (port 80/8080). Base,
  secrets, Prometheus, Loki, Vault et interfaces de gestion restent sur le
  réseau interne Docker `resilience_net`, non publié (exigence §4).
- Grafana et Prometheus ne sont publiés qu'en local (bind `127.0.0.1`) pour la
  démo au jury, pas sur le PA du groupe.

## 2. Conteneurs

- Images `-slim`, utilisateur **non-root** dans chaque Dockerfile applicatif.
- `read_only` + `tmpfs` là où c'est possible, `cap_drop: ALL`.
- `no-new-privileges` pour empêcher l'escalade via setuid.
- Healthchecks pour distinguer « conteneur up » de « service réellement sain ».

## 3. Filtrage applicatif (WAF)

- Limitation de débit (amortit le DoS applicatif).
- Blocage de signatures d'injection évidentes (SQLi, traversée de chemin, XSS).
- En-têtes de sécurité, masquage de version (`server_tokens off`).

## 4. Moindre privilège du moteur de remédiation

Le moteur de remédiation dispose de droits élevés sur les conteneurs : c'est un
**point sensible** explicitement pointé par le sujet (§3.4). Mesures :

- Il n'expose **aucune interface d'administration ouverte** : il agit via une
  liste fermée d'actions prédéfinies (`restart_service`, `restart_db`,
  `isolate`), pas un shell distant générique.
- Les actions sont **journalisées** (traçabilité) et **idempotentes**.
- Son jeton d'action (`REMEDIATION_TOKEN`) est à portée limitée et à courte durée.
- Il ne peut agir que sur les services du SI, jamais sur l'hôte au-delà du socket
  Docker nécessaire.

## 5. Traçabilité / investigation

- Journaux applicatifs au format JSON -> Promtail -> Loki -> consultables dans le
  SIEM/Grafana (fonction SOC intégrée à la supervision).
- Les événements WAF (requêtes bloquées) et auth (logins échoués) sont corrélables.

## 6. Ce qui reste hors périmètre (assumé)

- Pas de mTLS entre services (réseau interne isolé jugé suffisant pour 4 jours).
- Pas de scanner de vulnérabilités d'images intégré à la CI (recommandé en prod).
- Secrets en SOPS plutôt que Vault dynamique (arbitrage temps/valeur).

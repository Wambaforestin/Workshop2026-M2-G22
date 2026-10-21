# Project Resilience-Alpha — Démonstrateur de cyber-résilience

Workshop National EPSI/myDiL — BAC+5 — Session Octobre 2026.
Démonstrateur d'une **chaîne de cyber-résilience** : un SI de paiement fictif qui
encaisse un incident de sécurité contrôlé et **se rétablit seul**, sans
intervention corrective humaine.

> ⚠️ Environnement **entièrement fictif**. Aucune donnée bancaire réelle.
> Toute action offensive est limitée au laboratoire du groupe.

## Les cinq domaines (obligatoires) couverts

| Domaine | Réalisation |
|---|---|
| **Développement** | Microservices FastAPI (API métier, auth), base Postgres, vitrine + dashboard **React/Tailwind**, moteur de remédiation |
| **Infrastructure** | **Docker Compose**, **Ansible**, **Prometheus / Grafana / Loki** (+ Promtail), WAF nginx |
| **IA / Data** | Détection d'anomalies **ML** (covariance robuste, type EllipticEnvelope), assistant **RAG** (Ollama + LangChain) |
| **Cybersécurité** | WAF, SIEM (Loki/Grafana), durcissement, secrets **SOPS/Vault**, scénario Red Team de labo |
| **Transformation** | **EBIOS RM**, **PCA/PRA**, conformité **NIS2/DORA**, arbitrages |

## Architecture

```
          PC Attaquant (redteam/)
                 │  attaque contrôlée (DoS / sonde injection)
                 ▼
   ┌─────────────────────────────────────── PC Hôte ───────────────────────────────┐
   │   [WAF nginx] ──► [payment-api] ──► [Postgres]                                 │
   │       │   └─► [auth JWT]                                                       │
   │       └─► [storefront React]                                                   │
   │                                                                                │
   │   Observabilité : [Prometheus] ◄─ métriques ── (api, auth, ml, remediation)    │
   │                   [Loki] ◄─ journaux ── [Promtail]      [Grafana] (dashboards) │
   │                                                                                │
   │   Chaîne de résilience :                                                       │
   │     [ml-detection] ── anomalie ──► [remediation] ── actions ──► conteneurs     │
   │          ▲ métriques Prometheus         │ vérifie health/deep + tx test        │
   │     [rag-assistant] (Ollama+LangChain, lecture seule, sans droits privilégiés) │
   │     [dashboard React/Tailwind] : services, détection, remédiation, assistant   │
   └────────────────────────────────────────────────────────────────────────────────┘
```

## Démarrage rapide

Prérequis : Docker Desktop (WSL2 sous Windows), 16 Go RAM conseillés.

```bash
# 1. (optionnel) préparer les secrets
cp security/secrets.env.example security/secrets.env   # puis chiffrer avec SOPS

# 2. démarrer toute la plateforme
docker compose up -d --build

# 3. (optionnel) activer l'IA générative locale (RAG)
docker compose --profile ia up -d ollama
docker exec -it resilience-alpha-ollama-1 ollama pull llama3.2:3b
```

### Points d'accès (démo locale)

| Service | URL |
|---|---|
| Vitrine de paiement | http://localhost:8090 |
| Dashboard de supervision | http://localhost:3001 |
| Grafana | http://localhost:3000 (admin / `admin-demo`) |
| Prometheus | http://localhost:9090 |
| API détection ML | http://localhost:8200/state |
| Moteur de remédiation | http://localhost:8300/events |
| Assistant RAG | http://localhost:8400/ask |

## Dérouler la démonstration (le scénario du jury)

Voir **[docs/04_scenario_demo.md](docs/04_scenario_demo.md)** — enchaînement
complet : état sain → attaque → anomalie détectée → remédiation → reprise vérifiée.

```bash
# 1. état sain : payer depuis la vitrine (transaction fictive OK)
# 2. déclencher l'incident depuis le PC Attaquant :
pip install httpx
python redteam/dos_controlled.py --duree 20 --rps 80 --jaccepte-labo
# 3. observer dashboard + Grafana : anomalie → remédiation → service rétabli
# 4. re-payer : la nouvelle transaction aboutit = reprise prouvée
```

## Tests

```bash
pip install -r tests/requirements.txt
pytest tests/ -v          # tests unitaires (détection ML, RAG, API)
```

## Arborescence

```
payment-si/     SI de paiement (api FastAPI, auth JWT, db, frontend)
ml-detection/   détection d'anomalies (covariance robuste + boucle Prometheus)
rag-assistant/  assistant opérateur RAG (Ollama + LangChain + corpus)
remediation/    moteur de remédiation autonome (politique + actions Docker)
dashboard/      supervision React/Tailwind
infra/          waf, prometheus, grafana, loki, promtail, ansible
security/       durcissement + gestion des secrets (SOPS/Vault)
redteam/        scénario d'attaque de laboratoire (borné, défensif)
docs/           EBIOS RM, PCA/PRA, NIS2/DORA, scénario de démo
tests/          tests automatisés
```

## Rendus imposés (nommage §7)

| Rendu | Fichier |
|---|---|
| Dossier d'ingénierie et de gouvernance | `Workshop2026-M2-G01-Dossier.pdf` (généré, cf. PDF livré) |
| Archive des sources et du déploiement | `Workshop2026-M2-G01-Code.zip` |
| Support de présentation | `Workshop2026-M2-G01-Pres.pptx` (à produire par l'équipe) |
| Clip Chrono (≤ 60 s) | `Workshop2026-M2-G01-VidChrono.mp4` (à capturer lors de la démo) |

> Remplacez `G01` par le numéro réel de votre équipe (`G<n>`).

## Limites assumées

Prototype pédagogique de 4 jours, pas une plateforme industrielle prête à la
production. Les arbitrages (SOPS vs Vault, pas de mTLS interne, PC Hôte unique)
sont documentés dans `security/hardening.md` et `docs/`.

---
Généré avec Claude (Cowork) · données et contexte métier entièrement fictifs.

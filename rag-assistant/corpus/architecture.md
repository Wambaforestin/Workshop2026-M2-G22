# Architecture de la plateforme Resilience-Alpha

La plateforme est un SI de paiement fictif composé de microservices conteneurisés.

## Composants
- WAF (reverse-proxy nginx) : seul point d'entrée exposé. Filtre le trafic, limite le débit.
- API métier (payment-api, FastAPI) : crée les comptes, exécute les transactions, expose les métriques.
- Service d'authentification (auth, JWT) : émet et vérifie les jetons d'accès.
- Base de données (Postgres) : stocke comptes et transactions. Jamais exposée hors réseau interne.
- Vitrine marchande (storefront) : interface web de paiement.

## Chaîne de résilience
- ml-detection : détecte les anomalies par machine learning (détecteur de nouveauté à covariance robuste) sur les métriques Prometheus.
- remediation : moteur de reprise autonome, déclenche les opérations correctives.
- supervision/dashboard : vue temps réel des services, événements, alertes et avancement de la reprise.

## Observabilité
- Prometheus collecte les métriques. Grafana les visualise. Loki centralise les journaux via Promtail.

## Réseau
Tous les services communiquent sur le réseau interne Docker resilience_net. Seul le WAF est publié.

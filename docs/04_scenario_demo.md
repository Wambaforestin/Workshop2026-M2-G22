# Scénario de démonstration — le fil du jury

Déroulé de 5 minutes rendant visible l'état du service **avant**, **pendant** et
**après** l'incident (exigence §2).

## 0. Préparation (avant le jury)
```bash
docker compose up -d --build
# Vérifier que tout est UP sur le dashboard : http://localhost:3001
```

## 1. État sain (≈ 30 s)
- Ouvrir la **vitrine** (http://localhost:8090). Le bandeau affiche
  « service disponible ».
- Cliquer **Payer** : une transaction fictive aboutit (`status: settled`).
- Sur le **dashboard** : tous les services UP, détection « NORMAL ».

## 2. Déclenchement de l'incident (≈ 30 s) — depuis le PC Attaquant
```bash
python redteam/dos_controlled.py --duree 20 --rps 80 --jaccepte-labo
```
- Le **WAF** commence à renvoyer des `429` (limitation de débit — défense active).
- La vitrine peut afficher « indisponible » / les paiements ralentissent.

## 3. Détection (≈ 30 s)
- **Grafana** : l'alerte `TrafficSpike` (et éventuellement `HighLatency`) passe.
- **Dashboard** : la carte « Détection ML » passe **ANOMALIE**, driver `req_rate`,
  avec l'explication « débit anormalement élevé — possible déni de service ».

## 4. Remédiation autonome (≈ 60 s)
- La détection notifie le moteur de remédiation (`/incident`).
- Carte « Remédiation » : événements `incident → decision → action → verify →
  recovered`.
- Le moteur applique son plan (redémarrage ciblé) **et vérifie réellement** :
  `health/deep` 200 **+** une transaction fictive test aboutie.

## 5. Reprise prouvée (≈ 30 s)
- La vitrine réaffiche « service disponible ».
- Cliquer de nouveau **Payer** : la transaction aboutit → **le métier est
  réellement rétabli** (pas seulement un conteneur relancé).
- Dashboard : détection repasse **NORMAL**, remédiation **STABLE**.

## 6. Assistant opérateur (bonus, ≈ 30 s)
- Dans la carte **Assistant RAG**, poser :
  « Que faire si le service de paiement est indisponible ? »
- L'assistant répond à partir des **procédures** (sources citées), sans aucun
  droit d'action sur le système.

## Variante : scénario injection
```bash
python redteam/injection_probe.py --jaccepte-labo
```
Montre le WAF qui **bloque** (403) et journalise, et rappelle la distinction
reprise de disponibilité ≠ traitement d'une compromission.

## Le Clip Chrono (≤ 60 s)
Capturer en une **séquence continue** : lancement de l'attaque → apparition de
l'anomalie → réaction du système → vérification du service rétabli. Pas de coupe
masquant une action manuelle.

# PCA / PRA — Plan de continuité et de reprise d'activité

Adapté à la solution livrée (Resilience-Alpha). Le PCA vise à **maintenir** le
service de paiement ; le PRA vise à le **rétablir** après incident.

## 1. Objectifs de continuité et de reprise

| Indicateur | Cible retenue (démo) | Justification |
|---|---|---|
| **RTO** (délai de reprise) | < 60 s | Reprise automatique sans intervention humaine |
| **RPO** (perte de données) | ~ 0 | Transactions en base transactionnelle (ACID), pas de perte en vol |
| **Disponibilité visée** | Démontrable sur le périmètre labo | Objectif pédagogique, pas un SLA industriel |

## 2. Scénarios couverts

| Scénario | Couvert par | Type de réponse |
|---|---|---|
| Indisponibilité API/base | Détection ML + remédiation (restart base → API) | **Disponibilité** |
| Pic de trafic / DoS applicatif | WAF rate-limit + remédiation (durcissement/restart) | **Disponibilité** |
| Erreurs anormales / injection | WAF + flag investigation | Disponibilité **+** investigation (distincte) |

**Distinction essentielle** (§2 du sujet) : restaurer la **disponibilité** (faire
redémarrer le service) n'est pas corriger une **compromission** ou une **fuite**.
Le moteur de remédiation rétablit le service ; une compromission ouvre, en
parallèle, une procédure d'investigation — les deux réponses ne sont pas les
mêmes et ne se substituent pas l'une à l'autre.

## 3. Mécanisme de reprise (boucle fermée)

```
Collecte (Prometheus/Loki) → Détection (ML — covariance robuste)
   → Décision (politique de remédiation selon le driver)
   → Action (Ansible / API Docker : restart, durcissement, isolation)
   → Vérification RÉELLE (health/deep + transaction fictive test)
   → Clôture  (ou nouvelle tentative, max 3)
```

Une reprise n'est déclarée que si la **vérification métier** réussit : santé
profonde (base joignable + comptes lisibles) **et** une nouvelle transaction
fictive aboutit. Un conteneur qui redémarre ne suffit pas.

## 4. Responsabilités (RACI simplifié)

| Activité | Responsable | Consulté |
|---|---|---|
| Détection d'anomalie | Service ML (automatique) | Équipe IA/Data |
| Décision de remédiation | Moteur de remédiation (politique) | Équipe Infra/Cyber |
| Exécution des opérations | Ansible / API Docker | Équipe Infra |
| Validation de la reprise | Vérification automatique + opérateur | Toute l'équipe |
| Investigation compromission | Opérateur + fonction SOC (SIEM) | Équipe Cyber |

## 5. Choix de restauration

- **Priorité à la disponibilité du paiement** : on relance base puis API.
- **Idempotence** : les actions peuvent être rejouées sans effet de bord.
- **Limite de tentatives** (3) : au-delà, bascule en traitement humain (le sujet
  sanctionne le recours humain pendant le live, mais en industriel une
  escalade maîtrisée est préférable à une boucle infinie).

## 6. Risques subsistant après la reprise

- Une reprise de **disponibilité** ne garantit pas l'absence de **compromission**
  résiduelle : d'où le flag d'investigation.
- Dépendance au PC Hôte unique (pas de redondance matérielle en labo).
- Rejeu possible d'une attaque tant que la cause racine n'est pas corrigée.

## 7. Tests du plan

Le PRA est **testé en direct** (chaos engineering, jeudi) : injection de
défaillances, observation de la détection, de la remédiation et de la
vérification. Le Clip Chrono matérialise un cycle complet (attaque → anomalie →
reprise → service rétabli).

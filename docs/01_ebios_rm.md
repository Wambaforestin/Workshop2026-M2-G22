# Analyse de risques — EBIOS Risk Manager

Project Resilience-Alpha — SI de paiement fictif. Analyse structurée selon les
cinq ateliers EBIOS RM (méthode ANSSI).

## Atelier 1 — Cadrage et socle de sécurité

**Objet de l'étude** : plateforme de paiement fictive (vitrine, API métier,
authentification, base de données), sa chaîne de résilience (détection ML,
remédiation autonome) et sa supervision.

**Valeurs métier**
| Valeur métier | Description | Besoin de sécurité dominant |
|---|---|---|
| Exécution des transactions | Débit/crédit entre comptes | **Disponibilité**, intégrité |
| Solde des comptes | Exactitude des montants | **Intégrité** |
| Authentification | Accès légitime à l'API | Confidentialité, intégrité |
| Journaux / traçabilité | Preuve et investigation | Intégrité, disponibilité |

**Biens supports** : conteneurs (API, auth, db), WAF, réseau interne Docker,
socket Docker (utilisé par la remédiation), secrets (JWT, mot de passe base),
stack d'observabilité.

**Socle de sécurité** : durcissement conteneurs (non-root, cap_drop,
no-new-privileges), WAF en entrée unique, secrets hors dépôt (SOPS/Vault),
cloisonnement réseau (seul le WAF exposé). Écarts assumés : pas de mTLS interne,
secrets SOPS plutôt que Vault dynamique.

## Atelier 2 — Sources de risque / objectifs visés

| Source de risque (SR) | Objectif visé (OV) | Pertinence |
|---|---|---|
| Cybercriminel opportuniste | Interrompre le service (rançon implicite, nuisance) | Élevée |
| Attaquant applicatif | Détourner/altérer des transactions via injection | Élevée |
| Acteur interne négligent | Fuite de secrets, mauvaise config | Moyenne |
| Concurrent / déstabilisation | Atteinte à la réputation par indisponibilité | Moyenne |

Couples SR/OV prioritaires retenus : **interruption de service** et **atteinte à
l'intégrité des transactions**.

## Atelier 3 — Scénarios stratégiques

**Écosystème** : partenaires (marchands, clients fictifs), dépendance au PC Hôte,
au WiFi du campus. Parties prenantes critiques : l'hébergeur (PC Hôte lui-même).

- **SS1** : un attaquant externe sature l'API depuis le réseau du consortium →
  indisponibilité du paiement.
- **SS2** : un attaquant soumet des requêtes malveillantes à l'API exposée →
  tentative d'altération de données.

## Atelier 4 — Scénarios opérationnels

| # | Scénario opérationnel | Chemin d'attaque | Vraisemblance | Gravité |
|---|---|---|---|---|
| SO1 | **Déni de service applicatif** | Rafale de requêtes → saturation API/base → service indisponible | Forte | Critique (G4) |
| SO2 | **Injection applicative** | Paramètre malveillant → tentative SQLi → altération/lecture | Moyenne | Critique (G4) |
| SO3 | **Fuite de secret** | Secret en clair → accès base → exfiltration | Faible | Grave (G3) |
| SO4 | **Abus du moteur de remédiation** | Interface d'admin ouverte → prise de contrôle des conteneurs | Faible | Critique (G4) |

## Atelier 5 — Traitement du risque

| # | Mesure de traitement | Effet | Statut démo |
|---|---|---|---|
| SO1 | WAF rate-limiting + détection ML `req_rate` + remédiation (restart/durcissement) | Réduit vraisemblance et impact | **Implémenté** |
| SO2 | WAF filtrage signatures + requêtes **paramétrées** côté API + détection `error_ratio` + flag investigation | Réduit vraisemblance | **Implémenté** |
| SO3 | Secrets SOPS/Vault hors dépôt, base non exposée, rotation | Réduit vraisemblance | **Implémenté** (SOPS) |
| SO4 | Remédiation sans interface ouverte, actions fermées, jeton à portée limitée, journalisation | Réduit vraisemblance | **Implémenté** |

**Risques résiduels** (après traitement) : DoS volumétrique massif dépassant le
rate-limiting (hors périmètre labo) ; compromission du PC Hôte lui-même ;
absence de mTLS interne. Suivi recommandé en contexte industriel.

### Synthèse — services jugés critiques
L'API métier et la base sont **critiques** (le paiement en dépend directement).
L'arrêt d'une fonction de paiement coûte, pour l'activité : retards partenaires,
perte de confiance, et — en financier régulé — exposition réglementaire. C'est ce
coût qui justifie l'investissement dans la reprise automatique.

# Gestion des secrets — Resilience-Alpha

Le sujet impose la gestion des secrets avec **HashiCorp Vault** ou **SOPS**.
Principe retenu : **aucun secret en clair dans le dépôt** (exigence 7.4).

## Approche retenue pour la démo : SOPS + age

SOPS chiffre les fichiers de secrets ; seule la clé `age` (hors dépôt) permet de
les déchiffrer au déploiement. C'est plus léger qu'un cluster Vault pour un labo
de 4 jours, tout en répondant à l'exigence.

### Mise en place

```bash
# 1. Générer une paire de clés age (la clé privée reste HORS du dépôt)
age-keygen -o ~/.config/sops/age/keys.txt

# 2. Chiffrer le fichier de secrets
export SOPS_AGE_RECIPIENTS=$(grep public ~/.config/sops/age/keys.txt | cut -d' ' -f4)
sops --encrypt --age $SOPS_AGE_RECIPIENTS secrets.env > secrets.enc.env

# 3. Au déploiement, déchiffrer vers l'environnement
sops --decrypt secrets.enc.env > .env
```

Seul `secrets.enc.env` (chiffré) est versionné. Le `.env` déchiffré et la clé
privée `age` sont dans `.gitignore`.

## Alternative : Vault (conditions réelles)

En production on préfèrerait Vault : secrets dynamiques (identifiants base à
durée de vie courte), rotation automatique, audit log, politique d'accès par
service. Le moteur de remédiation, qui détient des droits élevés, obtiendrait
un jeton Vault à portée limitée (politique restreinte aux seules opérations de
reprise) plutôt qu'un accès administrateur permanent — cf. `security/hardening.md`.

## Secrets concernés

| Secret | Usage | Rotation |
|--------|-------|----------|
| `JWT_SECRET` | Signature des jetons d'authentification | À chaque déploiement |
| `POSTGRES_PASSWORD` | Accès base de paiement | Rotation Vault en prod |
| `GRAFANA_ADMIN_PASSWORD` | Console de supervision | Manuelle |
| `REMEDIATION_TOKEN` | Autorise le moteur de remédiation à agir | Courte durée |

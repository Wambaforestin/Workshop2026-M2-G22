# Démonstration réelle à deux PC — attaque réseau + logs

Ce guide met en place la **vraie** configuration du sujet : deux ordinateurs
distincts, reliés par le **point d'accès mobile Windows** du groupe. Le PC
Attaquant lance une **vraie attaque réseau** sur le PC Hôte ; toute l'équipe
observe la détection, la remédiation et les **logs** sur le PC Hôte.

```
   PC ATTAQUANT (Machine 2)                 PC HÔTE (Machine 1)
   - kit redteam                            - toute la plateforme (13 services)
   - connecté AU hotspot du groupe   ──►    - crée le hotspot « RESILIENCE-G01 »
   - attaque 192.168.137.1:8090             - IP sur le hotspot : 192.168.137.1
                                            - on regarde dashboard + Grafana + logs
```

> Rappel sujet : **seul le WAF (port 8090) est exposé** sur le réseau du groupe.
> Base, Prometheus, Grafana restent internes au PC Hôte. On attaque donc le WAF,
> comme un vrai attaquant depuis l'extérieur.

---

## ÉTAPE 1 — PC Hôte : créer le point d'accès et lancer la plateforme

### 1.1 Activer le point d'accès mobile Windows
Paramètres → **Réseau et Internet** → **Point d'accès mobile** → **Activer**.
- Donnez-lui le nom **RESILIENCE-G01** (Modifier → nom + mot de passe).
- Windows attribue alors au PC Hôte l'adresse **192.168.137.1** sur cette interface.

Vérifiez l'adresse dans un terminal :
```
ipconfig
```
Cherchez la ligne **Adresse IPv4 . . . : 192.168.137.1** (carte « Connexion au réseau local* » du point d'accès). Notez cette IP — c'est la cible de l'attaque.

### 1.2 Autoriser le port 8090 dans le pare-feu Windows
Sans ça, l'autre PC ne pourra pas joindre le WAF. Dans un **PowerShell administrateur** :
```
New-NetFirewallRule -DisplayName "Resilience WAF 8090" -Direction Inbound -LocalPort 8090 -Protocol TCP -Action Allow
```

### 1.3 Lancer la plateforme
Dans le dossier du projet :
```
docker compose up -d --build
docker compose ps
```
Les 13 services doivent être **Up**, dont `resilience-alpha-waf-1` en `0.0.0.0:8090->80/tcp`.

### 1.4 Vérifier que le WAF répond sur l'IP du hotspot
Toujours sur le PC Hôte :
```
curl http://192.168.137.1:8090/api/health
```
Vous devez obtenir `{"service":"payment-api","status":"ok"}`. Si oui, le PC Attaquant pourra l'atteindre.

---

## ÉTAPE 2 — PC Attaquant : se connecter et préparer l'attaque

### 2.1 Se connecter au point d'accès
Sur le PC Attaquant, connectez-vous au WiFi **RESILIENCE-G01** (celui créé par le PC Hôte). **Ce doit être sa seule connexion** (pas de WiFi campus en même temps), conformément au sujet.

Vérifiez que vous joignez bien l'hôte :
```
ping 192.168.137.1
```

### 2.2 Préparer le kit (une seule fois)
Décompressez le zip **PC2-Attaquant**. Installez Python (si absent) puis la dépendance :
```
pip install httpx
```

### 2.3 Vérifier l'accès au WAF depuis l'attaquant
```
curl http://192.168.137.1:8090/api/health
```
Si vous obtenez le JSON `status ok`, la cible est joignable. (Sinon : voir Dépannage.)

---

## ÉTAPE 3 — Lancer la VRAIE attaque (depuis le PC Attaquant)

```
python redteam\dos_controlled.py --target http://192.168.137.1:8090 --duree 15 --rps 200 --jaccepte-labo
```

Ce n'est pas une simulation : ce sont de vraies requêtes HTTP envoyées **sur le
réseau** vers le PC Hôte. Résultat attendu dans le terminal attaquant : un
mélange de `200` (servies) et de `429` (bloquées par le WAF).

---

## ÉTAPE 4 — Observer sur le PC Hôte (les logs et la reprise)

Pendant et après l'attaque, regardez **trois choses** sur le PC Hôte :

### 4.1 Le dashboard (vue métier)
http://localhost:3001
- **Détection ML** passe en **ANOMALIE** (driver `req_rate`).
- **Remédiation autonome** affiche la suite d'événements : `incident → decision → action → verify → recovered`.
- **Paiement** peut clignoter DOWN puis repasser UP (c'est la reprise réelle).

### 4.2 Les logs dans Grafana / Loki (le SIEM)
http://localhost:3000 (admin / admin-demo) → ouvrir le dashboard **Resilience-Alpha — Supervision**.
Le panneau **Journaux (Loki)** affiche en direct :
- les requêtes **bloquées par le WAF** (`"blocked":"1"` / statut `429`),
- les lignes de la **détection** (`ANOMALIE driver=req_rate`),
- les actions de la **remédiation** (`action`, `recovered`).

Pour explorer librement : Grafana → **Explore** → source **Loki** → requête :
```
{container=~".*(waf|ml-detection|remediation).*"}
```

### 4.3 Les logs bruts en console (preuve directe)
Dans un terminal du PC Hôte :
```
docker compose logs -f waf ml-detection remediation
```
Vous voyez défiler : les 429 du WAF, l'anomalie détectée, puis le redémarrage
du service par la remédiation et la vérification (`verify`, `recovered`).

---

## Ce qui rend la démo « réelle » (à dire au jury)

- L'attaque part d'un **autre ordinateur**, par le **réseau**, sur le seul port exposé (le WAF).
- La remédiation agit **réellement** sur les conteneurs (socket Docker du PC Hôte), pas en simulation.
- Les **logs** circulent de bout en bout : WAF → Promtail → Loki → Grafana (SIEM).
- La reprise est **vérifiée** : une nouvelle transaction fictive doit aboutir.

Variante — montrer le blocage d'injection (WAF renvoie 403) :
```
python redteam\injection_probe.py --target http://192.168.137.1:8090 --jaccepte-labo
```

---

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `curl` depuis l'attaquant échoue | Pare-feu Windows bloque 8090 | Rejouer la règle PowerShell (étape 1.2) |
| `ping 192.168.137.1` échoue | Attaquant pas sur le hotspot | Reconnecter au WiFi RESILIENCE-G01 |
| L'IP de l'hôte n'est pas .137.1 | Autre interface active | Prendre l'IPv4 de la carte du point d'accès (`ipconfig`) et l'utiliser comme cible |
| Pas d'anomalie après 10 s | Débit trop faible | Monter `--rps 200` et `--duree 20` |
| Panneau Loki vide | Promtail démarre après le WAF | Attendre 30 s, ou `docker compose restart promtail` |

> Le script refuse toute cible qui n'est pas une adresse privée de labo, et exige
> `--jaccepte-labo`. L'attaque reste strictement confinée à votre réseau de groupe.

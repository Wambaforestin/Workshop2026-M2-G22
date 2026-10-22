# PC HÔTE (Machine 1) — démarrage rapide

Cet ordinateur héberge **toute la plateforme** et crée le point d'accès du groupe.
L'attaque viendra du **PC Attaquant** (Machine 2), via le réseau.

## En 4 commandes

```
# 1. Activer le point d'accès mobile Windows (nom : RESILIENCE-G01)
#    puis autoriser le port du WAF (PowerShell administrateur) :
New-NetFirewallRule -DisplayName "Resilience WAF 8090" -Direction Inbound -LocalPort 8090 -Protocol TCP -Action Allow

# 2. Lancer la plateforme
docker compose up -d --build

# 3. Vérifier que tout est Up
docker compose ps

# 4. Vérifier que le WAF répond sur l'IP du hotspot
curl http://192.168.137.1:8090/api/health
```

## Pendant la démo, gardez ces 3 fenêtres ouvertes

1. **Dashboard** : http://localhost:3001  (état des services, détection, remédiation)
2. **Grafana / logs** : http://localhost:3000  (admin / admin-demo) → dashboard « Resilience-Alpha »
3. **Logs console** : `docker compose logs -f waf ml-detection remediation`

## Le guide complet (réseau, attaque, logs, dépannage)

➡️ **docs/05_demo_deux_pc.md** — lisez-le, tout y est.

> Donnez au PC Attaquant l'adresse IP de ce PC sur le hotspot (normalement
> `192.168.137.1`, à confirmer avec `ipconfig`).

# Scénario Red Team — laboratoire contrôlé

> **Périmètre strict.** Ces scripts ne ciblent QUE votre propre SI fictif de
> démonstration, sur le PC Hôte de votre groupe. Toute action offensive est
> interdite sur les réseaux du campus, un autre consortium, un équipement tiers
> ou un service accessible sur Internet (sujet §3.4, §9). Les scripts refusent
> de s'exécuter contre une cible qui n'est pas explicitement autorisée.

## Objectif pédagogique

Produire, depuis le **PC Attaquant**, un effet **observable** sur la plateforme,
pour **déclencher votre propre chaîne de détection → remédiation** et prouver la
reprise automatique. Il ne s'agit pas d'exploiter une faille réelle : il s'agit
de créer une perturbation mesurable que vos propres mécanismes doivent repérer
et corriger seuls.

## Deux scénarios fournis

### 1. Déni de service applicatif contrôlé (`dos_controlled.py`)
Génère une rafale de requêtes HTTP légitimes vers l'API, à un débit élevé mais
**borné** (durée et cadence plafonnées). Effet attendu, entièrement défensif à
observer :
- le **WAF** applique sa limitation de débit (réponses 429) ;
- **Prometheus** voit le pic (`req_rate`), l'alerte `TrafficSpike` se déclenche ;
- la **détection ML** signale une anomalie `driver=req_rate` ;
- la **remédiation** applique son plan et vérifie la reprise.

C'est un générateur de charge, pas un outil d'attaque réutilisable : aucune
faille n'est exploitée, le trafic est du trafic applicatif normal en volume.

### 2. Sonde d'injection bénigne (`injection_probe.py`)
Envoie quelques requêtes contenant des **motifs d'injection classiques** (ex.
`' OR 1=1 --`) dans un paramètre d'URL. But : vérifier que **vos défenses
réagissent** — le WAF doit renvoyer `403` et journaliser la requête bloquée, et
l'API (requêtes paramétrées) ne doit de toute façon pas être affectée. La sonde
**constate** la défense ; elle ne contourne rien et n'exfiltre rien.

## Garde-fous intégrés

- Cible par défaut `http://localhost:8090` (votre labo). Toute autre cible doit
  être passée en argument **et** confirmée par `--jaccepte-labo`.
- Les hôtes publics/non privés sont **refusés** par le script.
- Débit et durée plafonnés en dur.
- Chaque exécution affiche une bannière rappelant le périmètre autorisé.

## Usage

```bash
pip install httpx
python dos_controlled.py --duree 20 --rps 60 --jaccepte-labo
python injection_probe.py --jaccepte-labo
```

Observez simultanément le dashboard (http://localhost:3001) et Grafana
(http://localhost:3000) : c'est là que la chaîne de résilience se donne à voir.

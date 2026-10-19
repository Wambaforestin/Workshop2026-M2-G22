# Automatisation Ansible — Resilience-Alpha

Ansible automatise les **opérations** prévues au cahier des charges : déploiement
reproductible de la plateforme sur le PC Hôte, et actions de reprise pilotées.

## Place dans le dispositif

| Outil | Rôle |
|-------|------|
| **Docker Compose** | Définit et orchestre les conteneurs (le *quoi*). |
| **Ansible** | Automatise les opérations sur l'hôte et les conteneurs : déploiement, redémarrage ciblé, rotation de secrets, snapshot base (le *comment opérationnel*). |
| **Moteur de remédiation** | Déclenche automatiquement certaines de ces opérations suite à un incident (le *quand/décision*). |

## Playbooks

- `playbooks/deploy.yml` — déploiement reproductible complet.
- `playbooks/remediate.yml` — opérations de reprise appelables par le moteur de
  remédiation (redémarrage d'un service, bascule de la base, isolation réseau).

## Usage

```bash
ansible-playbook -i inventory.ini playbooks/deploy.yml
ansible-playbook -i inventory.ini playbooks/remediate.yml -e "action=restart_service service=payment-api"
```

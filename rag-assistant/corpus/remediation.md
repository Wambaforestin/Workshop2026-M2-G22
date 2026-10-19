# Fonctionnement du moteur de remédiation

Le moteur de remédiation reçoit les incidents de la détection ML, décide d'une
action corrective adaptée, l'exécute, puis vérifie que le service est rétabli.

## Règles de décision (politique)
- driver = latency_p95 ou base injoignable -> redémarrage de la base puis de l'API.
- driver = req_rate (DoS) -> durcissement du débit + redémarrage API si saturée.
- driver = error_ratio -> redémarrage API + marquage pour investigation sécurité.
- driver = inflight -> redémarrage de l'API pour vider la file.

## Boucle fermée
Détection -> décision -> action (via playbook Ansible / API Docker) -> vérification
(/api/health/deep + transaction test) -> clôture ou nouvelle tentative (max 3).

## Garde-fous
Le moteur agit via une liste FERMÉE d'actions prédéfinies. Il n'expose aucune
interface d'administration ouverte. Toutes ses actions sont journalisées. Son
jeton est à portée limitée. Il ne peut pas être piloté par l'assistant RAG.

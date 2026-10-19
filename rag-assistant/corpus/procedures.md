# Procédures d'exploitation — Resilience-Alpha

## Procédure : service de paiement indisponible
1. Vérifier l'alerte dans Grafana (PaymentServiceDown) et l'état de payment_db_up.
2. Consulter /api/health/deep : s'il répond 503, la base est en cause.
3. Le moteur de remédiation redémarre automatiquement la base puis l'API.
4. Confirmer la reprise par une transaction fictive de test réussie.

## Procédure : pic de trafic / déni de service suspecté
1. L'alerte TrafficSpike se déclenche (> 50 req/s).
2. Le WAF applique déjà une limitation de débit (429 au-delà du seuil).
3. La détection ML signale l'anomalie avec driver = req_rate.
4. La remédiation peut activer un durcissement temporaire du débit.
5. Vérifier que le service métier reste utilisable pour le trafic légitime.

## Procédure : taux d'erreur anormal / injection applicative suspectée
1. Alerte HighErrorRate (> 20% de 5xx) ou driver ML = error_ratio.
2. Vérifier les journaux WAF : requêtes bloquées (SQLi, traversée de chemin).
3. Attention : une injection n'est PAS un simple problème de disponibilité.
   La remédiation restaure le service, mais l'investigation de la compromission
   est une action distincte (ne pas confondre reprise et correction d'une fuite).

## Procédure : vérifier une reprise réelle
Un conteneur qui redémarre ne prouve pas la reprise. Vérifier :
- /api/health/deep répond 200 (base joignable + comptes lisibles) ;
- une nouvelle transaction fictive aboutit (status settled) ;
- les métriques repassent sous les seuils d'alerte.

## Contacts et limites
Toute action offensive est limitée au SI fictif. En cas de difficulté, se référer au coach.

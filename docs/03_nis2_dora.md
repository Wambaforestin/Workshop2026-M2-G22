# Conformité — NIS2 et DORA

Lecture des enjeux réglementaires pour une activité financière fictive, en
distinguant ce qu'un prototype de 4 jours **peut démontrer** de ce qu'il ne peut
qu'**esquisser**.

## 1. NIS2 (Directive UE 2022/2555)

Relève la sécurité des réseaux et systèmes d'information pour les entités
essentielles/importantes. Points pertinents pour la plateforme :

| Exigence NIS2 | Ce que le démonstrateur montre | Démontrable en 4 j ? |
|---|---|---|
| Gestion des risques (art. 21) | Analyse EBIOS RM structurée | ✅ Oui |
| Détection et gestion d'incidents | Détection ML + remédiation + journaux SIEM | ✅ Oui |
| Continuité d'activité, gestion de crise | PCA/PRA, reprise automatique testée | ✅ Partiel |
| Sécurité de la chaîne d'approvisionnement | — (dépendances conteneurs listées) | ⚠️ Esquissé |
| Notification d'incident (24 h / 72 h) | Procédure décrite, pas de reporting réel | ❌ Non (hors prototype) |
| Chiffrement, contrôle d'accès | JWT, secrets SOPS, durcissement | ✅ Partiel |

## 2. DORA (Règlement UE 2022/2554)

Résilience opérationnelle numérique du secteur financier. Cinq piliers :

| Pilier DORA | Correspondance dans le projet | Démontrable ? |
|---|---|---|
| 1. Gestion du risque TIC | EBIOS RM, cartographie des biens supports | ✅ Oui |
| 2. Gestion/classification/notification d'incidents | Détection, journalisation, flag investigation | ✅ Partiel (notif. non) |
| 3. Tests de résilience opérationnelle | Chaos engineering, test du PRA en direct | ✅ Oui |
| 4. Risque lié aux tiers TIC | Dépendances (images, PC Hôte) documentées | ⚠️ Esquissé |
| 5. Partage d'informations sur les cybermenaces | — | ❌ Non (hors périmètre) |

## 3. Démarche de conseil — arbitrages et recommandations

**Ce que je recommanderais à une direction**, sur des éléments vérifiables :

1. **Investir d'abord dans la détection+reprise automatique** (piliers DORA 2 et
   3) : c'est là que le démonstrateur prouve une valeur mesurable (RTO < 60 s).
2. **Ne pas confondre disponibilité et sécurité** : séparer budgétairement la
   remédiation (disponibilité) et l'investigation (compromission).
3. **Passer de SOPS à Vault** en production pour les secrets dynamiques et
   l'audit — arbitrage temps/valeur non tenable à l'échelle industrielle.
4. **Mettre en place le reporting d'incident** (NIS2 24 h/72 h, DORA) : non
   démontrable par un prototype mais obligatoire en exploitation réelle.

## 4. Exigences qui ne peuvent PAS être démontrées en 4 jours

- Notification réglementaire d'incident aux autorités (délais légaux).
- Audit de résilience par un tiers indépendant (DORA pilier 3 avancé).
- Gestion contractuelle des prestataires TIC critiques (DORA pilier 4).
- Historique de conformité et revues périodiques.

Les signaler honnêtement fait partie de la démarche de conseil : un rapport de
conformité générique, sans lien avec l'architecture et les essais réels, ne
suffirait pas (sujet §3.5).

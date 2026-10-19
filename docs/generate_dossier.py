"""Génère le Dossier d'ingénierie et de gouvernance (PDF) — Resilience-Alpha."""
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, ListFlowable, ListItem,
)

OUT = "/home/claude/Workshop2026-M2-G01/Workshop2026-M2-G01-Dossier.pdf"

NAVY = colors.HexColor("#1b2a4a")
BLUE = colors.HexColor("#2f5bd4")
LIGHT = colors.HexColor("#eef2fb")
GREY = colors.HexColor("#5b6472")
GREEN = colors.HexColor("#1f9d6b")

styles = getSampleStyleSheet()
def S(name, **kw):
    styles.add(ParagraphStyle(name, **kw))

S("Cover", fontName="Helvetica-Bold", fontSize=30, textColor=NAVY, leading=34, alignment=TA_CENTER)
S("CoverSub", fontName="Helvetica", fontSize=14, textColor=BLUE, leading=20, alignment=TA_CENTER)
S("CoverMeta", fontName="Helvetica", fontSize=10, textColor=GREY, leading=16, alignment=TA_CENTER)
S("H1", fontName="Helvetica-Bold", fontSize=16, textColor=NAVY, leading=20, spaceBefore=14, spaceAfter=6)
S("H2", fontName="Helvetica-Bold", fontSize=12, textColor=BLUE, leading=16, spaceBefore=10, spaceAfter=4)
S("Body", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#1f2733"), leading=14, alignment=TA_JUSTIFY, spaceAfter=5)
S("Small", fontName="Helvetica", fontSize=8.5, textColor=GREY, leading=12)
S("Blt", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#1f2733"), leading=13)
S("Mono", fontName="Courier", fontSize=8, textColor=NAVY, leading=11)
S("TH", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.white, leading=11)
S("TD", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#1f2733"), leading=11)
S("TDb", fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY, leading=11)

story = []

def h1(t): story.append(Paragraph(t, styles["H1"]))
def h2(t): story.append(Paragraph(t, styles["H2"]))
def p(t): story.append(Paragraph(t, styles["Body"]))
def small(t): story.append(Paragraph(t, styles["Small"]))
def sp(h=6): story.append(Spacer(1, h))
def rule(): story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#c7d2ec"), spaceBefore=4, spaceAfter=8))

def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(i, styles["Blt"]), leftIndent=6, value="•") for i in items],
        bulletType="bullet", start="•", leftIndent=12, spaceAfter=6))

def table(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),5), ("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LINEBELOW",(0,0),(-1,-1),0.3,colors.HexColor("#d3dcef")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT]),
    ]
    if header:
        cmds += [("BACKGROUND",(0,0),(-1,0),NAVY), ("TOPPADDING",(0,0),(-1,0),6), ("BOTTOMPADDING",(0,0),(-1,0),6)]
    t.setStyle(TableStyle(cmds))
    story.append(t)
    sp(8)

def th(t): return Paragraph(t, styles["TH"])
def td(t): return Paragraph(t, styles["TD"])
def tdb(t): return Paragraph(t, styles["TH"])  # en-tetes: blanc sur fond navy

# ============================ COUVERTURE ============================
story.append(Spacer(1, 5.5*cm))
story.append(Paragraph("PROJECT RESILIENCE-ALPHA", styles["Cover"]))
sp(6)
story.append(Paragraph("Dossier d'ingénierie et de gouvernance", styles["CoverSub"]))
story.append(Paragraph("Cyber-résilience et reprise autonome", styles["CoverSub"]))
sp(20)
story.append(HRFlowable(width="40%", thickness=2, color=BLUE, hAlign="CENTER"))
sp(20)
story.append(Paragraph("Workshop National EPSI / myDiL — BAC+5", styles["CoverMeta"]))
story.append(Paragraph("Équipe Workshop2026-M2-G&lt;n&gt; · Session Octobre 2026", styles["CoverMeta"]))
story.append(Paragraph("Démonstrateur à données entièrement fictives", styles["CoverMeta"]))
story.append(PageBreak())

# ============================ 1. CONTEXTE ============================
h1("1. Contexte et objectif")
p("À l'automne 2026, une plateforme de paiement exploitée par une entreprise financière fictive subit "
  "une série d'incidents qui fragilisent la continuité de son activité. Les remises en service sont "
  "aujourd'hui manuelles, longues et difficilement reproductibles. L'initiative <b>Project "
  "Resilience-Alpha</b> vise à démontrer, sur un périmètre maîtrisé, qu'une reprise automatique peut "
  "être conçue, observée et vérifiée.")
p("Ce dossier présente les décisions qui structurent notre démonstrateur : architecture et flux, rôle "
  "des composants, nature de l'incident, mécanismes de détection et de reprise, résultats des essais, "
  "éléments de sécurité, analyse des risques, PCA/PRA et choix de gouvernance. L'objectif n'est pas de "
  "livrer une plateforme industrielle, mais une <b>chaîne de cyber-résilience crédible</b>, exécutable "
  "et défendable techniquement.")
h2("Objectif démontré")
bullets([
    "Un SI de paiement fictif, conteneurisé, exécute de vraies transactions simulées.",
    "Un incident de sécurité contrôlé est provoqué depuis un poste distinct (PC Attaquant).",
    "La plateforme détecte seule l'anomalie, décide d'une remédiation, l'exécute et <b>vérifie</b> le retour à un état utilisable.",
    "L'état du service est rendu visible avant, pendant et après l'incident.",
])

h1("2. Architecture et flux")
p("La solution réunit les cinq domaines obligatoires du sujet au sein d'une plateforme unique, "
  "orchestrée par Docker Compose. Un seul point d'entrée — le WAF — est exposé ; tous les autres "
  "services communiquent sur un réseau interne isolé.")
# Flux ASCII-like en table
flow = [
    [tdb("Couche"), tdb("Composants"), tdb("Rôle")],
    [td("Entrée"), td("WAF (nginx)"), td("Seul point exposé : filtrage applicatif, limitation de débit")],
    [td("Métier"), td("payment-api (FastAPI), auth (JWT), PostgreSQL, vitrine"), td("Comptes, transactions, authentification, interface")],
    [td("Observabilité"), td("Prometheus, Grafana, Loki, Promtail"), td("Métriques, visualisation, journaux centralisés (SIEM)")],
    [td("IA / Data"), td("ml-detection, rag-assistant (Ollama+LangChain)"), td("Détection d'anomalies ; assistant opérateur documentaire")],
    [td("Résilience"), td("remediation, dashboard React/Tailwind"), td("Reprise autonome et supervision temps réel")],
]
table(flow, [2.4*cm, 6.2*cm, 8.0*cm])
small("Réseau : <b>resilience_net</b> (interne Docker). Base, secrets et interfaces de gestion ne sont jamais publiés sur le réseau pédagogique.")

story.append(PageBreak())

# ============================ 3. CINQ DOMAINES ============================
h1("3. Les cinq domaines de responsabilité")

h2("3.1 — Développement")
p("Le SI de paiement est composé de microservices conteneurisés. L'<b>API métier</b> (FastAPI) crée les "
  "comptes et exécute les transactions de façon atomique (débit/crédit sous verrou, cohérence ACID). "
  "Le <b>service d'authentification</b> émet et vérifie des jetons JWT courts. La <b>vitrine</b> et le "
  "<b>dashboard</b> sont développés en React avec Tailwind CSS, conformément au pilier DEV.")

h2("3.2 — Infrastructure")
p("La plateforme se déploie de manière reproductible via <b>Docker Compose</b> ; des playbooks "
  "<b>Ansible</b> automatisent les opérations (déploiement, redémarrage ciblé, isolation). La stack "
  "d'observabilité <b>Prometheus / Grafana / Loki</b> (alimentée par Promtail) renseigne l'état des "
  "services et alimente réellement l'analyse de l'incident — pas d'Elastic Stack, par souci de charge "
  "mémoire sur le PC Hôte.")

h2("3.3 — IA / Data")
p("La détection ne se réduit pas à des conditions codées en dur : un modèle de machine learning non "
  "supervisé (détecteur de nouveauté à covariance robuste, <i>EllipticEnvelope</i>) apprend la « forme » "
  "du comportement normal et signale les écarts (détaillé en §4). Un second composant, l'<b>assistant "
  "RAG</b> (Ollama + LangChain, modèle local &lt; 8 Md de paramètres), aide l'opérateur à retrouver des "
  "informations dans les procédures et l'architecture — en lecture seule, <b>sans aucun droit "
  "privilégié</b> sur le système, et distinct du moteur de remédiation.")

h2("3.4 — Cybersécurité")
p("Les dispositifs défensifs attendus sont en place : durcissement des composants et des accès (conteneurs "
  "non-root, capacités réduites, no-new-privileges), filtrage applicatif par <b>WAF</b>, suivi des "
  "événements dans un <b>SIEM</b> (Loki/Grafana intégré à la supervision), et gestion des secrets par "
  "<b>SOPS</b> (alternative Vault documentée). Une attention particulière est portée au moteur de "
  "remédiation, qui dispose de droits élevés : il n'expose aucune interface d'administration ouverte "
  "(§5).")

h2("3.5 — Gouvernance et transformation")
p("La résilience ne se limite pas aux opérations techniques. Une analyse de risques <b>EBIOS Risk "
  "Manager</b> (§6), un <b>PCA/PRA</b> adapté (§7) et une lecture des enjeux <b>NIS2/DORA</b> (§8) "
  "justifient les choix : quels services sont critiques, quels risques sont retenus, et ce que coûte "
  "l'arrêt d'une fonction de paiement.")

story.append(PageBreak())

# ============================ 4. DETECTION ============================
h1("4. Détection d'anomalies (ML)")
p("<b>Principe.</b> On apprend à quoi ressemble une « journée normale » de la plateforme à travers "
  "quatre indicateurs issus de Prometheus, puis on trace une enveloppe autour de cette zone normale. "
  "Toute mesure qui en sort nettement est signalée. Le seuil de décision n'est pas écrit à la main : "
  "il est <b>calibré par le modèle</b> sur les données normales (environ 0,5 % de faux positifs tolérés).")
feats = [
    [tdb("Feature"), tdb("Signification"), tdb("Ce qu'un écart révèle")],
    [td("req_rate"), td("Requêtes par seconde"), td("Débit anormal → possible déni de service")],
    [td("error_ratio"), td("Part de réponses 5xx"), td("Erreurs anormales → injection ou panne applicative")],
    [td("latency_p95"), td("Latence au 95e percentile"), td("Latence anormale → saturation / contention base")],
    [td("inflight"), td("Requêtes en cours"), td("Accumulation → service en difficulté")],
]
table(feats, [2.6*cm, 5.4*cm, 8.6*cm])
p("<b>Pourquoi ce modèle.</b> Un <i>Isolation Forest</i> a d'abord été testé, mais il manquait certains "
  "écarts extrêmes portés par une seule variable. Le détecteur à covariance robuste mesure la distance "
  "de Mahalanobis au nuage normal : il tient compte des corrélations entre indicateurs et reste fiable "
  "sur ces cas. Le choix a été validé par tests automatisés (cas normal, pic de débit, pic de latence, "
  "pic d'erreurs → tous correctement classés).")
p("<b>Explicabilité.</b> Pour chaque alerte, le service indique le <i>driver principal</i> (la feature la "
  "plus hors-normale) et une phrase d'explication opérationnelle, puis notifie le moteur de remédiation. "
  "Le modèle est raccordé à la supervision et expose ses propres méta-métriques à Prometheus.")

h1("5. Reprise autonome (remédiation)")
p("Le moteur de remédiation ferme la boucle : il reçoit l'incident, décide d'une action selon une "
  "<b>politique explicite</b>, l'exécute sur les conteneurs, puis <b>vérifie réellement</b> le retour "
  "à un état utilisable avant de clôturer.")
story.append(Paragraph(
    "Détection → Décision (politique selon le driver) → Action (restart / durcissement / isolation) "
    "→ Vérification (health/deep + transaction fictive test) → Clôture ou nouvelle tentative (max 3)",
    styles["Mono"]))
sp(6)
pol = [
    [tdb("Driver d'anomalie"), tdb("Plan d'action"), tdb("Intention")],
    [td("latency_p95 / base down"), td("restart base → restart API"), td("Lever la contention / reconnecter")],
    [td("req_rate (DoS)"), td("restart API (+ durcissement débit)"), td("Absorber le pic, vider la file")],
    [td("error_ratio"), td("restart API + flag investigation"), td("Rétablir ET ouvrir une investigation sécurité")],
    [td("inflight"), td("restart API"), td("Vider la file de requêtes")],
]
table(pol, [4.6*cm, 6.0*cm, 6.0*cm])
p("<b>Reprise réelle, pas cosmétique.</b> Une reprise n'est déclarée que si la vérification métier "
  "réussit : santé profonde (base joignable + comptes lisibles) <b>et</b> une nouvelle transaction "
  "fictive qui aboutit. Un conteneur qui redémarre ne suffit pas.")
p("<b>Garde-fou du composant privilégié.</b> Le moteur agit via une <b>liste fermée</b> d'actions "
  "prédéfinies (pas de shell distant générique), toutes journalisées et idempotentes ; son jeton est à "
  "portée limitée ; il ne peut pas être piloté par l'assistant RAG. On ne distingue pas non plus "
  "restauration de disponibilité et correction d'une compromission : une erreur anormale déclenche, "
  "en parallèle de la reprise, un marquage pour investigation.")

story.append(PageBreak())

# ============================ 6. RED TEAM ============================
h1("6. Scénario d'attaque — laboratoire contrôlé")
p("L'incident est provoqué depuis un <b>PC Attaquant</b> distinct, strictement contre notre propre SI "
  "fictif. Toute action offensive est interdite sur les réseaux du campus, un autre groupe ou un "
  "service tiers. Les scripts refusent de s'exécuter contre une cible non privée et exigent une "
  "confirmation explicite du cadre de labo ; débit et durée sont plafonnés.")
bullets([
    "<b>Déni de service applicatif contrôlé</b> : une rafale bornée de requêtes légitimes crée un pic observable. "
    "Effet attendu : le WAF limite (429), l'alerte TrafficSpike se déclenche, la détection signale req_rate, la remédiation agit.",
    "<b>Sonde d'injection bénigne</b> : quelques motifs d'injection classiques sont envoyés pour vérifier que le WAF "
    "bloque (403) et journalise. L'API (requêtes paramétrées) n'est de toute façon pas vulnérable : la sonde constate la défense, elle ne contourne rien.",
])
p("Il ne s'agit pas d'un outil d'attaque réutilisable : aucun exploit n'est livré. L'objectif est "
  "pédagogique — produire un effet mesurable que nos propres mécanismes doivent repérer et corriger seuls.")

h1("7. PCA / PRA")
pcapra = [
    [tdb("Indicateur"), tdb("Cible (démo)"), tdb("Justification")],
    [td("RTO (délai de reprise)"), td("&lt; 60 s"), td("Reprise automatique sans intervention humaine")],
    [td("RPO (perte de données)"), td("~ 0"), td("Base transactionnelle ACID, pas de perte en vol")],
    [td("Disponibilité visée"), td("Démontrable sur le labo"), td("Objectif pédagogique, non un SLA industriel")],
]
table(pcapra, [4.8*cm, 4.2*cm, 7.6*cm])
p("Le plan couvre l'indisponibilité API/base, le pic de trafic/DoS et les erreurs anormales. Il "
  "distingue explicitement <b>restaurer la disponibilité</b> (faire redémarrer le service) de "
  "<b>corriger une compromission</b> (investigation distincte). Le PRA est testé en direct (chaos "
  "engineering), et le Clip Chrono matérialise un cycle complet attaque → anomalie → reprise → service "
  "rétabli.")
h2("Risques subsistant après la reprise")
bullets([
    "Une reprise de disponibilité ne garantit pas l'absence de compromission résiduelle (d'où le flag d'investigation).",
    "Dépendance au PC Hôte unique (pas de redondance matérielle en labo).",
    "Rejeu possible tant que la cause racine n'est pas corrigée.",
])

story.append(PageBreak())

# ============================ 8. NIS2/DORA ============================
h1("8. Conformité — NIS2 et DORA")
p("Démarche de conseil : distinguer ce qu'un prototype de quatre jours <b>peut démontrer</b> de ce "
  "qu'il ne peut qu'<b>esquisser</b>, plutôt qu'un rapport de conformité générique détaché de "
  "l'architecture.")
conf = [
    [tdb("Exigence"), tdb("Dans le projet"), tdb("Démontrable en 4 j ?")],
    [td("Gestion des risques TIC (NIS2 art.21 / DORA 1)"), td("Analyse EBIOS RM, cartographie des biens"), td("Oui")],
    [td("Détection et gestion d'incidents (DORA 2)"), td("Détection ML, remédiation, journaux SIEM"), td("Partiel (notif. réglementaire : non)")],
    [td("Tests de résilience opérationnelle (DORA 3)"), td("Chaos engineering, test du PRA en direct"), td("Oui")],
    [td("Continuité / gestion de crise (NIS2)"), td("PCA/PRA, reprise automatique testée"), td("Partiel")],
    [td("Risque lié aux tiers TIC (DORA 4)"), td("Dépendances images / PC Hôte documentées"), td("Esquissé")],
    [td("Notification d'incident (24 h / 72 h)"), td("Procédure décrite"), td("Non (hors prototype)")],
]
table(conf, [6.6*cm, 5.6*cm, 4.4*cm])
h2("Recommandations à une direction")
bullets([
    "Investir d'abord dans la détection + reprise automatique (valeur mesurable : RTO &lt; 60 s).",
    "Séparer budgétairement remédiation (disponibilité) et investigation (compromission).",
    "Passer de SOPS à Vault en production (secrets dynamiques, audit).",
    "Mettre en place le reporting réglementaire d'incident, non démontrable par un prototype mais obligatoire en exploitation.",
])

h1("9. Essais et limites assumées")
p("<b>Essais réalisés.</b> Tests automatisés de la détection (cas normal + trois types d'anomalies), de "
  "la validation des transactions (montants négatif/nul rejetés), de la récupération documentaire du RAG "
  "et des garde-fous Red Team (cible publique refusée, confirmation exigée) — tous au vert. Validation "
  "syntaxique des configurations Docker/Prometheus/Grafana.")
p("<b>Limites.</b> Prototype pédagogique de quatre jours : pas de mTLS interne, secrets en SOPS plutôt "
  "que Vault dynamique, PC Hôte unique sans redondance, modèle de détection entraîné sur des "
  "observations constituées faute d'historique de production. Ces arbitrages sont documentés dans le "
  "dépôt (security/, docs/). Ce que nous revendiquons est une chaîne de cyber-résilience crédible, "
  "exécutable et défendable — pas une plateforme industrielle prête à la production.")
sp(10)
rule()
small("Projet Resilience-Alpha — Dossier d'ingénierie et de gouvernance · Données et contexte métier "
      "entièrement fictifs · Équipe Workshop2026-M2-G&lt;n&gt; · EPSI/myDiL BAC+5, Octobre 2026.")

# ============================ MISE EN PAGE ============================
def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c7d2ec"))
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.4*cm, A4[0]-2*cm, 1.4*cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(2*cm, 1.0*cm, "Project Resilience-Alpha — Dossier d'ingénierie et de gouvernance")
    canvas.drawRightString(A4[0]-2*cm, 1.0*cm, "Page %d" % doc.page)
    canvas.restoreState()

def cover_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(LIGHT)
    canvas.rect(0, A4[1]-6*cm, A4[0], 6*cm, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, A4[0], 1.2*cm, fill=1, stroke=0)
    canvas.restoreState()

frame = Frame(2*cm, 1.7*cm, A4[0]-4*cm, A4[1]-3.4*cm, id="main")
doc = BaseDocTemplate(OUT, pagesize=A4, title="Workshop2026-M2-G<n> — Dossier", author="Equipe Resilience-Alpha")
doc.addPageTemplates([
    PageTemplate(id="cover", frames=[Frame(2*cm, 2*cm, A4[0]-4*cm, A4[1]-4*cm)], onPage=cover_bg),
    PageTemplate(id="body", frames=[frame], onPage=footer),
])
# première page = cover, puis bascule body
from reportlab.platypus import NextPageTemplate
story.insert(0, NextPageTemplate("body"))
story.insert(0, Paragraph("", styles["Body"]))  # anchor on cover template

doc.build(story)
print("PDF généré:", OUT)

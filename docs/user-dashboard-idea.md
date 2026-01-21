De algemene collaboratie-architectuur van VALOR
(menselijk samenwerken zonder inhoudelijke rollen, met agents als expliciterende actoren)

Hoe die architectuur zichtbaar wordt in het gebruikersdashboard
(wat ziet een gebruiker en waarom)

Een implementatieplan met Epics en User Stories
(zodanig geformuleerd dat dit voor alle perspectieven geldt)

Alles is perspectief-agnostisch, view-agnostisch en agent-agnostisch.

1. Algemene collaboratie-architectuur van VALOR
1.1 Kernprincipe

VALOR ondersteunt collectieve kennisconstructie, geen taakverdeling.

Daarom gelden de volgende architectuurprincipes:

Iedere gebruiker kan inhoudelijk alles doen

Niets is “waar” zonder expliciete status

Conflicten zijn expliciete objecten

AI Agents produceren voorstellen, geen waarheid

Besluitvorming is een aparte laag boven inhoud

1.2 Mens, Agent en Model: heldere scheiding
Mensen

creëren, wijzigen, bevragen en betwisten inhoud

werken parallel en asynchroon

zijn epistemisch gelijkwaardig

AI Agents

analyseren inhoud

doen voorstellen

signaleren inconsistenties, ambiguïteit en ontbrekende onderbouwing

veranderen nooit direct het canonieke model

Model (Neo4j)

single source of truth

bevat:

concepten

relaties

perspectieven

statussen

voorstellen

conflicten

1.3 Objecten met status (fundamenteel)

Alle inhoudelijke objecten hebben een status, bijvoorbeeld:

draft

proposed

contested

supported

accepted

superseded

Dit geldt voor:

nodes

relaties

claims

analyses

agentvoorstellen

Status vervangt hiërarchie.

1.4 Perspectieven en views

Een perspectief is een samenhangende manier van kijken (causaal, normatief, juridisch, waarden, etc.).

Een view is een visualisatie of interactievorm binnen een perspectief.

Belangrijk:

perspectieven delen hetzelfde onderliggende model

views lezen subsets, maar muteren nooit impliciet

1.5 Collaboratie = voorstel + reactie

Elke inhoudelijke bijdrage is één van de volgende:

directe wijziging (mens)

voorstel (mens of agent)

reactie op voorstel

statusovergang

Dit maakt samenwerking traceerbaar en uitbreidbaar naar democratische besluitvorming.

2. Het gebruikersdashboard als collaboratief kompas

Het dashboard is geen takenlijst, maar een situational awareness-interface.

2.1 Wat het dashboard expliciet niet is

geen rolgebaseerde UI

geen “to-do’s omdat jij X bent”

geen lineair workflow-scherm

2.2 Wat het dashboard wél toont

Het dashboard beantwoordt vier vragen:

Waar ben ik onderdeel van?

Waar gebeurt nu iets inhoudelijks?

Waar is spanning, conflict of onzekerheid?

Waar kan ik bijdragen?

2.3 Dashboardstructuur (conceptueel)
2.3.1 Mijn Omgevingen

Per gebruiker:

Organisaties

Projecten

Thema’s

Met indicaties:

recent actief

read-only of write

open voorstellen

2.3.2 Activiteitsoverzicht

Aggregatie over alle perspectieven:

nieuwe voorstellen (mens of agent)

gewijzigde statussen

gemarkeerde conflicten

open vragen van agents

Niet gesorteerd op “mijn taak”, maar op inhoudelijke relevantie.

2.3.3 Spanning en conflict

Een expliciet paneel:

conflicterende definities

inconsistente loops

concurrerende alternatieven

normatieve vs descriptieve spanning

Dit is essentieel voor jouw visie op publieke waarde.

2.3.4 Persoonlijke focus

Gebruiker kan zelf markeren:

interessante thema’s

gevolgde nodes

relevante voorstellen

Dit is persoonlijke ordening, geen autoriteit.

2.4 Navigatie vanuit dashboard

Vanuit elk dashboarditem:

naar perspectief

naar specifieke view

met contextselectie (node, relatie, pad)

3. Implementatieplan
3.1 Architectuurlagen
Frontend

Dashboard shell

Perspective shells

View modules

Context & selection management

Agent interaction panels

Backend

Graph API (Neo4j)

Proposal API

Agent API (CrewAI + LangChain)

Status & conflict services

3.2 Epics en User Stories
EPIC 1 — Collaboratieve kern (perspectief-agnostisch)

Doel: uniforme samenwerking over alle perspectieven.

US-COLLAB-01 — Objecten met expliciete status

Als gebruiker
wil ik dat elk inhoudelijk object een status heeft
zodat duidelijk is wat voorlopig, betwist of geaccepteerd is.

US-COLLAB-02 — Voorstellen als first-class object

Als gebruiker of AI Agent
wil ik wijzigingen als voorstel kunnen doen
zodat alternatieven expliciet naast elkaar kunnen bestaan.

US-COLLAB-03 — Conflicten expliciet maken

Als gebruiker
wil ik dat conflicten tussen voorstellen zichtbaar worden
zodat inhoudelijke spanning niet verborgen blijft.

EPIC 2 — Dashboard als collaboratief overzicht

Doel: zicht op samenwerking, niet op rollen.

US-DASH-01 — Overzicht van toegankelijke omgevingen

Als gebruiker
wil ik alle omgevingen zien waar ik toegang toe heb
zodat ik snel kan navigeren.

US-DASH-02 — Activiteitenfeed over perspectieven heen

Als gebruiker
wil ik recente inhoudelijke activiteit zien
zodat ik weet waar het gesprek plaatsvindt.

US-DASH-03 — Conflicten en spanning zichtbaar

Als gebruiker
wil ik conflicten en onzekerheden kunnen zien
zodat ik gericht kan bijdragen.

EPIC 3 — Contextuele interactie met AI Agents

Doel: AI als expliciterende partner, niet als chatbot.

US-AGENT-01 — Contextgebonden agentacties

Als gebruiker
wil ik bij selectie van een object relevante AI-acties zien
zodat de AI mij helpt op de juiste plek.

US-AGENT-02 — Gescheiden contextuele conversaties

Als gebruiker
wil ik dat AI-conversaties gebonden zijn aan context
zodat gesprekken niet door elkaar lopen.

(Implementatie: per node, per pad, per voorstel)

US-AGENT-03 — Gestructureerde agentoutputs

Als ontwikkelaar
wil ik dat agents alleen gestructureerde outputs leveren
zodat UI-consistentie behouden blijft.

(dit is jouw bestaande US en zit hier precies goed)

EPIC 4 — Perspectieven en views uitbreidbaar

Doel: nieuwe perspectieven en layouts zonder refactor.

US-PERS-01 — Perspective-agnostische shells

Als ontwikkelaar
wil ik perspectieven als modules kunnen toevoegen
zodat uitbreiding geen impact heeft op bestaande code.

US-VIEW-01 — View-isolatie

Als ontwikkelaar
wil ik layouts/views volledig geïsoleerd kunnen toevoegen
zodat nieuwe visualisaties geen bestaande beïnvloeden.

4. Belangrijk architecturaal inzicht (samenvattend)

VALOR is geen systeem dat zegt:

“Wie mag wat doen?”

Maar een systeem dat zegt:

“Wat bestaat hier, wat is betwist, wat is onderbouwd, en waar zit spanning?”

Het dashboard is de visuele manifestatie van dat principe.
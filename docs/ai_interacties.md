Hier zijn drie samenhangende, perspectief-onafhankelijke ontwerpopties voor context-aware conversatie in VALOR, inclusief implicaties voor frontend, backend, agent-orchestratie en samenwerking. Ik sluit af met een expliciet voorkeursmodel en positionering van US-CAUSA-AG-03 – AgentOutputs expliciet.

1. Kernprobleem (geabstraheerd)

Je wilt binnen VALOR:

context-aware interactie met AI Agents;

werken over meerdere perspectieven, meerdere views per perspectief en meerdere agents;

gelijktijdig samenwerken met meerdere gebruikers;

UI-consistentie behouden;

voorkomen dat één “alles-op-één-hoop”-chat semantisch en sociaal onhanteerbaar wordt.

Dit is geen UX-detail, maar een architecturaal vraagstuk over de locus van betekenis:
waar “bestaat” een conversatie in het systeem?

2. Ontwerpdimensies

Elke oplossing positioneert conversaties langs drie orthogonale assen:

Scope van context

Globaal (ecosysteem / perspectief)

View-gebonden

Object-gebonden (node, edge, cluster, artefact)

Scope van participatie

Privé (per gebruiker)

Gedeeld (collaboratief)

Scope van agentinteractie

Enkelvoudige agent

Multi-agent (georkestreerd)

Elke robuuste oplossing moet expliciet keuzes maken op deze assen.

3. Ontwerpoplossingen
Optie A – Eén globale chat met dynamische context-injectie

(af te raden bij collaboratief gebruik)

Beschrijving

Eén chatinterface per perspectief of workspace.

Context (geselecteerde node, view state) wordt impliciet meegegeven aan agent prompts.

Voordelen

Simpel te implementeren.

Lage cognitieve drempel voor solo-gebruik.

Nadelen

Context wisselt impliciet en onzichtbaar.

Onbruikbaar bij gelijktijdig werken door meerdere gebruikers.

Conversaties worden semantisch ambigu en niet reproduceerbaar.

UI-consistentie onder druk (schending van US-CAUSA-AG-03).

Conclusie
Alleen geschikt voor prototyping of single-user scenarios.

Optie B – Object-gebonden conversaties (node-centric)

(structureel sterk, maar incompleet)

Beschrijving

Elk object (node, edge, artefact) kan één of meer conversaties hebben.

Chat opent in context van het geselecteerde object.

Conversatie is persistent en deelbaar.

Voordelen

Context expliciet en stabiel.

Conversaties zijn herleidbaar en navigeerbaar.

Goed passend bij graph-gebaseerde modellen.

Nadelen

Fragmentatie: kennis zit opgesloten per object.

Geen plek voor cross-object of strategische gesprekken.

Agents hebben beperkt overzicht.

Conclusie
Zeer geschikt als één conversatietype, maar niet als enige.

Optie C – Meervoudig conversatiemodel (aanbevolen)

Conversation-as-a-First-Class Object

3.1 Kernidee

Conversaties zijn expliciete, zelfstandige entiteiten met:

een type;

een contextbinding;

een participatiescope;

een agentconfiguratie.

Niet “de chat”, maar meerdere conversation types.

4. Voorstel: Canoniek Conversatiemodel (perspectief-onafhankelijk)
4.1 Conversatietypen
1. Global Conversation

Scope: perspectief of ecosysteem

Gebruik: verkenning, reflectie, strategie

Context: expliciet geselecteerde artefacten (opt-in)

Participatie: privé of gedeeld

2. View-bound Conversation

Scope: specifieke view binnen een perspectief

Context: view state (filters, layout, selectie)

Gebruik: analyse van wat “nu zichtbaar is”

3. Object-bound Conversation

Scope: node, edge, cluster

Context: object + gerelateerde objecten

Gebruik: duiding, verrijking, transformatie

Persistent en navigeerbaar vanuit het object

4. Task / Action Conversation

Scope: tijdelijke taak

Context: expliciet gedefinieerd task-contextobject

Gebruik: “werk dit uit”, “genereer voorstel”, “valideer”

4.2 Frontend-architectuur implicaties
Principes

Geen impliciete context

Context altijd zichtbaar en muteerbaar

Conversatie ≠ UI-pane

Concrete UI-patronen

Conversatiepanelen zijn instantieerbaar (zoals tabs of threads).

Elk conversatiepaneel toont:

Type (global, view, object, task)

Contextbinding(en)

Actieve agenten

Objecten hebben:

een “Conversations”-entrypoint;

indicatie van bestaande conversaties.

Samenwerking

Gedeelde conversaties zijn read/write synchroon.

Privé-conversaties kunnen later “gepromoveerd” worden.

5. Backend-architectuur (CrewAI + LangChain)
5.1 Agentstructuur
Agent-niveaus

Perspective Agents

Domeinspecifiek (CAUSA, NORM, ACTOR, etc.)

Global Agents

Samenvatten, valideren, harmoniseren

Utility Agents

Structureren, formatteren, controleren

Belangrijk principe

Agents bezitten geen API’s.
Agents zijn pure reasoners.

5.2 API-ontwerp (FastAPI)

Niet: één FastAPI per agent
Wel: één backend met expliciete services

Kernservices

Conversation Service

Context Assembly Service

Agent Orchestration Service

Output Validation Service

Agents worden aangeroepen via orchestratie, niet direct.

5.3 Agent Orchestratie (CrewAI)
Orchestratiepatroon

Elke conversatie heeft:

een Conversation Orchestrator

een Agent Composition (welke agents, in welke rol)

CrewAI definieert:

taken per agent;

volgorde;

validatiestappen.

Context-flow

UI selecteert contextobject(en)

Context Assembly Service bouwt een expliciet contextpakket

Orchestrator verdeelt context over agents

Agent outputs → validatie → persistente opslag

6. Positionering van US-CAUSA-AG-03 – AgentOutputs expliciet

Deze user story is fundamenteel, niet optioneel.

Architecturale rol

Elke agentoutput:

is typed

volgt een schema

is losgekoppeld van presentatie

Gevolgen

UI renderet views, geen tekststromen.

Conversaties bestaan uit events met semantische payloads.

Multi-agent output kan worden samengevoegd, vergeleken en gereconcilieerd.

Concreet

JSON Schema / Pydantic per outputtype

Output Validation Service als verplichte stap

Geen “vrije chat text” richting frontend

7. Samenvattend voorkeursbeeld

Meervoudige conversaties als first-class objects

Expliciete contextbinding op elk niveau

Agent-orchestratie centraal, niet per agent

Strikt gestructureerde outputs als fundament

Frontend als context- en conversatiecomposer, niet als chatbox

Dit model is:

perspectief-onafhankelijk;

schaalbaar naar meerdere agents en gebruikers;

consistent met VALOR als epistemisch ecosysteem, niet als chatbot.
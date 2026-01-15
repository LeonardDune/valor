Ik geef je:

Een beknopte maar dragende architectuurbeschrijving van het geheel

Eén Epic: “CAUSAL perspectief uitbreidbaar maken”

Concreet geformuleerde User Stories, technisch genoeg om direct te implementeren

Duidelijke niet-doelen, zodat dit geen refactor-moeras wordt

Alles expliciet gericht op: nu één perspectief goed doen, later kunnen uitbreiden.

1. Bredere architectuur – op hoofdlijnen, functioneel
1.1 Architectuurprincipe (leidend)

Single Source of Truth

Neo4j bevat het canonieke graph-model

Frontend maakt projecties, geen kopieën van waarheid

Perspectief = projectie + interactieregels

Een perspectief:

selecteert een subset van de graph

hanteert eigen bewerkingen

toont eigen views

Views zijn vervangbaar

Een view (bijv. CLD-canvas) is:

geen eigenaar van data

geen eigenaar van layout

alleen een visualisatie-instrument

Layouts zijn puur technisch

Layouts:

kennen geen domein

kennen geen perspectief

werken op tijdelijke sessies

Dit is de minimale set principes die je uitbreidbaarheid borgt.

1.2 Frontend-architectuur (concreet, niet theoretisch)
Frontend
│
├─ App Shell
│   └─ Routing + globale context
│
├─ Perspective Layer
│   └─ CausalPerspective
│       ├─ GraphProjection
│       ├─ View Registry
│       └─ Interaction Rules
│
├─ View Layer
│   └─ CLDView
│       ├─ Canvas (React Flow)
│       └─ LayoutController
│
├─ Layout Layer
│   ├─ LayoutSession
│   ├─ ForceLayoutRunner
│   └─ SystemLayoutRunner
│
└─ Domain Contracts
    ├─ GraphNode
    ├─ GraphEdge
    └─ Ontology Types (UFO-aligned)


Belangrijk:

CAUSAL perspectief is één map

Andere perspectieven worden later kopieën van deze structuur

Geen gedeelde layout-logica tussen perspectieven

2. Wat betekent “CAUSAL perspectief” hier concreet

Het CAUSAL perspectief is:

gericht op oorzaak-gevolgrelaties

werkt met een CLD-view

gebruikt meerdere layouts om inzicht te geven

leest en schrijft causale claims in de graph

Niet meer, niet minder.

3. Epic: “CAUSAL perspectief uitbreidbaar inrichten”
Epic-doel

Als ontwikkelaar wil ik het CAUSAL perspectief zodanig structureren dat:

layouts volledig geïsoleerd zijn

views geen kennis hebben van andere perspectieven

een nieuw perspectief later kan worden toegevoegd zonder refactor van CAUSAL

4. User Stories (gegroepeerd, uitvoerbaar)
Epic CAUSAL-01 — Perspectiefstructuur expliciet maken
US-01.1 — CausalPerspective als expliciete module

Als ontwikkelaar
Wil ik dat het CAUSAL perspectief één duidelijk afgebakende module is
Zodat andere perspectieven later dezelfde structuur kunnen volgen

Acceptatiecriteria

CausalPerspective heeft:

eigen graph-projection

eigen view registry

Geen imports vanuit andere perspectieven

Geen layout-logica in deze laag

US-01.2 — GraphProjection voor CAUSAL

Als CAUSAL perspectief
Wil ik een expliciete projectie van nodes en edges
Zodat alleen causale elementen zichtbaar en bewerkbaar zijn

Acceptatiecriteria

Eén functie die:

Neo4j-resultaat → CausalGraph

Geen React Flow types in deze laag

Ontologie-types expliciet gebruikt

Epic CAUSAL-02 — Layouts isoleren via LayoutSession
US-02.1 — Introduceren van LayoutSession

Als layout-engine
Wil ik werken op een eigen LayoutSession
Zodat layouts elkaar niet beïnvloeden

Acceptatiecriteria

LayoutSession bevat:

lokale nodes

lokale edges

startposities

Elke layout-switch creëert een nieuwe session

Geen hergebruik van layout-state

US-02.2 — Force layout als onafhankelijke runner

Als gebruiker
Wil ik een force-based layout zien
Zodat clusters van causale verbanden zichtbaar worden

Acceptatiecriteria

ForceLayoutRunner:

kent geen React Flow

kent geen perspectief

Startposities worden bij session-creatie bepaald

Runner commit alleen position

US-02.3 — System layout als onafhankelijke runner

Als gebruiker
Wil ik een system layout zien
Zodat causale elementen logisch gepositioneerd zijn

Acceptatiecriteria

SystemLayoutRunner:

gebruikt dezelfde LayoutSession

geen D3-force verplicht

Wisselen van layout reset posities

Epic CAUSAL-03 — CLD View zuiver houden
US-03.1 — CLDView als renderer, niet als controller

Als ontwikkelaar
Wil ik dat CLDView alleen rendert
Zodat layout- en perspectieflogica elders blijft

Acceptatiecriteria

CLDView:

ontvangt nodes met posities

stuurt geen layout-events

Geen D3-code in CLDView

US-03.2 — LayoutController per view

Als CLDView
Wil ik één LayoutController
Zodat layouts verwisselbaar zijn

Acceptatiecriteria

LayoutController:

kiest runner op basis van layoutType

beheert session lifecycle

Geen kennis van Neo4j

Epic CAUSAL-04 — Voorbereiding op andere perspectieven (zonder ze te bouwen)
US-04.1 — Perspective contract vastleggen

Als ontwikkelaar
Wil ik een lichtgewicht contract voor perspectieven
Zodat een volgend perspectief hetzelfde patroon kan volgen

Acceptatiecriteria

Interface of type:

getProjection()

getViews()

CAUSAL implementeert dit contract

Geen generieke “PerspectiveEngine”

5. Niet-doelen (expliciet)

Om scope creep te voorkomen:

Geen variant-management

Geen conflictmodellering

Geen AI Agent integratie

Geen generieke “ecosysteem-engine”

Geen herontwerp van Neo4j-schema

Dit plan maakt ze mogelijk, maar implementeert ze niet.

6. Waarom dit werkt (en je tempo bewaart)

Je refactort structuur, niet gedrag

Je huidige CLD-functionaliteit blijft leidend

Je lost het layout-probleem fundamenteel op

Je creëert een herhaalbaar patroon voor:

waardenperspectief

stakeholderperspectief

oplossingsontwerp

Dit is exact de balans tussen:

architectuur als ruggengraat
en
code als voortgang
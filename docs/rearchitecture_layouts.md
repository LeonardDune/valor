Gezien jouw uitgebreide concept voor [VALOR](docs/VALOR-concept.md) en het [CAUSA-perspectief](docs/causa_concept.md), kan ik de architectuur en het implementatieplan expliciet afstemmen op CAUSA als perspectief binnen VALOR, inclusief de visie op uitbreidbaarheid naar andere perspectieven en layouts. Ik vat dit in een ontwikkelaarsvriendelijke structuur samen.

1. Bredere architectuur – VALOR ecosysteem
1.1 Overkoepelend systeem

VALOR is een platform dat:

Domeinoverstijgend werkt

Waardegedreven en expliciet normatief is

Menselijke samenwerking ondersteunt

Agents gebruikt als rolgebonden specialisten, geen hiërarchie, geen autonome beslissers

Principe:
Elke agent/perspectief werkt op een gedeelde graph (Neo4j), maar houdt zijn eigen subset en regels.

1.2 Perspectieven en agents

Een perspectief is een module waarin een groep mensen samenwerkt met een crew van AI agents.

Het perspectief:

selecteert een subset van de canonieke graph

bepaalt interactieregels voor de gebruikers

registreert beschikbare views (visualisaties)

bevat geen layout- of domeinlogica van andere perspectieven

CAUSA is een perspectief, andere perspectieven (AXIA, ACTOR, THEMIS, POLIS, PRAXIS, VALENS) volgen hetzelfde patroon.

1.3 Views

Views zijn puur visuele representaties van een perspectief-subset.

Ze hebben geen kennis van Neo4j of van andere perspectieven.

Ze ontvangen nodes + edges met posities van layouts.

Ze renderen, sturen interacties terug, maar voeren geen layout-berekeningen uit.

1.4 Layouts

Layouts zijn volledig geïsoleerde modules:

nemen een LayoutSession als input

manipuleren alleen tijdelijke node-posities

committen output naar de view

kennen geen perspectieven, geen andere layouts, geen Neo4j

Een perspectief kan oneindig veel layouts hebben, elk volledig onafhankelijk van andere layouts in hetzelfde perspectief of in andere perspectieven.

1.5 LayoutSession

Per run van een layout wordt een LayoutSession gecreëerd.

Bevat:

lokale nodes en edges (kopie van de geselecteerde subset)

startposities

layout-specifieke parameters

Is stateless, deterministisch en niet gedeeld.

Switch tussen layouts = nieuwe session, oude layouts blijven onaangetast.

1.6 Relaties tussen componenten
VALOR
 ├─ Perspectieven (CAUSA, AXIA, etc.)
 │    ├─ GraphProjection (subset van Neo4j)
 │    ├─ Views (CLDView, Lijst, Tabel)
 │    └─ LayoutController (LayoutSession -> LayoutRunner)
 │         └─ Layouts (Force, System, FeedbackLoop, ...)
 └─ Neo4j (single source of truth)


Perspectieven: organisatorisch en functioneel gescheiden

Views: visualisatie en interactie

Layouts: ordening en posities

Neo4j: alle data, hypothesen, claims, tegenstrijdigheden

1.7 Key design rules

Single source of truth: Neo4j bevat alle data. Perspectieven lezen en schrijven expliciet.

Layouts zijn plug-ins: volledig los van perspectieven en views.

Deterministisch: elke layout-run is volledig reproduceerbaar.

Extensible: nieuwe perspectieven of layouts worden toegevoegd zonder refactor van bestaande perspectieven of layouts.

Mens-in-de-loop: AI agents ondersteunen, dicteren niet.

2. Epic: “CAUSA-perspectief uitbreidbaar en robuust implementeren”

Doel:
Het CAUSA-perspectief zo inrichten dat het:

volledig zelfvoorzienend is

meerdere layouts kan hebben zonder elkaar te beïnvloeden

makkelijk uitbreidbaar is naar andere perspectieven en andere causal-analyse tools

2.1 User Stories
US-CAUSA-01 – Perspectiefmodulair

Als ontwikkelaar
Wil ik CAUSA implementeren als afzonderlijke module met eigen GraphProjection en Views
Zodat andere perspectieven later hetzelfde patroon kunnen volgen zonder refactor.

Acceptatiecriteria:

CausalPerspective module bevat GraphProjection, ViewRegistry, InteractionRules

Geen dependency op andere perspectieven

US-CAUSA-02 – LayoutSession per run

Als gebruiker of ontwikkelaar
Wil ik dat elke layout-run op een eigen LayoutSession draait
Zodat layouts onafhankelijk blijven en switchen layouts niet elkaar beïnvloedt.

Acceptatiecriteria:

LayoutSession bevat lokale kopieën van nodes en edges

Startposities worden bij elke layout-run opnieuw bepaald

Layouts committen alleen posities aan de view

US-CAUSA-03 – LayoutRunner interface

Als ontwikkelaar
Wil ik een gestandaardiseerde interface voor layouts
Zodat nieuwe layouts eenvoudig toegevoegd kunnen worden.

Acceptatiecriteria:

interface LayoutRunner {
  run(session: LayoutSession): LayoutResult;
}


Layouts zijn stateless en deterministisch

Layouts kennen geen perspectieven of andere layouts

US-CAUSA-04 – CLDView strikt renderer

Als ontwikkelaar
Wil ik dat CLDView alleen nodes en edges renderen
Zodat layout-logica volledig gescheiden blijft van visualisatie.

Acceptatiecriteria:

CLDView ontvangt nodes met posities

CLDView stuurt interacties terug

Geen D3-force code in de view

US-CAUSA-05 – Samenwerking en onzekerheid

Als gebruiker
Wil ik dat meerdere causal claims naast elkaar bestaan met status en zekerheid
Zodat menselijke deelnemers en AI agent samen exploreren.

Acceptatiecriteria:

Neo4j graph bevat CAUSAL_CLAIM met status, polariteit en zekerheid

UI toont visueel verschil tussen voorstellen, geaccepteerd en betwist

2.2 Niet-doelen pilot

Geen automatisering van causal discovery

Geen autonome AI-modellering

Geen beheer van meerdere perspectieven tegelijk (pilot beperkt tot CAUSA)

Geen complexe workflowregie of inter-perspectief integratie

3. Concreet implementatieplan (stapsgewijs)

Module-structuur opzetten

CausalPerspective module

GraphProjection, Views, LayoutController

Contract interface voor layouts

GraphProjection

subset van Neo4j voor causal claims

mapping naar interne node/edge-structuur

filter voor onzekerheid en status

Layout-infrastructuur

LayoutSession per run

LayoutRunner interface

ForceLayout en SystemLayout implementatie

CLDView

puur rendering

ontvangt node-posities

stuurt interacties terug

CAUSA-agent

stateless

input: graph subset + user event

output: suggesties, vragen, waarschuwingen

geen mutaties in Neo4j

Samenwerkingsscenario pilot

minimaal 2 gebruikers

causal loop met 3–5 factoren

agent detecteert loops en stelt vragen

Evaluatie en voorbereiding extensie

test: extra layout toevoegen

test: nieuwe causal claim types toevoegen

documenteer contracten voor toekomstige perspectieven


##Frontend architectuur voor AI Agents binnen VALOR ecosysteem

Goede en noodzakelijke vraag. Dit raakt precies het punt waar veel “AI-enabled” tools architectonisch ontsporen: agents die stilzwijgend overal tussendoor praten. Hier een nuchtere, uitbreidbare frontend-architectuur waarin AI Agents eerste-klas burgers zijn, zonder dat CAUSA of latere perspectieven vervuilen of refactors afdwingen.

Ik beschrijf eerst het conceptuele model, daarna de frontend-architectuur, en sluit af met concrete implicaties voor CAUSA nu.

1. Conceptueel model: wat is een AI Agent in VALOR?

Binnen VALOR is een AI Agent frontend-technisch géén:

chatbot in de marge

globale assistent

magische “achtergrondintelligentie”

Maar wél:

Een rolgebonden, perspectief-specifieke actor met expliciete interactiepunten en eigen UI-contracten.

Essentiële eigenschappen

Een AI Agent:

Is gebonden aan één perspectief

Heeft een afgebakende taak of rol

Interacteert via expliciete UI-kanalen

Produceert voorstellen, analyses of spanningen, geen mutaties

Is verwisselbaar en meervoudig

Dat laatste is cruciaal: meerdere agents tegelijk, zelfs met tegengestelde interpretaties.

2. Gevolg voor frontend-architectuur
Kernprincipe

Agents zijn geen features, maar participants.

Dat betekent: ze krijgen een structurele plek in de frontend-architectuur, vergelijkbaar met views en layouts.

3. Frontend-architectuur met Agents
3.1 Overzicht
Frontend
 ├─ PerspectiveShell (CAUSA)
 │    ├─ ViewArea
 │    │    └─ CLDView
 │    ├─ LayoutController
 │    ├─ AgentPanelRegion
 │    │    ├─ AgentUI (CausalAnalyst)
 │    │    ├─ AgentUI (LoopDetector)
 │    │    └─ AgentUI (DevilsAdvocate)
 │    └─ SharedEventBus


Belangrijk:

AgentUI is een first-class UI component

Meerdere AgentUI’s kunnen tegelijk actief zijn

AgentUI’s kennen geen layouts en geen views

3.2 AgentUI ≠ Chat

Een AgentUI is niet per definitie een chatinterface.

Mogelijke AgentUI-vormen:

Suggestiepanelen

Hypothese-lijsten

Spanningsmeldingen

Vragen aan gebruikers

Vergelijkingen tussen claims

Annotaties bij graph-elementen

Chat is slechts één mogelijke interactievorm.

4. Architectonisch patroon: Agent as View-Adjacent Component
4.1 Interfacecontract
interface PerspectiveAgent {
  id: AgentId;
  role: AgentRole;
  observe(events: PerspectiveEvent[]): AgentInput;
  produce(input: AgentInput): AgentOutput[];
}


Frontend vertaalt:

gebruikersacties

graph-events

layout-switches

naar PerspectiveEvents.

Agent produceert AgentOutputs, geen directe UI-mutaties.

4.2 AgentOutput types
type AgentOutput =
  | Suggestion
  | Question
  | ConflictSignal
  | PatternDetected
  | AnnotationProposal;


Frontend beslist:

waar dit zichtbaar wordt

hoe het wordt geprioriteerd

of het persistent wordt

Dit voorkomt agent-gedreven UI-chaos.

5. AgentPanelRegion: waarom een aparte regio?
Reden 1: uitbreidbaarheid

Nieuwe agent toevoegen = nieuwe panel

Geen impact op CLDView

Geen impact op Layouts

Geen impact op andere agents

Reden 2: normativiteit expliciet

Normatieve agents (bijv. “waardenwaakhond”) krijgen hun eigen zichtbare ruimte.

Geen vermenging van descriptief en normatief zonder expliciete confrontatie.

Reden 3: conflict is zichtbaar

Twee agents mogen elkaar tegenspreken.
Frontend faciliteert dat, maskeert het niet.

6. Events als bindmiddel
SharedEventBus (per perspectief)

Alle onderdelen publiceren en abonneren:

Views

LayoutController

AgentUIs

User interactions

type PerspectiveEvent =
  | NodeSelected
  | ClaimAdded
  | ClaimRejected
  | LayoutChanged
  | PerspectiveInitialized;


Agents luisteren mee, maar zijn passief totdat geactiveerd.

7. Wat verandert dit voor CAUSA nu?
7.1 Wat je NU moet doen

Zonder overengineering:

Reserveer structureel ruimte voor agents

AgentPanelRegion in CAUSA shell

Introduceer AgentUI als concept

ook al start je met één agent

Werk met PerspectiveEvents

ook al zijn het er eerst maar vijf

Laat agents alleen voorstellen doen

nooit direct muteren

7.2 Wat je NU expliciet niet doet

Geen globale chat

Geen agent die layout of graph direct wijzigt

Geen agent-logica in CLDView

Geen agent-specifieke code in layouts

8. User Stories – CAUSA Agents (toevoeging aan Epic)
US-CAUSA-AG-01 – AgentPanelRegion

Als gebruiker
Wil ik één of meerdere agentpanelen naast mijn CLD zien
Zodat analyses expliciet en vergelijkbaar blijven.

US-CAUSA-AG-02 – Meerdere agents tegelijk

Als gebruiker
Wil ik meerdere agents parallel kunnen activeren
Zodat verschillende interpretaties zichtbaar blijven.

US-CAUSA-AG-03 – AgentOutputs expliciet

Als ontwikkelaar
Wil ik dat agents alleen gestructureerde outputs leveren
Zodat UI-consistentie behouden blijft.

US-CAUSA-AG-04 – Normatief versus descriptief zichtbaar

Als gebruiker
Wil ik kunnen zien of een agent descriptief of normatief opereert
Zodat interpretaties niet onzichtbaar vermengd worden.

9. Waarom dit refactor-veilig is

CAUSA blijft leidend

Agents zijn plug-ins

Views blijven dumb

Layouts blijven stateless

Nieuwe perspectieven hergebruiken exact dit patroon

Je bouwt dus niet “AI erin”, maar AI ernaast, als mede-participant.
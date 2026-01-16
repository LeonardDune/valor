De AI Agent structuur wordt ingedeeld in meerdere agents per perspective, maar mogelijk ook zijn er globale agents op het VALOR ecosysteem niveau actief. Dat heeft uiteraard ook invloed op de backend. Ik wil voor de backend gebruik maken van CrewAI met LangChain. Schrijf een architectuur- en implementatieplan voor de backend. Is het handig dat elke agent zijn eigen set aan API's (FastAPI) heeft? Hoe moet dat dan met agent orchestratie?

Helder. Ik ga dit strak en uitvoerbaar neerzetten, met expliciete keuzes en trade-offs. Geen abstract agent-filosofie, maar een backend-architectuur die je morgen kunt bouwen en die meegroeit met VALOR zonder herontwerp.

Ik structureer dit als volgt:

Architectuurprincipes voor de VALOR-agent backend

Agentlandschap: globaal versus perspectief

CrewAI + LangChain: rolverdeling

API-architectuur: één API per agent of niet

Orchestratiepatroon (dit is het kernstuk)

Datastromen en state

Concreet implementatieplan (fasering)

1. Architectuurprincipes (leidend)

Voor de backend gelden deze harde principes:

Neo4j is single source of truth

Agents muteren nooit direct de graph

Agents werken via expliciete taken (Tasks), niet via chats

Orchestratie is expliciet, niet emergent

Perspectief-gebonden en globale agents zijn gescheiden verantwoordelijkheden

Frontend bepaalt wanneer agents actief worden, backend bepaalt hoe

Dit voorkomt een “agent-soep” waarin niemand nog begrijpt waarom iets gebeurt.

2. Agentlandschap
2.1 Twee agent-niveaus

Je hebt twee orthogonale assen:

As	Type
Scope	Perspectief-agent vs Globale agent
Rol	Analytisch, kritisch, synthetiserend, normatief
Perspectief-agents

Context: één perspectief (bijv. CAUSAL)

Input: perspectief-subset van de graph

Output: perspectief-specifieke analyses

Voorbeelden:

CausalAnalyst

LoopDetector

ClaimConsistencyChecker

Globale agents

Context: meerdere perspectieven

Input: meerdere graph-subsets + perspectief-annotaties

Output: spanningen, inconsistenties, alternatieven

Voorbeelden:

PerspectiveConflictAnalyzer

ValueTradeoffAgent

DesignVariantComparator

3. CrewAI en LangChain: taakverdeling
3.1 LangChain: cognitieve bouwstenen

Gebruik LangChain voor:

Prompt templates

Tool abstractions

Structured output parsing

Neo4j retrieval chains

Ontology-grounded context assembly

LangChain is per agent, niet globaal.

3.2 CrewAI: samenwerking en rolverdeling

CrewAI gebruik je voor:

Meerdere agents laten samenwerken

Expliciete taakverdeling

Controleerbare volgorde

Beperkte autonomie

Belangrijk:
Je gebruikt CrewAI niet als always-on orchestrator, maar per expliciete run.

Dus:

Geen langlevende crews

Geen impliciete triggers

4. API-architectuur: één API per agent?
Kort antwoord

Nee. Dat is niet handig.

Waarom niet

Te veel endpoints

Geen centrale autorisatie

Moeilijke observability

Orchestratie wordt verspreid

Agents worden “services” i.p.v. cognitieve rollen

5. Aanbevolen API-architectuur
5.1 Eén Agent Gateway (FastAPI)

Je bouwt één centrale FastAPI backend: de Agent Gateway.

Backend
 ├─ FastAPI Agent Gateway
 │    ├─ /perspectives/{id}/agents/run
 │    ├─ /global/agents/run
 │    ├─ /agents/status
 │    └─ /agents/history
 ├─ Agent Runtime
 ├─ Crew Orchestrator
 └─ Neo4j Access Layer


Agents zijn interne modules, geen publieke APIs.

5.2 Wat is een agent dan technisch?
agent/
 ├─ role.py
 ├─ tools.py
 ├─ prompts/
 ├─ policies.py
 └─ output_schema.py


Geen webserver. Geen HTTP. Geen state.

6. Orchestratie: dit is het kritieke ontwerpstuk
6.1 Orchestrator ≠ Agent

Je introduceert een Agent Orchestrator als aparte laag.

Verantwoordelijkheden:

Welke agents draaien?

In welke volgorde?

Met welke context?

Met welke beperkingen?

De orchestrator:

bevat geen LLM-logica

bevat geen domeinlogica

bevat alleen proceslogica

6.2 Orchestratiepatroon

Command-driven orchestration

Frontend stuurt expliciet een opdracht:

{
  "scope": "perspective",
  "perspective": "CAUSAL",
  "goal": "analyze_causal_structure",
  "agents": ["CausalAnalyst", "LoopDetector"],
  "constraints": {
    "maxDepth": 3,
    "normative": false
  }
}

6.3 CrewAI gebruik

De orchestrator bouwt per opdracht een Crew:

crew = Crew(
  agents=[causal_analyst, loop_detector],
  tasks=[analyze_structure_task, detect_loops_task],
  process=Process.sequential
)


Geen agent beslist zelf om iets te doen.

7. Datastromen
7.1 Inkomend

Frontend triggert agent run

Backend:

haalt graph-subset op

verrijkt met UFO-ontologie

voegt perspectief-metadata toe

7.2 Agent output

Agents leveren alleen gestructureerde output:

{
  "type": "ConflictSignal",
  "confidence": 0.82,
  "claims": ["c12", "c47"],
  "explanation": "...",
  "recommendation": "review"
}


Geen markdown blobs zonder schema.

7.3 Persistentie

Graph-wijzigingen: alleen na expliciete user-acceptatie

Agent output:

tijdelijk (session-bound)

optioneel opslaan als analyse-artifact

8. Globale agents en perspectieven

Globale agents:

draaien nooit automatisch

worden expliciet aangeroepen

krijgen meerdere perspectief-IDs als input

De orchestrator:

assembleert meerdere graph-views

labelt perspectief-bronnen

voorkomt semantische vermenging

9. Beveiliging en controle (kort maar essentieel)

Elke agent run:

krijgt een run-id

is reproduceerbaar

is auditeerbaar

Geen agent mag:

buiten zijn rol-context lezen

schrijven naar Neo4j

10. Implementatieplan (gefaseerd)
Fase 1 – Fundament

FastAPI Agent Gateway

Neo4j retrieval layer

Eén perspectief-agent (CAUSAL)

Geen CrewAI, single-agent runs

Fase 2 – Meerdere agents

Introduceer Agent Orchestrator

CrewAI per run

Gestructureerde output schemas

Agent history logging

Fase 3 – Globale agents

Multi-perspectief context assembly

Conflict agents

Vergelijkingsagents

Fase 4 – Schaal en betrouwbaarheid

Async execution

Timeouts

Partial results

Explainability logging

11. Antwoord op je kernvragen

Is het handig dat elke agent zijn eigen FastAPI heeft?
Nee. Dat schaalt slecht en breekt orchestratie.

Hoe moet het dan met agent orchestratie?
Via één expliciete orchestrator die per opdracht een Crew samenstelt. Geen autonome agentbeslissingen.

12. Samenvatting in één zin

Agents zijn cognitieve modules, geen services; orchestration is een expliciete backendverantwoordelijkheid, geen emergent gedrag.

Als volgende stap kan ik:

dit vertalen naar een concrete Python package-structuur

voorbeeldcode geven voor één CAUSAL-agent

of de Neo4j retrieval en UFO-grounding expliciet uitwerken

Geef aan waar je verder wilt verdiepen.

Ik ben nu bezig met:

US-CAUSA-AG-03 – AgentOutputs expliciet

Als ontwikkelaar
Wil ik dat agents alleen gestructureerde outputs leveren
Zodat UI-consistentie behouden blijft.

Hoe past dat hier in?

Dit past precies op een scharnierpunt in de architectuur dat je nu aan het neerzetten bent. US-CAUSA-AG-03 is geen “detail-user story”, maar een contract-story: je legt hier het fundament voor alle latere perspectieven en agents.

Ik plaats dit daarom expliciet in de architectuur, daarna maak ik het concreet en implementeerbaar voor CAUSA, zonder abstractie-opdrijving.

1. Waar past US-CAUSA-AG-03 in de architectuur?

Deze user story hoort niet primair bij CAUSA, maar bij de Agent Runtime Layer van VALOR.

Je introduceert hier een harde scheidslijn tussen:

agent reasoning

agent output als systeemartefact

Dat is essentieel omdat:

meerdere agents tegelijk actief kunnen zijn

meerdere perspectieven naast elkaar bestaan

de UI nooit agent-specifieke interpretatie mag bevatten

Architectuurlocatie
Backend
 ├─ FastAPI Agent Gateway
 ├─ Agent Orchestrator
 ├─ Agent Runtime
 │    ├─ Output Contracts   ← HIER
 │    ├─ Output Validation
 │    └─ Output Normalization
 └─ Neo4j Access Layer


US-CAUSA-AG-03 definieert het Output Contract-mechanisme.

2. Wat bedoelen we exact met “gestructureerde output”?

Niet: “JSON in plaats van tekst”.
Wel: semantisch getypeerde output met expliciete bedoeling.

Dus:

elk agent-resultaat heeft een type

dat type is UI-onafhankelijk

dat type is perspectief-gebonden maar uitbreidbaar

3. Output als first-class concept

Je introduceert één kernconcept:

AgentOutput = Typed, Validated, Interpretable Artifact

Minimale interface
class AgentOutput(BaseModel):
    output_type: str
    perspective: str
    confidence: float
    payload: dict
    meta: OutputMeta


Maar dit is slechts het container-niveau.

4. CAUSA-specifieke Output Types

Voor CAUSA definieer je een beperkte canon. Niet generiek, niet exhaustief.

4.1 Voorbeeld: ontbrekende schakel
class MissingLinkSignal(BaseModel):
    output_type: Literal["missing_link"]
    perspective: Literal["CAUSAL"]
    confidence: float
    source_factor_id: str
    target_factor_id: Optional[str]
    rationale: str
    supporting_claims: list[str]

4.2 Voorbeeld: mogelijke feedback loop
class FeedbackLoopHypothesis(BaseModel):
    output_type: Literal["feedback_loop"]
    perspective: Literal["CAUSAL"]
    loop_type: Literal["reinforcing", "balancing"]
    factor_ids: list[str]
    certainty: Literal["low", "medium", "high"]
    explanation: str

4.3 Voorbeeld: inconsistentie
class CausalInconsistency(BaseModel):
    output_type: Literal["inconsistency"]
    claim_ids: list[str]
    inconsistency_type: Literal["polarity", "direction", "certainty"]
    explanation: str

5. Wat mag een agent niet doen?

Dit hoort expliciet in US-CAUSA-AG-03:

Geen vrije tekst zonder schema

Geen UI-instructies

Geen Neo4j IDs verzinnen

Geen gecombineerde outputs in één blob

Geen impliciete normativiteit

De agent mag:

meerdere outputs produceren

maar altijd als lijst van getypeerde artefacten

6. Hoe afdwingen in de runtime?
6.1 Validatie

Elke agent run eindigt met:

validated_outputs = OutputValidator.validate(
    raw_output,
    allowed_types=CAUSA_OUTPUT_TYPES
)


Bij falen:

agent-run faalt hard

output wordt niet doorgegeven aan frontend

fout is zichtbaar voor developer, niet voor gebruiker

6.2 Normalisatie

Je normaliseert niet inhoud, maar vorm:

confidence altijd [0.0 – 1.0]

certainty enums geharmoniseerd

factor_ids altijd expliciet

7. Wat betekent dit voor de frontend?

De frontend:

rendert op output_type

kent geen agents

kent geen prompts

kent geen reasoning-steps

Bijvoorbeeld:

switch (output.output_type) {
  case "feedback_loop":
    renderLoopSuggestion(output)
  case "missing_link":
    renderMissingLink(output)
}


Dit maakt:

meerdere agents tegelijk mogelijk

meerdere perspectieven tegelijk mogelijk

nieuwe agents zonder UI-refactor mogelijk

8. Relatie tot CrewAI en LangChain
LangChain

dwingt structured output af via:

PydanticOutputParser

JSON schema prompts

CrewAI

elke Task heeft:

expected_output schema

expliciet doel

Geen Task zonder schema.

9. Hoe herschrijf je US-CAUSA-AG-03 iets scherper?

Je huidige user story is goed, maar ik zou hem iets technischer en afdwingender formuleren:

US-CAUSA-AG-03 – Agent Outputs als getypeerde artefacten

Als ontwikkelaar
Wil ik dat elke CAUSA-agent uitsluitend vooraf gedefinieerde, gevalideerde output-types retourneert
Zodat frontend-visualisatie perspectief-onafhankelijk en uitbreidbaar blijft.

Acceptatiecriteria (voorbeeld)

 Elke agent output valideert tegen een Pydantic schema

 Elke output heeft een output_type en perspective

 Vrije tekst zonder schema wordt geweigerd

 Frontend gebruikt geen agent-naam of prompt-kennis

 Nieuwe output-types vereisen geen refactor van bestaande types

10. Waarom dit strategisch belangrijk is

Dit voorkomt dat VALOR:

een chatbot met diagrammen wordt

een agent-gedreven UI krijgt

vastloopt bij het tweede perspectief

Je zet hier feitelijk het equivalent neer van:

een AST in een compiler

een IR in een model-driven tool

een partituur i.p.v. improvisatie
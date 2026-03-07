# VALOR-O Implementatieplan
## Van ontologie-repo naar werkend ecosysteem

**Versie** | 0.1
**Datum** | maart 2026
**Status** | Concept — ter besluitvorming
**Relatie** | Uitwerking van Hoofdstuk 8 (Technische Architectuur) en Hoofdstuk 12 (Onderzoeksworkstream) van valor-ecosystem20.md

---

## 1. Uitgangspunten

### 1.1 Wat er is

De [valor-ontology repo](https://github.com/LeonardDune/valor-ontology) bevat negen TriG-modules (v0.1–v0.2) die de funderende lagen van VALOR-O implementeren:

| Module | Laag | Status |
|--------|------|--------|
| `00a-gufo-core` | Laag 1 — gUFO | Volledig, stabiel |
| `00b-ufo-b` | Laag 2 — Events/causaliteit | Volledig |
| `00c-ufo-c` | Laag 2 — Sociale entiteiten | Volledig |
| `00d-ufo-l` | Laag 2 — Rechtsbetrekkingen | Volledig |
| `00e-coodm` | Laag 2 — Besluitvorming + COVER basis | Volledig |
| `00f-cover` | Laag 2 — COVER uitbouw | Volledig |
| `00g-acta` | Laag 2 — DEMO-transacties | Volledig |
| `00h-causa` | Laag 2/3 — CLD-ontologie | Goed, maar lacunes |
| `00i-socia` | Laag 2/3 — Actor analysis | Aanwezig |

SHACL-shapes en een VoID-catalogus zijn aanwezig voor alle modules.

De bestaande VALOR-applicatie (FastAPI + Neo4j + React) heeft een datamodel dat direct mapt op VALOR-O:

| Huidig VALOR | VALOR-O |
|--------------|---------|
| `Factor` | `causa:CausalVariable` |
| `Claim` (edge + polariteit) | `causa:CausalClaim` + `causa:CausalSituation` |
| `Theme` / `ThemeVersion` | `valor:DesignSpace` / `valor:DesignPhase` |
| Deliberation (refine→ranking→consent) | `valor:DecisionEpisode` |
| `confidence` op Claim | `causa:hasUncertaintyLevel` |
| `evidence` op Claim | `causa:Evidence` |

### 1.2 Wat er ontbreekt

**Structurele hiaten:**

1. **Laag 3 — Epistemische module**: geen `valor:Tessera` als cross-cuttend concept; geen 5-waardige statusmachine (Contested en Reconsidered ontbreken); geen argumentatierelaties; geen `valor:DecisionEpisode`.
2. **Laag 4 — Toepassingsontologie**: geen `valor:DesignSpace`, `valor:DesignPhase`, `valor:DesignAlternative`, `valor:Participant`.
3. **Ontbrekende perspectief-modules**: Axia (apart van COVER), Delibera, Forma.
4. **`valor:Issue` verkeerd gepositioneerd**: staat in `00h-causa`, hoort in Laag 4.
5. **Per-module claim-klassen zijn niet verbonden**: `causa:CausalClaim` is geen subklasse van een centrale `valor:Tessera`.

### 1.3 Principes voor deze implementatie

- **Architectonische zuiverheid boven pragmatisch gemak**: centrale `valor:Tessera` met module-specifieke claim-klassen als subklassen.
- **Frontend hergebruik maximaliseren**: bestaande React-componenten worden adapters voor VALOR-O perspectieven.
- **Gelaagde migratie**: FastAPI blijft de API-laag; GraphDB/Fuseki vervangt Neo4j als semantische store; Neo4j blijft tijdelijk voor operationele data.
- **Alles open source en gratis**: geen commerciële licenties vereist.

---

## 2. Triplestore-keuze: Apache Jena Fuseki

### 2.1 Waarom Fuseki, niet GraphDB Free

GraphDB Free mist OWL reasoning — dit is een **harde vereiste** voor VALOR (SHACL-validatie bij faseovergangen, Forma-perspectief, feedback-loop detectie). GraphDB Enterprise is commercieel.

**Apache Jena Fuseki** is de juiste keuze:

| Vereiste | Fuseki |
|----------|--------|
| SPARQL 1.1 (incl. property paths) | ✅ Volledig |
| Named graphs per Design Space | ✅ Jena Datasets |
| SHACL-validatie | ✅ `jena-shacl` module |
| OWL EL reasoning (real-time) | ✅ ELK reasoner (free Java library) |
| OWL DL reasoning (fase-overgangen) | ✅ HermiT (free Java library) |
| Vrij en open source | ✅ Apache License 2.0 |

### 2.2 Architectuur van de reasoning-stack

```
┌──────────────────────────────────┐
│  Apache Jena Fuseki              │
│  (SPARQL endpoint, named graphs, │
│   SHACL via jena-shacl)          │
└────────────┬─────────────────────┘
             │ Jena API
┌────────────▼─────────────────────┐
│  Reasoning microservice (Java)   │
│  ┌─────────────┐ ┌─────────────┐ │
│  │  ELK        │ │  HermiT     │ │
│  │  (OWL EL)   │ │  (OWL DL)   │ │
│  │  real-time  │ │  asynchroon │ │
│  └─────────────┘ └─────────────┘ │
└──────────────────────────────────┘
```

ELK draait continu voor incrementele inferentie tijdens modelleren. HermiT wordt asynchroon aangeroepen bij faseovergangen en op verzoek vanuit Forma.

### 2.3 Named graph structuur

Per Design Space (één per voormalige ThemeVersion):

```
valor:{designspace}/ontology    → VALOR-O basis (read-only, gedeeld)
valor:{designspace}/asis        → gedeelde as-is Tesserae
valor:{designspace}/alt/{id}    → to-be Tesserae per alternatief
valor:{designspace}/decisions   → DecisionEpisodes + stemhistorie
valor:{designspace}/agents      → AgentTesserae (vragen, suggesties)
valor:{designspace}/provenance  → PROV-O provenance records
```

---

## 3. Ontologie: benodigde wijzigingen

### 3.1 Nieuwe bestanden

#### `00j-tessera.trig` — Laag 3: Epistemische module

De centrale Tessera-klasse die alle perspectief-claims verenigt.

**Kerninhoud:**

```turtle
# Namespace: https://valor-ecosystem.nl/ontology/tessera# (prefix tess:)
# Imports: 00a-gufo-core, 00c-ufo-c

valor:Tessera
    a owl:Class ;
    rdf:type gufo:SubKind ;
    rdfs:subClassOf ufoc:Belief ;
    # Een reïficatie van een statement over de werkelijkheid.
    # Elke module-specifieke claim (causa:CausalClaim, socia:StakeholderClaim, enz.)
    # is een subklasse van valor:Tessera.
```

**Properties op Tessera:**

| Property | Type | Toelichting |
|----------|------|-------------|
| `valor:claimType` | `valor:ClaimType` (AsIs \| ToBe) | Huidig vs. gewenst |
| `valor:epistemicStatus` | `valor:EpistemicStatus` | 5-waardige machine (zie §3.3) |
| `valor:claimedBy` | `ufoc:Agent` | Auteur (menselijk of AI) |
| `valor:claimedAt` | `xsd:dateTime` | Tijdstempel |
| `valor:inAlternative` | `valor:DesignAlternative` | Optioneel; anders geldig in alle alternatieven |
| `valor:inPhase` | `valor:DesignPhase` | De fase waarin de claim is gemaakt |
| `valor:hasEvidence` | `valor:Evidence` | Ondersteunend/weerleggend bewijs |
| `valor:supports` | `valor:Tessera` | Argumentatierelatie |
| `valor:undermines` | `valor:Tessera` | Argumentatierelatie |
| `valor:qualifies` | `valor:Tessera` | Argumentatierelatie |
| `valor:presupposes` | `valor:Tessera` | Argumentatierelatie |

**Epistemische statusmachine (5-waardig):**

```
                    ┌─────────────┐
                    │  Proposed   │◄──────────────────┐
                    └──────┬──────┘                   │
                           │                    Reconsidered
               ┌───────────┼───────────┐              │
               ▼           ▼           ▼              │
          ┌─────────┐ ┌─────────┐ ┌──────────┐        │
          │Contested│ │Accepted │ │ Rejected │────────►┘
          └────┬────┘ └─────────┘ └──────────┘
               │
     ┌─────────┴─────────┐
     ▼                   ▼
┌─────────┐         ┌──────────┐
│Accepted │         │ Rejected │
└─────────┘         └──────────┘
```

Status-instanties: `valor:ProposedStatus`, `valor:ContestedStatus`, `valor:AcceptedStatus`, `valor:RejectedStatus`, `valor:ReconsideredStatus`.

**valor:Evidence:**

```turtle
valor:Evidence
    rdfs:subClassOf ufoc:SocialObject ;
    # EvidenceType: Empirical | Theoretical | Expert | Experiential
    # evidenceStrength: xsd:decimal (0.0–1.0)
    # evidenceSource: xsd:anyURI
```

**valor:DecisionEpisode:**

```turtle
valor:DecisionEpisode
    rdfs:subClassOf gufo:Event ;
    # Deelnemende agents (Participants), tijdstip
    # hasVote → valor:Vote (IntrinsicMode van een Participant)
    # Uitkomst: welke Tesserae aangenomen/verworpen
    # episodeType: PhaseTransition | InSessionVoting | AsyncVoting
```

---

#### `00k-application.trig` — Laag 4: VALOR Toepassingsontologie

**Namespace:** `https://valor-ecosystem.nl/ontology/application#` (prefix: `app:`)
**Imports:** 00a-gufo-core, 00c-ufo-c, 00j-tessera

**Kernklassen:**

```turtle
# valor:Issue — verplaatst vanuit 00h-causa
valor:Issue
    rdfs:subClassOf ufoc:SocialObject ;
    # Constituted by: gedeeld ufoc:Concern van een gemeenschap over een gufo:Situation
    # hasConcernedAgent, concernedWithSituation, hasDesignSpace

# valor:DesignSpace
valor:DesignSpace
    rdf:type gufo:Kind ;
    rdfs:subClassOf gufo:FunctionalComplex ;
    # Bevat: alle Tesserae, fases, alternatieven, deelnemers voor één Issue
    # hasIssue, hasPhase, hasParticipant, hasAlternative

# valor:DesignPhase
valor:DesignPhase
    rdf:type gufo:SubKind ;
    rdfs:subClassOf gufo:Situation ;
    # temporele begrenzing (beginPoint, endPoint)
    # phaseStatus: Active | Closed | Archived
    # phaseModel: DesignThinking | DoubleDiamond | Agile | PolicyCycle
    # hasPhaseTransition → valor:PhaseTransition

# valor:PhaseTransition (specialisatie van valor:DecisionEpisode)
valor:PhaseTransition
    rdfs:subClassOf valor:DecisionEpisode ;
    # Formeel besluitvormingsmoment dat de Design Space naar de volgende fase brengt

# valor:DesignAlternative
valor:DesignAlternative
    rdf:type gufo:SubKind ;
    rdfs:subClassOf gufo:Situation ;
    # Geïmplementeerd als named graph in Fuseki
    # alternativeStatus: Active | Selected | Archived
    # sharesAsisGraph → valor:DesignSpace (gedeelde as-is graph)

# valor:Participant
valor:Participant
    rdf:type gufo:Role ;
    rdfs:subClassOf ufoc:Agent ;
    # Rol is context-afhankelijk per DesignSpace
```

**Participant-rollen** (elk als `«role»` subklasse van `valor:Participant`):

| Rol | Stem | Schrijf | Tessera | Forma | Toelichting |
|-----|------|---------|---------|-------|-------------|
| `valor:Initiator` | ja | ja | ja | nee | Governance-config |
| `valor:Facilitator` | nee | procedureel | nee | nee | Sessiebegeleid |
| `valor:Contributor` | ja | ja | ja | nee | Primaire rol |
| `valor:Expert` | nee | ja | ja | nee | Geen stemrecht |
| `valor:Observer` | nee | nee | nee | lees | Alleen lezen |
| `valor:Engineer` | nee | ja | ja | ja | Technische validatie |

---

### 3.2 Wijzigingen in bestaande modules

#### `00h-causa.trig` — drie aanpassingen

1. **`valor:Issue` verwijderen** — verplaatst naar `00k-application.trig`. Import van `00k` toevoegen.
2. **`causa:CausalClaim` als subklasse van `valor:Tessera`**:
   ```turtle
   causa:CausalClaim
       rdfs:subClassOf valor:Tessera ;    # nieuw
       rdfs:subClassOf ufoc:Belief ;      # behouden
   ```
3. **Eigen `causa:EpistemicStatus` verwijderen** — gebruik `valor:epistemicStatus` van de centrale Tessera. De drie status-instanties (`causa:ProposedStatus` enz.) worden vervangen door de vijf in `00j-tessera`.

#### `00i-socia.trig` — zelfde patroon als causa

De stakeholder-claim klasse (nog te controleren in de module) krijgt `rdfs:subClassOf valor:Tessera`. Eigen statusmachine verwijderen.

#### `00g-acta.trig`, `00e-coodm.trig` — import aanpassen

`owl:imports <https://valor-ecosystem.nl/ontology/tessera>` toevoegen zodat de modules de Tessera-klasse kunnen gebruiken in hun claim-subklassen.

---

### 3.3 Nieuwe perspectief-modules

#### `00l-axia.trig` — Axia (waardeperspectief)

**Namespace:** `axia:`
**Imports:** 00f-cover, 00j-tessera, 00k-application

Axia bouwt bovenop COVER (al geïmplementeerd). De module voegt toe:

```turtle
axia:ValueClaim
    rdfs:subClassOf valor:Tessera ;
    # Een Tessera die een waarde-implicatie beschrijft van een ontwerpelement
    # hasValueType → cover:ValueType
    # claimPolarity → axia:SupportsClaim | axia:UnderminsClaim

axia:ValueTensionClaim
    rdfs:subClassOf valor:Tessera ;
    # Beschrijft een spanning tussen twee ValueTypes in een gegeven context
    # involvesTension → cover:ValueTension (al in 00e-coodm)

axia:DesignImplication
    rdfs:subClassOf gufo:Relator ;
    # Verbindt een Tessera (ontwerpkeuze) met de ValueType(s) die ze beïnvloedt
    # mediates: valor:Tessera ↔ cover:ValueType
```

#### `00m-delibera.trig` — Delibera (besluitvormingsperspectief)

**Namespace:** `delib:`
**Imports:** 00j-tessera, 00k-application, 00e-coodm

```turtle
delib:ArgumentationNetwork
    rdfs:subClassOf gufo:Situation ;
    # Samenhangende verzameling Tesserae + argumentatierelaties
    # hasRootTessera → valor:Tessera
    # forDesignSpace → valor:DesignSpace

delib:Vote
    rdfs:subClassOf gufo:IntrinsicMode ;
    # Positie van een Participant t.a.v. een Tessera
    # votePosition: Accept | Reject | Defer
    # castBy → valor:Participant
    # forTessera → valor:Tessera
    # isAnonymous → xsd:boolean

delib:AgentTessera
    rdfs:subClassOf valor:Tessera ;
    # Claim van een Socratische Agent
    # agentType: Causa | Lexa | Acta | Socia | Axia | Delibera | Forma
    # isQuestion → xsd:boolean
```

#### `00n-forma.trig` — Forma (ontologisch perspectief)

**Namespace:** `forma:`
**Imports:** 00a-gufo-core, 00j-tessera

Forma is primair een query-perspectief; de module formaliseert de OntoUML-annotaties als VALOR-O klassen zodat ze bevraagbaar zijn via SPARQL.

```turtle
forma:OntologicalElement
    rdfs:subClassOf gufo:FunctionalComplex ;
    # Elk klasse/property-element in de VALOR-O graph als bevraagbare entiteit
    # stereotype → valor:ontoumlStereotype (al gedeclareerd in 00a)
    # validationStatus: Valid | Warning | Error

forma:EngineerTessera
    rdfs:subClassOf valor:Tessera ;
    # Technisch bezwaar van een Engineer
    # violatesConstraint → sh:NodeShape (referentie naar SHACL-shape)
```

---

### 3.4 SHACL-shapes uitbreiden

Voor elke nieuwe module wordt een corresponderende SHACL-shapes file aangemaakt:

- `00j-tessera.shacl.trig` — verplichte properties, statusmachine-constraints
- `00k-application.shacl.trig` — DesignSpace vereist minimaal 1 Issue en 1 Participant
- `00l-axia.shacl.trig`, `00m-delibera.shacl.trig`, `00n-forma.shacl.trig`

**Kritieke shapes voor 00j-tessera:**
- `T1`: elke Tessera heeft precies 1 `valor:epistemicStatus`
- `T2`: elke Tessera heeft precies 1 `valor:claimedBy` (Agent)
- `T3`: elke Tessera heeft precies 1 `valor:claimedAt` (dateTime)
- `T4`: `valor:claimType` is verplicht (AsIs of ToBe)
- `T5`: `valor:undermines`/`valor:supports` mogen niet circulair zijn (SPARQL-based constraint)
- `T6`: Tessera met status `Accepted` of `Rejected` vereist link naar een `valor:DecisionEpisode`

---

## 4. API-laag: FastAPI modernisering

### 4.1 Architectuur

FastAPI blijft de API-laag. Neo4j blijft tijdelijk voor auth en sessies. Fuseki wordt de semantische store.

```
┌──────────────────────────────────────────────────────┐
│  React Frontend (bestaand + nieuwe perspectief-UIs)  │
└─────────────────────────┬────────────────────────────┘
                          │ REST + WebSocket
┌─────────────────────────▼────────────────────────────┐
│  FastAPI Backend                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────┐  │
│  │  Tessera API  │  │  SPARQL proxy │  │ Auth/IAM │  │
│  │  /tessera/    │  │  /sparql/     │  │ Supabase │  │
│  └───────┬───────┘  └───────┬───────┘  └──────────┘  │
│          │                  │                         │
│  ┌───────▼──────────────────▼──────┐  ┌───────────┐  │
│  │  GraphDB/Fuseki adapter          │  │  Reasoner │  │
│  │  (SPARQLWrapper)                 │  │  service  │  │
│  └──────────────────────────────────┘  └───────────┘  │
└──────────┬───────────────────────────────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐  ┌──────────┐
│ Fuseki │  │  Neo4j   │
│(VALOR-O│  │(auth,    │
│ data)  │  │ sessions)│
└────────┘  └──────────┘
```

### 4.2 Nieuwe routes

#### Tessera API (`/tessera/`)

| Methode | Route | Functie |
|---------|-------|---------|
| `POST` | `/tessera/` | Nieuwe Tessera aanmaken (schrijft naar Fuseki) |
| `GET` | `/tessera/{id}` | Tessera ophalen met metadata |
| `PATCH` | `/tessera/{id}/status` | Epistemische status wijzigen (vereist DecisionEpisode) |
| `POST` | `/tessera/{id}/evidence` | Bewijs toevoegen |
| `POST` | `/tessera/{id}/argue` | Argumentatierelatie leggen (supports/undermines/qualifies/presupposes) |

De Tessera API is de **enige schrijfroute** naar Fuseki. Alle perspectief-specifieke routes converteren intern naar Tessera-aanroepen.

#### SPARQL Proxy (`/sparql/`)

| Methode | Route | Functie |
|---------|-------|---------|
| `GET` | `/sparql/query` | SPARQL SELECT/CONSTRUCT (readonly) |
| `POST` | `/sparql/query` | Idem, voor langere queries |

De proxy voegt automatisch toegangscontrole toe: een Participant ziet alleen de named graphs van de DesignSpaces waarvoor hij uitgenodigd is.

#### Design Space API (`/designspace/`)

| Methode | Route | Functie |
|---------|-------|---------|
| `POST` | `/designspace/` | Nieuwe DesignSpace aanmaken (+ named graphs initialiseren in Fuseki) |
| `POST` | `/designspace/{id}/phase/transition` | Faseovergang uitvoeren (triggert HermiT-check + DecisionEpisode) |
| `GET` | `/designspace/{id}/perspective/{name}` | SPARQL-projectie voor een perspectief ophalen |

### 4.3 Bestaande routes als adapters

De bestaande routes voor Factors en Claims worden adapters die intern Tessera-aanroepen doen. Zo blijft de bestaande frontend werken zonder wijzigingen tijdens de migratie:

```python
# Bestaande route — nu een adapter
@app.post("/themes/{theme_id}/factors")
async def create_factor(factor_data: FactorCreate, ...):
    # Converteert naar: causa:CausalVariable + causa:CausalClaim via Tessera API
    tessera = await tessera_service.create(
        type="causa:CausalVariable",
        claimType="AsIs",
        content=factor_data,
        designSpace=theme_id
    )
    # Schrijft ook naar Neo4j voor backwards compatibility
    return await crud.create_factor(...)
```

---

## 5. Frontend: hergebruik en uitbreiding

### 5.1 Bestaande componenten — directe mapping

| Bestaande component | VALOR-O perspectief | Aanpassing |
|--------------------|---------------------|------------|
| `ValorWorkspace.tsx` | **Causa** | Minimaal: toon epistemische status per node, voeg Contested/Reconsidered toe |
| `RefinementBoard.tsx` | **Delibera** (fase 1) | Hernoemen + koppelen aan DecisionEpisode |
| `RankingBoard.tsx` | **Delibera** (fase 2) | Idem |
| `ConsentBoard.tsx` | **Delibera** (fase 3) | Idem |
| `MemberManagement.tsx` | Participant-beheer | Rollen uitbreiden naar 6 VALOR-O rollen |
| D3 force layout (`useForceLayout.ts`) | Causa + Socia | Behouden |

### 5.2 Nieuwe perspectief-modules

Elke module is een zelfstandige React-component die via de SPARQL proxy zijn data ophaalt. Volgorde van prioriteit:

**Prioriteit 1 — Causa uitbreiden** (bestaande workspace)
- Epistemische status per node visualiseren (groen/geel/oranje/rood conform §11.3 plan)
- "Betwist deze claim"-knop → `valor:ContestedStatus` + argumentatierelatie
- As-is / To-be toggle per element

**Prioriteit 2 — Socia perspectief**
- Stakeholderkaart op basis van `socia:`-queries
- Actor nodes, interesse/doel-wolken, afhankelijkheidspijlen
- SPARQL-projectie: `SELECT ?actor ?interest ?dependency WHERE { ... }`

**Prioriteit 3 — Delibera perspectief**
- Argumentatiediagram (IBIS-stijl) op basis van `delib:ArgumentationNetwork`
- Tijdlijn van DecisionEpisodes
- Steminterface die schrijft via `/tessera/{id}/status`

**Prioriteit 4 — Axia perspectief**
- Waardencanvas op basis van `axia:`-queries over COVER
- Heatmap-overlay: welke Tesserae raken welke ValueTypes

**Prioriteit 5 — Forma perspectief**
- OntoUML-diagram op basis van `forma:`-queries
- Monaco Editor voor SPARQL
- SHACL-validatierapport

**Prioriteit 6 — Lexa en Acta**
- Lexa: normenkaart op basis van `00d-ufo-l`
- Acta: transactiediagram op basis van `00g-acta`

### 5.3 State management

Bestaande context (`OrganizationContext`, `ThemeContext`, `AuthContext`) wordt uitgebreid:

- `OrganizationContext` → `DesignSpaceContext` (mapt ThemeVersion op DesignSpace)
- Nieuw: `TesseraContext` — houdt epistemische status bij per element (React Query cache op `/tessera/`)
- Nieuw: `PerspectiveContext` — actief perspectief per DesignSpace

---

## 6. Implementatiefasen

### Fase 0: Voorbereiding (2 weken)

**Ontologie:**
- [ ] `valor:Issue` verplaatsen vanuit `00h-causa` naar nieuw `00k-application.trig`
- [ ] `causa:EpistemicStatus` in `00h-causa` deprecaten (marked als `owl:deprecated`)
- [ ] Design Decision DD-061 schrijven: keuze voor centrale `valor:Tessera` boven per-module status

**Infrastructuur:**
- [ ] Apache Jena Fuseki deployen (Docker) op VPS via Coolify
- [ ] ELK reasoner integreren als Java sidecar
- [ ] HermiT integreren als async Java service
- [ ] VALOR-O TriG-bestanden laden in Fuseki (bestaande 9 modules)
- [ ] VoID catalogus bijwerken met Fuseki endpoint

---

### Fase 1: Laag 3 — Tessera module (3 weken)

**Ontologie:**
- [ ] `00j-tessera.trig` schrijven (centrale Tessera-klasse, 5-waardige statusmachine, argumentatierelaties, DecisionEpisode)
- [ ] `00j-tessera.shacl.trig` schrijven (constraints T1–T6)
- [ ] `00h-causa.trig` updaten: CausalClaim subclasseert Tessera, eigen status verwijderen
- [ ] `00i-socia.trig` updaten: socia-claims subclasseert Tessera
- [ ] Alle TriG-bestanden laden in Fuseki, SHACL-validatie draaien

**API:**
- [ ] `app/services/fuseki.py` — SPARQLWrapper adapter naar Fuseki
- [ ] `app/routers/tessera.py` — Tessera API routes (POST, GET, PATCH status, POST evidence, POST argue)
- [ ] Bestaande Factor/Claim routes als adapters naar Tessera API

**Test:**
- [ ] Bestaand Factor aanmaken → verschijnt als `causa:CausalClaim` in Fuseki
- [ ] Epistemic status wijzigen → DecisionEpisode aangemaakt
- [ ] SHACL-validatie passeert op aangemaakt data

---

### Fase 2: Laag 4 — Application Ontologie (2 weken)

**Ontologie:**
- [ ] `00k-application.trig` schrijven (DesignSpace, DesignPhase, DesignAlternative, Participant + 6 rollen)
- [ ] `00k-application.shacl.trig` schrijven
- [ ] Laden in Fuseki

**API:**
- [ ] `app/routers/designspace.py` — DesignSpace routes + named graph initialisatie in Fuseki
- [ ] `app/routers/sparql.py` — SPARQL proxy met toegangscontrole
- [ ] Bestaande ThemeVersion migratiescript → DesignSpace + named graphs

**Test:**
- [ ] Bestaande ThemeVersions zijn bevraagbaar als DesignSpaces via SPARQL
- [ ] Named graphs per DesignSpace aanwezig in Fuseki

---

### Fase 3: Causa-perspectief uitbreiden (2 weken)

**Ontologie:**
- [ ] `00h-causa.trig` v0.3: Contested + Reconsidered statussen toevoegen; FeedbackLoop SPARQL-detectie documenteren

**Frontend:**
- [ ] Epistemische status visualisatie in `ValorWorkspace.tsx` (kleurcodering per node/edge)
- [ ] "Betwist"-knop → ContestedStatus + argumentatierelatie
- [ ] As-is / To-be toggle

**Test:**
- [ ] End-to-end: Factor aanmaken → Tessera in Fuseki → status in UI zichtbaar
- [ ] Betwisten van een Claim → ContestedStatus correct opgeslagen

---

### Fase 4: Delibera-perspectief (3 weken)

**Ontologie:**
- [ ] `00m-delibera.trig` + shapes schrijven en laden

**API:**
- [ ] DecisionEpisode routes (stemmen, afsluiten, heroverweging initiëren)
- [ ] Bestaande deliberation routes als adapters naar nieuwe DecisionEpisode structuur

**Frontend:**
- [ ] `DeliberaView.tsx` — argumentatiediagram + DecisionEpisode tijdlijn
- [ ] Bestaande Refinement/Ranking/ConsentBoards koppelen aan `valor:DecisionEpisode`

---

### Fase 5: Axia en Socia-perspectieven (4 weken)

- [ ] `00l-axia.trig` + frontend `AxiaView.tsx`
- [ ] `00i-socia.trig` v0.2 (i* integratie) + frontend `SociaView.tsx`

---

### Fase 6: Lexa, Acta, Forma (6 weken)

- [ ] `LexaView.tsx` op basis van `00d-ufo-l`
- [ ] `ActaView.tsx` op basis van `00g-acta`
- [ ] `00n-forma.trig` + `FormaView.tsx` met Monaco SPARQL-editor + SHACL-rapport

---

### Fase 7: Neo4j afbouwen

Zodra alle schrijfoperaties via Fuseki gaan en alle reads gemigreerd zijn:
- [ ] Migratiescript: alle Neo4j data → Fuseki triples
- [ ] Neo4j-leesroutes uitschakelen
- [ ] Neo4j-instantie termineren (uiteindelijk)

---

## 7. Design Decisions te registreren

De volgende beslissingen moeten als DD worden vastgelegd in `DESIGN-DECISIONS.md` van de ontologie-repo:

| DD-nr | Beslissing |
|-------|-----------|
| DD-061 | Centrale `valor:Tessera` als superklasse; module-specifieke claims als subklassen |
| DD-062 | `valor:Issue` naar Laag 4 (Application Ontology), niet in CAUSA |
| DD-063 | Apache Jena Fuseki + HermiT + ELK boven GraphDB (open source, OWL DL gratis) |
| DD-064 | `causa:EpistemicStatus` deprecated; `valor:epistemicStatus` centraal |
| DD-065 | 5-waardige statusmachine: Contested en Reconsidered toegevoegd t.o.v. v0.1 |
| DD-066 | Named graph structuur per DesignSpace (ontology/asis/alt/decisions/agents/provenance) |
| DD-067 | FastAPI blijft API-laag; geen migratie naar Node.js/Fastify |
| DD-068 | Neo4j tijdelijk duaal met Fuseki; Neo4j termineren na volledige migratie |

---

## 8. Risico's en mitigaties

| Risico | Waarschijnlijkheid | Impact | Mitigatie |
|--------|-------------------|--------|-----------|
| Fuseki performance bij grote DesignSpaces | Middel | Middel | Named graph partitionering; ELK voor real-time (OWL EL is polynomiaal) |
| HermiT timeout bij complexe ontologieën | Laag | Laag | Asynchroon draaien; timeout + fallback naar "consistentie onbekend" |
| Bestaande Neo4j data niet volledig migeerbaar naar VALOR-O | Middel | Hoog | Adapters bewaren Neo4j als bron; migratie incrementeel per DesignSpace |
| Perspectief-ontologieën niet expressief genoeg voor UI | Laag | Middel | SPARQL-projecties zijn aanpasbaar zonder ontologie-wijzigingen |
| Contributor leert gUFO-termen lekken door de UI | Middel | Laag | Perspectief-specifieke taallaag in frontend; gUFO nooit direct zichtbaar in gebruikers-UI |

---

## 9. Volgorde van commits in de ontologie-repo

Na afstemming van dit plan:

```
1. feat: add DD-061 through DD-068 to DESIGN-DECISIONS.md
2. feat: add 00j-tessera module (central Tessera, 5-state machine, DecisionEpisode)
3. feat: add 00j-tessera.shacl shapes (T1-T6)
4. refactor: 00h-causa — CausalClaim extends Tessera, deprecate local EpistemicStatus
5. refactor: 00i-socia — socia claims extend Tessera
6. refactor: 00g-acta, 00e-coodm — import tessera module
7. feat: add 00k-application module (DesignSpace, DesignPhase, Participant + roles)
8. feat: add 00k-application.shacl shapes
9. refactor: 00h-causa — move valor:Issue to 00k-application
10. feat: add 00l-axia module (ValueClaim, DesignImplication)
11. feat: add 00m-delibera module (ArgumentationNetwork, Vote, AgentTessera)
12. feat: add 00n-forma module (OntologicalElement, EngineerTessera)
13. feat: update void.trig — add new modules and Fuseki endpoint
```

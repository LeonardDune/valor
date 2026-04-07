# SOCIA — Frontend User Stories voor Claude Code
**Ontologie-gedreven: alle data komt uit VALOR-O via SPARQL**

---

## Codebase-instructies (lees dit eerst)

**Raadpleeg de bestaande codebase voordat je iets bouwt.**

CAUSA is het referentieperspectief voor canvas-conventies. AXIA-userstories (v2) zijn het referentiedocument voor het ontologie-gedreven patroon: bootstrap-queries, perspectief-engine, Tessera-infrastructuur. Bestudeer beide voordat je SOCIA bouwt.

**Alle SOCIA-componenten volgen exact dezelfde conventies** — design system, canvas-setup, SPARQL-querypatroon, Tessera-component, Yjs-integratie.

---

## Architectuurprincipe: de frontend is een view op VALOR-O

Geen enkele keuzelijst of statuswaarde is hardcoded. Alle opties worden geladen via SPARQL. Dit geldt nadrukkelijk voor:

- `socia:StakeholderRole`-individuen (`Applicant`, `PolicyMaker`, `Implementer`, `Supervisor`, `ChainPartner`, `AffectedParty`) — gecontroleerd vocabulaire in de graph
- `socia:DependencyStrength`-individuen (`Open`, `Committed`, `Critical`) — uit de graph
- `socia:DependencyType`-subklassen (`GoalDependency`, `TaskDependency`, `ResourceDependency`, `SoftGoalDependency`) — uit de graph
- `app:ParticipantRole`-individuen inclusief `hasVotingRight` — uit de graph
- `valor:EpistemicStatus`-individuen en transitiematrix — uit de graph (gedeeld met alle perspectieven)

---

## Ontologische grondslag (00i-socia.trig)

| Ontologie-klasse | Rol in de UI |
|---|---|
| `socia:Stakeholder` | Canvas-node: een actor met intentionele modi |
| `socia:HumanStakeholder` | Subtype: fysieke persoon |
| `socia:OrganisationalActor` | Subtype: institutionele agent |
| `socia:StakeholderRole` | Palet-item: zes gecontroleerde vocabulaire-individuen |
| `socia:StakeholderInterestProfile` | Detailpaneel: verzameling intentionele modi |
| `socia:InterestClaim` | Canvas-element + Tessera: bewering over belang |
| `socia:GoalClaim` | Canvas-element + Tessera: bewering over doel |
| `socia:PowerClaim` | Canvas-element + Tessera: bewering over macht |
| `socia:IntentionalDependency` | Canvas-edge: SocialCommitment Relator tussen twee Stakeholders |
| `socia:DependencyStrength` | Edge-eigenschap: Open / Committed / Critical |
| `socia:DependencyType` | Edge-eigenschap: Goal / Task / Resource / SoftGoal |
| `socia:ActorBoundary` | Canvas-groepering: intentionele grens rond een Stakeholder |
| `socia:StakeholderMap` | Canvasdocument: de volledige actor-analyse voor een Issue |

Namespaces:
- `socia:` → `https://valor-ecosystem.nl/ontology/socia#`
- `ufoc:` → `https://valor-ecosystem.nl/ontology/ufo-c#`
- `valor:` → `https://valor-ecosystem.nl/ontology/`
- `app:` → `https://valor-ecosystem.nl/ontology/application#`
- `acta:` → `https://valor-ecosystem.nl/ontology/acta#`
- `axia:` → `https://valor-ecosystem.nl/ontology/axia#`

---

## Perspectiefrelaties (kritisch voor SOCIA)

SOCIA staat niet op zichzelf. Drie relaties met andere perspectieven zijn ontologisch verankerd en moeten in de UI zichtbaar zijn:

**SOCIA → ACTA** (`socia:dependencyInstantiatedAs → acta:Transaction`)
Een `socia:IntentionalDependency` kan worden gekoppeld aan een `acta:Transaction` in ACTA. Dit is de brug van "wie is van wie afhankelijk" naar "hoe is die afhankelijkheid transactioneel geregeld". In de SOCIA-UI: een dependency-edge toont een badge als er een corresponderende ACTA-transactie bestaat; klikken navigeert naar ACTA.

**SOCIA → AXIA** (`socia:Stakeholder` als drager van `cover:ValueExperience`)
Stakeholders zijn de agents die waarden ervaren. In de AXIA-heatmap zijn stakeholders de context voor ValueExperiences. In de SOCIA-UI: een overlay toont welke `axia:ValueClaim`s betrekking hebben op een geselecteerde stakeholder — vanuit AXIA's named graph gelezen, niet gedupliceerd.

**SOCIA → Tessera** (`socia:stakeholderSubmitsClaim → valor:Tessera`)
Stakeholders dienen claims in. In de SOCIA-UI is een stakeholder-node tegelijk de actor die Tesserae indient. De `valor:claimedBy`-property op een Tessera verwijst naar de `ufoc:Agent`-URI van de stakeholder — dezelfde URI als in SOCIA. Dit is geen koppeling tussen systemen maar één en dezelfde entiteit in de graph.

---

## Epic 0 — Bootstrap: ontologie laden

### US-00 — Schema bij initialisatie laden

```
Als SOCIA-perspectief
wil ik bij opstarten de relevante ontologie-individuen laden
zodat alle UI-elementen worden gegenereerd vanuit VALOR-O.
```

**Acceptatiecriteria:**
- Voer bij perspectief-initialisatie de volgende bootstrap-queries uit (conform het patroon uit AXIA US-00):

```sparql
# Laad StakeholderRole-individuen (gecontroleerd vocabulaire)
SELECT ?uri ?label ?comment WHERE {
  ?uri a socia:StakeholderRole ;
       rdfs:label ?label .
  OPTIONAL { ?uri rdfs:comment ?comment }
  FILTER(lang(?label) = "nl")
}

# Laad DependencyStrength-individuen
SELECT ?uri ?label WHERE {
  ?uri a socia:DependencyStrength ;
       rdfs:label ?label .
  FILTER(lang(?label) = "nl")
}

# Laad DependencyType-subklassen
SELECT ?uri ?label WHERE {
  ?uri rdfs:subClassOf socia:IntentionalDependency ;
       rdfs:label ?label .
  FILTER(lang(?label) = "nl")
}

# Laad epistemische statussen + transitiematrix (gedeeld met AXIA)
# Conform AXIA US-00 — gebruik dezelfde queryresultaten als reeds geladen
```

- Sla op in `sociaStore.schema`
- Laadstatus en foutafhandeling conform het bestaande patroon

---

## Epic 1 — Canvas & navigatie

### US-01 — SOCIA-perspectief registreren

```
Als platformgebruiker
wil ik SOCIA kunnen openen als perspectief binnen VALOR
zodat ik de stakeholder-analyse kan modelleren.
```

**Acceptatiecriteria:**
- Registreer SOCIA als route en perspectief-entry conform CAUSA
- De SOCIA-pagina voert US-00 uit bij mount
- Paginatitel: `SOCIA — Stakeholderperspectief`

---

### US-02 — StakeholderMap laden vanuit de graph

```
Als modelleerder
wil ik bij het openen van SOCIA de bestaande stakeholders en afhankelijkheden zien
zodat het canvas de actuele toestand van de graph weergeeft.
```

**Acceptatiecriteria:**
- Query bij canvasinitialisatie:

```sparql
SELECT ?stakeholder ?label ?type ?role ?roleLabel ?boundary WHERE {
  GRAPH <valor:{designspace}/asis> {
    ?stakeholder a ?type ;
                 rdfs:label ?label .
    OPTIONAL {
      ?stakeholder socia:playsRole ?role .
      ?role rdfs:label ?roleLabel .
      FILTER(lang(?roleLabel) = "nl")
    }
    OPTIONAL { ?stakeholder socia:hasBoundary ?boundary }
    VALUES ?type { socia:HumanStakeholder socia:OrganisationalActor }
  }
}
```

- Laad ook alle `socia:IntentionalDependency`-instanties als edges
- Transformeer naar React Flow nodes en edges conform het CAUSA-transformatiepatroon
- Canvas-layout: opgeslagen als `valor:canvasX` / `valor:canvasY` in de graph (conform AXIA-patroon)

---

## Epic 2 — Stakeholders aanmaken

### US-03 — Stakeholder-node aanmaken

```
Als modelleerder
wil ik een Stakeholder kunnen toevoegen aan het canvas
zodat ik een actor registreer die relevant is voor het Issue.
```

**Acceptatiecriteria:**
- Aanmaken via contextmenu (conform CAUSA-patroon)
- Dialog vraagt: naam (`rdfs:label`), type (HumanStakeholder / OrganisationalActor — geladen als subklassen van `socia:Stakeholder`), rol (keuzelijst uit `sociaStore.schema.stakeholderRoles` — **niet hardcoded**)
- Node-type: `stakeholderNode` — visueel onderscheid tussen HumanStakeholder (cirkel/persoonspictogram) en OrganisationalActor (rechthoek/gebouwpictogram) conform het design system
- Schrijf naar de graph:

```sparql
INSERT DATA {
  GRAPH <valor:{designspace}/asis> {
    <{stakeholder-uri}> a socia:HumanStakeholder ;
                        rdfs:label "{naam}"@nl ;
                        socia:isStakeholderIn <{issue-uri}> ;
                        socia:playsRole socia:Applicant .
  }
}
```

- De stakeholder-URI is tegelijk de `ufoc:Agent`-URI die in andere perspectieven als `valor:claimedBy`-verwijzing wordt gebruikt — **dezelfde entiteit, geen kopie**

---

### US-04 — ActorBoundary visualiseren

```
Als modelleerder
wil ik de intentionele grens van een Stakeholder kunnen tonen
zodat interne elementen en externe afhankelijkheden visueel worden afgebakend.
```

**Acceptatiecriteria:**
- Elke Stakeholder-node heeft een uitklapbare `socia:ActorBoundary` — visueel als een groeperings-container (conform React Flow Group nodes)
- Binnen de boundary: interne elementen (`socia:InternalGoal`, `socia:InternalTask`, `socia:InternalResource`, `socia:InternalSoftGoal`) als kleinere sub-nodes
- Externe afhankelijkheden (`socia:IntentionalDependency`) kruisen de boundary-rand als edges
- Boundary aanmaken schrijft een `socia:ActorBoundary`-instantie en `socia:hasBoundary`-triple naar de graph

---

### US-05 — Interne elementen toevoegen aan een ActorBoundary

```
Als modelleerder
wil ik interne doelen, taken, middelen en kwaliteitseisen kunnen toevoegen aan een ActorBoundary
zodat de intentionele structuur van een actor zichtbaar is.
```

**Acceptatiecriteria:**
- Aanmaken via hover-knop op de boundary of contextmenu: `+ Intern doel`, `+ Interne taak`, `+ Intern middel`, `+ Interne kwaliteitseis`
- Sub-node types worden geladen als subklassen van `socia:InternalElement` uit de graph — geen hardcoded enum
- Sub-node toont `rdfs:label` (inline bewerkbaar)
- Schrijft `socia:boundaryContains`-triple naar de graph

---

## Epic 3 — StakeholderClaims

### US-06 — StakeholderClaim aanmaken

```
Als modelleerder
wil ik een claim kunnen registreren over een belang, doel of machtspositie van een Stakeholder
zodat de bewering epistemisch traceerbaar is als Tessera.
```

**Acceptatiecriteria:**
- Drie claimtypen: `socia:InterestClaim`, `socia:GoalClaim`, `socia:PowerClaim` — geladen als subklassen van `socia:StakeholderClaim` via SPARQL, niet hardcoded
- Aanmaken via het detailpaneel van een Stakeholder-node (tab `Claims`)
- Gebruik **exact dezelfde Tessera-component als AXIA en CAUSA** — `socia:StakeholderClaim` is een `valor:Tessera`-subklasse en erft de volledige epistemische infrastructuur
- Schrijf naar de graph:

```sparql
INSERT DATA {
  GRAPH <valor:{designspace}/asis> {
    <{claim-uri}> a socia:InterestClaim ;
                  valor:claimContent "{tekst}"@nl ;
                  valor:epistemicStatus valor:ProposedStatus ;
                  valor:claimType valor:AsIsType ;
                  valor:claimedBy <{stakeholder-uri}> ;
                  valor:claimedAt "{timestamp}"^^xsd:dateTime ;
                  valor:inPhase <{phase-uri}> .
  }
}
```

- Let op: `valor:claimedBy` verwijst naar de **stakeholder-URI zelf** — de Stakeholder is tegelijk de Agent die de claim indient (`socia:stakeholderSubmitsClaim` is een scherpere specificatie van `valor:claimedBy` voor dit domein)
- GDI-flags, statusbeheer en Evidence-koppeling conform de bestaande Tessera-infrastructuur

---

## Epic 4 — IntentionalDependency

### US-07 — IntentionalDependency aanmaken

```
Als modelleerder
wil ik een intentionele afhankelijkheid kunnen tekenen tussen twee Stakeholders
zodat ik registreer wie van wie afhankelijk is en op welke manier.
```

**Acceptatiecriteria:**
- Edge-type `intentionalDependencyEdge` — custom React Flow edge
- Aanmaken via handle-drag van Stakeholder A naar Stakeholder B (conform CAUSA-patroon); bij loslaten: dialog
- Dialog vraagt:
  - `socia:DependencyType`: keuzelijst uit `sociaStore.schema.dependencyTypes` (**niet hardcoded**: GoalDependency / TaskDependency / ResourceDependency / SoftGoalDependency)
  - `socia:DependencyStrength`: keuzelijst uit `sociaStore.schema.dependencyStrengths` (**niet hardcoded**: Open / Committed / Critical)
  - `valor:claimContent`: omschrijving van de afhankelijkheid (dit is de bijbehorende StakeholderClaim)
- Schrijf naar de graph:

```sparql
INSERT DATA {
  GRAPH <valor:{designspace}/asis> {
    <{dep-uri}> a socia:GoalDependency ;
                socia:depender <{stakeholder-a-uri}> ;
                socia:dependee <{stakeholder-b-uri}> ;
                socia:hasDependencyStrength socia:CriticalDependency ;
                socia:dependencyContext <{issue-uri}> .
  }
}
```

- Edge-visualisatie: dikte afhankelijk van DependencyStrength (Open = dun, Critical = dik); type-icoon op de edge (Goal / Task / Resource / SoftGoal)
- Koppel automatisch een `socia:StakeholderClaim` als Tessera bij de dependency (via het detailpaneel)

---

### US-08 — ACTA-koppeling op een IntentionalDependency

```
Als modelleerder
wil ik zien of een IntentionalDependency is uitgewerkt als ACTA-transactie
zodat de brug tussen stakeholder-afhankelijkheid en transactionele uitvoering zichtbaar is.
```

**Acceptatiecriteria:**
- Query bij laden van de dependency-edges:

```sparql
SELECT ?dep ?transaction ?transactionLabel WHERE {
  GRAPH ?g {
    ?dep a socia:IntentionalDependency ;
         socia:dependencyInstantiatedAs ?transaction .
    ?transaction rdfs:label ?transactionLabel .
  }
}
```

- Dependency-edges met een gekoppelde ACTA-transactie tonen een **ACTA-badge** op de edge (conform het CAPAX-badge-patroon in AXIA)
- Klikken op de badge navigeert naar ACTA en selecteert de corresponderende transactie — gebruik de bestaande perspectief-navigatiefunctie
- Dependency-edges zonder ACTA-koppeling tonen een lege badge met tooltip: `Nog niet uitgewerkt in ACTA`
- Vanuit het detailpaneel: knop `Koppel ACTA-transactie` opent een zoekdialoog die ACTA-transacties uit de graph ophaalt:

```sparql
SELECT ?tx ?label WHERE {
  GRAPH ?g {
    ?tx a acta:Transaction ;
        rdfs:label ?label .
  }
  FILTER(lang(?label) = "nl")
}
```

- Koppelen schrijft `socia:dependencyInstantiatedAs`-triple naar de graph via de Tessera-engine

---

## Epic 5 — AXIA-overlay op stakeholders

### US-09 — Waarde-implicaties per Stakeholder tonen

```
Als modelleerder
wil ik per Stakeholder kunnen zien welke waarde-implicaties (uit AXIA) betrekking op hem hebben
zodat de verbinding tussen actoren en waarden zichtbaar is zonder data te dupliceren.
```

**Acceptatiecriteria:**
- Toolbar-toggle `AXIA-overlay` (alleen actief als AXIA-claims aanwezig zijn in de graph)
- Bij activatie: query over de AXIA-named graph voor de actieve DesignSpace:

```sparql
SELECT ?stakeholder ?valueType ?valueTypeLabel ?polarity ?polarityLabel WHERE {
  GRAPH <valor:{designspace}/asis> {
    ?stakeholder a socia:Stakeholder .
  }
  GRAPH ?axiaGraph {
    ?claim a axia:ValueClaim ;
           valor:claimedBy ?stakeholder ;
           axia:concernsValueType ?valueType ;
           axia:claimPolarity ?polarity .
    ?valueType rdfs:label ?valueTypeLabel .
    ?polarity rdfs:label ?polarityLabel .
    FILTER(lang(?valueTypeLabel) = "nl")
  }
}
```

- Stakeholder-nodes krijgen een kleuroverlap met de ValueType-kleur uit het AXIA-kleurschema (conform de heatmap-conventie in AXIA)
- Klikken op de overlay-badge opent een tooltip met de betrokken ValueTypes en polariteiten
- **Geen data kopiëren naar de SOCIA-graph**: de overlay leest rechtstreeks uit de AXIA-named graph

---

### US-10 — DEMOS-blindspot signaleren

```
Als modelleerder
wil ik een waarschuwing zien als AffectedParty-stakeholders ontbreken of geen claims hebben
zodat de democratische inclusiviteit van de analyse zichtbaar is.
```

**Acceptatiecriteria:**
- Voer bij canvasload een controlequery uit:

```sparql
ASK {
  GRAPH <valor:{designspace}/asis> {
    ?s a socia:Stakeholder ;
       socia:playsRole socia:AffectedParty .
  }
}
```

- Als het antwoord `false` is: toon een persistente waarschuwingsbanner bovenaan het canvas: `Geen getroffenen (AffectedParty) geregistreerd — controleer de inclusiviteit van de analyse`
- Als AffectedParty-stakeholders wel aanwezig zijn maar geen `socia:InterestClaim` hebben: toon een badge op de node met tooltip `Geen belangen geregistreerd voor deze getroffene`
- Dit is geen blokkerende fout maar een informatieve signalering — conform de GDI-vlaggen in het Tessera-systeem

---

## Epic 6 — StakeholderMap

### US-11 — StakeholderMap persisteren

```
Als modelleerder
wil ik de volledige stakeholder-analyse persisteren als StakeholderMap
zodat de analyse als geheel traceerbaar is in de graph.
```

**Acceptatiecriteria:**
- Bij aanmaken van de eerste Stakeholder in een DesignSpace: maak automatisch een `socia:StakeholderMap`-instantie aan:

```sparql
INSERT DATA {
  GRAPH <valor:{designspace}/asis> {
    <{map-uri}> a socia:StakeholderMap ;
                socia:mapAddressesIssue <{issue-uri}> ;
                socia:mapAuthor <{agent-uri}> ;
                socia:mapCreatedAt "{timestamp}"^^xsd:dateTime .
  }
}
```

- Elke nieuwe Stakeholder en Dependency wordt automatisch via `socia:mapIncludesStakeholder` en `socia:mapIncludesDependency` aan de StakeholderMap gekoppeld
- Meerdere maps per DesignSpace zijn mogelijk (bijv. as-is en to-be variant); toon als tabbladen boven het canvas

---

## Epic 7 — Vergelijkingspaneel

### US-12 — Afhankelijkheidsmatrix via SPARQL

```
Als modelleerder
wil ik een matrix zien die alle stakeholders en hun onderlinge afhankelijkheden toont
zodat ik machtsstructuren en kritieke afhankelijkheden systematisch kan analyseren.
```

**Acceptatiecriteria:**
- Knop `Matrix` in de toolbar opent een overlay conform de bestaande overlay-structuur
- Query:

```sparql
SELECT ?depender ?dependerLabel ?dependee ?dependeeLabel
       ?depType ?strengthLabel WHERE {
  GRAPH <valor:{designspace}/asis> {
    ?dep a socia:IntentionalDependency ;
         socia:depender ?depender ;
         socia:dependee ?dependee ;
         socia:hasDependencyStrength ?strength .
    ?depender rdfs:label ?dependerLabel .
    ?dependee rdfs:label ?dependeeLabel .
    ?strength rdfs:label ?strengthLabel .
    OPTIONAL { ?dep a ?depType .
      FILTER(?depType != socia:IntentionalDependency &&
             ?depType != owl:NamedIndividual) }
  }
  FILTER(lang(?dependerLabel) = "nl" && lang(?dependeeLabel) = "nl")
}
```

- Matrix: rijen = dependers, kolommen = dependees; cel toont DependencyType-icoon + sterkte-badge
- Kritieke afhankelijkheden (`socia:CriticalDependency`) worden gemarkeerd in de accentkleur van het design system

---

## Epic 8 — Tessera-infrastructuur

### US-13 — StakeholderClaim epistemisch beheren

```
Als modelleerder
wil ik de epistemische status van een StakeholderClaim kunnen beheren
zodat de levenscyclus van stakeholder-beweringen gevolgd wordt.
```

**Acceptatiecriteria:**
- Gebruik exact dezelfde Tessera-component als AXIA en CAUSA — `socia:StakeholderClaim` erft `valor:Tessera`
- Statusovergangen geladen uit de graph via `valor:allowedTransitionTo` (conform AXIA US-10)
- `valor:requiresDecisionEpisode`-blokkering conform de bestaande Tessera-implementatie
- GDI-vlaggen: `TruthfulnessIssue` automatisch bij ontbrekend `valor:hasEvidence`; `MeaningfulnessIssue` handmatig markeerbaar

---

## Epic 9 — Samenwerking en export

### US-14 — Real-time synchronisatie

```
Als modelleerder
wil ik dat canvas-wijzigingen direct zichtbaar zijn voor andere deelnemers.
```

**Acceptatiecriteria:**
- Gebruik de bestaande Yjs/y-websocket-integratie — geen tweede CRDT-laag
- Schrijfoperaties lopen via de Tessera-engine
- Participantrol (`app:ParticipantRole`) bepaalt schrijfrecht — geladen uit de graph via `app:roleWeight` en `app:hasVotingRight`, niet hardcoded

---

### US-15 — SPARQL CONSTRUCT export

```
Als ontologie-engineer
wil ik de SOCIA-modellering exporteren als TTL
zodat de graph-inhoud buiten het platform inspecteerbaar is.
```

**Acceptatiecriteria:**
- Knop `Exporteer → TTL` voert een SPARQL CONSTRUCT uit:

```sparql
CONSTRUCT {
  ?s a ?type ; rdfs:label ?label ;
     socia:isStakeholderIn ?issue ;
     socia:playsRole ?role .
  ?dep a ?depType ;
       socia:depender ?depender ;
       socia:dependee ?dependee ;
       socia:hasDependencyStrength ?strength ;
       socia:dependencyInstantiatedAs ?tx .
  ?claim a ?claimType ;
         valor:claimContent ?content ;
         valor:epistemicStatus ?status ;
         valor:claimedBy ?s .
}
WHERE {
  GRAPH <valor:{designspace}/asis> {
    ?s a ?type .
    VALUES ?type { socia:HumanStakeholder socia:OrganisationalActor }
    ?s rdfs:label ?label .
    OPTIONAL { ?s socia:isStakeholderIn ?issue }
    OPTIONAL { ?s socia:playsRole ?role }
    OPTIONAL {
      ?dep socia:depender|socia:dependee ?s ;
           a ?depType ;
           socia:depender ?depender ;
           socia:dependee ?dependee .
      OPTIONAL { ?dep socia:hasDependencyStrength ?strength }
      OPTIONAL { ?dep socia:dependencyInstantiatedAs ?tx }
    }
    OPTIONAL {
      ?claim valor:claimedBy ?s ;
             a ?claimType ;
             valor:claimContent ?content ;
             valor:epistemicStatus ?status .
    }
  }
}
```

- Download als `.ttl`; geen frontend-serialisatie

---

## Bestandsstructuur

Volg de mappenstructuur van CAUSA en AXIA als template:

```
src/perspectives/socia/
├── components/
│   ├── nodes/
│   │   ├── StakeholderNode.tsx        # cirkel (Human) / rechthoek (Org)
│   │   ├── ActorBoundaryNode.tsx      # React Flow Group node
│   │   ├── InternalElementNode.tsx    # sub-node binnen boundary
│   ├── edges/
│   │   ├── IntentionalDependencyEdge.tsx
│   ├── panels/
│   │   ├── StakeholderDetailPanel.tsx
│   │   ├── ClaimList.tsx              # StakeholderClaims via Tessera-component
│   │   ├── DependencyMatrix.tsx
│   ├── overlays/
│   │   ├── AxiaOverlay.tsx            # leest AXIA-graph, dupliceert niets
│   │   ├── DemosWarningBanner.tsx
├── store/
│   └── sociaStore.ts
├── lib/
│   ├── sociaEngine.ts                 # SPARQL-queries + transformaties
│   ├── actaLinkResolver.ts            # dependency → acta:Transaction
│   └── axiaOverlayQuery.ts            # leest AXIA-named graph
├── SociaCanvas.tsx
└── index.ts
```

---

## Implementatievolgorde

| Fase | User Stories | Resultaat |
|---|---|---|
| **1** | US-00, US-01, US-02, US-03 | SOCIA geregistreerd, stakeholders op canvas |
| **2** | US-04, US-05, US-07 | ActorBoundary + interne elementen + dependencies |
| **3** | US-06, US-13 | StakeholderClaims als Tesserae |
| **4** | US-08 | ACTA-koppeling op dependency-edges |
| **5** | US-09, US-10 | AXIA-overlay + DEMOS-signalering |
| **6** | US-11, US-12 | StakeholderMap + vergelijkingsmatrix |
| **7** | US-14, US-15 | Samenwerking + export |

---

## Wat er niet in staat (en waarom)

| Niet aanwezig | Reden |
|---|---|
| Hardcoded rollenlijst (`Aanvrager`, `Beleidsmaker`, ...) | `socia:StakeholderRole`-individuen staan als gecontroleerd vocabulaire in de graph (DD-AI.2) |
| Hardcoded sterktewaarden (`Zwak`, `Matig`, `Sterk`) | `socia:DependencyStrength`-individuen (`Open`, `Committed`, `Critical`) komen uit de graph |
| Aparte stakeholder-database naast de graph | Stakeholder-URIs zijn `ufoc:Agent`-URIs; dezelfde entiteiten leven in ACTA, AXIA en SOCIA |
| Eigen ValueType-weergave in SOCIA | De AXIA-overlay leest de AXIA-named graph; SOCIA dupliceert geen waarde-data |
| Frontend TTL-serialisatie | SPARQL CONSTRUCT levert correcte RDF direct uit de graph |

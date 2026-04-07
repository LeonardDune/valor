# AXIA — Frontend User Stories voor Claude Code (v2)
**Ontologie-gedreven: alle data komt uit VALOR-O via SPARQL**

---

## Codebase-instructies (lees dit eerst)

**Raadpleeg de bestaande codebase voordat je iets bouwt.**

CAUSA is het referentieperspectief. Bestudeer de CAUSA-implementatie en extraheer:
- het global design system (Tailwind config, CSS variables, kleurpallet, typografie)
- de canvas-setup (React Flow configuratie, pannen/zoomen, achtergrond, controls)
- het patroon voor custom node- en edge-types
- de Zustand store-structuur en naamgevingsconventies
- de Yjs/CRDT-integratie voor real-time samenwerking
- de Tessera-component en epistemische statuskleuren
- hoe SPARQL-queries worden opgebouwd en uitgevoerd via de perspectief-engine

**Alle AXIA-componenten volgen exact dezelfde conventies.** Geen nieuwe design tokens, geen andere libraries, geen afwijkende structuur.

---

## Architectuurprincipe: de frontend is een view op VALOR-O

**Geen enkele keuzelijst, toggle of statuswaarde is hardcoded in de frontend.**

Alle opties — ValueTypes, polariteiten, statussen, faseovergangen, Osborne-niveaus, alternatievenlijsten — worden bij startup of op aanvraag geladen via SPARQL-queries op de Fuseki-graph. De ontologie is de single source of truth.

Concreet patroon (volg de bestaande perspectief-engine-conventie van CAUSA):
1. Bij perspectief-initialisatie: voer bootstrap-queries uit die de relevante ontologie-individuen laden
2. Sla de resultaten op in de Zustand store als geladen schema (niet als hardcoded type)
3. Render UI-elementen op basis van de geladen schema-data

**SPARQL-queries horen in de perspectief-engine (`src/perspectives/axia/lib/axiaEngine.ts` of equivalent), nooit inline in componenten.**

---

## Ontologische grondslag (00l-axia.trig + 00f-cover.trig)

Relevante klassen en hun betekenis voor de frontend:

| Ontologie-klasse | Rol in de UI |
|---|---|
| `coodm:ValueType` | Palet-item: beschikbare waarden om claims over te maken; komt uit de graph, niet hardcoded |
| `axia:ValueClaim` | Canvas-node: een Tessera die een waarde-implicatie beschrijft |
| `axia:ValueTensionClaim` | Canvas-node: een Tessera over spanning tussen twee ValueTypes |
| `axia:DesignImplication` | Canvas-edge: Relator die een Tessera verbindt met een ValueType |
| `axia:ClaimPolarity` | Polariteit-individu: `SupportingPolarity`, `UnderminingPolarity`, `AmbiguousPolarity` — uit de graph |
| `valor:EpistemicStatus` | Status-individu: `Proposed`, `Contested`, `Accepted`, `Rejected`, `Reconsidered` — uit de graph |
| `valor:allowedTransitionTo` | Transitiematrix: welke statusovergangen zijn toegestaan — uit de graph |
| `valor:UncertaintyLevel` | Onzekerheidsniveau-individu: `StatisticalRisk`, `Scenario`, `DeepUncertainty`, `Ignorance` — uit de graph |

Namespaces:
- `axia:` → `https://valor-ecosystem.nl/ontology/axia#`
- `coodm:` → `https://valor-ecosystem.nl/ontology/coodm#`
- `cover:` → `https://valor-ecosystem.nl/ontology/cover#`
- `valor:` → `https://valor-ecosystem.nl/ontology/`
- `tess:` → `https://valor-ecosystem.nl/ontology/tessera#`

---

## Epic 0 — Bootstrap: ontologie laden

### US-00 — Perspectief-schema bij initialisatie laden

```
Als AXIA-perspectief
wil ik bij opstarten de relevante ontologie-individuen laden
zodat alle UI-elementen worden gegenereerd vanuit VALOR-O en nooit hardcoded zijn.
```

**Acceptatiecriteria:**
- Voer bij perspectief-initialisatie de volgende bootstrap-queries uit (conform het bootstrap-patroon van CAUSA):

```sparql
# Laad alle beschikbare ValueTypes uit de graph
SELECT ?uri ?label WHERE {
  ?uri a coodm:ValueType ;
       rdfs:label ?label .
  FILTER(lang(?label) = "nl")
}

# Laad polariteit-individuen
SELECT ?uri ?label WHERE {
  ?uri a axia:ClaimPolarity ;
       rdfs:label ?label .
  FILTER(lang(?label) = "nl")
}

# Laad epistemische statussen + transitiematrix
SELECT ?status ?label ?allowedNext ?requiresEpisode WHERE {
  ?status a valor:EpistemicStatus ;
          rdfs:label ?label .
  OPTIONAL { ?status valor:allowedTransitionTo ?allowedNext }
  OPTIONAL { ?status valor:requiresDecisionEpisode ?requiresEpisode }
  FILTER(lang(?label) = "nl")
}

# Laad onzekerheidsniveaus
SELECT ?uri ?label WHERE {
  ?uri a valor:UncertaintyLevel ;
       rdfs:label ?label .
  FILTER(lang(?label) = "nl")
}
```

- Sla resultaten op in `axiaStore.schema` (conform de store-structuur van CAUSA)
- Zolang het schema niet geladen is: toon een laadstatus conform de bestaande loading-state-component
- Als een query mislukt: toon een foutmelding conform de bestaande error-state-component; blokkeer het perspectief

---

## Epic 1 — Canvas & navigatie

### US-01 — AXIA-perspectief registreren in het platform

```
Als platformgebruiker
wil ik AXIA kunnen openen als perspectief binnen VALOR
zodat ik vanuit de bekende platformnavigatie naar de waardekaart kan navigeren.
```

**Acceptatiecriteria:**
- Registreer AXIA als route en perspectief-entry conform de bestaande perspectief-registratie (zie CAUSA)
- De AXIA-pagina voert US-00 uit bij mount voordat het canvas getoond wordt
- Paginatitel: `AXIA — Waardeperspectief`

---

### US-02 — Waardekaart laden vanuit de graph

```
Als modelleerder
wil ik bij het openen van AXIA de bestaande ValueClaims en ValueTensionClaims zien
zodat het canvas de actuele toestand van de graph weergeeft.
```

**Acceptatiecriteria:**
- Voer bij canvasinitialisatie een query uit die alle `axia:ValueClaim`- en `axia:ValueTensionClaim`-instanties ophaalt voor de actieve DesignSpace en het actieve alternatief:

```sparql
SELECT ?claim ?type ?label ?polarity ?polarityLabel ?valueType ?valueTypeLabel ?status WHERE {
  GRAPH ?g {
    ?claim a ?type ;
           valor:claimContent ?label ;
           valor:epistemicStatus ?status .
    OPTIONAL {
      ?claim axia:concernsValueType ?valueType .
      ?valueType rdfs:label ?valueTypeLabel .
      FILTER(lang(?valueTypeLabel) = "nl")
    }
    OPTIONAL {
      ?claim axia:claimPolarity ?polarity .
      ?polarity rdfs:label ?polarityLabel .
      FILTER(lang(?polarityLabel) = "nl")
    }
  }
  VALUES ?type { axia:ValueClaim axia:ValueTensionClaim }
}
```

- Transformeer de queryresultaten naar React Flow nodes conform het transformatiepatroon van CAUSA
- Canvas-positie per node: opgeslagen als `valor:canvasX` / `valor:canvasY` op de claim (zie hoe CAUSA canvas-layout persisteert), of als apart layout-document in de graph

---

## Epic 2 — ValueClaim aanmaken

### US-03 — ValueClaim aanmaken via het waardepalet

```
Als modelleerder
wil ik een ValueClaim kunnen aanmaken door een ValueType te kiezen uit het palet
zodat ik een ontologisch gegronde bewering doe over de waarde-implicatie van een ontwerpelement.
```

**Acceptatiecriteria:**
- Het waardepalet is een zijpaneel of contextmenu met alle `coodm:ValueType`-individuen uit `axiaStore.schema.valueTypes` — dus geladen via US-00, niet hardcoded
- Per ValueType: toon `rdfs:label` en optioneel `rdfs:comment` als tooltip
- Gebruiker kiest een ValueType en een polariteit uit `axiaStore.schema.polarities` (eveneens uit de graph: `SupportingPolarity`, `UnderminingPolarity`, `AmbiguousPolarity`)
- Gebruiker typt de `valor:claimContent` (de propositionele inhoud van de claim)
- Bij bevestigen: schrijf een nieuwe `axia:ValueClaim`-instantie naar de graph via de Tessera-engine:

```sparql
INSERT DATA {
  GRAPH <valor:{designspace}/alternative/{id}> {
    <{claim-uri}> a axia:ValueClaim ;
                  valor:claimContent "{tekst}"@nl ;
                  valor:epistemicStatus valor:ProposedStatus ;
                  valor:claimType valor:ToBeType ;
                  valor:claimedBy <{agent-uri}> ;
                  valor:claimedAt "{timestamp}"^^xsd:dateTime ;
                  valor:inAlternative <{alternative-uri}> ;
                  axia:concernsValueType <{valueType-uri}> ;
                  axia:claimPolarity axia:SupportingPolarity .
  }
}
```

- Na succesvolle schrijfoperatie: voeg de node toe aan het React Flow canvas conform het bestaande patroon
- Node-type: `valueClaimNode` (custom React Flow node)
- Visuele vorm: zeshoek; kleur afhankelijk van polariteit (groen = supporting, rood = undermining, oranje = ambiguous) — kleuren uit de design tokens, niet hardcoded

---

### US-04 — ValueTensionClaim aanmaken

```
Als modelleerder
wil ik een ValueTensionClaim kunnen aanmaken tussen twee ValueTypes
zodat ik een ontologisch gegronde bewering doe over een waardespanning.
```

**Acceptatiecriteria:**
- Aanmaken via handle-drag tussen twee `valueClaimNode`s die naar verschillende ValueTypes verwijzen, of via contextmenu
- Dialog vraagt: `valor:claimContent` (omschrijving van de spanning), optioneel `axia:tensionContext` (het Issue — zoekbaar in de graph)
- Schrijf een nieuwe `axia:ValueTensionClaim` naar de graph:

```sparql
INSERT DATA {
  GRAPH <valor:{designspace}/asis> {
    <{tension-uri}> a axia:ValueTensionClaim ;
                    valor:claimContent "{tekst}"@nl ;
                    valor:epistemicStatus valor:ProposedStatus ;
                    valor:claimType valor:AsIsType ;
                    valor:claimedBy <{agent-uri}> ;
                    valor:claimedAt "{timestamp}"^^xsd:dateTime ;
                    axia:tensionBetween <{valueType-uri-1}> ;
                    axia:tensionBetween <{valueType-uri-2}> .
  }
}
```

- Edge-type `valueTensionEdge`: dubbele pijl in de spanningskleur van het design system
- Transitieve spanningsdetectie: SPARQL-query die controleert of A↔C al volgt uit A↔B en B↔C:

```sparql
ASK {
  ?t1 a axia:ValueTensionClaim ; axia:tensionBetween <{A}> ; axia:tensionBetween <{B}> .
  ?t2 a axia:ValueTensionClaim ; axia:tensionBetween <{B}> ; axia:tensionBetween <{C}> .
  FILTER NOT EXISTS {
    ?t3 a axia:ValueTensionClaim ; axia:tensionBetween <{A}> ; axia:tensionBetween <{C}> .
  }
}
```

- Bij `true`: toon de bestaande toast-component met suggestie

---

## Epic 3 — DesignImplication

### US-05 — DesignImplication aanmaken

```
Als modelleerder
wil ik een DesignImplication kunnen registreren tussen een Tessera en een ValueType
zodat ik formeel vastleg welk ontwerpelement welke waarde beïnvloedt.
```

**Acceptatiecriteria:**
- Een `axia:DesignImplication` is een Relator: hij verbindt een willekeurige `valor:Tessera` (ook van andere perspectieven, bijv. een `causa:CausalClaim`) met een `coodm:ValueType`
- Aanmaken via rechtsklik op een node op het canvas: `+ Waarde-implicatie koppelen`
- Dialoog: kies een ValueType uit het palet (geladen via US-00), kies een polariteit
- Schrijf naar de graph:

```sparql
INSERT DATA {
  GRAPH <valor:{designspace}/alternative/{id}> {
    <{implication-uri}> a axia:DesignImplication ;
                        axia:implicationSource <{tessera-uri}> ;
                        axia:implicationTarget <{valueType-uri}> ;
                        axia:implicationPolarity axia:SupportingPolarity .
  }
}
```

- Visualiseer als gerichte edge tussen de Tessera-node en de ValueType in het palet-paneel

---

## Epic 4 — Waardepalet en filtering

### US-06 — ValueType-palet met live filtering

```
Als modelleerder
wil ik een doorzoekbaar palet zien van alle ValueTypes in de ontologie
zodat ik snel de juiste waarde kan vinden om een claim over te maken.
```

**Acceptatiecriteria:**
- Palet toont alle `coodm:ValueType`-individuen uit `axiaStore.schema.valueTypes`
- Doorzoekbaar op `rdfs:label` (live filter, geen nieuwe query per toetsaanslag)
- Per ValueType: toon een badge met het aantal bestaande ValueClaims in de actieve DesignSpace (geladen via een aparte count-query bij palet-open)
- ValueTypes waarover al claims bestaan krijgen een visueel onderscheid (bijv. filled vs. outline)
- Geen importfunctie, geen hardcoded lijst — de ontologie bepaalt wat er beschikbaar is

---

### US-07 — Alternatief-filter op het canvas

```
Als modelleerder
wil ik het canvas kunnen filteren op een actief DesignAlternatief
zodat ik alleen de ValueClaims zie die relevant zijn voor dat alternatief.
```

**Acceptatiecriteria:**
- Beschikbare alternatieven worden geladen via SPARQL op `00k-application.trig`:

```sparql
SELECT ?alt ?label WHERE {
  GRAPH <valor:{designspace}/base> {
    ?alt a app:DesignAlternative ;
         rdfs:label ?label .
  }
}
```

- Alternatieven verschijnen als gekleurde tabs conform de bestaande alternatief-tab-component
- Bij selectie: canvas toont ValueClaims uit de named graph van dat alternatief + gedeelde as-is claims
- Niet-actieve alternatief-claims zijn ghost (opacity conform CAUSA-conventie)
- `axiaStore.activeAlternativeId` wordt bijgewerkt

---

## Epic 5 — Heatmap

### US-08 — Heatmap-overlay via SPARQL-aggregatie

```
Als modelleerder
wil ik een heatmap-overlay activeren die toont welke waarden het meest worden beïnvloed
zodat ik de waarde-impact van het actieve alternatief in één oogopslag zie.
```

**Acceptatiecriteria:**
- Heatmap-toggle in de toolbar (conform CAUSA)
- Bij activatie: voer een SPARQL-aggregatiequery uit:

```sparql
SELECT ?valueType (COUNT(?sup) AS ?supports) (COUNT(?und) AS ?undermines) WHERE {
  GRAPH <valor:{designspace}/alternative/{id}> {
    {
      ?claim a axia:ValueClaim ;
             axia:concernsValueType ?valueType ;
             axia:claimPolarity axia:SupportingPolarity ;
             valor:epistemicStatus valor:AcceptedStatus .
      BIND(?claim AS ?sup)
    } UNION {
      ?claim a axia:ValueClaim ;
             axia:concernsValueType ?valueType ;
             axia:claimPolarity axia:UnderminingPolarity ;
             valor:epistemicStatus valor:AcceptedStatus .
      BIND(?claim AS ?und)
    }
  }
}
GROUP BY ?valueType
```

- Bereken nettoscore per ValueType: `supports - undermines`
- Kleur de ValueType-badges in het palet op basis van nettoscore via de semantische kleuren van het design system
- Legenda conform de bestaande legenda-component
- Heatmap herberekent automatisch bij statuswijziging van een ValueClaim

---

## Epic 6 — Vergelijkingspaneel

### US-09 — Alternatievenvergelijking via SPARQL

```
Als modelleerder
wil ik een matrix zien die alle alternatieven naast elkaar toont per ValueType
zodat ik waarde-afwegingen systematisch kan vergelijken.
```

**Acceptatiecriteria:**
- Knop `Vergelijk` opent een overlay conform de bestaande overlay-structuur
- Matrix wordt gegenereerd door een SPARQL-query over meerdere named graphs:

```sparql
SELECT ?alt ?altLabel ?valueType ?valueTypeLabel ?polarity ?polarityLabel WHERE {
  ?alt a app:DesignAlternative ; rdfs:label ?altLabel .
  GRAPH ?g {
    ?claim a axia:ValueClaim ;
           valor:inAlternative ?alt ;
           valor:epistemicStatus valor:AcceptedStatus ;
           axia:concernsValueType ?valueType ;
           axia:claimPolarity ?polarity .
    ?valueType rdfs:label ?valueTypeLabel .
    ?polarity rdfs:label ?polarityLabel .
  }
}
ORDER BY ?valueType ?alt
```

- Rijen = ValueTypes, kolommen = alternatieven
- Cel toont polariteits-icoon + klikbaar voor details
- Geen hardcoded celwaarden; alles uit de queryresultaten
- Export via SPARQL CONSTRUCT query die de matrix als TTL teruggeeft (geen frontend-serialisatie)

---

## Epic 7 — Tessera-infrastructuur

### US-10 — ValueClaim als Tessera beheren

```
Als modelleerder
wil ik de epistemische status van een ValueClaim kunnen beheren
zodat de levenscyclus van de claim gevolgd wordt conform de VALOR-O statusmachine.
```

**Acceptatiecriteria:**
- Gebruik exact de Tessera-component en het detailpaneel van CAUSA — geen nieuwe variant
- De beschikbare statusovergangen worden geladen uit `axiaStore.schema.transitions` (geladen in US-00 via `valor:allowedTransitionTo`)
- De statusdropdown toont alleen de ontologisch toegestane volgende statussen voor de huidige status
- Overgangen die `valor:requiresDecisionEpisode = true` hebben blokkeren de statuswijziging totdat een `valor:DecisionEpisode`-referentie is opgegeven
- Statuswijziging schrijft via de Tessera-engine naar de graph (conform het bestaande schrijfpatroon)
- GDI-flags (`valor:gdiFlag`) worden getoond als waarschuwingsbadges conform de bestaande badge-component; `TruthfulnessIssue` wordt automatisch getoond als er geen `valor:hasEvidence` aanwezig is

---

### US-11 — Evidence koppelen aan een ValueClaim

```
Als modelleerder
wil ik bewijs kunnen koppelen aan een ValueClaim
zodat de onderbouwing van de waarde-implicatie traceerbaar is.
```

**Acceptatiecriteria:**
- Gebruik de bestaande Evidence-component van CAUSA
- Bewijs-typen worden geladen uit de graph via de bootstrap-query op `valor:EvidenceType`
- Koppelen schrijft een `valor:Evidence`-instantie en `valor:hasEvidence`-triple naar de graph
- Na koppelen: `TruthfulnessIssue` GDI-flag verdwijnt automatisch (SHACL TG-02 auto-rule)

---

## Epic 8 — Samenwerking en rollen

### US-12 — Real-time synchronisatie en aanwezigheid

```
Als modelleerder
wil ik dat canvas-wijzigingen direct zichtbaar zijn voor andere deelnemers
zodat we gelijktijdig kunnen modelleren.
```

**Acceptatiecriteria:**
- Gebruik de bestaande Yjs/y-websocket-integratie — geen tweede CRDT-laag
- Aanwezigheidsindicatoren en node-locking conform het bestaande patroon
- Schrijfoperaties naar de graph lopen altijd via de Tessera-engine, ook in real-time modus
- Rol-beperking (`Moderator` / `Deelnemer` / `Waarnemer`) conform het platform-brede RBAC-model; rollen worden geladen uit de graph, niet hardcoded

---

## Epic 9 — Export

### US-13 — SPARQL CONSTRUCT export

```
Als ontologie-engineer
wil ik de AXIA-modellering kunnen exporteren als TTL
zodat ik de graph-inhoud buiten het platform kan inspecteren of archiveren.
```

**Acceptatiecriteria:**
- Knop `Exporteer → TTL` voert een SPARQL CONSTRUCT query uit op de relevante named graphs:

```sparql
CONSTRUCT {
  ?claim a ?type ;
         valor:claimContent ?content ;
         valor:epistemicStatus ?status ;
         axia:concernsValueType ?vt ;
         axia:claimPolarity ?pol ;
         valor:claimedBy ?agent ;
         valor:claimedAt ?ts .
  ?impl a axia:DesignImplication ;
        axia:implicationSource ?src ;
        axia:implicationTarget ?target ;
        axia:implicationPolarity ?impPol .
}
WHERE {
  GRAPH ?g {
    { ?claim a axia:ValueClaim } UNION { ?claim a axia:ValueTensionClaim }
    ?claim a ?type ;
           valor:claimContent ?content ;
           valor:epistemicStatus ?status ;
           valor:claimedBy ?agent ;
           valor:claimedAt ?ts .
    OPTIONAL { ?claim axia:concernsValueType ?vt }
    OPTIONAL { ?claim axia:claimPolarity ?pol }
    OPTIONAL {
      ?impl a axia:DesignImplication ;
            axia:implicationSource ?claim ;
            axia:implicationTarget ?target ;
            axia:implicationPolarity ?impPol .
            BIND(?claim AS ?src)
    }
  }
}
```

- Resultaat wordt gedownload als `.ttl`-bestand
- Geen frontend-serialisatie: de graph levert correcte RDF

---

### US-14 — Canvas-snapshot exporteren

```
Als modelleerder
wil ik het canvas exporteren als afbeelding
zodat ik de waardekaart kan delen in rapporten.
```

**Acceptatiecriteria:**
- Gebruik de canvas-exportfunctie die al in het platform aanwezig is (zie CAUSA of andere perspectieven)
- Bestandsnaam: `axia-waardekaart-{datum}.svg`

---

## Wat er niet meer in staat (en waarom)

| Vervallen US | Reden |
|---|---|
| Hardcoded waardenlijst importeren | ValueTypes staan al in de ontologie; `coodm:ValueType`-instanties zijn de bron |
| Hardcoded context-level switcher | Osborne-niveaus worden geladen als `app:ContextLevel`-individuen uit `00k-application.trig` |
| Hardcoded polariteit-strings | `axia:ClaimPolarity`-individuen staan in de ontologie |
| Hardcoded statusmachine | `valor:allowedTransitionTo`-triples bepalen de machine |
| Frontend TTL-serialisatie | SPARQL CONSTRUCT levert de correcte RDF direct vanuit de graph |
| `src/data/axia/valueLists.ts` | Dit bestand mag niet worden aangemaakt |

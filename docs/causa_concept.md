# CAUSA-agent

## 1. Doel en positionering

CAUSA is een ondersteunende AI-agent binnen het VALOR-ecosysteem die **menselijke samenwerking faciliteert bij het gezamenlijk construeren van causale modellen (causal loops)** rond maatschappelijke en publieke vraagstukken.

CAUSA is **geen analyserende autoriteit** en **geen autonoom modellerend systeem**. De agent functioneert als:

* gespreks- en denkfacilitator
* structuurbrenger in gezamenlijke causal reasoning
* expliciteerder van aannames, onzekerheden en lacunes

De primaire intelligentie blijft bij de menselijke deelnemers; CAUSA versterkt die intelligentie door patroonherkenning, vraagstelling en suggesties.

---

## 2. Probleemdefinitie

Bij complexe maatschappelijke vraagstukken:

* werken meerdere mensen gelijktijdig aan oorzaken en gevolgen
* bestaan meerdere, concurrerende interpretaties van causaliteit
* zijn relaties vaak onzeker, contextafhankelijk en iteratief

Huidige tools voor causal loop diagrams zijn:

* individueel gericht
* statisch
* slecht in het expliciet maken van onzekerheid en meningsverschil

CAUSA adresseert dit door:

* een gedeeld, dynamisch causale model (Neo4j)
* expliciete ondersteuning van samenwerking
* een AI-agent die het *proces* ondersteunt, niet de *inhoud dicteert*

---

## 3. Ontwerpprincipes

### 3.1 Mens-in-de-loop (leidend)

* Mensen maken en wijzigen het causale model
* De agent suggereert en bevraagt
* Besluiten en consolidatie zijn altijd menselijk

### 3.2 Onzekerheid is first-class

* Niet elke causale relatie hoeft direct "waar" te zijn
* Voorstellen, betwisting en alternatieven blijven zichtbaar

### 3.3 Samenwerking vóór optimalisatie

* Het systeem ondersteunt dialoog en gezamenlijk begrip
* Niet het "beste" model, maar een *gedeeld* model staat centraal

### 3.4 Neo4j als gedeeld werkgeheugen

* De graph bevat ook:

  * hypothesen
  * claims
  * tegenstrijdigheden
* Geen verborgen agent state

---

## 4. Functionele scope van de CAUSA-pilot

De pilot richt zich op **één werksessie** rond **één maatschappelijk probleem**.

### 4.1 Wat gebruikers kunnen

* factoren toevoegen, wijzigen en verwijderen
* causale relaties leggen met:

  * richting
  * polariteit (+ / -)
  * mate van zekerheid
* bestaande relaties bevragen of betwisten
* meerdere causaliteiten naast elkaar laten bestaan

### 4.2 Wat de CAUSA-agent doet

De agent:

* stelt gerichte vragen, zoals:

  * "Welke factor versterkt dit effect?"
  * "Is deze invloed altijd positief?"
* suggereert ontbrekende schakels
* herkent mogelijke loops (versterkend of dempend)
* signaleert onduidelijkheden of inconsistenties

De agent:

* voert **geen mutaties** uit op het model
* schrijft **geen** causal claims weg

---

## 5. Conceptueel datamodel (pilot-niveau)

### 5.1 Bestaande concepten (hergebruik)

* `FACTOR`
* `BEINVLOEDT`

### 5.2 Nieuwe concepten voor samenwerking

#### CAUSAL_CLAIM

Een expliciete, contextgebonden uitspraak over causaliteit.

Eigenschappen:

* `id`
* `polariteit` (`+` | `-`)
* `zekerheid` (`laag` | `middel` | `hoog`)
* `status` (`voorstel` | `geaccepteerd` | `betwist`)
* `auteur`
* `sessie_id`

Relaties:

* `(FACTOR)-[:CLAIMT_INVLOED]->(CAUSAL_CLAIM)`
* `(CAUSAL_CLAIM)-[:OP]->(FACTOR)`

`BEINVLOEDT` blijft bestaan voor geconsolideerde causaliteit.

---

## 6. Architectuuroverzicht (pilot)

### 6.1 Frontend (NodeJS)

* Causal Workspace
* Real-time visualisatie van factoren en claims
* Weergave van onzekerheid en status
* UI voor agent-suggesties en vragen

### 6.2 Backend (FastAPI + Python)

* API voor:

  * ophalen en muteren van causal claims
  * sessiecontext
  * agent-interacties

### 6.3 CAUSA-agent

* Stateless service
* Input:

  * subset van de graph
  * expliciete vraag of actie van gebruiker
* Output:

  * suggesties
  * vragen
  * waarschuwingen

---

## 7. Rol van AI-frameworks (pilot)

### 7.1 Positie

AI-frameworks worden **instrumenteel** ingezet:

* geen workflow-regie
* geen persistente state
* geen directe graph-mutaties

### 7.2 Keuze

* **CrewAI**: optioneel, voor rolvaste facilitator-agent
* **LangChain**: voor contextselectie en promptstructuur
* **AutoGen**: niet nodig in de pilot

---

## 8. Implementatie-aanpak (stapsgewijs)

### Stap 1 – Technische basis

* mono-repo in VS Code
* FastAPI backend
* verbinding met bestaande Neo4j graph

### Stap 2 – Causal Workspace

* eenvoudige frontend voor:

  * factoren
  * causal claims
* real-time updates (polling of websockets)

### Stap 3 – CAUSA-agent v1

* agent kan:

  * huidige causal claims lezen
  * vragen genereren
  * suggesties formuleren

### Stap 4 – Samenwerkingsscenario

* minimaal scenario:

  * twee gebruikers
  * één versterkende loop
  * agent herkent patroon en stelt vraag

### Stap 5 – Reflectie en bijstelling

* evalueren:

  * helpt de agent het gesprek?
  * worden aannames explicieter?
* pas daarna abstraheren of formaliseren

---

## 9. Succescriteria voor de pilot

De pilot is geslaagd als:

* meerdere mensen tegelijk kunnen werken
* causaliteit explicieter en rijker wordt
* onzekerheden zichtbaar blijven
* de agent het denkproces verdiept
* niemand de agent als autoriteit ervaart

---

## 10. Bewuste keuzes (niet gedaan)

* geen volledig metamodel
* geen formele ontologie
* geen automatische causal discovery
* geen besluitvorming door AI

Deze keuzes houden de pilot werkbaar en leerzaam.

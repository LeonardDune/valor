---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ["docs/causa_concept.md"]
date: 2026-01-07
author: Renzo
---

# Product Brief: causa-agent

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

CAUSA is een gespecialiseerde AI-agent binnen een onderzoeksprogramma naar AI-ondersteunde Value-Based Ecosystems Design (VBED) voor publieke dienstverlening. Als open source pilot draagt CAUSA bij aan de verbetering van gezamenlijk causaal begrip in complexe maatschappelijke vraagstukken, met als doel de kwaliteit, snelheid en samenhang van ecosysteemontwerpen in de publieke sector te verbeteren.

Het kernprobleem dat CAUSA adresseert is het structureel tekortschieten in gezamenlijk causaal begrip bij complexe maatschappelijke dossiers, waar causale redeneringen impliciet, fragmentarisch en persoonsgebonden blijven. Dit leidt tot suboptimale interventies die dezelfde ongewenste dynamieken reproduceren.

CAUSA faciliteert realtime collaborative causal modeling via een Neo4j-based workspace, waar teams simultaan werken aan gedeelde causale modellen. De agent versterkt het menselijke denkproces door patroonherkenning, vraagstelling en structurele ondersteuning, terwijl alle mutaties door mensen worden gevalideerd. Onzekerheid wordt first-class behandeld via expliciete claims met polariteit, zekerheid en status.

---

## Core Vision

### Problem Statement

Bij complexe maatschappelijke vraagstukken werken meerdere mensen gelijktijdig aan oorzaken en gevolgen, maar falen zij structureel in het vormen en onderhouden van een gedeeld causaal begrip. Causale redeneringen blijven impliciet en fragmentarisch, probleemdefinities verschuiven per overleg, feedbacklussen worden zelden gezamenlijk gevalideerd, en historische inzichten verdwijnen bij personeelswisselingen. Dit resulteert in suboptimale interventies die symptoombestrijdend zijn of elkaar onbedoeld tegenwerken.

### Problem Impact

Het probleem wordt het meest intens ervaren door professionals in het midden tussen beleid, uitvoering en verantwoording: beleidsmedewerkers, ketenregisseurs, uitvoerende professionals en procesbegeleiders. Zij zien het systeem wél, voelen dat het misgaat in de causaliteit, maar missen instrumenten om dit gedeeld, expliciet en overdraagbaar te maken.

### Why Existing Solutions Fall Short

Huidige causal loop diagrammen en systeemkaarten zijn statisch, individueel gericht en maken onzekerheid onzichtbaar. Tools als Vensim, Insight Maker of Miro ondersteunen wel visualisatie, maar niet realtime multi-user samenwerking, versiebeheer of systematische validatie van alternatieve perspectieven. Workshops en documentatie zijn arbeidsintensief en fragiel bij personeelswisselingen.

### Proposed Solution

CAUSA biedt een realtime collaborative causal workspace gebouwd op Neo4j, waar teams simultaan werken aan gedeelde causale modellen. De agent faciliteert het denkproces door vragen te stellen, patronen te herkennen en inconsistenties te signaleren, terwijl alle mutaties door mensen worden gevalideerd. Onzekerheid wordt first-class behandeld via expliciete claims met polariteit, zekerheid en status.

De agent integreert als gespecialiseerde component in een multi-agent VBED architectuur, gevoed door een gedeelde ontologische kennisbasis over waarden, rechtsbetrekkingen, capabilities en middelen.

### Key Differentiators

**Unieke combinatie van collaborative causal modeling en AI-facilitatie** die realtime multi-user samenwerking mogelijk maakt met expliciete onzekerheidshandling.

**Mens-in-de-loop principe** waar AI versterkt in plaats van vervangt, met volledige menselijke controle over modelmutaties.

**Integratie in onderzoeksprogramma voor VBED** dat ontologiegedreven AI-ondersteuning biedt voor waardegericht ecosysteemontwerp.

**Open source pilot aanpak** gericht op institutionalisering van causal reasoning in publieke sector ontwerppraktijken.

**Focus op reflectievermogen** door systematische explicitering van aannames, alternatieven en onzekerheden in causale redeneringen.

---

## Target Users

### Primary Users

#### **Lisa van der Berg - VBED Analist bij Ministerie van Justitie**
**Context:** 42 jaar, senior beleidsmedewerker met 15 jaar ervaring in complexe maatschappelijke dossiers. Werkt aan jeugdcriminaliteit en slachtofferzorg ecosystemen.

**Motivaties:** Wil onderbouwde, evidence-based beleid maken dat echt werkt. Frustreert zich aan "beleid dat op gevoel gemaakt wordt". Doel: interventies die meetbare impact hebben.

**Probleem Ervaring:**
- Moet constant schakelen tussen Excel sheets, PowerPoint diagrammen en vergaderverslagen
- Verliest overzicht wanneer stakeholders hun eigen "waarheden" inbrengen
- Bestrijdt symptomen in plaats van oorzaken door gebrek aan gedeeld causaal begrip
- Voelt zich verantwoordelijk maar machteloos bij falende interventies

**Succes Visie:**
"Als ik met één klik kan zien hoe alle factoren samenhangen, inclusief waar mensen het oneens over zijn, dan kan ik eindelijk beleid maken dat écht verschil maakt."

#### **Marcus de Vries - Ketenregisseur bij Gemeente Amsterdam**
**Context:** 38 jaar, ervaren procesarchitect die samenwerkingsverbanden coördineert tussen politie, justitie, jeugdzorg en gemeenten.

**Motivaties:** Wil naadloze samenwerking tussen organisaties bereiken. Doel: systemen die werken voor burgers, niet voor organisaties.

**Probleem Ervaring:**
- Bestrijdt dagelijks "organisatie-ego's" die samenwerking blokkeren
- Verliest energie aan het herhalen van dezelfde discussies bij personeelswisselingen
- Mist tools om complexe afhankelijkheden zichtbaar te maken voor stakeholders
- Voelt zich facilitator in plaats van regisseur door gebrek aan gedeelde inzichten

**Succes Visie:**
"Als ik een tool heb die automatisch inconsistenties signaleert en alternatieve perspectieven zichtbaar maakt, kan ik eindelijk échte ketensamenwerking organiseren."

#### **Dr. Fatima Al-Rashid - Academisch onderzoeker VBED**
**Context:** 45 jaar, universitair docent en onderzoeker die VBED methodologie ontwikkelt en toepast in publieke sector pilots.

**Motivaties:** Wil wetenschappelijke inzichten praktisch toepasbaar maken. Doel: brug slaan tussen theorie en praktijk in publieke dienstverlening.

**Probleem Ervaring:**
- Frustreert zich aan de kloof tussen academische modellen en praktijk
- Moet constant vertalen tussen formele ontologieën en dagelijkse besluitvorming
- Verliest momentum wanneer pilots blijven steken in theoretische discussies
- Mist instrumenten om reflectie en validatie systematisch te organiseren

**Succes Visie:**
"Als CAUSA de vertaalslag maakt tussen ontologische modellen en dagelijkse praktijk, dan kunnen we eindelijk evidence-based ecosysteem design mainstream maken."

### Secondary Users

#### **Jan-Peter Visser - Data Analist bij Inspectie Veiligheid & Justitie**
**Context:** 35 jaar, data-specialist die monitoring en evaluatie van keteninterventies ondersteunt.

**Motivaties:** Wil data-driven inzichten leveren die echt gebruikt worden. Doel: brug tussen cijfers en menselijke verhalen.

**Probleem Ervaring:**
- Produceert rapporten die niemand leest vanwege gebrek aan context
- Mist verband tussen kwantitatieve data en kwalitatieve causaliteit
- Frustreert zich aan "data als doel op zich" in plaats van middel
- Kan niet meedoen aan strategische discussies zonder causal inzicht

**Succes Visie:**
"Als ik data kan verbinden met gedeelde causal modellen, dan worden mijn analyses eindelijk relevant voor besluitvorming."

### User Journey

#### **Ontdekkingsfase**
- **VBED Analist:** Ontdekt CAUSA tijdens onderzoek naar nieuwe VBED tools
- **Ketenregisseur:** Wordt geïntroduceerd door collega tijdens ketenoverleg
- **Data Analist:** Hoor erover tijdens evaluatie workshop

#### **Onboarding**
- **Dag 1:** Account aanmaken, eerste causal workspace openen
- **Week 1:** Basis tutorial doorlopen, eerste simpele model maken
- **Maand 1:** Uitnodigen van eerste collega's voor gezamenlijke sessie

#### **Kern Gebruik**
- **Dagelijks:** Controleren van updates in lopende modellen
- **Wekelijks:** Deelnemen aan collaborative sessions
- **Maandelijks:** Review van modelontwikkeling en inzichten

#### **Succes Moment**
- **"Aha!"** Wanneer eerste inconsistentie wordt gesignaleerd en opgelost
- **Validatie** Wanneer stakeholder zegt: "Dit hadden we eerder moeten doen"
- **Impact** Wanneer beleid gebaseerd op gedeeld model meetbare resultaten oplevert

#### **Langetermijn Integratie**
- **Routine:** CAUSA wordt standaard tool in VBED proces
- **Uitbreiding:** Integratie met bestaande systemen en workflows
- **Adoptie:** Wordt verwacht instrument voor nieuwe projecten

---

## Success Metrics

### User Success Metrics

**Gedeeld begrip ontstaat**
- Teams kunnen gezamenlijk een causal model beschrijven en uitleggen
- Deelnemers herkennen zowel eigen inzichten als die van anderen
- Causaliteit wordt expliciet en traceerbaar met volledige metadata

**Samenwerking verloopt sneller en effectiever**
- Minder tijd kwijt aan uitleggen van impliciete aannames
- Realtime multi-user iteraties met minder misverstanden
- Traceerbare historie van modelontwikkeling

**Reflectie en discussie verbeteren**
- Alternatieve scenario's naast elkaar zichtbaar en bespreekbaar
- Inconsistente aannames worden gesignaleerd en geadresseerd
- Onzekerheden en betwiste claims expliciet vastgelegd

### Business Objectives (Onderzoeksimpact)

**Bijdrage aan VBED methodologie**
- Verbetering van kwaliteit, snelheid, volledigheid en reflectievermogen in ecosysteemontwerp
- Institutionalisering van causal reasoning in publieke sector ontwerppraktijken
- Herbruikbaar ecosysteem van causal maps over projecten en domeinen

**Wetenschappelijke en maatschappelijke relevantie**
- Ontologiegedreven AI-ondersteuning voor complexe ontwerpactiviteiten
- Evidence-based ecosysteem design mainstream in publieke dienstverlening
- Nieuwe generatie ontwerppraktijken met semantisch bewuste AI agents

### Key Performance Indicators

**Kwaliteit van causal modeling**
- Aantal expliciete causal claims per workshop/sessie (target: 15-25 per uur)
- Percentage claims met volledige metadata (zekerheid, polariteit, auteur) (target: >90%)
- Mate van consolidatie tussen gebruikersversies (target: >80% overlap)

**Snelheid en efficiëntie**
- Tijd om causale map op te stellen voor complex vraagstuk (target: <4 uur voor initiële model)
- Aantal iteraties nodig voor consensus (target: <3 iteraties)
- Gebruikerstevredenheid met efficiëntie (target: >7/10 op Likert-schaal)

**Volledigheid en dekking**
- Percentage geïdentificeerde factoren vs. domeinrelevante factoren (target: >85%)
- Aantal geïdentificeerde loops en feedbackrelaties (target: 5-10 per complex vraagstuk)
- Dekking van kernproblemen en interventiepaden (target: >90%)

**Reflectievermogen en discussiekwaliteit**
- Aantal vastgelegde alternatieve scenario's per sessie (target: 3-5)
- Acceptatiegraad van CAUSA suggesties (target: >60%)
- Aantal interacties per gebruiker per sessie (target: 10-15)

**Gebruikservaring en adoptie**
- Frequentie van gebruik binnen VBED projecten (target: wekelijks per actief project)
- Aantal multi-user sessies vs. solo werk (target: >70% collaborative)
- Adoptiegraad in pilotorganisaties (target: >50% van doelgebruikers actief)

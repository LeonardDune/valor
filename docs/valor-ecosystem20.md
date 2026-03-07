# VALOR Ecosysteem
## Een Epistemisch Platform voor Waardegedreven Publieke Dienstverlening

**Versie** | 1.1
**Datum** | maart 2026
**Status** | Definitief
---

## 1. Visie en Positionering

### 1.1 Het probleem

Maatschappelijke vraagstukken — schuldenproblematiek, klimaatadaptatie, zorgtoegankelijkheid, digitale inclusie — zijn per definitie complex. Ze kennen meerdere oorzaken, raken meerdere belangen, worden beoordeeld vanuit meerdere waarden, en vragen om oplossingen die juridisch houdbaar, procesmatig uitvoerbaar en democratisch legitiem zijn. Tegelijkertijd zijn de mensen die aan die oplossingen werken zelden experts op alle relevante domeinen tegelijk: een beleidsmedewerker kent de juridische context maar niet de systeemwereld; een burger kent de leefwereld maar niet de wetgeving; een ontwerper kent de gebruikerservaring maar niet de ontologische structuur van het domein.

Bestaande tools voor beleidsontwerp, participatie en kennismanagement behandelen deze perspectieven als aparte werelden. Een causaal diagram in Vensim communiceert niet met een stakeholderanalyse in Miro, die niet communiceert met een juridisch advies in Word, die niet communiceert met een procesontwerp in BPMN. De kennis die in elk van die tools is opgebouwd, blijft geïsoleerd. Verbanden worden niet gelegd. Spanningen blijven onzichtbaar. Beslissingen worden genomen zonder de consequenties in andere perspectieven te overzien.

Het gevolg: oplossingen die juridisch kloppen maar de verkeerde oorzaken adresseren. Processen die efficiënt zijn maar waarden schenden. Interventies die voor betrokkenen onbegrijpelijk zijn omdat de rationale verloren is gegaan.

### 1.2 De VALOR-visie

VALOR is een epistemisch platform voor het gezamenlijk ontwerpen van oplossingen voor maatschappelijke vraagstukken. Het integreert meerdere perspectieven op hetzelfde ontologische fundament, zodat verbanden tussen perspectieven zichtbaar zijn, spanning ertussen bespreekbaar wordt, en beslissingen traceerbaar worden vastgelegd.

De kern van VALOR is een radicale architectuurkeuze: **alle perspectieven zijn van meet af aan uitgedrukt in dezelfde ontologische taal** — gUFO, de Gentle Unified Foundational Ontology. Een causaal gevolg is een `gufo:Situation`. Een stakeholder is een `gufo:Agent`. Een norm is een sociaal object uit UFO-L. Er is geen vertaling nodig tussen perspectieven, omdat ze allemaal op hetzelfde fundament zijn gebouwd. Wat wél verschilt per perspectief is uitsluitend de presentatie: de visuele taal, de terminologie, de interactiepatronen die aansluiten bij de denk- en werkwijze van de deelnemers.

Elk modelleerelement in VALOR is een **claim over de werkelijkheid** — een bewering over hoe de wereld is (as-is) of zou moeten worden (to-be). Claims kunnen worden voorgesteld, betwist, onderbouwd met bewijs, aangenomen of verworpen. Faseovergangen en definitieve ontwerpkeuzes zijn formele besluitvormingsmomenten waaraan deelnemers democratisch bijdragen. De volledige redeneergeschiedenis van een ontwerp — welke claims zijn gemaakt, door wie, op basis van welk bewijs, met welke tegenwerpingen, en hoe is uiteindelijk besloten — is traceerbaar vastgelegd en te allen tijde te reconstrueren.

AI-agents nemen deel aan het ontwerpproces als **Socratische gesprekspartners**: deelnemers die door vragen stellen, alternatieven voorleggen en consequenties van keuzes zichtbaar maken de kwaliteit van het model verbeteren — zonder ooit te beslissen wat erin komt.

### 1.3 Wat VALOR niet is

VALOR is geen besluitvormingssysteem dat uitkomsten produceert. Het faciliteert het besluitvormingsproces, maar de beslissingen worden genomen door mensen. VALOR is geen experttool die alleen toegankelijk is voor ontologen of informatici. Deelnemers werken in hun eigen taal en perspectief, zonder kennis van de onderliggende ontologische structuur te hoeven verwerven. VALOR is geen neutraal registratiesysteem. Het is een actief epistemisch instrument: het maakt spanningen zichtbaar die anders verborgen zouden blijven, stelt vragen die anders niet gesteld zouden worden, en borgt dat de redenering achter een ontwerp niet verloren gaat.

### 1.4 Kernbegrippen

**Issue.** Een maatschappelijk vraagstuk: een situatie in de werkelijkheid die door betrokken partijen als problematisch wordt ervaren en om een gedeelde oplossing vraagt. In VALOR uitgedrukt als een `ufoc:SocialObject` dat bestaat doordat een gemeenschap van agents een gedeeld `ufoc:Concern` heeft over een onderliggende `gufo:Situation` (de toestand van de wereld die als problematisch wordt ervaren). Een Issue is daarmee een sociaal construct — het bestaat doordat agents het als zodanig constitueren — niet door de toestand van de wereld zelf. De link naar die toestand wordt vastgelegd via `valor:concernedWithSituation`.

**Design Space.** De gestructureerde ontwerpomgeving voor één Issue. Bevat alle perspectieven, alle alternatieven, alle fasen, alle claims en alle besluitvormingsepisodes die betrekking hebben op dat Issue. Meerdere Design Spaces kunnen gelijktijdig actief zijn in VALOR.

**Perspectief.** Een gefocuste view op de ontologische graph van een Design Space, in de taal en visuele notatie die past bij een specifieke manier van denken over het Issue. VALOR kent zeven perspectieven: Causa, Lexa, Acta, Socia, Axia, Delibera en Forma (zie Hoofdstuk 4).

**Fase.** Een afgebakende periode in de lifecycle van een Design Space, geïnspireerd op Design Thinking maar aanpasbaar per vraagstuk. Na elke fase wordt democratisch besloten welke elementen van het model worden meegenomen naar de volgende fase.

**Alternatief.** Een coherente verzameling to-be claims die een mogelijke oplossingsrichting beschrijft. Meerdere alternatieven kunnen parallel bestaan binnen een Design Space en onafhankelijk van elkaar worden uitgewerkt, maar delen een gemeenschappelijke as-is beschrijving van het Issue.

**Claim.** Elk modelleerelement in VALOR — elke node, relatie, kardinaliteit, waarde-oordeel — is een claim over de werkelijkheid. Claims hebben een epistemische status (voorgesteld, betwist, aangenomen, verworpen, heroverwogen) en kunnen worden onderbouwd met bewijs. De claim-structuur is het hart van VALOR's epistemische architectuur. Elke claim is een **Tessera**: een bouwsteen van het mozaïek dat het ontwerp vormt.

**Tessera.** De systeemnaam voor een claim als bouwsteen. Naar het Latijnse *tessera*: het tegeltje waarmee een Romein toegang kreeg tot een vergadering, en de bouwsteen van een mozaïek. Elke Tessera heeft een auteur, een tijdstempel, een epistemische status, een verzameling ondersteunend of weerleggend bewijs, en argumentatierelaties met andere Tesserae.

**Besluitvormingsepisode.** Een formeel moment waarop deelnemers democratisch besluiten over de epistemische status van een set Tesserae — bij een faseovergang of bij de vaststelling van een definitief ontwerp. Besluitvormingsepisodes zijn zelf gemodelleerd als `gufo:Event`-instanties met volledige provenance.

**Socratische Agent.** Een AI-agent die deelneemt aan ontwerpprocessen als gesprekspartner zonder stemrecht. De agent stelt vragen, legt alternatieven voor, maakt gevolgen van keuzes zichtbaar — maar beslist nooit. Zie Hoofdstuk 5.

---

## 2. VALOR-O: De Basis-Ontologie

### 2.1 Architectuurprincipe

De basis-ontologie van VALOR — VALOR-O — is de gemeenschappelijke ontologische fundering waarop alle perspectieven, alle claims, alle besluitvormingsepisodes en alle ontwerpfasen zijn gebouwd. VALOR-O is een domeinontologie op ecosysteemniveau, gebouwd bovenop gUFO en de relevante UFO-extensies.

VALOR-O bestaat uit vier lagen die van abstract naar concreet gaan:

```
┌─────────────────────────────────────────────────────────┐
│  Laag 4: VALOR Toepassingsontologie                      │
│  (Issue, Design Space, Fase, Alternatief, Deelnemer)     │
├─────────────────────────────────────────────────────────┤
│  Laag 3: Epistemische module                             │
│  (Tessera, Bewijs, Argumentatie, Besluitvormingsepisode) │
├─────────────────────────────────────────────────────────┤
│  Laag 2: UFO-extensies                                   │
│  (UFO-B, UFO-C, UFO-L, Decision ontology,               │
│   CLD-formalisering, Actor Analysis, VSD)               │
├─────────────────────────────────────────────────────────┤
│  Laag 1: gUFO                                            │
│  (Taxonomy of Individuals + Taxonomy of Types)           │
└─────────────────────────────────────────────────────────┘
```

Alle perspectieven bevragen en beschrijven dezelfde VALOR-O graph via SPARQL-projecties. Er is geen aparte datastore per perspectief. Een `valor:Agent` (Socia) die een privacybelang heeft is exact dezelfde resource als de drager van dat belang in de Axia-view en de participant in een besluitvormingsepisode in Delibera.

### 2.2 Laag 1: gUFO

De onderste laag is gUFO v1.0 in zijn volledigheid: de Taxonomy of Individuals (Endurant, Event, Situation, AbstractIndividual en hun specialisaties) en de Taxonomy of Types (EndurantType, EventType, SituationType en de rigiditeits- en sortaliteitshiërarchie). gUFO fungeert als de universele ontologische grondtaal. Alle concepten in de hogere lagen zijn specialisaties of instanties van gUFO-concepten.

De OWL 2 punning-conventie — waarbij een klasse tegelijkertijd een `owl:Class` (subklasse-hiërarchie) en een `rdf:type gufo:Kind` (type-hiërarchie) is — wordt door VALOR-O als standaardpatroon gehanteerd voor alle domeinconcepten.

### 2.3 Laag 2: UFO-extensies

**UFO-B — Events en perdurants.** De volledige ontologie van events, participaties en causale afhankelijkheden. UFO-B voegt toe: onderscheid tussen atomaire en complexe events, temporele kwalificatie van participaties, en causale afhankelijkheidsrelaties. Fundeert Causa en Acta.

**UFO-C — Sociale entiteiten.** Agents met intenties, commitments, sociale objecten, normen als sociale objecten. Een `valor:Stakeholder` is een `ufoc:Agent` met intentionele `gufo:IntrinsicMode`s (doelen, belangen, zorgen). Commitments zijn Relators tussen agents die een normatieve verwachting uitdrukken. Fundeert Socia en Delibera.

**UFO-L — Rechtsbetrekkingen.** Normen, rechten, plichten, bevoegdheden, rechtspersonen. Een vergunningsbevoegdheid is een `ufol:Right` dat inhereerst aan een institutionele agent via een normatieve `gufo:Situation`. Wetgeving is een sociaal object dat normatieve situaties instelt. Uitgebreid door Weigand et al. (2024) met een policy-ontologie: organisatiebeleid is een bundel van rechten en plichten (`ufol:Policy`) die inhereert aan een organisatorische agent via een delegatieverhouding, nadrukkelijk onderscheiden van het beleidsdocument als artifact. Fundeert Lexa.

**Decision ontology (COoDM).** De Core Ontology on Decision Making (Guizzardi, Carneiro, Porello 2020) modelleert beslissingen als intenties met een doel waarvan de propositiële inhoud wordt gerealiseerd door een situatie voortgebracht via een handeling. De deliberatie die aan de beslissing voorafgaat is een event getriggerd door een onbevredigde intentionele toestand. Preferenties zijn gemodelleerd als value ascriptions — geloofstoestandsIntrinsicModes met betrekking tot waarde-ervaringen. Fundeert Delibera. Uitgebreid door Weigand et al. (2024) met policy-grondslag.

**COVER — Common Ontology of Value and Risk.** Guizzardi c.s. hebben waarde uitgedrukt in UFO via de COVER-ontologie. Waarden zijn daarin gemodelleerd als typen (`valor:ValueType`) waarvan *value experiences* de instanties zijn — kwaliteiten die inhereren aan agents in concrete situaties. Dit is een hybride positie die zowel het objectieve karakter van waarden (als type) als hun subjectieve beleving (als kwaliteit van een agent in een situatie) uitdrukt. VALOR-O volgt deze formalisering direct: de VSD-spanning tussen subjectivistische en objectivistische waardenpositie is hiermee opgelost door Guizzardi's eigen werk. Fundeert Axia volledig.

**DEMO — Enterprise Ontology (Dietz/Mulder).** DEMO modelleert organisaties als netwerken van transacties tussen actor roles. De kernstructuur is het Complete Transaction Pattern (CTP): request → promise → execute → accept, met coördinatie-acts en productie-acts als onderscheiden acttypen. DEMO onderscheidt drie organisatielagen: de B-organisatie (ontologisch, de essentie), de I-organisatie (infologisch) en de D-organisatie (datalogisch). Een bestaand paper (Almeida c.s., EEWC 2013) revisiteert het DEMO-transactiepatroon expliciet in UFO/OntoUML: sociale relaties in transacties worden gemodelleerd als `ufoc:Commitment`-Relators, het transactiepatroon wordt volledig uitgedrukt in OntoUML. DEMO hoeft daarmee niet opnieuw geformaliseerd te worden — de bridge met UFO is al gelegd. Fundeert Acta als transactioneel perspectief op dienstverlening: een publieke dienst is geen procesflow maar een netwerk van transacties tussen burger en overheid als actor roles.

**Policy Analysis of Multi-Actor Systems (Enserink et al., TU Delft).** Het standaardwerk op het vakgebied beleidsanalyse in multi-actorsystemen. Kernmethoden: systeemsanalyse (Causa), actoranalyse (Socia), en onzekerheidsanalyse. Het boek introduceert een cruciale dimensie die VALOR-O moet ondersteunen: **onzekerheid als expliciete eigenschap van claims**. Onzekerheid varieert van statistisch risico (kansverdelingen bekend) tot diepe onzekerheid (geen overeenstemming over modellen of waarden). In VALOR-O: elke Tessera draagt een `valor:UncertaintyLevel`-annotatie conform de PAMS-taxonomie. Fundeert de epistemische module aanvullend op de IBIS-argumentatiestructuur.

**Causal Loop Diagram-formalisering.** Variabelen als `gufo:Quality`-types die inhereren aan objecten of situaties. Causale relaties als specialisaties van `gufo:contributedToTrigger` met polariteit (versterkend/dempend) en vertraging als `gufo:IntrinsicMode`. Feedback loops als cyclische relatiepatronen identificeerbaar via SPARQL. Fundeert Causa.

**Actor Analysis (i*-framework).** Hard goals als intentionele `gufo:IntrinsicMode`s van actors; soft goals als preferentiële IntrinsicModes; taken als `gufo:EventType`s; intentionele afhankelijkheden als `ufoc:Commitment`-Relators met specifieke modaliteit. Fundeert Socia aanvullend op UFO-C.

**Public Service Ecosystem (Osborne 2022).** Het integratieve raamwerk van Osborne beschrijft waardecreatie in publieke dienstverlening als een ecosysteem-fenomeen over vier niveaus: institutioneel, service, individueel en beliefs. Waarde wordt co-gecreëerd in dynamische interacties, niet lineair geproduceerd door organisaties. Dit raamwerk fungeert als de overkoepelende theoretische legitimatie van VALOR als platform: VALOR is zelf een instrument voor waardeco-creatie in een publiek service ecosysteem. De vier niveaus van Osborne zijn herkenbaar in VALOR-O: `valor:InstitutionalContext`, `valor:ServiceRelation` (DEMO-transactie), `valor:IndividualExperience` (kwaliteitsIntrinsicMode van een burger-agent), en `valor:BeliefSituation` (normatieve en epistemische situaties).

De formalisering van de niet-standaard elementen (CLD, i*-Actor Analysis) is onderdeel van de VALOR-O onderzoeksworkstream (zie Hoofdstuk 12). DEMO, COVER, COoDM, policy-ontologie en PAMS zijn gedeeltelijk al geformaliseerd en vereisen integratie en aanpassing, geen nieuwe formalisering van de grond af.

### 2.4 Laag 3: De epistemische module

De epistemische module is uniek voor VALOR en heeft geen directe voorloper in de UFO-literatuur. Ze formaliseert de claim-structuur die het hart vormt van VALOR's epistemologie.

**Tessera (Claim).** Elke Tessera is een reïficatie van een statement over de werkelijkheid — een triple of een samenhangende verzameling triples — met de volgende eigenschappen:

- `valor:claimContent` — de mensleesbare inhoud van de claim als `rdf:langString`, zoals de indiener die heeft geformuleerd; de formele ontologische structuur wordt vastgelegd via perspectief-specifieke properties
- `valor:epistemicStatus` — één van: `Proposed`, `Contested`, `Accepted`, `Rejected`, `Reconsidered`
- `valor:claimType` — `AsIs` (beschrijft de huidige werkelijkheid) of `ToBe` (beschrijft een gewenste toekomstige werkelijkheid)
- `valor:claimedBy` — de agent (menselijk of AI) die de claim heeft voorgesteld
- `valor:claimedAt` — tijdstempel
- `valor:inAlternative` — het alternatief waarbinnen de claim geldt (optioneel; claims zonder alternatief gelden voor alle alternatieven)
- `valor:inPhase` — de ontwerpfase waarin de claim is gemaakt

**Bewijs.** Een `valor:Evidence` is een informatieobject (publicatie, onderzoeksrapport, ervaringsverslag, databestand) dat een Tessera ondersteunt of ondermijnt. Bewijs heeft een type (`valor:EvidenceType`: empirisch, theoretisch, ervaringskennis, expert judgement), een bron, en een sterkte-indicatie.

**Argumentatierelaties.** Tesserae staan in argumentatierelaties tot elkaar: `valor:supports`, `valor:undermines`, `valor:qualifies`, `valor:presupposes`. Deze relaties vormen de argumentatienetwerk-structuur (IBIS-geïnspireerd) die de redeneergeschiedenis van een ontwerp vastlegt.

**Besluitvormingsepisode.** Een `valor:DecisionEpisode` is een `gufo:Event` waarbij een verzameling `valor:Participant`s een besluit neemt over de epistemische status van een set Tesserae. Een episode heeft: een tijdstip, de deelnemende agents, de stemmen (als anonieme of gedeanonimiseerde IntrinsicModes), de uitkomst (welke Tesserae worden aangenomen/verworpen), en een link naar het sessielogboek.

### 2.5 Laag 4: De VALOR toepassingsontologie

De bovenste laag modelleert de VALOR-specifieke structuren die de ontwerpomgeving organiseren.

Een `valor:Issue` is een `ufoc:SocialObject` — een maatschappelijk vraagstuk dat bestaat doordat een gemeenschap van agents een gedeeld `ufoc:Concern` heeft over een onderliggende `gufo:Situation`. Het Issue is daarmee een sociaal construct (het bestaat in virtue van collectieve intentionaliteit), nadrukkelijk onderscheiden van de situatie in de werkelijkheid die aanleiding geeft. Die situatie wordt vastgelegd via `valor:concernedWithSituation`. Een Issue heeft een domein, een scope-beschrijving, en is gelinkt aan de agents die er een zorg-IntrinsicMode ten aanzien van hebben (`valor:hasConcernedAgent`).

Een `valor:DesignSpace` is een `gufo:FunctionalComplex` die het geheel van modelleerelementen, perspectieven, alternatieven, fasen en besluitvormingsepisodes voor één Issue omvat. Een DesignSpace heeft een lifecycle conform het gekozen fasemodel.

Een `valor:DesignPhase` is een `gufo:Situation` met temporele begrenzing, een status (`Active`, `Closed`, `Archived`) en een faseovergang-event dat de Besluitvormingsepisode bevat.

Een `valor:DesignAlternative` is geïmplementeerd als een **named graph** in GraphDB. Alternatieven delen de as-is Tesserae (gemeenschappelijke named graph) maar bevatten elk hun eigen to-be Tesserae. Alternatieven kunnen worden vergeleken via SPARQL-queries over meerdere named graphs.

Een `valor:Participant` is een `ufoc:Agent` met een rol (`Initiator`, `Contributor`, `Expert`, `Observer`, `Facilitator`, `Engineer`) binnen een specifieke DesignSpace. Deelname is per uitnodiging en rol-afhankelijk voor besluitvorming. Initiator en Contributor hebben stemrecht; de overige rollen niet.

---

## 3. Claim-architectuur en Epistemische Statusmachine

### 3.1 Elke modelleerelement is een Tessera

In VALOR is er geen onderscheid tussen "het model" en "de discussie over het model". Elk element dat een deelnemer toevoegt — een stakeholder, een causaliteitsrelatie, een norm, een waarde-afweging, een processtap — is onmiddellijk een Tessera: een claim over de werkelijkheid met een epistemische status en een auteur.

Dit heeft een fundamentele UX-consequentie: de modelleervlakken in de verschillende perspectieven zijn niet neutrale tekenborden maar **epistemische ruimten**. Wanneer een deelnemer een causaliteitsrelatie tekent in Causa, stelt hij daarmee een claim voor: "Ik beweer dat X bijdraagt aan Y." Die claim is zichtbaar voor andere deelnemers, kan worden betwist, kan worden onderbouwd met bewijs, en wordt uiteindelijk — via een Besluitvormingsepisode — aangenomen of verworpen.

De epistemische status van een Tessera bepaalt haar zichtbaarheid en gewicht in het model: alleen aangenomen Tesserae dragen bij aan de "canonieke" weergave van het ontwerp. Voorgestelde en betwiste Tesserae zijn zichtbaar maar visueel onderscheiden. Verworpen Tesserae zijn gearchiveerd maar niet verwijderd — ze maken deel uit van de redeneergeschiedenis.

### 3.2 De epistemische statusmachine

Elke Tessera doorloopt een levenscyclus van epistemische statussen:

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

**Proposed.** De initiële status van elke nieuwe Tessera. De claim is zichtbaar voor alle deelnemers in de relevante DesignSpace maar nog niet beslecht.

**Contested.** Eén of meer deelnemers hebben een tegenwerping ingediend — een argumentatierelatie `valor:undermines` van een andere Tessera, of een expliciete betwisting. De betwisting zelf is ook een Tessera, met haar eigen epistemische status.

**Accepted.** De claim is aangenomen via een Besluitvormingsepisode. Aangenomen Tesserae vormen de canonieke representatie van het ontwerp in de betreffende fase.

**Rejected.** De claim is verworpen via een Besluitvormingsepisode. De Tessera blijft bewaard in de redeneergeschiedenis maar draagt niet bij aan het canonieke model.

**Reconsidered.** Een eerder aangenomen of verworpen Tessera wordt heroverwogen — doorgaans omdat nieuw bewijs beschikbaar is of omdat de context is gewijzigd. De Tessera keert terug naar Proposed met een link naar de oorspronkelijke besluitvormingsepisode en een toelichting op de reden voor heroverweging.

### 3.3 Bewijs en argumentatie

Een Tessera kan worden onderbouwd met `valor:Evidence`. Bewijs heeft vier typen:

- **Empirisch bewijs** — kwantitatieve of kwalitatieve onderzoeksresultaten (design science, action research, statistieken, evaluatieonderzoek)
- **Theoretisch bewijs** — wetenschappelijke theorieën of modellen die de claim ondersteunen of ondermijnen
- **Ervaringskennis** — kennis opgedaan door directe ervaring met het vraagstuk (burgers, uitvoerders, professionals)
- **Expert judgement** — beargumenteerde oordelen van domeinexperts

Bewijs is zelf ook een Tessera — het kan worden betwist ("dit onderzoek heeft methodologische beperkingen"), aangevuld ("er is ook tegenbewijs") of heroverwogen. Zo ontstaat een gelaagd argumentatienetwerk dat de volledige redeneergeschiedenis van een ontwerp vastlegt.

### 3.4 As-is en to-be

Elke Tessera heeft een claimtype: **as-is** of **to-be**.

As-is Tesserae beschrijven de huidige werkelijkheid waarin het Issue zich afspeelt: hoe werkt het systeem nu, welke actoren spelen welke rol, welke normen gelden, wat zijn de causale mechanismen die het probleem in stand houden. As-is Tesserae zijn gedeeld over alle alternatieven — ze vormen de gemeenschappelijke probleemanalyse.

To-be Tesserae beschrijven een gewenste toekomstige werkelijkheid: hoe zou het systeem moeten werken, welke nieuwe actoren of rollen zijn nodig, welke normen moeten worden gewijzigd, welke causale ketens worden doorbroken of gecreëerd. To-be Tesserae zijn specifiek voor een alternatief — verschillende alternatieven bevatten verschillende, soms conflicterende sets to-be Tesserae.

---

## 4. De Zeven Perspectieven

### 4.1 Architectuur van de perspectieven

Alle perspectieven zijn **SPARQL-projecties** op dezelfde VALOR-O graph. Een perspectief bestaat uit: een perspectief-ontologie (een OWL-module die de relevante subset van VALOR-O beschrijft), een set SPARQL-queries die die subset ophalen, en een UI-module die de resultaten visualiseert in de taal van het perspectief. Deelnemers zien alleen de elementen die relevant zijn voor hun perspectief, in de terminologie en visuele notatie die bij hun denk- en werkwijze past.

Wanneer een deelnemer in een perspectief een element toevoegt of wijzigt, wordt dat onmiddellijk vertaald naar VALOR-O triples — als een nieuwe Tessera met status Proposed. Die Tessera is direct zichtbaar in alle andere perspectieven die er een view op hebben.

### 4.2 Causa — Het causale perspectief

**Theoretische basis.** Causal Loop Diagrams (Forrester/Meadows), Causal Inference (Pearl), systeemdenken.

**Wat wordt gemodelleerd.** Oorzaak-gevolgketens, versterkende en dempende terugkoppelingen, vertraagde effecten, systeemgrenzen. Causa maakt zichtbaar welke mechanismen het Issue in stand houden en welke interventies welke effecten hebben.

**Kernconcepten in VALOR-O.** Variabelen als `gufo:Quality`-types die inhereren aan objecten of situaties. Causale relaties als specialisaties van `gufo:contributedToTrigger` met polariteits- en vertragings-attributen. Feedback loops als cyclische patronen in de relatie-graph. Interventies als `gufo:EventType`s die de waarde van een variabele beïnvloeden.

**Visuele notatie.** Cirkels of rechthoeken voor variabelen, pijlen met `+`/`-` voor causale relaties, dubbele pijlen voor vertraagde effecten, `R`/`B` labels voor reinforcing en balancing loops.

**Typische deelnemers.** Beleidsanalisten, systeemdenkers, onderzoekers, betrokken burgers die het probleem vanuit hun ervaring kennen.

**Tessera-voorbeelden in Causa.** "Schuldenproblematiek leidt tot verminderde arbeidsparticipatie" (as-is, causaliteitsrelatie). "De interventie 'schuldhulpverlening' vermindert de schuldenlast" (to-be, interventie-effect).

### 4.3 Lexa — Het normatieve perspectief

**Theoretische basis.** UFO-L rechtsbetrekkingen (Guizzardi c.s.), rechtstheorie, institutionele ontologie.

**Wat wordt gemodelleerd.** Wetten, regels, normen, rechten, plichten, bevoegdheden, rechtspersonen. Lexa maakt zichtbaar welke normatieve structuren het Issue omgeven: welke rechten hebben betrokkenen, welke plichten rusten op uitvoerders, welke bevoegdheden kent de wet toe, en hoe verhouden die normatieve structuren zich tot de gewenste oplossing.

**Kernconcepten in VALOR-O.** `ufol:Norm` als sociaal object (UFO-C) dat normatieve situaties instelt. `ufol:Right` en `ufol:Duty` als IntrinsicModes van institutionele agents. `ufol:LegalRelator` als Relator die rechtsbetrekkingen tussen agents uitdrukt. `ufol:Authority` als bevoegdheid die conditioneel rechten en plichten toekent.

**Visuele notatie.** Genormaliseerde kaders voor normen, pijlen voor normadressering (norm → plichtsdrager), sloten voor bevoegdheden, ketenen voor verplichtingen.

**Typische deelnemers.** Juristen, beleidsmakers, compliance-officers, belangenbehartigers.

**Tessera-voorbeelden in Lexa.** "Artikel 12 Grondwet verleent iedere burger het recht op eerbiediging van de persoonlijke levenssfeer" (as-is). "De nieuwe verordening legt gemeenten een informatieplicht op jegens schuldenaren" (to-be).

### 4.4 Acta — Het transactieperspectief

**Theoretische basis.** DEMO Enterprise Ontology (Dietz/Mulder), UFO-B events en perdurants, service design. Het DEMO-transactiepatroon is door Almeida c.s. (2013) al geformaliseerd in UFO/OntoUML, wat directe integratie in VALOR-O mogelijk maakt.

**Wat wordt gemodelleerd.** Dienstverlening als een netwerk van transacties tussen actor roles — niet als een procesflow maar als een samenstel van verzoek-belofte-uitvoering-acceptatie-cycli. Acta maakt zichtbaar wie welke transacties initieert en uitvoert, welke producten of diensten worden geleverd, en welke commitments daarin worden aangegaan. Het Complete Transaction Pattern (CTP) van DEMO is de structurerende eenheid: elke interactie tussen burger en overheid is een transactie met een initiator, een executor, een resultaat en een acceptatiemoment.

**Kernconcepten in VALOR-O.** `valor:Transaction` als specialisatie van `ufoc:Commitment`-Relator conform het DEMO-transactiepatroon. `valor:ActorRole` als `«role»` van een `ufoc:Agent` in een transactiecontext. `valor:CoordinationAct` en `valor:ProductionAct` als specialisaties van `gufo:EventType` conform DEMO's onderscheid. `gufo:broughtAbout` voor de relatie tussen een productie-act en de voortgebrachte situatie (het transactieresultaat). DEMO's drie organisatielagen (B/I/D) zijn representeerbaar als drie niveaus van `valor:OrganizationalLayer`.

**Visuele notatie.** DEMO Construction Diagram (CD)-stijl: cirkels voor transacties, pijlen voor transactie-afhankelijkheden — vereenvoudigd voor niet-experts. Alternatief: swim-lane weergave per actor role, herkenbaar als BPMN maar semantisch gegrond in DEMO.

**Typische deelnemers.** Uitvoerders, service designers, procesverantwoordelijken, burgers die de dienstverlening vanuit hun perspectief beschrijven.

**Tessera-voorbeelden in Acta.** "De burger initieert een aanvraagtransactie; de gemeente is executor en levert een beschikking als transactieresultaat" (as-is). "De schuldhulpverlener committeert zich aan een saneringsplan als resultaat van een coöperatieve transactie met de burger" (to-be).

### 4.5 Socia — Het stakeholderperspectief

**Theoretische basis.** UFO-C sociale entiteiten, Actor Analysis (i* framework), Value Sensitive Design (directe en indirecte stakeholders).

**Wat wordt gemodelleerd.** Actoren, hun belangen, doelen, afhankelijkheden, machtsverhoudingen en onderlinge commitments. Socia maakt zichtbaar wie er belang bij heeft, wat ze willen, en hoe ze van elkaar afhankelijk zijn.

**Kernconcepten in VALOR-O.** `ufoc:Agent` als specialisatie van `gufo:Object` met intentionele `gufo:IntrinsicMode`s. `valor:Interest` als type van IntrinsicMode dat een belang uitdrukt. `valor:Goal` als intentionele IntrinsicMode die een gewenste situatie beschrijft. `ufoc:Commitment` als Relator die een afhankelijkheid of toezegging uitdrukt tussen agents. `valor:PowerRelation` als comparatieve relatie die machtsverhoudingen uitdrukt.

**Visuele notatie.** Cirkels voor actoren, wolken voor doelen, pijlen voor afhankelijkheden met sterkte-indicatie, kleurcodering voor mate van belang of invloed.

**Typische deelnemers.** Beleidsmakers, burgers, vertegenwoordigers van belangengroepen, sociale wetenschappers.

**Tessera-voorbeelden in Socia.** "De schuldenaar heeft als primair belang het herstel van financiële zelfredzaamheid" (as-is). "De incassobranche heeft een financieel belang bij het voortduren van betalingsachterstanden" (as-is, betwistbaar).

### 4.6 Axia — Het waardeperspectief

**Theoretische basis.** COVER — Common Ontology of Value and Risk (Guizzardi c.s.), Value Sensitive Design (Friedman c.s.), waarde-pluralisme (Berlin, Williams), Public Service Ecosystem (Osborne 2022).

**Wat wordt gemodelleerd.** Waarden die op het spel staan, spanningen tussen waarden, afwegingscriteria en de gevolgen van ontwerpkeuzes voor verschillende waarden. Axia maakt zichtbaar welke waarden in het ontwerp in het geding zijn en hoe alternatieve ontwerpen zich daartoe verhouden.

**Kernconcepten in VALOR-O.** VALOR-O volgt Guizzardi's COVER-ontologie: waarden zijn `valor:ValueType`s (objectieve typen) waarvan *value experiences* de instanties zijn — `gufo:Quality`s die inhereren aan agents in concrete situaties. Dit lost de subjectief/objectief-spanning in VSD op: een waarde als privacy bestaat als objectief type én als individuele ervaring van een agent in een situatie. `valor:ValueTension` is een `gufo:Situation` waarbij twee of meer value experiences in conflict zijn. `valor:DesignImplication` verbindt een Tessera (ontwerpkeuze) met de value type(s) die ze beïnvloedt. De vier niveaus van Osborne (institutioneel, service, individueel, beliefs) zijn representeerbaar als contextniveaus waarop value experiences plaatsvinden.

**Visuele notatie.** Zeshoeken voor value types (waardekaart), pijlen voor ondersteunende of ondermijnende relaties tussen Tesserae en waarden, heatmap-overlay die toont welke waarden door een specifiek alternatief worden beïnvloed.

**Typische deelnemers.** Ethici, beleidsfilosofen, burgers, vertegenwoordigers van getroffen groepen, bestuurders.

**Tessera-voorbeelden in Axia.** "Geautomatiseerde schuldsignalering dient de waarde Efficiëntie maar genereert een value experience van Privacy-schending bij burgers" (to-be, waarde-implicatie). "Er bestaat een ValueTension tussen Zelfredzaamheid en Bescherming in de context van schuldhulpverlening" (as-is).

### 4.7 Delibera — Het besluitvormingsperspectief

**Theoretische basis.** Decision ontology (Guizzardi/Mylopoulos), deliberatieve democratietheorie (Habermas, Fishkin), IBIS (Rittel/Webber).

**Wat wordt gemodelleerd.** Besluitvormingsepisodes, de argumentatienetwerken die eraan ten grondslag liggen, de uitkomsten en hun rationale. Delibera is het perspectief dat de democratische besluitvormingsdimensie van VALOR zichtbaar maakt.

**Kernconcepten in VALOR-O.** `valor:DecisionEpisode` als `gufo:Event` met participerende agents en uitkomst-situatie. `valor:Vote` als IntrinsicMode van een Participant die een positie ten aanzien van een Tessera uitdrukt. `valor:ArgumentationNetwork` als samenhangende verzameling Tesserae en hun argumentatierelaties. `valor:PhaseTransition` als bijzonder type DecisionEpisode dat de lifecycle van een DesignSpace voortstuwt.

**Visuele notatie.** Tijdlijn van besluitvormingsepisodes, argumentatiediagram (IBIS-stijl: Issues, Positions, Arguments), stemoverzichten, faseovergangen als mijlpalen.

**Typische deelnemers.** Alle deelnemers; Delibera is het perspectief dat voor iedereen toegankelijk is en de democratische dimensie van het proces borgt.

### 4.8 Forma — Het ontologische perspectief

**Theoretische basis.** gUFO volledig, OntoUML 2.0, formele ontologie.

**Wat wordt gemodelleerd.** De volledige ontologische structuur van het domein — alle concepten, relaties, kardinaliteiten, stereotypen — in OntoUML-notatie. Forma is de expert-view: de technische representatie van het model in zijn volledige precisie.

**Kernconcepten in VALOR-O.** Alle 21 OntoUML klasse-stereotypen en 21 relatie-stereotypen. Generalisatiehiërarchieën, Relators, Modes, Qualities, Events, Situations — in volledige OntoUML-notatie met tagged values en SHACL-validatie.

**Visuele notatie.** OntoUML 2.0 volledige notatie: stereotypelabels, kardinaliteiten, diamanten voor compositie, gestippelde pijlen voor dependentie, open driehoeken voor generalisatie.

**Typische deelnemers.** Ontologie-engineers, informatieanalisten, architecten. Forma is niet bedoeld als primaire interface voor domeinexperts of burgers, maar is te allen tijde beschikbaar voor technische validatie en voor deelnemers die de onderliggende structuur willen inspecteren.

---

## 5. AI Agents als Socratische Gesprekspartner

### 5.1 Positionering

AI Agents in VALOR zijn **Socratische gesprekspartners**: deelnemers die door het stellen van gerichte vragen, het aandragen van alternatieven en het blootleggen van impliciete aannames de kwaliteit van het model verbeteren — zonder ooit te beslissen wat erin komt. Een agent die zegt "dit klopt niet" creëert afhankelijkheid en ondermijnt eigenaarschap. Een agent die vraagt "wat bedoel je precies als je zegt dat schuldenaren niet willen meewerken — is dat altijd zo, of alleen onder bepaalde omstandigheden, en wat zou dat onderscheid betekenen voor jullie ontwerp?" dwingt tot scherper denken zonder de beslissing over te nemen.

Agents nemen deel aan sessies als uitgenodigde gesprekspartner **zonder stemrecht**. Ze stellen vragen, leggen alternatieven voor en maken gevolgen van keuzes zichtbaar — maar bepalen nooit wat de groep besluit. Een agent kan een verschil van inzicht documenteren als informatie voor de groep, niet als bezwaar. Agents spreken op uitnodiging of op door de facilitator ingestelde momenten — nooit proactief tussendoor. Agent-inbreng is in de sessie-interface visueel onderscheiden van menselijke inbreng. Deelnemers kunnen agent-suggesties negeren zonder registratie als "afwijking".

### 5.2 Agents per perspectief

Elk perspectief heeft een eigen Socratische agent, gekalibreerd op de denk- en werkwijze van dat perspectief. De agents zijn niet zeven aparte systemen maar zeven configuraties van dezelfde onderliggende agent-architectuur, met perspectief-specifieke systeemprompten, context-selectie en vraagstrategieën.

**Causa-agent.** Stelt vragen over de volledigheid en correctheid van causale ketens. Signaleert mogelijke terugkoppelingen die niet zijn meegenomen, vraagt naar vertraagde effecten, en daagt uit om de systeemgrens te expliciteren. *"Jullie model toont dat schuldhulpverlening de schuldenlast vermindert. Maar vermindert het ook de kans op nieuwe schulden? En zo niet — wat ontbreekt er dan nog in het model?"*

**Lexa-agent.** Stelt vragen over normatieve volledigheid en juridische houdbaarheid. Signaleert mogelijke conflicten tussen normen, vraagt naar de juridische grondslag van bevoegdheden, en daagt uit om de reikwijdte van rechten en plichten te expliciteren. *"Jullie beschrijven een informatieplicht voor gemeenten. Op welke wet is die gebaseerd? En geldt die plicht ook voor uitbestede uitvoering?"*

**Acta-agent.** Stelt vragen over procesvolledigheid, uitzonderingsgevallen en uitvoerbaarheid. *"Wat gebeurt er als de burger de aanvraag niet volledig invult? Is er een herstelstap, en wie is verantwoordelijk?"*

**Socia-agent.** Stelt vragen over vergeten stakeholders, verborgen belangen en machtsdynamieken. *"Ik zie incassobureaus niet terug in jullie stakeholderkaart. Zijn die relevant voor dit vraagstuk? En zo ja — wat is hun belang?"*

**Axia-agent.** Stelt vragen over waarde-implicaties van ontwerpkeuzes en onontdekte spanningen. *"Jullie kiezen voor geautomatiseerde signalering. Hoe verhoudt die keuze zich tot de waarde menselijke waardigheid? En wie draagt de last als het systeem een fout maakt?"*

**Delibera-agent.** Stelt vragen over de kwaliteit van het besluitvormingsproces zelf: zijn alle stemmen gehoord, zijn de argumenten helder gearticuleerd, zijn de consequenties van het besluit duidelijk? *"Drie deelnemers hebben deze claim betwist maar nog geen tegenargument ingediend. Willen jullie die ruimte geven voordat de stemming plaatsvindt?"*

**Forma-agent.** Stelt vragen over ontologische precisie en gUFO-conformiteit, gericht aan engineers. *"Je modelleert 'Aanvraag' als een Kind. Maar kan een Aanvraag bestaan zonder een specifieke Burger die hem indient? Als dat niet kan, is het misschien een Relator."*

### 5.3 Technische architectuur van de agents

Elke agent-aanroep bevat als context: de relevante delen van de VALOR-O graph (als Turtle), de perspectief-ontologie, de casus-beschrijving, de sessiehistorie (eerdere vragen, antwoorden en besluiten), en de epistemische status van de relevante Tesserae. Zonder volledige context zijn agent-vragen te generiek om waardevol te zijn.

Elke agent-uiting bevat drie elementen: de vraag of het alternatief zelf, de redenering (welk principe, welke domeinkennis, welke VALOR-O structuur ligt ten grondslag), en een zekerheidsaanduiding ("dit is een standaard patroon in vergelijkbare ontologieën" vs. "dit is een open vraag waarover experts van mening verschillen").

Alle agent-inbreng wordt gelogd als onderdeel van de Tessera-geschiedenis: elke vraag van een agent is een `valor:AgentTessera` met de agent als claimant, zichtbaar in Delibera als onderdeel van het argumentatienetwerk.

### 5.4 Het spanningsveld van invloed zonder stemrecht

Een agent die altijd beschikbaar is, altijd articuleert en nooit sociaal ongemak ervaart, heeft een structureel voordeel in een groepsdiscussie — ook zonder formele beslissingsmacht. Dit risico vraagt om expliciete governance:

De facilitator heeft een **agent-stilte-modus** voor momenten waarop de groep zonder AI-ondersteuning wil delibereren. Na afloop van een sessie genereert het systeem een **agent-invloedrapport**: hoeveel van de aangenomen Tesserae zijn voorgesteld of actief gestimuleerd door een agent? Als dat percentage structureel hoog is, is dat een signaal dat de Socratische rol niet goed wordt ingevuld. Deelnemers kunnen op elk moment alle agent-Tesserae tegelijk verbergen, zodat alleen de menselijke inbreng zichtbaar is.


---

## 6. Design Lifecycle en Fasemodel

### 6.1 Fasen als ontologische structuur

De lifecycle van een Design Space is niet alleen een projectmanagementconstructie — het is een ontologische structuur in VALOR-O. Elke fase is een `valor:DesignPhase` met temporele begrenzing, een status en een set criteria die bepalen wanneer de fase kan worden afgesloten. De overgang van de ene naar de volgende fase is een `valor:PhaseTransition`: een Besluitvormingsepisode waaraan alle actieve deelnemers bijdragen.

### 6.2 Het standaardfasemodel

VALOR biedt een standaardfasemodel geïnspireerd op Design Thinking, maar het fasemodel is configureerbaar per Design Space. Andere modellen — zoals dubbele diamant, agile sprints of beleidslevenscyclus — zijn als alternatieve fasemodellen beschikbaar.

**Fase 1: Verkenning (Empathize & Define)**

Doel: het Issue begrijpen vanuit de ervaringen van betrokkenen en de as-is werkelijkheid in kaart brengen. Primaire perspectieven: Causa (welke mechanismen), Socia (wie zijn betrokken), Lexa (welk normkader). Output: een gevalideerde set as-is Tesserae die het Issue beschrijven.

Faseovergang-criterium: alle deelnemers zijn het eens over de as-is beschrijving als voldoende basis voor het ontwerp. Niet alle Tesserae hoeven aangenomen te zijn — maar de scope van het Issue is beslecht.

**Fase 2: Probleemanalyse (Define & Ideate)**

Doel: de diepere oorzaken en structuren van het Issue analyseren en eerste ontwerprichtingen verkennen. Primaire perspectieven: Causa (oorzaak-gevolganalyse), Axia (welke waarden staan op het spel), Delibera (welke issues zijn het meest urgent). Output: een gevalideerde probleemstructuur en een eerste set to-be Tesserae per alternatief.

Faseovergang-criterium: er is overeenstemming over welke alternatieven verder worden uitgewerkt en welke worden gesloten.

**Fase 3: Ontwerp (Prototype)**

Doel: de geselecteerde alternatieven uitwerken in alle relevante perspectieven. Alle perspectieven actief. Output: volledig uitgewerkte alternatieven als coherente sets Tesserae over alle perspectieven heen, inclusief onderlinge consistentie.

Faseovergang-criterium: elk alternatief is voldoende uitgewerkt voor vergelijking en beoordeling. SHACL-validatie in Forma slaagt voor alle aangenomen Tesserae.

**Fase 4: Afweging (Test & Decide)**

Doel: de alternatieven vergelijken, de gevolgen voor waarden en stakeholders expliciteren, en democratisch besluiten welk alternatief of welke combinatie wordt aanbevolen. Primaire perspectieven: Axia (waarde-afweging), Socia (stakeholdereffecten), Delibera (besluitvorming). Output: een aanbeveling met volledige rationale.

**Fase 5: Documentatie (Implement)**

Doel: het gekozen ontwerp en de volledige redeneergeschiedenis documenteren voor implementatie, verantwoording en toekomstige heroverweging. Output: exporteerbaar ontwerpdocument, VALOR-O export als Turtle, en een leesbaar verantwoordingsverslag.

### 6.3 Alternatieven en scenario's

Binnen een Design Space kunnen meerdere alternatieven parallel worden uitgewerkt. Alternatieven worden aangemaakt bij de overgang naar Fase 3. Ze delen de as-is Tesserae uit Fasen 1 en 2 maar bevatten elk hun eigen to-be Tesserae.

Alternatieven zijn geïmplementeerd als **named graphs** in GraphDB, met een gedeelde named graph voor de as-is Tesserae. SPARQL-queries kunnen over meerdere named graphs heen opereren, waardoor alternatieven direct vergelijkbaar zijn: welke Tesserae zijn uniek voor alternatief A, welke zijn gedeeld, welke zijn conflicterend?

Deelnemers kunnen worden uitgenodigd voor de uitwerking van een specifiek alternatief — of voor alle alternatieven. Een deelnemer die aan meerdere alternatieven werkt ziet visueel welk alternatief actief is en kan schakelen tussen alternatieven.

### 6.4 Democratische besluitvorming bij faseovergangen

Bij elke faseovergang vindt een Besluitvormingsepisode plaats. De facilitator kondigt de episode aan, geeft deelnemers tijd om openstaande Tesserae te beoordelen, en opent dan de stemronde.

Stemmechanisme: deelnemers geven voor elke Tessera met status Proposed of Contested een positie: Accepteren, Verwerpen, of Uitstellen (voor verder beraad). Anoniem of gedeanonimiseerd, configureerbaar per Design Space.

Drempelwaarden: configureerbaar per Design Space. Standaard: een Tessera wordt aangenomen bij eenvoudige meerderheid; bij meer dan 30% Verwerpen is de Tessera betwist en komt ze voor nader beraad; bij unanimiteit is de aanname definitief.

Het systeem toont na de episode: hoeveel Tesserae zijn aangenomen, hoeveel verworpen, hoeveel uitgesteld. Voor uitgestelde Tesserae wordt een volgende bespreekmomenten ingepland.

---

## 7. Gebruikers, Rollen en Uitnodigingsmodel

### 7.1 Gebruikersmodel

VALOR is een multi-tenant platform. Meerdere organisaties of initiatieven kunnen gelijktijdig actief zijn, elk met hun eigen Design Spaces, deelnemers en Tesserae. Er is geen centrale autoriteit die beslist over de inhoud van Design Spaces — die autoriteit ligt bij de deelnemers zelf, georganiseerd conform de democratische principes van het ecosysteem.

Elke gebruiker is een `valor:Participant` — een `ufoc:Agent` met een identiteit, rollen en een persoonlijke bijdragegeschiedenis. Gebruikers kunnen aan meerdere Design Spaces deelnemen, met mogelijk verschillende rollen per Design Space.

### 7.2 Rollen

**Initiator.** De partij die een Design Space aanmaakt en de initiële framing van het Issue bepaalt. De Initiator heeft geen bijzondere besluitvormingsbevoegdheid maar draagt verantwoordelijkheid voor de governance-configuratie (fasemodel, stemmechanisme, uitnodigingsbeleid).

**Facilitator.** Verantwoordelijk voor het begeleiden van sessies, het bewaken van de democratische kwaliteit van het proces, en het beheren van agent-configuratie. De Facilitator heeft geen extra stemgewicht maar kan procedurele beslissingen nemen (agent-stilte, uitstel van stemming).

**Contributor.** Actieve deelnemer die Tesserae kan toevoegen, betwisten en onderbouwen, en die deelneemt aan Besluitvormingsepisodes. De primaire rol voor domeinexperts, burgers en uitvoerders.

**Expert.** Domein- of methodologisch expert die Tesserae kan toevoegen en beoordelen maar geen stemrecht heeft in Besluitvormingsepisodes. Experts dragen bij aan de kwaliteit van het model zonder de democratische besluitvorming te domineren.

**Observer.** Leestoegang tot de Design Space, inclusief alle Tesserae en besluitvormingsepisodes. Geen schrijftoegang. Geschikt voor bestuurders, journalisten, onderzoekers die het proces willen volgen.

**Engineer.** Toegang tot Forma (de ontologische view) en tot de SHACL-validator en SPARQL-editor. Verantwoordelijk voor de technische kwaliteit van de VALOR-O representatie. Heeft geen bijzondere stemrechten maar kan technische bezwaren registreren als Tessera.

### 7.3 Uitnodigingsmodel

Deelname aan een Design Space is **per uitnodiging**. De Initiator stelt de initiële deelnemerslijst samen en kan de uitnodigingsbevoegdheid delegeren aan Contributors.

Uitnodigingen zijn rol-specifiek en kunnen tijdgebonden zijn: een burger kan worden uitgenodigd voor de Verkenningsfase maar niet voor de Ontwerpfase, of voor een specifiek perspectief (alleen Socia en Axia) maar niet voor Forma.

Uitnodigingen bevatten: de Design Space, de rol, de perspectieven waartoe toegang wordt verleend, de fasen waarvoor de uitnodiging geldt, en een persoonlijke toelichting van de uitnodigende partij. Uitgenodigde gebruikers die nog geen VALOR-account hebben, ontvangen een uitnodigingslink waarmee ze een account kunnen aanmaken.

### 7.4 Transparantie en privacy

Alle bijdragen van Contributors zijn standaard zichtbaar voor alle deelnemers in dezelfde Design Space — inclusief wie welke Tessera heeft voorgesteld. Dit borgt transparantie en verantwoordelijkheid.

Per Design Space kan de Initiator kiezen voor **gepseudonimiseerde bijdragen**: deelnemers zijn zichtbaar voor de facilitator maar verschijnen voor andere deelnemers als een pseudoniem. Dit is relevant voor vraagstukken waarbij deelnemers anders sociaal druk zouden ervaren om bepaalde posities niet in te nemen.

Stemmen in Besluitvormingsepisodes zijn configureerbaar als anoniem of gedeanonimiseerd. Anoniem stemmen verlaagt de drempel voor afwijkende posities; gedeanonimiseerd stemmen verhoogt de verantwoordelijkheid.

---

## 8. Technische Architectuur

### 8.1 Overzicht

VALOR is een gedistribueerde webapplicatie met een modulaire architectuur. De kerncomponenten zijn: de VALOR-O graph database, de perspectief-engines, de Tessera-engine, de sessie- en besluitvormingsmodule, en de agent-laag.

```
┌─────────────────────────────────────────────────────────────────┐
│                        VALOR Frontend                            │
│  React + TypeScript │ React Flow │ Perspective UI Modules        │
│  Causa │ Lexa │ Acta │ Socia │ Axia │ Delibera │ Forma           │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                        VALOR Backend                             │
│  Node.js + Fastify                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Tessera API  │  │ Session API  │  │ Perspective Query API  │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  Agent API   │  │  Auth / IAM  │  │  Export / Import API   │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────────┐
        ▼                    ▼                         ▼
┌──────────────┐   ┌─────────────────┐   ┌────────────────────────┐
│   GraphDB    │   │  OWL Reasoner   │   │   Anthropic API        │
│  (VALOR-O)   │   │  HermiT / ELK   │   │  (Socratische Agents)  │
└──────────────┘   └─────────────────┘   └────────────────────────┘
```

### 8.2 Graph database

**Ontotext GraphDB Enterprise** als primaire triplestore, vanwege: volledige SHACL-ondersteuning, OWL reasoning, named graph-beheer voor alternatieven, en SPARQL 1.1 inclusief property paths (nodig voor feedback loop detectie in Causa).

Named graph-structuur per Design Space:
- `valor:{designspace}/base` — de VALOR-O basis-ontologie (read-only)
- `valor:{designspace}/asis` — gedeelde as-is Tesserae
- `valor:{designspace}/alternative/{id}` — to-be Tesserae per alternatief
- `valor:{designspace}/decisions` — Besluitvormingsepisodes en stemhistorie
- `valor:{designspace}/agents` — agent-Tesserae (vragen en suggesties)
- `valor:{designspace}/provenance` — PROV-O provenance voor alle Tesserae

### 8.3 Tessera-engine

De Tessera-engine is de centrale component die alle schrijfoperaties naar de graph coördineert. Elke modelwijziging — vanuit welk perspectief dan ook — wordt door de Tessera-engine omgezet naar: een nieuwe triple of set triples in de relevante named graph, een bijbehorende `valor:Tessera`-resource met epistemische metadata, en een PROV-O provenance record.

De engine is verantwoordelijk voor: Tessera-aanmaak en statusbeheer, conflictdetectie (twee conflicterende Tesserae in hetzelfde alternatief), en notificatie van relevante deelnemers bij nieuwe of betwiste Tesserae.

### 8.4 Perspectief-engines

Elke perspectief-engine bestaat uit: een SPARQL-querybibliotheek die de relevante subset van VALOR-O ophaalt, een transformatiefunctie die de SPARQL-resultaten omzet naar de datastructuur van de perspectief-UI, en een schrijffunctie die UI-interacties omzet naar Tessera-aanroepen.

Perspectief-engines zijn declaratief gedefinieerd via perspectief-ontologieën — OWL-modules die de relevante concepten en relaties beschrijven. Dit maakt het toevoegen van nieuwe perspectieven mogelijk zonder nieuwe UI-code te schrijven, zolang de perspectief-ontologie voldoende declaratief is.

### 8.5 OWL redeneerder

HermiT (volledige OWL DL) voor consistentiechecks bij Fase-overgangen en voor de Forma-view. ELK (OWL EL, aanzienlijk sneller) voor real-time inferentie tijdens modellering. De redeneerder draait als een aparte Java-service (asynchrone aanroepen vanuit de backend).

### 8.6 Agent-laag

De Socratische agents worden aangedreven door de Anthropic API (Claude). Elke agent-aanroep bevat als context: de relevante VALOR-O subgraph als Turtle (via SPARQL construct), de perspectief-ontologie, de casus-beschrijving, de sessiehistorie, en de epistemische status van relevante Tesserae. Agents schrijven nooit direct naar de graph — hun uitingen worden via de Tessera-engine geregistreerd als `valor:AgentTessera`.

### 8.7 Frontend

React + TypeScript als basisframework. React Flow voor de grafische modelleervlakken in Causa, Socia, Acta en Forma — met custom node- en edge-types per perspectief. Zustand voor state management. Tailwind + shadcn/ui voor de UI-componenten. Monaco Editor voor de SPARQL-interface in Forma. Yjs (CRDT) voor real-time samenwerking in sessies.

### 8.8 Authenticatie en autorisatie

OAuth 2.0 + OpenID Connect voor authenticatie. RBAC (Role-Based Access Control) op Design Space niveau: elke resource in de graph is getagd met de Design Space en het perspectief waartoe ze behoort, en toegangscontrole wordt afgedwongen op API-niveau. Rollen en perspectieftoegang zijn per Design Space configureerbaar door de Initiator.

### 8.9 Export en import

Vanuit VALOR exporteerbaar:
- Volledige VALOR-O graph als Turtle, RDF/XML of JSON-LD
- Geselecteerde alternatieven als OntoUML JSON (conforming to OntoUML Vocabulary v1.1.0)
- Besluitvormingshistorie als PROV-O Turtle
- Leesbaar verantwoordingsverslag als HTML of PDF (gegenereerd op basis van Tessera-metadata)
- Perspectief-specifieke exports: Causa als CLD-diagram (SVG/PNG), Acta als BPMN XML, Socia als stakeholderkaart

Importeerbaar:
- Bestaande gUFO/OntoUML Turtle-bestanden als beginpunt voor een Design Space
- OntoUML JSON v1.1.0
- Eerder geëxporteerde VALOR Design Spaces (voor archief of hergebruik)

---

## 9. Toegankelijkheid en Participatieontwerp

### 9.1 Toegankelijkheid als eerste eis

Deelnemers in VALOR zijn zelden ontologie-engineers. Een beleidsmedewerker, een schuldhulpverlener, een burger met schuldenproblematiek — zij moeten zinvol kunnen bijdragen aan een Design Space zonder te weten wat een `gufo:Relator` is of wat het verschil is tussen een `«role»` en een `«subkind»`.

Dit vereist een **radicale scheiding tussen de modelleertaal (VALOR-O/gUFO) en de participatietaal** (de taal van het perspectief en het domein). Deelnemers zien nooit gUFO-terminologie tenzij ze expliciet kiezen voor de Forma-view. Ze zien de concepten en relaties van hun perspectief, in de taal die zij kennen.

### 9.2 Intuïtieve perspectief-interfaces

Elke perspectief-UI is ontworpen volgens de principes van het perspectief — niet als een generieke graafeditor met een ander label. Causa voelt als een systeemdenkdiagram. Socia voelt als een stakeholderkaart. Axia voelt als een waardencanvas. De interactiepatronen zijn zo vertrouwd mogelijk: drag-and-drop, directe tekstinvoer, suggestieversieringen.

Nieuwe elementen worden toegevoegd via **perspectief-specifieke invoerpatronen**: in Causa beschrijft een deelnemer in een tekstveldje een oorzaak-gevolgrelatie in gewone taal ("meer schuldhulpverleners leidt tot kortere wachttijden"), en het systeem — ondersteund door de Tessera-engine en eventueel de Socratische agent — vertaalt dat naar een VALOR-O triple en vraagt de deelnemer te bevestigen dat de weergave klopt.

### 9.3 Terugkoppeling in eigen taal

Alle systeemfeedback — validatieberichten, agent-vragen, statuswijzigingen — is geformuleerd in de taal van het perspectief. Wanneer de SHACL-validator een inconsistentie detecteert in de Forma-representatie van een Causa-Tessera, ziet de Causa-deelnemer niet een SHACL-foutmelding maar een begrijpelijke vraag: "Je hebt een relatie getekend van X naar Y, maar Y is nog niet gedefinieerd als onderdeel van dit vraagstuk. Bedoel je een nieuwe factor toe te voegen?"

### 9.4 Progressieve ontsluiting

Deelnemers die meer willen weten over de ontologische structuur achter hun perspectief, kunnen die laag geleidelijk ontsluiten. Een "meer informatie"-knop bij elk element toont: wat is dit in VALOR-O termen, welke gUFO-concepten zijn betrokken, welke andere perspectieven zien dit element ook. Dit maakt VALOR ook een leeromgeving voor ontologisch denken — voor wie dat wil.

---

## 10. Sessiebeheer en Procesondersteuning

### 10.1 Sessiearchitectuur

Een modelleersessie in VALOR is een tijdgebonden, gefaciliteerde bijeenkomst van deelnemers die samen werken aan één of meer perspectieven van een Design Space. Sessies kunnen fysiek, online of hybride zijn. De VALOR-interface ondersteunt real-time samenwerking via Yjs CRDT.

**Voorbereiding.** De facilitator configureert de sessie: actief perspectief, actieve fase, actieve alternatieven, uitgenodigde deelnemers, en agent-configuratie (welke agents actief, op welke momenten). Het systeem laadt de relevante context voor de Socratische agents.

**Werksessie.** Deelnemers modelleren in hun perspectief. Nieuwe elementen zijn direct zichtbaar voor alle andere deelnemers. De Tessera-engine registreert elke toevoeging als Proposed Tessera. De Socratische agent is beschikbaar op uitnodiging van de facilitator of op door de facilitator ingestelde triggers (bijvoorbeeld: na elke vijfde nieuwe Tessera wordt de agent uitgenodigd voor een reflectievraag).

**Plenaire bespreking.** Op verzoek van de facilitator of op een vooraf bepaald moment wordt het canvas bevroren en worden de nieuwste Tesserae besproken. Deelnemers kunnen Tesserae betwisten, onderbouwen of expliciet ondersteunen. De agent kan worden uitgenodigd voor een Socratische vraag.

**Sessieafsluiting.** De facilitator sluit de sessie. Het sessielogboek wordt automatisch gegenereerd: tijdstempel, deelnemers, nieuwe Tesserae, betwistingen, agent-interventies, en eventuele stemrondes. Het logboek is opgeslagen als PROV-O provenance in de graph.

### 10.2 Asynchroon werken

Niet alle bijdragen aan een Design Space vinden plaats in sessies. VALOR ondersteunt ook **asynchrone bijdragen**: deelnemers kunnen buiten sessies nieuwe Tesserae voorstellen, bestaande Tesserae betwisten, en bewijs uploaden. Asynchrone Tesserae worden gemarkeerd als "buiten sessie ingediend" en komen in de eerstvolgende sessie of Besluitvormingsepisode aan de orde.

### 10.3 Notificaties

Deelnemers ontvangen notificaties bij: nieuwe Tesserae in een Design Space waarvoor ze een actieve rol hebben, betwistingen van hun eigen Tesserae, agent-vragen die gericht zijn aan alle deelnemers, aankondiging van een Besluitvormingsepisode, en faseovergangen.

Notificatiefrequentie en -kanalen zijn per gebruiker configureerbaar.

---

## 11. Forma: De gUFO Ontologie-editor

### 11.1 Positie van Forma in VALOR

Forma is het ontologische perspectief van VALOR — de expert-view die de volledige VALOR-O structuur toont in OntoUML-notatie. Forma is tegelijkertijd de technische kern van het ecosysteem: alle Tesserae die in de andere perspectieven worden aangemaakt, zijn zichtbaar in Forma als ontologische elementen. En omgekeerd: ontologische precisie die in Forma wordt aangebracht, is direct zichtbaar in de relevante andere perspectieven.

Forma is niet bedoeld als primaire interface voor domeinexperts of burgers. Het is de werkplek van ontologie-engineers en technisch analytici die de ontologische kwaliteit van het model bewaken. Maar Forma is te allen tijde beschikbaar voor alle deelnemers die de onderliggende structuur willen inspecteren — transparantie is een kernwaarde van VALOR.

### 11.2 Volledige OntoUML-ondersteuning

Forma implementeert de volledige OntoUML 2.0 specificatie: alle 21 klasse-stereotypen en 21 relatie-stereotypen, met correcte visuele notatie, tagged values en SHACL-validatie.

**Klasse-stereotypen (21):**

Kern-sortalen: `«kind»`, `«collective»`, `«quantity»`, `«relator»`, `«mode»`, `«quality»`, `«subkind»`, `«role»`, `«phase»`

Niet-sortalen: `«category»`, `«mixin»`, `«roleMixin»`, `«phaseMixin»`

Events en situaties: `«event»`, `«situation»`

OntoUML 2.0-toevoegingen: `«historicalRole»`, `«historicalRoleMixin»`

Technisch: `«type»`, `«abstract»`, `«datatype»`, `«enumeration»`

**Relatie-stereotypen (21):**

Dependentierelaties (gestippelde pijlen): `«mediation»`, `«characterization»`, `«externalDependence»`, `«derivation»`, `«structuration»`, `«instantiation»`, `«manifestation»`, `«historicalDependence»`

Deel-geheel relaties (gedeelde diamant): `«componentOf»`, `«memberOf»`, `«subCollectionOf»`, `«subQuantityOf»`, `«containment»`

Event-relaties (volle pijlen): `«participation»`, `«participational»`, `«creation»`, `«termination»`, `«bringsAbout»`, `«triggers»`

Materieel/comparatief (volle lijnen): `«material»`, `«comparative»`

Generalisatie (open driehoek): `rdfs:subClassOf`

**OWL 2 Punning.** Forma ondersteunt en visualiseert de OWL 2 punning-conventie expliciet: een klasse zoals `Persoon` is tegelijkertijd een `owl:Class` (in de subklasse-hiërarchie) en een `rdf:type gufo:Kind` (in de type-hiërarchie). Forma toont deze dualiteit als een overlay op het canvas, schakelbaar per element.

### 11.3 Tessera-integratie in Forma

In Forma zijn alle Tesserae zichtbaar als ontologische elementen, gekleurd naar epistemische status: groen (Accepted), geel (Proposed), oranje (Contested), rood (Rejected). Engineers kunnen in Forma:

- Technische bezwaren registreren als `valor:EngineerTessera`: een Tessera die een ontologisch probleem signaleert en die zichtbaar is in Delibera als onderdeel van het argumentatienetwerk
- SHACL-validatierapport opvragen per alternatief of per fase
- OWL-consistentiecheck uitvoeren (asynchroon via HermiT)
- SPARQL-queries uitvoeren op de volledige VALOR-O graph via de Monaco-editor

### 11.4 SHACL-validatieregels

Forma valideert in real-time de gUFO-conformiteit van aangenomen Tesserae. Kernregels:

- Een `«kind»` kan niet specialiseren van een andere `«kind»`
- Een `«relator»` vereist ten minste twee `«mediation»`-relaties naar onderscheiden entiteiten
- Een `«mode»` of `«quality»` vereist een `«characterization»`-relatie met multipliciteit 1 aan de dragerkant
- Rigide typen kunnen niet specialiseren van anti-rigide typen
- Een `«role»` vereist een verbinding met een `«mediation»`-relatie
- Fasen komen in partities (complete + disjuncte generalisatieset)
- `«material»`-relaties zijn afgeleid en vereisen een `«derivation»`-relatie naar een `«relator»`

Validatieberichten worden in Forma getoond als inline waarschuwingen met een link naar het relevante gUFO-axioma en een uitleg-knop. In de andere perspectieven worden validatieproblemen vertaald naar perspectief-specifieke taal.

---

## 12. VALOR-O Onderzoeksworkstream

### 12.1 Karakter van het werk

VALOR-O kan niet worden gebouwd als een IT-project tussen de sprints door. De formalisering van UFO-extensies en niet-UFO theorieën is **wetenschappelijk onderzoek** met eigen methodologie, mijlpalen en kwaliteitscriteria. De onderzoeksworkstream loopt parallel aan — en voor een groot deel voorafgaand aan — de softwareontwikkeling.

De onderzoeksworkstream heeft vier fasen die gedeeltelijk parallel lopen.

### 12.2 Fase -1a: Inventarisatie (3 maanden)

Systematische inventarisatie van alle beschikbare UFO-extensies: welke zijn als OWL/TTL beschikbaar, welke bestaan alleen in publicaties, welke zijn gedeeltelijk geformaliseerd? Concrete producten:
- Inventaris van alle relevante Guizzardi c.s. publicaties met beschikbaarheidsbeoordeling per extensie
- Overzicht van OWL-bestanden beschikbaar via NEMO/LabES repositories
- Prioritering op basis van relevantie voor VALOR (UFO-C en UFO-B als hoogste prioriteit)
- Eerste contact met NEMO (LabES/UFES) voor samenwerking en toegang tot interne bestanden

### 12.3 Fase -1b: Integratie bestaande formaliseringen (4 maanden, deels parallel aan -1a)

Meerdere relevante bronnen zijn al gedeeltelijk geformaliseerd in UFO/OntoUML maar moeten worden geïntegreerd in VALOR-O als coherente modules. Per bron: beoordeling van beschikbaarheid als OWL-bestand, aanvulling van ontbrekende elementen, aanpassing aan gUFO-naamgevingsconventies, en SHACL-shapes voor validatie.

Prioriteitsvolgorde en specifieke integratiepunten:

*(1) UFO-C sociale entiteiten* — directe import, aanvulling met `valor:Stakeholder`, `valor:Interest`, `valor:Goal` als specialisaties.

*(2) UFO-B volledige events* — directe import, aanvulling met temporele kwalificatiepatronen voor Causa.

*(3) UFO-L rechtsbetrekkingen + Weigand policy-ontologie (2024)* — UFO-L importeren; de policy-ontologie van Weigand et al. integreren: `ufol:Policy` als bundel IntrinsicModes via delegatieverhouding, onderscheiden van `valor:PolicyDocument` als artifact. Fundeert Lexa volledig.

*(4) COoDM Decision ontology (Guizzardi, Carneiro, Porello 2020)* — integreren als `valor:Decision`-module met BDI-structuur, preferenties als value ascriptions, en deliberatie als event conform COoDM.

*(5) COVER Value ontology (Guizzardi c.s.)* — integreren als `valor:ValueType` en `valor:ValueExperience`-module. Lost de VSD-positievraag op. Geen nieuwe formalisering nodig, wel aanpassing aan VALOR-O naamruimte.

*(6) DEMO transactiepatroon in UFO (Almeida c.s., EEWC 2013)* — het bestaande OntoUML-model integreren als `valor:Transaction`-module. Aanvullen met de drie DEMO-organisatielagen (B/I/D) als `valor:OrganizationalLayer`-types. Maakt Acta als transactioneel perspectief mogelijk zonder nieuwe formalisering.

### 12.4 Fase -1c: Formalisering niet-geformaliseerde theorieën (6 maanden)

Twee theorieën vereisen nog substantieel formaliseringswerk omdat ze niet eerder in UFO zijn uitgedrukt.

**Causal Loop Diagrams.** Centrale ontwerpvraag: hoe worden dynamische variabelen uitgedrukt in een statische OWL-ontologie? Mogelijke oplossingen: (a) variabelen als kwaliteitsdimensies met tijdgebonden waarden via temporele kwalificatie; (b) variabelen als abstracte typen waarvan de huidige waarde een concrete kwaliteitsinstantie is; (c) een hybride representatie. De keuze heeft gevolgen voor de expressiviteit van de Causa-view en de detectie van feedback loops via SPARQL. Aanvullend: integratie van onzekerheidsannotaties conform PAMS-taxonomie (Enserink et al.) als `valor:UncertaintyLevel` op Tessera-niveau — van statistisch risico tot diepe onzekerheid.

**Actor Analysis (i*-framework).** Centrale ontwerpvraag: hoe worden intentionele afhankelijkheden (dependum-relaties) uitgedrukt in VALOR-O? Het i* framework onderscheidt vier typen dependum (goal, task, resource, softgoal) — elk met een eigen ontologische status in UFO-C. Integratie met `ufoc:Commitment` als generieke afhankelijkheidsstructuur, met modaliteitsspecificaties per type.

VSD als aparte formaliseringsopgave vervalt: de waarde-ontologie is al afgedekt door COVER (zie Fase -1b).

### 12.5 Fase -1d: Integratie en validatie (3 maanden)

Integratie van alle modules tot VALOR-O v1.0. Consistentiecheck via HermiT. Validatie via ten minste drie representatieve casussen uit het domein waardegedreven publieke dienstverlening (bij voorkeur in samenwerking met uitvoerende organisaties). Aanpassing op basis van bevindingen. Output: VALOR-O v1.0 als publiek OWL/TTL repository met volledige documentatie.

### 12.6 Samenwerkingspartners

- **NEMO / LabES (UFES, Vitória, Brazilië)** — Guizzardi's onderzoeksgroep, primaire partner voor validatie van UFO-extensies
- **TU Delft / Faculteit Techniek, Bestuur en Management** — expertise in beleidsontwerp en participatieve methoden
- **Universiteit van Amsterdam / Instituut voor Informatica** — expertise in formele ontologie en kennisrepresentatie
- **TNO** — expertise in digitale overheid en toegepast onderzoek publieke dienstverlening
- **Uitvoerende overheden** (gemeenten, uitvoeringsorganisaties) als validatiepartner voor de casussen

---

## 13. Roadmap

### 13.1 Overzicht

De VALOR-roadmap heeft twee parallelle sporen: de **onderzoeksworkstream** (VALOR-O ontwikkeling) en de **softwareontwikkeling**. De softwareontwikkeling start zodra VALOR-O een stabiele v0.5 heeft bereikt — voldoende om op te bouwen maar nog niet compleet. VALOR-O en de software groeien daarna iteratief samen.

```
ONDERZOEK  │ -1a ████ │ -1b ████████ │ -1c ████████████ │ -1d ██████ │
           │   mnd 1-3│   mnd 2-6   │    mnd 4-10      │  mnd 9-12 │
           │          │             │                  │           │
SOFTWARE   │          │          Fase 0 ██ │ Fase 1-3 ████████ │ Fase 4-7 ████████ │ Fase 8-9 ████ │
           │          │          mnd 5-6  │  mnd 7-18        │  mnd 19-30        │  mnd 28-34   │
```

### 13.2 Onderzoeksworkstream

| Fase | Naam | Duur | Deliverables |
|---|---|---|---|
| **-1a** | Inventarisatie & beschikbaarheidsbeoordeling | 3 mnd | Inventaris + prioritering + NEMO-contact + beoordeling DEMO/COVER/COoDM/Weigand |
| **-1b** | Integratie bestaande formaliseringen | 4 mnd | OWL-modules UFO-B, UFO-C, UFO-L+Policy, COoDM, COVER, DEMO-transactie |
| **-1c** | Formalisering niet-geformaliseerde theorieën | 6 mnd | OWL-modules CLD (incl. onzekerheidsannotaties), Actor Analysis (i*) |
| **-1d** | Integratie VALOR-O | 3 mnd | VALOR-O v1.0 + casusvalidatie + publiek repository |

### 13.3 Softwareontwikkeling

| Fase | Naam | Duur | Deliverables |
|---|---|---|---|
| **Fase 0** | Fundament | 6 wk | GraphDB setup, VALOR-O v0.5 geladen, Tessera-engine v0.1, auth/IAM, CI/CD |
| **Fase 1** | Forma MVP | 8 wk | Volledige OntoUML-editor (21+21), SHACL-validatie v1, Turtle import/export, named graphs voor alternatieven |
| **Fase 2** | Tessera-architectuur | 6 wk | Tessera-engine v1.0, epistemische statusmachine, bewijs-upload, argumentatierelaties, PROV-O logging |
| **Fase 3** | Delibera | 6 wk | Besluitvormingsepisodes, stemmodule, faseovergang-mechanisme, sessielogboek |
| **Fase 4** | Causa | 8 wk | Causale view (CLD-notatie), feedback loop detectie via SPARQL, Causa-agent, perspectief-ontologie |
| **Fase 5** | Socia | 6 wk | Stakeholderview, Actor Analysis-notatie, Socia-agent, uitnodigingsmodel |
| **Fase 6** | Axia + Lexa | 8 wk | Waardecanvas, normatieve view, Axia-agent, Lexa-agent, waarde-implicatie relaties |
| **Fase 7** | Acta | 6 wk | Procesview (BPMN-stijl), Acta-agent, service journey-notatie |
| **Fase 8** | Integratie & tuning | 8 wk | Cross-perspectief traceerbaarheid, alternatievenvergelijking, verantwoordingsexport, performance (500+ nodes) |
| **Fase 9** | GA & hardening | 6 wk | Security audit, toegankelijkheidsaudit, gebruikerstests met niet-technische deelnemers, documentatie |

### 13.4 Mijlpalen

| Mijlpaal | Timing | Beschrijving |
|---|---|---|
| **M1** | Maand 3 | VALOR-O v0.3: UFO-C + UFO-B beschikbaar als OWL |
| **M2** | Maand 6 | VALOR-O v0.5: alle UFO-extensies; Fase 0 software compleet |
| **M3** | Maand 10 | VALOR-O v0.8: CLD en Actor Analysis geformaliseerd; Forma + Tessera + Delibera werkend |
| **M4** | Maand 12 | VALOR-O v1.0: volledige basis-ontologie gevalideerd via casussen |
| **M5** | Maand 18 | VALOR beta: alle perspectieven beschikbaar; eerste pilotgebruikers |
| **M6** | Maand 24 | VALOR v1.0 GA: volledig platform beschikbaar; security en toegankelijkheid geauditeerd |

---

## 14. Risico's en Mitigatie

| Risico | Kans | Impact | Mitigatie |
|---|---|---|---|
| VALOR-O formalisering duurt langer dan gepland door ontologische complexiteit | Hoog | Hoog | Gefaseerde release: start software op VALOR-O v0.5; later fasen bouwen op completere versies. Reserveer 30% buffer in onderzoeksplanning |
| Onvoldoende samenwerking met NEMO/LabES | Middel | Hoog | Vroeg contact leggen (Fase -1a maand 1); alternatieve validatiepartners identificeren; publicaties als primaire bron gebruiken bij uitblijven samenwerking |
| DEMO-transactiepatroon en gUFO zijn niet volledig aligned in het bestaande bridge-paper | Laag | Middel | Grondig reviewen van Almeida c.s. (2013); ontologie-engineer beoordeelt gaps; aanvullende formalisering waar nodig in Fase -1b |
| Deelnemers zonder technische achtergrond vinden de perspectief-interfaces alsnog te complex | Middel | Hoog | Vroege gebruikerstests (Fase 5) met echte niet-technische deelnemers; UX-iteratie ingebakken in elke perspectief-fase; progressieve ontsluiting als escape valve |
| Socratische agents hebben disproportionele invloed ondanks governance-maatregelen | Middel | Middel | Agent-invloedrapport na elke sessie; facilitatortraining; agent-stilte-modus; empirisch onderzoek naar groepsdynamica in pilotfase |
| React Flow schaalt niet bij 500+ nodes in Forma | Laag | Middel | Vroege performance-spike in Fase 1; viewport-virtualisatie; lazy loading; fallback naar SPARQL-tabel voor grote modellen |
| OWL-redeneerder te traag voor real-time gebruik | Middel | Middel | ELK als snellere redeneerder voor real-time; HermiT alleen voor batch-checks bij faseovergangen; asynchroon met gebruikersfeedback |
| Democratische besluitvorming leidt tot ontologisch inconsistente modellen | Laag | Hoog | SHACL-validatie signaleert inconsistenties; engineer-Tessera als formeel bezwaarmechanisme; inconsistente aanvaarding is mogelijk maar expliciet gedocumenteerd |
| Alternatieven-divergentie maakt graph te complex voor beheer | Middel | Middel | Named graph-architectuur houdt alternatieven geïsoleerd; vergelijkings-SPARQL is standaard beschikbaar; archivering van inactieve alternatieven |
| Intellectueel eigendom van UFO-extensies belemmert hergebruik | Laag | Hoog | Vroeg IP-overleg met NEMO; prefereer open licenties (CC BY, Apache 2.0); documenteer licenties van alle gebruikte ontologieën |

---

## 15. Open Vragen en Beslispunten

| # | Vraag | Type | Eigenaar | Deadline |
|---|---|---|---|---|
| 1 | Welke UFO-extensies zijn al als OWL beschikbaar? Welke moeten worden geformaliseerd? | Onderzoek | Ontologie-onderzoeker | Fase -1a |
| 2 | Is samenwerking met NEMO/LabES haalbaar en op welke voorwaarden? | Governance | Projectleider | Fase -1a mnd 1 |
| 3 | Is de COVER-waarde-ontologie voldoende als fundering voor Axia, of zijn aanvullingen nodig voor het publiek dienstverlening-domein? | Ontologisch | Ontologie-onderzoeker | Fase -1b |
| 4 | Hoe worden dynamische CLD-variabelen uitgedrukt in een statische OWL-ontologie, en welke SPARQL-query-strategie detecteert feedback loops? | Ontologisch | Ontologie-onderzoeker | Fase -1c |
| 4b | Is het bestaande DEMO-UFO bridge-paper (Almeida 2013) voldoende als basis, of zijn er gaps die aanvullende formalisering vereisen? | Ontologisch | Ontologie-engineer | Fase -1b |
| 5 | Welk fasemodel is het meest geschikt als standaard voor VALOR? (Design Thinking, dubbele diamant, of beleidslevenscyclus?) | Product | Product Owner | Fase 0 |
| 6 | GraphDB Community of Enterprise? (Enterprise vereist voor volledige SHACL) | Technisch | Architect | Fase 0 |
| 7 | Anoniem of gedeanonimiseerd stemmen als standaard in Besluitvormingsepisodes? | Governance | Product Owner | Fase 3 |
| 8 | Hoe worden Tesserae van niet-aangemelde burgers (anonieme inbreng) behandeld? | Governance + Technisch | Product Owner + Architect | Fase 3 |
| 9 | HermiT (OWL DL, volledig) of ELK (OWL EL, sneller) als primaire redeneerder? | Technisch | Architect | Fase 1 |
| 10 | Licentiemodel VALOR: open source (MIT/Apache 2.0), open core, of commercieel? | Strategisch | Management | Fase 0 |
| 11 | Hoe wordt de epistemische status van Tesserae die zijn aangenomen in een afgesloten fase behandeld bij heroverweging? Kan een gesloten fase worden heropend? | Ontologisch + Governance | Architect + Product Owner | Fase 3 |
| 12 | Hoe worden conflicterende Tesserae in hetzelfde alternatief gesignaleerd en behandeld? | Technisch | Architect | Fase 2 |
| 13 | Zijn perspectief-ontologieën volledig declaratief genereerbaar tot UI-views, of is per perspectief handmatige UI-code nodig? | Technisch | Architect | Fase 4 |
| 14 | Hoe wordt het agent-invloedrapport berekend, en wat zijn de drempelwaarden voor interventie? | UX + Ethiek | UX Lead | Fase 5 |
| 15 | Welke bestaande participatie- en deliberatiemethoden (World Café, open space, systeemopstellingen) zijn integreerbaar als sessiemodus? | Product | Product Owner + Facilitator | Fase 8 |
| 16 | Hoe wordt VALOR-O geversioneerd? Kan een Design Space verwijzen naar een specifieke versie van VALOR-O, en wat zijn de migratieconsequenties bij een VALOR-O update? | Technisch | Architect | Fase 0 |

---

## 16. Referenties

**gUFO en UFO-extensies**
- Almeida et al. (2019), *gUFO: A Lightweight Implementation of the Unified Foundational Ontology (UFO)*
- gUFO v1.0.0 specificatie: https://nemo-ufes.github.io/gufo/
- Guizzardi, G. (2005), *Ontological Foundations for Structural Conceptual Models*, CTIT PhD thesis
- Guizzardi et al. (2013), *UFO-C: A Foundational Ontology for Social Entities*
- Guizzardi et al. (2015), *UFO-L: An Ontological Account of Legal Relationships*
- Guizzardi et al. (2018), *Endurant Types in Ontology-Driven Conceptual Modeling: Towards OntoUML 2.0*, ER 2018
- Fonseca et al. (2019), *Relations in Ontology-Driven Conceptual Modeling*, ER 2019
- Guizzardi, R., Carneiro, B.G., Porello, D., Guizzardi, G. (2020), *A Core Ontology on Decision Making*, ONTOBRAS 2020 (COoDM)
- Guizzardi, G. et al. (2022), *The Common Ontology of Value and Risk (COVER)*, Applied Ontology
- Almeida, J.P.A. et al. (2013), *Revisiting the DEMO Transaction Pattern with the Unified Foundational Ontology (UFO)*, EEWC 2013

**OntoUML**
- OntoUML Vocabulary v1.1.0: https://dev.ontouml.org/ontouml-vocabulary/
- OntoUML Metamodel: https://w3id.org/ontouml/metamodel

**Enterprise Ontology / DEMO**
- Dietz, J.L.G., Mulder, H.B.F. (2020), *Enterprise Ontology: A Human-Centric Approach to Understanding the Essence of Organisation*, Springer (The Enterprise Engineering Series)
- Dietz, J.L.G. (2006), *Enterprise Ontology: Theory and Methodology*, Springer

**Beleidsontologie**
- Weigand, H., Johannesson, P., Andersson, B. (2024), *Ontological Analysis of Policy-Based Decision Making*, VMBO 2024, CEUR-WS Vol. 3821
- Enserink, B. et al. (2022), *Policy Analysis of Multi-Actor Systems*, 2nd edition, TU Delft OPEN Books. https://doi.org/10.5074/T.2022.004

**Publieke dienstverlening en waardecreatie**
- Osborne, S.P. et al. (2022), *Value Creation in the Public Service Ecosystem: An Integrative Framework*, Public Administration Review. https://doi.org/10.1111/puar.13474
- Friedman, B., Hendry, D. (2019), *Value Sensitive Design*, MIT Press

**Theoretische grondslagen**
- Forrester, J.W. (1968), *Principles of Systems*, MIT Press
- Meadows, D. (2008), *Thinking in Systems*, Chelsea Green
- Pearl, J. (2009), *Causality: Models, Reasoning and Inference*, Cambridge UP
- Yu, E. (1995), *Modelling Strategic Relationships for Process Reengineering*, PhD thesis (i* framework)
- Rittel, H., Webber, M. (1973), *Dilemmas in a General Theory of Planning*, Policy Sciences
- Habermas, J. (1981), *Theorie des kommunikativen Handelns*, Suhrkamp
- Hevner et al. (2004), *Design Science in Information Systems Research*, MIS Quarterly

**Technologie**
- W3C OWL 2 Web Ontology Language: https://www.w3.org/TR/owl2-overview/
- W3C SHACL Shapes Constraint Language: https://www.w3.org/TR/shacl/
- W3C PROV-O Provenance Ontology: https://www.w3.org/TR/prov-o/
- Ontotext GraphDB: https://graphdb.ontotext.com/
- React Flow: https://reactflow.dev/

---

*VALOR Ecosysteem — Product Plan v1.1 — februari 2026*
*Dit document is zelf een levend document: elk voorstel, elke betwisting en elk besluit over de inhoud ervan is in principe een Tessera.*
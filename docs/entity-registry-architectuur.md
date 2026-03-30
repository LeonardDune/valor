# Vraag:
Je hebt kennis van het VALOR ecosysteem. Ik ben op zoek naar de Kinds binnen dit ecosysteem. Dus die entiteiten die essentieel zijn: rigide en sortal binnen elke mogelijke wereld. Dus onafhankelijk van het maatschappelijk vraagstuk, perspectief of fase in een ontwerp.
Wat zouden deze kinds moeten zijn? Bekijk ook https://github.com/LeonardDune/valor-ontology

# Antwoord:
Laat me eerst de projectbestanden en de GitHub-pagina raadplegen.Nu haal ik de GitHub-repo op:Ik zie dat de repo verder is dan mijn projectbestanden — er zijn nu modules t/m `00w`. Laat me een paar kernbestanden ophalen:Ik heb genoeg uit de projectbestanden en de repo-structuur. Laat me nu het antwoord opbouwen vanuit wat ik weet.

---

# Kinds in VALOR-O

De kernvraag is: welke entiteiten in VALOR zijn **essentieel** — dat wil zeggen, een individu *kan niet ophouden* instantie te zijn van dit type zolang het bestaat, en dit type levert een *eigen identiteitscriterium* mee? Ongeacht maatschappelijk vraagstuk, perspectief of ontwerpfase.

De toets is dus streng: stel je voor dat je het vraagstuk verandert van schuldhulpverlening naar klimaatadaptatie. Bestaat het concept nog steeds, met hetzelfde identiteitscriterium? Dan is het een Kind.

---

## De kandidaten per module

### UFO-C grondlaag (00c)

**`ufoc:Agent`** — *Kind*
Het meest fundamentele Kind in VALOR. Een Agent is een FunctionalComplex met intentionele toestanden (BDI). Of je nu kijkt naar een jeugdprofessional, een gemeente of een buurtbewoner: ze zijn agent ongeacht welke rol ze spelen, welk vraagstuk aan de orde is, of welke fase het ontwerp heeft. Je kunt niet ophouden Agent te zijn terwijl je als entiteit blijft bestaan. `PhysicalAgent` en `InstitutionalAgent` zijn SubKinds.

---

### ACTA (00g)

**`acta:TransactionType`** — *Kind* (EventType-branch, maar als second-order entiteit: Kind van types)
Een TransactionType is een soorttypering van een coördinatie-/productie-episode. Het is wat het is — een bepaald soort transactie — ongeacht of die transactie ooit wordt uitgevoerd, door wie, of voor welk vraagstuk.

> ⚠️ Nuance: TransactionType is een *type van events*, geen endurant. In gUFO is de Kind-hiërarchie primair voor endurants. Voor event-types geldt `gufo:EventType` als categorie. Maar in het VALOR-model is `TransactionType` wel degelijk een ontologisch stabiele entiteit: het bestaat onafhankelijk van uitvoering. Behandel het als Kind binnen de event-ontologie-branch.

**`acta:TransactionResult`** — *Kind* (als `gufo:Situation`)
Een TransactionResult is de situatie die door een ProductionAct wordt voortgebracht. Het is wat het is — een resulterende toestand — ongeacht wie hem heeft voortgebracht of waarvoor. Tevens het `cover:ValueObject`. De identiteit ervan hangt niet af van een rol of relatie.

---

### COVER (00f)

**`cover:ValueType`** — *Kind*
Een ValueType is een type van waarde (veiligheid, autonomie, rechtvaardigheid). Het bestaat ongeacht of iemand het nu ervaart of proposeert. Het heeft een eigen identiteitscriterium: twee ValueTypes zijn verschillend als ze verschillende dimensies van menselijk welzijn articuleren. Onveranderlijk door het hele ontwerpproces.

**`cover:ValueExperience`** — *Kind* (als `gufo:Event`)
Een ValueExperience is een concrete gebeurtenis waarin een individu waarde ervaart of juist waardeschade lijdt. Als zo'n episode heeft plaatsgevonden, is het altijd die episode geweest — het kan niet ophouden een ValueExperience te zijn. (Vergelijkbaar met: een geboorte is altijd een geboorte.)

> `cover:ValueObject` is *niet* zelfstandig een Kind — het is het object dat de waarde-ervaring mogelijk maakt, maar zijn identiteit hangt af van de context (het IS het TransactionResult).

---

### CAUSA (00h)

**`causa:CausalVariable`** — *Kind* (als `gufo:Quality`)
Een CausalVariable is een meetbare eigenschap van de werkelijkheid die in een causaal model voorkomt (bijv. "recidivecijfer", "wachttijd"). De identiteit ervan is intrinsiek: het is die variabele, ongeacht in welk model hij verschijnt of welke waarde hij heeft.

**`causa:CausalClaim`** — hier is discussie mogelijk. Een CausalClaim is een Belief (UFO-C mode), en beliefs zijn *momenten* — ze hangen aan hun drager. Maar als abstracte propositionele entiteit (los van wie hem gelooft) zou het een `gufo:Proposition`-achtige entiteit zijn. In de huidige VALOR-architectuur is het een mode, dus **geen Kind** in strikte zin.

**`causa:Intervention`** — *Kind* (als EventType)
Een Intervention is een bepaald type ingreep in de werkelijkheid. Het bestaat als ontologische entiteit ongeacht of het wordt uitgevoerd.

---

### SOCIA (00i)

**`socia:Actor`** — hier is voorzichtigheid geboden. Actor is in i* een *rol* die een Agent speelt in een afhankelijkheidsstructuur. In UFO-termen is het anti-rigid: een Agent kan ophouden Actor te zijn (als hij uit de dependency structure treedt). Dus **geen Kind** — eerder een Role.

---

### DELIBERA / COoDM (00e / 00m)

**`delibera:Tessera`** (Claim) — *Kind*
Een Tessera is een propositioneel object dat in een deliberatieproces wordt ingebracht. Eenmaal ingebracht als Tessera, is het altijd die Tessera — het heeft een vaste epistemische identiteit (welke claim, door wie, wanneer). Het kan van epistemicStatus veranderen (van `Proposed` naar `Accepted`), maar dat is een *fase*, niet een verlies van identiteit. Tessera is een **Kind**, met fasen als Phases.

**`delibera:DecisionEpisode`** — *Kind* (als Event)
Een beslissingsepisode is een afgebakende episode in de tijd. Eenmaal plaatsgevonden, altijd een DecisionEpisode.

---

### VALOR-CORE (00s)

**`valor:Issue`** — *Kind* (als `gufo:SocialObject`)
Een maatschappelijk vraagstuk heeft een eigen identiteit: het is dit vraagstuk, met deze constitutieve situatie en deze betrokken community. Het kan opgelost worden (dan bestaat het niet meer), maar zolang het bestaat is het onveranderlijk een Issue. Ongeacht welk perspectief of fase.

---

## Samenvatting: de Kinds van VALOR-O

| Kind | Module | gUFO-supertype | Rationale |
|---|---|---|---|
| `ufoc:Agent` | UFO-C | `gufo:FunctionalComplex` | Essentieel kenmerk van elk handelend subject |
| `ufoc:PhysicalAgent` | UFO-C | SubKind van Agent | Personen, fysiek gesitueerd |
| `ufoc:InstitutionalAgent` | UFO-C | SubKind van Agent | Organisaties, collectief erkend |
| `acta:TransactionType` | ACTA | `gufo:EventType` | Soorttypering van coördinatie, onafhankelijk van uitvoering |
| `acta:TransactionResult` | ACTA | `gufo:Situation` | Resulterende toestand; identiteit intrinsiek |
| `cover:ValueType` | COVER | `gufo:Kind` | Waardedimensie bestaat onafhankelijk van ervaring |
| `cover:ValueExperience` | COVER | `gufo:Event` | Concrete waarde-episode; onherleidbaar individueel |
| `causa:CausalVariable` | CAUSA | `gufo:Quality` | Meetbare eigenschap van de werkelijkheid |
| `causa:Intervention` | CAUSA | `gufo:EventType` | Type ingreep; onafhankelijk van uitvoering |
| `delibera:Tessera` | DELIBERA | `gufo:SocialObject` | Propositionele identiteit vastgelegd in deliberatie |
| `delibera:DecisionEpisode` | DELIBERA | `gufo:Event` | Afgebakende beslissepisode |
| `valor:Issue` | VALOR-CORE | `gufo:SocialObject` | Maatschappelijk vraagstuk als ontologisch object |

---

## Wat zijn nadrukkelijk *geen* Kinds

- `ActorRole` — anti-rigid (een agent speelt de rol contingent)
- `socia:Actor` — anti-rigid Role
- `cover:ValueProposition` — een propositioneel object dat afhankelijk is van wie het formuleert
- `cover:ValueObject` — identiteit afhankelijk van context (= TransactionResult)
- `causa:CausalClaim` — mode (hangt aan een drager)
- `nexus:EcosystemAgent` — SubKind van Agent, maar ook gelezen als Role (→ discussiepunt)
- `valor:IssueCommunity` — SubKind van CollectiveIntentionalCommunity, maar constitutief afhankelijk van gedeeld Concern → grensgebied

---

## Eén open architectuurvraag

`valor:CollectiveIntentionalCommunity` is in de huidige documentatie gedeclareerd als `«category»` (rigid non-sortal). Dat klopt: het groepeert Agents met gedeelde intentionaliteit zonder eigen identiteitscriterium. Maar `IssueCommunity` en `EcosystemAgent` als SubKinds ervan — zijn die dan Kinds of SubKinds van een Category? Technisch gezien moeten zij hun identiteitscriterium dan elders vandaan halen (namelijk van `Agent`). Dit is een integratiepunt dat in Fase -1d explicitering verdient.

# Vraag:
Lees nog even gUFO na: met name de definities van Rigidtype en Sortaltype etc.
https://nemo-ufes.github.io/gufo/

Levert dat nog andere inzichten op? Behoeft de VALOR ontology wellicht nog aanpassingen?

# Antwoord:

Uitstekend — de volledige gUFO-spec is nu gelezen. Hier zijn de nieuwe inzichten en de consequenties voor VALOR-O.

---

# Nieuwe inzichten vanuit de gUFO-spec

## 1. Vijf cruciale precisieringen die mijn vorige analyse bijstellen

### 1.1 `gufo:Kind` geldt **uitsluitend voor Endurants**

De gUFO-definitie is ondubbelzinnig:

> *"Every **gufo:Endurant** instantiates one and only one gufo:Kind."*

`gufo:Kind` is een subklasse van `gufo:EndurantType`. Endurants zijn Objects en Aspects. **Events en Situations zijn geen endurants.** Hieruit volgt dat mijn eerdere categorisering van `TransactionResult` (Situation), `ValueExperience` (Event), `DecisionEpisode` (Event) en `Intervention` (EventType) als "Kinds" **incorrect** was. Ze vallen buiten de scope van de Kind-hiërarchie.

De juiste types voor events en situations zijn `gufo:EventType` en `gufo:SituationType` — en die hebben hun eigen taxonomie los van de Sortal/Rigid-as.

---

### 1.2 `gufo:SemiRigidType` en `gufo:Mixin` bestaan echt — en zijn relevanter dan ik dacht

gUFO definieert expliciet:

> *"A **SemiRigidType** applies necessarily to some of its instances and contingently to some others."*

Voorbeeld: `FemaleAnimal` is noodzakelijk vrouwelijk voor leeuwen (rigid), maar contingent voor clownvissen (die van geslacht kunnen wisselen). Dit is het type dat VALOR's `CollectiveIntentionalCommunity` waarschijnlijk behoeft — zie §3 hieronder.

---

### 1.3 `gufo:Agent` is in gUFO een **Category**, niet een Kind

gUFO noemt `Agent` expliciet als voorbeeldinstantie van `gufo:Category`:

> *"'Agent' may be a gufo:Category that classifies both people and organizations."*

Dit betekent: `Agent` is **rigid** (essentieel voor zijn instanties) maar **non-sortal** (geen eigen identiteitscriterium — personen en organisaties hebben verschillende identiteitscriteria). In VALOR-O's `00c-ufo-c.ttl` staat `ufoc:Agent` gedeclareerd als `rdf:type gufo:Kind` — dat is **een fout**. Het moet `gufo:Category` zijn. De echte Kinds zijn `PhysicalAgent` en `InstitutionalAgent`.

---

### 1.4 De `gufo:Kind`-definitie omvat ook Relators en Aspects

gUFO zegt:

> *"Examples include kinds of ordinary objects such as 'Person', 'House', 'Car'; kinds of **relators**, such as 'Marriage', 'RentalContract'; kinds of **existentially-dependent aspects** of objects, such as 'Weight', 'Belief', 'Vulnerability'."*

Dit is een verbreding ten opzichte van mijn vorige analyse: ook `gufo:Relator`-subklassen en `gufo:IntrinsicMode`-subklassen kunnen Kinds zijn. In VALOR-O betekent dit dat bijvoorbeeld `acta:TransactionType` (als relator-achtig patroon) en `causa:CausalVariable` (als Quality-subklasse) wél als Kinds kunnen worden gekwalificeerd — maar dan als Kinds van hun respectieve Endurant-branch.

---

### 1.5 `gufo:NonRigidType` heeft nu drie subcategorieën, niet twee

Mijn eerdere uitleg noemde only rigid/anti-rigid. gUFO voegt toe:

- `gufo:AntiRigidType` — contingent voor **alle** instanties
- `gufo:SemiRigidType` → `gufo:Mixin` — noodzakelijk voor sommige, contingent voor andere instanties

---

## 2. Gecorrigeerde Kinds-tabel voor VALOR-O

Alleen endurants; events en situations hebben hun eigen EventType/SituationType-taxonomie.

| Klasse | Module | Endurant-branch | Correct type | Noot |
|---|---|---|---|---|
| `ufoc:PhysicalAgent` | UFO-C | `gufo:FunctionalComplex` | **Kind** | Identiteitscriterium: fysieke continuïteit |
| `ufoc:InstitutionalAgent` | UFO-C | `gufo:FunctionalComplex` | **Kind** | Identiteitscriterium: collectieve erkenning |
| `cover:ValueType` | COVER | `gufo:Object` of abstracte entiteit | **Kind** | Waardedimensie met eigen identiteitscriterium |
| `causa:CausalVariable` | CAUSA | `gufo:Quality` | **Kind** | Meetbare eigenschap met eigen identiteitscriterium |
| `delibera:Tessera` | DELIBERA | `gufo:SocialObject` → `gufo:Object` | **Kind** | Propositionele entiteit; identiteit is de claim zelf |
| `valor:Issue` | VALOR-CORE | `gufo:SocialObject` | **Kind** | Maatschappelijk vraagstuk met eigen identiteitscriterium |

---

## 3. Aanpassingen die VALOR-O nodig heeft

### Aanpassing A — `ufoc:Agent` moet `gufo:Category` worden *(kritiek)*

**Huidig (fout):**
```turtle
ufoc:Agent rdf:type gufo:Kind .
```

**Correct:**
```turtle
ufoc:Agent rdf:type gufo:Category .
```

Rationale: Agent groepeert PhysicalAgent en InstitutionalAgent die elk een eigen identiteitscriterium dragen. Agent zelf draagt geen identiteitscriterium — het is rigid (essentieel) maar non-sortal. Dit is precies gUFO's definitie van Category.

---

### Aanpassing B — `valor:CollectiveIntentionalCommunity` moet heroverwogen worden

In de huidige documentatie staat `CollectiveIntentionalCommunity` als `«category»`. Dat is consistent met gUFO. Maar de subklassen `IssueCommunity` en `EcosystemAgent` zijn gedeclareerd als SubKinds van `Agent`. Dit creëert een spanning: ze erven hun identiteitscriterium van `Agent` (de Category), maar een Category heeft geen identiteitscriterium om te erven. De identiteit moet dan van `PhysicalAgent` of `InstitutionalAgent` komen — maar `IssueCommunity` kan ook een losse collectieve entiteit zijn die niet per se één van die Kinds instantieert.

**Aanbeveling:** Declareer `IssueCommunity` als een `gufo:Kind` van `gufo:Collection` (een `VariableCollection` van Agents met gedeeld Concern), en `EcosystemAgent` als een `gufo:Kind` van `gufo:FunctionalComplex`. Dat geeft elk zijn eigen identiteitscriterium.

---

### Aanpassing C — EventType/SituationType correct labelen

`acta:TransactionResult` (Situation), `delibera:DecisionEpisode` (Event), `causa:Intervention` (EventType) mogen **niet** als `gufo:Kind` worden gedeclareerd. Ze zijn respectievelijk:

```turtle
acta:TransactionResult  rdf:type gufo:SituationType .
delibera:DecisionEpisode rdf:type gufo:EventType .
causa:Intervention       rdf:type gufo:EventType .
```

De Sortal/Rigid-dimensie is voor hen niet van toepassing binnen gUFO.

---

### Aanpassing D — `causa:CausalClaim` als `gufo:IntrinsicMode`-Kind

`CausalClaim` is in VALOR-O een specialisatie van `ufoc:Belief` (zelf een `gufo:IntrinsicMode`). Modes kunnen Kinds zijn — gUFO noemt `Vulnerability` en `Belief` als voorbeelden van Kinds binnen de Aspect-branch. Dus:

```turtle
causa:CausalClaim rdf:type gufo:Kind .
rdfs:subClassOf ufoc:Belief .  # via IntrinsicMode
```

Dit is wél een Kind, maar dan als Kind van een Aspect, niet van een Object.

---

## Samenvatting

De grootste correctie is structureel: **`ufoc:Agent` moet Category worden, niet Kind**. Dat is een fout in de huidige TTL die cascadeert door alle modules die op Agent voortbouwen. Verder is de Kind-taxonomie strikt beperkt tot Endurants — events, situations en hun types vallen buiten de Sortal/Rigid-as en hebben hun eigen EventType/SituationType-declaraties.

# Vraag:

Stel de VALOR ontology is aangepast. Wat zijn dan de essentiële concepten binnen VALOR? Dus die ‘dingen’ die los van vraagstuk, perspectief of fase hetzelfde blijven. Dat kan dan ook iets anders zijn dan alleen Kinds, toch?

# Antwoord:

Laat me even goed nadenken.Goed. Nu kan ik een grondig antwoord geven. De vraag is breder dan "alleen Kinds" — terecht.

---

# De essentiële concepten van VALOR-O

Je hebt gelijk: de vraag "wat blijft hetzelfde ongeacht vraagstuk, perspectief of fase" is **breder dan Kind**. In UFO zijn er meerdere categorieën van essentiële, stabiele concepten:

1. **Kinds** — essentiële endurant-types (behandeld)
2. **Categories** — essentiële non-sortal types (rigid maar cross-Kind)
3. **Essentiële relaties** — structurele verbindingen die altijd gelden
4. **Essentiële EventTypes en SituationTypes** — vaste patronen van wat er *gebeurt*
5. **Essentiële Moments (Aspects)** — intrinsieke eigenschappen die noodzakelijk bij een drager horen

Hieronder werk ik alle vijf uit voor VALOR-O.

---

## Laag 1 — Essentiële Categories (rigid, non-sortal)

Dit zijn de transversale concepten die *altijd* en *overal* in VALOR gelden, maar geen eigen identiteitscriterium leveren.

**`ufoc:Agent`** *(gecorrigeerd naar Category)*
Elke entiteit in VALOR die intentioneel handelt is Agent — altijd, ongeacht vraagstuk of fase. Geen identiteitscriterium (personen en organisaties zijn anders), maar absoluut rigid. Dit is het anker van het gehele sociale domein.

**`gufo:FunctionalComplex` als Category via `sysont:System`**
Elke `System` in SYSONT is een FunctionalComplex met componenten die complementaire functionele rollen spelen. System is een Category: het groepeert entiteiten van verschillende Kinds (gemeenten, netwerken, dienstverleningsketens) op basis van een gedeeld structuurcriterium. Rigid, non-sortal.

**`cover:ValueType`** *(hier als Category, niet Kind)*
Eigenlijk verdient heroverweging: is `ValueType` een Kind of een Category? Een ValueType zoals "autonomie" of "veiligheid" bestaat onafhankelijk van welk individu het draagt of welk vraagstuk het raakt — dat wijst op rigiditeit. Maar of het een eigen identiteitscriterium heeft (sortal) of slechts een gedeelde eigenschap uitdrukt (non-sortal) hangt af van je theorie. In Sales et al. (2017) is een ValueType een abstracte categorisering van waarden — eerder Category dan Kind.

---

## Laag 2 — Essentiële Kinds (rigid, sortal — alleen endurants)

| Kind | Endurant-branch | Essentie |
|---|---|---|
| `ufoc:PhysicalAgent` | `gufo:FunctionalComplex` | Fysieke actor; identiteit via lichamelijke continuïteit |
| `ufoc:InstitutionalAgent` | `gufo:FunctionalComplex` | Organisatie; identiteit via collectieve erkenning |
| `valor:Issue` | `gufo:SocialObject` | Maatschappelijk vraagstuk; identiteit is de constitutieve situatie + betrokken community |
| `delibera:Tessera` | `gufo:SocialObject` | Propositionele claim in deliberatie; identiteit is de bewering zelf |
| `causa:CausalVariable` | `gufo:Quality` | Meetbare eigenschap van de werkelijkheid; identiteit via het gemeten construct |
| `causa:CausalClaim` | `gufo:IntrinsicMode` | Beleidstheorie; Kind van een Belief-mode |
| `acta:TransactionType` | `gufo:Relator`-adjacente entiteit | Soorttypering van coördinatie; identiteit is de rol-structuur |

---

## Laag 3 — Essentiële EventTypes en SituationTypes

Deze vallen buiten de Sortal/Rigid-as maar zijn wél essentieel: het zijn de vaste *patronen van wat er gebeurt* in elk VALOR-gebruik.

**EventTypes** — ongeacht vraagstuk altijd aanwezig:

| EventType | Module | Wat het beschrijft |
|---|---|---|
| `delibera:DecisionEpisode` | DELIBERA | Het moment waarop een groep een claim aanneemt of verwerpt |
| `acta:CoordinationAct` | ACTA | De communicatieve handeling waarmee een transactie gecoördineerd wordt |
| `acta:ProductionAct` | ACTA | De uitvoeringshandeling die een TransactionResult voortbrengt |
| `cover:ValueExperience` | COVER | De concrete episode waarin een agent waarde ervaart of waardeschade lijdt |
| `causa:Intervention` | CAUSA | Het type ingreep dat in een SolutionModel wordt voorgesteld |

**SituationTypes** — vaste configuraties die altijd relevant zijn:

| SituationType | Module | Wat het beschrijft |
|---|---|---|
| `acta:TransactionResult` | ACTA | De toestand voortgebracht door een ProductionAct; tevens het ValueObject |
| `causa:ExplanatoryModel` | CAUSA | Een set CausalClaims over het probleem |
| `causa:SolutionModel` | CAUSA | Een set Interventions als ontwerpalternatief |
| `capax:CapabilityGap` | CAPAX | De situatie dat een vereiste capability ontbreekt |
| `sysont:SystemSituation` | SYSONT | Een configuratie van een systeem op een moment — fundeert manifestatiecondities |

---

## Laag 4 — Essentiële Aspects (Modes en Relators)

Dit zijn de intrinsieke en extrinsieke eigenschappen die *noodzakelijk* bij hun dragers horen — in elke VALOR-context.

**Essentiële IntrinsicModes** (altijd aanwezig bij hun drager):

| Mode | Drager | Essentie |
|---|---|---|
| `delibera:EpistemicStatus` | `delibera:Tessera` | Elke Tessera heeft altijd een epistemische status (Proposed/Accepted/Rejected) |
| `causa:UncertaintyLevel` | `causa:CausalClaim` | Elke CausalClaim heeft altijd een onzekerheidsniveau (PAMS-taxonomie) |
| `capax:Capability` | `ufoc:Agent` | Elke Agent draagt capabilities — het ontbreken ervan is zelf een capability-mode |

**Essentiële Relators** (structurele verbindingen die altijd gelden):

| Relator | Medieert | Essentie |
|---|---|---|
| `ufoc:SocialCommitment` | Agent ↔ Agent | Elk i\*-afhankelijkheidspatroon is een SocialCommitment — altijd, ongeacht domein |
| `cover:ValueAscription` | Agent ↔ ValueObject | De verbinding tussen een agent, een waardeoordeel en een object — fundeert alle waardeafweging |
| `lexa:LegalRelator` | TransactionType ↔ Norm | Elke transactie in een publieke context is juridisch gegrond — altijd |

---

## De architecturele kern: wat dit zegt over VALOR

Als je al deze essentiële concepten naast elkaar legt, zie je dat VALOR-O steunt op **vijf onvermijdelijke spanningsvelden** die in elk vraagstuk, elk perspectief en elke fase terugkeren:

1. **Agent ↔ Issue** — wie draagt het vraagstuk?
2. **CausalClaim ↔ Intervention** — waarom werkt een oplossing (theorie) en wat doe je dan (ingreep)?
3. **TransactionType ↔ ValueExperience** — wat wordt gedaan en wat ervaart de burger?
4. **Tessera ↔ DecisionEpisode** — wat wordt beweerd en wanneer wordt beslist?
5. **Capability ↔ TransactionType** — kan het ook echt?

Deze vijf relaties zijn de **invariante structuur** van VALOR — essentiëler dan de modules zelf, en aanwezig ongeacht of je kijkt naar schuldhulpverlening, klimaatadaptatie of zorgtoegankelijkheid.
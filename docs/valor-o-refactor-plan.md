# VALOR-O Refactorplan
## Van Neo4j/REST naar Fuseki/Tessera — Epics, Stories & Technische Analyse

**Versie** | 0.1
**Datum** | maart 2026
**Branch** | `refactor/valor-o`
**Relatie** | Uitwerking van `docs/valor-ontology-implementatieplan.md` en `docs/valor-ecosystem20.md`

---

## 1. Codebase-analyse

Voordat de refactor begint is de bestaande codebase grondig bekeken. De bevindingen hieronder sturen de prioritering van de Epics.

### 1.1 Authenticatie en toegangsbeheer

**Huidig model:**

```
JWT (Supabase) → verify_token() → ensure_user_sync() → Neo4j User node
                                                              ↓
                                             check_permission() → HAS_ROLE relaties in Neo4j
```

`get_current_user` in `auth.py` verifiëert het Supabase JWT-token en synchroniseert de gebruiker JIT naar Neo4j. `check_permission` in `db/permissions.py` bevraagt Neo4j voor RBAC via `HAS_ROLE` relaties tussen `User`, `Organization`, `Project` en `ThemeBase` nodes.

**Bevinding — security gap:** Meerdere schrijfroutes missen de auth/permissie-check volledig:

| Route | Probleem |
|-------|----------|
| `PATCH /factors/{factor_id}` | Geen `get_current_user`, geen `check_permission` |
| `DELETE /factors/{factor_id}` | Geen `get_current_user`, geen `check_permission` |
| `DELETE /claims/{claim_id}` | Geen `check_permission` op eigendom |

Dit betekent dat elke gebruiker met een geldig JWT-token andermans factoren kan wijzigen of verwijderen. **Dit moet gefixed worden vóór alle andere refactorwerk.**

**Architecturale consequentie voor Fuseki:**

RBAC zit volledig in Neo4j. Als Neo4j verdwijnt als kennisopslag, vervalt daarmee ook het permissiemodel. De conclusie is:

- **Neo4j blijft de identity store**: gebruikersbeheer, `HAS_ROLE`-relaties, organisatiehiërarchie
- **Fuseki is de knowledge store**: alle VALOR-O Tesserae, DesignSpaces, named graphs
- **Fuseki is nooit publiek bereikbaar**: draait op intern netwerk, alleen bereikbaar via de FastAPI backend
- **De SPARQL proxy controleert altijd eerst permissies via Neo4j** voordat een query of update Fuseki bereikt

```
Client → FastAPI (JWT check) → Neo4j (HAS_ROLE check) → Fuseki (SPARQL)
                     ↑
             Fuseki is intern netwerk,
             nooit direct bereikbaar
```

### 1.2 Frontend — hergebruikpotentieel

**Positief:**

- `perspectives/causa/` is al goed gemodulariseerd: eigen `Shell`, `hooks/useCausaData`, `projections/graph.ts`, `views/` — dit patroon schaalt direct naar nieuwe perspectieven
- De workspace gebruikt **React Flow** (niet D3) — ideaal voor node/edge visualisaties in alle VALOR-O perspectieven
- `api.ts` heeft een centrale axios client met Supabase token-interceptor — één plek om aan te passen voor Fuseki SPARQL responses
- Shadcn/UI + Tailwind is consistent doorgevoerd

**Uitdagingen:**

| Uitdaging | Ernst | Toelichting |
|-----------|-------|-------------|
| `useCausaData` bevraagt Neo4j via REST | Hoog | Elke `api.getThemeClaims()` gaat naar Neo4j; moet omgezet naar SPARQL-responses van Fuseki |
| Nodes/edges hebben geen epistemisch statusveld | Hoog | Geen `epistemicStatus` in het huidige datamodel; visualisatielaag moet uitgebreid worden |
| State management is ad-hoc | Middel | Mix van `useState`, React Query en Context API; geen duidelijk patroon voor Tessera-state |
| WebSocket events zijn Neo4j-specifiek | Middel | `FACTOR_CREATED`, `CLAIM_UPDATED` moeten naast `TESSERA_CREATED` bestaan in de transitieperiode |
| Geen perspectief-routing | Laag | `App.tsx` heeft geen `/perspectives/` routes; alleen een workspace per theme |

### 1.3 API-laag — hergebruikpotentieel

**Positief:**

- FastAPI + Pydantic structuur is solide en type-safe
- `auth.py` werkt goed: HS256 + RS256/ES256 JWKS, JIT user sync
- Router-structuur (proposals, threads, sessions, deliberation) is uitbreidbaar

**Uitdagingen:**

| Bevinding | Impact |
|-----------|--------|
| `main.py` is 820 regels met vrijwel alle routes erin | Beheersbaar, maar nieuwe routers (tessera, designspace, sparql) moeten er naast gezet worden |
| `crud.py` is 1667 regels Neo4j-monoliet | Bij migratie: elke functie individueel omzetten of wrappen als adapter |
| `check_permission` inconsistent toegepast | Technische schuld; risico dat nieuwe routes het patroon ook overslaan |

---

## 2. Architectuurprincipes voor de refactor

1. **Fuseki is niet publiek** — de SPARQL proxy in FastAPI is de enige toegangspoort
2. **Neo4j blijft voor identiteit** — User nodes, HAS_ROLE, uitnodigingen, sessies
3. **Tessera API is de enige schrijfroute naar Fuseki** — perspectief-routes zijn adapters
4. **Bestaande frontend blijft werken tijdens migratie** — adapter-patroon op bestaande routes
5. **Geen perspectief-termen in de UI** — gUFO/VALOR-O terminologie nooit zichtbaar voor eindgebruikers
6. **Security first** — auth gaps dichten vóór uitbreiding

---

## 3. Epics en User Stories

### Afhankelijkheidsgraph (kritisch pad)

```
Epic 0 (Security fix)
  └─► Epic 1 (Fuseki infra)
        └─► Epic 2 (Tessera Engine)
              └─► Epic 3 (DesignSpace API)
                    ├─► Epic 4 (Causa upgrade)
                    ├─► Epic 5 (Delibera)
                    ├─► Epic 6 (Socia)
                    ├─► Epic 7 (Axia)
                    ├─► Epic 8 (Forma)
                    ├─► Epic 9 (Lexa + Acta)
                    └─► Epic 10 (AI Agents)
                                    ↓ (alles stabiel)
                              Epic 11 (Neo4j afbouwen)
```

---

### Epic 0 — Security: ontbrekende auth op mutatieroutes

**Prioriteit: blocker — uitvoeren vóór alle andere werk**
**Doel:** Bestaande security gap dichten. Geen nieuwe features totdat schrijfroutes correct beveiligd zijn.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-0.1 | Als platformbeheerder wil ik dat `PATCH /factors/{id}` vereist dat de aanroeper lid is van het bijbehorende theme | `get_current_user` + `check_permission(MEMBER)` toegevoegd; 403 bij onbevoegde aanroep |
| US-0.2 | Als platformbeheerder wil ik dat `DELETE /factors/{id}` hetzelfde vereist | Idem |
| US-0.3 | Als platformbeheerder wil ik dat `PATCH /claims/{id}` en `DELETE /claims/{id}` eigendom verifiëren | Claim-eigendom gecontroleerd via theme_id → check_permission |
| US-0.4 | Als developer wil ik een integratietest die afdwingt dat alle schrijfroutes een auth-dependency hebben zodat deze gap niet terugkeert | Test faalt als een POST/PATCH/DELETE route geen `Depends(get_current_user)` heeft |

---

### Epic 1 — Fuseki Triplestore Infrastructuur

**Doel:** Apache Jena Fuseki draaien op de VPS (intern netwerk), alle 14 VALOR-O modules geladen, SPARQL endpoint bereikbaar voor de backend — nooit voor de buitenwereld.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-1.1 | Als platformbeheerder wil ik Fuseki deployen via Coolify op de VPS op een intern netwerk zodat het endpoint niet publiek bereikbaar is | Fuseki bereikbaar op intern hostname; geen publieke poort; health check actief |
| US-1.2 | Als platformbeheerder wil ik alle 14 VALOR-O TriG-modules laden in Fuseki zodat de ontologie bevraagbaar is | `SELECT * WHERE { ?s a owl:Class }` retourneert VALOR-O klassen; alle modules aanwezig |
| US-1.3 | Als platformbeheerder wil ik een geautomatiseerd laadscript hebben dat de TriG-bestanden vanuit de ontologie-repo laadt zodat redeployment reproduceerbaar is | Script is idempotent; versienummer van modules wordt gelogd |

---

### Epic 2 — Tessera Engine (Backend)

**Doel:** Centrale schrijf-API naar Fuseki. Alle latere perspectieven schrijven via deze laag. Bestaande Factor/Claim routes werken als adapters — de frontend merkt niets.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-2.1 | Als backend-developer wil ik een `fuseki.py` service-adapter zodat de backend SPARQL queries en updates naar Fuseki kan sturen | SPARQL SELECT, UPDATE en CONSTRUCT werken; named graph isolatie per DesignSpace; alle calls gaan door auth-laag |
| US-2.2 | Als gebruiker wil ik een Tessera aanmaken via `POST /tessera/` zodat claims als `valor:Tessera` in Fuseki worden opgeslagen | Tessera heeft `epistemicStatus=Proposed`, `claimedBy`, `claimedAt`, `claimType`; permissie-check via Neo4j |
| US-2.3 | Als gebruiker wil ik de epistemische status van een Tessera wijzigen via `PATCH /tessera/{id}/status` | Ongeldige transities geblokkeerd; `Accepted`/`Rejected` vereist `DecisionEpisode`-link |
| US-2.4 | Als gebruiker wil ik bewijs toevoegen aan een Tessera via `POST /tessera/{id}/evidence` | Evidence heeft type (Empirical/Theoretical/Expert/Experiential), strength en source |
| US-2.5 | Als gebruiker wil ik argumentatierelaties leggen via `POST /tessera/{id}/argue` (supports/undermines/qualifies/presupposes) | Circulaire `undermines`-relaties geblokkeerd; SHACL T5-constraint gevalideerd |
| US-2.6 | Als developer wil ik dat `POST /factors`, `POST /claims_manual` als adapters schrijven naar zowel Neo4j als Fuseki zodat de bestaande frontend niet breekt | Bestaande integratietests slagen; data verschijnt in beide stores |

---

### Epic 3 — DesignSpace API & Named Graphs

**Doel:** Semantische workspace-structuur per project. Migratie van ThemeVersion-patroon naar DesignSpace + named graphs in Fuseki.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-3.1 | Als gebruiker wil ik een DesignSpace aanmaken via `POST /designspace/` zodat de 6 named graphs worden geïnitialiseerd in Fuseki | Named graphs `asis`, `alt/default`, `decisions`, `agents`, `provenance`, `ontology` aangemaakt; permissie-check via Neo4j HAS_ROLE |
| US-3.2 | Als gebruiker wil ik SPARQL queries uitvoeren via `GET /sparql/query` met automatische access control | Query wordt pas doorgestuurd naar Fuseki nadat Neo4j bevestigt dat de gebruiker toegang heeft tot de betrokken DesignSpace named graphs |
| US-3.3 | Als platformbeheerder wil ik een migratiescript draaien dat bestaande ThemeVersions omzet naar DesignSpaces in Fuseki | Alle bestaande Factors en Claims verschijnen als `causa:CausalClaim` Tesserae in Fuseki; checksum op aantal records |
| US-3.4 | Als gebruiker wil ik een faseovergang initiëren via `POST /designspace/{id}/phase/transition` | Overgang vereist quorum van stemmen; `app:PhaseTransition` DecisionEpisode aangemaakt; SHACL-validatie asynchroon via HermiT |

---

### Epic 4 — Causa Perspectief: Semantische Upgrade

**Doel:** Bestaande workspace uitbreiden met epistemische status-visualisatie, As-is/To-be toggle en contestatie. Geen UX-breuk.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-4.1 | Als gebruiker wil ik de epistemische status van elke node/edge zien via kleurcodering in de workspace | Proposed=grijs, Contested=oranje, Accepted=groen, Rejected=rood, Reconsidered=paars; badge op node |
| US-4.2 | Als gebruiker wil ik een claim betwisten via een "Betwist"-knop | Status → ContestedStatus; `valor:undermines` of `valor:qualifies` relatie aangemaakt; betwisting zichtbaar voor andere deelnemers |
| US-4.3 | Als gebruiker wil ik schakelen tussen As-is en To-be weergave | Toggle filtert op `valor:claimType` (AsIsType / ToBeType); layout behoudt posities |
| US-4.4 | Als gebruiker wil ik feedback-loops in het causale model zien | SPARQL property-path query detecteert cycli; nodes in cyclus gemarkeerd met een visuele indicator |

---

### Epic 5 — Delibera Perspectief

**Doel:** Argumentatiediagram, steminterface en koppeling bestaande deliberation boards aan `valor:DecisionEpisode`.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-5.1 | Als gebruiker wil ik een argumentatiediagram (IBIS-stijl) zien met Tesserae en hun supports/undermines/qualifies relaties | Diagram opgebouwd uit `delib:ArgumentationNetwork` SPARQL queries; React Flow graph |
| US-5.2 | Als gebruiker wil ik stemmen op een Tessera (Accept/Reject/Defer) via een DecisionEpisode | Vote opgeslagen als `valor:Vote`; epistemische status wijzigt na quorum; alleen stemgerechtigde rollen (Initiator, Contributor) |
| US-5.3 | Als gebruiker wil ik de bestaande RefinementBoard, RankingBoard en ConsentBoard gekoppeld zien aan `valor:DecisionEpisode` | Bestaande UI werkt ongewijzigd; deliberatiedata wordt parallel via Tessera API naar Fuseki geschreven |
| US-5.4 | Als gebruiker wil ik een tijdlijn van DecisionEpisodes zien | Tijdlijn toont episodes met datum, deelnemers, stemuitslag en statuswijziging |

---

### Epic 6 — Socia Perspectief

**Doel:** Stakeholderkaart op basis van `socia:` queries. Actoren, intentionele afhankelijkheden, belangen.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-6.1 | Als gebruiker wil ik een stakeholderkaart zien met actoren en hun intentionele afhankelijkheden | React Flow kaart toont `socia:StakeholderMap` met actor-nodes en `socia:IntentionalDependency` edges |
| US-6.2 | Als gebruiker wil ik StakeholderClaims aanmaken (InterestClaim, GoalClaim, PowerClaim) | Claims opgeslagen als subklasse van `valor:Tessera` met epistemische status via Tessera API |

---

### Epic 7 — Axia Perspectief

**Doel:** Waardenperspectief: ValueClaims, waardespanningen, heatmap-overlay op Causa-workspace.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-7.1 | Als gebruiker wil ik een waardencanvas zien met ValueClaims gegroepeerd per waardetype | Canvas toont `axia:ValueClaim` Tesserae per `cover:ValueType`; aangemaakt via Tessera API |
| US-7.2 | Als gebruiker wil ik waardespanningen (ValueTensionClaim) registreren en visualiseren | Spanning zichtbaar als relatie tussen twee ValueTypes |
| US-7.3 | Als gebruiker wil ik een heatmap-overlay op de Causa-workspace die aangeeft welke factoren welke waarden raken | Overlay kleurt nodes op basis van gekoppelde `axia:DesignImplication` relaties |

---

### Epic 8 — Forma Perspectief

**Doel:** Ontologische engineeringview: SHACL-validatie, SPARQL-editor, EngineerTesserae.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-8.1 | Als engineer wil ik een Monaco SPARQL-editor gebruiken om de graph direct te bevragen | Editor heeft syntax highlighting, autocomplete op VALOR-O prefixen, resultaten in tabel; queries gaan via de beveiligde SPARQL proxy |
| US-8.2 | Als engineer wil ik SHACL-validatierapporten zien per DesignSpace | Rapport toont violations per SHACL-shape met verwijzing naar betrokken Tesserae |
| US-8.3 | Als engineer wil ik EngineerTesserae aanmaken (TechnicalObjection, OntologicalObservation, ModelRecommendation) | EngineerTessera opgeslagen als `forma:EngineerTessera` subklasse van `valor:Tessera` |

---

### Epic 9 — Lexa & Acta Perspectieven

**Doel:** Normatief perspectief (wet- en regelgeving) en transactieperspectief (DEMO).

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-9.1 | Als gebruiker wil ik een normenkaart zien op basis van `ufo-l` | Kaart toont `ufol:LegalRelator` nodes en hun relaties tot factoren in de DesignSpace |
| US-9.2 | Als gebruiker wil ik een transactiediagram (DEMO CTP) zien op basis van `acta:` queries | Diagram toont `acta:Transaction` nodes met initiator/executor rollen en CTP-stappen |

---

### Epic 10 — AI Agents: Socratische Gesprekspartner

**Doel:** Per perspectief een Socratische agent die als Tessera-auteur werkt en vragen en suggesties registreert als `valor:AgentTessera`.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-10.1 | Als gebruiker wil ik per perspectief een AI-agent activeren die vragen stelt over de huidige Tesserae | Agent context = SPARQL CONSTRUCT van relevante subgraph; output = `valor:AgentTessera` via Tessera API |
| US-10.2 | Als gebruiker wil ik agent-uitingen als apart filterbare Tesserae zien | Filter op `valor:claimedBy` type agent vs. menselijke Participant; badge "AI" op node |
| US-10.3 | Als developer wil ik de bestaande CrewAI-agenten (CausalAnalyst, DevilsAdvocate) laten schrijven naar Fuseki via de Tessera API | Agents schrijven via `POST /tessera/`; production-safety flag verwijderd na succesvolle Fuseki-integratie |

---

### Epic 11 — Neo4j Kennisopslag Afbouwen

**Prioriteit: laatste — alleen uitvoeren als Epics 0–5 volledig stabiel zijn**
**Nota bene:** Neo4j blijft als identity store. Alleen de kennisopslag (Factors, Claims, ThemeVersions als graph data) verdwijnt uit Neo4j.

| # | User Story | Acceptatiecriteria |
|---|------------|-------------------|
| US-11.1 | Als platformbeheerder wil ik een migratiescript draaien dat alle Neo4j kennisdata converteert naar VALOR-O Tesserae in Fuseki | Alle Factors, Claims, deliberation data gemigreerd; checksums op aantal records kloppen |
| US-11.2 | Als developer wil ik de Neo4j-leesroutes voor Factors/Claims uitschakelen en Fuseki als enige kennisbron gebruiken | Alle API-endpoints retourneren graph-data uit Fuseki; Neo4j-driver alleen nog gebruikt voor auth/RBAC |

---

## 4. Risico's en mitigaties

| Risico | Waarschijnlijkheid | Impact | Mitigatie |
|--------|-------------------|--------|-----------|
| Fuseki performance bij grote DesignSpaces | Middel | Middel | Named graph partitionering; ELK voor real-time OWL EL |
| `useCausaData` refactor breekt bestaande UI | Hoog | Hoog | Adapter-patroon: REST endpoints blijven werken, schrijven naar beide stores tegelijk |
| RBAC-gat bij nieuwe Tessera/SPARQL routes | Hoog | Hoog | Elke nieuwe route verplicht `Depends(get_current_user)` + Neo4j permissiecheck; integratietest als poortwachter (US-0.4) |
| Fuseki per ongeluk publiek bereikbaar | Laag | Kritiek | Fuseki draait op intern Docker-netwerk; geen publieke poort in Coolify config |
| Bestaande deliberation data verloren bij migratie | Middel | Hoog | Dual-write periode: data gaat naar zowel Neo4j als Fuseki; Epic 11 pas na volledige verificatie |
| gUFO-terminologie lekt door naar gebruikersinterface | Middel | Laag | Perspectief-specifieke taallaag in frontend; vertaaltabel in `api.ts` projecties |

---

## 5. Technische schuld die direct aangepakt moet worden

Los van de refactor zijn er twee issues die nu al in de codebase zitten en aangepakt moeten worden:

1. **`PATCH /factors/{id}` en `DELETE /factors/{id}`** — geen authenticatie of permissiecontrole (Epic 0)
2. **Inconsistent gebruik van `check_permission`** — patroon moet worden gedocumenteerd en afgedwongen via een test (US-0.4)

---

## 6. Volgorde van GitHub Issues

```
Blok A — sequentieel, niet paralleliseerbaar:
  Epic 0 → Epic 1 → Epic 2 → Epic 3

Blok B — parallel mogelijk zodra Epic 3 stabiel is:
  Epic 4, Epic 5, Epic 10

Blok C — parallel mogelijk zodra Blok B stabiel is:
  Epic 6, Epic 7, Epic 8, Epic 9

Blok D — laatste stap:
  Epic 11 (alleen Neo4j kennisopslag; identity store blijft)
```

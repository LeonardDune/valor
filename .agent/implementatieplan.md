# Valor — Implementatieplan

**Laatste update:** 2026-03-28
**Branch:** epic/issue-352-tessera-engine-v1

---

## Afgeronde Epics

| Epic | Issue | Titel |
|------|-------|-------|
| Epic 0 | #213 | Security: auth op mutatieroutes |
| Epic 1 | #268 | Fuseki Triplestore Infrastructuur |
| Epic 2 | #269 | Tessera Engine (Backend) |
| Epic 3 | #270 | DesignSpace API & Named Graphs ← fundament voor alles |
| Epic 4 | #271 | Causa Perspectief: Semantische Upgrade |
| Epic 11 | #278 | Neo4j Kennisopslag Afbouwen |
| Epic 16 | #410 | DISC: Discourse & Deliberation Threads |

---

## Actieve Epic

### Epic T — Tessera-engine v1.0 (#352)

**Branch:** `epic/issue-352-tessera-engine-v1`

| US | Issue | Status | Notitie |
|----|-------|--------|---------|
| US-T.4 | #372 | ✅ gemerged | PROV-O logging |
| US-T.5 | #384 | ✅ gemerged | GDI-flag TruthfulnessIssue |
| US-T.3 | #371 | ✅ gemerged | WebSocket TESSERA_PROPOSED / TESSERA_CONTESTED |
| US-T.1 | #369 | ✅ gemerged | Conflictdetectie via valor:undermines |
| US-T.2 | #370 | ⏳ geblokkeerd | Auto-CapabilityGap — wacht op US-9.4 (#368) uit Epic 9 |

**Volgende stap:** Epic T epic branch mergen naar `development` (US-T.2 deferred naar na Epic 9).

---

## Implementatievolgorde (open Epics)

### Fase A — Parallelle perspectieven (onafhankelijk, starten zodra Epic T gemerged)

Alle vier vereisen alleen Epic 3 ✅. Kunnen parallel lopen.

| Epic | Issue | Titel | Afhankelijkheden |
|------|-------|-------|------------------|
| Epic 17 US-17.0 | #475 | Write-path consolidatie (prerequisite voor rest E17) | Epic 3 ✅, Epic 4 ✅ |
| Epic 6 | #273 | Socia Perspectief | Epic 3 ✅ |
| Epic 7 | #274 | Axia Perspectief | Epic 3 ✅ |
| Epic 8 | #275 | Forma Perspectief | Epic 3 ✅ |
| Epic 10 | #277 | AI Agents: Socratische Gesprekspartner | Epic 3 ✅ |

> **Let op US-17.0 (#475):** consolideert de twee divergerende write-paden (`fuseki_knowledge.py` → asis en `tessera.py` → main graph) naar één `baseline`-pad. Moet vóór de andere Epic 17 stories én vóór productie-migratie.

### Fase B — Afhankelijk van Socia + Axia stabiel

| Epic | Issue | Titel | Afhankelijkheden |
|------|-------|-------|------------------|
| Epic 17 (rest) | #456 | Baseline/Scenario Navigatie (US-17.1 t/m 17.5) | US-17.0 ✅, Epic 6 stabiel, Epic 7 stabiel |
| Epic 9 | #276 | Lexa & Acta Perspectieven | Epic 3 ✅, Epic 6 stabiel, Epic 7 stabiel, Epic T ✅ |

> Epic 9 US-9.4 (#368) — CAPAX-engine gate-check — **deblokkert US-T.2** uit Epic T.

### Fase C — Afhankelijk van Epic 9 + IssueCommunity

| Epic | Issue | Titel | Afhankelijkheden |
|------|-------|-------|------------------|
| Epic T US-T.2 | #370 | Auto-CapabilityGap | US-9.4 (#368) uit Epic 9 |
| Epic 14 | #406 | IssueCommunity & Ecosysteem-legitimering | Epic 3 ✅, valor-core OWL-module in Fuseki |
| Epic 12 | #405 | DEMOS: Democratische Inclusiviteitstoetsing | Epic 6 stabiel, Epic 14 ✅ |
| Epic 15 | #407 | Platform Governance: Hard & Soft Ethics | Epic 3 ✅, integreert Epic 10 & 12 |

### Fase D — Delibera afronden (alles samenkomt hier)

| Epic | Issue | Titel | Afhankelijkheden |
|------|-------|-------|------------------|
| Epic 5 | #272 | Delibera Perspectief | Epic 3 ✅, Epic 4 ✅, Epic 9, Epic 12, Epic 17 |

**Gedetailleerde US-afhankelijkheden binnen Epic 5:**

| US | Issue | Geblokkeerd door |
|----|-------|-----------------|
| US-5.0 | #441 | — (Neo4j → Tessera baseId migratie, start hier) |
| US-5.1 t/m 5.4 | #302–#305 | onafhankelijk |
| US-5.5 | #361 | Epic 9 US-9.4 (FeasibilityAssessment) |
| US-5.6 | #362 | onafhankelijk |
| US-5.7 | #385 | Epic 12 (InclusivityAssessment) |
| US-5.8 | #386 | Epic 9 LEXA+ (US-9.6) |

---

## Dependency-diagram

```
Epic 3 ✅ (fundament)
├── Epic T (#352) ← actief
│   └── US-T.2 ──── wacht op Epic 9 US-9.4
├── Epic 17 US-17.0 (#475) ← start zodra Epic T gemerged
├── Epic 6 (#273) ← Socia
│   └── (stabiel) ──→ Epic 9, Epic 12, Epic 17 rest
├── Epic 7 (#274) ← Axia
│   └── (stabiel) ──→ Epic 9, Epic 17 rest
├── Epic 8 (#275) ← Forma (onafhankelijk)
├── Epic 10 (#277) ← AI Agents (onafhankelijk)
├── Epic 9 (#276) ← Lexa & Acta
│   ├── US-9.4 ──→ deblokkert US-T.2 + Epic 5 US-5.5
│   └── LEXA+ (US-9.6) ──→ Epic 5 US-5.8
├── Epic 14 (#406) ← IssueCommunity
│   └── (✅) ──→ Epic 12
├── Epic 12 (#405) ← DEMOS
│   └── (✅) ──→ Epic 5 US-5.7
├── Epic 15 (#407) ← Platform Governance
└── Epic 5 (#272) ← Delibera (eindpunt, alles samenkomt)
```

---

## Geblokkeerde items (samenvatting)

| Item | Geblokkeerd door | Verwacht in |
|------|-----------------|-------------|
| US-T.2 Auto-CapabilityGap (#370) | Epic 9 US-9.4 (#368) | Na Fase B |
| Epic 5 US-5.5 FeasibilityAssessment gate | Epic 9 US-9.4 (#368) | Na Fase B |
| Epic 5 US-5.7 InclusivityAssessment gate | Epic 12 (#405) | Na Fase C |
| Epic 5 US-5.8 NormativeFeasibility gate | Epic 9 US-9.6 LEXA+ | Na Fase B |
| Epic 12 DEMOS | Epic 14 IssueCommunity | Na Fase C start |
| Epic 17 rest (17.1–17.5) | Epic 6 + 7 stabiel | Na Fase A |

---

## Hoe dit plan te onderhouden

- **Na merge van een User Story:** vink de US af (✅) in de actieve Epic-tabel
- **Na merge van een Epic naar development:** verplaats naar "Afgeronde Epics", update actieve Epic
- **Bij nieuwe blokkade of afhankelijkheidswijziging:** update de geblokkeerde items tabel + dependency-diagram
- **Bij start nieuwe Epic:** voeg toe als "Actieve Epic" sectie met US-tabel

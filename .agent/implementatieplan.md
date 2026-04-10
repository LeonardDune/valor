# Valor — Implementatieplan

**Laatste update:** 2026-04-06
**Branch:** development

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
| Epic 18 | #481 | Entity Identiteitsarchitectuur (US-AI.1 t/m US-AI.8) |
| Epic 6 | #273 | Socia Perspectief v1 (US-6.1, 6.2, 6.4, 6.5 ✅ — US-6.3 deferred → vervangen door US-6.13) |
| Epic 7 | #274 | Axia Perspectief v1 (US-7.1–7.5 volledig ✅ — v2 scope open) |

---

## Actieve Epics

### Epic T — Tessera-engine v1.0 (#352) [deels afgerond]

| US | Issue | Status | Notitie |
|----|-------|--------|---------|
| US-T.4 | #372 | ✅ gemerged | PROV-O logging |
| US-T.5 | #384 | ✅ gemerged | GDI-flag TruthfulnessIssue |
| US-T.3 | #371 | ✅ gemerged | WebSocket TESSERA_PROPOSED / TESSERA_CONTESTED |
| US-T.1 | #369 | ✅ gemerged | Conflictdetectie via valor:undermines |
| US-T.2 | #370 | ⏳ geblokkeerd | Auto-CapabilityGap — wacht op US-9.4 (#368) uit Epic 9 |

**Status:** Epic T epic branch gemerged naar `development` (US-T.2 deferred naar na Epic 9).

---

## Implementatievolgorde (open Epics)

### Fase A — Parallelle perspectieven v1 ✅ AFGEROND

| Epic | Issue | Titel | Status |
|------|-------|-------|--------|
| Epic 17 US-17.0 | #475 | Write-path consolidatie | ✅ gemerged |
| Epic 6 v1 | #273 | Socia Perspectief (basiscanvas) | ✅ gemerged |
| Epic 7 v1 | #274 | Axia Perspectief (basiscanvas) | ✅ gemerged |

### Fase A2 — Socia + Axia v2: ontologie-gedreven rebuild (ACTIEF)

Epic 6 en Epic 7 zijn heropend met volledige v2 User Stories op basis van VALOR-O. Dit is een uitbreiding van de afgeronde v1-scope, niet een vervanging.

**Epic 6 v2 — SOCIA (#273)**

| US | Issue | Titel | Status |
|----|-------|-------|--------|
| US-6.00 | #511 | Bootstrap: SOCIA-schema laden | ⬜ open |
| US-6.01 | #512 | SOCIA-perspectief registreren | ⬜ open |
| US-6.02 | #513 | StakeholderMap laden vanuit graph | ⬜ open |
| US-6.03 | #514 | Stakeholder-node aanmaken | ⬜ open |
| US-6.04 | #515 | ActorBoundary visualiseren | ⬜ open |
| US-6.05 | #516 | Interne elementen toevoegen aan ActorBoundary | ⬜ open |
| US-6.06 | #517 | StakeholderClaim aanmaken als Tessera | ⬜ open |
| US-6.07 | #518 | IntentionalDependency aanmaken | ⬜ open |
| US-6.08 | #519 | ACTA-koppeling op IntentionalDependency | ⏳ geblokkeerd: Epic 9 |
| US-6.09 | #520 | AXIA-overlay per Stakeholder | ⏳ geblokkeerd: Epic 7 v2 |
| US-6.10 | #521 | DEMOS-blindspot signaleren | ⬜ open (partieel: Epic 12) |
| US-6.11 | #522 | StakeholderMap persisteren | ⬜ open |
| US-6.12 | #523 | Afhankelijkheidsmatrix via SPARQL | ⬜ open |
| US-6.13 | #524 | StakeholderClaim epistemisch beheren | ⬜ open |
| US-6.14 | #525 | Real-time synchronisatie | ⬜ open |
| US-6.15 | #526 | SPARQL CONSTRUCT export | ⬜ open |

**Epic 7 v2 — AXIA (#274)**

| US | Issue | Titel | Status |
|----|-------|-------|--------|
| US-7.00 | #527 | Bootstrap: AXIA-schema laden | ✅ gemerged |
| US-7.01 | #528 | AXIA-perspectief registreren | ✅ gemerged |
| US-7.02 | #529 | Waardekaart laden + fix axia:concernsValueType | ✅ gemerged |
| US-7.03 | #530 | ValueClaim aanmaken via waardepalet | ✅ gemerged |
| US-7.04 | #531 | ValueTensionClaim aanmaken | ✅ gemerged |
| US-7.05 | #532 | DesignImplication aanmaken | ⬜ open |
| US-7.06 | #533 | ValueType-palet met live filtering | ⬜ open |
| US-7.07 | #534 | Alternatief-filter op canvas | ⏳ geblokkeerd: Epic 17 (#456) |
| US-7.08 | #535 | Heatmap-overlay via SPARQL-aggregatie | ⬜ open |
| US-7.09 | #536 | Alternatievenvergelijking via SPARQL | ⬜ open |
| US-7.10 | #537 | ValueClaim als Tessera beheren | ⬜ open |
| US-7.11 | #538 | Evidence koppelen aan ValueClaim | ⬜ open |
| US-7.12 | #539 | Real-time synchronisatie | ⬜ open |
| US-7.13 | #540 | SPARQL CONSTRUCT export | ⬜ open |
| US-7.14 | #541 | Canvas-snapshot exporteren | ⬜ open |

> **Aanbevolen volgorde binnen Fase A2:**
> AXIA eerst (US-7.00–7.03 → ontologie fix + bootstrap), dan SOCIA (US-6.00–6.03), daarna parallel.

### Fase B — ONTSLOTEN: Socia + Axia stabiel ✅

| Epic | Issue | Titel | Afhankelijkheden |
|------|-------|-------|------------------|
| Epic 17 (rest) | #456 | Baseline/Scenario Navigatie (US-17.1 t/m 17.5) | US-17.0 ✅, Epic 6 ✅, Epic 7 ✅ |
| Epic 9 | #276 | Lexa & Acta Perspectieven | Epic 3 ✅, Epic 6 ✅, Epic 7 ✅, Epic T ✅ |

> Epic 9 US-9.4 (#368) — CAPAX-engine gate-check — **deblokkert US-T.2** uit Epic T en **US-6.3** uit Epic 6.

### Fase C — Afhankelijk van Epic 9 + IssueCommunity

| Epic | Issue | Titel | Afhankelijkheden |
|------|-------|-------|------------------|
| Epic T US-T.2 | #370 | Auto-CapabilityGap | US-9.4 (#368) uit Epic 9 |
| US-6.3 | #363 | CAPAX-overlay in Socia | US-9.4 (#368) uit Epic 9 |
| Epic 14 | #406 | IssueCommunity & Ecosysteem-legitimering | Epic 3 ✅, valor-core OWL-module in Fuseki |
| Epic 12 | #405 | DEMOS: Democratische Inclusiviteitstoetsing | Epic 6 ✅, Epic 14 ✅ |
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
├── Epic T (#352) ✅ (US-T.2 wacht op Epic 9)
├── Epic 17 US-17.0 (#475) ✅
├── Epic 6 v1 (#273) ✅ → Epic 6 v2 (#511–#526) ← ACTIEF
│   ├── US-6.08 (#519) wacht op Epic 9 ACTA
│   ├── US-6.09 (#520) wacht op Epic 7 v2
│   └── US-6.10 (#521) partieel geblokkeerd door Epic 12
├── Epic 7 v1 (#274) ✅ → Epic 7 v2 (#527–#541) ← ACTIEF
│   └── US-7.07 (#534) wacht op Epic 17 rest
├── Epic 8 (#275) ← Forma (onafhankelijk, open)
├── Epic 10 (#277) ← AI Agents (onafhankelijk, open)
├── Epic 9 (#276) ← Lexa & Acta ← VOLGENDE PRIORITEIT
│   ├── US-9.4 ──→ deblokkert US-T.2 + US-6.3 + Epic 5 US-5.5
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
| US-6.08 ACTA-koppeling (#519) | Epic 9 ACTA (#276) | Fase B |
| US-6.09 AXIA-overlay (#520) | Epic 7 v2 ValueClaims (#529–#530) | Fase A2 |
| US-6.10 DEMOS-signalering volledig (#521) | Epic 12 DEMOS (#405) | Fase C |
| US-7.07 Alternatief-filter (#534) | Epic 17 rest (#456) | Fase B |
| US-T.2 Auto-CapabilityGap (#370) | Epic 9 US-9.4 (#368) | Na Fase B |
| Epic 5 US-5.5 FeasibilityAssessment gate | Epic 9 US-9.4 (#368) | Na Fase B |
| Epic 5 US-5.7 InclusivityAssessment gate | Epic 12 (#405) | Na Fase C |
| Epic 5 US-5.8 NormativeFeasibility gate | Epic 9 US-9.6 LEXA+ | Na Fase B |
| Epic 12 DEMOS | Epic 14 IssueCommunity | Na Fase C start |

---

## Hoe dit plan te onderhouden

- **Na merge van een User Story:** vink de US af (✅) in de actieve Epic-tabel
- **Na merge van een Epic naar development:** verplaats naar "Afgeronde Epics", update actieve Epic
- **Bij nieuwe blokkade of afhankelijkheidswijziging:** update de geblokkeerde items tabel + dependency-diagram
- **Bij start nieuwe Epic:** voeg toe als "Actieve Epic" sectie met US-tabel

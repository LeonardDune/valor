# Phase Snapshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Na elke deliberatie-finalisatie wordt een onveranderlijke fase-snapshot aangemaakt in Fuseki; de actieve `asis`-graph behoudt alleen de goedgekeurde items; historische fasen zijn volledig (inclusief afgewezen items + argumentatie) en navigeerbaar via een fase-switcher in de UI.

**Architecture:** Na `finalize_deliberation` wordt de volledige `asis`-graph gekopieerd naar `urn:valor:ds:{id}/phase/{session_id}` (snapshot met alles), daarna worden afgewezen tesserae uit `asis` verwijderd. Lijst van snapshots + uitkomsten per tessera worden in de `decisions`-graph geregistreerd. De frontend laadt factoren/claims uit de snapshot-graph in plaats van `asis` wanneer een historische fase actief is.

**Tech Stack:** Python/FastAPI, SPARQL 1.1 Update (Fuseki), React 19 + TypeScript, React Query, Shadcn/UI

---

## Bestandsstructuur

### Nieuw
- `backend/app/db/fuseki_phases.py` — SPARQL-operaties voor snapshot aanmaken, annoteren, prunen en opvragen
- `frontend/src/components/deliberation/PhaseSelector.tsx` — Dropdown/select UI voor fase-navigatie

### Gewijzigd
- `backend/app/db/deliberation.py` — `finalize_deliberation` roept `fuseki_phases.create_phase_snapshot` aan
- `backend/app/routers/factors.py` — `GET /designspace/{ds_id}/factors` accepteert `?phase=<session_id>`
- `backend/app/routers/claims.py` — `GET /designspace/{ds_id}/claims` accepteert `?phase=<session_id>`
- `backend/app/routers/designspace.py` — nieuw endpoint `GET /designspace/{ds_id}/phase-snapshots`
- `backend/app/db/fuseki_knowledge.py` — `_sparql_get_factors` en `_sparql_get_claims` accepteren optioneel `graph_uri`
- `frontend/src/services/api.ts` — `getThemeVersionFactors`, `getThemeVersionClaims` accepteren optioneel `phase`; nieuw `getPhaseSnapshots`
- `frontend/src/context/DesignSpaceContext.tsx` — voegt `phaseSnapshots`, `activePhase`, `setActivePhase` toe
- `frontend/src/components/Workspace/ValorWorkspace.tsx` — integreert `PhaseSelector`

---

## Consent-uitkomst definitie

Een tessera is **afgewezen** als:
- Het `tessera_base_id` niet voorkomt in de consent shortlist (d.w.z. uit ranking verwijderd: `discard_p >= 0.3`), **OF**
- Het in de consent shortlist zit maar minstens één deelnemer heeft `vote = 'reject'` uitgebracht

Een tessera is **geaccepteerd** als het in de shortlist zit en nul `reject`-stemmen heeft.

Tesserae die **nooit deel uitmaakten van de sessie** (geen ranking/feedback gekregen) worden **niet aangeraakt** — ze blijven in `asis`.

---

## Task 1: `fuseki_phases.py` — snapshot aanmaken en prunen

**Files:**
- Create: `backend/app/db/fuseki_phases.py`

### Stap 1.1 — Schrijf de module met drie functies

```python
"""SPARQL-operaties voor fase-snapshots in Fuseki.

Na elke deliberatie-finalisatie:
1. copy_asis_to_snapshot  — kopieert asis volledig naar phase/{session_id}
2. annotate_snapshot      — voegt phaseOutcome (Accepted/Rejected) per tessera toe
3. prune_rejected_from_asis — verwijdert afgewezen tesserae + afhankelijke claims uit asis
4. register_snapshot_in_decisions — registreert de snapshot in de decisions-graph zodat die opvraagbaar is
"""
import uuid
import logging
from datetime import datetime, timezone

from app.ontology import VALOR_NS
from app.services.fuseki import sparql_update, sparql_select_global

logger = logging.getLogger(__name__)

_XSD  = "http://www.w3.org/2001/XMLSchema#"
_PROV = "https://www.w3.org/ns/prov#"


def _asis_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/asis"

def _phase_graph(ds_id: str, session_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/phase/{session_id}"

def _decisions_graph(ds_id: str) -> str:
    return f"urn:valor:ds:{ds_id}/decisions"

def _tessera_uri(base_id: str) -> str:
    return f"urn:valor:tessera:{base_id}"

def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


async def copy_asis_to_snapshot(ds_id: str, session_id: str) -> str:
    """Kopieert de volledige asis-graph naar een nieuwe phase-graph.
    Retourneert de phase-graph URI.
    """
    asis  = _asis_graph(ds_id)
    phase = _phase_graph(ds_id, session_id)
    sparql = f"COPY <{asis}> TO <{phase}>"
    await sparql_update(sparql, ds_id)
    return phase


async def annotate_snapshot(
    ds_id: str,
    session_id: str,
    accepted_ids: list[str],
    rejected_ids: list[str],
) -> None:
    """Voegt phaseOutcome-triples toe aan de snapshot-graph."""
    phase = _phase_graph(ds_id, session_id)
    snapshot_uri = f"urn:valor:phase-snapshot:{session_id}"
    timestamp = datetime.now(timezone.utc).isoformat()

    outcome_triples = []
    for tid in accepted_ids:
        turi = _tessera_uri(tid)
        outcome_triples.append(
            f'<{turi}> <{VALOR_NS}phaseOutcome> <{VALOR_NS}Accepted> .'
        )
    for tid in rejected_ids:
        turi = _tessera_uri(tid)
        outcome_triples.append(
            f'<{turi}> <{VALOR_NS}phaseOutcome> <{VALOR_NS}Rejected> .'
        )

    outcomes_block = "\n    ".join(outcome_triples)

    sparql = f"""INSERT DATA {{
  GRAPH <{phase}> {{
    <{snapshot_uri}> a <{VALOR_NS}PhaseSnapshot> ;
      <{VALOR_NS}sessionId> "{_escape(session_id)}"^^<{_XSD}string> ;
      <{_PROV}generatedAtTime> "{timestamp}"^^<{_XSD}dateTime> .
    {outcomes_block}
  }}
}}"""
    await sparql_update(sparql, ds_id)


async def register_snapshot_in_decisions(
    ds_id: str,
    session_id: str,
    accepted_count: int,
    rejected_count: int,
) -> None:
    """Registreert de snapshot in de decisions-graph zodat deze opvraagbaar is."""
    decisions = _decisions_graph(ds_id)
    phase     = _phase_graph(ds_id, session_id)
    snapshot_uri = f"urn:valor:phase-snapshot:{session_id}"
    ds_uri    = f"urn:valor:ds:{ds_id}"
    timestamp = datetime.now(timezone.utc).isoformat()

    sparql = f"""INSERT DATA {{
  GRAPH <{decisions}> {{
    <{snapshot_uri}> a <{VALOR_NS}PhaseSnapshot> ;
      <{VALOR_NS}inDesignSpace> <{ds_uri}> ;
      <{VALOR_NS}sessionId> "{_escape(session_id)}"^^<{_XSD}string> ;
      <{VALOR_NS}graphUri> "{_escape(phase)}"^^<{_XSD}string> ;
      <{VALOR_NS}acceptedCount> "{accepted_count}"^^<{_XSD}integer> ;
      <{VALOR_NS}rejectedCount> "{rejected_count}"^^<{_XSD}integer> ;
      <{_PROV}generatedAtTime> "{timestamp}"^^<{_XSD}dateTime> .
  }}
}}"""
    await sparql_update(sparql, ds_id)


async def prune_rejected_from_asis(ds_id: str, rejected_ids: list[str]) -> None:
    """Verwijdert afgewezen tesserae en hun afhankelijke claims uit asis.

    Stap 1: verwijder claims waarvan fromFactor of toFactor afgewezen is.
    Stap 2: verwijder de afgewezen tesserae zelf.
    """
    if not rejected_ids:
        return

    asis = _asis_graph(ds_id)
    uris = ", ".join(f"<{_tessera_uri(tid)}>" for tid in rejected_ids)

    # Stap 1: verwijder claims die verwijzen naar afgewezen factoren
    sparql_claims = f"""DELETE {{
  GRAPH <{asis}> {{
    ?claim ?p ?o .
  }}
}}
WHERE {{
  GRAPH <{asis}> {{
    ?claim ?p ?o .
    {{ ?claim <{VALOR_NS}fromFactor> ?factor . FILTER(?factor IN ({uris})) }}
    UNION
    {{ ?claim <{VALOR_NS}toFactor> ?factor . FILTER(?factor IN ({uris})) }}
  }}
}}"""
    await sparql_update(sparql_claims, ds_id)

    # Stap 2: verwijder de afgewezen tesserae zelf
    sparql_tesserae = f"""DELETE {{
  GRAPH <{asis}> {{
    ?s ?p ?o .
  }}
}}
WHERE {{
  GRAPH <{asis}> {{
    ?s ?p ?o .
    FILTER(?s IN ({uris}))
  }}
}}"""
    await sparql_update(sparql_tesserae, ds_id)


async def get_phase_snapshots(ds_id: str) -> list[dict]:
    """Retourneert alle fase-snapshots voor een DesignSpace, gesorteerd op tijd."""
    decisions = _decisions_graph(ds_id)
    rows = await sparql_select_global(f"""
SELECT ?snapshotUri ?sessionId ?graphUri ?generatedAt ?acceptedCount ?rejectedCount WHERE {{
  GRAPH <{decisions}> {{
    ?snapshotUri a <{VALOR_NS}PhaseSnapshot> ;
      <{VALOR_NS}sessionId> ?sessionId ;
      <{VALOR_NS}graphUri> ?graphUri ;
      <{_PROV}generatedAtTime> ?generatedAt .
    OPTIONAL {{ ?snapshotUri <{VALOR_NS}acceptedCount> ?acceptedCount }}
    OPTIONAL {{ ?snapshotUri <{VALOR_NS}rejectedCount> ?rejectedCount }}
  }}
}}
ORDER BY ASC(?generatedAt)
""")
    return [
        {
            "session_id": r["sessionId"],
            "graph_uri":  r["graphUri"],
            "created_at": r["generatedAt"],
            "accepted_count": int(r.get("acceptedCount", 0)),
            "rejected_count": int(r.get("rejectedCount", 0)),
        }
        for r in rows
    ]
```

- [ ] **Stap 1.2 — Controleer syntax**

```bash
cd backend && python -c "from app.db.fuseki_phases import copy_asis_to_snapshot; print('OK')"
```
Verwacht: `OK`

- [ ] **Stap 1.3 — Commit**

```bash
git add backend/app/db/fuseki_phases.py
git commit -m "feat(phases): voeg fuseki_phases module toe voor snapshot-operaties"
```

---

## Task 2: `deliberation.py` — finalize roept snapshot aan

**Files:**
- Modify: `backend/app/db/deliberation.py` (functie `finalize_deliberation`)

De huidige `finalize_deliberation` sluit de sessie en zet `current_phase` door. Vervang het blok ná het sluiten van de sessie met de snapshot-logica.

### Bepaal afgewezen tesserae

```python
async def _get_rejected_tessera_ids(session_id: str) -> tuple[list[str], list[str]]:
    """Retourneert (accepted_ids, rejected_ids) op basis van ranking + consent votes."""
    driver = get_driver()

    # Alle tesserae met rankings
    query_rankings = """
    MATCH (s:VotingSession {id: $sid})-[:COLLECTED]->(r:Ranking)
    WITH r.tessera_base_id AS tid,
         count(*) AS total,
         count(CASE WHEN r.category = 'discard' THEN 1 END) AS discard_count
    RETURN tid, (toFloat(discard_count) / total) AS discard_p
    """

    # Consent-objections per tessera
    query_consent = """
    MATCH (s:VotingSession {id: $sid})-[:COLLECTED]->(v:ConsentVote)
    WHERE v.vote = 'reject'
    RETURN DISTINCT v.tessera_base_id AS tid
    """

    with driver.session() as sess:
        rankings = {r["tid"]: r["discard_p"] for r in sess.run(query_rankings, {"sid": session_id})}
        consent_rejected = {r["tid"] for r in sess.run(query_consent, {"sid": session_id})}

    rejected, accepted = [], []
    for tid, discard_p in rankings.items():
        if discard_p >= 0.3 or tid in consent_rejected:
            rejected.append(tid)
        else:
            accepted.append(tid)

    return accepted, rejected
```

### Nieuw `finalize_deliberation`

```python
async def finalize_deliberation(session_id: str, user_id: str) -> Dict[str, Any]:
    """Sluit sessie, maakt fase-snapshot en prunet afgewezen items uit asis."""
    from app.db.sessions import get_session_context, get_ds_id_for_session
    from app.db.designspace import get_design_space_meta, set_design_space_phase, PHASE_SEQUENCE
    from app.db.fuseki_phases import (
        copy_asis_to_snapshot,
        annotate_snapshot,
        register_snapshot_in_decisions,
        prune_rejected_from_asis,
    )

    driver = get_driver()
    issue_id, project_id = await get_session_context(session_id)
    if not issue_id:
        return {"status": "error", "message": "Context niet gevonden"}

    try:
        # 1. Sluit sessie
        query_close = """
        MATCH (s:VotingSession {id: $sid})
        SET s.status = 'closed', s.stage = 'closed', s.ended_at = datetime()
        """
        with driver.session() as sess:
            sess.run(query_close, {"sid": session_id})

        # 2. Bepaal geaccepteerde en afgewezen tesserae
        accepted_ids, rejected_ids = await _get_rejected_tessera_ids(session_id)

        # 3. Fase-snapshot aanmaken (alleen als er een DesignSpace aan hangt)
        ds_id = await get_ds_id_for_session(session_id)
        if ds_id:
            await copy_asis_to_snapshot(ds_id, session_id)
            await annotate_snapshot(ds_id, session_id, accepted_ids, rejected_ids)
            await register_snapshot_in_decisions(
                ds_id, session_id, len(accepted_ids), len(rejected_ids)
            )
            await prune_rejected_from_asis(ds_id, rejected_ids)

            # 4. Zet DesignSpace door naar de volgende fase
            meta = get_design_space_meta(ds_id)
            current_phase = (meta or {}).get("current_phase", "exploration")
            next_phase = None
            if current_phase in PHASE_SEQUENCE:
                idx = PHASE_SEQUENCE.index(current_phase)
                if idx + 1 < len(PHASE_SEQUENCE):
                    next_phase = PHASE_SEQUENCE[idx + 1]
                    set_design_space_phase(ds_id, next_phase)

        return {
            "status": "success",
            "session_id": session_id,
            "accepted": len(accepted_ids),
            "rejected": len(rejected_ids),
            "next_phase": next_phase if ds_id else None,
        }

    except Exception as e:
        logger.error(f"Error finalizing deliberation: {e}")
        return {"status": "error", "message": str(e)}
```

- [ ] **Stap 2.1 — Implementeer `_get_rejected_tessera_ids` in `deliberation.py`**

Voeg de helper-functie toe vóór `finalize_deliberation`.

- [ ] **Stap 2.2 — Vervang `finalize_deliberation`**

Vervang de bestaande functie door de nieuwe versie hierboven.

- [ ] **Stap 2.3 — Controleer import**

```bash
cd backend && python -c "from app.db.deliberation import finalize_deliberation; print('OK')"
```
Verwacht: `OK`

- [ ] **Stap 2.4 — Commit**

```bash
git add backend/app/db/deliberation.py
git commit -m "feat(phases): finalize_deliberation maakt fase-snapshot en prunet asis"
```

---

## Task 3: Backend — snapshot-lijst endpoint + phase-parameter voor factors/claims

**Files:**
- Modify: `backend/app/routers/designspace.py` — nieuw `GET /designspace/{ds_id}/phase-snapshots`
- Modify: `backend/app/routers/factors.py` — voeg `phase` query-param toe
- Modify: `backend/app/routers/claims.py` — voeg `phase` query-param toe
- Modify: `backend/app/db/fuseki_knowledge.py` — `_sparql_get_factors` en `_sparql_get_claims` accepteren `graph_uri`

### 3.1 — `fuseki_knowledge.py`: optionele `graph_uri` parameter

Pas de signaturen aan:

```python
async def _sparql_get_factors(ds_id: str, graph_uri: str | None = None) -> list[dict]:
    target = graph_uri or _ds_asis_graph(ds_id)
    rows = await sparql_select_global(f"""
SELECT ?tessera ?baseId ?name ?role ?description ?outcome WHERE {{
  GRAPH <{target}> {{
    ?tessera a <{VALOR_NS}Tessera> ;
             <{VALOR_NS}baseId> ?baseId ;
             <{VALOR_NS}claimContent> ?name ;
             <{VALOR_NS}factorRole> ?role .
    OPTIONAL {{ ?tessera <{VALOR_NS}description> ?description }}
    OPTIONAL {{ ?tessera <{VALOR_NS}phaseOutcome> ?outcome }}
    FILTER NOT EXISTS {{ ?tessera <{VALOR_NS}fromFactor> ?x }}
  }}
}}
""")
    return [
        {
            "id": row["baseId"],
            "version_id": row["baseId"],
            "name": row["name"],
            "description": row.get("description"),
            "type": row.get("role"),
            "theme_id": None,
            "thread_id": None,
            "phase_outcome": row.get("outcome", "").split("#")[-1] if row.get("outcome") else None,
        }
        for row in rows
    ]
```

Doe hetzelfde voor `_sparql_get_claims` — voeg `graph_uri: str | None = None` toe, gebruik `target` i.p.v. `asis_graph`, en voeg `?outcome` toe aan SELECT + OPTIONAL.

### 3.2 — `factors.py`: phase query-param

```python
from typing import Optional

@router.get("/designspace/{ds_id}/factors")
async def list_designspace_factors(
    ds_id: str,
    phase: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    if not await check_permission(user["id"], ds_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze DesignSpace")
    graph_uri = f"urn:valor:ds:{ds_id}/phase/{phase}" if phase else None
    return await fuseki_knowledge._sparql_get_factors(ds_id, graph_uri=graph_uri)
```

### 3.3 — `claims.py`: phase query-param

Identieke aanpak als factors.

### 3.4 — `designspace.py`: phase-snapshots endpoint

```python
from app.db.fuseki_phases import get_phase_snapshots

@router.get("/{design_space_id}/phase-snapshots")
async def list_phase_snapshots(
    design_space_id: str,
    user: dict = Depends(get_current_user),
):
    if not await check_permission(user["id"], design_space_id, Role.VIEWER):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze DesignSpace")
    return await get_phase_snapshots(design_space_id)
```

- [ ] **Stap 3.1 — Pas `_sparql_get_factors` aan in `fuseki_knowledge.py`**
- [ ] **Stap 3.2 — Pas `_sparql_get_claims` aan in `fuseki_knowledge.py`**
- [ ] **Stap 3.3 — Pas `factors.py` aan (voeg `phase` param toe)**
- [ ] **Stap 3.4 — Pas `claims.py` aan (voeg `phase` param toe)**
- [ ] **Stap 3.5 — Voeg phase-snapshots endpoint toe aan `designspace.py`**
- [ ] **Stap 3.6 — Controleer imports**

```bash
cd backend && python -c "from app.routers.factors import router; print('OK')"
cd backend && python -c "from app.routers.claims import router; print('OK')"
cd backend && python -c "from app.routers.designspace import router; print('OK')"
```
Verwacht: alle drie `OK`

- [ ] **Stap 3.7 — Start backend en test manueel**

```bash
cd backend && python -m uvicorn app.main:app --reload --port 8000
# Test:
curl -s http://localhost:8000/designspace/{ds_id}/phase-snapshots \
  -H "Authorization: Bearer {token}" | python -m json.tool
```
Verwacht: lege array `[]` (of snapshots als er al finalisaties zijn).

- [ ] **Stap 3.8 — Commit**

```bash
git add backend/app/db/fuseki_knowledge.py backend/app/routers/factors.py \
        backend/app/routers/claims.py backend/app/routers/designspace.py
git commit -m "feat(phases): phase query-param voor factors/claims + phase-snapshots endpoint"
```

---

## Task 4: Frontend — API-calls + `DesignSpaceContext` uitbreiden

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/context/DesignSpaceContext.tsx`

### 4.1 — `api.ts`: nieuw type + functies

```typescript
export interface PhaseSnapshot {
    session_id: string;
    graph_uri: string;
    created_at: string;
    accepted_count: number;
    rejected_count: number;
}

// In het api-object:
getPhaseSnapshots: async (dsId: string): Promise<PhaseSnapshot[]> => {
    const response = await apiClient.get<PhaseSnapshot[]>(`/designspace/${dsId}/phase-snapshots`);
    return response.data;
},

// Bestaande aanpassen — voeg optionele phase toe:
getThemeVersionClaims: async (dsId: string, phase?: string) => {
    const params = phase ? { phase } : {};
    const response = await apiClient.get<Claim[]>(`/designspace/${dsId}/claims`, { params });
    return response.data;
},

getThemeVersionFactors: async (dsId: string, phase?: string) => {
    const params = phase ? { phase } : {};
    const response = await apiClient.get<Factor[]>(`/designspace/${dsId}/factors`, { params });
    return response.data;
},

getThemeFactors: async (dsId: string, phase?: string) => {
    const params = phase ? { phase } : {};
    const response = await apiClient.get<Factor[]>(`/designspace/${dsId}/factors`, { params });
    return response.data;
},
```

### 4.2 — `DesignSpaceContext.tsx`: fase-state

Voeg toe aan `DesignSpaceContextType`:
```typescript
phaseSnapshots: PhaseSnapshot[];
activePhaseId: string | null;   // null = huidige/asis
setActivePhaseId: (id: string | null) => void;
```

In de provider:
```typescript
const [phaseSnapshots, setPhaseSnapshots] = useState<PhaseSnapshot[]>([]);
const [activePhaseId, setActivePhaseId] = useState<string | null>(null);

// Laad snapshots samen met versieinformatie:
const [fetchedSnapshots, fetchedActive, fetchedVersions] = await Promise.all([
    api.getPhaseSnapshots(dsId),
    api.getThemeActiveVersion(dsId),
    api.getThemeVersions(dsId)
]);
setPhaseSnapshots(fetchedSnapshots);
```

- [ ] **Stap 4.1 — Voeg `PhaseSnapshot` interface toe aan `api.ts`**
- [ ] **Stap 4.2 — Voeg `getPhaseSnapshots` toe aan het api-object in `api.ts`**
- [ ] **Stap 4.3 — Pas `getThemeVersionClaims`, `getThemeVersionFactors`, `getThemeFactors` aan**
- [ ] **Stap 4.4 — Breid `DesignSpaceContextType` uit in `DesignSpaceContext.tsx`**
- [ ] **Stap 4.5 — Voeg state en laadlogica toe in `DesignSpaceProvider`**
- [ ] **Stap 4.6 — TypeScript check**

```bash
cd frontend && npm run build 2>&1 | grep -E "error TS|Error"
```
Verwacht: geen TypeScript errors.

- [ ] **Stap 4.7 — Commit**

```bash
git add frontend/src/services/api.ts frontend/src/context/DesignSpaceContext.tsx
git commit -m "feat(phases): fase-snapshot state in DesignSpaceContext en api-calls"
```

---

## Task 5: Frontend — `PhaseSelector` component + integratie

**Files:**
- Create: `frontend/src/components/deliberation/PhaseSelector.tsx`
- Modify: `frontend/src/components/Workspace/ValorWorkspace.tsx`

### 5.1 — `PhaseSelector.tsx`

```tsx
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { History } from 'lucide-react';
import { type PhaseSnapshot } from '@/services/api';

interface PhaseSelectorProps {
    snapshots: PhaseSnapshot[];
    activePhaseId: string | null;
    onSelect: (phaseId: string | null) => void;
}

export const PhaseSelector: React.FC<PhaseSelectorProps> = ({
    snapshots,
    activePhaseId,
    onSelect,
}) => {
    if (snapshots.length === 0) return null;

    return (
        <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-muted-foreground" />
            <Select
                value={activePhaseId ?? 'current'}
                onValueChange={(v) => onSelect(v === 'current' ? null : v)}
            >
                <SelectTrigger className="w-52 h-8 text-sm">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="current">
                        <span className="font-medium">Huidige fase</span>
                    </SelectItem>
                    {snapshots.map((s, i) => (
                        <SelectItem key={s.session_id} value={s.session_id}>
                            <div className="flex items-center gap-2">
                                <span>Fase {i + 1}</span>
                                <span className="text-xs text-muted-foreground">
                                    {new Date(s.created_at).toLocaleDateString('nl-NL')}
                                </span>
                                <Badge variant="secondary" className="text-xs ml-1">
                                    {s.accepted_count} ✓
                                </Badge>
                                <Badge variant="destructive" className="text-xs">
                                    {s.rejected_count} ✗
                                </Badge>
                            </div>
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
            {activePhaseId && (
                <Badge variant="outline" className="text-xs text-amber-600 border-amber-400">
                    Alleen-lezen
                </Badge>
            )}
        </div>
    );
};
```

### 5.2 — `ValorWorkspace.tsx`: integratie

In `ValorWorkspace` haal `phaseSnapshots`, `activePhaseId`, `setActivePhaseId` op uit `useDesignSpace()`. Geef `activePhaseId` door als `phase`-prop naar `CausaShell`, zodat die er mee data ophaalt. Voeg `<PhaseSelector>` toe in de toolbar.

```tsx
// In ValorWorkspace.tsx — in het toolbar-gedeelte, naast bestaande controls:
<PhaseSelector
    snapshots={phaseSnapshots}
    activePhaseId={activePhaseId}
    onSelect={setActivePhaseId}
/>
```

In `CausaShell` (of waar de data-fetch plaatsvindt): geef `phase` door aan `getThemeVersionFactors` en `getThemeVersionClaims`.

- [ ] **Stap 5.1 — Maak `PhaseSelector.tsx` aan**
- [ ] **Stap 5.2 — Integreer `PhaseSelector` in `ValorWorkspace.tsx`**
- [ ] **Stap 5.3 — Geef `activePhaseId` als prop door naar data-fetch functies in Shell/ValorWorkspace**
- [ ] **Stap 5.4 — TypeScript check**

```bash
cd frontend && npm run build 2>&1 | grep -E "error TS|Error"
```
Verwacht: geen errors.

- [ ] **Stap 5.5 — Visuele check**

Start de frontend en navigeer naar een DesignSpace. Controleer:
- Als er nog geen snapshots zijn: `PhaseSelector` is niet zichtbaar
- Als er snapshots zijn: dropdown toont "Huidige fase" + genummerde historische fasen
- Klikken op een historische fase: grafiek toont alleen items uit die fase
- Afgewezen items zichtbaar met rode markering
- "Alleen-lezen" badge zichtbaar

- [ ] **Stap 5.6 — Commit**

```bash
git add frontend/src/components/deliberation/PhaseSelector.tsx \
        frontend/src/components/Workspace/ValorWorkspace.tsx
git commit -m "feat(phases): PhaseSelector component en integratie in werkruimte"
```

---

## Task 6: End-to-end verificatie

- [ ] **Stap 6.1 — Voltooi een deliberatiesessie (refine → ranking → consent → finaliseren)**

Controleer in de backend-logs:
- Geen errors bij `copy_asis_to_snapshot`
- Geen errors bij `prune_rejected_from_asis`

- [ ] **Stap 6.2 — Controleer Fuseki via SPARQL**

```bash
curl -X POST http://localhost:3030/valor/sparql \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'query=SELECT+?g+WHERE+{+GRAPH+?g+{+?s+?p+?o+}+}+GROUP+BY+?g' \
  | python -m json.tool | grep phase
```
Verwacht: `urn:valor:ds:{ds_id}/phase/{session_id}` verschijnt.

- [ ] **Stap 6.3 — Controleer asis bevat alleen geaccepteerde items**

```bash
curl -X POST http://localhost:3030/valor/sparql \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=SELECT+?t+WHERE+{+GRAPH+<urn:valor:ds:{ds_id}/asis>+{+?t+a+<{VALOR_NS}Tessera>+}+}" \
  | python -m json.tool
```
Verwacht: alleen geaccepteerde tesserae.

- [ ] **Stap 6.4 — Controleer phase-snapshots endpoint**

```bash
curl http://localhost:8000/designspace/{ds_id}/phase-snapshots \
  -H "Authorization: Bearer {token}" | python -m json.tool
```
Verwacht: array met één snapshot (session_id, created_at, accepted_count, rejected_count).

- [ ] **Stap 6.5 — Controleer historische fase in UI**

- Selecteer de historische fase in de dropdown
- Grafiek toont alle items (ook afgewezen) uit die fase
- Afgewezen items hebben `phase_outcome: "Rejected"` — voeg een visuele indicator toe als die nog ontbreekt (bv. rode rand op nodes in `CLDNode`)

- [ ] **Stap 6.6 — Final commit**

```bash
git add -A
git commit -m "feat(phases): end-to-end fase-snapshots werkend"
```

---

## Aandachtspunten

1. **SPARQL COPY**: Fuseki 4.x ondersteunt `COPY <g1> TO <g2>`. Als `phase/{session_id}` al bestaat, overschrijft `COPY` de inhoud. Dit is correct gedrag.

2. **Pruning van claims bij factor-afwijzing**: `prune_rejected_from_asis` verwijdert ook claims waarvan de bron- of doelfactor is afgewezen. Dit is de juiste semantiek: een causale relatie kan niet bestaan als een van de betrokken factoren wegvalt.

3. **Vaste fase-namen** (`exploration/definition/evaluation/decision`): de `PHASE_SEQUENCE` in `designspace.py` kan verwijderd worden als de gebruiker geen vaste sequentie wil. Dit is een losstaande wijziging (buiten dit plan).

4. **Read-only handhaving**: de UI toont "Alleen-lezen" badge bij een historische fase. Mutatie-endpoints (POST/PATCH/DELETE factors/claims) controleren niet actief of `phase` is meegegeven — dat is acceptabel omdat de frontend geen mutatie-knoppen toont in read-only modus.

5. **Tesserae die nooit gestemd zijn**: factoren/claims die geen enkele ranking of feedback ontvingen tijdens de sessie, worden niet aangeraakt door `prune_rejected_from_asis` — ze blijven in `asis`.

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.auth import get_current_user
from app.db.designspace import (
    create_design_space as db_create_design_space,
    get_design_space_meta,
    get_design_spaces_by_project,
    set_design_space_phase,
    PHASE_SEQUENCE,
)
from app.db.permissions import check_permission
from app.models.domain import (
    DesignSpaceCreate, DesignSpaceResponse, Role,
    DesignAlternativeCreate, DesignAlternativeResponse,
    PhaseTransitionRequest, PhaseTransitionResponse,
    ParticipantAdd, ParticipantResponse,
)
from app.ontology import VALOR_NS
from app.services.fuseki import (
    initialize_design_space_graphs, initialize_alternative_graph,
    sparql_proxy_query, sparql_select, sparql_update,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/designspace", tags=["designspace"])


@router.post("/", response_model=DesignSpaceResponse, status_code=201)
async def create_design_space(
    request: DesignSpaceCreate,
    user: dict = Depends(get_current_user),
) -> DesignSpaceResponse:
    user_id = user["id"]

    if request.project_id:
        if not await check_permission(user_id, request.project_id, Role.MEMBER):
            raise HTTPException(
                status_code=403,
                detail="Onvoldoende rechten voor dit project.",
            )

    ds_id = await db_create_design_space(
        name=request.name,
        description=request.description,
        issue_uri=request.issue_uri,
        owner_id=user_id,
        project_id=request.project_id,
    )

    named_graphs = await initialize_design_space_graphs(ds_id, request.issue_uri)

    logger.info("DesignSpace aangemaakt: %s door gebruiker %s", ds_id, user_id)

    return DesignSpaceResponse(
        id=ds_id,
        name=request.name,
        description=request.description,
        issue_uri=request.issue_uri,
        design_space_uri=f"urn:valor:ds:{ds_id}",
        named_graphs=named_graphs,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/by-project/{project_id}")
async def list_design_spaces_by_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    theme_id: str | None = Query(default=None),
) -> list[dict]:
    """Geeft alle DesignSpaces terug die aan een Project gekoppeld zijn."""
    user_id = user["id"]
    # Check permission op theme als meegegeven (user heeft theme-rol), anders op project
    check_entity = theme_id if theme_id else project_id
    if not await check_permission(user_id, check_entity, Role.VIEWER):
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor dit project.")
    return get_design_spaces_by_project(project_id)


@router.get("/{design_space_id}/can-resolve")
async def can_resolve_thread(
    design_space_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Geeft terug of de huidige gebruiker een thread mag resolveren (MODERATOR-rol vereist)."""
    user_id = user["id"]
    can = await check_permission(user_id, design_space_id, Role.MODERATOR)
    return {"can_resolve": can}


@router.post("/{design_space_id}/alternative/", response_model=DesignAlternativeResponse, status_code=201)
async def create_alternative(
    design_space_id: str,
    request: DesignAlternativeCreate,
    user: dict = Depends(get_current_user),
) -> DesignAlternativeResponse:
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.MEMBER):
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    alt_id = str(uuid.uuid4())
    creator_uri = f"urn:valor:user:{user_id}"
    created_at = datetime.now(timezone.utc).isoformat()

    alt_uri = await initialize_alternative_graph(
        ds_id=design_space_id,
        alt_id=alt_id,
        name=request.name,
        description=request.description or "",
        creator_uri=creator_uri,
        created_at=created_at,
    )

    logger.info("DesignAlternative aangemaakt: %s in DesignSpace %s door %s", alt_uri, design_space_id, user_id)

    return DesignAlternativeResponse(
        alternative_id=alt_id,
        alternative_uri=alt_uri,
        graph_uri=alt_uri,
        design_space_id=design_space_id,
        name=request.name,
        description=request.description,
        status="active",
        created_at=created_at,
    )


@router.get("/{design_space_id}/alternatives", response_model=list[DesignAlternativeResponse])
async def list_alternatives(
    design_space_id: str,
    user: dict = Depends(get_current_user),
) -> list[DesignAlternativeResponse]:
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.VIEWER):
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    base_graph = f"urn:valor:ds:{design_space_id}/base"
    rows = await sparql_select(
        f"""SELECT ?alt ?name ?desc ?status ?createdBy ?createdAt WHERE {{
          GRAPH <{base_graph}> {{
            ?alt a <{VALOR_NS}DesignAlternative> ;
              <{VALOR_NS}inDesignSpace> <urn:valor:ds:{design_space_id}> ;
              <{VALOR_NS}alternativeName> ?name ;
              <{VALOR_NS}alternativeStatus> ?status .
            OPTIONAL {{ ?alt <{VALOR_NS}alternativeDescription> ?desc . }}
            OPTIONAL {{ ?alt <{VALOR_NS}createdBy> ?createdBy . }}
            OPTIONAL {{ ?alt <{VALOR_NS}createdAt> ?createdAt . }}
          }}
        }}""",
        f"{design_space_id}/base",
    )

    result = []
    for row in rows:
        alt_uri = row["alt"]
        alt_id = alt_uri.rsplit("/", 1)[-1]
        status_uri = row.get("status", "")
        status = "archived" if status_uri.endswith("Archived") else "active"
        result.append(DesignAlternativeResponse(
            alternative_id=alt_id,
            alternative_uri=alt_uri,
            graph_uri=alt_uri,
            design_space_id=design_space_id,
            name=row.get("name", ""),
            description=row.get("desc"),
            status=status,
            created_at=row.get("createdAt", ""),
        ))
    return result


@router.get("/{design_space_id}/sparql")
async def sparql_query(
    design_space_id: str,
    query: str = Query(..., description="SPARQL SELECT/CONSTRUCT/ASK/DESCRIBE query"),
    user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.VIEWER):
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten voor deze DesignSpace.",
        )

    result = await sparql_proxy_query(query, design_space_id)

    logger.info("SPARQL proxy: DesignSpace %s bevraagd door gebruiker %s", design_space_id, user_id)

    return JSONResponse(content=result)


@router.post("/{design_space_id}/phase/transition", response_model=PhaseTransitionResponse)
async def phase_transition(
    design_space_id: str,
    request: PhaseTransitionRequest,
    user: dict = Depends(get_current_user),
) -> PhaseTransitionResponse:
    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.MODERATOR):
        raise HTTPException(
            status_code=403,
            detail="Onvoldoende rechten — moderator of hoger vereist voor faseovergang.",
        )

    meta = get_design_space_meta(design_space_id)
    if not meta:
        raise HTTPException(status_code=404, detail="DesignSpace niet gevonden.")

    from_phase = meta["current_phase"]
    project_id = meta["project_id"]

    if request.target_phase:
        if request.target_phase not in PHASE_SEQUENCE:
            raise HTTPException(
                status_code=422,
                detail=f"Ongeldige fase '{request.target_phase}'. Geldige fases: {PHASE_SEQUENCE}.",
            )
        to_phase = request.target_phase
    else:
        current_idx = PHASE_SEQUENCE.index(from_phase) if from_phase in PHASE_SEQUENCE else 0
        if current_idx >= len(PHASE_SEQUENCE) - 1:
            raise HTTPException(
                status_code=422,
                detail=f"DesignSpace is al in de eindstand '{from_phase}'. Geen verdere faseovergang mogelijk.",
            )
        to_phase = PHASE_SEQUENCE[current_idx + 1]

    # -- Actieve alternatieven ophalen uit asis-graph --------------------------
    asis_graph = f"urn:valor:ds:{design_space_id}/asis"
    alt_rows = await sparql_select(
        f"""SELECT DISTINCT ?alt WHERE {{
          GRAPH <{asis_graph}> {{
            ?t <{VALOR_NS}inAlternative> ?alt .
          }}
          FILTER NOT EXISTS {{
            GRAPH <urn:valor:ds:{design_space_id}/base> {{
              ?alt <{VALOR_NS}alternativeStatus> <{VALOR_NS}Archived> .
            }}
          }}
        }}""",
        design_space_id,
    )
    active_alternatives = [r["alt"] for r in alt_rows]

    # -- Gate-check per actief alternatief -------------------------------------
    missing_gates: list[str] = []
    for alt_uri in active_alternatives:
        for gate_type, gate_label in [
            (f"{VALOR_NS}FeasibilityAssessment", "FeasibilityAssessment"),
            (f"{VALOR_NS}ClaimCoverageAssessment", "ClaimCoverageAssessment"),
        ]:
            rows = await sparql_select(
                f"""SELECT ?status WHERE {{
                  GRAPH <{asis_graph}> {{
                    ?t a <{gate_type}> ;
                       <{VALOR_NS}inAlternative> <{alt_uri}> ;
                       <{VALOR_NS}epistemicStatus> ?status .
                  }}
                }}""",
                design_space_id,
            )
            if not rows:
                alt_label = alt_uri.rsplit(":", 1)[-1]
                missing_gates.append(f"{gate_label} ontbreekt voor alternatief '{alt_label}'")

    if missing_gates:
        raise HTTPException(
            status_code=422,
            detail={"message": "Gate-check mislukt.", "missing": missing_gates},
        )

    # -- Alternatieven archiveren bij NotFeasible / NotCovered -----------------
    archived_alternatives: list[str] = []
    base_graph = f"urn:valor:ds:{design_space_id}/base"

    for alt_uri in active_alternatives:
        for gate_type, verdict_status in [
            (f"{VALOR_NS}FeasibilityAssessment", f"{VALOR_NS}NotFeasible"),
            (f"{VALOR_NS}ClaimCoverageAssessment", f"{VALOR_NS}NotCovered"),
        ]:
            rows = await sparql_select(
                f"""SELECT ?t WHERE {{
                  GRAPH <{asis_graph}> {{
                    ?t a <{gate_type}> ;
                       <{VALOR_NS}inAlternative> <{alt_uri}> ;
                       <{VALOR_NS}epistemicStatus> <{verdict_status}> .
                  }}
                }}""",
                design_space_id,
            )
            if rows:
                alt_label = alt_uri.rsplit(":", 1)[-1]
                if alt_label not in archived_alternatives:
                    archived_alternatives.append(alt_label)
                await sparql_update(
                    f"""INSERT DATA {{
                      GRAPH <{base_graph}> {{
                        <{alt_uri}> <{VALOR_NS}alternativeStatus> <{VALOR_NS}Archived> .
                      }}
                    }}""",
                    design_space_id,
                )
                break

    # -- PhaseTransition DecisionEpisode schrijven -----------------------------
    transitioned_at = datetime.now(timezone.utc).isoformat()
    episode_id = str(uuid.uuid4())
    episode_uri = f"urn:valor:episode:{episode_id}"
    decisions_graph = f"urn:valor:ds:{design_space_id}/decisions"
    user_uri = f"urn:valor:user:{user_id}"
    from_phase_uri = f"urn:valor:phase:{from_phase}"
    to_phase_uri = f"urn:valor:phase:{to_phase}"

    await sparql_update(
        f"""INSERT DATA {{
          GRAPH <{decisions_graph}> {{
            <{episode_uri}> a <{VALOR_NS}PhaseTransition> ;
              <{VALOR_NS}fromPhase> <{from_phase_uri}> ;
              <{VALOR_NS}toPhase> <{to_phase_uri}> ;
              <{VALOR_NS}triggeredBy> <{user_uri}> ;
              <{VALOR_NS}triggeredAt> "{transitioned_at}"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
              <{VALOR_NS}inDesignSpace> <urn:valor:ds:{design_space_id}> .
          }}
        }}""",
        design_space_id,
    )

    # -- Neo4j fase bijwerken --------------------------------------------------
    set_design_space_phase(design_space_id, to_phase)

    # -- WebSocket broadcast ---------------------------------------------------
    if project_id:
        from app.services.connection_manager import manager
        await manager.broadcast_data(project_id, {
            "type": "PHASE_TRANSITION",
            "payload": {
                "design_space_id": design_space_id,
                "from_phase": from_phase,
                "to_phase": to_phase,
                "archived_alternatives": archived_alternatives,
                "transitioned_at": transitioned_at,
            },
        })

    logger.info(
        "Faseovergang DesignSpace %s: %s → %s door %s (gearchiveerd: %s)",
        design_space_id, from_phase, to_phase, user_id, archived_alternatives,
    )

    return PhaseTransitionResponse(
        design_space_id=design_space_id,
        from_phase=from_phase,
        to_phase=to_phase,
        archived_alternatives=archived_alternatives,
        decision_episode_uri=episode_uri,
        transitioned_at=transitioned_at,
    )


# ── Participant endpoints ─────────────────────────────────────────────────────

@router.post("/{design_space_id}/participants", response_model=ParticipantResponse, status_code=201)
async def add_participant(
    design_space_id: str,
    request: ParticipantAdd,
    user: dict = Depends(get_current_user),
) -> ParticipantResponse:
    """Voeg een deelnemer toe aan een DesignSpace met een VALOR-O Participant-rol.

    Vereist MEMBER-rechten. Slaat de rol op in Neo4j (HAS_ROLE) en registreert
    een app:Participant triple in de base-graph van de DesignSpace in Fuseki.
    """
    from app.services.ontology_cache import get_participant_role_data
    from app.db.permissions import assign_role

    user_id = user["id"]

    if not await check_permission(user_id, design_space_id, Role.MEMBER):
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    role_data = get_participant_role_data()
    if request.valor_role not in role_data:
        valid = list(role_data.keys()) or ["Initiator", "Facilitator", "Contributor", "Expert", "Observer", "Engineer"]
        raise HTTPException(
            status_code=422,
            detail=f"Ongeldige VALOR-O rol '{request.valor_role}'. Geldige waarden: {valid}",
        )

    rol = role_data[request.valor_role]
    rbac_role_str = rol["rbac_role"]
    rbac_role = Role(rbac_role_str)

    # Neo4j: HAS_ROLE relatie aanmaken
    await assign_role(request.user_id, design_space_id, rbac_role)

    # Fuseki: app:Participant triple in base-graph
    APP_NS = f"{VALOR_NS}application#"
    base_graph = f"urn:valor:ds:{design_space_id}/base"
    participant_uri = f"urn:valor:participant:{design_space_id}:{request.user_id}"
    role_uri = rol["uri"]
    added_at = datetime.now(timezone.utc).isoformat()

    sparql = f"""PREFIX app: <{APP_NS}>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
INSERT DATA {{
  GRAPH <{base_graph}> {{
    <{participant_uri}> a app:Participant ;
      app:hasRole <{role_uri}> ;
      app:participatesIn <urn:valor:ds:{design_space_id}> ;
      app:participantInvitedAt "{added_at}"^^xsd:dateTime ;
      app:participantInvitedBy <urn:valor:user:{user_id}> .
  }}
}}"""
    await sparql_update(sparql, design_space_id)

    logger.info("Participant %s toegevoegd aan DS %s als %s", request.user_id, design_space_id, request.valor_role)

    return ParticipantResponse(
        participant_uri=participant_uri,
        user_id=request.user_id,
        valor_role=request.valor_role,
        rbac_role=rbac_role_str,
        has_voting_right=rol["voting_right"],
        added_at=added_at,
    )


@router.get("/{design_space_id}/participants", response_model=list[ParticipantResponse])
async def list_participants(
    design_space_id: str,
    user: dict = Depends(get_current_user),
) -> list[ParticipantResponse]:
    """Geeft alle deelnemers van een DesignSpace terug."""
    from app.services.ontology_cache import get_participant_role_data

    user_id = user["id"]
    if not await check_permission(user_id, design_space_id, Role.VIEWER):
        raise HTTPException(status_code=403, detail="Onvoldoende rechten voor deze DesignSpace.")

    APP_NS = f"{VALOR_NS}application#"
    base_graph = f"urn:valor:ds:{design_space_id}/base"

    rows = await sparql_select(f"""
        PREFIX app: <{APP_NS}>
        SELECT ?participant ?role ?invitedAt ?invitedBy WHERE {{
          GRAPH <{base_graph}> {{
            ?participant a app:Participant ;
              app:hasRole ?role ;
              app:participatesIn <urn:valor:ds:{design_space_id}> .
            OPTIONAL {{ ?participant app:participantInvitedAt ?invitedAt . }}
            OPTIONAL {{ ?participant app:participantInvitedBy ?invitedBy . }}
          }}
        }}
    """, design_space_id)

    role_data = get_participant_role_data()
    uri_to_label = {d["uri"]: label for label, d in role_data.items()}

    results = []
    for row in rows:
        p_uri = row["participant"]
        role_uri = row["role"]
        valor_role = uri_to_label.get(role_uri, role_uri.split("#")[-1])
        rol = role_data.get(valor_role, {})
        user_part = p_uri.split(":")[-1] if ":" in p_uri else p_uri
        results.append(ParticipantResponse(
            participant_uri=p_uri,
            user_id=user_part,
            valor_role=valor_role,
            rbac_role=rol.get("rbac_role", "viewer"),
            has_voting_right=rol.get("voting_right", False),
            added_at=row.get("invitedAt", ""),
        ))

    return results

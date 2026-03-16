"""VALOR-O Participant-rollen helpers — wrapper om ontology_cache.

Alle roldata (mapsToRBACRole, roleWeight, hasVotingRight) komt uit de
ontologie (00k-application.trig) via ontology_cache. Geen hardcoded lijsten.
"""
from app.services.ontology_cache import (
    get_participant_role_data,
    get_rbac_role_weights,
    has_voting_right,
    rbac_to_valor_role,
)

__all__ = [
    "get_participant_role_data",
    "get_rbac_role_weights",
    "has_voting_right",
    "rbac_to_valor_role",
]

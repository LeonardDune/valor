from app.models.domain import ConversationResponse
from app.models.domain import ConversationResponse, Claim
from app.agent.registry import AgentRegistry
from app.agent.agents import CausalAnalystAgent, DevilsAdvocateAgent
from app.agent.crew import CrewOrchestrator
from app.db.crud import fetch_existing_factors, get_conversation_topic, revoke_claims
import uuid
from datetime import datetime
from typing import List

# Initialize Registry with default agents
# In a real app, this might go in a startup event, but module-level init works for this scope.
if not AgentRegistry.get_all_agents():
    AgentRegistry.register(CausalAnalystAgent())
    AgentRegistry.register(DevilsAdvocateAgent())

async def process_user_message(message: str, conversation_id: str) -> ConversationResponse:
    # 1. Fetch context
    existing_factors = await fetch_existing_factors(conversation_id)
    topic = await get_conversation_topic(conversation_id)
    
    factors_str = ", ".join(existing_factors) if existing_factors else "Geen bestaande factoren."
    topic_str = topic if topic else "Algemeen beleidsonderzoek"
    
    context = (
        f"Thema: {topic_str}. "
        f"Bestaande factoren: {factors_str}. "
        "Taal: Nederlands."
    )

    # 2. Determine Perspective
    # For now, default to CAUSA. Future: derive from input or UI toggle.
    perspective = "CAUSA" 

    # 3. Run Crew
    agent_responses = await CrewOrchestrator.run_for_perspective(perspective, message, context)

    # 4. Aggregate Logic
    primary_reply = ""
    all_claims = []
    all_agent_outputs = []
    
    for resp in agent_responses:
        # Aggregate claims and outputs
        all_claims.extend(resp.extracted_claims)
        all_agent_outputs.extend(resp.agent_outputs)
        
        # Select primary reply (prefer Causal Analyst for continuity)
        if "Causal" in resp.agent_name:
            primary_reply = resp.reply
    
    # Fallback if no Causal Analyst found
    if not primary_reply and agent_responses:
        primary_reply = agent_responses[0].reply

    return ConversationResponse(
        conversation_id=conversation_id,
        reply=primary_reply,
        extracted_claims=all_claims,
        agent_responses=agent_responses,
        agent_outputs=all_agent_outputs
    )

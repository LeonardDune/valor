from typing import List, Dict, Any, Union
from crewai import Crew, Process
from app.agent.registry import AgentRegistry
from app.agent.tasks import create_analysis_task, create_critique_task
from app.models.domain import Claim, AgentResponse
from app.agent.schemas import PerspectiveExtraction, AgentOutput, SuggestionType, ClaimPayload
import json
import asyncio
import uuid
from datetime import datetime

class CrewOrchestrator:
    """
    Orchestrates the dynamic assembly and execution of CrewAI crews 
    based on the requested perspective.
    Acts as the strict Gatekeeper for Agent Contracts.
    """

    @classmethod
    async def run_for_perspective(cls, perspective: str, input_text: str, context: str) -> List[AgentResponse]:
        """
        Assembles a crew for the given perspective and executes it in parallel.
        """
        # 1. Fetch agents
        agents = AgentRegistry.get_agents_by_perspective(perspective)
        
        if not agents:
            return []

        # 2. logical to crewai mapping
        crew_agents = [a.create_crewai_agent() for a in agents]
        
        # 3. Create Tasks
        tasks = []
        
        # Helper to execute a single agent's crew
        async def run_single_agent_crew(valor_agent, crew_agent, task):
            # 1-agent crew
            crew = Crew(
                agents=[crew_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )
            # crew.kickoff() returns CrewOutput (which contains pydantic field)
            output = await asyncio.to_thread(crew.kickoff)
            return (valor_agent, output)

        # Build tasks and prepare coroutines
        coroutines = []
        for valor_agent, crew_agent in zip(agents, crew_agents):
            if "Causal" in valor_agent.name:
                task = create_analysis_task(crew_agent, input_text, context)
            elif "Advocate" in valor_agent.name:
                task = create_critique_task(crew_agent, input_text, context)
            else:
                task = create_analysis_task(crew_agent, input_text, context)
            
            tasks.append(task)
            coroutines.append(run_single_agent_crew(valor_agent, crew_agent, task))

        # Execute all crews in parallel
        results = await asyncio.gather(*coroutines)
        
        # 4. Process and Validate Outputs
        responses = []
        for valor_agent, outputobj in results:
            extracted_claims = []
            agent_outputs = []
            reply_text = str(outputobj.raw)

            # A. Check for Strict Contract Compliance
            if outputobj.pydantic and isinstance(outputobj.pydantic, PerspectiveExtraction):
                structured_data: PerspectiveExtraction = outputobj.pydantic
                reply_text = structured_data.thought_process
                
                for item in structured_data.agent_outputs:
                    # B. Gatekeeper Logic: Metadata Injection & Validation
                    # Ensure perspective matches the requested one (or agent's own)
                    item.perspective = perspective 
                    
                    # Add to strictly typed output list
                    agent_outputs.append(item)
                    
                    # C. Backward Compatibility: Map Suggestions to extracted_claims
                    if item.kind == "suggestion" and item.data.type == SuggestionType.CREATE:
                        cp: ClaimPayload = item.data.claim
                        if cp:
                            new_claim = Claim(
                                id=str(uuid.uuid4()),
                                created_at=datetime.now(),
                                statement=cp.statement,
                                source_node=cp.source_node,
                                target_node=cp.target_node,
                                relationship_type=cp.relationship_type,
                                polarity=cp.polarity,
                                confidence=cp.confidence * 100 # payload is 0-1, domain is 0-100 (legacy quirk)
                            )
                            extracted_claims.append(new_claim)

            # D. Construct Response
            responses.append(AgentResponse(
                agent_name=valor_agent.name,
                perspective=valor_agent.perspective,
                reply=reply_text,
                extracted_claims=extracted_claims,
                agent_outputs=agent_outputs
            ))
            
        return responses

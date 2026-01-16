from typing import List, Dict, Any, Union
from crewai import Crew, Process

from app.agent.registry import AgentRegistry
from app.agent.tasks import create_analysis_task, create_critique_task
from app.models.domain import Claim, AgentResponse 
import json
import asyncio

class CrewOrchestrator:
    """
    Orchestrates the dynamic assembly and execution of CrewAI crews 
    based on the requested perspective.
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
        # We need to map which task factory to use for which agent.
        # For this pilot, we can do a simple name-based mapping or expand the ValorAgent protocol
        tasks = []
        agent_role_map = {} 
        
        # Helper to execute a single agent's crew
        async def run_single_agent_crew(valor_agent, crew_agent, task):
            # 1-agent crew
            crew = Crew(
                agents=[crew_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True
            )
            output = await asyncio.to_thread(crew.kickoff)
            return (valor_agent, str(output))

        # Build tasks and prepare coroutines
        coroutines = []
        for valor_agent, crew_agent in zip(agents, crew_agents):
            agent_role_map[crew_agent.role] = valor_agent
            
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
        
        # Format Response
        responses = []
        for valor_agent, output_content in results:
            extracted_claims = []
            responses.append(AgentResponse(
                agent_name=valor_agent.name,
                perspective=valor_agent.perspective,
                reply=output_content,
                extracted_claims=extracted_claims
            ))
            
        return responses

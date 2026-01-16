from typing import List, Dict
from app.agent.types import ValorAgent

class AgentRegistry:
    """
    Registry for managing available agents in the VALOR system.
    Allows looking up agents by their assigned perspective.
    """
    _agents: List[ValorAgent] = []

    @classmethod
    def register(cls, agent: ValorAgent):
        """Register a new agent with the system."""
        cls._agents.append(agent)

    @classmethod
    def get_agents_by_perspective(cls, perspective: str) -> List[ValorAgent]:
        """
        Retrieve all agents assigned to a specific perspective.
        Also includes agents marked with 'GLOBAL' perspective.
        """
        return [
            agent for agent in cls._agents 
            if agent.perspective == perspective or agent.perspective == "GLOBAL"
        ]

    @classmethod
    def get_all_agents(cls) -> List[ValorAgent]:
        """Retrieve all registered agents."""
        return cls._agents

    @classmethod
    def clear(cls):
        """Clear the registry (useful for testing)."""
        cls._agents = []

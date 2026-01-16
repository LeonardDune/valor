from typing import Protocol, Any, List, Optional
from pydantic import BaseModel
from crewai import Agent

class ValorAgent(Protocol):
    """
    Protocol defining the interface for all agents in the VALOR ecosystem.
    Wraps CrewAI Agent creation with VALOR-specific metadata (Perspective).
    """
    name: str
    role: str
    goal: str
    perspective: str  # e.g., "CAUSA", "AXIA", "GLOBAL"

    def create_crewai_agent(self) -> Agent:
        """Creates and returns the underlying CrewAI Agent instance."""
        ...

# AgentResponse moved to domain.py to avoid circular imports and duplication

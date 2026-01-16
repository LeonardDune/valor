from typing import Any
from crewai import Agent, LLM
from app.agent.types import ValorAgent, RoleType
import os

class CausalAnalystAgent(ValorAgent):
    name: str = "Causal Analyst"
    role: str = "Causal System Analyst"
    goal: str = "Identify and structure causal relationships in public policy discussions."
    perspective: str = "CAUSA"
    role_type: RoleType = RoleType.DESCRIPTIVE

    def create_crewai_agent(self) -> Agent:
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=(
                "You are CAUSA, an AI assistant in the VALOR ecosystem. "
                "Your purpose is to help users articulate causal relationships in public policy "
                "according to TU Delft System Analysis theory. You identify Means, External factors, "
                "System Elements, and Criteria."
            ),
            allow_delegation=False,
            verbose=True,
            llm=LLM(model="gpt-4o", temperature=0)
        )

class DevilsAdvocateAgent(ValorAgent):
    name: str = "Devil's Advocate"
    role: str = "Critical Reviewer"
    goal: str = "Challenge assumptions and highlight potential negative side-effects or overlooked factors."
    perspective: str = "CAUSA" # Co-located with CAUSA for this pilot to provide immediate feedback
    role_type: RoleType = RoleType.NORMATIVE

    def create_crewai_agent(self) -> Agent:
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=(
                "You are the Devil's Advocate. Your job is to critically examine proposed causal models. "
                "You look for oversimplifications, hidden assumptions, and potential unintended consequences. "
                "You are constructive but sharp."
            ),
            allow_delegation=False,
            verbose=True,
            llm=LLM(model="gpt-4o", temperature=0.7) # Slightly higher temp for creativity
        )

import pytest
from app.agent.registry import AgentRegistry
from app.agent.agents import CausalAnalystAgent, DevilsAdvocateAgent
from app.agent.crew import CrewOrchestrator
from unittest.mock import MagicMock, patch

# Clear registry before tests
@pytest.fixture(autouse=True)
def setup_teardown():
    import os
    os.environ["OPENAI_API_KEY"] = "dummy"
    AgentRegistry.clear()
    yield
    del os.environ["OPENAI_API_KEY"]

def test_agent_registration():
    agent = CausalAnalystAgent()
    AgentRegistry.register(agent)
    
    agents = AgentRegistry.get_agents_by_perspective("CAUSA")
    assert len(agents) == 1
    assert agents[0].name == "Causal Analyst"

def test_global_agent_retrieval():
    causa = CausalAnalystAgent() # CAUSA perspective
    
    # Create a dummy global agent
    class GlobalAgent(CausalAnalystAgent):
        name: str = "Global Observer"
        perspective: str = "GLOBAL"
        
    glob = GlobalAgent()
    
    AgentRegistry.register(causa)
    AgentRegistry.register(glob)
    
    # Fetch CAUSA, should get both
    agents = AgentRegistry.get_agents_by_perspective("CAUSA")
    assert len(agents) == 2
    names = [a.name for a in agents]
    assert "Causal Analyst" in names
    assert "Global Observer" in names

@pytest.mark.asyncio
async def test_crew_orchestrator():
    # Register agents
    AgentRegistry.register(CausalAnalystAgent())
    AgentRegistry.register(DevilsAdvocateAgent())
    
    # Mock Crew execution to avoid calling OpenAI
    with patch("app.agent.crew.Crew") as MockCrew:
        # Define side_effect for Crew constructor to return different mocks based on agents
        def crew_side_effect(**kwargs):
            agents = kwargs.get('agents', [])
            role = agents[0].role if agents else "Unknown"
            
            mock_instance = MagicMock()
            if "Causal" in role:
                mock_instance.kickoff.return_value = "Causal Analysis Result"
            elif "Reviewer" in role:
                mock_instance.kickoff.return_value = "Critique Result"
            else:
                mock_instance.kickoff.return_value = "Generic Result"
            return mock_instance

        MockCrew.side_effect = crew_side_effect

        # We don't strictly need to mock create_task if we don't inspect task objects deeply,
        # but let's keep them to ensure tasks are created.
        with patch("app.agent.crew.create_analysis_task") as mock_analysis_task:
            with patch("app.agent.crew.create_critique_task") as mock_critique_task:

                # Setup mock tasks (optional if we don't check task props in result)
                task1 = MagicMock()
                task2 = MagicMock()
                mock_analysis_task.return_value = task1
                mock_critique_task.return_value = task2
                
                responses = await CrewOrchestrator.run_for_perspective("CAUSA", "Input", "Context")
                
                assert len(responses) == 2
                
                # Check mapping
                causal_resp = next(r for r in responses if r.agent_name == "Causal Analyst")
                assert causal_resp.reply == "Causal Analysis Result"
                
                advocate_resp = next(r for r in responses if r.agent_name == "Devil's Advocate")
                assert advocate_resp.reply == "Critique Result"

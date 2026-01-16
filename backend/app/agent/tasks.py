from crewai import Task, Agent
from app.agent.schemas import PerspectiveExtraction

def create_analysis_task(agent: Agent, input_text: str, context: str) -> Task:
    """
    Creates a task for reducing user input into causal claims.
    """
    return Task(
        description=f"""
        Analyze the following user input in the context of: {context}
        
        User Input: "{input_text}"
        
        Identify:
        1. Causal relationships (Source -> Target).
        2. Variable types (Means, External, Element, Criteria).
        3. Polarity (+/-).
        
        CRITICAL: 
        - You must output ONLY the structured JSON object matching the Schema.
        - Do not output Markdown formatting, code blocks, or conversational text.
        - Map your findings to 'Suggestion' (CREATE) items.
        """,
        expected_output="A structured set of causal claims.",
        agent=agent,
        output_pydantic=PerspectiveExtraction
    )

def create_critique_task(agent: Agent, input_text: str, context: str) -> Task:
    """
    Creates a task for critiquing the user input/model.
    """
    return Task(
        description=f"""
        Critique the following user input from a critical perspective. Context: {context}
        
        User Input: "{input_text}"
        
        Look for:
        1. Logical fallacies.
        2. Overlooked external factors.
        3. Potential negative side effects.
        
        CRITICAL:
        - Output ONLY the structured JSON object.
        - Use 'Question' items for clarifying questions.
        - Use 'ConflictSignal' items for contradictions.
        - Use 'Suggestion' (DELETE/UPDATE) if you dispute a specific claim.
        """,
        expected_output="A structured set of critical questions or conflicts.",
        agent=agent,
        output_pydantic=PerspectiveExtraction
    )

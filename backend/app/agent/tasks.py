from crewai import Task
from crewai import Agent

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
        
        Format your response as a clear list of claims and a brief explanation.
        """,
        expected_output="A structured list of identified causal claims and a summary of the reasoning.",
        agent=agent
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
        
        Provide 2-3 sharp, constructive questions or counter-points.
        """,
        expected_output="A set of critical questions or counter-considerations.",
        agent=agent
    )

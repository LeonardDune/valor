from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal
from enum import Enum
from datetime import datetime

# --- Enums ---
class SuggestionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class FactorType(str, Enum):
    MEANS = "middel"
    EXTERNAL = "extern"
    ELEMENT = "systeemelement"
    CRITERIA = "criterium"

# --- Payload Models (The "Content") ---

class ClaimPayload(BaseModel):
    """Represents a potential claim to be created or updated."""
    source_node: str
    target_node: str
    source_type: FactorType
    target_type: FactorType
    relationship_type: str = "CAUSES"
    polarity: str = "+"
    statement: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class RevocationPayload(BaseModel):
    """Represents a suggestion to remove a relationship."""
    source: str
    target: str

class Suggestion(BaseModel):
    """
    Action: Suggest a change to the graph.
    Used for: Adding new claims, modifying existing ones, or deleting them.
    """
    type: SuggestionType
    claim: Optional[ClaimPayload] = None
    revocation: Optional[RevocationPayload] = None
    reasoning: Optional[str] = None

class Question(BaseModel):
    """
    Action: Ask the user a question.
    Used for: Disambiguation, gathering missing info, or challenging assumptions.
    """
    text: str
    options: List[str] = []

class ConflictSignal(BaseModel):
    """
    Action: Format a conflict for the UI.
    Used for: Showing that the user's statement contradicts existing knowledge or themselves.
    """
    source_statement: str
    conflicting_statement: str
    reasoning: str

class Annotation(BaseModel):
    """
    Action: Annotate a specific node in the UI.
    Used for: Adding warnings, notes, or highlighting nodes.
    """
    node_id: str # Ideally the name or ID if known
    text: str
    severity: Literal["info", "warning", "error"] = "info"

# --- The Contract (The "Envelope") ---

class AgentOutput(BaseModel):
    """
    The strictly typed artifact returned by any Agent.
    This is the ONLY thing the Orchestrator accepts.
    """
    kind: Literal["suggestion", "question", "conflict", "annotation"]
    
    # Metadata (injected by Orchestrator or suggested by Agent)
    perspective: str = Field(description="The perspective generating this output (e.g. CAUSA)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Certainty score of this output")
    
    # The actual content
    data: Union[Suggestion, Question, ConflictSignal, Annotation]

class PerspectiveExtraction(BaseModel):
    """
    Wrapper for LLM responses to ensure a list of outputs is returned.
    This is the model passed to Task.output_pydantic.
    """
    agent_outputs: List[AgentOutput]
    thought_process: str = Field(description="Brief reasoning steps before generating outputs.")

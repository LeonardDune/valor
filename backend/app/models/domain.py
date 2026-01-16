from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class ClaimType(str):
    CAUSAL = "causal"
    CORRELATION = "correlation"

from enum import Enum

class FactorType(str, Enum):
    MEANS = "middel"
    EXTERNAL = "extern"
    ELEMENT = "systeemelement"
    CRITERIA = "criterium"

class FactorBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: FactorType = FactorType.ELEMENT

class Factor(FactorBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ClaimBase(BaseModel):
    statement: str
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    source_node: str # Name of the cause factor
    source_id: Optional[str] = None # UUID of the cause factor
    source_type: Optional[FactorType] = None
    target_node: str # Name of the effect factor
    target_id: Optional[str] = None # UUID of the effect factor
    target_type: Optional[FactorType] = None
    relationship_type: str = "CAUSES" # CAUSES, MENTIONS
    polarity: str = "+" # +, -, or ?

class Claim(ClaimBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)

class ChatMessage(BaseModel):
    role: str # user, agent
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    topic: Optional[str] = None

class Revocation(BaseModel):
    source: str = Field(description="The exact name of the source factor")
    target: str = Field(description="The exact name of the target factor")

class SuggestionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class Suggestion(BaseModel):
    type: SuggestionType
    claim: Optional[Claim] = None
    revocation: Optional[Revocation] = None
    reasoning: Optional[str] = None

class Question(BaseModel):
    text: str
    options: List[str] = []

class ConflictSignal(BaseModel):
    source_claim: Claim
    conflicting_claim: Claim
    reasoning: str

class Annotation(BaseModel):
    node_id: str
    text: str

# Union of all output types
# Must use standard typing.Union or specialized Pydantic handling if needed for polymorphism
from typing import Union, Literal
class AgentOutput(BaseModel):
    kind: Literal["suggestion", "question", "conflict", "annotation"]
    data: Union[Suggestion, Question, ConflictSignal, Annotation]

class ConversationResponse(BaseModel):
    conversation_id: str
    reply: str # Keeping for backward compatibility or simple text
    extracted_claims: List[Claim] = [] # Keeping for backward compatibility
    agent_outputs: List[AgentOutput] = []

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    organization_id: str # Required link to Organization
    created_at: datetime = Field(default_factory=datetime.now)

class Theme(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str # The central topic
    description: Optional[str] = None
    project_id: str
    created_at: datetime = Field(default_factory=datetime.now)

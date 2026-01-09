from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class ClaimType(str):
    CAUSAL = "causal"
    CORRELATION = "correlation"

class FactorBase(BaseModel):
    name: str
    description: Optional[str] = None

class Factor(FactorBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ClaimBase(BaseModel):
    statement: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_node: str # Name of the cause factor
    target_node: str # Name of the effect factor
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

class ConversationResponse(BaseModel):
    conversation_id: str
    reply: str
    extracted_claims: List[Claim] = []

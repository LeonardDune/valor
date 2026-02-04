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

class LifecycleStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"

# --- Base Models (Identity) ---
class ThemeBase(BaseModel):
    id: str = Field(description="Unique Identifier of the Theme (Identity)")
    created_at: datetime
    created_by: str = Field(description="User ID of the Creator (Immutable)")

class FactorBase(BaseModel):
    id: str = Field(description="Unique Identifier of the Factor (Identity)")
    created_at: datetime
    created_by: str = Field(description="User ID of the Creator (Immutable)")

class ClaimBase(BaseModel):
    id: str = Field(description="Unique Identifier of the Claim (Identity)")
    created_at: datetime
    created_by: str = Field(description="User ID of the Creator (Immutable)")

# --- Version Models (State) ---

class ThemeVersion(BaseModel):
    id: str
    base_id: str = Field(description="Reference to ThemeBase")
    name: str
    description: str
    status: str = "active" # active, closed
    created_at: datetime
    valid_from: datetime
    valid_to: Optional[datetime] = None

class FactorVersion(BaseModel):
    id: str
    base_id: str = Field(description="Reference to FactorBase")
    name: str
    type: str = "systeemelement"
    description: Optional[str] = None
    version_id: str = Field(description="Belongs to ThemeVersion")
    # Derived from? Optional logic

class ClaimVersion(BaseModel):
    id: str
    base_id: str = Field(description="Reference to ClaimBase")
    statement: str
    polarity: str
    confidence: float
    # Note: connect to FactorVersions in graph
    source_version_id: str
    target_version_id: str

# --- API Data Models (Legacy Compatibility / Frontend View) ---

class Factor(FactorBase): 
    # Use Base ID as 'id' for stable reference
    name: str 
    type: str
    description: Optional[str]
    version_id: str # The ID of the specific version being viewed

class Claim(ClaimBase):
    statement: str
    polarity: str
    confidence: float
    source_id: str # Base ID of source
    target_id: str # Base ID of target
    version_id: str

class Theme(ThemeBase):
    name: str
    description: str
    current_version_id: str

class ChatMessage(BaseModel):
    role: str # user, agent
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    topic: Optional[str] = None

class AgentResponse(BaseModel):
    agent_name: str
    perspective: str
    reply: str
    extracted_claims: List[Claim] = []

class ConversationResponse(BaseModel):
    conversation_id: str
    reply: str
    extracted_claims: List[Claim] = []
    agent_responses: List[AgentResponse] = []

class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class Role(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class InviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: Optional[str] = None
    is_platform_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    organization_id: str # Required link to Organization
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)

# Consolidating into the definitions above (Lines 26-70)
# We remove these duplicates to avoid confusion.
# The 'Theme' and 'ThemeVersion' usage should rely on the classes defined earlier or updated below.

class Decision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)
    author_id: Optional[str] = None

class ConversationThread(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: Optional[str] = None
    theme_version_id: str = Field(..., alias="space_id") # Aliased for backward DB compatibility until migration is complete
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)

class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    author_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    # Target relationships will be handled in Graph relationships, not strictly in Pydantic model structure if dynamic

class Conflict(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    detection_date: datetime = Field(default_factory=datetime.now)
    status: str = "open" # open, resolved, ignored

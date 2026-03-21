from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

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

class ClaimBase(BaseModel):
    id: str = Field(description="Unique Identifier of the Claim (Identity)")
    created_at: datetime
    created_by: str = Field(description="User ID of the Creator (Immutable)")

class Claim(ClaimBase):
    statement: str
    polarity: str
    confidence: float
    evidence_text: Optional[str] = None
    evidence_url: Optional[str] = None
    source_id: str
    target_id: str
    version_id: str
    claim_thread_id: Optional[str] = None
    source_thread_id: Optional[str] = None
    target_thread_id: Optional[str] = None
    status: Optional[str] = None

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
    MODERATOR = "moderator"
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

class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    author_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    # Target relationships will be handled in Graph relationships, not strictly in Pydantic model structure if dynamic

class DesignSpaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    issue_uri: str
    project_id: Optional[str] = None

class DesignSpaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    issue_uri: str
    design_space_uri: str
    named_graphs: Dict[str, str]
    created_at: str


class DesignAlternativeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DesignAlternativeResponse(BaseModel):
    alternative_id: str
    alternative_uri: str
    graph_uri: str
    design_space_id: str
    name: str
    description: Optional[str] = None
    status: str
    created_at: str


class PhaseTransitionRequest(BaseModel):
    target_phase: Optional[str] = None  # None = auto-advance naar volgende fase


class PhaseTransitionResponse(BaseModel):
    design_space_id: str
    from_phase: str
    to_phase: str
    archived_alternatives: List[str]
    decision_episode_uri: str
    transitioned_at: str

class ParticipantAdd(BaseModel):
    user_id: str
    valor_role: str  # "Initiator", "Facilitator", "Contributor", "Expert", "Observer", "Engineer"


class ParticipantResponse(BaseModel):
    participant_uri: str
    user_id: str
    valor_role: str
    rbac_role: str
    has_voting_right: bool
    added_at: str


class ThreadCreate(BaseModel):
    topic: str
    target_id: Optional[str] = None # Optional for legacy version threads, required for generic

class ThreadMessageCreate(BaseModel):
    content: str



class DeliberationStage(str, Enum):
    REFINE = "refine"
    RANKING = "ranking"
    CONSENT = "consent"
    CLOSED = "closed"

class VotingSession(BaseModel):
    id: str
    theme_version_id: str
    status: str = "active"
    stage: DeliberationStage = DeliberationStage.REFINE
    config: Dict[str, Any]
    created_by: str
    created_at: datetime

class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    claim_version_id: str
    user_id: str
    color: str # green, amber, red
    motivation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class RankingCategory(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    BACKLOG = "backlog"
    DISCARD = "discard"

class Ranking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    claim_version_id: str
    user_id: str
    category: RankingCategory
    created_at: datetime = Field(default_factory=datetime.now)

class ConsentVoteType(str, Enum):
    APPROVE = "approve"
    OBJECT = "object"

class ConsentVote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    claim_version_id: str
    user_id: str
    vote: ConsentVoteType
    motivation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

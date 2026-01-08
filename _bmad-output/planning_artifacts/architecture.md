---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: ["prd.md", "product-brief-causa-agent-2026-01-07.md", "research/technical-ai-agent-evaluation-frameworks-research-2026-01-07.md", "research/domain-Domain-Analysis-Scientific-GovTech-Requirements-for-AI-Agent-Evaluation-Frameworks-research-2026-01-07.md", "ux-design/wireframes/causa-main-workspace.excalidraw", "ux-design/wireframes/causa-settings.excalidraw", "ux-design/wireframes/causa-dashboard.excalidraw", "docs/causa_concept.md", "docs/VALOR-concept.md", "docs/onderzoeksopdracht.md", "ux-design-specification.md"]
workflowType: 'architecture'
project_name: 'CAUSA - Causal Systems Analyst'
user_name: 'Renzo'
date: '2026-01-07'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
90 functionele requirements georganiseerd in 15 capability gebieden, met focus op:
- Conversational Reasoning (FR1-FR6): Natural language dialogue, automatic claim extraction
- Multi-User Collaboration (FR7-FR12): Simultaneous participation, real-time updates
- AI Agent Integration (FR13-FR18): Dialogue facilitation, suggestion management
- Causal Model Management (FR19-FR30): Claim-based modeling, relationship visualization
- Uncertainty Handling (FR31-FR36): Confidence tracking, epistemic status management
- VALOR Ecosystem Integration (FR37-FR42): Multi-agent communication, cross-agent insights
- User Management & Access (FR43-FR48): RBAC, multi-tenant workspaces
- Workspace & Session Management (FR49-FR54): Project organization, collaboration controls
- Data Integration & Import (FR55-FR60): External data sources, automated mapping
- Audit & Compliance (FR61-FR66): Government logging, regulatory reporting
- Advanced Visualization (FR67-FR72): Graph rendering, scenario simulations
- Scenario Analysis & Simulation (FR73-FR78): Parameter modification, sensitivity testing
- External Tool Integration (FR79-FR84): API connections, data exchange
- Mobile & Cross-Device Support (FR85-FR90): Responsive interfaces, offline capability

**Non-Functional Requirements:**
Kritische kwaliteitseisen die architectuur vormgeven:
- Performance: <2s AI responses, <500ms model operations, 50+ concurrent users
- Security: MFA, end-to-end encryption, GDPR compliance, FedRAMP requirements
- Scalability: 10,000+ users, auto-scaling, multi-region deployment
- Accessibility: WCAG 2.1 AA compliance, cognitive accessibility
- Integration: 99.9% API uptime, standardized VALOR protocols

**Scale & Complexity:**
- Project complexity: High (conversational AI agents, multi-agent orchestration, scientific/govtech domain)
- Primary domain: Open source gov (government/public services platform)
- Project context: Greenfield - CAUSA as VALOR ecosystem pioneer agent
- Estimated architectural components: 15-20 microservices/modules
- Cross-cutting concerns: Security, compliance, multi-tenancy, real-time collaboration, government accessibility

### Technical Constraints & Dependencies

**Technology Stack (van research):**
- Python backend met FastAPI, Neo4j graph database, LangChain/AutoGen frameworks
- React frontend, Docker containers, Kubernetes orchestration
- Real-time communication via WebSockets
- VALOR multi-agent ecosystem integratie

**Domain Constraints:**
- Scientific/govtech compliance (GDPR, FedRAMP, research ethics)
- Academic validation requirements en peer review workflows
- Multi-stakeholder governance modellen

**Infrastructure Constraints:**
- SaaS deployment naar Vercel (frontend) + Render (backend)
- Docker-first development approach
- Enterprise-grade security en audit requirements

### Cross-Cutting Concerns Identified

**Security & Compliance:**
- End-to-end encryption voor alle data
- Role-based access control over alle componenten
- Audit logging en compliance reporting
- Multi-tenant data isolation

**Real-time Collaboration:**
- Conflict resolution bij simultane edits
- Live cursors en presence indicators
- Version control voor causal models
- Synchronization across distributed users

**AI Agent Orchestration:**
- Consistent agent communication protocols
- Uncertainty quantification handling
- Performance optimization voor AI responses
- Fallback mechanisms bij AI failures

**Scalability & Performance:**
- Auto-scaling voor variable workloads
- Caching strategies voor causal model data
- Database performance optimization
- CDN integration voor global distribution

## Starter Template Evaluation

### Primary Technology Domain

Full-stack SaaS applicatie gebaseerd op project requirements analysis:
- Complex multi-tenant platform met AI agents
- Real-time collaboration features
- Enterprise-grade security en compliance
- Docker-first deployment naar Vercel + Render
- Neo4j graph database integratie

### Starter Options Considered

**Geanalyseerde opties voor full-stack Python/React starters 2026:**

**Optie 1: Full Stack FastAPI Template (GitHub) - AANBEVOLEN**
- FastAPI backend met React frontend
- PostgreSQL database (aanpasbaar naar Neo4j)
- Docker containerization
- Authenticatie en admin panel included
- GitHub Actions CI/CD
- Uitstekend onderhouden door FastAPI creator

**Optie 2: React Vite N Stack Template**
- Moderne frontend stack (Vite, React, TanStack, Shadcn)
- Geen backend included - alleen frontend
- Goede voor pure frontend development
- Maar mist Python backend capabilities

**Optie 3: Custom Setup**
- Volledige controle over architectuur
- Maar meer setup werk vereist
- Risico van inconsistenties

### Selected Starter: GRANDstack (GraphQL, React, Apollo, Neo4j)

**Rationale for Selection:**
GRANDstack is de ideale keuze voor CAUSA vanwege de native Neo4j + GraphQL integratie:

- **Neo4j Native**: Graph database out-of-the-box, perfect voor causal modeling
- **GraphQL API**: Ideaal voor complexe graph queries en real-time updates
- **React Frontend**: Moderne frontend stack voor collaborative UI
- **RDFlib Compatible**: Semantic web capabilities eenvoudig toe te voegen
- **Graph-Centric**: Architectuur die perfect past bij causal reasoning patterns

Hoewel GRANDstack standaard Node.js gebruikt voor GraphQL server, kunnen we dit vervangen door een Python GraphQL server (Strawberry/Ariadne) om FastAPI en AI agents te behouden.

**Architectural Decisions Provided by Starter:**

**Backend Architecture:**
- GraphQL server (Strawberry/Ariadne Python libraries)
- Neo4j database driver voor graph operations
- RDFlib integratie voor semantic processing
- **CrewAI Framework** voor VALOR multi-agent ecosystem orchestration
- **LangChain Integration** voor individuele agent capabilities
- **AI Agent Integration**: CAUSA agent met causal reasoning capabilities
- JWT authenticatie met role-based access
- WebSocket support voor real-time collaboration

**Frontend Architecture:**
- React 18 met TypeScript
- Apollo Client voor GraphQL state management
- Graph visualization components (D3.js/React Flow)
- Real-time subscriptions voor collaborative editing
- Tailwind CSS voor styling

**Database & Storage:**
- Neo4j graph database voor causal model storage
- RDFlib voor semantic processing en RDF data handling
- Redis voor caching en session management
- Custom graph schema migrations

**GraphQL Schema:**
- Auto-generated schema van Neo4j data model
- Custom resolvers voor causal logic en AI agent integratie
- Subscriptions voor real-time causal model updates
- Federated schema voor VALOR multi-agent communication

**Development Experience:**
- Docker Compose voor local development
- pytest voor backend testing, Jest voor frontend
- ESLint + Prettier voor code quality
- Hot reloading voor frontend development

**Deployment & DevOps:**
- Docker containers voor productie
- GraphQL federation gateway
- GitHub Actions CI/CD pipelines
- Neo4j clustering voor enterprise scalability

**Initialization Command:**

```bash
# Clone GRANDstack template
git clone https://github.com/grand-stack/grand-stack-starter.git causa-app
cd causa-app

# Replace Node.js GraphQL server with Python:
# - Install Strawberry/Ariadne GraphQL libraries
# - Configure Neo4j driver with RDFlib integration
# - Add FastAPI routes alongside GraphQL
# - Integrate LangChain/AutoGen for AI agents
# - Setup WebSocket support for real-time features
```

**Note:** GRANDstack geeft ons de beste foundation voor graph-centric applicaties, met Neo4j en GraphQL als eerste klas burgers in de architectuur.

### VALOR Multi-Agent Ecosystem Framework

**Framework Selection voor VALOR Orchestration:**

**Primaire Framework: CrewAI (Core Orchestration)**
- **Waarom CrewAI?** Uitstekend voor team-based agent orchestration met role-based workflows
- **VALOR Fit:** Perfect voor ecosystem waar agents specifieke rollen hebben (AXIA=waarden, ACTOR=stakeholders, etc.)
- **Capabilities:** Multi-agent collaboration, task delegation, hierarchical coordination
- **Performance:** 2.2x sneller dan alternatieven volgens 2026 benchmarks

**Ondersteunende Frameworks (Hybrid Approach):**
- **LangGraph:** Voor state management in complexe agent interactions en lange-running causal analyses
- **LangChain:** Voor individuele agent capabilities, tool integratie, en prompt engineering
- **AutoGen:** Voor peer-to-peer agent communicatie protocols en dynamic agent spawning

**Ecosystem Architecture Patterns:**
- **Federated GraphQL Schema:** Voor cross-agent data sharing
- **Event-Driven Communication:** Voor real-time agent coordination
- **Hierarchical Orchestration:** VALENS als central orchestrator
- **Semantic Interoperability:** RDF-based agent communication

**VALOR Agent Roles & CrewAI Integration:**
- **CAUSA (Causal Analyst):** CrewAI crew leader voor causal reasoning
- **AXIA (Values Agent):** Ethics en value-based decision support
- **ACTOR (Stakeholder Agent):** Multi-perspective analysis
- **THEMIS (Legal Agent):** Compliance en regulatory guidance
- **POLIS (Policy Agent):** Governance en policy impact analysis
- **PRAXIS (Intervention Agent):** Action planning en implementation
- **VALENS (Synthesis Agent):** Final orchestration en consensus building

**Communication Protocols:**
- **GraphQL Federation:** Voor schema stitching across agents
- **WebSocket Events:** Voor real-time agent coordination
- **REST APIs:** Voor external system integration
- **Message Queues:** Voor asynchronous agent coordination

### AI Agent & Tool Integration Strategy

**Framework Roles & Responsibilities:**

**CrewAI (Multi-Agent Orchestration):**
- VALOR ecosystem coordination
- Role-based task delegation
- Hierarchical workflow management
- Agent collaboration patterns

**LangChain/LangGraph (AI Capabilities):**
- Individual agent reasoning
- Tool integration (Neo4j, RDFlib)
- Prompt engineering
- State management voor complexe analyses

**AutoGen (Dynamic Communication):**
- Peer-to-peer agent interactions
- Dynamic agent spawning
- Real-time conversation patterns

**RDF/Neo4j Integration:**
- **RDF Graph (Neo4j):** Domain knowledge storage (ontologies, causal models, instances)
- **RDFlib:** Semantic processing en reasoning voor agents
- **Neo4j Driver:** Direct database access voor causal queries

**Tool Architecture:**
```python
# LangChain tools voor Neo4j + RDFlib
from langchain.tools import tool
from neo4j import GraphDatabase
from rdflib import Graph

@tool
def query_causal_relationships(hypothesis: str) -> str:
    """Query Neo4j voor causal relationships gerelateerd aan hypothesis"""
    driver = GraphDatabase.driver("bolt://localhost:7687")
    with driver.session() as session:
        result = session.run("""
        MATCH (a:Variable)-[r:CAUSES]->(b:Variable)
        WHERE r.hypothesis = $hypothesis
        RETURN a.name, type(r), b.name, r.confidence
        """, hypothesis=hypothesis)
    return format_results(result)

@tool
def semantic_validation(relationship: dict) -> bool:
    """Valideer causal relationship tegen RDF ontology"""
    rdf_graph = Graph()
    rdf_graph.parse("causal_ontology.ttl")
    # Semantic reasoning logic
    return validate_against_ontology(rdf_graph, relationship)

# CrewAI integration
causa_agent = Agent(
    role="Causal Analyst",
    goal="Discover and validate causal relationships",
    tools=[query_causal_relationships, semantic_validation],
    backstory="Expert in causal inference and graph analysis"
)
```

**Data Flow Architecture:**
1. **User Input** → GraphQL API → CrewAI Orchestration
2. **CrewAI** → Task delegation → LangChain Agents
3. **LangChain Agents** → Tool execution → Neo4j/RDFlib
4. **Results** → Semantic processing → GraphQL Response

### Party Mode Collaborative Insights

**Enterprise Architect Perspective:**
- Governance als first-class citizen in agent orchestration
- Regulatory compliance monitoring in elke agent interactie
- Audit trails voor multi-agent decision processes

**AI/ML Engineer Perspective:**
- Hybrid framework: CrewAI core + LangGraph voor state management
- Agent learning en adaptation patterns voor continuous improvement
- Performance optimization voor lange-running causal analyses

**Domain Expert (GovTech) Perspective:**
- Explainable AI requirements voor government transparency
- Semantic interoperability via RDF/OWL voor cross-domain data sharing
- Knowledge graph integration tussen agents

**Startup Founder Perspective:**
- Evolutionary architecture: begin eenvoudig, schaal modulair
- Microservices per agent voor onafhankelijke deployment
- Federated architecture voor future ecosystem expansion

**UX Designer Perspective:**
- Unified user experience across alle agent interactions
- Consistent design language en interaction patterns
- Progressive disclosure van agent capabilities

**Synthese Aanbevelingen:**
- **Semantic Communication Layer:** RDF-based protocols voor agent interoperability
- **Microservices Decomposition:** Per-agent deployment voor scalability en independence
- **Unified Governance:** Enterprise-grade audit en compliance framework
- **Progressive Architecture:** Evolutionary design voor future ecosystem growth

### Party Mode Round 2 - Governance Architecture Insights

**Enterprise Governance Officer:**
- Immutable audit trails voor alle agent outputs (blockchain-based logging)
- Regulatory compliance logging standards (GDPR, FedRAMP)
- Data retention policies voor governance data

**AI Ethics Researcher:**
- Algorithmic humility patterns in agent responses
- Human-AI collaboration guardrails tegen automation bias
- Ethical review workflows voor sensitive analyses

**Collaboration Scientist:**
- Synthesis algorithms voor multi-perspective convergence
- Consensus-building workflows voor hypotheses resolution
- Conflict resolution protocols voor productive disagreement

**Platform Architect:**
- Federated workspace architecture voor cross-organization collaboration
- Secure data sharing protocols tussen workspaces
- Workspace federation patterns voor grensoverschrijdende problemen

**Data Governance Expert:**
- Complete data provenance tracking voor alle claims
- Source attribution metadata voor herkomst verificatie
- Data quality validation pipelines

**Public Sector CIO:**
- Open standards voor data portability en vendor neutrality
- Sovereign data architecture patterns
- Digital sovereignty garanties voor publieke instellingen

**Synthese Aanbevelingen Round 2:**
- **Immutable Audit Layer:** Blockchain/IPFS voor governance compliance
- **Synthesis Engine:** VALENS agent met consensus building capabilities
- **Federation Protocols:** Secure cross-workspace interoperability
- **Provenance Tracking:** Complete data lineage in ontology
- **Ethical Guardrails:** Algorithmic humility en validation workflows

### UX Design Impact Analysis

**Conversational UX as Architectural Driver:**
The updated UX design represents a fundamental shift toward conversational causal reasoning, where users make and discuss causal claims rather than building diagrams. This requires architectural support for:

- **Claim-Centric Architecture:** Causal claims as first-class objects with epistemic status tracking
- **Conversational State Management:** Multi-turn AI-human dialogue with context preservation
- **Progressive Disclosure:** Context-aware revelation of related claims and relationships
- **Epistemic Conflict Resolution:** Social resolution of competing causal interpretations

**Data Model Extensions Required:**
The conversational UX necessitates significant ontology and data model extensions:

**New Node Types for Conversational UX:**
- **Claim** nodes: `:Claim {id, statement, confidence, source, epistemicStatus, conversationThreadId, workspaceId, createdBy, createdAt}`
- **ConversationThread** nodes: `:ConversationThread {id, topic, participants[], claimCount, status, workspaceId, sessionId}`
- **EpistemicStatus** nodes: `:EpistemicStatus {id, claimId, status, confidence, rationale, authorId, timestamp}`

**New Relationship Types:**
- `[:SUPPORTS {strength, evidence[], conversationContext}]` - Evidence-based claim support
- `[:CHALLENGES {rationale, alternativeHypothesis}]` - Constructive disagreement
- `[:CONTEXTUALIZES {relevance, scope}]` - Conversational context linking

**Real-time Collaboration Architecture Enhancement:**
The conversational-first UX requires sophisticated real-time features beyond current capabilities:

**Conversational State Synchronization:**
- **Differential sync** for claim threads (not just model changes)
- **Presence indicators** showing engagement with specific claims
- **Epistemic conflict detection** at the conversational level
- **Progressive disclosure** based on conversational context and user focus

**AI Agent Integration Pattern Evolution:**
The UX positions AI as a collaborative facilitator, requiring enhanced agent patterns:

**Conversational AI Agent Architecture:**
- **Multi-turn dialogue support** with conversation history preservation
- **Epistemic humility indicators** (confidence scores, uncertainty flags)
- **Suggestion lifecycle management** (propose → discuss → validate → accept/reject)
- **Contextual AI responses** based on current conversational state

**Frontend State Management Complexity:**
The conversational UX demands advanced state management:

**New State Management Requirements:**
- **Conversation state tracking** across sessions and workspaces
- **Epistemic status management** for all claims and relationships
- **Progressive disclosure logic** based on user context and claim relevance
- **Multi-user conversational awareness** for real-time collaboration
- **Undo/redo capabilities** at the conversational level

**New Architectural Decisions Required:**

**Conversational Persistence Strategy:**
- **Decision:** Claims as immutable conversation artifacts with epistemic status evolution
- **Rationale:** Supports auditability while enabling epistemic progression through discussion
- **Implementation:** Event-sourced claim lifecycles with conversation threading

**Epistemic Conflict Resolution Architecture:**
- **Decision:** Social resolution with AI facilitation (not transactional locking)
- **Rationale:** Aligns with UX goal of "productive friction" through constructive disagreement
- **Implementation:** Conflict detection algorithms + consensus-building workflows

**Progressive Disclosure Engine:**
- **Decision:** Context-aware claim and relationship revelation based on conversational state
- **Rationale:** Prevents cognitive overload while maintaining causal connections
- **Implementation:** Graph algorithms for conversational relevance and epistemic proximity scoring

**Conversational AI Orchestration:**
- **Decision:** CrewAI agents with LangGraph state management for conversational flows
- **Rationale:** Supports complex multi-turn AI-human collaborative reasoning
- **Implementation:** Conversation-aware agent coordination with context preservation

**Implementation Priorities:**

**High Priority (Blocks UX Implementation):**
- Extend Neo4j ontology for claims and conversation modeling
- Implement conversational real-time synchronization infrastructure
- Add epistemic status tracking and conflict resolution
- Enhance AI agent patterns for conversational participation

**Medium Priority (Enhances UX Experience):**
- Implement progressive disclosure algorithms
- Develop conversational state management frontend architecture
- Add advanced conflict resolution and consensus-building features
- Integrate conversational AI agent capabilities

**Low Priority (Future Conversational Features):**
- Cross-workspace conversation federation
- Advanced epistemic analytics and conversation insights
- Conversation archiving and retrieval optimization
- Multi-language conversational support

**Performance Requirements Update:**
- Conversational state sync: <100ms latency for real-time feel
- Claim thread loading: <200ms for active conversation threads
- Epistemic status updates: real-time across all conversation participants
- Progressive disclosure: <50ms for context-aware claim revelation

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Neo4j versie en deployment model
- Authentication strategy (JWT vs OAuth2)
- GraphQL federation approach
- Multi-tenancy data isolation
- AI agent communication protocols

**Important Decisions (Shape Architecture):**
- Database schema evolution strategy
- Caching architecture voor performance
- Real-time synchronization mechanism
- Error handling en fallback patterns
- Security token management

**Deferred Decisions (Post-MVP):**
- Advanced monitoring en observability
- Multi-region deployment strategy
- Advanced AI agent learning patterns
- Integration met external govtech systems

### Data Architecture

**Neo4j Database Version & Configuration:**
- **Decision:** Neo4j 5.20+ Enterprise Edition
- **Rationale:** Latest LTS versie met advanced graph algorithms, RDF support, en enterprise security features vereist voor causal modeling at scale
- **Version:** 5.20.0 (verified current stable)
- **Deployment:** Neo4j AuraDB Professional voor managed cloud deployment (Vercel/Render compatible)
- **Affects:** Performance, scalability, security compliance
- **Provided by Starter:** Neo4j integration included

**Database Schema Strategy:**
- **Decision:** Labeled Property Graph met RDF extensies
- **Rationale:** Flexibele LPG voor dynamic causal modeling + RDF voor semantic interoperability met VALOR ecosystem
- **Implementation:** Neo4j's RDF toolbox voor ontology integration
- **Migration:** Schema evolution via Neo4j migrations framework
- **Affects:** Data modeling flexibility, agent reasoning capabilities

**Ontology Integration Strategy:**
- **Decision:** CAUSA Causal Modeling Ontology in Neo4j RDF
- **Rationale:** Structureert causal domain knowledge voor semantic interoperability met VALOR agents
- **Implementation:** Neo4j RDF toolbox voor ontology storage en SPARQL querying
- **File:** backend/app/kernel/ontology.ttl (basis ontology voorzet)
- **Affects:** Agent reasoning capabilities, semantic validation, cross-agent communication

**Ontology Extension Requirements:**
- **Project/Session/Workspace Modeling:** Voor scope management en multi-user collaboration
- **Conflict Modeling:** Hypotheses, claims, argumenten met herkomst tracking (mens/agent/bron)
- **AI Agent Governance:** Traceerbare analysediensten met aannames en bronnen
- **Multi-user Dynamics:** Concurrente causal claims en alternatieve waarderingen
- **Extensibility:** Uitbreidbaar naarmate meer VALOR agents worden toegevoegd

**Neo4j Graph Data Model - LPG + RDF Integration:**

**Multi-Agent Collaboration Nodes:**
- **Project** nodes: :Project {id, name, description, domain, stakeholders[], ownerId, privacy, status, createdAt, updatedAt}
- **Session** nodes: :Session {id, projectId, title, description, startTime, endTime, participants[], status, createdBy, createdAt}
- **Workspace** nodes: :Workspace {id, projectId, name, description, ownerId, collaborators[], privacy, createdAt, updatedAt}

**Ontology-Aligned Node Labels & Properties:**
- **AnalyseContext** nodes: :AnalyseContext {id, name, description, domain, stakeholders[], projectId, sessionId, workspaceId, createdBy, createdAt}
- **PubliekeWaarde** nodes: :PubliekeWaarde {id, name, definition, category, workspaceId, createdBy, createdAt}
- **WaardeInterpretatie** nodes: :WaardeInterpretatie {id, criteria, norms, weight, contextId, valueId, workspaceId, createdBy, createdAt}
- **Factor** nodes: :Factor {id, name, description, contextId, workspaceId, sessionId, createdBy, createdAt}
- **Indicator** nodes: :Indicator {id, name, measurementLevel, unit, factorId, workspaceId, createdBy, createdAt}
- **CausaleRelatie** nodes: :CausaleRelatie {id, direction, assumptions[], uncertainty, workspaceId, sessionId, createdBy, createdAt}
- **CausalLoop** nodes: :CausalLoop {id, name, description, pattern, workspaceId, sessionId, createdBy, createdAt}
- **Waardering** nodes: :Waardering {id, normativeClaim, contextId, factorId, interpretationId, workspaceId, createdBy, createdAt}
- **Onderzoeksvraag** nodes: :Onderzoeksvraag {id, question, uncertaintyType, contextId, workspaceId, createdBy, createdAt}
- **Claim** nodes: :Claim {id, statement, confidence, source, workspaceId, sessionId, createdBy, createdAt}

**Ontology-Aligned Relationship Types & Properties:**
- **veroorzaakt** relationships: [:veroorzaakt {direction, assumptions[], uncertainty, createdBy, createdAt}]
- **maaktDeelUitVan** relationships: [:maaktDeelUitVan {position, createdBy, createdAt}]
- **waardeertFactor** relationships: [:waardeertFactor {contribution, evidence[], createdBy, createdAt}]
- **heeftIndicator** relationships: [:heeftIndicator {operationalization, createdBy, createdAt}]
- **onderbouwt** relationships: [:onderbouwt {strength, evidence[], createdBy, createdAt}]
- **bevraagt** relationships: [:bevraagt {relevance, createdBy, createdAt}]
- **heeftContext** relationships: [:heeftContext {role, createdBy, createdAt}]
- **interpreteertWaarde** relationships: [:interpreteertWaarde {operationalization, createdBy, createdAt}]

**RDF Mapping Patterns:**
- LPG nodes → RDF subjects met URI patterns: valor:node/{label}/{id}
- LPG properties → RDF data properties: valor:hasName, valor:hasConfidence
- LPG relationships → RDF object properties: valor:causes, valor:supports
- Ontology classes → LPG node labels
- Ontology properties → LPG relationship types + RDF properties

**Graph Schema Constraints:**
```cypher
// Node key constraints
CREATE CONSTRAINT variable_id IF NOT EXISTS FOR (v:Variable) REQUIRE v.id IS NODE KEY
CREATE CONSTRAINT hypothesis_id IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.id IS NODE KEY

// Relationship uniqueness (bidirectional CAUSES relationships niet toegestaan)
CREATE CONSTRAINT unique_causes IF NOT EXISTS FOR ()-[r:CAUSES]-() 
REQUIRE r.id IS UNIQUE

// Property existence constraints
CREATE CONSTRAINT variable_required IF NOT EXISTS FOR (v:Variable) 
REQUIRE v.id IS NOT NULL AND v.name IS NOT NULL
```

**Indexing Strategy:**
- **Node indexes:** :Variable(name), :Hypothesis(workspaceId), :Workspace(ownerId)
- **Relationship indexes:** :CAUSES[confidence], :SUPPORTS[createdAt]
- **Full-text indexes:** Voor textual search op descriptions en claims
- **Point indexes:** Voor geospatial data (indien gebruikt)

**Query Patterns & Best Practices:**
```cypher
// Causal path finding
MATCH path = (start:Variable)-[:CAUSES*1..5]->(end:Variable)
WHERE start.id = $startId AND end.id = $endId
RETURN path, reduce(conf = 1.0, r IN relationships(path) | conf * r.confidence) AS pathConfidence
ORDER BY pathConfidence DESC

// Evidence-based claim validation
MATCH (c:Claim)-[:SUPPORTS]->(e:Evidence)
WHERE c.confidence < 0.5
RETURN c, collect(e) AS supportingEvidence
ORDER BY size(supportingEvidence) DESC

// Multi-user conflict detection
MATCH (h1:Hypothesis)-[:CAUSES]->(v:Variable)<-[:CAUSES]-(h2:Hypothesis)
WHERE h1 <> h2 AND h1.workspaceId = h2.workspaceId
RETURN h1, h2, v, 
  CASE WHEN h1.confidence > h2.confidence THEN 'h1_dominates' 
       WHEN h2.confidence > h1.confidence THEN 'h2_dominates'
       ELSE 'conflict' END AS conflictStatus
```

**RDF/SPARQL Integration:**
- **SPARQL endpoints:** Voor semantic queries over RDF data
- **Hybrid queries:** Cypher + SPARQL voor complex reasoning
- **Ontology reasoning:** RDF inference voor implicit relationships
- **Semantic validation:** RDF Schema validation tegen VALOR ontology

**AI Agent Architecture Pattern:**
- **Decision:** Agents als specialised analysediensten (niet autonoom)
- **Rationale:** Governance, verantwoording en menselijke validatie als kernfunctionaliteit
- **Implementation:** FastAPI endpoints per agent met project/session context
- **Input:** project-id, session-id, expliciete scope
- **Output:** Voorstellen (geen besluiten) met traceerbare metadata
- **Affects:** Agent orchestration, human-AI collaboration, accountability

**Caching Strategy:**
- **Decision:** Redis Cluster voor multi-layer caching
- **Rationale:** Sub-millisecond response times vereist voor real-time collaboration (<500ms NFR)
- **Layers:** Application cache (query results), GraphQL cache (resolver responses), Session cache (user state)
- **Implementation:** Redis 7.2+ met clustering voor high availability
- **Affects:** Performance optimization, scalability

### Authentication & Security

**Authentication Strategy:**
- **Decision:** JWT + OAuth2 hybrid approach
- **Rationale:** JWT voor stateless API authentication + OAuth2 voor third-party integrations en enterprise SSO
- **Implementation:** FastAPI Users + Authlib voor OAuth2 flows
- **MFA:** WebAuthn/FIDO2 voor sterke authenticatie (FedRAMP compliance)
- **Affects:** User access, API security, enterprise integration

**Authorization Pattern:**
- **Decision:** Role-Based Access Control (RBAC) + Attribute-Based Access Control (ABAC)
- **Rationale:** RBAC voor basic roles (Admin, Analyst, Viewer) + ABAC voor fine-grained permissions gebaseerd op project/workspace attributes
- **Implementation:** Casbin policy engine voor ABAC rules
- **Multi-tenancy:** Organization-level isolation met row-level security
- **Affects:** Data security, collaboration controls, governance compliance

**Data Encryption Strategy:**
- **Decision:** End-to-end encryption met envelope encryption
- **Rationale:** GDPR compliance + FedRAMP requirements voor sensitive causal data
- **Implementation:** AES-256 envelope encryption + RSA key management
- **At Rest:** Encrypted Neo4j database files
- **In Transit:** TLS 1.3 voor alle communications
- **Affects:** Data protection, regulatory compliance, performance overhead

**Security Token Management:**
- **Decision:** Decentralized token management met refresh rotation
- **Rationale:** Prevents token replay attacks + enables secure session management
- **Implementation:** JWT refresh tokens met configurable expiration
- **Revocation:** Redis-backed token blacklist voor immediate revocation
- **Affects:** Session security, user experience, compliance requirements

### API & Communication Patterns

**GraphQL Federation Strategy:**
- **Decision:** Apollo Federation 2.0 voor VALOR multi-agent schema stitching
- **Rationale:** Enables distributed agent services met unified GraphQL API voor cross-agent queries
- **Implementation:** Apollo Gateway als central orchestration point
- **Entities:** Projects, Sessions, Workspaces als federated entities
- **Affects:** Agent interoperability, API consistency, development complexity

**Real-time Communication Protocol:**
- **Decision:** GraphQL Subscriptions + WebSocket multiplexing
- **Rationale:** Real-time causal model updates + agent notifications vereist voor collaboration (<500ms NFR)
- **Implementation:** Apollo Server subscriptions met WebSocket transport
- **Channels:** Model updates, agent suggestions, conflict notifications, presence indicators
- **Affects:** User experience, collaboration features, performance requirements

**API Error Handling Strategy:**
- **Decision:** Structured error responses met error codes en context
- **Rationale:** Complex causal analyses hebben detailed error information nodig voor debugging en user guidance
- **Implementation:** GraphQL error extensions + custom error types (ValidationError, ConflictError, AgentError)
- **Localization:** Multi-language error messages voor international users
- **Affects:** Developer experience, user experience, debugging capabilities

**Rate Limiting & Throttling:**
- **Decision:** Multi-tier rate limiting met Redis-backed counters
- **Rationale:** Protects AI agent resources + voorkomt abuse in collaborative environment
- **Tiers:** Free tier (10 req/min), Professional (100 req/min), Enterprise (unlimited)
- **Implementation:** FastAPI rate limiter met Redis voor distributed counting
- **Affects:** Resource protection, cost control, service availability

**API Documentation Strategy:**
- **Decision:** Interactive GraphQL playground + OpenAPI 3.0 spec generation
- **Rationale:** Complex VALOR ecosystem vereist excellent documentation voor agent integratie
- **Implementation:** GraphQL Voyager voor schema visualization + ReDoc voor REST endpoints
- **Automation:** CI/CD pipeline generates up-to-date documentation
- **Affects:** Developer onboarding, agent integration, API governance

### Infrastructure & Deployment

**Hosting Strategy:**
- **Decision:** Vercel (frontend) + Render (backend) SaaS deployment
- **Rationale:** Optimal voor full-stack Python/React apps met global CDN en managed services
- **Frontend:** Vercel voor React deployment met edge functions
- **Backend:** Render voor Python/FastAPI met managed databases
- **Affects:** Performance, cost, scalability, developer experience

**CI/CD Pipeline Strategy:**
- **Decision:** GitHub Actions monorepo pipeline met environment-based deployments
- **Rationale:** Unified workflow voor frontend/backend met security scanning en automated testing
- **Stages:** Build → Test → Security Scan → Deploy (dev/staging/prod)
- **Triggers:** PR validation, main branch deployment, scheduled security scans
- **Affects:** Development velocity, code quality, deployment reliability

**Environment Configuration:**
- **Decision:** Environment-specific config met secret management
- **Rationale:** Secure handling van API keys, database credentials, en environment variables
- **Implementation:** Python-dotenv voor local + cloud provider secret managers
- **Multi-tenancy:** Environment-level tenant isolation
- **Affects:** Security, operational flexibility, compliance

**Monitoring & Observability:**
- **Decision:** Comprehensive monitoring stack met business metrics
- **Rationale:** Enterprise-grade observability vereist voor 99.9% uptime en governance compliance
- **Stack:** Prometheus metrics + Grafana dashboards + ELK logging + Sentry error tracking
- **Metrics:** API performance, AI agent response times, causal model operations, user engagement
- **Affects:** Operational excellence, issue resolution, governance reporting

**Scaling Strategy:**
- **Decision:** Horizontal pod autoscaling met database connection pooling
- **Rationale:** Handles variable AI agent workloads en collaborative usage patterns
- **Implementation:** Kubernetes HPA voor backend + Vercel edge scaling voor frontend
- **Limits:** Configurable per tenant (Free/Professional/Enterprise tiers)
- **Affects:** Cost optimization, user experience, resource efficiency

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
15+ areas waar AI agents verschillende keuzes kunnen maken, wat zou leiden tot inconsistenties in de VALOR codebase

### Naming Patterns

**Database Naming Conventions:**
- Tables: snake_case (users, causal_relationships, workspaces)
- Columns: snake_case met expliciete namen (user_id, confidence_score, created_at)
- Foreign Keys: fk_[referenced_table]_[referencing_table] (fk_user_workspace)
- Indexes: idx_[table]_[column] (idx_users_email)
- Constraints: ck_[table]_[rule] (ck_causal_confidence_range)

**API Naming Conventions:**
- Endpoints: RESTful plural nouns (/api/workspaces, /api/projects/{id}/sessions)
- Route parameters: snake_case ({workspace_id}, {project_id})
- Query parameters: snake_case (?limit=10&offset=0)
- Headers: Kebab-Case (X-Request-Id, X-User-Context)

**Code Naming Conventions:**
- Components: PascalCase (UserDashboard, CausalModelCanvas)
- Files: kebab-case (user-dashboard.tsx, causal-model-canvas.tsx)
- Functions: camelCase (getUserData, validateCausalRelationship)
- Variables: camelCase (userId, confidenceScore)
- Constants: SCREAMING_SNAKE_CASE (MAX_CONFIDENCE=1.0)

### Structure Patterns

**Project Organization:**
- Feature-based structure: /features/[feature]/components|services|types
- Shared utilities: /shared/[domain]/[utility]
- Tests: co-located met implementation (__tests__/component.test.tsx)
- Configuration: /config/[environment].json

**Backend Structure:**
- FastAPI routers: /api/v1/[domain]/routes.py
- Services: /services/[domain]/[service].py
- Models: /models/[domain]/[model].py
- Agents: /agents/[agent_name]/[agent].py

**Frontend Structure:**
- Pages: /pages/[route].tsx (Next.js App Router)
- Components: /components/[domain]/[component].tsx
- Hooks: /hooks/[domain]/[hook].ts
- Stores: /stores/[domain]/[store].ts

### Format Patterns

**API Response Formats:**
- Success: {"data": {...}, "meta": {"total": 10, "page": 1}}
- Error: {"error": {"code": "VALIDATION_ERROR", "message": "Invalid causal relationship", "details": {...}}}
- Pagination: {"data": [...], "meta": {"page": 1, "limit": 10, "total": 50, "hasMore": true}}
- Dates: ISO 8601 strings ("2024-01-07T14:30:00Z")

**GraphQL Schema Patterns:**
- Types: PascalCase (CausalRelationship, UserWorkspace)
- Fields: camelCase (confidenceScore, createdAt)
- Enums: SCREAMING_SNAKE_CASE (RELATIONSHIP_TYPE_CAUSES)
- Unions: ...Type (AgentResponse, ValidationResult)

**Data Exchange Formats:**
- JSON: camelCase keys voor API, snake_case voor database
- RDF: Turtle format voor ontology serialisatie
- CSV: headers in Title Case voor exports

### Communication Patterns

**Event System Patterns:**
- Event names: [domain].[action].[subject] (workspace.user.joined, causal.relationship.created)
- Payload structure: {"eventId": "uuid", "timestamp": "iso8601", "actor": {...}, "data": {...}}
- Event versioning: v1, v2 in event name (workspace.user.joined.v2)
- Error events: [domain].error.[subject] (causal.error.validation_failed)

**State Management Patterns:**
- Actions: [domain]/[action] (workspace/join, causal/relationship/create)
- State structure: normalized {entities: {}, ids: []}
- Selectors: camelCase (getWorkspaceUsers, getCausalRelationships)
- Async actions: [action]Async (createWorkspaceAsync)

**GraphQL Patterns:**
- Queries: PascalCase (GetWorkspace, ListCausalRelationships)
- Mutations: PascalCase (CreateWorkspace, UpdateCausalRelationship)
- Subscriptions: PascalCase (WorkspaceUpdated, CausalModelChanged)
- Fragments: PascalCase (WorkspaceFields, CausalRelationshipFields)

### Process Patterns

**Error Handling Patterns:**
- Validation errors: onmiddellijke feedback met specifieke veld-errors
- System errors: user-friendly berichten met support contact
- Network errors: retry logic met exponential backoff
- Agent errors: traceerbare outputs met fallback suggesties

**Loading State Patterns:**
- Global loading: page-level spinners voor navigation
- Local loading: component-level indicators voor actions
- Progressive loading: skeleton screens voor data tabelen
- Background sync: toast notifications voor async updates

**Validation Patterns:**
- Client-side: immediate feedback tijdens input
- Server-side: comprehensive validation met detailed errors
- Agent validation: semantic checking tegen ontology
- Cross-field validation: relationship dependencies

**Authentication Flow Patterns:**
- Login: OAuth2 flow met PKCE voor security
- Session refresh: automatic JWT refresh 5 min voor expiry
- Logout: complete session cleanup + token revocation
- MFA: WebAuthn challenge-response flow

### Enforcement Guidelines

**All AI Agents MUST:**

1. **Follow established naming conventions** - geen afwijkingen toegestaan
2. **Use defined project structure** - nieuwe code past in bestaande patterns
3. **Implement consistent API patterns** - responses volgen gedefinieerde formaten
4. **Handle errors volgens patterns** - geen custom error handling
5. **Document pattern violations** - rapporteren als inconsistenties gevonden

**Pattern Enforcement:**

- **Code Reviews:** Automatische checks voor naming conventions
- **Linting Rules:** ESLint + Prettier configuraties voor format enforcement
- **API Testing:** Contract tests voor response format compliance
- **Documentation:** Pattern violations worden gedocumenteerd en opgelost

### Pattern Examples

**Good Examples:**

```typescript
// Correct component naming
export function UserDashboard() { ... }

// Correct API response format
{
  "data": { "id": 123, "name": "Workspace" },
  "meta": { "createdAt": "2024-01-07T10:00:00Z" }
}

// Correct event naming
workspace.user.joined { userId: 123, workspaceId: 456 }
```

**Anti-Patterns:**

```typescript
// Wrong: inconsistent naming
export function userDashboard() { ... }

// Wrong: custom error format
{ "success": false, "msg": "Error occurred" }

// Wrong: inconsistent event structure
{ "event": "user_joined", "payload": { "user": 123 } }
```

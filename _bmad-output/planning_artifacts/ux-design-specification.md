---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: ["_bmad-output/planning_artifacts/product-brief-causa-agent-2026-01-07.md", "_bmad-output/planning_artifacts/prd.md", "docs/causa_concept.md", "docs/onderzoeksopdracht.md", "docs/VALOR-concept.md"]
---

# UX Design Specification valor

**Author:** Renzo
**Date:** 2026-01-08

---

## Executive Summary

### Project Vision

CAUSA is een gespecialiseerde AI-agent binnen een onderzoeksprogramma naar AI-ondersteunde Value-Based Ecosystems Design (VBED) voor publieke dienstverlening. Als open source pilot draagt CAUSA bij aan de verbetering van gezamenlijk causaal begrip in complexe maatschappelijke vraagstukken, met als doel de kwaliteit, snelheid en samenhang van ecosysteemontwerpen in de publieke sector te verbeteren.

Het kernprobleem dat CAUSA adresseert is het structureel tekortschieten in gezamenlijk causaal begrip bij complexe maatschappelijke dossiers, waar causale redeneringen impliciet, fragmentarisch en persoonsgebonden blijven. Dit leidt tot suboptimale interventies die symptoombestrijdend zijn of elkaar onbedoeld tegenwerken.

CAUSA faciliteert realtime collaborative causal modeling via een Neo4j-based workspace, waar teams simultaan werken aan gedeelde causale modellen. De agent versterkt het menselijke denkproces door patroonherkenning, vraagstelling en structurele ondersteuning, terwijl alle mutaties door mensen worden gevalideerd. Onzekerheid wordt first-class behandeld via expliciete claims met polariteit, zekerheid en status.

### Target Users

CAUSA targets professionals in the middle ground between policy, execution, and accountability: policy employees, chain coordinators, executive professionals, and process facilitators. These users see the system but lack instruments to make causal understanding shared, explicit, and transferable. The primary users include:

- **Policy Analysts** like Lisa van der Berg who struggle with fragmented data across Excel sheets and stakeholder meetings
- **Chain Coordinators** like Marcus de Vries who fight "organizational egos" blocking collaboration
- **Academic Researchers** like Dr. Fatima Al-Rashid bridging theory and practice gaps
- **Data Analysts** like Jan-Peter Visser whose reports lack causal context

### Key Design Challenges

**Complex Domain Expertise**: Users work with intricate causal relationships in societal systems, requiring interfaces that support both technical precision and collaborative exploration.

**Uncertainty as First-Class Citizen**: Unlike typical software where data is certain, CAUSA must handle probabilistic causal claims with explicit metadata tracking (author, certainty, polarity, status).

**Realtime Multi-User Collaboration**: Supporting simultaneous editing of complex graph structures while maintaining data integrity and user awareness.

**AI-Human Balance**: Facilitating AI assistance for pattern recognition and suggestions while ensuring human validation and control over all model mutations.

**Cross-Stakeholder Communication**: Bridging different organizational cultures, terminologies, and perspectives in government/public sector contexts.

### Design Opportunities

**Visual Causal Exploration**: Opportunity to create intuitive graph-based interfaces that make complex systemic relationships accessible to non-technical users.

**Collaborative Sensemaking**: Design for collective intelligence where diverse perspectives converge through shared causal understanding.

**Uncertainty Visualization**: Innovative ways to represent and interact with probabilistic information, making uncertainty productive rather than paralyzing.

**Progressive Disclosure**: Layered interfaces that support both quick assessments and deep causal analysis.

**Contextual AI Assistance**: Embedding AI suggestions within collaborative workflows that enhance rather than replace human expertise.

## Core User Experience

### Party Mode Discussion Insights

**🎉 PARTY MODE ACTIVATED - Multi-Agent UX Discussion**

The core experience definition was stress-tested through a collaborative party mode discussion with BMAD agents bringing diverse perspectives. This revealed critical refinements and validated the social process approach.

**Agent Perspectives & Key Questions:**

**Sally (UX Designer):** "How do we ensure users don't get overwhelmed by causal complexity? Should we consider progressive disclosure or guided workflows?"

**Mary (Business Analyst):** "What evidence validates that users want collaborative causal reasoning? Have we tested this core assumption?"

**Winston (Architect):** "What are the data consistency challenges for realtime multi-user causal modeling? How do we handle conflict resolution?"

**John (Product Manager):** "WHY would government analysts adopt this? What's the compelling job they're trying to get done that existing tools don't serve?"

**Maya (Design Thinking Coach):** "How do we create empathy for users transitioning from individual to collective work?"

**Emerging Insights from Discussion:**

**Sally:** "Progressive disclosure should be semantic, not UI-driven. Start with one causal claim, reveal related claims only when they reinforce, contradict, or complete a loop."

**Mary:** "Users don't articulate wanting 'causal models' - they express pain points: 'We keep talking past each other,' 'Every team has its own picture.' CAUSA satisfies unmet coordination needs."

**Winston:** "Data consistency doesn't require strong real-time synchronization. Causal claims are append-only assertions. Preserve conflicts at semantic layer, resolve socially, not transactionally."

**John:** "Adoption is driven by accountability, not novelty. Users need to justify interventions, explain decisions, survive scrutiny. CAUSA provides defensive infrastructure for public governance."

**Maya:** "Transition happens through preserved plurality. Remove ownership from conclusions, attach authorship to claims. Make uncertainty socially acceptable."

**Unifying Strategic Insight:** CAUSA works because it treats causal reasoning as a social process, not representational. Complexity managed by conversational focus. Demand validated by unmet coordination needs. Consistency semantic, not transactional. Adoption driven by accountability. Empathy emerges from preserved plurality.

### Defining Experience

CAUSA is a **collaborative reasoning environment** where groups articulate, challenge, and stabilize causal understanding—without ever having to model explicitly. The platform exists to hold shared thinking, not to produce diagrams. This positioning emerged directly from the party mode discussion, distinguishing CAUSA from tools that require diagram literacy.

**Core User Action:** Making and discussing causal claims explicit ("Factor A influences Factor B in this way, for this reason" including polarity, direction, uncertainty, and context). Party mode validated this as the atomic unit transforming implicit mental models into shareable knowledge objects.

**Critical User Action:** Confirming, nuancing, or rejecting a causal suggestion (human or AI) - the pivot point from implicit to explicit, individual to collective. Discussion revealed this as where trust is built or broken, requiring lightweight, safe, socially neutral interactions.

**Design Implication:** Every screen, every interaction, every workflow must serve these two actions. Party mode confirmed that secondary features must never interfere with this core dialogical flow.

### Platform Strategy

**Web-first, desktop-optimized, tablet-capable** platform designed for VBED work contexts (workshops, policy design sessions, multi-stakeholder meetings, desk-based analysis). Party mode discussion emphasized professional settings where precision and collaboration matter more than mobile convenience.

**Primary Input:** Mouse + keyboard for precision interactions required in causal reasoning; touch as enhancement for tablets in facilitated workshops where physical interaction adds value.

**Government Constraints:** Browser-based with zero local installs, works on locked-down laptops, no admin rights required, compatible with modern Chromium-based browsers, designed for on-prem or sovereign cloud deployment, includes fine-grained role-based access control. Party mode validated these as mandatory, not optional.

**Device Affordances:**
- **Desktop:** Multi-monitor support for causal map on one screen and discussion/agent prompts on another; keyboard shortcuts for confirm/challenge/annotate; hover-based previews of rationale chains
- **Tablet:** Pinch-zoom for exploring causal loops, tap to surface rationale panels, natural for facilitated sessions but never the primary modeling surface

**Offline Strategy:** Explicitly not required for core experience - collaborative modeling is inherently synchronous and dialogical.

**Technical Insight from Winston:** Data consistency handled through semantic preservation of conflicts rather than transactional resolution. Multiple users can assert claims concurrently; "resolution" happens socially.

**Design Implication:** Platform choices must prioritize professional work contexts over consumer convenience. Party mode confirmed that every technical decision should enable rather than constrain the core collaborative reasoning experience.

### Effortless Interactions

**Natural Reactions:** Responding to causal statements should feel conversational ("Yes, that makes sense," "Only under these conditions," "I'm not convinced") and translate directly into claim status updates, confidence scores, and alternative branches. No forms, no property panels, no modeling jargon. The system should read social cues and emotional context as fluently as technical content.

**Automatic Translation:** Dialogue automatically becomes structured causal claims, with loops and feedback structures detected in real-time, disagreement tracked socially, and history maintained invisibly. Users should never encounter "save" buttons, sync indicators, or structural warnings. The platform handles all complexity so users can focus purely on meaning-making.

**Delightful AI Moments:** When CAUSA asks the right question at the right moment (e.g., "You've identified three reinforcing effects here. Are they all equally strong?" or "This loop contradicts an earlier assumption. Is that intentional?") - creating the feeling of a skilled facilitator who understands the domain deeply, not a generic AI tool.

**Eliminated Steps:** Compared to competitors, CAUSA eliminates manual node/edge creation, explicit diagram layout decisions, separate "discussion" and "modeling" modes, and any export/import workflows. If users ever say "Now let's put this into the model," the design has failed.

**Party Mode Refinement:** Progressive disclosure is semantic/conversational, not UI-driven. Complexity managed by focusing on current conversational context and immediate causal neighborhood.

**Design Implication:** Success is measured by how invisible the technology becomes. The best CAUSA experience feels like an extension of natural human conversation, not interaction with a tool.

### Critical Success Moments

**"This is Better" Moment:** When a disagreement becomes visible without becoming personal - parallel explicit causal claims are preserved and visible without forcing premature consensus. Party mode revealed this surpasses whiteboards and Miro by making disagreement productive.

**Feeling Successful:** When the group leaves with genuine shared clarity about agreements, disagreements, and unknowns—all persisted, inspectable tomorrow, and understandable by someone who wasn't in the room. Party mode emphasized collective, durable success over individual ephemera.

**Make-or-Break Interaction:** Human validation of causal claims must feel lightweight, safe, reversible, and socially neutral. Party mode identified this as where trust is built or destroyed.

**Critical Flows:**
- **First Causal Claim Flow:** Dialogue → structured claim with metadata. If this works, users lean in.
- **First Disagreement Flow:** Parallel claims held without forced resolution → group sees disagreement structure. If this works, users trust the system.
- **Return-After-Time Flow:** Immediate grasp of causal structure and contested areas. If this works, CAUSA becomes institutional infrastructure.

**First-Time Success:** Users start talking naturally and the system responds meaningfully—"I didn't realize we were already building a model." Party mode confirmed onboarding should be contextual, invisible, progressive.

**Design Implication:** These moments aren't features—they're the reason CAUSA exists. Party mode validated that every design decision should enable these moments or get out of their way.

### Experience Principles

1. **Conversational Causality:** Causal reasoning emerges from dialogue, not diagrams. All core actions map to conversational moves.

2. **Collective Sensemaking:** Every interaction contributes to shared understanding, not personal artifacts. No private models or "my version" as default.

3. **Uncertainty as Asset:** Disagreement is a first-class object, not a failure state. Claims have explicit status, confidence levels, and plurality.

4. **Automatic Structure:** Users never manage structure; structure emerges from use. No manual node creation, no layout work, no explicit "modeling mode."

5. **Web-Native Collaboration:** Behaves like shared infrastructure, not a specialized tool. Zero install, multi-user default, audit-ready, public-sector compliant.

**North Star:** CAUSA succeeds when groups can think causally together, explicitly and safely, without ever feeling like they are modeling.

**Party Mode Outcome:** The discussion fundamentally strengthened CAUSA's positioning from "better modeling tool" to "collaborative reasoning environment." All five agent perspectives converged on treating causal reasoning as social process rather than representation.

## Desired Emotional Response

### Primary Emotional Goals

**Collective Capability** is CAUSA's dominant emotion - the profound feeling that "wij zien dit samen scherper dan ieder van ons afzonderlijk" (we see this together more sharply than any of us individually). CAUSA must feel like a space that carries complexity so people don't have to control it themselves.

**Four Key Emotions CAUSA Must Actively Evoke:**

1. **Safety to be Incomplete** - Users feel "I may say something that isn't finished yet" without status loss. Uncertainty becomes legitimate, not masked by jargon.

2. **Shared Sharpness** - The feeling that "the conversation is better than our individual contributions" and "something emerges that no one could formulate alone."

3. **Productive Friction** - Disagreement creates curiosity rather than defensiveness; relief that "this hasn't been smoothed over yet."

4. **Calm Instead of Cognitive Stress** - Where traditional tools create stress about correctness, CAUSA provides "the system remembers this" and "structure emerges without me guarding it."

### Emotional Journey Mapping

**First Encounter:** Curious relief - "This doesn't immediately demand definitions, arrows, or formats. I can just start by saying what I see."

**During Collaboration:** Engaged concentration - Like a well-moderated conversation where you listen and contribute simultaneously.

**After Session:** Shared ownership - "We have together better understood what this is really about" and "this story fits better than before."

**With Disagreement:** Legitimacy of difference - "We disagree, and that's visible and valuable."

**Returning Later:** Continuity of thinking - "Here lies our collective thinking process waiting" and "I step back into the same conversation, not a document."

### Micro-Emotions

**Confidence vs. Confusion:** Confidence in participation (contributing, expressing uncertainty, reacting); productive confusion in interpretation (causal direction, scope, assumptions). Design: Single contribution action always available, confusion localized to specific relations.

**Trust vs. Skepticism:** Trust in process (nothing disappears, disagreement preserved, edits attributable); skepticism toward claims (counter-claims, weak confidence, unresolved tension as contributions).

**Excitement vs. Anxiety:** Excitement from emergence (pattern visibility, connection discoveries); zero anxiety about correctness. Design: Gentle "reveal" moments, no validation states, provisional language.

**Accomplishment vs. Frustration:** Accomplishment = clarity gained (understanding disagreements, explicit uncertainties, sharper than started); frustration acceptable when shared and visible. Design: Session summaries emphasizing clarified tensions, avoid completion metaphors.

**Delight vs. Satisfaction:** Occasional subtle delight (surprising clarity, elegant disagreement visualization); sustained satisfaction (solid, calm, dependable infrastructure). Design: Micro-affirmations of collective progress.

**Belonging vs. Isolation:** Belonging through shared ownership of thought. Design: Claims not strongly owned, others can extend/reframe without overwriting, workspace as commons.

### Design Implications

**Safety to be Incomplete:** Provisional as default state, confidence levels lightweight/optional, open questions as first-class citizens, no visual punishment for unfinished thought.

**Shared Sharpness & Productive Friction:** Parallel visibility of competing explanations, side-by-side causal narratives, explicit markers for differences, avoid forced synthesis.

**Calm Instead of Cognitive Stress:** Minimal simultaneous stimuli, progressive structure revelation, predictable patterns, conversation-like interface.

**Collective Capability Cues:** Language reflecting aggregation, visual cues of cumulative insight, acknowledgment of disagreement as progress.

### Emotional Design Principles

1. **Emotional Training:** CAUSA trains users to trust incompleteness, value disagreement, feel carried by the collective.

2. **No Performance Space:** Infrastructure for thinking, not performance. Occasional delight, sustained satisfaction.

3. **Productive Disagreement:** Confusion and friction become assets, not liabilities to eliminate.

4. **Collective Flow:** Interface emphasizes convergence/divergence, not authorship. Language shifts organically from "I" to "we."

5. **Safety First:** Design eliminates anxiety about correctness, incompleteness, or expertise requirements.

**Emotional North Star:** CAUSA feels like thinking together in the presence of complexity, without anyone pretending to control it.

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

**Slack - The Gold Standard for Collective Sensemaking-in-Flow:**
- **Why users love it:** Lowers participation cost to near-zero, keeps thinking conversational, tolerates incompleteness
- **UX excellence:** Conversation as primary object, low-stakes contribution, persistent but non-final discussions
- **CAUSA adaptation:** Conversation-first interaction with causal threads and epistemic reactions

**Miro - Spatial Thinking Without Commitment:**
- **Why users love it:** Handles messy problems, makes relationships visible, supports group workshops
- **UX excellence:** Spatial externalization, permission to be messy, collective presence cues
- **CAUSA adaptation:** Spatial metaphor with automatic meaningful proximity (causal strength, uncertainty)

**Notion - Calm, Trustworthy Knowledge Holding:**
- **Why users love it:** Where thinking settles, decisions become legible, institutional memory lives
- **UX excellence:** Progressive structure, predictable interaction, "safe place for shared understanding"
- **CAUSA adaptation:** Progressive formalization with causal claims as expandable blocks, temporal continuity

**Synthesis:** These tools share low barrier to contribution, tolerance for incompleteness, collective ownership, progressive structure, and persistence without finality. None ask users to "model" - they ask users to participate.

### Transferable UX Patterns

**Adopt Directly (Low Risk, High Fit):**
- **Conversation-first interaction** (Slack) - meaning emerges through exchange, not upfront structure
- **Low-stakes contribution** (all) - partial thoughts acceptable, no ceremony required
- **Progressive formalization** (Notion) - start lightweight, gradually become structured
- **Calm, predictable interaction** (Notion) - low cognitive overhead, trustworthy persistence
- **Threading for complexity localization** (Slack) - contain discussions without fragmenting whole

**Adapt Deliberately (High Value, Needs Care):**
- **Spatial externalization** (Miro) → **semantic spatialization** - relationships visible with automatic meaningful proximity
- **Co-presence indicators** (Miro) → **epistemic co-presence** - seeing others' reasoning builds trust
- **Shared surfaces** (Miro) → **collective reasoning commons** - no individual ownership by default
- **Discussion workflows** (GitHub) → **causal claim lifecycles** - propose, discuss, refine with optional resolution

### Anti-Patterns to Avoid

**Existential Risks CAUSA Must Actively Reject:**

1. **Premature Formalization** - No upfront requirements for variables, directions, or equations
2. **Diagram-Centrism** - Diagrams are views, not the product; no "completeness" pressure
3. **Flat Visual Metaphors** - Visual differentiation must encode epistemic meaning
4. **Individual Ownership by Default** - Collective stewardship, optional attribution
5. **Completion Bias** - Stability, not closure, is success; "still under discussion" is valid
6. **Hidden AI Authority** - Every AI action inspectable and contestable

### Design Inspiration Strategy

**Adopt Directly:** Conversation-first interaction, low-stakes contribution, progressive structuring, calm predictability, threading for complexity containment - these transfer unchanged and align perfectly with CAUSA's social process approach.

**Adapt Deliberately:** Spatial metaphors become semantic (causal relationships), co-presence becomes epistemic (reasoning visibility), shared surfaces become commons (collective ownership), discussion workflows become claim lifecycles - powerful patterns modified for CAUSA's unique causal reasoning context.

**Avoid Entirely:** Form builders, manual layouts, permission-heavy workflows, gamification, "one true model" mentalities - these conflict with CAUSA's core emotional goals and collaborative reasoning purpose.

**Design Heuristic:** For every decision, ask: "Does this reduce or increase the cognitive cost of participating in shared uncertainty?"
- Lowers threshold to contribute → adopt
- Makes disagreement safer → adopt
- Externalizes structure invisibly → adopt
- Rewards certainty over curiosity → avoid
- Shifts focus from meaning to correctness → avoid

<!-- UX design content will be appended sequentially through collaborative workflow steps -->
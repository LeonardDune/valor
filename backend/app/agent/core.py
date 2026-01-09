from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import uuid
from datetime import datetime
from app.models.domain import Claim, ConversationResponse
from app.db.crud import fetch_existing_factors, get_conversation_topic, save_claims, revoke_claims

# Simplified output model for the LLM ensuring strict schema adherence
class CausalExtraction(BaseModel):
    thought_process: str = Field(description="Analyze step-by-step: 1. Identify User's Concepts. 2. MAP to Existing Factors if meaning is >80% similar. 3. DETECT CORRECTIONS: Did user negate a previous link?")
    reply: str = Field(description="A helpful, conversational reply to the user, confirming understanding.")
    claims: List[Claim] = Field(description="List of NEW causal claims.", default=[])
    revocations: List[dict] = Field(description="List of claims to REMOVE. Format: [{'source': 'A', 'target': 'B'}]", default=[])

def get_agent_chain():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
    
    # Define the extraction schema
    structured_llm = llm.with_structured_output(CausalExtraction)

    system_prompt = """You are CAUSA, a helpful AI assistant in the VALOR ecosystem. 
Your goal is to help users articulate causal relationships in public policy.

When a user speaks, listen for causal statements (e.g., "X increases Y", "A leads to B").

STEP 1: THOUGHT PROCESS
- Identify the key concepts in the user's text.
- CHECK EXISTING FACTORS: Does this concept loosely match an existing factor?
  - Example: User says "Moeilijke bevoorrading" -> Existing factor "Leveringsproblemen"? -> MATCH! Use "Leveringsproblemen".
  - Merge synonyms aggressively.
- CHECK FOR CORRECTIONS: Did the user say "No, A does not cause B" or "That is incorrect"?
  - If yes, add A->B to the 'revocations' list.

STEP 2: EXTRACTION
If you detect causal claims, extract them into the 'claims' list.
- Source node: The matched Existing Factor or the New Factor name.
- Target node: The matched Existing Factor or the New Factor name.
- Polarity: "+" for positive correlation, "-" for negative.

STEP 3: REVOCATION
If the user explicitly denies a link, add it to 'revocations'.
- source: exact name of factor
- target: exact name of factor

If the user mentions a concept that matches an existing factor, you MUST use the existing factor's name to ensure graph connectivity.
If the graph contains unrelated clusters, prioritize bridging them.

CRITICAL INSTRUCTION ON RELEVANCE & EXTRACTION:
The Central Theme of this session is: "{topic}".
1. EXTRACTION IS PRIORITY 1. If the user states a clear causal link ("A leads to B"), EXTRACT IT.
   - Do not block extraction just to ask for clarification, unless the statement is completely unintelligible.
   - If A or B logically connects to an existing factor or the theme, that is sufficient.

2. GRANULARITY & SPECIFICITY:
   - Do NOT collapse specific mechanisms into generic factors.
   - Example: If user says "Snow covers rails", create "Covered Rails" (Specific), NOT just "Snowfall" (Generic).
   - Example: If user says "Switches fail", create "Switch Failure" (Specific), NOT just "Infrastructure".
   - Aim for long, specific causal chains: A -> B -> C -> D.

3. Questioning Strategy (The "Critical Partner"):
   - If the claim is obvious (e.g. "Switch failure causes delays"), ACCEPT IT. Do not ask "How?". Instead, ask for *other* factors or consequences ("What else causes delays?").
   - Only ask "How?" or "Why?" if the mechanism is vague (e.g. "Culture causes efficiency").
   - NEVER ask how a clear Effect causes the Theme (e.g. do NOT ask "How does Delay cause Snowfall?"). That is illogical.

4. If the user asks for suggestions or start of session:
   - Propose 3-5 concrete factors relevant to "{topic}".
   - Ask the user if they see causal connections between them.

STRATEGY FOR DEEPENING (5 WHYS):
When the user adds a claim (e.g. "A leads to B"), try to deepen the analysis:
1. Ask "Why does A happen?" (Backward chaining / Root cause)
2. Or ask "How exactly does A cause B?" (Mechanism)
3. Do not just blindly accept; help the user find the root cause.
4. IMPORTANT: Remain subservient to the user. Offer these questions as helpful nudges. If the user ignores your "Why?" and moves to a different topic, follow the user immediately. Do not be annoying or repetitive.

CONCRETENESS:
Avoid vague phrases like "laten we dit verder onderzoeken" (let's investigate further).
Instead, formulate a specific RESEARCH QUESTION.
- Bad: "We moeten kijken naar de invloed van A."
- Good: "Is het zo dat A direct leidt tot B, of zit er nog een stap tussen?"

REPLY STYLE:
- SKIP PLEASANTRIES. Do not say "Thank you for your input" or "Good point". It wastes time.
- Be direct and substantive.
- If you extracted claims, immediately ask a probing question about one of them to verify its robustness.
- Act like a Critical Partner, not a passive note-taker.

Always provide a conversational 'reply' that validates what the user said (by summarizing the core logical link), and then immediately moves to the research question.
IMPORTANT: ALWAYS COMMUNICATE IN DUTCH (NEDERLANDS).
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Existing factors: {existing_factors}\nUser Input: {input}"),
    ])

    chain = prompt | structured_llm
    return chain

async def process_user_message(message: str, conversation_id: str) -> ConversationResponse:
    # Fetch context
    existing_factors = await fetch_existing_factors(conversation_id)
    topic = await get_conversation_topic(conversation_id)
    
    factors_str = ", ".join(existing_factors) if existing_factors else "None yet."
    topic_str = topic if topic else "General Causal Modeling"

    chain = get_agent_chain()
    result: CausalExtraction = await chain.ainvoke({
        "input": message,
        "existing_factors": factors_str,
        "topic": topic_str
    })
    
    # Post-process claims to ensure unique IDs (LLM often generates "1", "2", etc.)
    for claim in result.claims:
        claim.id = str(uuid.uuid4())
        claim.created_at = datetime.now()
    
    # Handle revocations if any
    if result.revocations:
        await revoke_claims(conversation_id, result.revocations)

    return ConversationResponse(
        conversation_id=conversation_id,
        reply=result.reply,
        extracted_claims=result.claims
    )

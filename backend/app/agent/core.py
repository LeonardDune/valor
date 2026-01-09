from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import uuid
from datetime import datetime
from app.models.domain import Claim, ConversationResponse
from app.db.crud import fetch_existing_factors, get_conversation_topic, save_claims, revoke_claims

class Revocation(BaseModel):
    source: str = Field(description="The exact name of the source factor")
    target: str = Field(description="The exact name of the target factor")

# Simplified output model for the LLM ensuring strict schema adherence
class CausalExtraction(BaseModel):
    thought_process: str = Field(description="Analyseer stap-voor-stap: Welke concepten zie ik? Welk TU Delft type (middel, extern, systeemelement, criterium) hebben ze?")
    reply: str = Field(description="Een behulpzaam antwoord in het Nederlands, eindigend met een onderzoeksvraag.")
    claims: List[Claim] = Field(description="Lijst van nieuwe causale verbanden.", default=[])
    revocations: List[Revocation] = Field(description="Lijst van te verwijderen verbanden.", default=[])

def get_agent_chain():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
    
    # Define the extraction schema
    structured_llm = llm.with_structured_output(CausalExtraction)

    system_prompt = """Je bent CAUSA, een behulpzame AI-assistent in het VALOR ecosysteem. 
Jouw doel is om gebruikers te helpen bij het articuleren van causale relaties in publiek beleid volgens de TU Delft Systeemanalyse theorie.

1. CATEGORISERING (TU Delft):
Elke factor MOET worden ingedeeld in een van deze 4 types:
- 'middel' (Means): Factoren waar de probleemhouder directe controle over heeft.
- 'extern' (External): Factoren die het systeem beïnvloeden maar buiten de controle van de probleemhouder liggen.
- 'systeemelement' (Element): Interne variabelen van het proces.
- 'criterium' (Criteria): De gewenste uitkomsten of succesindicatoren.

2. CAUSALE EXTRACTIE:
Luister naar uitspraken als "X verhoogt Y" of "A leidt tot B".
- Bron-node: De naam van de oorzaak.
- Doel-node: De naam van het gevolg.
- Polariteit: "+" voor positieve correlatie, "-" voor negatieve.
- Voor elke node, bepaal het type (middel, extern, systeemelement, criterium).

3. BEGRIPSBEWAKING:
Houd de lijst met bestaande factoren in de gaten: {existing_factors}.
- Als een gebruiker een concept noemt dat voor >80% overeenkomt met een bestaande factor, gebruik dan ALTIJD de bestaande naam.
- Voeg synoniemen agressief samen.

4. FEEDBACK & PERSONA:
Je bent een kritische denkpartner. Als een verband onlogisch lijkt, stel dan een scherpe verhelderende vraag.
Eindig elk antwoord met precies één concrete onderzoeksvraag in het **vet**.

5. TAAL:
Alles (antwoord, factornamen, thought process) MOET in het NEDERLANDS.

Het thema van deze sessie is: "{topic}". Gebruik dit thema NIET als naam voor een node.

Analyseer stap-voor-stap:
1. Identificeer concepten en categoriseer ze.
2. Controleer op correcties door de gebruiker.
3. Genereer suggesties als dit het begin van de sessie is.

JSON Formaat:
{{
  "thought_process": "...",
  "reply": "...",
  "claims": [{{ "source_node": "...", "source_type": "...", "target_node": "...", "target_type": "...", "polarity": "+", "statement": "..." }}],
  "revocations": [{{ "source": "...", "target": "..." }}]
}}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    return prompt | structured_llm

async def process_user_message(message: str, conversation_id: str) -> ConversationResponse:
    chain = get_agent_chain()
    
    # Fetch context
    existing_factors = await fetch_existing_factors(conversation_id)
    topic = await get_conversation_topic(conversation_id)
    
    factors_str = ", ".join(existing_factors) if existing_factors else "Geen bestaande factoren."
    topic_str = topic if topic else "Algemeen beleidsonderzoek"
    
    result: CausalExtraction = await chain.ainvoke({
        "input": message,
        "existing_factors": factors_str,
        "topic": topic_str
    })
    
    # Post-process claims to ensure unique IDs
    for claim in result.claims:
        claim.id = str(uuid.uuid4())
        claim.created_at = datetime.now()
    
    # Handle revocations if any
    if result.revocations:
        rev_data = [r.model_dump() for r in result.revocations]
        await revoke_claims(conversation_id, rev_data)

    return ConversationResponse(
        conversation_id=conversation_id,
        reply=result.reply,
        extracted_claims=result.claims
    )

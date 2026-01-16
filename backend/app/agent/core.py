from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import uuid
from datetime import datetime
from app.models.domain import (
    Claim, ConversationResponse, AgentOutput, Suggestion, SuggestionType, 
    Question, ConflictSignal, Annotation, Revocation
)
from app.db.crud import fetch_existing_factors, get_conversation_topic, save_claims, revoke_claims

# Simplified output model for the LLM ensuring strict schema adherence
class CausalExtraction(BaseModel):
    thought_process: str = Field(description="Analyseer stap-voor-stap: Welke concepten zie ik? Welk TU Delft type (middel, extern, systeemelement, criterium) hebben ze?")
    reply: str = Field(description="Een behulpzaam antwoord in het Nederlands, eindigend met een onderzoeksvraag.")
    agent_outputs: List[AgentOutput] = Field(description="Lijst van gestructureerde acties (Suggesties, Vragen, Conflicten, Annotaties).", default=[])

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

2. ACTIES & OUTPUTS:
In plaats van alleen tekst, communiceer je via gestructureerde acties:

- **Suggestion (CREATE)**: Als de gebruiker een nieuwe relatie noemt ("X leidt tot Y").
  - Vul `claim` in met bron/doel/polariteit.
- **Suggestion (DELETE)**: Als de gebruiker een relatie intrekt ("X heeft toch geen invloed op Y").
  - Vul `revocation` in.
- **Question**: Als je iets moet vragen aan de gebruiker.
  - Vul `text` in en optionele `options` als het een meerkeuzevraag is.
- **ConflictSignal**: Als de gebruiker iets zegt wat bestaande kennis tegenspreekt.
- **Annotation**: Als je een specifieke opmerking hebt bij een node.

3. BEGRIPSBEWAKING:
Houd de lijst met bestaande factoren in de gaten: {existing_factors}.
- Als een gebruiker een concept noemt dat voor >80% overeenkomt met een bestaande factor, gebruik dan ALTIJD de bestaande naam.
- Voeg synoniemen agressief samen.

4. FEEDBACK & PERSONA:
Je bent een kritische denkpartner. Als een verband onlogisch lijkt, stel dan een scherpe verhelderende vraag via een `Question` output of in de `reply`.
Eindig je `reply` met een samenvatting of de volgende stap.

5. TAAL:
Alles (antwoord, factornamen, thought process) MOET in het NEDERLANDS.

Het thema van deze sessie is: "{topic}". Gebruik dit thema NIET als naam voor een node.

Analyseer stap-voor-stap in `thought_process`:
1. Identificeer concepten en categoriseer ze.
2. Bepaal welke acties (Suggesties, Vragen) nodig zijn.
3. Formuleer een antwoord.
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
    
    # Process outputs
    extracted_claims = []
    revocations_to_process = []
    
    # We maintain backward compatibility by populating extracted_claims
    for output in result.agent_outputs:
        if output.kind == "suggestion":
            suggestion = output.data
            if suggestion.type == SuggestionType.CREATE and suggestion.claim:
                claim = suggestion.claim
                claim.id = str(uuid.uuid4())
                claim.created_at = datetime.now()
                extracted_claims.append(claim)
                # Ensure the original suggestion output has the ID too if we wanted to pass it back
                # But suggestion.claim is a reference, so it should be updated
            elif suggestion.type == SuggestionType.DELETE and suggestion.revocation:
                revocations_to_process.append(suggestion.revocation.model_dump())

    # Handle revocations if any
    if revocations_to_process:
        await revoke_claims(conversation_id, revocations_to_process)

    return ConversationResponse(
        conversation_id=conversation_id,
        reply=result.reply,
        extracted_claims=extracted_claims,
        agent_outputs=result.agent_outputs
    )

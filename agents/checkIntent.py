from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from gemini_agent import gemini_client

# Prompt with {context}
intent_prompt = ChatPromptTemplate.from_template(
    "Check the following message: {context}\n\n"
    "Classify it into one of the following intents (respond in a **single word**):\n"
    "'RFQ', 'Complaint', 'Invoice', 'Regulation', 'Fraud_Risk'.\n"
    "If none match, respond with 'ERROR'."
)

intent_chain = LLMChain(llm=gemini_client, prompt=intent_prompt)

# Function takes text (already parsed)
async def check_file_intent_from_text(text: str) -> str:
    if not text.strip():
        return "ERROR"
    result = await intent_chain.ainvoke({"context": text})
    return result["text"].strip()

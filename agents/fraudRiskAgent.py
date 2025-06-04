from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from .gemini_agent import gemini_client

fraud_prompt = ChatPromptTemplate.from_template(
    "You're a fraud detection analyst. Examine the following report:\n\n"
    "{context}\n\n"
    "Extract and return JSON with:\n"
    "- incident_type\n"
    "- description\n"
    "- suspected_entity\n"
    "- amount_involved\n"
    "- dates\n"
    "- recommended_action\n"
    "- urgency_level\n\n"
    "Ensure well-structured JSON only,skip unpresented details."
)
fraud_chain = LLMChain(llm=gemini_client, prompt=fraud_prompt)

async def fraudRiskAgent(data):
    text = data.get("content") if isinstance(data, dict) else str(data)
    if not text.strip():
        return {"error": "Empty content"}
    result = await fraud_chain.ainvoke({"context": text})
    return result["text"].strip()

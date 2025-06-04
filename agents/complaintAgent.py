from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from .gemini_agent import gemini_client

complaint_prompt = ChatPromptTemplate.from_template(
    "You are a customer service AI. Analyze the complaint email:\n\n"
    "{context}\n\n"
    "Return a JSON with:\n"
    "- customer_name\n"
    "- product_or_service\n"
    "- issue_description\n"
    "- date_of_incident\n"
    "- requested_action\n"
    "- contact_details\n\n"
    "Ensure well-structured JSON only,skip unpresented details."
)
complaint_chain = LLMChain(llm=gemini_client, prompt=complaint_prompt)

async def complaintAgent(data):
    text = data.get("content") if isinstance(data, dict) else str(data)
    if not text.strip():
        return {"error": "Empty content"}
    result = await complaint_chain.ainvoke({"context": text})
    return result["text"].strip()

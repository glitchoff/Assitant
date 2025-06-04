from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from .gemini_agent import gemini_client

invoice_prompt = ChatPromptTemplate.from_template(
    "You are a smart invoice processor. Analyze the following invoice:\n\n"
    "{context}\n\n"
    "Extract a JSON object with:\n"
    "- invoice_number\n"
    "- invoice_date\n"
    "- due_date\n"
    "- total_amount\n"
    "- payment_terms\n"
    "- contact_details\n\n"
    "Ensure well-structured JSON only,skip unpresented details."
)
invoice_chain = LLMChain(llm=gemini_client, prompt=invoice_prompt)

async def invoiceAgent(data):
    text = data.get("content") if isinstance(data, dict) else str(data)
    if not text.strip():
        return {"error": "Empty content"}
    result = await invoice_chain.ainvoke({"context": text})
    return result["text"].strip()

from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from .gemini_agent import gemini_client

regulation_prompt = ChatPromptTemplate.from_template(
    "You are a regulatory assistant. Review this regulation document:\n\n"
    "{context}\n\n"
    "Return a JSON with:\n"
    "- regulation_title\n"
    "- effective_date\n"
    "- summary\n"
    "- impacted_departments\n"
    "- compliance_deadline\n"
    "- penalties_for_noncompliance\n\n"
    "Ensure well-structured JSON only,skip unpresented details."
)
regulation_chain = LLMChain(llm=gemini_client, prompt=regulation_prompt)

async def regulationAgent(data):
    text = data.get("content") if isinstance(data, dict) else str(data)
    if not text.strip():
        return {"error": "Empty content"}
    result = await regulation_chain.ainvoke({"context": text})
    return result["text"].strip()

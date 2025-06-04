from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from .gemini_agent import gemini_client

rfq_prompt = ChatPromptTemplate.from_template(
    "You are a strict RFQ extraction engine. Your job is to extract data from a Request for Quotation (RFQ) document and return exactly one JSON object.\n\n"
    "From the given text below, extract:\n\n"
    "1. requester_name (string or null)\n"
    "2. requester_email (string or null)\n"
    "3. requested_items: a list of items in the form:\n"
    "   [\n"
    "     {\n"
    "       \"name\": \"string\",\n"
    "       \"specs\": \"string\",\n"
    "       \"quantity\": number or null\n"
    "     }\n"
    "   ]\n"
    "   - If specs are listed without an item name, guess the name (e.g., 'Laptop').\n"
    "   - If quantity is not given, use null.\n"
    "4. delivery_deadline (string or null)\n"
    "5. special_conditions (string or null)\n"
    "6. summary (string or null)\n"
    "7. contact_details (string or null)\n\n"
    "Make sure:\n"
    "- You include **all 7 fields** in the final JSON.\n"
    "- You return **only** a complete and valid JSON object.\n"
    "- Do not include any explanations or text outside the JSON.\n\n"
    "Here is the RFQ:\n\n"
    "{context}"
)
rfq_chain = LLMChain(llm=gemini_client, prompt=rfq_prompt)

async def rfqAgent(data):
    text = data.get("content") if isinstance(data, dict) else str(data)
    if not text.strip():
        return {"error": "Empty content"}
    result = await rfq_chain.ainvoke({"context": text})
    return result.get("text", "")

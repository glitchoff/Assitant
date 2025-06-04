from .gemini_agent import gemini_client

invoice_prompt = ChatPromptTemplate.from_template(
    ""
)

invoice_chain = LLMChain(llm=gemini_client, prompt=invoice_prompt)

async def invoiceAgent(data):
    if isinstance(data, dict) and 'content' in data:
        text = data['content']
    else:
        text = str(data)
        
    if not text.strip():
        return "ERROR"
        
    result = await invoice_chain.ainvoke({"context": text})
    return result["text"].strip()


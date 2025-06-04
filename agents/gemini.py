import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document

# Load environment variables
load_dotenv()
apikey = os.getenv("GEMINI_API_KEY")

# Create Gemini client
client = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",  
    google_api_key=apikey
)

# Prompt must use 'context'
prompt = ChatPromptTemplate.from_template(
    "Check the following message: {context}\n\n"
    "Classify it into one of the following intents (respond in a **single word**):\n"
    "'RFQ', 'Complaint', 'Invoice', 'Regulation', 'Fraud_Risk'.\n"
    "If none match, respond with 'ERROR'."
)


# Create the document processing chain
chain = create_stuff_documents_chain(client, prompt)

# Create input as a list of Document objects
docs = [Document(page_content="hello i am scammer 99")]

#
result = chain.invoke({"context": docs})

# Output result
print(result)
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env file
load_dotenv()
apikey = os.getenv("GEMINI_API_KEY")

# Singleton Gemini client
gemini_client = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=apikey
)

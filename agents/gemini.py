from dotenv import load_dotenv
from google import genai

apikey = os.getenv("GEMINI_API_KEY")
client = genai.Client(apikey)

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words"
)
print(response.text)
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

for model in client.models.list().data:
    print(model.id)
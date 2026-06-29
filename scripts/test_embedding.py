import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

text = "The Kalman filter estimates the state of a moving object."

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=text
)

embedding = result.embeddings[0].values

print(f"Embedding length: {len(embedding)}")
print(f"First 10 numbers: {embedding[:10]}")
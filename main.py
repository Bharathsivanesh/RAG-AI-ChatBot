# pip install google-genai python-dotenv

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "bharath.txt")

def load_knowledge():
    """Reads your knowledge file."""
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"{DATA_FILE} not found")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return f.read()

def ask_question(question):
    """Ask a question based on your knowledge data."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    knowledge_text = load_knowledge()

    # Combine your data and the question
    prompt = f"""
You are an expert assistant. Use ONLY the information in the text below to answer the user's question and just giev me as a paragraph not a \\n and *.

Knowledge Base:
{knowledge_text}

User Question:
{question}
"""

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    print("=== Gemini Response ===\n")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
    )

    print(response.text)
    print("\n=== End of Response ===")

if __name__ == "__main__":
    user_question = input("Ask your question: ")
    ask_question(user_question)

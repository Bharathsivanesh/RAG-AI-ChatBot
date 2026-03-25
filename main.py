# pip install fastapi uvicorn sqlalchemy psycopg2-binary google-genai python-dotenv

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
engine = create_engine(DATABASE_URL)
client = genai.Client(api_key=GEMINI_API_KEY)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "bharath.txt")

# ================= FILE =================
def load_knowledge():
    if not os.path.exists(DATA_FILE):
        return ""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return f.read()

# ================= DB =================
def get_student_data(student_id: int):
    query = """
    SELECT 
        s.id,
        s.student_name,
        sub.subject_name,
        se.exam_type,
        se.semester,
        sm.obtained_marks,
        sm.max_marks
    FROM student_marks sm
    JOIN students s ON sm.student_id = s.id
    JOIN student_exam se ON sm.exam_id = se.id
    JOIN subjects sub ON se.subject_id = sub.id
    WHERE s.id = :student_id
    """

    with engine.connect() as conn:
        result = conn.execute(text(query), {"student_id": student_id})
        rows = result.fetchall()

    return rows

# ================= CONTEXT =================
def build_context(data):
    if not data:
        return "No data available for this student."

    context = ""

    for row in data:
        percentage = (row.obtained_marks / row.max_marks) * 100

        if percentage < 50:
            status = "Weak"
        elif percentage < 70:
            status = "Average"
        else:
            status = "Strong"

        context += (
            f"Subject: {row.subject_name}, "
            f"Exam: {row.exam_type}, "
            f"Semester: {row.semester}, "
            f"Marks: {row.obtained_marks}/{row.max_marks}, "
            f"Percentage: {percentage:.2f}%, "
            f"Status: {status}. "
        )

    return context

# ================= AI =================
def ask_ai(question, context, knowledge_text):
    prompt = f"""
You are a smart academic AI assistant.

STRICT RULES:
- Use ONLY student data
- DO NOT say you don’t have data
- Identify weak subjects clearly
- Answer in ONE paragraph

STUDENT DATA:
{context}

KNOWLEDGE:
{knowledge_text}

QUESTION:
{question}
"""

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
    )

    return response.text

# ================= API =================
@app.get("/ask")
def ask(question: str, student_id: int):
    try:
        student_data = get_student_data(student_id)
        print("RAW DATA:", student_data)

        db_context = build_context(student_data)
        print("CONTEXT:", db_context)

        knowledge_text = load_knowledge()

        answer = ask_ai(question, db_context, knowledge_text)

        return {"student_id": student_id, "answer": answer}

    except Exception as e:
        return {"error": str(e)}
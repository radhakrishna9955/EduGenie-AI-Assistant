import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "your_gemini_api_key" in api_key.lower():
        return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name="gemini-2.5-flash")
    except Exception as e:
        print(f"[Gemini Config Error] {e}")
        return None

def answer_question_with_gemini(question: str) -> str:
    """
    Send a question to Gemini and return its answer as plain text.
    Gracefully handles missing keys or network errors.
    """
    model = get_gemini_model()
    if not model:
        # High quality offline fallback response for demonstrations
        return (
            f"💡 **EduGenie Insight:**\n\n"
            f"Here is an educational breakdown for **'{question}'**:\n\n"
            f"1. **Core Concept:** In academia, this concept centers on fundamental principles of system behavior and observation.\n"
            f"2. **Key Insight:** When exploring {question.lower()}, focus on foundational laws, cause-and-effect relationships, and practical real-world applications.\n"
            f"3. **Summary:** Always verify with standard references and practical examples.\n\n"
            f"*(Note: Connect your GEMINI_API_KEY in `.env` to enable live cloud generation with Gemini 2.5 Flash.)*"
        )
    try:
        prompt = (
            f"You are EduGenie, an expert, enthusiastic academic tutor. Answer the student's question "
            f"clearly, concisely, and accurately in 2-4 well-structured paragraphs with bullet points if helpful:\n\n{question}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Unable to fetch live answer ({str(e)}). Please check your internet connection or API quota."


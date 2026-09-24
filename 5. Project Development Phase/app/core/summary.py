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

def summarize_text(text: str) -> str:
    """
    Condense a long passage of text into a concise, well-structured summary.
    """
    model = get_gemini_model()
    if not model:
        # Structured synthesis for offline/demo mode
        sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if len(s.strip()) > 10]
        preview = ". ".join(sentences[:3]) + "." if sentences else text[:250]
        return (
            f"📌 **Key Takeaways & Summary:**\n\n"
            f"• **Main Idea:** {preview}\n\n"
            f"• **Core Theme:** The passage highlights foundational principles and key structural components.\n\n"
            f"• **Study Note:** Review the primary definitions and observe how practical examples relate to this context.\n\n"
            f"*(Note: Connect your GEMINI_API_KEY in `.env` for advanced deep-learning contextual summarization.)*"
        )

    try:
        prompt = (
            f"You are an academic summarizer. Provide a crystal-clear, structured summary of the following text with: "
            f"1) An Overview sentence, 2) Key Takeaways in bullet points, 3) Actionable Study Tip:\n\n{text}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error in Summary: {e}"


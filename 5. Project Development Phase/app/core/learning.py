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

def get_learning_recommendations(topic: str) -> str:
    """
    Generate a structured, progressive learning roadmap for a given topic.
    """
    model = get_gemini_model()
    if not model:
        topic_name = topic.strip().title()
        return f"""### 🗺️ Comprehensive Learning Roadmap: {topic_name}

#### 🟢 Phase 1: Foundations & Core Concepts (Weeks 1–2)
* **What to learn:** Basic terminology, historical context, underlying principles, and essential setup.
* **Key Milestones:** Grasp fundamental rules, understand core notation, and complete 3 introductory exercises.
* **Recommended Free Resources:**
  - Official Documentation & Standard Academic Guides
  - *Crash Course & YouTube Tutorials (Khan Academy / freeCodeCamp)*
  - Interactive sandbox practice exercises

#### 🟡 Phase 2: Intermediate Deep Dive & Practical Implementations (Weeks 3–5)
* **What to learn:** Key algorithms, design patterns, architecture flow, and real-world case studies.
* **Key Milestones:** Build a mini-project applying {topic_name} concepts from scratch.
* **Recommended Free Resources:**
  - *Coursera / edX Open Audits*
  - Comprehensive textbook: *Standard Academic Handbook of {topic_name}*
  - GitHub open-source repositories and hands-on sample projects

#### 🔴 Phase 3: Advanced Mastery & Optimization (Weeks 6+)
* **What to learn:** Edge cases, performance tuning, advanced architectural paradigms, and research papers.
* **Key Milestones:** Deploy a production-ready application and contribute to community discussions.
* **Recommended Free Resources:**
  - *ArXiv research preprints & ACM Digital Library*
  - Specialized industry benchmarks and masterclasses

*(💡 Tip: Add your GEMINI_API_KEY in `.env` to generate dynamic custom roadmaps for niche subjects!)*
"""

    prompt = f"""
You are an expert academic tutor and curriculum designer. The student wants to master: {topic}.
Create a high-impact, beautifully structured learning roadmap with:
1. Phase 1: Foundations & Prerequisites (Beginner)
2. Phase 2: Core Concepts & Hands-on Practice (Intermediate)
3. Phase 3: Advanced Topics & Real-world Mastery (Advanced)
4. Curated recommended resources (Books, Free Courses, Websites, Repositories)
5. Actionable Next Step to start today.

Format nicely in clean Markdown with emojis and bold headers.
"""
    try:
        response = model.generate_content(prompt)
        if hasattr(response, "text"):
            return response.text
        elif hasattr(response, "parts") and response.parts:
            return response.parts[0].text
        else:
            return "❌ Could not extract content from Gemini response."
    except Exception as e:
        return f"❌ Error occurred: {str(e)}"


import json
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from app.database import get_db_session
import app.models as models
from app.api.auth import get_current_user_from_request

from app.core.qna import answer_question_with_gemini
from app.core.explanation import explain_topic
from app.core.summary import summarize_text
from app.core.quiz import generate_quiz
from app.core.learning import get_learning_recommendations

router = APIRouter(tags=["Study Tools"])

@router.get("/qa")
async def answer_question(request: Request, question: str = Query(...)):
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        
        # Save UserQuery record
        user_query = models.UserQuery(
            user_id=user.user_id,
            query_type="QnA",
            query_text=question
        )
        db.add(user_query)
        db.commit()
        db.refresh(user_query)
        
        # Generate response
        answer = answer_question_with_gemini(question)
        
        # Save AIResponse record
        ai_response = models.AIResponse(
            query_id=user_query.query_id,
            response_text=answer,
            model_used="gemini-2.5-flash"
        )
        db.add(ai_response)
        db.commit()
        
        return {"answer": answer}
    finally:
        db.close()

@router.post("/explain/")
async def explain_api(request: Request):
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        
        data = await request.json()
        topic = data.get("topic")
        if not topic:
            return JSONResponse(content={"error": "Please provide a topic."}, status_code=400)
            
        # Save UserQuery record
        user_query = models.UserQuery(
            user_id=user.user_id,
            query_type="Explanation",
            query_text=topic
        )
        db.add(user_query)
        db.commit()
        db.refresh(user_query)
        
        # Generate response
        explanation = explain_topic(topic)
        
        # Save AIResponse record
        ai_response = models.AIResponse(
            query_id=user_query.query_id,
            response_text=explanation,
            model_used="LaMini-Flan-T5-783M"
        )
        db.add(ai_response)
        db.commit()
        
        return {"topic": topic, "explanation": explanation}
    finally:
        db.close()

@router.post("/summarize/")
async def summarize_api(request: Request):
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        
        data = await request.json()
        text = data.get("text")
        if not text:
            return JSONResponse(content={"error": "Please provide text to summarize."}, status_code=400)
            
        # Save UserQuery record
        user_query = models.UserQuery(
            user_id=user.user_id,
            query_type="Summary",
            query_text=text
        )
        db.add(user_query)
        db.commit()
        db.refresh(user_query)
        
        # Generate response
        summary = summarize_text(text)
        
        # Save AIResponse record
        ai_response = models.AIResponse(
            query_id=user_query.query_id,
            response_text=summary,
            model_used="gemini-2.5-flash"
        )
        db.add(ai_response)
        
        # Save Summary record
        summary_record = models.Summary(
            query_id=user_query.query_id,
            summary_text=summary
        )
        db.add(summary_record)
        
        db.commit()
        
        return {"summary": summary}
    finally:
        db.close()

@router.post("/quiz")
async def quiz_api(request: Request):
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        
        data = await request.json()
        text = data.get("text")
        if not text:
            return JSONResponse(content={"error": "Please provide text for quiz."}, status_code=400)
            
        # Save UserQuery record
        user_query = models.UserQuery(
            user_id=user.user_id,
            query_type="Quiz",
            query_text=text
        )
        db.add(user_query)
        db.commit()
        db.refresh(user_query)
        
        # Generate response
        quiz = generate_quiz(text)
        
        # Save AIResponse record
        ai_response = models.AIResponse(
            query_id=user_query.query_id,
            response_text=json.dumps(quiz),
            model_used="gemini-2.5-flash"
        )
        db.add(ai_response)
        
        # Save Quiz records if generated successfully
        if isinstance(quiz, list):
            for q in quiz:
                opts = q.get("options", ["", "", "", ""])
                while len(opts) < 4:
                    opts.append("")
                quiz_item = models.Quiz(
                    query_id=user_query.query_id,
                    question_text=q.get("question", ""),
                    option_a=str(opts[0]),
                    option_b=str(opts[1]),
                    option_c=str(opts[2]),
                    option_d=str(opts[3]),
                    correct_answer=q.get("answer", "")
                )
                db.add(quiz_item)
                
        db.commit()
        return JSONResponse(content={"quiz": quiz})
    finally:
        db.close()

@router.get("/learn/recommendations")
async def learning_recommendation_api(request: Request, topic: str = Query(...)):
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        
        # Save UserQuery record
        user_query = models.UserQuery(
            user_id=user.user_id,
            query_type="Recommendation",
            query_text=topic
        )
        db.add(user_query)
        db.commit()
        db.refresh(user_query)
        
        # Generate response
        recommendation = get_learning_recommendations(topic)
        
        # Save AIResponse record
        ai_response = models.AIResponse(
            query_id=user_query.query_id,
            response_text=recommendation,
            model_used="gemini-2.5-flash"
        )
        db.add(ai_response)
        
        # Save LearningPath record
        learning_path_rec = models.LearningPath(
            query_id=user_query.query_id,
            topic=topic,
            difficulty_level="Adaptive",
            recommended_resources=recommendation
        )
        db.add(learning_path_rec)
        db.commit()
        
        return {"topic": topic, "recommendation": recommendation}
    finally:
        db.close()

@router.get("/history")
async def get_study_history(request: Request, limit: int = 20):
    """Retrieve the recent study history of queries and AI responses for the active user."""
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        queries = (
            db.query(models.UserQuery)
            .filter(models.UserQuery.user_id == user.user_id)
            .order_by(models.UserQuery.created_at.desc())
            .limit(limit)
            .all()
        )
        history_list = []
        for q in queries:
            resp_text = q.ai_response.response_text if q.ai_response else ""
            model_used = q.ai_response.model_used if q.ai_response else "system"
            history_list.append({
                "query_id": q.query_id,
                "query_type": q.query_type,
                "query_text": q.query_text,
                "response_text": resp_text,
                "model_used": model_used,
                "created_at": q.created_at.strftime("%b %d, %Y • %I:%M %p") if q.created_at else ""
            })
        return {"history": history_list}
    finally:
        db.close()

@router.delete("/history/{query_id}")
async def delete_history_item(request: Request, query_id: int):
    """Delete a single query from user history."""
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        item = db.query(models.UserQuery).filter(
            models.UserQuery.query_id == query_id,
            models.UserQuery.user_id == user.user_id
        ).first()
        if not item:
            return JSONResponse(status_code=404, content={"error": "Item not found"})
        db.delete(item)
        db.commit()
        return {"message": "History item deleted successfully"}
    finally:
        db.close()

@router.post("/clear-history")
async def clear_all_history(request: Request):
    """Clear all study history for the logged in user."""
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        db.query(models.UserQuery).filter(models.UserQuery.user_id == user.user_id).delete()
        db.commit()
        return {"message": "All history cleared successfully"}
    finally:
        db.close()

@router.get("/stats")
async def get_study_stats(request: Request):
    """Retrieve learning statistics and counts for the user dashboard."""
    db = get_db_session()
    try:
        user = get_current_user_from_request(request, db)
        total_queries = db.query(models.UserQuery).filter(models.UserQuery.user_id == user.user_id).count()
        qa_count = db.query(models.UserQuery).filter(models.UserQuery.user_id == user.user_id, models.UserQuery.query_type == "QnA").count()
        explain_count = db.query(models.UserQuery).filter(models.UserQuery.user_id == user.user_id, models.UserQuery.query_type == "Explanation").count()
        summary_count = db.query(models.UserQuery).filter(models.UserQuery.user_id == user.user_id, models.UserQuery.query_type == "Summary").count()
        quiz_count = db.query(models.UserQuery).filter(models.UserQuery.user_id == user.user_id, models.UserQuery.query_type == "Quiz").count()
        roadmap_count = db.query(models.UserQuery).filter(models.UserQuery.user_id == user.user_id, models.UserQuery.query_type == "Recommendation").count()

        return {
            "total_queries": total_queries,
            "qa_count": qa_count,
            "explain_count": explain_count,
            "summary_count": summary_count,
            "quiz_count": quiz_count,
            "roadmap_count": roadmap_count,
            "user_name": user.name
        }
    finally:
        db.close()


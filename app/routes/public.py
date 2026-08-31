"""Public-facing routes: welcome/registration, profile, and chat."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import conversation_service
from app.services.knowledge_service import knowledge_service
from app.templating import templates

router = APIRouter()

SESSION_COOKIE_KEY = "visitor_session_id"


def get_current_session_id(request: Request) -> str | None:
    return request.session.get(SESSION_COOKIE_KEY)


@router.get("/", response_class=HTMLResponse)
def welcome(request: Request, db: Session = Depends(get_db)):
    session_id = get_current_session_id(request)
    if session_id and conversation_service.get_visitor_session(db, session_id):
        return RedirectResponse(url="/profile", status_code=302)
    return templates.TemplateResponse(request, "welcome.html", {})


@router.post("/register")
def register(
    request: Request,
    visitor_name: str = Form(...),
    company: str = Form(...),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    visitor_name = visitor_name.strip()
    company = company.strip()
    if not visitor_name or not company:
        return templates.TemplateResponse(
            request,
            "welcome.html",
            {"error": "Name and company are required."},
            status_code=400,
        )

    session = conversation_service.create_visitor_session(
        db,
        visitor_name=visitor_name,
        company=company,
        email=email,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    request.session[SESSION_COOKIE_KEY] = session.id
    return RedirectResponse(url="/profile", status_code=302)


@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    session_id = get_current_session_id(request)
    session = (
        conversation_service.get_visitor_session(db, session_id) if session_id else None
    )
    if not session:
        return RedirectResponse(url="/", status_code=302)

    knowledge_service.load()
    sections = {chunk.source for chunk in knowledge_service.chunks}
    profile_chunks = [c for c in knowledge_service.chunks if c.source == "profile"]
    resume_chunks = [c for c in knowledge_service.chunks if c.source == "resume"]
    skills_chunks = [c for c in knowledge_service.chunks if c.source == "skills"]
    education_chunks = [c for c in knowledge_service.chunks if c.source == "education"]
    projects_chunks = [c for c in knowledge_service.chunks if c.source == "projects"]
    leadership_chunks = [c for c in knowledge_service.chunks if c.source == "leadership"]

    history = conversation_service.get_conversation_history(db, session.id)

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "visitor": session,
            "sections_available": sections,
            "profile_chunks": profile_chunks,
            "resume_chunks": resume_chunks,
            "skills_chunks": skills_chunks,
            "education_chunks": education_chunks,
            "projects_chunks": projects_chunks,
            "leadership_chunks": leadership_chunks,
            "history": history,
        },
    )


@router.post("/chat")
def chat(request: Request, question: str = Form(...), db: Session = Depends(get_db)):
    session_id = get_current_session_id(request)
    session = (
        conversation_service.get_visitor_session(db, session_id) if session_id else None
    )
    if not session:
        return JSONResponse({"error": "No active session. Please register first."}, status_code=401)

    question = question.strip()
    if not question:
        return JSONResponse({"error": "Question cannot be empty."}, status_code=400)

    interaction = conversation_service.ask_question(db, session, question)
    return JSONResponse({"question": interaction.question, "answer": interaction.answer})

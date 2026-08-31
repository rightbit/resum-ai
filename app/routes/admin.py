"""Admin analytics routes.

Protected with HTTP Basic auth using credentials from environment
variables (ADMIN_USERNAME / ADMIN_PASSWORD). This is intentionally simple
per the project requirements - no user accounts, roles, or password
storage/hashing infrastructure for this first version.
"""
from __future__ import annotations

import secrets
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AIInteraction, ConversationMessage, VisitorSession
from app.templating import templates
from fastapi import HTTPException, status

router = APIRouter(prefix="/admin")
security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify HTTP Basic credentials against configured admin username/password."""
    correct_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    company: str | None = None,
    visitor_name: str | None = None,
    visit_date: str | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    stmt = select(VisitorSession).order_by(VisitorSession.started_at.desc())
    if company:
        stmt = stmt.where(VisitorSession.company.ilike(f"%{company}%"))
    if visitor_name:
        stmt = stmt.where(VisitorSession.visitor_name.ilike(f"%{visitor_name}%"))
    if visit_date:
        try:
            parsed = date.fromisoformat(visit_date)
            stmt = stmt.where(func.date(VisitorSession.started_at) == parsed.isoformat())
        except ValueError:
            pass

    sessions = list(db.scalars(stmt))

    question_counts: dict[str, int] = dict(
        db.execute(
            select(
                ConversationMessage.session_id,
                func.count(ConversationMessage.id),
            )
            .where(ConversationMessage.role == "user")
            .group_by(ConversationMessage.session_id)
        ).all()
    )

    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "sessions": sessions,
            "question_counts": question_counts,
            "filters": {
                "company": company or "",
                "visitor_name": visitor_name or "",
                "visit_date": visit_date or "",
            },
        },
    )


@router.get("/session/{session_id}", response_class=HTMLResponse)
def admin_session_detail(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    session = db.get(VisitorSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at.asc())
        )
    )
    interactions = list(
        db.scalars(
            select(AIInteraction)
            .where(AIInteraction.session_id == session_id)
            .order_by(AIInteraction.created_at.asc())
        )
    )

    return templates.TemplateResponse(
        request,
        "admin/session_detail.html",
        {"visitor": session, "messages": messages, "interactions": interactions},
    )

"""Session and conversation persistence.

Encapsulates all database writes/reads related to visitor sessions,
chat messages, and logged AI interactions so route handlers stay thin.
"""
from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIInteraction, ConversationMessage, VisitorSession
from app.services.ai_service import AIProvider, get_ai_provider
from app.services.knowledge_service import KnowledgeService, knowledge_service


def create_visitor_session(
    db: Session,
    visitor_name: str,
    company: str,
    email: str | None = None,
    user_agent: str | None = None,
    referrer: str | None = None,
) -> VisitorSession:
    """Create and persist a new visitor session."""
    session = VisitorSession(
        visitor_name=visitor_name.strip(),
        company=company.strip(),
        email=(email or "").strip() or None,
        user_agent=user_agent,
        referrer=referrer,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_visitor_session(db: Session, session_id: str) -> VisitorSession | None:
    return db.get(VisitorSession, session_id)


def touch_session(db: Session, session: VisitorSession) -> None:
    """Update last_activity_at to now."""
    from datetime import datetime, timezone

    session.last_activity_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()


def add_message(db: Session, session_id: str, role: str, content: str) -> ConversationMessage:
    message = ConversationMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversation_history(db: Session, session_id: str) -> list[ConversationMessage]:
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.created_at.asc())
    )
    return list(db.scalars(stmt))


def ask_question(
    db: Session,
    session: VisitorSession,
    question: str,
    ai_provider: AIProvider | None = None,
    knowledge: KnowledgeService | None = None,
) -> AIInteraction:
    """Answer a visitor's question and persist the full interaction.

    This is the central "ask" pipeline described in the requirements:
    retrieve relevant knowledge, build a prompt, call the AI, then store
    both the user message and the assistant's answer.
    """
    ai_provider = ai_provider or get_ai_provider()
    knowledge = knowledge or knowledge_service

    # Persist the user's question as a conversation message immediately.
    add_message(db, session.id, "user", question)

    history = get_conversation_history(db, session.id)
    prior_turns = [
        {"role": m.role, "content": m.content} for m in history[:-1]
    ]  # exclude the question we just added; provider appends it separately

    context = knowledge.build_context(question)

    start = time.monotonic()
    answer = ai_provider.generate_answer(question, context, history=prior_turns)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    add_message(db, session.id, "assistant", answer)

    interaction = AIInteraction(
        session_id=session.id,
        question=question,
        answer=answer,
        model=getattr(ai_provider, "model_name", None),
        response_time_ms=elapsed_ms,
    )
    db.add(interaction)
    touch_session(db, session)
    db.commit()
    db.refresh(interaction)
    return interaction

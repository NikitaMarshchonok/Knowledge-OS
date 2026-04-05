from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageExchangeResponse,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionRead,
)
from app.services.chat import ChatService, ChatServiceError

router = APIRouter(tags=["chat"])
service = ChatService()


@router.post("/chat/sessions", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
def create_chat_session(payload: ChatSessionCreate, db: Session = Depends(get_db)):
    try:
        return service.create_session(db, project_id=payload.project_id, title=payload.title)
    except ChatServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/chat/sessions", response_model=list[ChatSessionRead])
def list_chat_sessions(
    project_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.list_sessions(db, project_id=project_id, limit=limit)


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionDetail)
def get_chat_session(session_id: UUID, db: Session = Depends(get_db)):
    try:
        return service.get_session(db, session_id)
    except ChatServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageExchangeResponse)
def send_chat_message(session_id: UUID, payload: ChatMessageCreate, db: Session = Depends(get_db)):
    try:
        return service.send_message(db, session_id=session_id, payload=payload)
    except ChatServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

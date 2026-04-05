from uuid import UUID

from datetime import datetime, timezone
from sqlalchemy.orm import Session, selectinload

from app.models import ChatMessage, ChatMessageRole, ChatSession, Project
from app.schemas.ask import AskRequest, ConversationTurn
from app.schemas.chat import ChatMessageCreate, ChatMessageExchangeResponse
from app.services.answer_generation import AnswerGenerationError, AnswerGenerationService


class ChatServiceError(Exception):
    pass


class ChatService:
    def __init__(self) -> None:
        self.answer_service = AnswerGenerationService()

    def create_session(self, db: Session, *, project_id: UUID, title: str | None = None) -> ChatSession:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            raise ChatServiceError("Project not found")

        session = ChatSession(project_id=project_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def list_sessions(self, db: Session, *, project_id: UUID | None = None, limit: int = 50) -> list[ChatSession]:
        query = db.query(ChatSession)
        if project_id is not None:
            query = query.filter(ChatSession.project_id == project_id)
        return query.order_by(ChatSession.updated_at.desc()).limit(limit).all()

    def get_session(self, db: Session, session_id: UUID) -> ChatSession:
        session = (
            db.query(ChatSession)
            .options(selectinload(ChatSession.messages))
            .filter(ChatSession.id == session_id)
            .first()
        )
        if session is None:
            raise ChatServiceError("Chat session not found")

        session.messages.sort(key=lambda item: item.created_at)
        return session

    def send_message(self, db: Session, *, session_id: UUID, payload: ChatMessageCreate) -> ChatMessageExchangeResponse:
        session = self.get_session(db, session_id)
        user_content = payload.content.strip()
        if not user_content:
            raise ChatServiceError("Message content cannot be empty")

        user_message = ChatMessage(session_id=session.id, role=ChatMessageRole.user, content=user_content)
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        history_turns = self._build_history(session.messages + [user_message])
        ask_payload = AskRequest(
            query=user_content,
            project_id=session.project_id,
            top_k=payload.top_k,
            document_ids=payload.document_ids,
            mime_types=payload.mime_types,
            debug=payload.debug,
            conversation_history=history_turns,
        )

        try:
            ask_response = self.answer_service.ask(ask_payload, db)
        except AnswerGenerationError as exc:
            raise ChatServiceError(str(exc)) from exc

        assistant_message = ChatMessage(
            session_id=session.id,
            role=ChatMessageRole.assistant,
            content=ask_response.answer,
            ask_run_id=ask_response.ask_run_id,
        )
        db.add(assistant_message)
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assistant_message)
        db.refresh(session)

        return ChatMessageExchangeResponse(
            session=session,
            user_message=user_message,
            assistant_message=assistant_message,
            citations=ask_response.citations,
            supporting_results=ask_response.supporting_results,
        )

    def _build_history(self, messages: list[ChatMessage]) -> list[ConversationTurn]:
        turns: list[ConversationTurn] = []
        for message in messages[-8:]:
            turns.append(ConversationTurn(role=message.role.value, content=message.content))
        return turns

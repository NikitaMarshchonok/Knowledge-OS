from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Document, DocumentStatus, Project, Workspace
from app.schemas.document import DocumentRead
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectRead
from app.services.bootstrap import get_or_create_default_workspace
from app.services.storage import save_upload_file

router = APIRouter(prefix="/projects", tags=["projects"])
settings = get_settings()


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    workspace_id = payload.workspace_id
    if workspace_id is None:
        workspace = get_or_create_default_workspace(db)
        workspace_id = workspace.id
    else:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    project = Project(name=payload.name, description=payload.description, workspace_id=workspace_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(selectinload(Project.documents))
        .filter(Project.id == project_id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/{project_id}/documents/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(project_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    filename, storage_path, size_bytes = save_upload_file(file, settings.storage_dir, project_id)

    document = Document(
        project_id=project_id,
        filename=filename,
        original_name=file.filename or filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        storage_path=storage_path,
        status=DocumentStatus.uploaded,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("/{project_id}/documents", response_model=list[DocumentRead])
def list_documents(project_id: UUID, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return (
        db.query(Document)
        .filter(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
        .all()
    )

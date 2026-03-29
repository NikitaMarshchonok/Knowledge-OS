from sqlalchemy.orm import Session

from app.models import User, Workspace


def get_or_create_default_workspace(db: Session) -> Workspace:
    workspace = db.query(Workspace).first()
    if workspace:
        return workspace

    default_user = User(email="owner@knowledge.local", full_name="Workspace Owner")
    db.add(default_user)
    db.flush()

    workspace = Workspace(owner_id=default_user.id, name="Default Workspace")
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace

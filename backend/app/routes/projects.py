from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, User
from app.schemas import ProjectCreate, ProjectBriefUpdate, ProjectResponse, UserResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = Project(
        name=body.name,
        content_type=body.content_type,
        audience=body.audience,
        goal=body.goal,
        tone=body.tone,
        user_id=user_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user_result = await db.execute(select(User).where(User.id == project.user_id))
    user = user_result.scalar_one_or_none()

    response = ProjectResponse.model_validate(project)
    if user:
        response.user = UserResponse.model_validate(user)
    return response


@router.patch("/{project_id}/brief", response_model=ProjectResponse)
async def update_project_brief(
    project_id: str,
    body: ProjectBriefUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.brief_responses = body.brief_responses
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Comment
from app.schemas import CommentCreate, CommentResponse, CommentResolve

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    content_version_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    comment = Comment(
        content_version_id=content_version_id,
        user_id=user_id,
        text=body.text,
        anchor_selector=body.anchor_selector,
        parent_comment_id=body.parent_comment_id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentResponse.model_validate(comment)


@router.get("/version/{version_id}", response_model=list[CommentResponse])
async def get_comments_for_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[CommentResponse]:
    result = await db.execute(
        select(Comment)
        .where(Comment.content_version_id == version_id)
        .order_by(Comment.created_at)
    )
    comments = result.scalars().all()
    return [CommentResponse.model_validate(c) for c in comments]


@router.patch("/{comment_id}/resolve", response_model=CommentResponse)
async def resolve_comment(
    comment_id: str,
    body: CommentResolve,
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.resolved = body.resolved
    await db.commit()
    await db.refresh(comment)
    return CommentResponse.model_validate(comment)

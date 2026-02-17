from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker, get_db
from app.dependencies import get_current_user
from app.models import (
    ApprovedAsset,
    Claim,
    ComplianceRecord,
    ContentVersion,
    Project,
    content_version_assets,
    content_version_claims,
)
from app.schemas import (
    AssetSwapRequest,
    DirectEditRequest,
    EditRequest,
    EditResponse,
    GenerateRequest,
    GenerateResponse,
    RevertRequest,
    VersionResponse,
    VersionSummary,
)
from app.schemas.compliance import ComplianceCheckResponse
from app.services import llm_assembly, orchestrator

router = APIRouter(prefix="/api/content", tags=["content"])


async def _build_version_response(
    db: AsyncSession, version: ContentVersion,
) -> VersionResponse:
    claim_result = await db.execute(
        select(content_version_claims.c.claim_id).where(
            content_version_claims.c.content_version_id == version.id
        )
    )
    claim_ids = [row[0] for row in claim_result]

    asset_result = await db.execute(
        select(content_version_assets.c.approved_asset_id).where(
            content_version_assets.c.content_version_id == version.id
        )
    )
    asset_ids = [row[0] for row in asset_result]

    compliance_result = await db.execute(
        select(ComplianceRecord).where(
            ComplianceRecord.content_version_id == version.id
        )
    )
    compliance_records = list(compliance_result.scalars().all())

    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        parent_version_id=version.parent_version_id,
        version_number=version.version_number,
        html_content=version.html_content,
        edit_instruction=version.edit_instruction,
        created_at=version.created_at,
        claim_ids=claim_ids,
        asset_ids=asset_ids,
        compliance_checks=[
            ComplianceCheckResponse.model_validate(r) for r in compliance_records
        ],
    )


@router.post(
    "/{project_id}/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_content(
    project_id: str,
    request: GenerateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    result = await orchestrator.generate(
        project_id, request.claim_ids, request.asset_ids, user_id, db,
    )
    version_response = await _build_version_response(db, result["version"])
    return GenerateResponse(version=version_response)


@router.post("/{project_id}/edit", response_model=EditResponse)
async def edit_content(
    project_id: str,
    request: EditRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EditResponse:
    result = await orchestrator.edit(
        project_id, request.instruction, user_id, db,
    )
    version_response = await _build_version_response(db, result["version"])
    return EditResponse(version=version_response)


@router.post("/{project_id}/direct-edit", response_model=EditResponse)
async def direct_edit_content(
    project_id: str,
    request: DirectEditRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EditResponse:
    result = await orchestrator.direct_edit(
        project_id, request.html_content, user_id, db,
    )
    version_response = await _build_version_response(db, result["version"])
    return EditResponse(version=version_response)


@router.post("/{project_id}/swap-asset", response_model=EditResponse)
async def swap_asset(
    project_id: str,
    request: AssetSwapRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EditResponse:
    result = await orchestrator.swap_asset(
        project_id, request.old_asset_id, request.new_asset_id, user_id, db,
    )
    version_response = await _build_version_response(db, result["version"])
    return EditResponse(version=version_response)


@router.get("/{project_id}/versions", response_model=list[VersionSummary])
async def get_versions(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[VersionSummary]:
    history = await orchestrator.get_version_history(project_id, db)
    return [
        VersionSummary(
            id=v["id"],
            version_number=v["version_number"],
            edit_instruction=v["edit_instruction"],
            created_at=datetime.fromisoformat(v["created_at"]) if v["created_at"] else None,
        )
        for v in history
    ]


@router.get("/{project_id}/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    project_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> VersionResponse:
    version = await db.get(ContentVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=404, detail="Version not found")
    return await _build_version_response(db, version)


@router.post("/{project_id}/revert", response_model=VersionResponse)
async def revert_version(
    project_id: str,
    request: RevertRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VersionResponse:
    result = await orchestrator.revert_to_version(
        project_id, request.target_version_id, user_id, db,
    )
    return await _build_version_response(db, result["version"])


@router.post("/{project_id}/generate/stream")
async def generate_content_stream(
    project_id: str,
    request: GenerateRequest,
    user_id: str = Depends(get_current_user),
):
    # Manual session: DI session closes before StreamingResponse generator runs.
    async with async_session_maker() as db:
        claims_result = await db.execute(
            select(Claim).where(Claim.id.in_(request.claim_ids))
        )
        claims = [
            Claim(id=c.id, text=c.text, category=c.category)
            for c in claims_result.scalars().all()
        ]

        assets_result = await db.execute(
            select(ApprovedAsset).where(ApprovedAsset.id.in_(request.asset_ids))
        )
        assets = [
            ApprovedAsset(id=a.id, name=a.name, file_url=a.file_url)
            for a in assets_result.scalars().all()
        ]

        project_row = await db.get(Project, project_id)
        if not project_row:
            raise HTTPException(status_code=404, detail="Project not found")
        project = Project(
            id=project_row.id,
            name=project_row.name,
            tone=project_row.tone,
            audience=project_row.audience,
            goal=project_row.goal,
            brief_responses=project_row.brief_responses,
        )

    async def event_generator():
        try:
            async for chunk in llm_assembly.generate_content_stream(
                claims, assets, project,
            ):
                yield chunk
        except Exception:
            import json
            logger.exception("SSE stream error")
            yield f"data: {json.dumps({'error': 'Generation failed. Please try again.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

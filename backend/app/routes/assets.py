from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ApprovedAsset
from app.schemas import AssetResponse

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("/", response_model=list[AssetResponse])
async def list_assets(
    asset_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[AssetResponse]:
    stmt = select(ApprovedAsset)
    if asset_type is not None:
        stmt = stmt.where(ApprovedAsset.asset_type == asset_type)
    result = await db.execute(stmt)
    assets = result.scalars().all()
    return [AssetResponse.model_validate(a) for a in assets]


@router.get("/search", response_model=list[AssetResponse])
async def search_assets(
    q: str,
    db: AsyncSession = Depends(get_db),
) -> list[AssetResponse]:
    escaped = q.replace("%", "\\%").replace("_", "\\_")
    stmt = select(ApprovedAsset).where(ApprovedAsset.name.ilike(f"%{escaped}%"))
    result = await db.execute(stmt)
    assets = result.scalars().all()
    return [AssetResponse.model_validate(a) for a in assets]


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> AssetResponse:
    asset = await db.get(ApprovedAsset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.model_validate(asset)

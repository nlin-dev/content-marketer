import re

import nh3
from bs4 import BeautifulSoup
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ApprovedAsset,
    Claim,
    ContentVersion,
    EventType,
    Project,
    content_version_assets,
    content_version_claims,
)
import anthropic

from app.services import audit, compliance, llm_assembly
from app.services.claim_retrieval import search_claims


class LLMError(Exception):
    pass

ALLOWED_TAGS = {
    "div", "p", "span", "h1", "h2", "h3", "h4", "img", "table", "tr", "td",
    "th", "thead", "tbody", "ul", "ol", "li", "strong", "em", "br", "a",
    "sup", "sub",
}

ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "*": {"data-claim-id", "data-asset-id", "data-isi", "data-editable", "class", "id", "style"},
    "img": {"src", "alt"},
    "a": {"href"},
}


def sanitize_html(html: str) -> str:
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)


async def get_isi_html(db: AsyncSession) -> str:
    result = await db.execute(
        select(ApprovedAsset).where(ApprovedAsset.name == "ISI Block")
    )
    isi_asset = result.scalar_one_or_none()
    if isi_asset and isi_asset.metadata_ and "html" in isi_asset.metadata_:
        return isi_asset.metadata_["html"]
    return '<div data-isi="true" data-editable="false"><p>ISI not available.</p></div>'


async def append_isi(html: str, db: AsyncSession) -> str:
    isi_html = await get_isi_html(db)
    if 'data-isi="true"' in html:
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.find_all(attrs={"data-isi": "true"}):
            el.decompose()
        html = str(soup)
    return html + isi_html


async def _get_current_version(
    db: AsyncSession, project_id: str,
) -> ContentVersion | None:
    stmt = (
        select(ContentVersion)
        .where(ContentVersion.project_id == project_id)
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def check_version(
    db: AsyncSession, project_id: str,
) -> ContentVersion | None:
    return await _get_current_version(db, project_id)


async def create_version(
    db: AsyncSession,
    project_id: str,
    html: str,
    parent_version_id: str | None,
    version_number: int,
    edit_instruction: str | None,
    claim_ids: list[str],
    asset_ids: list[str],
) -> ContentVersion:
    version = ContentVersion(
        project_id=project_id,
        parent_version_id=parent_version_id,
        version_number=version_number,
        html_content=html,
        edit_instruction=edit_instruction,
    )
    db.add(version)
    await db.flush()

    for claim_id in claim_ids:
        await db.execute(
            content_version_claims.insert().values(
                content_version_id=version.id, claim_id=claim_id,
            )
        )
    for asset_id in asset_ids:
        await db.execute(
            content_version_assets.insert().values(
                content_version_id=version.id, approved_asset_id=asset_id,
            )
        )
    await db.flush()
    return version


async def _get_version_claims_and_assets(
    db: AsyncSession, version: ContentVersion,
) -> tuple[list[str], list[str]]:
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
    return claim_ids, asset_ids


async def discover_claims(
    query: str, db: AsyncSession, limit: int = 10,
) -> list[dict]:
    results = await search_claims(query, db, limit)
    return [{"claim": claim, "distance": distance} for claim, distance in results]


async def generate(
    project_id: str,
    claim_ids: list[str],
    asset_ids: list[str],
    user_id: str,
    db: AsyncSession,
) -> dict:
    current = await check_version(db, project_id)

    claims_result = await db.execute(select(Claim).where(Claim.id.in_(claim_ids)))
    claims = list(claims_result.scalars().all())

    assets_result = await db.execute(select(ApprovedAsset).where(ApprovedAsset.id.in_(asset_ids)))
    assets = list(assets_result.scalars().all())

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        raw_html = await llm_assembly.generate_content(claims, assets, project)
    except anthropic.APIError as exc:
        raise LLMError(str(exc)) from exc
    html = sanitize_html(raw_html)
    html = await append_isi(html, db)

    version_number = (current.version_number + 1) if current else 1
    version = await create_version(
        db, project_id, html,
        parent_version_id=current.id if current else None,
        version_number=version_number,
        edit_instruction=None,
        claim_ids=claim_ids,
        asset_ids=asset_ids,
    )

    compliance_result = await compliance.run_compliance_checks(
        html, db, version.id, claim_ids, asset_ids,
    )
    await audit.log(db, EventType.CONTENT_GENERATED, user_id, project_id, {"version_id": version.id})
    await db.commit()

    return {"version": version, "compliance": compliance_result}


async def edit(
    project_id: str,
    instruction: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    current = await check_version(db, project_id)
    if not current:
        raise HTTPException(status_code=400, detail="No existing version to edit")

    claim_ids, asset_ids = await _get_version_claims_and_assets(db, current)

    claims_result = await db.execute(select(Claim).where(Claim.id.in_(claim_ids)))
    claims = list(claims_result.scalars().all())

    assets_result = await db.execute(select(ApprovedAsset).where(ApprovedAsset.id.in_(asset_ids)))
    assets = list(assets_result.scalars().all())

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        raw_html = await llm_assembly.edit_content(
            current.html_content, instruction, claims, assets, project,
        )
    except anthropic.APIError as exc:
        raise LLMError(str(exc)) from exc
    html = sanitize_html(raw_html)
    html = await append_isi(html, db)

    version = await create_version(
        db, project_id, html,
        parent_version_id=current.id,
        version_number=current.version_number + 1,
        edit_instruction=instruction,
        claim_ids=claim_ids,
        asset_ids=asset_ids,
    )

    compliance_result = await compliance.run_compliance_checks(
        html, db, version.id, claim_ids, asset_ids,
    )
    await audit.log(db, EventType.CONTENT_EDITED, user_id, project_id, {"version_id": version.id})
    await db.commit()

    return {"version": version, "compliance": compliance_result}


async def direct_edit(
    project_id: str,
    html_content: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    current = await check_version(db, project_id)
    if not current:
        raise HTTPException(status_code=400, detail="No existing version to edit")

    claim_ids, asset_ids = await _get_version_claims_and_assets(db, current)

    html = sanitize_html(html_content)
    html = await append_isi(html, db)

    version = await create_version(
        db, project_id, html,
        parent_version_id=current.id,
        version_number=current.version_number + 1,
        edit_instruction="Direct edit",
        claim_ids=claim_ids,
        asset_ids=asset_ids,
    )

    compliance_result = await compliance.run_compliance_checks(
        html, db, version.id, claim_ids, asset_ids,
    )
    await audit.log(db, EventType.CONTENT_EDITED, user_id, project_id, {"version_id": version.id})
    await db.commit()

    return {"version": version, "compliance": compliance_result}


async def swap_asset(
    project_id: str,
    old_asset_id: str,
    new_asset_id: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    current = await check_version(db, project_id)
    if not current:
        raise HTTPException(status_code=400, detail="No existing version to edit")

    new_asset = await db.get(ApprovedAsset, new_asset_id)
    if not new_asset:
        raise HTTPException(status_code=404, detail="New asset not found")

    claim_ids, asset_ids = await _get_version_claims_and_assets(db, current)

    html = current.html_content
    html = re.sub(
        rf'data-asset-id="{re.escape(old_asset_id)}"',
        f'data-asset-id="{new_asset_id}"',
        html,
    )
    # Update img src for swapped asset
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img", attrs={"data-asset-id": new_asset_id}):
        img["src"] = new_asset.file_url
    html = str(soup)

    html = sanitize_html(html)
    html = await append_isi(html, db)

    updated_asset_ids = [
        new_asset_id if aid == old_asset_id else aid for aid in asset_ids
    ]

    version = await create_version(
        db, project_id, html,
        parent_version_id=current.id,
        version_number=current.version_number + 1,
        edit_instruction=f"Swapped asset {old_asset_id} for {new_asset_id}",
        claim_ids=claim_ids,
        asset_ids=updated_asset_ids,
    )

    compliance_result = await compliance.run_compliance_checks(
        html, db, version.id, claim_ids, updated_asset_ids,
    )
    await audit.log(db, EventType.CONTENT_EDITED, user_id, project_id, {"version_id": version.id})
    await db.commit()

    return {"version": version, "compliance": compliance_result}


async def revert_to_version(
    project_id: str,
    target_version_id: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    current = await check_version(db, project_id)

    target = await db.get(ContentVersion, target_version_id)
    if not target or target.project_id != project_id:
        raise HTTPException(status_code=404, detail="Target version not found")

    claim_ids, asset_ids = await _get_version_claims_and_assets(db, target)

    version_number = (current.version_number + 1) if current else 1
    version = await create_version(
        db, project_id, target.html_content,
        parent_version_id=current.id if current else None,
        version_number=version_number,
        edit_instruction=f"Reverted to version {target.version_number}",
        claim_ids=claim_ids,
        asset_ids=asset_ids,
    )

    compliance_result = await compliance.run_compliance_checks(
        target.html_content, db, version.id, claim_ids, asset_ids,
    )
    await audit.log(db, EventType.CONTENT_EDITED, user_id, project_id, {"version_id": version.id})
    await db.commit()

    return {"version": version, "compliance": compliance_result}


async def get_version_history(
    project_id: str, db: AsyncSession,
) -> list[dict]:
    stmt = (
        select(ContentVersion)
        .where(ContentVersion.project_id == project_id)
        .order_by(ContentVersion.version_number.desc())
    )
    result = await db.execute(stmt)
    versions = result.scalars().all()

    return [
        {
            "id": v.id,
            "version_number": v.version_number,
            "parent_version_id": v.parent_version_id,
            "edit_instruction": v.edit_instruction,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]

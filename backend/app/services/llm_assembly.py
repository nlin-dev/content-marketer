import json

import anthropic

from app.config import settings
from app.models.approved_asset import ApprovedAsset
from app.models.claim import Claim
from app.models.project import Project


def build_system_prompt(
    claims: list[Claim], assets: list[ApprovedAsset], project: Project
) -> str:
    claim_categories = {c.category.value for c in claims}
    has_efficacy = any(
        cat.startswith("efficacy") for cat in claim_categories
    )

    prompt = (
        "You are a pharmaceutical content writer specializing in email marketing.\n\n"
        "## Rules\n\n"
        "1. You MUST use each claim verbatim. Wrap every claim in a span with its ID:\n"
        '   `<span data-claim-id="{claim_id}">exact claim text</span>`\n'
        "   Do NOT paraphrase, abbreviate, or alter claim text in any way.\n\n"
        "2. Reference approved assets using img tags with their ID:\n"
        '   `<img src="{file_url}" alt="{name}" data-asset-id="{asset_id}" />`\n\n'
        "3. Output valid HTML suitable for email. No <script> tags. Use inline-friendly markup.\n\n"
    )

    if has_efficacy:
        prompt += (
            "4. FAIR BALANCE: Efficacy claims are included. You MUST present safety "
            "information proportionally. Include relevant safety claims with equal "
            "prominence.\n\n"
        )

    prompt += (
        f"## Content Parameters\n\n"
        f"- Content type: email\n"
        f"- Tone: {project.tone.value}\n"
        f"- Target audience: {project.audience.value}\n"
    )

    return prompt


def build_user_prompt(
    claims: list[Claim], assets: list[ApprovedAsset], project: Project
) -> str:
    parts: list[str] = []

    parts.append("## Approved Claims\n")
    for claim in claims:
        parts.append(f"- ID: {claim.id} | Text: {claim.text}")

    parts.append("\n## Approved Assets\n")
    for asset in assets:
        parts.append(
            f"- ID: {asset.id} | Name: {asset.name} | URL: {asset.file_url}"
        )

    parts.append(f"\n## Project Context\n")
    parts.append(f"- Name: {project.name}")
    parts.append(f"- Goal: {project.goal.value}")
    if project.brief_responses:
        parts.append(f"- Brief responses: {json.dumps(project.brief_responses)}")

    parts.append(
        "\n## Instruction\n\n"
        "Generate an HTML email body using these approved claims and assets."
    )

    return "\n".join(parts)


async def generate_content(
    claims: list[Claim],
    assets: list[ApprovedAsset],
    project: Project,
) -> str:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system_prompt = build_system_prompt(claims, assets, project)
    user_prompt = build_user_prompt(claims, assets, project)

    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


async def generate_content_stream(
    claims: list[Claim],
    assets: list[ApprovedAsset],
    project: Project,
):
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system_prompt = build_system_prompt(claims, assets, project)
    user_prompt = build_user_prompt(claims, assets, project)

    full_text = ""
    async with client.messages.stream(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        async for text in stream.text_stream:
            full_text += text
            yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

    yield f"data: {json.dumps({'type': 'complete', 'content': full_text})}\n\n"


async def edit_content(
    current_html: str,
    instruction: str,
    claims: list[Claim],
    assets: list[ApprovedAsset],
    project: Project,
) -> str:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    system_prompt = build_system_prompt(claims, assets, project) + (
        "\n\n## Editing Mode\n\n"
        "You are editing existing content. Preserve all data-claim-id and "
        "data-asset-id attributes. Only modify as instructed."
    )
    user_prompt = (
        f"## Current HTML\n\n```html\n{current_html}\n```\n\n"
        f"## Edit Instruction\n\n{instruction}\n\n"
        f"## Available Claims\n\n"
    )
    for claim in claims:
        user_prompt += f"- ID: {claim.id} | Text: {claim.text}\n"
    user_prompt += "\n## Available Assets\n\n"
    for asset in assets:
        user_prompt += (
            f"- ID: {asset.id} | Name: {asset.name} | URL: {asset.file_url}\n"
        )

    message = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text

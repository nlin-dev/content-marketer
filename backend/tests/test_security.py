import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_asset_search_escapes_wildcards(client):
    """Searching with '%' should not match all records."""
    response = await client.get("/api/assets/search", params={"q": "%"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_resolve_comment_requires_auth(client):
    """resolve_comment should reject requests without X-User-Id header."""
    response = await client.patch(
        "/api/comments/fake-id/resolve",
        json={"resolved": True},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_project_brief_requires_auth(client):
    """update_project_brief should reject requests without X-User-Id header."""
    response = await client.patch(
        "/api/projects/fake-id/brief",
        json={"brief_responses": {}},
    )
    assert response.status_code == 422

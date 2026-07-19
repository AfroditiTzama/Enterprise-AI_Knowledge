import pytest


@pytest.mark.asyncio
async def test_api_is_running(client):
    response = await client.get("/docs")

    assert response.status_code == 200
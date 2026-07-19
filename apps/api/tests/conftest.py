import pytest
from httpx import ASGITransport, AsyncClient

from knowledge_assistant.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client
import pytest_asyncio
from aiohttp.test_utils import TestClient
from pytest_aiohttp.plugin import AiohttpClient

from api.main import app_factory


def pytest_configure() -> None:
    pass


@pytest_asyncio.fixture
async def api_client(aiohttp_client: AiohttpClient, loop) -> TestClient:
    app = await app_factory()
    client = await aiohttp_client(app)
    return client

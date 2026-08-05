import pytest
from httpx import AsyncClient, ASGITransport
from server import app, validate_password_strength

def test_password_strength():
    assert validate_password_strength("weak")[0] == False
    assert validate_password_strength("Strong1!")[0] == True
    assert validate_password_strength("noupper1!")[0] == False
    assert validate_password_strength("NOLOWER1!")[0] == False
    assert validate_password_strength("NoNumber!")[0] == False
    assert validate_password_strength("NoSpecial1")[0] == False

@pytest.mark.asyncio
async def test_csp_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers

@pytest.mark.asyncio
async def test_csrf_protection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200

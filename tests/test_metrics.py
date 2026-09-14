import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_http_metrics_are_exposed() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/health/live")
        assert response.status_code == 200

        metrics_response = await client.get("/metrics")

    assert metrics_response.status_code == 200

    metrics = metrics_response.text

    assert "education_platform_http_requests_total" in metrics
    assert "education_platform_http_requests_in_progress" in metrics
    assert "education_platform_http_request_duration_seconds_bucket" in metrics

    assert 'route="/health/live"' in metrics

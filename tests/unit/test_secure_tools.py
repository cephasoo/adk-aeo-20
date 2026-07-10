import pytest
from app.agent import (
    audit_brand_aeo_visibility,
    inject_aeo_schema_metafield
)

def test_audit_brand_aeo_visibility_calculation(monkeypatch):
    # Temporarily clear env variables to force SerpAPI Mock Mode
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    # Execute AEO Citation Tracker in Mock Mode
    report = audit_brand_aeo_visibility(
        brand_name="Sonnet and Prose",
        search_query="best Shopify SEO agency"
    )

    # Assertions
    assert "AEO Citation Audit for Brand: Sonnet and Prose" in report
    assert "Share of Model (SoM)**: 50.0%" in report
    assert "Brand Citations Found**: 2" in report

def test_inject_aeo_schema_metafield_success(monkeypatch):
    # Temporarily clear env variables to force WordPress Mock Mode
    monkeypatch.delenv("WP_API_URL", raising=False)
    monkeypatch.delenv("WP_USERNAME", raising=False)
    monkeypatch.delenv("WP_APPLICATION_PASSWORD", raising=False)

    # Execute Schema Injector in Mock Mode
    report = inject_aeo_schema_metafield(
        wp_post_id=123,
        schema_type="FAQ",
        schema_json='{"@context": "https://schema.org", "@type": "FAQPage"}'
    )

    # Assertions
    assert "Success" in report
    assert "Post #123" in report

def test_telegram_webhook_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # Send a mock telegram update payload to /webhook
    payload = {
        "update_id": 999,
        "message": {
            "message_id": 1,
            "chat": {"id": 12345, "type": "private"},
            "text": "/start"
        }
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

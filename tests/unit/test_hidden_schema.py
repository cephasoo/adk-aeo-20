import pytest
from app.tools.audit_hidden_schema import audit_url, check_similarity

def test_check_similarity():
    visible = "our platform integrates fully with canvas learning management system"
    
    # Perfect match
    assert check_similarity("platform integrates fully with canvas", visible) == 1.0
    
    # Fuzzy match
    assert check_similarity("platform fully integrates with canvas", visible) >= 0.80
    
    # Completely absent
    assert check_similarity("platform integrates with blackboard support", visible) < 0.80

def test_audit_url_mock(monkeypatch):
    class MockResponse:
        status_code = 200
        content = b"""
        <html>
        <head>
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "FAQPage",
              "mainEntity": [
                {
                  "@type": "Question",
                  "name": "Does it integrate with Canvas?",
                  "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes, our platform integrates fully with canvas learning system."
                  }
                },
                {
                  "@type": "Question",
                  "name": "Is it secure?",
                  "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "The platform is not secure at all and leaks data."
                  }
                }
              ]
            }
            </script>
        </head>
        <body>
            <h1>Integrations Page</h1>
            <h2>Does it integrate with Canvas?</h2>
            <p>Yes, our platform integrates fully with canvas learning system.</p>
            <h2>Is it secure?</h2>
            <p>We take security very seriously with AES-256 encryption.</p>
        </body>
        </html>
        """
        def raise_for_status(self):
            pass

    import requests
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse())
    
    res = audit_url("http://example.com/page")
    assert res["status"] == "WARNING"
    assert res["total_faqs_in_schema"] == 2
    assert res["failed_faqs_in_schema"] == 1  # Canvas Q&A is visible, Security answer is hidden/absent
    assert res["compliance_score"] == "50.0%"

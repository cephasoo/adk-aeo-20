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

def test_audit_url_faq_mock(monkeypatch):
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
    assert res["total_fields_audited"] == 4  # 2 questions + 2 answers
    assert res["failed_fields_count"] == 1  # Canvas Q&A is visible, Security answer is hidden/absent
    assert res["compliance_score"] == "75.0%"

def test_audit_url_recipe_mock(monkeypatch):
    class MockResponse:
        status_code = 200
        content = b"""
        <html>
        <head>
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Recipe",
              "name": "Chocolate Chip Cookies",
              "recipeIngredient": [
                "1 cup butter",
                "2 cups flour",
                "1 cup chocolate chips"
              ],
              "recipeInstructions": [
                "Preheat oven to 350 degrees.",
                "Mix ingredients in a bowl.",
                "Bake for 10 minutes (secret step)."
              ]
            }
            </script>
        </head>
        <body>
            <h1>Chocolate Chip Cookies Recipe</h1>
            <h3>Ingredients</h3>
            <ul>
                <li>1 cup butter</li>
                <li>2 cups flour</li>
                <li>1 cup chocolate chips</li>
            </ul>
            <h3>Instructions</h3>
            <ol>
                <li>Preheat oven to 350 degrees.</li>
                <li>Mix ingredients in a bowl.</li>
            </ol>
        </body>
        </html>
        """
        def raise_for_status(self):
            pass

    import requests
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse())
    
    res = audit_url("http://example.com/recipe")
    assert res["status"] == "WARNING"
    assert res["total_fields_audited"] == 7  # Name + 3 ingredients + 3 instructions
    assert res["failed_fields_count"] == 1  # The secret third step is hidden
    assert res["violations"][0]["field"] == "Instruction Step"
    assert "secret step" in res["violations"][0]["expected_text"]

def test_audit_url_breadcrumb_and_review_mock(monkeypatch):
    class MockResponse:
        status_code = 200
        content = b"""
        <html>
        <head>
            <script type="application/ld+json">
            [
              {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                  {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home"
                  },
                  {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Products"
                  }
                ]
              },
              {
                "@context": "https://schema.org",
                "@type": "Review",
                "reviewBody": "This software is amazing!",
                "author": {
                  "@type": "Person",
                  "name": "John Doe"
                }
              }
            ]
            </script>
        </head>
        <body>
            <div class="breadcrumbs">
                <a href="/">Home</a> / <span class="current">Products</span>
            </div>
            <div class="testimonial">
                <blockquote>This software is amazing!</blockquote>
                <cite>- Anonymous Client</cite>
            </div>
        </body>
        </html>
        """
        def raise_for_status(self):
            pass

    import requests
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse())
    
    res = audit_url("http://example.com/multi")
    assert res["status"] == "WARNING"
    assert res["total_fields_audited"] == 4  # 2 breadcrumbs + reviewBody + reviewerName
    assert res["failed_fields_count"] == 1  # John Doe is not in body (Anonymous Client is)
    assert res["violations"][0]["schema_type"] == "Review"
    assert res["violations"][0]["field"] == "Reviewer Name"

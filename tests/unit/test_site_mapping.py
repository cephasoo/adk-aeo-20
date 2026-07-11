import pytest
from app.tools.site_mapper import discover_site_structure, map_product_lines

def test_site_mapper_calls(monkeypatch):
    # Mock requests.get
    class MockResponse:
        def __init__(self, text, status_code):
            self.text = text
            self.status_code = status_code

    def mock_get(url, *args, **kwargs):
        if "robots.txt" in url:
            return MockResponse("Sitemap: https://example.com/sitemap.xml", 200)
        elif "sitemap.xml" in url:
            return MockResponse("<sitemapindex><sitemap><loc>https://example.com/sitemap-products.xml</loc></sitemap></sitemapindex>", 200)
        else:
            # Homepage mock HTML
            html = """
            <html>
                <header>
                    <nav>
                        <a href="/products">Products</a>
                        <a href="/pricing">Pricing</a>
                    </nav>
                </header>
                <body>
                    <p>Welcome to Example</p>
                </body>
            </html>
            """
            return MockResponse(html, 200)

    monkeypatch.setattr("requests.get", mock_get)

    # Mock get_model / Gemini API
    class MockModel:
        class ApiClient:
            class Models:
                def generate_content(self, model, contents):
                    class TextObj:
                        text = "Mocked synthesized site structure tree or product table"
                    return TextObj()
            aio = None
            models = Models()
        api_client = ApiClient()
        model = "gemini-3.1-flash-lite"

    monkeypatch.setattr("app.tools.site_mapper.get_model", lambda: MockModel())

    # 1. Run discover_site_structure
    res_struct = discover_site_structure("https://example.com")
    assert "Mocked synthesized site" in res_struct

    # 2. Run map_product_lines
    res_products = map_product_lines("https://example.com")
    assert "Mocked synthesized site" in res_products

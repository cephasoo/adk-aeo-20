import pytest
import json
from app.tools.google_docs_native import (
    read_google_doc,
    create_google_doc,
    append_to_google_doc,
    update_google_doc,
    resolve_document_id
)

def test_resolve_document_id_direct():
    # Long alphanumeric ID without spaces/slashes should return immediately
    direct_id = "1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v"
    assert resolve_document_id(direct_id) == direct_id

def test_resolve_document_id_search_mock(monkeypatch):
    class MockFiles:
        def list(self, q, spaces, fields):
            assert "name = 'My Test Document'" in q
            # Returns a list containing one matching file
            class MockListRequest:
                def execute(self):
                    return {"files": [{"id": "resolved-doc-id-456", "name": "My Test Document"}]}
            return MockListRequest()

    class MockDriveService:
        def files(self):
            return MockFiles()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (None, MockDriveService()))
    
    resolved = resolve_document_id("My Test Document")
    assert resolved == "resolved-doc-id-456"

def test_read_google_doc_mock(monkeypatch):
    class MockExportRequest:
        def execute(self):
            return b"Native Python client mock content."

    class MockFiles:
        def export(self, fileId, mimeType):
            assert fileId == "test-doc-id-123"
            assert mimeType == "text/plain"
            return MockExportRequest()

    class MockDriveService:
        def files(self):
            return MockFiles()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (None, MockDriveService()))
    monkeypatch.setattr("app.tools.google_docs_native.resolve_document_id", lambda val: "test-doc-id-123")
    
    content = read_google_doc("test-doc-id-123")
    assert content == "Native Python client mock content."

def test_create_google_doc_mock(monkeypatch):
    class MockCreateRequest:
        def execute(self):
            return {"id": "created-doc-id-999"}

    class MockFiles:
        def create(self, body, fields):
            assert body["name"] == "New Document Title"
            assert body["mimeType"] == "application/vnd.google-apps.document"
            return MockCreateRequest()

    class MockDriveService:
        def files(self):
            return MockFiles()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (None, MockDriveService()))
    
    res = json.loads(create_google_doc("New Document Title"))
    assert res["status"] == "SUCCESS"
    assert res["document_id"] == "created-doc-id-999"
    assert "created-doc-id-999" in res["url"]

def test_append_google_doc_mock(monkeypatch):
    class MockExportRequest:
        def execute(self):
            return b"<html><body>Existing content.</body></html>"

    class MockUpdateRequest:
        def execute(self):
            return {"id": "test-doc-123"}

    class MockFiles:
        def export(self, fileId, mimeType):
            assert fileId == "test-doc-123"
            assert mimeType == "text/html"
            return MockExportRequest()
            
        def update(self, fileId, media_body):
            assert fileId == "test-doc-123"
            assert media_body.size() > 0
            return MockUpdateRequest()

    class MockDriveService:
        def files(self):
            return MockFiles()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (None, MockDriveService()))
    monkeypatch.setattr("app.tools.google_docs_native.resolve_document_id", lambda val: "test-doc-123")
    
    res = append_to_google_doc("test-doc-123", "Appended content.")
    assert "Successfully appended" in res

def test_update_google_doc_mock(monkeypatch):
    class MockUpdateRequest:
        def execute(self):
            return {"id": "test-doc-123"}

    class MockFiles:
        def update(self, fileId, media_body):
            assert fileId == "test-doc-123"
            # Verify media_body is uploaded
            assert media_body.size() > 0
            return MockUpdateRequest()

    class MockDriveService:
        def files(self):
            return MockFiles()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (None, MockDriveService()))
    monkeypatch.setattr("app.tools.google_docs_native.resolve_document_id", lambda val: "test-doc-123")
    
    res = update_google_doc("test-doc-123", "Replacement content with **bold** and ```mermaid\ngraph TD; A-->B;\n```.")
    assert "Successfully replaced content" in res

def test_markdown_to_html_with_mermaid():
    from app.tools.google_docs_native import markdown_to_html_with_mermaid
    md = """# Hello Title
This is **bold** text and *italic* text.

```mermaid
graph TD;
    A-->B;
    B-->C;
```

And some trailing text."""
    
    html = markdown_to_html_with_mermaid(md)
    
    # Assert standard HTML structure
    assert "<!DOCTYPE html>" in html
    assert "<h1>Hello Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    
    # Assert Mermaid block got converted to image with mermaid.ink URL and width="600"
    assert '<img width="600"' in html
    assert 'src="https://mermaid.ink/img/' in html
    assert 'alt="Mermaid Diagram"' in html


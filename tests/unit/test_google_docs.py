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
    
    html, warning = markdown_to_html_with_mermaid(md)
    
    # Assert standard HTML structure
    assert "<!DOCTYPE html>" in html
    assert "<h1>Hello Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    
    # Assert Mermaid block got converted to image with mermaid.ink URL and width="600"
    assert '<img width="600"' in html
    assert 'src="https://mermaid.ink/img/' in html
    assert 'alt="Mermaid Diagram"' in html
    assert warning == ""

def test_table_auto_repair():
    from app.tools.google_docs_native import markdown_to_html_with_mermaid
    # Missing separator row table
    md_missing = """| Header A | Header B |
| Cell A1 | Cell B1 |"""
    html, warning = markdown_to_html_with_mermaid(md_missing)
    assert "repaired" in warning
    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html

def test_table_warning():
    from app.tools.google_docs_native import markdown_to_html_with_mermaid
    # Table with pipe but invalid format (no adjacent rows with pipes)
    md_invalid = """This has a | character but it is not a table."""
    html, warning = markdown_to_html_with_mermaid(md_invalid)
    assert "WARNING: Pipe characters" in warning
    assert "<table>" not in html

def test_file_based_helpers(tmp_path, monkeypatch):
    from app.tools.google_docs_native import update_google_doc_from_file, append_to_google_doc_from_file
    
    # Write a test markdown file
    md_file = tmp_path / "test_doc.md"
    md_file.write_text("Hello from file!\n\n| H1 | H2 |\n|---|---|\n| C1 | C2 |", encoding="utf-8")
    
    # Mock Drive service and file update/export endpoints
    class MockUpdate:
        def execute(self):
            return {"id": "test-doc-123"}
            
    class MockFiles:
        def update(self, fileId, media_body):
            assert fileId == "test-doc-123"
            return MockUpdate()
        def export(self, fileId, mimeType):
            assert fileId == "test-doc-123"
            class MockExport:
                def execute(self):
                    return b"<html><body>Existing content</body></html>"
            return MockExport()

    class MockDriveService:
        def files(self):
            return MockFiles()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (None, MockDriveService()))
    monkeypatch.setattr("app.tools.google_docs_native.resolve_document_id", lambda val: "test-doc-123")
    
    # Test update from file
    res_update = update_google_doc_from_file("test-doc-123", str(md_file))
    assert "Successfully replaced content" in res_update
    
    # Test append from file
    res_append = append_to_google_doc_from_file("test-doc-123", str(md_file))
    assert "Successfully appended text" in res_append


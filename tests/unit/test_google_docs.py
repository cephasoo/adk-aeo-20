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
    class MockDocResource:
        def execute(self):
            return {
                "body": {
                    "content": [
                        {
                            "paragraph": {
                                "elements": [
                                    {"textRun": {"content": "Native Python client mock content."}}
                                ]
                            }
                        }
                    ]
                }
            }

    class MockDocuments:
        def get(self, documentId):
            assert documentId == "test-doc-id-123"
            return MockDocResource()

    class MockDocsService:
        def documents(self):
            return MockDocuments()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (MockDocsService(), None))
    
    # Bypass title resolution by providing a long valid-looking ID format
    direct_id = "1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v"
    monkeypatch.setattr("app.tools.google_docs_native.resolve_document_id", lambda val: "test-doc-id-123")
    
    content = read_google_doc(direct_id)
    assert content == "Native Python client mock content."

def test_create_google_doc_mock(monkeypatch):
    class MockDocResource:
        def execute(self):
            return {"documentId": "created-doc-id-999"}

    class MockDocuments:
        def create(self, body):
            assert body["title"] == "New Document Title"
            return MockDocResource()

    class MockDocsService:
        def documents(self):
            return MockDocuments()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (MockDocsService(), None))
    
    res = json.loads(create_google_doc("New Document Title"))
    assert res["status"] == "SUCCESS"
    assert res["document_id"] == "created-doc-id-999"
    assert "created-doc-id-999" in res["url"]

def test_append_google_doc_mock(monkeypatch):
    class MockBatchRequest:
        def execute(self):
            return {}

    class MockDocResource:
        def execute(self):
            return {
                "body": {
                    "content": [
                        {"endIndex": 50}
                    ]
                }
            }

    class MockDocuments:
        def get(self, documentId):
            return MockDocResource()
        def batchUpdate(self, documentId, body):
            assert documentId == "test-doc-123"
            requests = body["requests"]
            assert len(requests) == 1
            assert requests[0]["insertText"]["text"] == "Appended content."
            assert requests[0]["insertText"]["location"]["index"] == 49
            return MockBatchRequest()

    class MockDocsService:
        def documents(self):
            return MockDocuments()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (MockDocsService(), None))
    monkeypatch.setattr("app.tools.google_docs_native.resolve_document_id", lambda val: "test-doc-123")
    
    res = append_to_google_doc("test-doc-123", "Appended content.")
    assert "Successfully appended" in res

def test_update_google_doc_mock(monkeypatch):
    class MockBatchRequest:
        def execute(self):
            return {}

    class MockDocResource:
        def execute(self):
            return {
                "body": {
                    "content": [
                        {"endIndex": 100}
                    ]
                }
            }

    class MockDocuments:
        def get(self, documentId):
            return MockDocResource()
        def batchUpdate(self, documentId, body):
            assert documentId == "test-doc-123"
            requests = body["requests"]
            assert len(requests) == 2
            # Delete request
            assert "deleteContentRange" in requests[0]
            assert requests[0]["deleteContentRange"]["range"]["startIndex"] == 1
            assert requests[0]["deleteContentRange"]["range"]["endIndex"] == 99
            # Insert request
            assert "insertText" in requests[1]
            assert requests[1]["insertText"]["text"] == "Replacement content."
            assert requests[1]["insertText"]["location"]["index"] == 1
            return MockBatchRequest()

    class MockDocsService:
        def documents(self):
            return MockDocuments()

    monkeypatch.setattr("app.tools.google_docs_native.get_google_services", lambda: (MockDocsService(), None))
    monkeypatch.setattr("app.tools.google_docs_native.resolve_document_id", lambda val: "test-doc-123")
    
    res = update_google_doc("test-doc-123", "Replacement content.")
    assert "Successfully replaced content" in res

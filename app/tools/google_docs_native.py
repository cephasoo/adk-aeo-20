import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

def get_google_services():
    """Authenticates and returns the docs and drive API client services."""
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception:
            pass
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Google OAuth 'credentials.json' is missing in project root.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return docs_service, drive_service

def resolve_document_id(identifier: str) -> str:
    """Resolves document ID from either a direct ID or a Document Title search."""
    identifier = identifier.strip()
    # Google Doc IDs are typically 44 characters or longer, containing alphanumeric, hyphens, and underscores.
    if len(identifier) > 30 and '/' not in identifier and ' ' not in identifier:
        return identifier
        
    try:
        _, drive_service = get_google_services()
        query = f"name = '{identifier}' and mimeType = 'application/vnd.google-apps.document' and trashed = false"
        results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        if files:
            # Return the first matching file ID
            return files[0]['id']
    except Exception:
        pass
        
    return identifier

def read_google_doc(document_id_or_title: str) -> str:
    """
    Reads the textual body content of a Google Document.
    
    Args:
        document_id_or_title: The unique document ID or Title string.
    """
    try:
        document_id = resolve_document_id(document_id_or_title)
        docs_service, _ = get_google_services()
        doc = docs_service.documents().get(documentId=document_id).execute()
        
        body = doc.get('body', {})
        content = body.get('content', [])
        text_runs = []
        
        for element in content:
            if 'paragraph' in element:
                elements = element.get('paragraph', {}).get('elements', [])
                for elem in elements:
                    if 'textRun' in elem:
                        text_runs.append(elem.get('textRun', {}).get('content', ''))
                        
        return "".join(text_runs)
    except Exception as e:
        return f"Error reading document: {str(e)}"

def create_google_doc(title: str) -> str:
    """
    Creates a new Google Document and returns its URL.
    
    Args:
        title: The title of the new document.
    """
    try:
        docs_service, _ = get_google_services()
        body = {'title': title}
        doc = docs_service.documents().create(body=body).execute()
        doc_id = doc.get('documentId')
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return json.dumps({"status": "SUCCESS", "document_id": doc_id, "url": url}, indent=2)
    except Exception as e:
        return json.dumps({"status": "FAIL", "error": str(e)})

def append_to_google_doc(document_id_or_title: str, text: str) -> str:
    """
    Appends a text block to the end of a Google Document.
    
    Args:
        document_id_or_title: The target document ID or Title.
        text: The text string to append.
    """
    try:
        document_id = resolve_document_id(document_id_or_title)
        docs_service, _ = get_google_services()
        doc = docs_service.documents().get(documentId=document_id).execute()
        body = doc.get('body', {})
        content = body.get('content', [])
        end_index = 1
        if content:
            end_index = content[-1].get('endIndex', 1) - 1
            if end_index < 1:
                end_index = 1
                
        requests_list = [
            {
                'insertText': {
                    'location': {'index': end_index},
                    'text': text
                }
            }
        ]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests_list}
        ).execute()
        
        return f"Successfully appended text to document {document_id}."
    except Exception as e:
        return f"Error appending to document: {str(e)}"

def update_google_doc(document_id_or_title: str, new_content: str) -> str:
    """
    Replaces the entire body content of a Google Document with new text.
    Equivalent to a delete-all followed by insert, executed as a single
    atomic batchUpdate call.
    
    Args:
        document_id_or_title: The target document ID or Title.
        new_content: The new text content to replace the document body.
    """
    try:
        document_id = resolve_document_id(document_id_or_title)
        docs_service, _ = get_google_services()
        doc = docs_service.documents().get(documentId=document_id).execute()
        body = doc.get('body', {})
        content = body.get('content', [])
        end_index = 1
        if content:
            end_index = content[-1].get('endIndex', 1) - 1
            if end_index < 1:
                end_index = 1

        requests_list = []

        # Step 1: Delete all existing body content (if any exists beyond the mandatory newline)
        if end_index > 1:
            requests_list.append({
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': end_index
                    }
                }
            })

        # Step 2: Insert the replacement text at the beginning
        requests_list.append({
            'insertText': {
                'location': {'index': 1},
                'text': new_content
            }
        })

        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests_list}
        ).execute()

        return f"Successfully replaced content of document {document_id}."
    except Exception as e:
        return f"Error updating document: {str(e)}"

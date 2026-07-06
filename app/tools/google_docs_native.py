import os
import json
import io
import re
import base64
import markdown
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

def get_google_services():
    """Authenticates and returns the docs and drive API client services."""
    # Define unified paths
    global_token_path = r"C:\Users\USER\.gemini\gdrive-token.json"
    local_token_path = "token.json"
    
    token_path = global_token_path if os.path.exists(global_token_path) else (local_token_path if os.path.exists(local_token_path) else global_token_path)
    
    global_secrets_path = r"C:\Users\USER\.gemini\client_secrets.json"
    local_secrets_path_1 = "client_secrets.json"
    local_secrets_path_2 = "credentials.json"
    
    secrets_path = None
    for p in [global_secrets_path, local_secrets_path_1, local_secrets_path_2]:
        if os.path.exists(p):
            secrets_path = p
            break
            
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            pass
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if not secrets_path:
                raise FileNotFoundError("Google OAuth client secrets file ('client_secrets.json') is missing.")
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save to the resolved token path (creates directory if needed)
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'w') as token:
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

def markdown_to_html_with_mermaid(md_content: str) -> str:
    """
    Converts a Markdown string to standard HTML, converting Mermaid syntax
    into base64-encoded image tags targeting mermaid.ink with explicit widths.
    """
    # Find all ```mermaid ... ``` code blocks
    pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL | re.IGNORECASE)
    
    def replace_mermaid(match):
        mermaid_code = match.group(1).strip()
        # UTF-8 encode and then Base64 encode the diagram definition
        encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        img_url = f"https://mermaid.ink/img/{encoded}"
        # Force a width attribute so Google Drive fits the image to page margins on import
        return f'<p><img width="600" src="{img_url}" alt="Mermaid Diagram" /></p>'
        
    processed_md = pattern.sub(replace_mermaid, md_content)
    
    # Convert Markdown body to HTML
    html_body = markdown.markdown(processed_md, extensions=['extra', 'nl2br'])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
</head>
<body>
{html_body}
</body>
</html>"""
    return html_content

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
    Replaces the entire body content of a Google Document. Converts Markdown (and Mermaid blocks)
    to structured HTML, and updates the document contents atomically via the Google Drive API
    media update endpoint (converting the HTML structure natively into Docs styles).
    
    Args:
        document_id_or_title: The target document ID or Title.
        new_content: The new Markdown text content to replace the document body.
    """
    try:
        document_id = resolve_document_id(document_id_or_title)
        _, drive_service = get_google_services()
        
        # Convert Markdown to structured HTML with Mermaid diagram support
        html_content = markdown_to_html_with_mermaid(new_content)
        
        # Create an in-memory file payload
        fh = io.BytesIO(html_content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/html', resumable=True)
        
        # Overwrite the Google Doc with the HTML payload, which triggers conversion
        drive_service.files().update(
            fileId=document_id,
            media_body=media
        ).execute()
        
        return f"Successfully replaced content of document {document_id}."
    except Exception as e:
        return f"Error updating document: {str(e)}"

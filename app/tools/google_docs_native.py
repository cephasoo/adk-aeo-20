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
            
    drive_service = build('drive', 'v3', credentials=creds)
    return None, drive_service


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

def markdown_to_html_with_mermaid(md_content: str) -> tuple[str, str]:
    """
    Converts a Markdown string to standard HTML, converting Mermaid syntax
    into base64-encoded image tags targeting mermaid.ink with explicit widths.
    Also auto-repairs tables and checks for warnings.
    
    Returns:
        A tuple of (html_content, warning_msg)
    """
    # 1. Preprocess and auto-repair tables
    lines = md_content.splitlines()
    repaired_lines = []
    i = 0
    n = len(lines)
    repaired = False
    
    while i < n:
        line = lines[i]
        if '|' in line:
            # We found a potential table row
            if i + 1 < n and '|' in lines[i+1]:
                next_line = lines[i+1]
                # Check if next_line is a separator row
                is_separator = all(c in '|:- \t' for c in next_line.strip()) and next_line.strip().count('-') > 0
                if not is_separator:
                    # Auto-inject separator row!
                    stripped = line.strip()
                    pipe_count = stripped.count('|')
                    cols = pipe_count - 1 if (stripped.startswith('|') and stripped.endswith('|')) else pipe_count + 1
                    if cols < 1:
                        cols = 1
                    separator_row = "|" + "|".join(["---"] * cols) + "|"
                    repaired_lines.append(line)
                    repaired_lines.append(separator_row)
                    repaired = True
                    i += 1
                    continue
        repaired_lines.append(line)
        i += 1
        
    repaired_md = "\n".join(repaired_lines)
    
    # 2. Convert Mermaid blocks
    pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL | re.IGNORECASE)
    
    def replace_mermaid(match):
        mermaid_code = match.group(1).strip()
        encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        img_url = f"https://mermaid.ink/img/{encoded}"
        return f'<p><img width="600" src="{img_url}" alt="Mermaid Diagram" /></p>'
        
    processed_md = pattern.sub(replace_mermaid, repaired_md)
    
    # 3. Convert Markdown body to HTML
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
    
    # 4. Generate warnings if pipes are present but no table was generated
    warning_msg = ""
    no_code_md = re.sub(r'```.*?```', '', md_content, flags=re.DOTALL)
    no_code_md = re.sub(r'`[^`]*`', '', no_code_md)
    if '|' in no_code_md and '<table>' not in html_body:
        warning_msg = (
            "WARNING: Pipe characters ('|') were detected in the input markdown, but no HTML <table> block "
            "was generated. Please check your table formatting. Ensure you have a header row and a valid "
            "separator row (e.g., '|---|---|') directly underneath."
        )
    elif repaired:
        warning_msg = "NOTE: A markdown table was missing a separator row, which was automatically repaired."
        
    return html_content, warning_msg

def read_google_doc(document_id_or_title: str) -> str:
    """
    Reads the textual body content of a Google Document.
    
    Args:
        document_id_or_title: The unique document ID or Title string.
    """
    try:
        document_id = resolve_document_id(document_id_or_title)
        _, drive_service = get_google_services()
        # Export the document content as plain text
        content_bytes = drive_service.files().export(fileId=document_id, mimeType='text/plain').execute()
        return content_bytes.decode('utf-8')
    except Exception as e:
        return f"Error reading document: {str(e)}"

def create_google_doc(title: str, allow_duplicates: bool = False) -> str:
    """
    Creates a new Google Document and returns its URL. If a document with the
    same title already exists and allow_duplicates is False, reuses and returns
    the existing document's ID and URL instead of creating a duplicate.
    
    Args:
        title: The title of the new document.
        allow_duplicates: If True, bypasses checks and creates a new copy regardless.
    """
    try:
        _, drive_service = get_google_services()
        
        # Check for existing document if duplicates are not allowed
        if not allow_duplicates:
            try:
                query = f"name = '{title}' and mimeType = 'application/vnd.google-apps.document' and trashed = false"
                results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                files = results.get('files', [])
                if files:
                    existing_id = files[0]['id']
                    url = f"https://docs.google.com/document/d/{existing_id}/edit"
                    return json.dumps({
                        "status": "SUCCESS",
                        "document_id": existing_id,
                        "url": url,
                        "created": False,
                        "message": f"Document '{title}' already exists. Reusing existing document."
                    }, indent=2)
            except Exception:
                pass

        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document'
        }
        doc = drive_service.files().create(body=file_metadata, fields='id').execute()
        doc_id = doc.get('id')
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return json.dumps({
            "status": "SUCCESS",
            "document_id": doc_id,
            "url": url,
            "created": True
        }, indent=2)
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
        _, drive_service = get_google_services()
        
        # Export existing document content as HTML to preserve formatting
        html_bytes = drive_service.files().export(fileId=document_id, mimeType='text/html').execute()
        html_content = html_bytes.decode('utf-8')
        
        # Convert appended text to HTML (handling mermaid diagrams and tables)
        append_html, warning = markdown_to_html_with_mermaid(text)
        
        # Extract the body contents of the appended HTML and merge
        from bs4 import BeautifulSoup
        soup_orig = BeautifulSoup(html_content, 'html.parser')
        soup_append = BeautifulSoup(append_html, 'html.parser')
        
        # Append all children of the append body to the original body
        if soup_orig.body and soup_append.body:
            for child in list(soup_append.body.children):
                soup_orig.body.append(child)
        else:
            # Fallback if body tags are missing
            html_content = html_content.replace("</body>", f"{append_html}</body>")
            soup_orig = BeautifulSoup(html_content, 'html.parser')
            
        updated_html = str(soup_orig)
        
        # Write back via Drive API update
        fh = io.BytesIO(updated_html.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/html', resumable=True)
        
        drive_service.files().update(
            fileId=document_id,
            media_body=media
        ).execute()
        
        result_msg = f"Successfully appended text to document {document_id}."
        if warning:
            result_msg += f"\n\n{warning}"
        return result_msg
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
        html_content, warning = markdown_to_html_with_mermaid(new_content)
        
        # Create an in-memory file payload
        fh = io.BytesIO(html_content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/html', resumable=True)
        
        # Overwrite the Google Doc with the HTML payload, which triggers conversion
        drive_service.files().update(
            fileId=document_id,
            media_body=media
        ).execute()
        
        result_msg = f"Successfully replaced content of document {document_id}."
        if warning:
            result_msg += f"\n\n{warning}"
        return result_msg
    except Exception as e:
        return f"Error updating document: {str(e)}"

def update_google_doc_from_file(document_id_or_title: str, file_path: str) -> str:
    """
    Replaces the entire content of a Google Document with the content of a local markdown file.
    
    Args:
        document_id_or_title: The target document ID or Title.
        file_path: The absolute path to the local markdown file.
    """
    try:
        if not os.path.exists(file_path):
            return json.dumps({"status": "FAIL", "error": f"Local file not found: {file_path}"})
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        return update_google_doc(document_id_or_title, content)
    except Exception as e:
        return json.dumps({"status": "FAIL", "error": str(e)})

def append_to_google_doc_from_file(document_id_or_title: str, file_path: str) -> str:
    """
    Appends the content of a local markdown file to the end of a Google Document.
    
    Args:
        document_id_or_title: The target document ID or Title.
        file_path: The absolute path to the local markdown file.
    """
    try:
        if not os.path.exists(file_path):
            return json.dumps({"status": "FAIL", "error": f"Local file not found: {file_path}"})
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        return append_to_google_doc(document_id_or_title, content)
    except Exception as e:
        return json.dumps({"status": "FAIL", "error": str(e)})

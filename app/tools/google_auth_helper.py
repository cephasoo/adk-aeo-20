import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

def run_headless_auth(port: int = 8080):
    """
    Runs a state-synchronized OAuth 2.0 flow for Google Drive and Google Docs
    suitable for headless or agent-driven environments.
    """
    client_secrets_path = r"C:\Users\USER\.gemini\client_secrets.json"
    global_token_path = r"C:\Users\USER\.gemini\gdrive-token.json"
    local_token_path = "token.json"
    
    if not os.path.exists(client_secrets_path):
        print(f"Error: GCP client secrets file not found at {client_secrets_path}", file=sys.stderr)
        return False
        
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_path,
        scopes=SCOPES,
        redirect_uri=f'http://localhost:{port}/'
    )
    
    print(f"Starting local redirect callback server on port {port}...", flush=True)
    # run_local_server internally calls authorization_url exactly once when open_browser=False,
    # avoiding MismatchingStateError (CSRF State Mismatch).
    flow.run_local_server(port=port, open_browser=False)
    
    creds = flow.credentials
    creds_dict = {
        "type": "authorized_user",
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token
    }
    
    # Save globally
    os.makedirs(os.path.dirname(global_token_path), exist_ok=True)
    with open(global_token_path, 'w') as f:
        json.dump(creds_dict, f, indent=2)
    print(f"Token saved to global directory: {global_token_path}", flush=True)
        
    # Save locally in project root for bot tool usage
    with open(local_token_path, 'w') as f:
        json.dump(creds_dict, f, indent=2)
    print(f"Token copied to local project: {local_token_path}", flush=True)
    
    return True

if __name__ == '__main__':
    # Force unbuffered stdout if run as main script
    sys.stdout.reconfigure(line_buffering=True)
    run_headless_auth()

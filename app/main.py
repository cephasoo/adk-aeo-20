import os
import sys
import time
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv

# Add the project root folder to Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env variables from .env file
load_dotenv()

# Import our Gutenberg AEO agent workflow and the ADK runner
from app.agent import root_agent
from google.adk.runners import InMemoryRunner

# Instantiate the runner globally
runner = InMemoryRunner(agent=root_agent, app_name="app")
runner.auto_create_session = True

app = FastAPI(title="Gutenberg AEO Copilot Telegram Webhook")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

def markdown_to_html(text: str) -> str:
    """Converts basic markdown formatting to HTML for Telegram parsing."""
    import re
    import html

    # 1. Protect markdown links [text](url) by extracting them
    links = []
    def save_link(match):
        links.append(match.groups())
        return f"___LINK_PLACEHOLDER_{len(links)-1}___"

    t = re.sub(r'\[(.*?)\]\((.*?)\)', save_link, text)

    # 2. Escape HTML special characters for the rest of the text
    t = html.escape(t)

    # 3. Restore links as HTML <a> tags
    for idx, (link_text, url) in enumerate(links):
        escaped_link_text = html.escape(link_text)
        # Escape quotes in URL to prevent attribute injection
        safe_url = url.replace('"', '&quot;')
        t = t.replace(f"___LINK_PLACEHOLDER_{idx}___", f'<a href="{safe_url}">{escaped_link_text}</a>')

    # 4. Convert bold **text** to <b>text</b>
    t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t)
    # 5. Convert bold __text__ to <b>text</b>
    t = re.sub(r'__(.*?)__', r'<b>\1</b>', t)
    # 6. Convert inline code `code` to <code>code</code>
    t = re.sub(r'`(.*?)`', r'<code>\1</code>', t)

    # 7. Parse bulleted lists: convert starting '* ' and '- ' to clean, indent-aligned unicode bullet points '• '
    lines = []
    for line in t.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('* ') or stripped.startswith('- '):
            indent = len(line) - len(stripped)
            line = ' ' * indent + '• ' + stripped[2:]
        lines.append(line)
    t = '\n'.join(lines)

    # 8. Parse italics: convert _text_ to <i>text</i> and *text* to <i>text</i> safely
    t = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', t)
    t = re.sub(r'(?<!_)_(?!_)(.*?)(?<!_)_(?!_)', r'<i>\1</i>', t)

    # 9. Parse block quotes: convert > text to <blockquote>text</blockquote>
    lines = []
    for line in t.split('\n'):
        if line.startswith('&gt; '):
            line = f"<blockquote>{line[5:]}</blockquote>"
        elif line.startswith('&gt;'):
            line = f"<blockquote>{line[4:]}</blockquote>"
        lines.append(line)
    t = '\n'.join(lines)

    return t

def send_telegram_message(chat_id: int, text: str):
    """Sends a formatted text message back to the Telegram chat, chunking if necessary."""
    if not TOKEN:
        print(f"[MOCK SEND] Chat ID: {chat_id} | Msg: {text}")
        return

    # Split the message into chunks if it is too long (limit is 4096, we use 3800 to be safe with HTML tags)
    chunks = []
    current_chunk = []
    current_length = 0
    in_code_block = False
    code_block_lang = ""

    for line in text.split('\n'):
        # Track code block status to handle split code blocks nicely
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                code_block_lang = line.strip()[3:]
            else:
                code_block_lang = ""

        # Estimate line length (add 1 for the newline character)
        line_len = len(line) + 1
        if current_length + line_len > 3800:
            # Close code block if open in this chunk
            if in_code_block:
                current_chunk.append("```")
            chunks.append("\n".join(current_chunk))

            # Start new chunk
            current_chunk = []
            # Re-open code block in next chunk if it was split
            if in_code_block:
                current_chunk.append(f"```{code_block_lang}")
            current_chunk.append(line)
            current_length = sum(len(l) + 1 for l in current_chunk)
        else:
            current_chunk.append(line)
            current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    url = f"{TELEGRAM_API_URL}/sendMessage"

    for chunk in chunks:
        html_text = markdown_to_html(chunk)
        payload = {
            "chat_id": chat_id,
            "text": html_text,
            "parse_mode": "HTML"
        }
        try:
            print(f"[*] Sending message chunk to Telegram chat {chat_id}...")
            response = requests.post(url, json=payload, timeout=10)

            # If HTML rendering fails, fallback to plain text
            if response.status_code != 200:
                print(f"[!] Telegram API warning (status {response.status_code}): {response.text}")
                print("[*] Retrying chunk in plain text mode...")
                payload["text"] = chunk  # Use raw unescaped text
                payload.pop("parse_mode", None)
                retry_resp = requests.post(url, json=payload, timeout=10)
                if retry_resp.status_code == 200:
                    print("[*] Telegram message chunk delivered successfully in plain text mode.")
                else:
                    print(f"[!] Telegram API error on retry (status {retry_resp.status_code}): {retry_resp.text}")
            else:
                print("[*] Telegram message chunk delivered successfully.")
        except Exception as e:
            print(f"Error sending message chunk to Telegram: {e}")

# Initialize Firestore Client if configured, fallback to None if ADC credentials are missing
db = None
try:
    from google.cloud import firestore
    db = firestore.Client()
    print("[*] Google Cloud Firestore client initialized successfully.")
except Exception as e:
    print(f"[*] Firestore initialization skipped or failed: {e}. Session persistence will run in-memory only.")

def restore_telegram_session(chat_id: int, app_name: str, session_id: str):
    """Restores the conversation session from Firestore if it exists."""
    if db is None:
        return
    try:
        user_id = str(chat_id)
        doc_ref = db.collection("telegram_sessions").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            sess_json = data.get("session_json")
            if sess_json:
                from google.adk.sessions import Session
                sess = Session.model_validate_json(sess_json)
                # Inject the session directly into the runner's session service storage
                if app_name not in runner.session_service.sessions:
                    runner.session_service.sessions[app_name] = {}
                if user_id not in runner.session_service.sessions[app_name]:
                    runner.session_service.sessions[app_name][user_id] = {}
                runner.session_service.sessions[app_name][user_id][session_id] = sess
                print(f"[*] Restored long-term session context for chat ID {chat_id} from Firestore.")
    except Exception as e:
        print(f"[!] Warning: Failed to restore session from Firestore: {e}")

def prune_session_history_with_summary(sess, max_turns: int = 7):
    """Groups events by invocation_id. Summarizes excess turns recursively using Gemini and prepends as context."""
    if not sess.events:
        return sess

    import uuid
    from google.adk.events import Event

    # Group events by invocation_id while preserving chronological order
    groups = []
    current_id = None
    current_group = []

    # Filter out existing summary turns during the grouping step
    active_events = [e for e in sess.events if e.invocation_id != "historical_summary"]
    existing_summary_event = next((e for e in sess.events if e.invocation_id == "historical_summary" and e.author == "user"), None)
    old_summary = existing_summary_event.output.replace("[System Summary of earlier turns: ", "").rstrip("]") if existing_summary_event else None

    for event in active_events:
        inv_id = getattr(event, "invocation_id", None) or ""
        if inv_id != current_id:
            if current_group:
                groups.append(current_group)
            current_group = [event]
            current_id = inv_id
        else:
            current_group.append(event)
    if current_group:
        groups.append(current_group)

    # If the number of unique invocation groups exceeds max_turns, summarize the excess ones
    if len(groups) > max_turns:
        excess_groups = groups[:-max_turns]
        keep_groups = groups[-max_turns:]

        # Serialize excess logs for summarization
        log_lines = []
        for g in excess_groups:
            for e in g:
                log_lines.append(f"{e.author}: {e.output[:300] if e.output else ''}")
        excess_logs = "\n".join(log_lines)

        # Call model to summarize
        from app.agent import model
        prompt = f"Summarize the following conversation logs and tool interactions in under 50 words: \n{excess_logs}"
        
        # If we have an old summary, recursively merge it
        if old_summary:
            prompt = (
                f"Merge the following existing summary and the new logs into a single cohesive summary under 50 words:\n"
                f"Existing: {old_summary}\n"
                f"New Logs:\n{excess_logs}"
            )

        try:
            summary_text = ""
            # Call model synchronously (since we are running inside the polling handler thread)
            response = model.api_client.models.generate_content(model=model.model, contents=prompt)
            summary_text = response.text.strip()
        except Exception as e:
            print(f"[!] Warning: Failed to generate conversation summary: {e}")
            summary_text = old_summary or "Earlier logs pruned."

        # Construct the special summary turn events
        summary_event_user = Event(
            id=str(uuid.uuid4()),
            invocation_id="historical_summary",
            author="user",
            output=f"[System Summary of earlier turns: {summary_text}]"
        )
        summary_event_agent = Event(
            id=str(uuid.uuid4()),
            invocation_id="historical_summary",
            author="GutenbergAeoCopilot",
            output="Acknowledged. I will retain this context."
        )

        # Re-compile events: summary turn + kept turns
        pruned_events = [summary_event_user, summary_event_agent]
        for g in keep_groups:
            pruned_events.extend(g)
        sess.events = pruned_events
        print(f"[*] Pruned session: summarized {len(excess_groups)} turns. Retained last {max_turns} turns.")

    return sess

def save_telegram_session(chat_id: int, app_name: str, session_id: str):
    """Saves the conversation session back to Firestore."""
    if db is None:
        return
    try:
        user_id = str(chat_id)
        if app_name in runner.session_service.sessions:
            if user_id in runner.session_service.sessions[app_name]:
                sess = runner.session_service.sessions[app_name][user_id].get(session_id)
                if sess:
                    # Prune history using recursive summarization (keep last 7 turns raw)
                    sess = prune_session_history_with_summary(sess, max_turns=7)
                    sess_json = sess.model_dump_json()
                    doc_ref = db.collection("telegram_sessions").document(user_id)
                    doc_ref.set({"session_json": sess_json, "updated_at": firestore.SERVER_TIMESTAMP})
                    print(f"[*] Successfully persisted updated session context for chat ID {chat_id} to Firestore.")
    except Exception as e:
        print(f"[!] Warning: Failed to persist session to Firestore: {e}")

def handle_incoming_message(chat_id: int, text: str):
    """Feeds incoming Telegram commands to the ADK agent and returns responses."""
    text_clean = text.strip()

    # Simple direct greeting check
    if text_clean.startswith("/start"):
        welcome_text = (
            "👋 **Welcome to the Gutenberg AEO Copilot Bot!**\n\n"
            "I am an autonomous agent equipped with frontier-class SEO and AEO auditing capabilities.\n\n"
            "**Available Actions:**\n"
            "- `/audit <post_id_or_url>`: Run a 19-rule rendered technical SEO and AEO audit.\n"
            "- `/track <url> | <query>`: Track Google search organic position and SERP features.\n"
            "- `/aeo <url> | <query>`: Check AI Overview citation and calculate Share of Model (SoM).\n"
            "- `/redirect <url>`: Analyze redirect chains, hops, and loops.\n"
            "- `/canonical <urls_list>`: Check canonical tag paths and duplicate cannibalization.\n"
            "- `/schema <post_id> | <type>`: Generate and inject JSON-LD schemas into your WP post metadata.\n"
            "- `/gsc <url>`: Check Search Console indexing and performance metrics (authenticated properties only)."
        )
        send_telegram_message(chat_id, welcome_text)
        return

    if text_clean.startswith("/login"):
        parts = text_clean.split(None, 1)
        if len(parts) < 2:
            send_telegram_message(chat_id, "🔒 **Usage**: `/login <developer_secret_key_or_token>`")
            return

        token_or_key = parts[1].strip()
        dev_key = os.environ.get("DEVELOPER_SECRET_KEY")

        if dev_key and token_or_key == dev_key:
            # Generate a mock developer JWT token
            import jwt
            import datetime
            payload = {
                "sub": str(chat_id),
                "scopes": ["site:write", "gsc_read"],
                "verified_properties": ["aeo-copilot.local", "localhost", "127.0.0.1", "travelanders.com"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }
            token = jwt.encode(payload, dev_key, algorithm="HS256")

            # Store session JWT
            from app.tools.seo_tools import set_user_session
            set_user_session(str(chat_id), token)

            send_telegram_message(
                chat_id,
                "🔒 **Login Successful!**\n\nDeveloper JWT session initialized with scope `site:write` (valid for 24 hours)."
            )
        else:
            # Parse as standard JWT
            try:
                import jwt
                if dev_key:
                    # In a production context, verify using issuer key. Here we decode via dev_key
                    claims = jwt.decode(token_or_key, dev_key, algorithms=["HS256"])
                    from app.tools.seo_tools import set_user_session
                    set_user_session(str(chat_id), token_or_key)
                    send_telegram_message(chat_id, "🔒 **Login Successful!**\n\nOAuth JWT session verified and registered.")
                else:
                    send_telegram_message(chat_id, "❌ Error: DEVELOPER_SECRET_KEY is not configured in .env.")
            except Exception as e:
                send_telegram_message(chat_id, f"❌ Invalid authentication token: {e}")
        return

    # Trigger the ADK Agent reasoning engine
    try:
        app_name = runner.app_name
        session_id = f"session_{chat_id}"

        # Restore session context from Firestore if available
        restore_telegram_session(chat_id, app_name, session_id)

        print(f"[*] Dispatching prompt to ADK Agent: '{text_clean}'")

        # Format user input for ADK GenAI types
        from google.genai import types
        new_msg = types.Content(role="user", parts=[types.Part.from_text(text=text_clean)])

        # Run the workflow using the runner
        response_events = runner.run(
            user_id=str(chat_id),
            session_id=session_id,
            new_message=new_msg
        )

        # Parse events to find final output text
        reply_content = ""
        for event in response_events:
            if event.is_final_response():
                parts = event.content.parts if hasattr(event, "content") and hasattr(event.content, "parts") else []
                if parts:
                    reply_content = parts[0].text

        if not reply_content:
            reply_content = "Agent finished execution but returned no output."

        send_telegram_message(chat_id, reply_content)

        # Persist updated session context to Firestore
        save_telegram_session(chat_id, app_name, session_id)
    except Exception as e:
        error_msg = f"❌ Error during agent execution: {e}"
        print(error_msg, file=sys.stderr)
        send_telegram_message(chat_id, error_msg)

@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Endpoint for webhook mode (used in production hosting)."""
    data = await request.json()
    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text")

    if chat_id and text:
        background_tasks.add_task(handle_incoming_message, chat_id, text)

    return {"status": "ok"}

def run_polling():
    """Polls Telegram API for new messages (used for local development)."""
    if not TOKEN:
        print("[!] Error: TELEGRAM_BOT_TOKEN missing from environment variables.")
        sys.exit(1)

    # Register native Telegram menu commands
    commands = [
        {"command": "start", "description": "Welcome and command overview"},
        {"command": "login", "description": "Authenticate session with developer JWT secret"},
        {"command": "audit", "description": "Audit WordPress post or URL for SEO/AEO"},
        {"command": "track", "description": "Track query organic ranking positioning"},
        {"command": "aeo", "description": "Check SGE/AI Overview Share of Model"},
        {"command": "redirect", "description": "Analyze HTTP redirect chains"},
        {"command": "canonical", "description": "Verify canonical links and duplication"},
        {"command": "schema", "description": "Generate and inject schema markup"},
        {"command": "gsc", "description": "Check Google Search Console index status"}
    ]
    try:
        print("[*] Registering native bot commands on Telegram...")
        requests.post(f"{TELEGRAM_API_URL}/setMyCommands", json={"commands": commands}, timeout=10)
    except Exception as e:
        print(f"[!] Warning: Failed to register commands: {e}")

    print("[*] Starting Telegram Bot in local POLLING mode...")
    print("[*] Press Ctrl+C to stop.")

    offset = 0
    while True:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates"
            response = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25)
            if response.status_code == 200:
                updates = response.json().get("result", [])
                for update in updates:
                    update_id = update.get("update_id", 0)
                    offset = update_id + 1

                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    text = message.get("text")

                    if chat_id and text:
                        handle_incoming_message(chat_id, text)
            else:
                print(f"[!] Error fetching updates: Status code {response.status_code}")
        except KeyboardInterrupt:
            print("\n[*] Stopping polling mode.")
            break
        except Exception as e:
            print(f"[!] Error in polling loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # If file run directly, default to local polling mode
    run_polling()

# Gutenberg AEO Copilot: Staging & Setup Guide

This guide details the step-by-step instructions to configure your local WordPress environment, register your Telegram Bot, and map your credentials.

---

## Step 1: Local WordPress Staging Setup

Since you do not have an active staging instance, we will configure a local sandbox.

### Recommended Method: LocalWP (Easiest)
1.  Download and install **[LocalWP](https://localwp.com/)** (free for Windows).
2.  Click **Create a New Site** -> select **Create a new site from scratch**.
3.  Name your site: `aeo-copilot` (this maps locally to `http://aeo-copilot.local`).
4.  Set up your Admin credentials (e.g., username: `admin`, password: `yourpassword`).
5.  Once the site starts, click **Go to Admin** to access the dashboard.

### Configure Gutenberg & Clean Performance Settings
To align with our [Gutenberg Technical SEO Blueprint](file:///C:/Users/USER/.gemini/antigravity/brain/e3819422-7215-4bb2-b9a2-79dcc51f38fc/gutenberg_technical_seo_guide.md):
1.  In WordPress Admin, go to **Appearance -> Themes** and ensure a default block theme (like **Twenty Twenty-Four** or **GeneratePress**) is active.
2.  Open your active theme's `functions.php` file (or use a code snippets plugin) and add the following line to enforce separate style enqueuing:
    ```php
    add_filter( 'should_load_separate_core_block_assets', '__return_true' );
    ```

### Generate WordPress REST API Credentials
The ADK agent interacts with Gutenberg via the secure REST API using **Application Passwords**:
1.  Go to **Users -> Profile** in your WordPress Admin sidebar.
2.  Scroll down to the **Application Passwords** section.
3.  Enter a name for the app: `Antigravity Copilot` and click **Add New Application Password**.
4.  Copy the generated 24-character password string (e.g., `xxxx xxxx xxxx xxxx xxxx xxxx`). **Do not close the tab until you copy it.**

---

## Step 2: Telegram Bot Registration

We will use the free Telegram Bot API to handle chatbot queries.

1.  Open the Telegram app and search for the verified **`@BotFather`** account.
2.  Click **Start** and send the command:
    ```text
    /newbot
    ```
3.  Follow the prompts:
    *   Give your bot a name (e.g., `Gutenberg AEO Copilot`).
    *   Give your bot a unique username ending in `bot` (e.g., `gutenberg_aeo_copilot_bot`).
4.  BotFather will reply with a confirmation message containing your **HTTP API Token** (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Copy this token.

---

## Step 3: Configure Environment Variables

Create a file named `.env` in the root of your project directory (`C:\Users\USER\secure-agent-lab\gutenberg-aeo-copilot\.env`) and fill in your keys:

```bash
# Model & Analytics Credentials
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_MODEL="gemini-3.5-flash"
GOOGLE_CLOUD_PROJECT="your-google-cloud-project-id"

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"

# WordPress REST API Credentials
WP_API_URL="http://your-wordpress-domain.local/wp-json/wp/v2"
WP_USERNAME="your-wordpress-username"
WP_APPLICATION_PASSWORD="your-wordpress-application-password"

# Search & AEO Audit Credentials
SERPAPI_API_KEY="your-serpapi-api-key"

# Oauth2 Credentials for developer signature bypassing
DEVELOPER_SECRET_KEY="your-developer-secret-key"
```

---

## Step 4: Google Search Console (GSC) Audit Mode

The `/gsc` command inspects URL indexation, mobile usability, CTR metrics, and search queries. It supports two modes:

### 1. Demo / Mock Mode (Default Local Setup)
* If `GSC_MCP_COMMAND` is not defined in your `.env` file, the bot automatically falls back to **Demo Mode**.
* In this mode, running `/gsc <url>` will immediately output fully populated, clean mock reports. This allows you to demo and test the full Search Console command set locally without configuring complex OAuth connections.

### 2. Production Mode (VPS / Live Deployment)
* When deployed live, users authenticate securely using **Google OAuth 2.0**.
* You configure the GSC MCP command in your VPS `.env` pointing to the Search Console server executable (e.g., `npx -y @google/search-console-mcp`).
* Users run `/login` in Telegram, sign in via their Google Account in the browser, and the bot securely queries their real Search Console properties on their behalf using their OAuth access token.

```

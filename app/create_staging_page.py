import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

wp_url = os.environ.get("WP_API_URL")
wp_username = os.environ.get("WP_USERNAME")
wp_password = os.environ.get("WP_APPLICATION_PASSWORD")

# Clean the password (remove spaces)
if wp_password:
    wp_password_clean = wp_password.replace(" ", "")
else:
    wp_password_clean = ""

print(f"Connecting to WordPress REST API: {wp_url}")
print(f"Authenticating as user: '{wp_username}'")

# Gutenberg Block HTML for a lean landing page
gutenberg_content = """<!-- wp:heading {"level":1} -->
<h1>Ultimate Guide to eCommerce Growth</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Welcome to our landing page. This page outlines advanced strategies for scaling Shopify and WooCommerce store traffic organic model visibility.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Why SEO Matters for eCommerce</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Organic search remains the highest-converting marketing channel for digital brands globally.</p>
<!-- /wp:paragraph -->

<!-- wp:image {"sizeSlug":"full","linkDestination":"none"} -->
<figure class="wp-block-image size-full"><img src="http://example.com/growth-chart.png" alt="" /></figure>
<!-- /wp:image -->

<!-- wp:heading {"level":4} -->
<h4>Skip-Level Heading Warning</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This section is nested under an H4 instead of an H3, which will trigger an SEO hierarchy warning.</p>
<!-- /wp:paragraph -->"""

post_data = {
    "title": "AEO Staging Landing Page",
    "content": gutenberg_content,
    "status": "draft"
}

try:
    # Use Basic Authentication with username and application password
    response = requests.post(
        f"{wp_url}/posts",
        auth=(wp_username, wp_password_clean),
        json=post_data,
        timeout=10
    )
    if response.status_code == 201:
        created_post = response.json()
        print("\n" + "="*50)
        print("🎉 SUCCESS! Created mock Gutenberg page successfully.")
        print(f" - Post ID: {created_post.get('id')}")
        print(f" - Title: {created_post.get('title', {}).get('rendered')}")
        print(f" - Status: {created_post.get('status')}")
        print(f" - Link: {created_post.get('link')}")
        print("="*50)
        print(f"\n👉 You can now run '/audit {created_post.get('id')}' in your Telegram bot!")
    else:
        print("\n❌ FAILED to create post.")
        print(f" - HTTP Status: {response.status_code}")
        print(f" - Response Body: {response.text}")
        print("\n💡 Tip: Please check that your username and Application Password (not your dashboard login password) are correct in your .env file.")
except Exception as e:
    print(f"\n❌ Connection Error: {e}")

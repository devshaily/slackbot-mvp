import os
import uuid
import threading
from dotenv import load_dotenv
from flask import Flask, request, send_file, abort, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError

import pipeline
from report import build_pdf

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DOWNLOAD_TOKEN = os.getenv("DOWNLOAD_TOKEN", "change-me")

# Initialize Flask and Slack apps
flask_app = Flask(__name__)
slack_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
handler = SlackRequestHandler(slack_app)

# Simple in-memory storage
STATE = {}

# Health check endpoints
@flask_app.get("/")
def health():
    return jsonify({"status": "ok"})

@flask_app.get("/healthz")
def render_health():
    return jsonify({"status": "ok"})

# Main processing function (runs in background)
def process_keywords_async(channel_id, user_id, text):
    """
    This runs in a separate thread so Slack doesn't timeout
    """
    try:
        # Clean and process keywords
        cleaned = pipeline.clean_keywords(text)
        groups = pipeline.simple_group(cleaned)
        
        # Generate outlines and post ideas
        outlines = {}
        post_ideas = {}
        
        for g in groups:
            outlines[g['label']] = pipeline.fake_outline(g['label'], g['items'])
            post_ideas[g['label']] = pipeline.generate_post_ideas(g['label'], g['items'])
        
        # Create PDF report
        slug = uuid.uuid4().hex
        pdf_path = build_pdf(slug, cleaned, groups, outlines, post_ideas)
        
        # Store results
        STATE[slug] = {
            'pdf_path': pdf_path,
            'cleaned': cleaned,
            'groups': groups,
            'outlines': outlines,
            'post_ideas': post_ideas,
            'user_id': user_id,
            'channel_id': channel_id,
        }
        
        # Generate download URL
        download_url = f"{BASE_URL}/download/{slug}?token={DOWNLOAD_TOKEN}"
        
        # Build Slack message blocks
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "✅ Keyword Processing Complete"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Total keywords processed:* {len(cleaned)}"}},
            {"type": "divider"}
        ]
        
        # Add each group
        for g in groups:
            keywords_preview = ", ".join(g['items'][:5])
            if len(g['items']) > 5:
                keywords_preview += "..."
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{g['label'].upper()}* ({len(g['items'])} keywords)\n`{keywords_preview}`"
                }
            })
        
        # Add download link
        blocks.extend([
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"📄 *Download Report:* <{download_url}|Click here to download PDF>"}}
        ])
        
        # Send result to Slack
        slack_app.client.chat_postMessage(
            channel=channel_id,
            text="Keyword processing complete!",
            blocks=blocks
        )
        
    except Exception as e:
        # If something goes wrong, notify the user
        error_msg = f"Sorry, something went wrong: {str(e)}"
        try:
            slack_app.client.chat_postMessage(
                channel=channel_id,
                text=error_msg
            )
        except:
            print(f"Failed to send error message: {e}")

# Slack command handler
@slack_app.command("/keywords")
def handle_keywords(ack, body, respond):
    # IMPORTANT: Acknowledge immediately (within 3 seconds)
    ack("🔄 Processing your keywords... I'll post results here in a moment!")
    
    # Get request details
    channel_id = body.get("channel_id")
    user_id = body.get("user_id")
    text = (body.get("text") or "").strip()
    
    # Validate input
    if not text:
        respond("❌ Please provide keywords after the command.\n*Example:* `/keywords ai marketing, content automation, seo optimization`")
        return
    
    # Start processing in background thread
    thread = threading.Thread(
        target=process_keywords_async,
        args=(channel_id, user_id, text)
    )
    thread.start()

# Download endpoint
@flask_app.get("/download/<slug>")
def download(slug):
    # Check token
    token = request.args.get("token")
    if token != DOWNLOAD_TOKEN:
        abort(401)
    
    # Get report data
    data = STATE.get(slug)
    if not data:
        abort(404)
    
    # Send file
    return send_file(data['pdf_path'], as_attachment=True)

# Slack events endpoint
@flask_app.post("/slack/events")
def slack_events():
    return handler.handle(request)

# For slash commands specifically
@flask_app.post("/slack/commands")
def slack_commands():
    return handler.handle(request)

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False)
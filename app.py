import os
import uuid
from dotenv import load_dotenv
from flask import Flask, request, send_file, abort, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError


import pipeline
from report import build_pdf

# -----------------
# Environment Setup
# -----------------
load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DOWNLOAD_TOKEN = os.getenv("DOWNLOAD_TOKEN", "change-me")

# Flask + Slack Bolt
flask_app = Flask(__name__)
slack_app = App(token=os.getenv("SLACK_BOT_TOKEN"), signing_secret=os.getenv("SLACK_SIGNING_SECRET"))
handler = SlackRequestHandler(slack_app)


# In-memory storage (no DB for MVP)
STATE = {}

# -----------------
# Health check route
# -----------------
@flask_app.get("/")
def health():
    return jsonify({"status": "ok"})


# -----------------
# Slack command: /keywords
# -----------------
@slack_app.command("/keywords")
def handle_keywords(ack, body, respond):
    ack()
    channel_id = body.get("channel_id")
    user_id = body.get("user_id")
    text = (body.get("text") or "").strip()

    if not text:
        respond("Please paste keywords after the command. Example: `/keywords ai marketing, content automation, ad optimization`")
        return

    # Step 1–3: clean + group + outline
    cleaned = pipeline.clean_keywords(text)
    groups = pipeline.simple_group(cleaned)
    outlines = {g['label']: pipeline.fake_outline(g['label'], g['items']) for g in groups}

    # Step 5: PDF report
    slug = uuid.uuid4().hex
    pdf_path = build_pdf(slug, cleaned, groups, outlines)

    STATE[slug] = {
        'pdf_path': pdf_path,
        'cleaned': cleaned,
        'groups': groups,
        'outlines': outlines,
        'user_id': user_id,
        'channel_id': channel_id,
    }

    download_url = f"{BASE_URL}/download/{slug}?token={DOWNLOAD_TOKEN}"

    # Step 4 & Slack output
    block_lines = [
        {"type": "header", "text": {"type": "plain_text", "text": "Keyword Batch – Results"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Cleaned keywords:* {len(cleaned)}"}},
        {"type": "divider"}
    ]

    for g in groups:
        block_lines.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{g['label']}* – {len(g['items'])} items\n`" + ", ".join(g['items'][:10]) + (" …" if len(g['items']) > 10 else "") + "`"
            }
        })

    block_lines.extend([
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"📄 *Report:* <{download_url}|Download PDF>"}}
    ])

    try:
        slack_app.client.chat_postMessage(
            channel=channel_id,
            text="Keyword batch processed",
            blocks=block_lines
        )
    except SlackApiError as e:
        # Handle case where bot isn't yet in the channel
        if e.response["error"] == "not_in_channel":
            try:
                slack_app.client.conversations_join(channel=channel_id)
                slack_app.client.chat_postMessage(
                    channel=channel_id,
                    text="Keyword batch processed",
                    blocks=block_lines
                )
            except Exception as join_err:
                print("Failed to auto-join or post:", join_err)
        else:
            print("Slack API Error:", e.response)



# -----------------
# Flask download route
# -----------------
@flask_app.get("/download/<slug>")
def download(slug):
    token = request.args.get("token")
    if token != DOWNLOAD_TOKEN:
        abort(401)
    data = STATE.get(slug)
    if not data:
        abort(404)
    return send_file(data['pdf_path'], as_attachment=True)


# -----------------
# Slack Events Endpoint
# -----------------
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # Step 1: Handle Slack URL verification challenge
    data = request.get_json()
    if data and "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Step 2: Pass normal events to Slack Bolt handler
    return handler.handle(request)


# -----------------
# Run app
# -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)

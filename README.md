# Slackbot MVP – Content Pipeline

This MVP demonstrates a minimal end-to-end Slack automation pipeline for marketing content processing.

- `/keywords` Slack command accepts a list of keywords.
- Cleans and deduplicates the input.
- Groups keywords using simple heuristic rules (no external APIs).
- Creates a basic outline for each group.
- Generates a downloadable PDF report.
- Fully deployed on Render (Docker-based).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your Slack credentials:
# SLACK_BOT_TOKEN=...
# SLACK_SIGNING_SECRET=...
# BASE_URL=http://localhost:8000
# DOWNLOAD_TOKEN=....

# Run server locally
-python app.py

## Deployment
The app is containerized with Docker and deployed on Render. 
Live URL: https://slackbot-mvp.onrender.com

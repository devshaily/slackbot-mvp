# Slackbot MVP – Content Pipeline (Partial Working)


This MVP demonstrates a minimal end-to-end pipeline for the assignment:


- `/keywords` Slack command accepts a pasted list of keywords.
- Cleans & deduplicates the list.
- Groups keywords via simple, deterministic heuristics (no external APIs).
- Generates a template-based (fake) outline per group.
- Produces a downloadable PDF report.


> This is intentionally simple to satisfy the "partial working" requirement fast.


## 1) Local Setup


```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in SLACK_BOT_TOKEN & SLACK_SIGNING_SECRET


# run server
gunicorn app:flask_app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
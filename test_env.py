from dotenv import load_dotenv
import os

load_dotenv()

print("BOT_TOKEN:", os.getenv("SLACK_BOT_TOKEN"))
print("SIGNING_SECRET:", os.getenv("SLACK_SIGNING_SECRET"))
print("BASE_URL:", os.getenv("BASE_URL"))
print("DOWNLOAD_TOKEN:", os.getenv("DOWNLOAD_TOKEN"))

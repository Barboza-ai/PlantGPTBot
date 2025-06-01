from flask import Flask, request
import requests
import os
from openai import OpenAI

app = Flask(__name__)

# ✅ Read from environment variables
BOT_TOKEN = os.environ['BOT_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

BOT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
client = OpenAI(api_key=OPENAI_API_KEY)

# 🌿 Create plant reply
def generate_plant_response(user_text):
    prompt = f"""
    You are a houseplant. The user describes a problem — like yellow leaves or too much water.
    Reply as if you're the plant: emotional, dramatic, or witty — but helpful.
    End with a tip for plant care.

    User: {user_text}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a witty, emotional houseplant that gives helpful plant care advice."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# 📩 Telegram Webhook
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_text = message.get("text", "")

    if chat_id and user_text:
        reply = generate_plant_response(user_text)
        payload = {"chat_id": chat_id, "text": reply}
        requests.post(BOT_URL, json=payload)

    return "ok"

# 🚀 Start Flask server
if __name__ == "__main__":
    import socket
    print("✅ Copy your public bot URL and use it below:")
    print(f"https://{socket.gethostname()}.repl.co")
    app.run(host="0.0.0.0", port=5000)

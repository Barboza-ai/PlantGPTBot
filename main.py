from flask import Flask, request
import requests
import os
from openai import OpenAI
import io
from PIL import Image
import torch
from torchvision import models, transforms

app = Flask(__name__)

# ✅ Read from environment variables
BOT_TOKEN = os.environ['BOT_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

BOT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
client = OpenAI(api_key=OPENAI_API_KEY)

# ⚙️ Pre-trained image classification model
_weights = models.ResNet18_Weights.DEFAULT
model = models.resnet18(weights=_weights)
model.eval()
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=_weights.meta["mean"], std=_weights.meta["std"]),
])
classes = _weights.meta["categories"]

# 🔍 Classify an image and return top label
def classify_image(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = preprocess(image).unsqueeze(0)
    with torch.no_grad():
        output = model(tensor)
        idx = output.argmax(dim=1).item()
    return classes[idx]

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
    photos = message.get("photo")

    if chat_id and photos:
        file_id = photos[-1]["file_id"]
        file_info = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
            params={"file_id": file_id},
        ).json()
        file_path = file_info.get("result", {}).get("file_path")
        if file_path:
            img_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            img_bytes = requests.get(img_url).content
            label = classify_image(img_bytes)
            payload = {"chat_id": chat_id, "text": label}
            requests.post(BOT_URL, json=payload)
        return "ok"

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

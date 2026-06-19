"""
LINE Chatbot + Gemini AI สำหรับร้านค้าออนไลน์
พร้อม order flow, admin dashboard, SQLite database
"""

import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai
from dotenv import load_dotenv

from database import init_db, get_store, get_products, get_session
from order_flow import handle_order_flow
from dashboard.routes import admin_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme-secret-key")

# ---------- LINE ----------
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ---------- Gemini ----------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ---------- Dashboard Blueprint ----------
app.register_blueprint(admin_bp)

init_db()

HANDOFF_KEYWORDS = ["คุยกับแอดมิน", "พนักงาน", "ร้องเรียน", "คืนเงิน", "ของเสีย"]


def build_system_prompt():
    store = get_store()
    products = get_products(active_only=True)
    products_text = "\n".join(
        f"- {p['name']}: {p['price']:,} บาท (สต็อก: {p['stock']})"
        for p in products
    )
    return f"""คุณเป็นผู้ช่วยตอบแชทให้ร้าน "{store['name']}"

ข้อมูลร้าน:
- เวลาเปิด-ปิด: {store['hours']}
- ค่าจัดส่ง: {store['shipping']}
- ช่องทางชำระเงิน: {store['payment']}

รายการสินค้า:
{products_text}

กฎการตอบ:
1. ตอบสั้น กระชับ เป็นมิตร ใช้ภาษาไทยธรรมชาติ
2. ตอบจากข้อมูลที่ให้เท่านั้น ถ้าไม่รู้ให้บอกว่าจะให้แอดมินติดต่อกลับ
3. ห้ามแต่งข้อมูลราคาหรือสต็อกที่ไม่มีในรายการ
4. ถ้าลูกค้าสนใจสั่งซื้อ ให้แนะนำให้พิมพ์ว่า "สั่งซื้อ" เพื่อสั่งผ่านระบบ
"""


def ask_gemini(user_message: str) -> str:
    try:
        response = model.generate_content(
            f"{build_system_prompt()}\n\nคำถามลูกค้า: {user_message}"
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Error] {e}")
        return "ขอโทษค่ะ ระบบขัดข้องชั่วคราว รบกวนรอแอดมินตอบกลับสักครู่นะคะ"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text

    # 1. handoff ให้แอดมิน
    if any(k in user_text for k in HANDOFF_KEYWORDS):
        reply_text = "รับเรื่องแล้วค่ะ แอดมินจะติดต่อกลับโดยเร็วที่สุดนะคะ"

    # 2. order flow (สถานะสั่งซื้อ)
    else:
        order_reply = handle_order_flow(user_id, user_text)
        reply_text = order_reply if order_reply is not None else ask_gemini(user_text)

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )


@app.route("/", methods=["GET"])
def health_check():
    return "LINE Chatbot is running OK"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

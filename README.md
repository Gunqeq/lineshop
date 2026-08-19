# LINE Chatbot Starter — Flask + Gemini AI

Chatbot ตอบลูกค้าอัตโนมัติสำหรับร้านค้าออนไลน์ เชื่อมต่อกับ **LINE Official Account** และใช้ **Gemini AI** เพื่อให้บอทเข้าใจภาษาธรรมชาติ ไม่ได้จำกัดแค่การตรวจจับ Keyword

---

## 📁 โครงสร้างโปรเจกต์

```text
line-chatbot-starter/
├── app.py              # โค้ดหลัก รับ Webhook จาก LINE และส่งต่อ Gemini
├── store_data.py       # ข้อมูลร้านค้าและสินค้า
├── requirements.txt    # รายชื่อ Python libraries ที่ต้องติดตั้ง
├── .env.example        # ตัวอย่างไฟล์ Environment Variables
└── .gitignore          # ป้องกันไฟล์สำคัญถูก Commit
```

---

# 🚀 ขั้นตอนติดตั้ง

## 1. สร้าง LINE Official Account + Channel

1. เข้า [LINE Developers Console](https://developers.line.biz/console/)
2. สร้าง **Provider** ใหม่ หากยังไม่มี
3. สร้าง Channel ประเภท **Messaging API**
4. ไปที่แท็บ **Messaging API**
5. คัดลอกค่าต่อไปนี้

* **Channel access token** — กด `Issue` หากยังไม่มี
* **Channel secret** — อยู่ในแท็บ `Basic settings`

---

## 2. สร้าง Gemini API Key

1. เข้า [Google AI Studio](https://aistudio.google.com/app/apikey)
2. กด **Create API Key**
3. คัดลอก API Key และเก็บไว้สำหรับตั้งค่าใน `.env`

> ⚠️ **ห้ามนำ API Key ไปใส่ไว้ใน Source Code หรือ Commit ขึ้น GitHub**

---

## 3. ติดตั้งโปรเจกต์

### สร้าง Virtual Environment

```bash
python -m venv venv
```

### เปิดใช้งาน Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. ตั้งค่า Environment Variables

คัดลอกไฟล์ `.env.example` เป็น `.env`

**Windows**

```bash
copy .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

จากนั้นเปิดไฟล์ `.env` แล้วใส่ค่าที่ได้รับจาก LINE และ Gemini

ตัวอย่าง:

```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
GEMINI_API_KEY=your_gemini_api_key
```

> 🔒 **อย่า Commit ไฟล์ `.env` ขึ้น GitHub**

---

# 🏪 5. ตั้งค่าข้อมูลร้านค้า

เปิดไฟล์:

```text
store_data.py
```

แล้วแก้ข้อมูลให้ตรงกับร้านจริง เช่น

* ชื่อร้าน
* รายละเอียดร้าน
* เวลาเปิด-ปิด
* ค่าจัดส่ง
* รายการสินค้า
* ราคา
* รายละเอียดสินค้า

ตัวอย่าง:

```python
STORE_NAME = "My Online Shop"

STORE_INFO = {
    "open_time": "09:00",
    "close_time": "18:00",
    "shipping_fee": 50,
}
```

---

# ▶️ 6. รันเซิร์ฟเวอร์

ใช้คำสั่ง:

```bash
python app.py
```

หากทำงานสำเร็จ Server จะเปิดที่:

```text
http://localhost:5000
```

---

# 🌐 7. เปิด Webhook ให้ LINE เข้าถึง Server

เนื่องจาก `localhost` ไม่สามารถให้ LINE เข้าถึงโดยตรงได้ จึงต้องใช้ **ngrok** เพื่อสร้าง Public URL ชั่วคราว

ดาวน์โหลด ngrok ได้จาก [ngrok](https://ngrok.com/download)

จากนั้นรัน:

```bash
ngrok http 5000
```

จะได้ URL ประมาณ:

```text
https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

นำ URL ไปต่อท้ายด้วย:

```text
/callback
```

ตัวอย่าง:

```text
https://xxxx.ngrok-free.app/callback
```

จากนั้นนำ URL นี้ไปใส่ใน:

**LINE Developers Console → Messaging API → Webhook settings**

แล้วกด:

```text
Verify
```

หากสำเร็จ ระบบจะแจ้งว่า Webhook สามารถเชื่อมต่อได้

---

## ⚙️ 8. เปิดใช้งาน Webhook

ในหน้า **Messaging API**

ตั้งค่า:

```text
Use webhook: Enabled
```

และใน **LINE Official Account Manager**

ปิด:

```text
Auto-reply messages
```

เพื่อป้องกันข้อความตอบกลับซ้ำกับ Chatbot ของเรา

---

# 💬 9. ทดสอบ Chatbot

เพิ่มเพื่อน LINE Official Account ของคุณ

จากนั้นลองส่งข้อความ เช่น:

```text
มีเสื้อสีดำไหม
```

หรือ

```text
ค่าส่งเท่าไหร่
```

หรือ

```text
ร้านเปิดกี่โมง
```

Gemini AI จะช่วยให้ Chatbot เข้าใจคำถามที่มีรูปแบบแตกต่างกันได้ เช่น:

```text
เสื้อดำมีมั้ย
```

```text
ขอเสื้อสีดำหน่อย
```

```text
มีเสื้อโทนดำหรือเปล่า
```

---

# 📸 Screenshots

## 👤 User — Chat

<p align="center">
  <img
    width="420"
    src="https://github.com/user-attachments/assets/ac2af9e6-7923-4065-b31f-eca94b625c1c"
    alt="LINE Chatbot User Interface"
  />
</p>

---

## 🛠️ Admin — Dashboard

<p align="center">
  <img
    width="900"
    src="https://github.com/user-attachments/assets/8fd055cb-287c-4e6d-b843-bb8458b184b7"
    alt="LINE Chatbot Admin Dashboard"
  />
</p>

---

# 🔐 Security

**ห้าม Commit ไฟล์ `.env` ขึ้น GitHub เด็ดขาด**

ไฟล์ `.gitignore` ควรมี:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

หาก API Key หลุดหรือถูกเผยแพร่ไปแล้ว:

1. **Revoke API Key เดิมทันที**
2. สร้าง API Key ใหม่
3. เปลี่ยนค่าใน `.env`
4. ตรวจสอบ Git History หาก Key เคยถูก Commit ไปแล้ว

---

# 🧰 Technologies

| Technology         | Purpose                                  |
| ------------------ | ---------------------------------------- |
| Python             | Backend                                  |
| Flask              | Web Server / Webhook                     |
| LINE Messaging API | รับและส่งข้อความ                         |
| Gemini AI          | Natural Language Processing              |
| ngrok              | เปิด Local Server ให้เข้าถึงจาก Internet |
| dotenv             | จัดการ Environment Variables             |

---

# ✨ Features

* 🤖 AI Chatbot ด้วย Gemini
* 💬 รองรับภาษาธรรมชาติ
* 🛍️ ตอบคำถามเกี่ยวกับสินค้า
* 💰 ตอบข้อมูลราคาและค่าจัดส่ง
* 🏪 ตอบข้อมูลร้านค้า
* 📱 เชื่อมต่อ LINE Official Account
* 🔐 แยก API Keys ออกจาก Source Code
* 🌐 รองรับ Webhook ผ่าน ngrok

---

# 📌 Important

> โปรเจกต์นี้เหมาะสำหรับใช้เป็น Starter Template สำหรับสร้าง LINE AI Chatbot สำหรับร้านค้าออนไลน์

ก่อนนำไปใช้งานจริง ควรเพิ่มระบบ Authentication, Database, Logging, Error Handling และระบบจัดการคำสั่งซื้อเพื่อให้เหมาะกับ Production Environment

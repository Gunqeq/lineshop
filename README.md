# LINE Chatbot Starter (Flask + Gemini AI)

Chatbot ตอบลูกค้าอัตโนมัติสำหรับร้านค้าออนไลน์ เชื่อมต่อ LINE Official Account
ใช้ Gemini AI ให้บอทเข้าใจภาษาธรรมชาติ ไม่ใช่แค่ keyword matching

## โครงสร้างไฟล์

```
line-chatbot-starter/
├── app.py              # โค้ดหลัก รับ webhook จาก LINE และส่งต่อ Gemini
├── store_data.py        # ข้อมูลร้านค้า/สินค้า (แก้ตรงนี้ให้ตรงกับร้านจริง)
├── requirements.txt     # รายชื่อ library ที่ต้องติดตั้ง
├── .env.example          # ตัวอย่างไฟล์ตั้งค่า (copy เป็น .env)
└── .gitignore
```

## ขั้นตอนติดตั้ง

### 1. สร้าง LINE Official Account + Channel

1. ไปที่ [LINE Developers Console](https://developers.line.biz/console/)
2. สร้าง Provider ใหม่ (ถ้ายังไม่มี)
3. สร้าง Channel แบบ "Messaging API"
4. ไปที่แท็บ "Messaging API" คัดลอกค่า:
   - **Channel access token** (กด Issue ถ้ายังไม่มี)
   - **Channel secret** (อยู่แท็บ Basic settings)

### 2. สร้าง Gemini API Key

1. ไปที่ [Google AI Studio](https://aistudio.google.com/app/apikey)
2. กด Create API Key คัดลอกมาเก็บไว้

### 3. ติดตั้งโปรเจกต์

```bash
# สร้าง virtual environment
python -m venv venv
source venv/bin/activate  # Windows ใช้: venv\Scripts\activate

# ติดตั้ง library
pip install -r requirements.txt

# ตั้งค่า environment variables
cp .env.example .env
# แล้วเปิดไฟล์ .env ใส่ค่า token/key ที่ได้จากขั้นตอนก่อนหน้า
```

### 4. แก้ข้อมูลร้านค้า

เปิดไฟล์ `store_data.py` แก้ชื่อร้าน เวลาเปิด-ปิด ค่าส่ง และรายการสินค้าให้ตรงกับร้านจริง

### 5. รันเซิร์ฟเวอร์

```bash
python app.py
```

เซิร์ฟเวอร์จะรันที่ `http://localhost:5000`

### 6. เปิด webhook ให้ LINE เรียกได้ (ใช้ ngrok)

เครื่อง local เราไม่มี public URL ต้องใช้ ngrok เปิด tunnel ชั่วคราว

```bash
# ติดตั้ง ngrok จาก https://ngrok.com/download
ngrok http 5000
```

จะได้ URL แบบ `https://xxxx-xx-xx-xx-xx.ngrok-free.app`

นำ URL นี้ + `/callback` (เช่น `https://xxxx.ngrok-free.app/callback`)
ไปใส่ในช่อง **Webhook URL** ที่หน้า LINE Developers Console
แท็บ Messaging API > Webhook settings แล้วกด Verify

อย่าลืมเปิด "Use webhook" เป็น Enabled และปิด "Auto-reply messages" ใน
LINE Official Account Manager เพื่อไม่ให้ชนกับบอทของเรา

### 7. ทดสอบ

เพิ่มเพื่อน LINE OA ของคุณ (QR code อยู่หน้า Messaging API)
แล้วลองพิมพ์คุยดู เช่น "มีเสื้อสีดำไหม" หรือ "ค่าส่งเท่าไหร่"



ห้าม commit ไฟล์ `.env` ขึ้น GitHub เด็ดขาด (มี `.gitignore` กันไว้ให้แล้ว)
ถ้า API key หลุดไปที่ไหน ให้ revoke แล้วสร้างใหม่ทันที

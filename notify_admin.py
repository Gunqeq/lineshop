"""
Push LINE message แจ้งแอดมินเมื่อมีออเดอร์ใหม่
ต้องตั้งค่า ADMIN_LINE_USER_ID ใน .env
"""

import os
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
ADMIN_LINE_USER_ID = os.getenv("ADMIN_LINE_USER_ID", "")


def push_admin_order_notify(order_id: int, data: dict, total: int):
    if not ADMIN_LINE_USER_ID:
        print("[Notify] ADMIN_LINE_USER_ID ยังไม่ได้ตั้งค่า ข้ามการแจ้งเตือน")
        return

    items_text = "\n".join(
        f"  • {i['product_name']} x{i['qty']} ({i['price']*i['qty']:,} บาท)"
        for i in data["items"]
    )

    message = (
        f"🛒 ออเดอร์ใหม่ #{order_id}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{items_text}\n"
        f"รวม: {total:,} บาท\n"
        f"━━━━━━━━━━━━━━\n"
        f"ชื่อ: {data['customer_name']}\n"
        f"ที่อยู่: {data['address']}\n"
        f"โทร: {data['phone']}"
    )

    configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        api.push_message(
            PushMessageRequest(
                to=ADMIN_LINE_USER_ID,
                messages=[TextMessage(text=message)],
            )
        )

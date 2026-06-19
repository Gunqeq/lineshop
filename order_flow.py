"""
Order conversation state machine
States: idle → ordering_select → ordering_qty → ordering_name → ordering_address → ordering_phone → ordering_confirm
"""

from database import (
    get_products, get_product, get_session, save_session,
    clear_session, create_order, get_store,
)
from notify_admin import push_admin_order_notify

ORDER_TRIGGER_KEYWORDS = ["สั่ง", "order", "สั่งซื้อ", "ซื้อ", "จอง"]
CANCEL_KEYWORDS = ["ยกเลิก", "cancel", "เลิก", "ออก"]


def is_order_trigger(text: str) -> bool:
    return any(k in text.lower() for k in ORDER_TRIGGER_KEYWORDS)


def handle_order_flow(line_user_id: str, text: str) -> str | None:
    """
    ถ้าเป็น order flow → ตอบเอง return str
    ถ้าไม่ใช่ → return None (ให้ Gemini ตอบแทน)
    """
    session = get_session(line_user_id)
    state = session["state"]
    data = session["data"]

    # ยกเลิกได้ทุก state
    if any(k in text for k in CANCEL_KEYWORDS) and state != "idle":
        clear_session(line_user_id)
        return "ยกเลิกออเดอร์แล้วค่ะ หากต้องการสั่งซื้อใหม่พิมพ์ว่า 'สั่งซื้อ' ได้เลยนะคะ"

    if state == "idle":
        if is_order_trigger(text):
            return _start_order(line_user_id)
        return None

    if state == "ordering_select":
        return _handle_select(line_user_id, text, data)

    if state == "ordering_qty":
        return _handle_qty(line_user_id, text, data)

    if state == "ordering_name":
        return _handle_name(line_user_id, text, data)

    if state == "ordering_address":
        return _handle_address(line_user_id, text, data)

    if state == "ordering_phone":
        return _handle_phone(line_user_id, text, data)

    if state == "ordering_confirm":
        return _handle_confirm(line_user_id, text, data)

    return None


# ---------- step handlers ----------

def _start_order(line_user_id: str) -> str:
    products = get_products(active_only=True)
    in_stock = [p for p in products if p["stock"] > 0]
    if not in_stock:
        return "ขอโทษค่ะ ตอนนี้สินค้าหมดทุกรายการ รบกวนติดตามเร็วๆนี้นะคะ"

    lines = ["สวัสดีค่ะ มีสินค้าดังนี้ค่ะ\n"]
    for p in in_stock:
        lines.append(f"{p['id']}. {p['name']} — {p['price']:,} บาท (เหลือ {p['stock']} ชิ้น)")
    lines.append("\nพิมพ์ตัวเลขหน้าสินค้าที่ต้องการสั่งซื้อได้เลยค่ะ")

    save_session(line_user_id, "ordering_select", {"items": []})
    return "\n".join(lines)


def _handle_select(line_user_id, text, data):
    try:
        pid = int(text.strip())
    except ValueError:
        return "กรุณาพิมพ์ตัวเลขหน้าสินค้าที่ต้องการค่ะ เช่น 1, 2, 3"

    product = get_product(pid)
    if not product or not product["active"]:
        return "ไม่พบสินค้าหมายเลขนั้นค่ะ กรุณาเลือกใหม่อีกครั้ง"
    if product["stock"] <= 0:
        return f"'{product['name']}' หมดสต็อกแล้วค่ะ กรุณาเลือกสินค้าอื่น"

    data["current_product"] = product
    save_session(line_user_id, "ordering_qty", data)
    return f"เลือก '{product['name']}' ราคา {product['price']:,} บาทค่ะ\nต้องการกี่ชิ้นคะ?"


def _handle_qty(line_user_id, text, data):
    try:
        qty = int(text.strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        return "กรุณาพิมพ์จำนวนเป็นตัวเลขค่ะ เช่น 1, 2"

    product = data["current_product"]
    if qty > product["stock"]:
        return f"สต็อกเหลือแค่ {product['stock']} ชิ้นค่ะ กรุณาพิมพ์จำนวนใหม่"

    data["items"].append({
        "product_id": product["id"],
        "product_name": product["name"],
        "price": product["price"],
        "qty": qty,
    })
    data.pop("current_product", None)

    subtotal = sum(i["price"] * i["qty"] for i in data["items"])
    items_summary = "\n".join(f"  - {i['product_name']} x{i['qty']} = {i['price']*i['qty']:,} บาท" for i in data["items"])

    save_session(line_user_id, "ordering_name", data)
    return (
        f"รับไว้แล้วค่ะ สรุปตะกร้าตอนนี้:\n{items_summary}\n"
        f"รวม {subtotal:,} บาท\n\n"
        "กรุณาพิมพ์ชื่อ-นามสกุลผู้รับสินค้าค่ะ"
    )


def _handle_name(line_user_id, text, data):
    data["customer_name"] = text.strip()
    save_session(line_user_id, "ordering_address", data)
    return "ขอบคุณค่ะ กรุณาพิมพ์ที่อยู่จัดส่งให้ครบค่ะ (บ้านเลขที่ / ซอย / ถนน / ตำบล / อำเภอ / จังหวัด / รหัสไปรษณีย์)"


def _handle_address(line_user_id, text, data):
    data["address"] = text.strip()
    save_session(line_user_id, "ordering_phone", data)
    return "ได้รับที่อยู่แล้วค่ะ กรุณาพิมพ์เบอร์โทรศัพท์เพื่อติดต่อค่ะ"


def _handle_phone(line_user_id, text, data):
    phone = text.strip().replace("-", "").replace(" ", "")
    if not phone.isdigit() or len(phone) < 9:
        return "กรุณาพิมพ์เบอร์โทรศัพท์ให้ถูกต้องค่ะ"

    data["phone"] = phone
    store = get_store()
    items_summary = "\n".join(
        f"  - {i['product_name']} x{i['qty']} = {i['price']*i['qty']:,} บาท"
        for i in data["items"]
    )
    total = sum(i["price"] * i["qty"] for i in data["items"])

    save_session(line_user_id, "ordering_confirm", data)
    return (
        f"สรุปออเดอร์ค่ะ\n"
        f"━━━━━━━━━━━━━━\n"
        f"สินค้า:\n{items_summary}\n"
        f"รวม: {total:,} บาท\n"
        f"ผู้รับ: {data['customer_name']}\n"
        f"ที่อยู่: {data['address']}\n"
        f"โทร: {phone}\n"
        f"━━━━━━━━━━━━━━\n"
        f"ชำระเงิน: {store['payment']}\n\n"
        "พิมพ์ 'ยืนยัน' เพื่อสั่งซื้อ หรือ 'ยกเลิก' เพื่อยกเลิกค่ะ"
    )


def _handle_confirm(line_user_id, text, data):
    if "ยืนยัน" not in text and "confirm" not in text.lower():
        return "พิมพ์ 'ยืนยัน' เพื่อยืนยันออเดอร์ หรือ 'ยกเลิก' เพื่อยกเลิกค่ะ"

    order_id, total = create_order(
        line_user_id=line_user_id,
        customer_name=data["customer_name"],
        address=data["address"],
        phone=data["phone"],
        items=data["items"],
    )

    clear_session(line_user_id)

    try:
        push_admin_order_notify(order_id, data, total)
    except Exception as e:
        print(f"[Notify Error] {e}")

    return (
        f"ยืนยันออเดอร์ #{order_id} เรียบร้อยแล้วค่ะ\n"
        f"ยอดรวม {total:,} บาท\n\n"
        "กรุณาโอนเงินและส่งสลิปมาให้แอดมินนะคะ แอดมินจะยืนยันออเดอร์และจัดส่งโดยเร็วค่ะ"
    )

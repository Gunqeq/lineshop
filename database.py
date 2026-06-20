"""
SQLite database layer — stores, products, orders, chat sessions
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "lineshop.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS store (
                id          INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                hours       TEXT,
                shipping    TEXT,
                payment     TEXT,
                admin_user_id TEXT
            );

            CREATE TABLE IF NOT EXISTS products (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                price   INTEGER NOT NULL,
                stock   INTEGER NOT NULL DEFAULT 0,
                active  INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                line_user_id TEXT NOT NULL,
                customer_name TEXT,
                address     TEXT,
                phone       TEXT,
                total       INTEGER DEFAULT 0,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    INTEGER NOT NULL REFERENCES orders(id),
                product_id  INTEGER NOT NULL REFERENCES products(id),
                product_name TEXT NOT NULL,
                price       INTEGER NOT NULL,
                qty         INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                line_user_id TEXT PRIMARY KEY,
                state       TEXT DEFAULT 'idle',
                data        TEXT DEFAULT '{}'
            );
        """)
        _seed_if_empty(conn)


def _seed_if_empty(conn):
    row = conn.execute("SELECT COUNT(*) as c FROM store").fetchone()
    if row["c"] > 0:
        return
    conn.execute("""
        INSERT INTO store (id, name, hours, shipping, payment)
        VALUES (1, 'ร้านตัวอย่าง', 'เปิดทุกวัน 09:00-21:00',
                'ส่งฟรีเมื่อซื้อครบ 500 บาท / ค่าส่งปกติ 50 บาท',
                'โอนผ่านธนาคาร หรือ พร้อมเพย์')
    """)
    products = [
        ("เสื้อยืดคอกลม สีขาว", 290, 15),
        ("เสื้อยืดคอกลม สีดำ", 290, 8),
        ("กระเป๋าผ้าแคนวาส", 350, 20),
        ("หมวกแก๊ป", 250, 0),
    ]
    conn.executemany(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", products
    )


# ---------- store ----------

def get_store():
    with get_conn() as conn:
        return dict(conn.execute("SELECT * FROM store WHERE id=1").fetchone())


def update_store(name, hours, shipping, payment, admin_user_id=None):
    with get_conn() as conn:
        conn.execute("""
            UPDATE store SET name=?, hours=?, shipping=?, payment=?, admin_user_id=?
            WHERE id=1
        """, (name, hours, shipping, payment, admin_user_id))


# ---------- products ----------

def get_products(active_only=True):
    sql = "SELECT * FROM products" + (" WHERE active=1" if active_only else "") + " ORDER BY id"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def get_product(pid):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        return dict(row) if row else None


def add_product(name, price, stock):
    with get_conn() as conn:
        conn.execute("INSERT INTO products (name, price, stock) VALUES (?,?,?)", (name, price, stock))


def update_product(pid, name, price, stock):
    with get_conn() as conn:
        conn.execute("UPDATE products SET name=?, price=?, stock=? WHERE id=?", (name, price, stock, pid))


def deactivate_product(pid):
    with get_conn() as conn:
        conn.execute("UPDATE products SET active=0 WHERE id=?", (pid,))


def reduce_stock(pid, qty):
    with get_conn() as conn:
        conn.execute("UPDATE products SET stock = MAX(0, stock-?) WHERE id=?", (qty, pid))


# ---------- orders ----------

def create_order(line_user_id, customer_name, address, phone, items):
    """items: list of {product_id, product_name, price, qty}"""
    total = sum(i["price"] * i["qty"] for i in items)
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO orders (line_user_id, customer_name, address, phone, total)
            VALUES (?,?,?,?,?)
        """, (line_user_id, customer_name, address, phone, total))
        order_id = cur.lastrowid
        conn.executemany("""
            INSERT INTO order_items (order_id, product_id, product_name, price, qty)
            VALUES (:order_id, :product_id, :product_name, :price, :qty)
        """, [{**i, "order_id": order_id} for i in items])
        for i in items:
            conn.execute(
                "UPDATE products SET stock = MAX(0, stock-?) WHERE id=?",
                (i["qty"], i["product_id"])
            )
        return order_id, total


def get_orders(limit=50):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT o.*, GROUP_CONCAT(oi.product_name || ' x' || oi.qty, ', ') as items_summary
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.id ORDER BY o.id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def update_order_status(order_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))


# ---------- chat sessions ----------

def get_session(line_user_id):
    import json
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE line_user_id=?", (line_user_id,)
        ).fetchone()
        if not row:
            return {"state": "idle", "data": {}}
        return {"state": row["state"], "data": json.loads(row["data"])}


def save_session(line_user_id, state, data):
    import json
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO chat_sessions (line_user_id, state, data)
            VALUES (?,?,?)
            ON CONFLICT(line_user_id) DO UPDATE SET state=excluded.state, data=excluded.data
        """, (line_user_id, state, json.dumps(data, ensure_ascii=False)))


def clear_session(line_user_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE chat_sessions SET state='idle', data='{}' WHERE line_user_id=?",
            (line_user_id,)
        )

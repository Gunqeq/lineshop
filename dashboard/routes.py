"""
Flask Blueprint สำหรับหน้าเว็บแอดมิน
เข้าใช้งานที่ /admin
"""

import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import (
    get_store, update_store,
    get_products, add_product, update_product, deactivate_product,
    get_orders, update_order_status,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin",
                     template_folder="templates")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))
        flash("รหัสผ่านไม่ถูกต้อง")
    return render_template("login.html")


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    orders = get_orders(limit=10)
    products = get_products(active_only=False)
    pending = sum(1 for o in orders if o["status"] == "pending")
    return render_template("dashboard.html", orders=orders, products=products, pending=pending)


# ---------- Products ----------

@admin_bp.route("/products")
@login_required
def products():
    return render_template("products.html", products=get_products(active_only=False))


@admin_bp.route("/products/add", methods=["POST"])
@login_required
def add_product_route():
    name = request.form["name"].strip()
    price = int(request.form["price"])
    stock = int(request.form["stock"])
    if name:
        add_product(name, price, stock)
        flash(f"เพิ่มสินค้า '{name}' แล้วค่ะ")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:pid>/edit", methods=["POST"])
@login_required
def edit_product_route(pid):
    update_product(pid, request.form["name"], int(request.form["price"]), int(request.form["stock"]))
    flash("อัปเดตสินค้าแล้วค่ะ")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:pid>/delete", methods=["POST"])
@login_required
def delete_product_route(pid):
    deactivate_product(pid)
    flash("ลบสินค้าแล้วค่ะ")
    return redirect(url_for("admin.products"))


# ---------- Orders ----------

@admin_bp.route("/orders")
@login_required
def orders():
    return render_template("orders.html", orders=get_orders(limit=100))


@admin_bp.route("/orders/<int:oid>/status", methods=["POST"])
@login_required
def update_status(oid):
    update_order_status(oid, request.form["status"])
    flash(f"อัปเดตสถานะออเดอร์ #{oid} แล้วค่ะ")
    return redirect(url_for("admin.orders"))


# ---------- Store settings ----------

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    store = get_store()
    if request.method == "POST":
        update_store(
            name=request.form["name"],
            hours=request.form["hours"],
            shipping=request.form["shipping"],
            payment=request.form["payment"],
            admin_user_id=request.form.get("admin_user_id", ""),
        )
        flash("บันทึกข้อมูลร้านแล้วค่ะ")
        return redirect(url_for("admin.settings"))
    return render_template("settings.html", store=store)

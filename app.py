from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# ---------- In-memory "database" ----------
PRODUCTS = [
    {"id": 1, "name": "Classic White T-Shirt", "price": 19.99, "category": "Men",
     "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400", "stock": 25,
     "description": "Premium cotton classic white t-shirt."},
    {"id": 2, "name": "Denim Jeans", "price": 49.99, "category": "Men",
     "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400", "stock": 15,
     "description": "Slim-fit denim jeans with stretch comfort."},
    {"id": 3, "name": "Floral Summer Dress", "price": 39.99, "category": "Women",
     "image": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400", "stock": 20,
     "description": "Lightweight floral dress perfect for summer."},
    {"id": 4, "name": "Leather Jacket", "price": 129.99, "category": "Men",
     "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400", "stock": 8,
     "description": "Genuine leather biker jacket."},
    {"id": 5, "name": "Wool Sweater", "price": 59.99, "category": "Women",
     "image": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400", "stock": 12,
     "description": "Cozy wool sweater for chilly days."},
    {"id": 6, "name": "Running Sneakers", "price": 89.99, "category": "Shoes",
     "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400", "stock": 30,
     "description": "Lightweight running sneakers with cushioned soles."},
    {"id": 7, "name": "Baseball Cap", "price": 14.99, "category": "Accessories",
     "image": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=400", "stock": 40,
     "description": "Adjustable cotton baseball cap."},
    {"id": 8, "name": "Silk Scarf", "price": 24.99, "category": "Accessories",
     "image": "https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=400", "stock": 18,
     "description": "Elegant silk scarf with a printed pattern."},
]

ORDERS = []


# ---------- Helpers ----------
def get_cart():
    return session.setdefault("cart", {})


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


def find_product(pid):
    return next((p for p in PRODUCTS if p["id"] == pid), None)


def cart_details():
    cart = get_cart()
    items, total = [], 0.0
    for pid_str, qty in cart.items():
        product = find_product(int(pid_str))
        if product:
            subtotal = product["price"] * qty
            items.append({**product, "qty": qty, "subtotal": round(subtotal, 2)})
            total += subtotal
    return items, round(total, 2)


# ---------- Routes ----------
@app.route("/")
def index():
    category = request.args.get("category")
    query = request.args.get("q", "").strip().lower()
    products = PRODUCTS
    if category:
        products = [p for p in products if p["category"].lower() == category.lower()]
    if query:
        products = [p for p in products if query in p["name"].lower() or query in p["description"].lower()]
    categories = sorted({p["category"] for p in PRODUCTS})
    cart_count = sum(get_cart().values())
    return render_template("index.html", products=products, categories=categories,
                           active_category=category, query=query, cart_count=cart_count)


@app.route("/product/<int:pid>")
def product_detail(pid):
    product = find_product(pid)
    if not product:
        flash("Product not found", "error")
        return redirect(url_for("index"))
    cart_count = sum(get_cart().values())
    return render_template("product.html", product=product, cart_count=cart_count)


@app.route("/add-to-cart/<int:pid>", methods=["POST"])
def add_to_cart(pid):
    product = find_product(pid)
    if not product:
        flash("Product not found", "error")
        return redirect(url_for("index"))
    qty = int(request.form.get("qty", 1))
    if qty < 1:
        qty = 1
    cart = get_cart()
    cart[str(pid)] = cart.get(str(pid), 0) + qty
    save_cart(cart)
    flash(f"Added {qty} × {product['name']} to cart", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart")
def view_cart():
    items, total = cart_details()
    return render_template("cart.html", items=items, total=total, cart_count=sum(get_cart().values()))


@app.route("/update-cart/<int:pid>", methods=["POST"])
def update_cart(pid):
    qty = int(request.form.get("qty", 1))
    cart = get_cart()
    if qty <= 0:
        cart.pop(str(pid), None)
    else:
        cart[str(pid)] = qty
    save_cart(cart)
    return redirect(url_for("view_cart"))


@app.route("/remove-from-cart/<int:pid>", methods=["POST"])
def remove_from_cart(pid):
    cart = get_cart()
    cart.pop(str(pid), None)
    save_cart(cart)
    flash("Item removed from cart", "success")
    return redirect(url_for("view_cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = cart_details()
    if not items:
        flash("Your cart is empty", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        order = {
            "id": str(uuid.uuid4())[:8].upper(),
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "address": request.form.get("address", "").strip(),
            "items": items,
            "total": total,
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        ORDERS.append(order)
        save_cart({})  # clear cart
        return render_template("cart.html", items=[], total=0, cart_count=0, order=order)

    return render_template("checkout.html", items=items, total=total,
                           cart_count=sum(get_cart().values()))


@app.route("/orders")
def orders():
    return render_template("orders.html", orders=ORDERS, cart_count=sum(get_cart().values()))


@app.route("/health")
def health():
    return jsonify(status="ok", products=len(PRODUCTS), orders=len(ORDERS)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

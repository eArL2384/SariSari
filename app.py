from flask import Flask, request, render_template, session, redirect, url_for
import csv
import os
from urllib.parse import quote, unquote

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallbacksecret")

def load_products(filename="products.csv"):
    products = []
    with open(filename, newline='', encoding='latin-1') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            product_name = (row.get('Product') or row.get('Product Name') or '').strip()
            price_str = row.get('Price', '').strip()
            category = row.get('Category', '').strip()
            try:
                price = float(price_str) if price_str else 0.0
            except ValueError:
                price = 0.0
            products.append({"product": product_name, "price": price, "category": category})
    return products

products = load_products()
categories = sorted(set(p['category'] for p in products))

@app.route("/", methods=["GET", "POST"])
def home():
    cart = session.get("cart", [])
    total = sum(i['price'] * i['qty'] for i in cart)

    amount_paid = None
    change = None

    if request.method == "POST":
        amount_paid_str = request.form.get("amountPaid", "")
        try:
            amount_paid = float(amount_paid_str)
            change = amount_paid - total
        except ValueError:
            amount_paid = None
            change = None

    return render_template("home.html",
                           categories=categories,
                           cart=cart,
                           total=total,
                           amount_paid=amount_paid,
                           change=change)

@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword", "").lower()
    results = [p for p in products if keyword in p['product'].lower()]
    return render_template("page.html", title="Search Results", results=results)

@app.route("/category/<cat>")
def category(cat):
    cat = unquote(cat)
    results = [p for p in products if p['category'] == cat]
    return render_template("page.html", title=cat, results=results)

@app.route("/add", methods=["POST"])
def add_to_cart():
    chosen_product = request.form.get("chosen")
    qty_str = request.form.get("quantity", "")
    qty = int(qty_str) if qty_str.isdigit() else 0
    if chosen_product and qty > 0:
        item = next((p for p in products if p['product'] == chosen_product), None)
        if item:
            cart = session.get("cart", [])
            cart.append({"product": item['product'], "price": item['price'], "qty": qty})
            session["cart"] = cart
    return redirect(url_for('home'))

@app.route("/remove/<int:index>")
def remove_item(index):
    cart = session.get("cart", [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session["cart"] = cart
    return redirect(url_for('home'))

@app.route("/clear", methods=["POST"])
def clear_cart():
    session["cart"] = []
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)

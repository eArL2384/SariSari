from flask import Flask, request, render_template_string, session, redirect, url_for
import csv
import os
from urllib.parse import quote, unquote

app = Flask(__name__)
# Use environment variable for secret key, fallback if not set
app.secret_key = os.environ.get("SECRET_KEY", "fallbacksecret")

def load_products(filename):
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

products = load_products("products.csv")
categories = sorted(set(p['category'] for p in products))

@app.route("/")
def home():
    cart = session.get("cart", [])
    total = sum(i['price'] * i['qty'] for i in cart)
    cart_display = "<br>".join([
        f"{i['product']} x{i['qty']} = ₱{i['price']*i['qty']} "
        f"<a href='{url_for('remove_item', index=idx)}'>[Remove]</a>"
        for idx, i in enumerate(cart)
    ])

    return render_template_string("""
        <h2>Store Calculator</h2>
        <!-- Search bar -->
        <form method="post" action="{{ url_for('search') }}">
            <input type="text" name="keyword" placeholder="Enter product keyword">
            <input type="submit" value="Search">
        </form>

        <!-- Category buttons -->
        <h3>Categories</h3>
        {% for cat in categories %}
        <form method="get" action="{{ url_for('category', cat=quote(cat)) }}" style="display:inline;">
            <button type="submit">{{cat}}</button>
        </form>
        {% endfor %}

        <h3>Cart</h3>
        <p>{{cart_display|safe}}</p>
        <p><b>Total: ₱{{total}}</b></p>
        <form action="{{ url_for('clear_cart') }}" method="post">
            <button type="submit">Clear Cart</button>
        </form>
    """, categories=categories, cart_display=cart_display, total=total, quote=quote)

@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword", "").lower()
    results = [p for p in products if keyword in p['product'].lower()]
    return render_template_string(TEMPLATE_PAGE, title="Search Results", results=results)

@app.route("/category/<cat>")
def category(cat):
    cat = unquote(cat)
    results = [p for p in products if p['category'] == cat]
    return render_template_string(TEMPLATE_PAGE, title=cat, results=results)

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

# Shared template for search/category pages
TEMPLATE_PAGE = """
    <h2>{{title}}</h2>
    <form method="post" action="{{ url_for('add_to_cart') }}">
        <select name="chosen">
            {% for p in results %}
            <option value="{{p['product']}}">{{p['product']}} (₱{{p['price']}})</option>
            {% endfor %}
        </select>
        <input type="hidden" name="quantity" id="quantity" value="">
        <p>Quantity: <span id="qtyDisplay"></span></p>

        <!-- Styled numpad -->
        <div class="numpad">
            {% for row in [[1,2,3],[4,5,6],[7,8,9]] %}
            <div class="row">
                {% for n in row %}
                <button type="button" onclick="addNumber({{n}})">{{n}}</button>
                {% endfor %}
            </div>
            {% endfor %}
            <div class="row">
                <button type="button" onclick="addNumber(0)">0</button>
                <button type="button" onclick="clearNumber()">Clear</button>
            </div>
        </div>

        <input type="submit" value="Add to Cart">
    </form>
    <form action="{{ url_for('home') }}">
        <button type="submit">Back</button>
    </form>

    <style>
    .numpad { display: inline-block; margin-top: 10px; }
    .row { display: flex; justify-content: center; margin: 5px 0; }
    .row button {
        width: 60px; height: 60px;
        font-size: 20px;
        margin: 2px;
    }
    </style>

    <script>
    function addNumber(n) {
        let qtyField = document.getElementById("quantity");
        qtyField.value = qtyField.value + n;
        document.getElementById("qtyDisplay").innerText = qtyField.value;
    }
    function clearNumber() {
        document.getElementById("quantity").value = "";
        document.getElementById("qtyDisplay").innerText = "";
    }
    </script>
"""

if __name__ == "__main__":
    app.run(debug=True)

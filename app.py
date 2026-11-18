from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db import execute_query, execute_one
from functools import wraps
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "boutique_secret_2025")

# Initialize Groq Client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = execute_one(
            "SELECT * FROM users WHERE username=%s AND password=%s AND is_active=TRUE",
            (username, password)
        )
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash(f"Welcome, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'customers': execute_one("SELECT COUNT(*) AS c FROM customers")['c'],
        'products': execute_one("SELECT COUNT(*) AS c FROM products")['c'],
        'orders': execute_one("SELECT COUNT(*) AS c FROM orders")['c'],
        'tailoring': execute_one("SELECT COUNT(*) AS c FROM tailoring_orders WHERE status NOT IN ('Delivered','Cancelled')")['c'],
    }
    low_stock = execute_query("""
        SELECT product_name, stock_quantity, reorder_level
        FROM products WHERE stock_quantity <= reorder_level ORDER BY stock_quantity
    """, fetch=True)
    recent_orders = execute_query("""
        SELECT o.order_id, c.full_name, o.final_amount, o.status
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC LIMIT 5
    """, fetch=True)
    return render_template('dashboard.html', stats=stats, low_stock=low_stock, recent_orders=recent_orders)

@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '')
    if search:
        custs = execute_query(
            "SELECT * FROM customers WHERE full_name ILIKE %s OR phone ILIKE %s ORDER BY customer_id DESC",
            (f'%{search}%', f'%{search}%'), fetch=True)
    else:
        custs = execute_query("SELECT * FROM customers ORDER BY customer_id DESC", fetch=True)
    return render_template('customers.html', customers=custs, search=search)

@app.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    execute_query("""
        INSERT INTO customers (full_name, email, phone, address, city, gender,
                              chest, waist, hip, shoulder, sleeve_length, dress_length)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        request.form['full_name'], request.form.get('email'),
        request.form['phone'], request.form.get('address'),
        request.form.get('city'), request.form.get('gender'),
        request.form.get('chest') or None, request.form.get('waist') or None,
        request.form.get('hip') or None, request.form.get('shoulder') or None,
        request.form.get('sleeve_length') or None, request.form.get('dress_length') or None,
    ))
    flash('Customer added successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/delete/<int:cid>')
@login_required
def delete_customer(cid):
    execute_query("DELETE FROM customers WHERE customer_id=%s", (cid,))
    flash('Customer deleted', 'info')
    return redirect(url_for('customers'))

@app.route('/products')
@login_required
def products():
    prods = execute_query("""
        SELECT p.*, c.category_name FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id ORDER BY p.product_id DESC
    """, fetch=True)
    categories = execute_query("SELECT * FROM categories ORDER BY category_name", fetch=True)
    return render_template('products.html', products=prods, categories=categories)

@app.route('/products/add', methods=['POST'])
@login_required
def add_product():
    execute_query("""
        INSERT INTO products (product_name, category_id, size, color, fabric, price, stock_quantity, reorder_level)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        request.form['product_name'], request.form.get('category_id') or None,
        request.form.get('size'), request.form.get('color'), request.form.get('fabric'),
        request.form['price'], request.form['stock_quantity'], request.form.get('reorder_level') or 5,
    ))
    flash('Product added!', 'success')
    return redirect(url_for('products'))

@app.route('/products/delete/<int:pid>')
@login_required
def delete_product(pid):
    execute_query("DELETE FROM products WHERE product_id=%s", (pid,))
    flash('Product deleted', 'info')
    return redirect(url_for('products'))

@app.route('/orders')
@login_required
def orders():
    ords = execute_query("""
        SELECT o.*, c.full_name AS customer_name, c.phone
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id ORDER BY o.order_id DESC
    """, fetch=True)
    customers_list = execute_query("SELECT customer_id, full_name FROM customers ORDER BY full_name", fetch=True)
    products_list = execute_query("SELECT product_id, product_name, price FROM products WHERE stock_quantity > 0 ORDER BY product_name", fetch=True)
    return render_template('orders.html', orders=ords, customers=customers_list, products=products_list)

@app.route('/orders/add', methods=['POST'])
@login_required
def add_order():
    customer_id = request.form['customer_id']
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])

    product = execute_one("SELECT price, stock_quantity FROM products WHERE product_id=%s", (product_id,))
    if not product or product['stock_quantity'] < quantity:
        flash('Insufficient stock!', 'danger')
        return redirect(url_for('orders'))

    unit_price = product['price']
    subtotal = unit_price * quantity

    order = execute_one("""
        INSERT INTO orders (customer_id, user_id, delivery_date, total_amount, final_amount, status)
        VALUES (%s,%s,%s,%s,%s,'Pending') RETURNING order_id
    """, (customer_id, session['user_id'], request.form.get('delivery_date') or None, subtotal, subtotal))

    execute_query("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
        VALUES (%s,%s,%s,%s,%s)
    """, (order['order_id'], product_id, quantity, unit_price, subtotal))

    execute_query("UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id=%s", (quantity, product_id))
    flash('Order placed successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/orders/status/<int:oid>/<status>')
@login_required
def update_order_status(oid, status):
    execute_query("UPDATE orders SET status=%s WHERE order_id=%s", (status, oid))
    flash('Order status updated', 'success')
    return redirect(url_for('orders'))

@app.route('/tailoring')
@login_required
def tailoring():
    t_orders = execute_query("""
        SELECT t.*, c.full_name AS customer_name, c.phone, e.full_name AS tailor_name
        FROM tailoring_orders t
        JOIN customers c ON t.customer_id = c.customer_id
        LEFT JOIN employees e ON t.assigned_tailor = e.employee_id ORDER BY t.tailoring_id DESC
    """, fetch=True)
    customers_list = execute_query("SELECT customer_id, full_name FROM customers ORDER BY full_name", fetch=True)
    tailors = execute_query("SELECT employee_id, full_name FROM employees WHERE is_active=TRUE ORDER BY full_name", fetch=True)
    return render_template('tailoring.html', orders=t_orders, customers=customers_list, tailors=tailors)

@app.route('/tailoring/add', methods=['POST'])
@login_required
def add_tailoring():
    execute_query("""
        INSERT INTO tailoring_orders
            (customer_id, dress_type, fabric_provided, measurements, design_notes,
             total_price, advance_paid, delivery_date, assigned_tailor)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        request.form['customer_id'], request.form['dress_type'], request.form.get('fabric_provided'),
        request.form.get('measurements'), request.form.get('design_notes'), request.form['total_price'],
        request.form.get('advance_paid') or 0, request.form.get('delivery_date') or None,
        request.form.get('assigned_tailor') or None,
    ))
    flash('Tailoring order created!', 'success')
    return redirect(url_for('tailoring'))

@app.route('/tailoring/status/<int:tid>/<status>')
@login_required
def update_tailoring_status(tid, status):
    execute_query("UPDATE tailoring_orders SET status=%s WHERE tailoring_id=%s", (status, tid))
    flash('Tailoring status updated', 'success')
    return redirect(url_for('tailoring'))

# --- CHATBOT ROUTE ---
@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a helpful customer support assistant for a Boutique Management System. Keep your answers short and polite."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = completion.choices[0].message.content
        return jsonify({'reply': reply})
    except Exception as e:
        print("CHATBOT ERROR:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
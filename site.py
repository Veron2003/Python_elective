from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import threading
import time

app = Flask(__name__)

def get_products():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return products

@app.route('/')
def index():
    products = get_products()
    return render_template('index.html', products=products)

@app.route('/update_product', methods=['POST'])
def update_product():
    product_id = request.form.get('product_id')
    new_id = request.form.get('new_id')
    new_name = request.form.get('new_name')
    price = request.form.get('price')
    quantity = request.form.get('quantity')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Update product details
    c.execute("UPDATE products SET id = ?, name = ?, price = ?, quantity = ? WHERE id = ?", 
              (new_id, new_name, price, quantity, product_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/restock_product', methods=['POST'])
def restock_product():
    product_id = request.form.get('restock_id')
    restock_quantity = request.form.get('restock_quantity')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Update product quantity
    c.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", 
              (restock_quantity, product_id))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

def vending_machine():
    # Include your existing vending machine logic here
    while True:
        # Example logic, replace with your actual vending machine logic
        print("Vending machine running...")
        time.sleep(1)  # Simulate vending machine activity

if __name__ == '__main__':
    # Start the vending machine thread
    t1 = threading.Thread(target=vending_machine)
    t1.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=8080)  # Replace with your desired IP and port

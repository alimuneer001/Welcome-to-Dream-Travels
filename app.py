from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
from datetime import datetime
import os
import hashlib
import functools
import json
import uuid

# Get the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(basedir, 'templates'),
            static_folder=os.path.join(basedir, 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Database path - use /tmp on Vercel for writable location
DB_PATH = os.environ.get('DB_PATH', 'travel.db')

# Database initialization
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS destination
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT NOT NULL,
                  price REAL NOT NULL,
                  image_url TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS booking
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  destination_id INTEGER NOT NULL,
                  travel_date TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (destination_id) REFERENCES destination (id))''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS user
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  is_admin INTEGER DEFAULT 0,
                  created_at TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  order_number TEXT NOT NULL,
                  total_amount REAL NOT NULL,
                  payment_method TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES user (id))''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS order_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  order_id INTEGER NOT NULL,
                  destination_id INTEGER NOT NULL,
                  quantity INTEGER NOT NULL,
                  price REAL NOT NULL,
                  travel_date TEXT NOT NULL,
                  FOREIGN KEY (order_id) REFERENCES orders (id),
                  FOREIGN KEY (destination_id) REFERENCES destination (id))''')
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Cart Management Functions
def get_cart():
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']

def add_to_cart(destination_id, price, travel_date, quantity=1):
    cart = get_cart()
    
    # Check if item is already in cart
    for item in cart:
        if item['destination_id'] == destination_id and item['travel_date'] == travel_date:
            item['quantity'] += quantity
            session.modified = True
            return
    
    # Add new item to cart
    cart.append({
        'destination_id': destination_id,
        'price': price,
        'travel_date': travel_date,
        'quantity': quantity
    })
    session.modified = True

def remove_from_cart(index):
    cart = get_cart()
    if 0 <= index < len(cart):
        del cart[index]
        session.modified = True

def get_cart_total():
    cart = get_cart()
    return sum(item['price'] * item['quantity'] for item in cart)

def clear_cart():
    session['cart'] = []

# User Authentication Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        if not session.get('is_admin'):
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    conn = get_db()
    destinations = conn.execute('SELECT * FROM destination').fetchall()
    conn.close()
    return render_template('home.html', destinations=destinations)

@app.route('/destination/<int:id>')
def destination_detail(id):
    conn = get_db()
    destination = conn.execute('SELECT * FROM destination WHERE id = ?', (id,)).fetchone()
    conn.close()
    if destination is None:
        flash('Destination not found', 'error')
        return redirect(url_for('home'))
    return render_template('destination_detail.html', destination=destination)

@app.route('/add-to-cart/<int:destination_id>', methods=['POST'])
@login_required
def add_destination_to_cart(destination_id):
    travel_date = request.form.get('travel_date')
    quantity = int(request.form.get('quantity', 1))
    
    if not travel_date:
        flash('Please select a travel date', 'error')
        return redirect(url_for('destination_detail', id=destination_id))
    
    conn = get_db()
    destination = conn.execute('SELECT * FROM destination WHERE id = ?', (destination_id,)).fetchone()
    conn.close()
    
    if destination is None:
        flash('Destination not found', 'error')
        return redirect(url_for('home'))
    
    add_to_cart(destination_id, destination['price'], travel_date, quantity)
    flash(f'Added {destination["name"]} to your cart', 'success')
    
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    conn = get_db()
    cart_items = []
    
    for index, item in enumerate(get_cart()):
        destination = conn.execute('SELECT * FROM destination WHERE id = ?', (item['destination_id'],)).fetchone()
        if destination:
            cart_items.append({
                'index': index,
                'destination': dict(destination),
                'travel_date': item['travel_date'],
                'quantity': item['quantity'],
                'subtotal': item['price'] * item['quantity']
            })
    
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total=get_cart_total())

@app.route('/cart/remove/<int:index>', methods=['POST'])
@login_required
def remove_item_from_cart(index):
    remove_from_cart(index)
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if not get_cart():
        flash('Your cart is empty', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        if not payment_method:
            flash('Please select a payment method', 'error')
            return redirect(url_for('checkout'))
        
        conn = get_db()
        try:
            # Create new order
            order_number = str(uuid.uuid4()).replace('-', '')[:10].upper()
            
            conn.execute('''INSERT INTO orders
                          (user_id, order_number, total_amount, payment_method, status, created_at)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (session['user_id'], order_number, get_cart_total(), payment_method, 'Completed',
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            
            # Get the order ID
            order = conn.execute('SELECT id FROM orders WHERE order_number = ?', (order_number,)).fetchone()
            order_id = order['id']
            
            # Add order items
            for item in get_cart():
                conn.execute('''INSERT INTO order_items
                              (order_id, destination_id, quantity, price, travel_date)
                              VALUES (?, ?, ?, ?, ?)''',
                           (order_id, item['destination_id'], item['quantity'], item['price'], item['travel_date']))
            
            conn.commit()
            
            # Clear cart after successful order
            clear_cart()
            
            flash('Your order has been placed successfully!', 'success')
            return render_template('order_confirmation.html', order_number=order_number)
            
        except Exception as e:
            flash(f'Error processing your order: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('checkout.html', cart_total=get_cart_total())

@app.route('/book/<int:destination_id>', methods=['GET', 'POST'])
@login_required
def book_trip(destination_id):
    conn = get_db()
    destination = conn.execute('SELECT * FROM destination WHERE id = ?', (destination_id,)).fetchone()
    
    if destination is None:
        conn.close()
        flash('Destination not found', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            travel_date = request.form.get('travel_date')
            if travel_date:
                # Add to cart instead of direct booking
                add_to_cart(destination_id, destination['price'], travel_date)
                flash(f'Added {destination["name"]} to your cart', 'success')
                return redirect(url_for('cart'))
            else:
                flash('Please select a travel date', 'error')
        except Exception as e:
            flash(f'Error adding to cart: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('booking.html', destination=destination)

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Authentication Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        conn = get_db()
        try:
            # Check if username or email already exists
            existing_user = conn.execute('SELECT id FROM user WHERE username = ? OR email = ?', 
                                       (username, email)).fetchone()
            if existing_user:
                flash('Username or email already exists', 'error')
                return render_template('signup.html')
                
            # Create new user
            hashed_password = hash_password(password)
            conn.execute('INSERT INTO user (username, email, password, created_at) VALUES (?, ?, ?, ?)',
                        (username, email, hashed_password, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            
            # Get the new user
            user = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
            
            # Set session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
        finally:
            conn.close()
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not all([username, password]):
            flash('All fields are required', 'error')
            return render_template('login.html')
        
        conn = get_db()
        try:
            # Get user
            user = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
            
            if not user or user['password'] != hash_password(password):
                flash('Invalid username or password', 'error')
                return render_template('login.html')
            
            # Set session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            
            next_page = request.args.get('next', url_for('home'))
            flash('Logged in successfully!', 'success')
            return redirect(next_page)
        except Exception as e:
            flash(f'Error logging in: {str(e)}', 'error')
        finally:
            conn.close()
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
@admin_required
def admin():
    conn = get_db()
    destinations = conn.execute('SELECT * FROM destination').fetchall()
    bookings = conn.execute('''
        SELECT b.*, d.name as destination_name 
        FROM booking b
        JOIN destination d ON b.destination_id = d.id
        ORDER BY b.created_at DESC
    ''').fetchall()
    
    # Get orders for admin
    orders = conn.execute('''
        SELECT o.*, u.username 
        FROM orders o
        JOIN user u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    ''').fetchall()
    
    conn.close()
    return render_template('admin.html', destinations=destinations, bookings=bookings, orders=orders)

@app.route('/admin/destination/delete/<int:id>', methods=['POST'])
@admin_required
def delete_destination(id):
    conn = get_db()
    try:
        # Check if the destination has bookings
        bookings = conn.execute('SELECT COUNT(*) FROM booking WHERE destination_id = ?', (id,)).fetchone()[0]
        if bookings > 0:
            flash(f'Cannot delete destination. It has {bookings} bookings.', 'error')
        else:
            conn.execute('DELETE FROM destination WHERE id = ?', (id,))
            conn.commit()
            flash('Destination deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting destination: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/booking/delete/<int:id>', methods=['POST'])
@admin_required
def delete_booking(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM booking WHERE id = ?', (id,))
        conn.commit()
        flash('Booking deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting booking: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

# Add sample destinations if none exist
def add_sample_destinations():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM destination').fetchone()[0]
    if count == 0:
        destinations = [
            ('Paris, France',
             'Experience the city of love with its iconic Eiffel Tower, world-class museums, and charming cafes.',
             1299.99,
             'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?q=80&w=1000&auto=format&fit=crop'),
            ('Bali, Indonesia',
             'Discover tropical paradise with pristine beaches, ancient temples, and vibrant culture.',
             899.99,
             'https://images.unsplash.com/photo-1584810359583-96fc3448beaa?q=80&w=1000&auto=format&fit=crop'),
            ('Tokyo, Japan',
             'Explore the perfect blend of traditional culture and modern technology in Japan\'s capital.',
             1499.99,
             'https://images.unsplash.com/photo-1503899036084-c55cdd92da26?q=80&w=1000&auto=format&fit=crop'),
            ('Santorini, Greece',
             'Enjoy breathtaking sunsets, white-washed buildings, and crystal-clear waters in this Mediterranean paradise.',
             1899.99,
             'https://images.unsplash.com/photo-1613395877344-13d4a8e0d49e?q=80&w=1000&auto=format&fit=crop'),
            ('New York City, USA',
             'Visit the city that never sleeps with its iconic skyline, Broadway shows, and diverse neighborhoods.',
             1599.99,
             'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?q=80&w=1000&auto=format&fit=crop'),
            ('Machu Picchu, Peru',
             'Discover the ancient Incan citadel set high in the Andes Mountains, a UNESCO World Heritage site.',
             2199.99,
             'https://images.unsplash.com/photo-1587595431973-160d0d94add1?q=80&w=1000&auto=format&fit=crop')
        ]
        conn.executemany('''INSERT INTO destination (name, description, price, image_url)
                           VALUES (?, ?, ?, ?)''', destinations)
        conn.commit()
    conn.close()

# Add an admin user if none exists
def add_admin_user():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM user WHERE is_admin = 1').fetchone()[0]
    if count == 0:
        conn.execute('''INSERT INTO user 
                      (username, email, password, is_admin, created_at) 
                      VALUES (?, ?, ?, ?, ?)''',
                   ('admin', 'admin@dreamtravels.com', hash_password('admin123'), 1, 
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        print("Admin user created with username: 'admin' and password: 'admin123'")
    conn.close()

if __name__ == '__main__':
    init_db()
    add_sample_destinations()
    add_admin_user()
    app.run(debug=True) 
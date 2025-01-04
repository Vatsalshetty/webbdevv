from flask import Flask, request, jsonify, render_template, session  , redirect , url_for# Add session
# from flask_sqlalchemy import SQLAlchemy  # Remove SQLAlchemy import
from flask_wtf.csrf import CSRFProtect
from flask_session import Session  # For session management
import logging
from werkzeug.security import generate_password_hash, check_password_hash  # Add this import
from cs50 import SQL  # Add CS50 SQL import

# App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///canteen.db'  # SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Add this line
app.config['SESSION_TYPE'] = 'filesystem'  # Required for sessions
csrf = CSRFProtect(app)  # Add this line
Session(app)  # Initialize session management
# db = SQLAlchemy(app)  # Remove SQLAlchemy initialization
db = SQL("sqlite:///canteen.db")  # Initialize CS50 SQL

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Remove SQLAlchemy Models
# # Models
# class User(db.Model):
#     __tablename__ = 'signup'
#     id = db.Column(db.Integer, primary_key=True)
#     first_name = db.Column(db.String(50), nullable=False)
#     last_name = db.Column(db.String(50), nullable=False)
#     email = db.Column(db.String(100), unique=True, nullable=False)
#     phone = db.Column(db.String(20), nullable=False)
#     password = db.Column(db.String(100), nullable=False)

# class MenuItem(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     price = db.Column(db.Float, nullable=False)
#     is_available = db.Column(db.Boolean, default=True)

# class Order(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('signup.id'))  # Fixed table reference
#     total_amount = db.Column(db.Float)
#     status = db.Column(db.String(50), default="Pending")
#     items = db.relationship('OrderItem', backref='order', lazy=True)

# class OrderItem(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'))
#     quantity = db.Column(db.Integer, nullable=False)
#     order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

# Initialize database
# with app.app_context():
#     db.create_all()
# Remove SQLAlchemy initialization

# Routes

canteens = [
    {"name": "Old VK", "menu": ["Dosa", "Idli", "Tea", "Coffee"]},
    {"name": "Library Canteen", "menu": ["Burger", "Sandwich", "Coffee"]},
    {"name": "Vidyarthi Khaana", "menu": ["Rice Bowl", "Paneer Tikka", "Lassi"]},
    {"name": "Hostel Mess", "menu": ["Dal", "Chapati", "Curd"]},
    {"name": "Coffee Kutira", "menu": ["Pizza", "Pasta", "Cola"]},
    {"name": "Nescafe", "menu": ["Fries", "Ice Cream", "Smoothie"]}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/searchres', methods=['GET'])
def searchres():
    query = request.args.get('query', '').strip().lower()
    if not query:
        return render_template('searchres.html', results=[], query=query)

    # Filter canteens based on menu availability
    results = [
        {"canteen": canteen["name"], "menu": item}
        for canteen in canteens
        for item in canteen["menu"]
        if query in item.lower()
    ]

    return render_template('searchres.html', results=results, query=query)

@app.route('/payment_success')
def payment_success():
    total = session.get('grand_total', 0)
    return render_template('suck_payment.html', total=total)

@app.route('/menuu/cart')
def cart():
    return render_template('cart.html')

@app.route('/menuu')
def menuu():
    return render_template("menu.html")

@app.route('/menu', methods=['GET'])
def get_menu():
    menu_items = db.execute("SELECT * FROM menu_item")
    return jsonify([{
        'id': item['id'],
        'name': item['name'],
        'price': item['price'],
        'is_available': item['is_available']
    } for item in menu_items])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
        
    try:
        data = request.form
        app.logger.debug(f"Received data: {data}")
        if not all([data.get('first_name'), data.get('last_name'), 
                   data.get('email'), data.get('phone'), data.get('password')]):
            return jsonify({'message': 'All fields are required'}), 400

        existing_user = db.execute("SELECT * FROM signup WHERE email = ?", data['email'])
        if existing_user:
            return jsonify({'message': 'User with this email already exists'}), 400

        hashed_password = generate_password_hash(data['password'])  # Hash the password
        db.execute(
            "INSERT INTO signup (first_name, last_name, email, phone, password) VALUES (?, ?, ?, ?, ?)",
            data['first_name'], data['last_name'], data['email'], data['phone'], hashed_password
        )
        return jsonify({'message': 'User signed up successfully'}), 201
        
    except Exception as e:
        app.logger.error(f"Error in signup: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    return render_template("index.html")
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return jsonify({'message': 'Missing credentials'}), 400
        
        user = db.execute("SELECT * FROM signup WHERE email = ?", email)
        if not user:
            return jsonify({'message': 'Invalid email or password'}), 401
        
        if not check_password_hash(user[0]['password'], password):
            return jsonify({'message': 'Invalid email or password'}), 401
        print("hello")
        session['user_id'] = user[0]['id']
        # Return a success message for front-end redirect
        return redirect(url_for('index'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500      

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        cart = session.get('cart', [])
        
        # Check if item already exists in cart
        for item in cart:
            if item['name'] == data['name']:
                item['quantity'] += 1
                break
        else:
            cart.append({
                'name': data['name'],
                'price': float(data['price']),
                'quantity': 1
            })
            
        session['cart'] = cart
        return jsonify({'message': 'Item added to cart', 'cart': cart}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.json
    cart = session.get('cart', [])
    if 0 <= data['index'] < len(cart):
        cart.pop(data['index'])
        session['cart'] = cart
    return jsonify({'message': 'Item removed from cart'})

@app.route('/update_total', methods=['POST'])
def update_total():
    data = request.json
    session['grand_total'] = data['total']
    return jsonify({'message': 'Total updated in session'})

# CSRF Exemptions
csrf.exempt(signup)  # Exempt signup route from CSRF
csrf.exempt(login)   # Exempt login route from CSRF
csrf.exempt(add_to_cart)
csrf.exempt(remove_from_cart)
csrf.exempt(update_total)

@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data['userId']
    items = data['items']

    try:
        total_amount = 0
        for item in items:
            menu_item = db.execute("SELECT * FROM menu_item WHERE id = ?", item['menuItem'])
            if not menu_item or not menu_item[0]['is_available']:
                return jsonify({'message': 'Invalid or unavailable menu item'}), 400
            total_amount += menu_item[0]['price'] * item['quantity']

        result = db.execute(
            "INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, ?)",
            user_id, total_amount, "Pending"
        )
        order_id = result.lastrowid

        for item in items:
            db.execute(
                "INSERT INTO order_item (menu_item_id, quantity, order_id) VALUES (?, ?, ?)",
                item['menuItem'], item['quantity'], order_id
            )

        return jsonify({'message': 'Order created successfully', 'order_id': order_id}), 201

    except Exception as e:
        app.logger.error(f"Error in create_order: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/get_cart')
def get_cart():
    return jsonify(session.get('cart', []))

@app.route('/orders/<int:user_id>', methods=['GET'])
def get_orders(user_id):
    orders = db.execute("SELECT * FROM orders WHERE user_id = ?", user_id)
    if not orders:
        return jsonify({'message': 'No orders found'}), 404

    result = []
    for order in orders:
        items = db.execute("SELECT * FROM order_item WHERE order_id = ?", order['id'])
        result.append({
            'order_id': order['id'],
            'total_amount': order['total_amount'],
            'status': order['status'],
            'items': [{
                'menu_item_id': item['menu_item_id'],
                'quantity': item['quantity']
            } for item in items]
        })
    return jsonify(result)

@app.route('/generate_qr')
def generate_qr():
    # Placeholder code to generate the QR
    return "QR generation logic goes here"


if __name__ == '__main__':
    app.run(debug=True)

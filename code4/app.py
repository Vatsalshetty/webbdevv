from flask import Flask, request, jsonify, render_template, session  # add session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///canteen.db'  # SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Add this line
csrf = CSRFProtect(app)  # Add this line
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(50), default="Pending")
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'))
    quantity = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

# Initialize database
with app.app_context():
    db.create_all()

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

@app.route('/signnup')
def signnup():
    return render_template("signup.html")

@app.route('/menuu')
def menuu():
    return render_template("menu.html")

@app.route('/menu', methods=['GET'])
def get_menu():
    menu_items = MenuItem.query.all()
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'price': item.price,
        'is_available': item.is_available
    } for item in menu_items])

@app.route('/signup', methods=['POST'])
def signup():
    data = request.form
    user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password=data['password']
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User signed up successfully'}), 201

@app.route('/login')
def login():
    return render_template("signup.html")

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data['userId']
    items = data['items']

    total_amount = 0
    for item in items:
        menu_item = MenuItem.query.get(item['menuItem'])
        if not menu_item or not menu_item.is_available:
            return jsonify({'message': 'Invalid or unavailable menu item'}), 400
        total_amount += menu_item.price * item['quantity']

    order = Order(user_id=user_id, total_amount=total_amount)
    db.session.add(order)
    db.session.commit()

    for item in items:
        order_item = OrderItem(
            menu_item_id=item['menuItem'],
            quantity=item['quantity'],
            order_id=order.id
        )
        db.session.add(order_item)

    db.session.commit()
    return jsonify({'message': 'Order created successfully', 'order_id': order.id}), 201

@app.route('/orders/<int:user_id>', methods=['GET'])
def get_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    if not orders:
        return jsonify({'message': 'No orders found'}), 404

    result = []
    for order in orders:
        items = [{
            'menu_item_id': item.menu_item_id,
            'quantity': item.quantity
        } for item in order.items]
        result.append({
            'order_id': order.id,
            'total_amount': order.total_amount,
            'status': order.status,
            'items': items
        })
    return jsonify(result)

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/generate_qr')
def generate_qr():
    # Placeholder code to generate the QR
    return "QR generation logic goes here"

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

@app.route('/get_cart')
def get_cart():
    return jsonify(session.get('cart', []))

@app.route('/update_total', methods=['POST'])
def update_total():
    data = request.json
    session['grand_total'] = data['total']
    return jsonify({'message': 'Total updated in session'})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.json
    cart = session.get('cart', [])
    if 0 <= data['index'] < len(cart):
        cart.pop(data['index'])
        session['cart'] = cart
    return jsonify({'message': 'Item removed from cart'})

# Exempt these routes from CSRF protection
csrf.exempt(add_to_cart)
csrf.exempt(remove_from_cart)
csrf.exempt(update_total)

if __name__ == '__main__':
    app.run(debug=True)
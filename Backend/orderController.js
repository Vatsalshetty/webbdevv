const Order = require('../models/orderModel');
const Restaurant = require('../models/restaurantModel');

exports.createOrder = async (req, res) => {
  try {
    const { restaurantId, items, userId } = req.body;

    const restaurant = await Restaurant.findById(restaurantId);
    if (!restaurant) {
      return res.status(404).json({ message: 'Restaurant not found' });
    }

    if (!restaurant.isOpen) {
      return res.status(400).json({ message: 'Restaurant is closed' });
    }

    let totalAmount = 0;
    for (const item of items) {
      const menuItem = restaurant.menuItems.id(item.menuItem);
      if (!menuItem) {
        return res.status(404).json({ message: `Menu item not found` });
      }
      if (!menuItem.isAvailable) {
        return res.status(400).json({ message: `${menuItem.name} is not available` });
      }
      totalAmount += menuItem.price * item.quantity;
    }

    const order = new Order({
      restaurant: restaurantId,
      userId,
      items,
      totalAmount
    });

    const savedOrder = await order.save();
    res.status(201).json(savedOrder);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

exports.getOrderById = async (req, res) => {
  try {
    const order = await Order.findById(req.params.id)
      .populate('restaurant')
      .populate('items.menuItem');
    if (!order) {
      return res.status(404).json({ message: 'Order not found' });
    }
    res.json(order);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.updateOrderStatus = async (req, res) => {
  try {
    const { status } = req.body;
    const order = await Order.findByIdAndUpdate(
      req.params.id,
      { status },
      { new: true }
    );
    if (!order) {
      return res.status(404).json({ message: 'Order not found' });
    }
    res.json(order);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

exports.getUserOrders = async (req, res) => {
  try {
    const orders = await Order.find({ userId: req.params.userId })
      .populate('restaurant')
      .populate('items.menuItem')
      .sort({ createdAt: -1 });
    res.json(orders);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

//Flask 

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'  # Adjust URI accordingly
db = SQLAlchemy(app)

# Define your models

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    is_open = db.Column(db.Boolean, default=True)
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    is_available = db.Column(db.Boolean, default=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    user_id = db.Column(db.Integer)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(50))
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'))
    quantity = db.Column(db.Integer)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

# Create the tables
with app.app_context():
    db.create_all()

# Create the order API routes

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        restaurant_id = data['restaurantId']
        items = data['items']
        user_id = data['userId']

        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({'message': 'Restaurant not found'}), 404

        if not restaurant.is_open:
            return jsonify({'message': 'Restaurant is closed'}), 400

        total_amount = 0
        for item in items:
            menu_item = MenuItem.query.get(item['menuItem'])
            if not menu_item:
                return jsonify({'message': 'Menu item not found'}), 404
            if not menu_item.is_available:
                return jsonify({'message': f'{menu_item.name} is not available'}), 400
            total_amount += menu_item.price * item['quantity']

        order = Order(
            restaurant_id=restaurant_id,
            user_id=user_id,
            total_amount=total_amount,
            status="Pending"  # Default status
        )
        db.session.add(order)
        db.session.commit()

        # Add items to order
        for item in items:
            order_item = OrderItem(
                menu_item_id=item['menuItem'],
                quantity=item['quantity'],
                order_id=order.id
            )
            db.session.add(order_item)

        db.session.commit()

        return jsonify(order), 201
    except Exception as error:
        return jsonify({'message': str(error)}), 400

@app.route('/orders/<int:id>', methods=['GET'])
def get_order_by_id(id):
    try:
        order = Order.query.get(id)
        if not order:
            return jsonify({'message': 'Order not found'}), 404
        
        order_items = [{
            'menuItem': item.menu_item.name,
            'quantity': item.quantity
        } for item in order.items]
        
        return jsonify({
            'id': order.id,
            'restaurantId': order.restaurant_id,
            'userId': order.user_id,
            'totalAmount': order.total_amount,
            'status': order.status,
            'items': order_items
        }), 200
    except Exception as error:
        return jsonify({'message': str(error)}), 500

@app.route('/orders/<int:id>', methods=['PUT'])
def update_order_status(id):
    try:
        data = request.get_json()
        status = data['status']

        order = Order.query.get(id)
        if not order:
            return jsonify({'message': 'Order not found'}), 404

        order.status = status
        db.session.commit()

        return jsonify(order), 200
    except Exception as error:
        return jsonify({'message': str(error)}), 400

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    try:
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
        if not orders:
            return jsonify({'message': 'No orders found for this user'}), 404

        result = []
        for order in orders:
            order_items = [{
                'menuItem': item.menu_item.name,
                'quantity': item.quantity
            } for item in order.items]
            
            result.append({
                'id': order.id,
                'restaurantId': order.restaurant_id,
                'userId': order.user_id,
                'totalAmount': order.total_amount,
                'status': order.status,
                'items': order_items
            })

        return jsonify(result), 200
    except Exception as error:
        return jsonify({'message': str(error)}), 500

if __name__ == '__main__':
    app.run(debug=True)

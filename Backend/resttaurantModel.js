const mongoose = require('mongoose');

const menuItemSchema = new mongoose.Schema({
  name: { type: String, required: true },
  description: { type: String, required: true },
  price: { type: Number, required: true },
  category: { type: String, required: true },
  isAvailable: { type: Boolean, default: true }
});

const restaurantSchema = new mongoose.Schema({
  name: { type: String, required: true },
  cuisine: { type: String, required: true },
  address: { type: String, required: true },
  rating: { type: Number, default: 0 },
  menuItems: [menuItemSchema],
  isOpen: { type: Boolean, default: true }
});

module.exports = mongoose.model('Restaurant', restaurantSchema);
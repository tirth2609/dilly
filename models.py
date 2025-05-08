from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True)
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    banquet_bookings = db.relationship('BanquetBooking', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address_line1 = db.Column(db.String(128), nullable=False)
    address_line2 = db.Column(db.String(128), nullable=True)
    city = db.Column(db.String(64), nullable=False)
    state = db.Column(db.String(64), nullable=False)
    postal_code = db.Column(db.String(16), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Address {self.address_line1}, {self.city}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=0)
    
    # Relationships
    menu_items = db.relationship('MenuItem', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)  # Price in INR
    image_url = db.Column(db.String(256), nullable=True)
    is_vegan = db.Column(db.Boolean, default=False)
    is_gluten_free = db.Column(db.Boolean, default=False)
    is_jain = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for guest bookings
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    special_requests = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='confirmed')  # confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Reservation {self.id}: {self.name} on {self.date} at {self.time}>'

class BanquetBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for guest bookings
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    requirements = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='pending')  # pending, confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BanquetBooking {self.id}: {self.name}, {self.event_type} on {self.date}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for guest orders
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    order_type = db.Column(db.String(32), default='takeaway')  # Always takeaway
    table_number = db.Column(db.Integer, nullable=True)  # For future dine-in orders if needed
    special_instructions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='pending')  # pending, preparing, ready, completed, cancelled
    total_amount = db.Column(db.Float, nullable=False)  # Total in INR
    payment_method = db.Column(db.String(32), nullable=False)  # counter, qr_code
    payment_status = db.Column(db.String(32), default='pending')  # pending, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.id}: {self.name}, ₹{self.total_amount}, {self.status}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of order in INR
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<OrderItem {self.id}: {self.menu_item_id}, Qty: {self.quantity}>'

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(10), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Available')  # Available, Occupied, Reserved, Unavailable
    description = db.Column(db.Text, nullable=True)
    qr_code_active = db.Column(db.Boolean, default=True)
    position_x = db.Column(db.Integer, nullable=True)  # For visual layout positioning
    position_y = db.Column(db.Integer, nullable=True)  # For visual layout positioning
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # We'll make table_number in Order table reference this table later
    # orders = db.relationship('Order', backref='table', lazy=True, foreign_keys='Order.table_number')
    
    def __repr__(self):
        return f'<Table {self.table_number}, Capacity: {self.capacity}, Status: {self.status}>'

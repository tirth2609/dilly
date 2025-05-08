from flask import render_template, url_for, flash, redirect, request, jsonify, session, abort
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime, time, timedelta
import json
import qrcode
import base64
import io
import os
from app import db
from models import User, MenuItem, Category, Reservation, BanquetBooking, Order, OrderItem, Address
from forms import (
    RegistrationForm, LoginForm, ReservationForm, BanquetBookingForm, 
    AddressForm, OrderForm, TrackOrderForm
)
from utils import save_image, generate_qr_code_data

def init_routes(app):
    
    @app.route('/')
    @app.route('/home')
    def home():
        featured_items = MenuItem.query.filter_by(is_available=True).limit(6).all()
        categories = Category.query.order_by(Category.display_order).all()
        return render_template('index.html', featured_items=featured_items, categories=categories)
    
    @app.route('/menu')
    def menu():
        categories = Category.query.order_by(Category.display_order).all()
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        return render_template('menu.html', categories=categories, menu_items=menu_items)
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/reservation', methods=['GET', 'POST'])
    def reservation():
        form = ReservationForm()
        if form.validate_on_submit():
            reservation = Reservation(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                date=form.date.data,
                time=datetime.strptime(form.time.data, '%H:%M').time(),
                guests=form.guests.data,
                special_requests=form.special_requests.data,
                status='confirmed',
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(reservation)
            db.session.commit()
            flash('Your reservation has been confirmed!', 'success')
            return redirect(url_for('reservation_success', reservation_id=reservation.id))
        return render_template('reservation.html', form=form)
    
    @app.route('/reservation/success/<int:reservation_id>')
    def reservation_success(reservation_id):
        reservation = Reservation.query.get_or_404(reservation_id)
        return render_template('reservation_success.html', reservation=reservation)
    
    @app.route('/banquet', methods=['GET', 'POST'])
    def banquet():
        form = BanquetBookingForm()
        if form.validate_on_submit():
            booking = BanquetBooking(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                event_type=form.event_type.data,
                date=form.date.data,
                time=datetime.strptime(form.time.data, '%H:%M').time(),
                guests=form.guests.data,
                requirements=form.requirements.data,
                status='pending',
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(booking)
            db.session.commit()
            flash('Your banquet booking request has been submitted. We will contact you shortly to confirm details.', 'success')
            return redirect(url_for('banquet_success', booking_id=booking.id))
        return render_template('banquet.html', form=form)
    
    @app.route('/banquet/success/<int:booking_id>')
    def banquet_success(booking_id):
        booking = BanquetBooking.query.get_or_404(booking_id)
        return render_template('banquet_success.html', booking=booking)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                phone=form.phone.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash('You have been logged in successfully!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash('Login unsuccessful. Please check your email and password.', 'danger')
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))
    
    @app.route('/profile')
    @login_required
    def profile():
        user_reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.date.desc()).all()
        user_banquets = BanquetBooking.query.filter_by(user_id=current_user.id).order_by(BanquetBooking.date.desc()).all()
        user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        user_addresses = Address.query.filter_by(user_id=current_user.id).all()
        return render_template('profile.html', 
                              reservations=user_reservations, 
                              banquets=user_banquets, 
                              orders=user_orders,
                              addresses=user_addresses)
    
    @app.route('/profile/address/add', methods=['GET', 'POST'])
    @login_required
    def add_address():
        form = AddressForm()
        if form.validate_on_submit():
            if form.is_default.data:
                # Set all other addresses to not default
                Address.query.filter_by(user_id=current_user.id, is_default=True).update({Address.is_default: False})
                
            address = Address(
                user_id=current_user.id,
                address_line1=form.address_line1.data,
                address_line2=form.address_line2.data,
                city=form.city.data,
                state=form.state.data,
                postal_code=form.postal_code.data,
                is_default=form.is_default.data
            )
            db.session.add(address)
            db.session.commit()
            flash('Address added successfully!', 'success')
            return redirect(url_for('profile'))
        return render_template('address_form.html', form=form, title='Add Address')
    
    @app.route('/profile/address/edit/<int:address_id>', methods=['GET', 'POST'])
    @login_required
    def edit_address(address_id):
        address = Address.query.get_or_404(address_id)
        if address.user_id != current_user.id:
            abort(403)
            
        form = AddressForm()
        if form.validate_on_submit():
            if form.is_default.data and not address.is_default:
                # Set all other addresses to not default
                Address.query.filter_by(user_id=current_user.id, is_default=True).update({Address.is_default: False})
                
            address.address_line1 = form.address_line1.data
            address.address_line2 = form.address_line2.data
            address.city = form.city.data
            address.state = form.state.data
            address.postal_code = form.postal_code.data
            address.is_default = form.is_default.data
            
            db.session.commit()
            flash('Address updated successfully!', 'success')
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.address_line1.data = address.address_line1
            form.address_line2.data = address.address_line2
            form.city.data = address.city
            form.state.data = address.state
            form.postal_code.data = address.postal_code
            form.is_default.data = address.is_default
            
        return render_template('address_form.html', form=form, title='Edit Address')
    
    @app.route('/profile/address/delete/<int:address_id>', methods=['POST'])
    @login_required
    def delete_address(address_id):
        address = Address.query.get_or_404(address_id)
        if address.user_id != current_user.id:
            abort(403)
            
        db.session.delete(address)
        db.session.commit()
        flash('Address deleted successfully!', 'success')
        return redirect(url_for('profile'))
    
    @app.route('/qr-menu')
    def qr_menu():
        table_id = request.args.get('table', '1')
        categories = Category.query.order_by(Category.display_order).all()
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        return render_template('qr_menu.html', 
                              categories=categories, 
                              menu_items=menu_items, 
                              table_id=table_id)
    
    @app.route('/qr-menu/order', methods=['POST'])
    def qr_menu_order():
        data = request.json
        table_id = data.get('table_id')
        items = data.get('items', [])
        
        if not items:
            return jsonify({'error': 'No items in order'}), 400
            
        # Calculate total
        total_amount = 0
        for item in items:
            menu_item = MenuItem.query.get(item['id'])
            if not menu_item:
                return jsonify({'error': f'Menu item {item["id"]} not found'}), 400
            total_amount += menu_item.price * item['quantity']
            
        # Create order
        order = Order(
            name=data.get('name', 'Table Customer'),
            email=data.get('email', 'table@example.com'),
            phone=data.get('phone', '0000000000'),
            order_type='dine-in',
            table_number=int(table_id),
            special_instructions=data.get('special_instructions', ''),
            total_amount=total_amount,
            payment_method='counter',
            payment_status='pending',
            status='pending',
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(order)
        db.session.flush()  # To get the order ID
        
        # Add order items
        for item in items:
            menu_item = MenuItem.query.get(item['id'])
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                quantity=item['quantity'],
                price=menu_item.price,
                notes=item.get('notes', '')
            )
            db.session.add(order_item)
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Your order has been placed. Please pay at the counter after your meal.'
        })
    
    @app.route('/takeaway', methods=['GET', 'POST'])
    def takeaway():
        categories = Category.query.order_by(Category.display_order).all()
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        
        form = OrderForm()
        
        # If user is logged in, populate address choices
        if current_user.is_authenticated:
            addresses = Address.query.filter_by(user_id=current_user.id).all()
            form.address_id.choices = [(a.id, f"{a.address_line1}, {a.city} - {a.postal_code}") for a in addresses]
            form.address_id.choices.insert(0, (0, 'Select an address'))
        else:
            form.address_id.choices = [(0, 'Please log in to use saved addresses')]
        
        return render_template('takeaway.html', 
                              categories=categories, 
                              menu_items=menu_items,
                              form=form)
    
    @app.route('/takeaway/place-order', methods=['POST'])
    def place_takeaway_order():
        form = OrderForm()
        
        # If user is logged in, populate address choices
        if current_user.is_authenticated:
            addresses = Address.query.filter_by(user_id=current_user.id).all()
            form.address_id.choices = [(a.id, f"{a.address_line1}, {a.city} - {a.postal_code}") for a in addresses]
            form.address_id.choices.insert(0, (0, 'Select an address'))
        else:
            form.address_id.choices = [(0, 'Please log in to use saved addresses')]
        
        if form.validate_on_submit():
            # Get cart from session
            cart = session.get('cart', [])
            if not cart:
                flash('Your cart is empty. Please add items before placing an order.', 'danger')
                return redirect(url_for('takeaway'))
                
            # Calculate total
            total_amount = 0
            for item in cart:
                menu_item = MenuItem.query.get(item['id'])
                if not menu_item:
                    flash(f'One of your items is no longer available.', 'danger')
                    return redirect(url_for('takeaway'))
                total_amount += menu_item.price * item['quantity']
                
            # Validate address for delivery
            if form.order_type.data == 'delivery':
                address_id = form.address_id.data
                if address_id == 0:
                    flash('Please select a delivery address.', 'danger')
                    return redirect(url_for('takeaway'))
                    
                address = Address.query.get(address_id)
                if not address or (current_user.is_authenticated and address.user_id != current_user.id):
                    flash('Invalid delivery address.', 'danger')
                    return redirect(url_for('takeaway'))
            else:
                address_id = None
                
            # Create order
            order = Order(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                order_type=form.order_type.data,
                address_id=address_id,
                special_instructions=form.special_instructions.data,
                total_amount=total_amount,
                payment_method=form.payment_method.data,
                payment_status='pending',
                status='pending',
                user_id=current_user.id if current_user.is_authenticated else None
            )
            
            db.session.add(order)
            db.session.flush()  # To get the order ID
            
            # Add order items
            for item in cart:
                menu_item = MenuItem.query.get(item['id'])
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=item['quantity'],
                    price=menu_item.price,
                    notes=item.get('notes', '')
                )
                db.session.add(order_item)
                
            db.session.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            flash('Your order has been placed successfully!', 'success')
            return redirect(url_for('order_success', order_id=order.id))
        
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
                
        return redirect(url_for('takeaway'))
    
    @app.route('/order/success/<int:order_id>')
    def order_success(order_id):
        order = Order.query.get_or_404(order_id)
        return render_template('order_success.html', order=order)
    
    @app.route('/track-order', methods=['GET', 'POST'])
    def track_order():
        form = TrackOrderForm()
        order = None
        
        if form.validate_on_submit():
            order_id = form.order_id.data
            order = Order.query.get(order_id)
            if not order:
                flash('Order not found. Please check the order ID and try again.', 'danger')
        
        return render_template('track_order.html', form=form, order=order)
    
    # API endpoints for AJAX calls
    
    @app.route('/api/menu/filter', methods=['POST'])
    def filter_menu():
        data = request.json
        filters = data.get('filters', {})
        
        query = MenuItem.query.filter_by(is_available=True)
        
        if filters.get('is_vegan'):
            query = query.filter_by(is_vegan=True)
        if filters.get('is_gluten_free'):
            query = query.filter_by(is_gluten_free=True)
        if filters.get('is_jain'):
            query = query.filter_by(is_jain=True)
        if filters.get('category_id'):
            query = query.filter_by(category_id=filters['category_id'])
            
        menu_items = query.all()
        result = []
        
        for item in menu_items:
            result.append({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': item.price,
                'image_url': item.image_url,
                'is_vegan': item.is_vegan,
                'is_gluten_free': item.is_gluten_free,
                'is_jain': item.is_jain,
                'category_id': item.category_id
            })
            
        return jsonify(result)
    
    @app.route('/api/cart/add', methods=['POST'])
    def add_to_cart():
        data = request.json
        item_id = data.get('id')
        quantity = data.get('quantity', 1)
        notes = data.get('notes', '')
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
            
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return jsonify({'error': 'Menu item not found'}), 404
            
        cart = session.get('cart', [])
        
        # Check if item already in cart
        item_index = None
        for i, item in enumerate(cart):
            if item['id'] == item_id:
                item_index = i
                break
                
        if item_index is not None:
            # Update existing item
            cart[item_index]['quantity'] += quantity
            if notes:
                cart[item_index]['notes'] = notes
        else:
            # Add new item
            cart.append({
                'id': item_id,
                'name': menu_item.name,
                'price': menu_item.price,
                'quantity': quantity,
                'notes': notes
            })
            
        session['cart'] = cart
        
        return jsonify({
            'success': True,
            'cart': cart,
            'message': f'{menu_item.name} added to cart'
        })
    
    @app.route('/api/cart/remove', methods=['POST'])
    def remove_from_cart():
        data = request.json
        item_id = data.get('id')
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
            
        cart = session.get('cart', [])
        
        # Find and remove item
        for i, item in enumerate(cart):
            if item['id'] == item_id:
                del cart[i]
                break
                
        session['cart'] = cart
        
        return jsonify({
            'success': True,
            'cart': cart,
            'message': 'Item removed from cart'
        })
    
    @app.route('/api/cart/update', methods=['POST'])
    def update_cart():
        data = request.json
        item_id = data.get('id')
        quantity = data.get('quantity')
        
        if not item_id or quantity is None:
            return jsonify({'error': 'Item ID and quantity are required'}), 400
            
        cart = session.get('cart', [])
        
        # Find and update item
        for item in cart:
            if item['id'] == item_id:
                if quantity <= 0:
                    cart.remove(item)
                else:
                    item['quantity'] = quantity
                break
                
        session['cart'] = cart
        
        return jsonify({
            'success': True,
            'cart': cart,
            'message': 'Cart updated'
        })
    
    @app.route('/api/cart/clear', methods=['POST'])
    def clear_cart():
        session.pop('cart', None)
        
        return jsonify({
            'success': True,
            'message': 'Cart cleared'
        })
    
    @app.route('/api/cart', methods=['GET'])
    def get_cart():
        cart = session.get('cart', [])
        
        return jsonify({
            'success': True,
            'cart': cart
        })
    
    @app.route('/api/check-time-slots', methods=['POST'])
    def check_time_slots():
        data = request.json
        date_str = data.get('date')
        
        if not date_str:
            return jsonify({'error': 'Date is required'}), 400
            
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
            
        # Get all reservations for the selected date
        reservations = Reservation.query.filter_by(date=selected_date).all()
        
        # Define all time slots
        time_slots = [
            ('12:00', '12:00 PM'), ('12:30', '12:30 PM'), 
            ('13:00', '1:00 PM'), ('13:30', '1:30 PM'),
            ('14:00', '2:00 PM'), ('14:30', '2:30 PM'),
            ('19:00', '7:00 PM'), ('19:30', '7:30 PM'),
            ('20:00', '8:00 PM'), ('20:30', '8:30 PM'),
            ('21:00', '9:00 PM'), ('21:30', '9:30 PM')
        ]
        
        # Count reservations per time slot
        slot_counts = {}
        for res in reservations:
            time_key = res.time.strftime('%H:%M')
            slot_counts[time_key] = slot_counts.get(time_key, 0) + 1
            
        # Assume max 10 reservations per time slot
        max_per_slot = 10
        available_slots = []
        
        for slot in time_slots:
            time_key = slot[0]
            count = slot_counts.get(time_key, 0)
            is_available = count < max_per_slot
            available_slots.append({
                'time': time_key,
                'label': slot[1],
                'available': is_available
            })
            
        return jsonify({
            'success': True,
            'date': date_str,
            'available_slots': available_slots
        })
    
    @app.route('/api/generate-table-qr', methods=['GET'])
    def generate_table_qr():
        table_id = request.args.get('table', '1')
        base_url = request.host_url.rstrip('/')
        qr_url = f'{base_url}/qr-menu?table={table_id}'
        
        qr_image = generate_qr_code_data(qr_url)
        
        return jsonify({
            'success': True,
            'table_id': table_id,
            'qr_data': qr_image
        })
    
    # Error handlers
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error_code=500, error_message='Server error'), 500

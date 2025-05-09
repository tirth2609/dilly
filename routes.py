from flask import render_template, url_for, flash, redirect, request, jsonify, session, abort
from flask_login import login_user, current_user, logout_user, login_required
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime, timedelta, time
from functools import wraps
import json
import qrcode
import base64
import io
import os
from app import db
from models import User, MenuItem, Category, Reservation, BanquetBooking, Order, OrderItem, Address, Table
from forms import (
    RegistrationForm, LoginForm, AdminLoginForm, ReservationForm, BanquetBookingForm, 
    AddressForm, OrderForm, TrackOrderForm, TableForm
)
from utils import save_image, generate_qr_code_data

def init_routes(app):
    # Admin required decorator
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.is_admin:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    
    # Admin Routes
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        # Get statistics for dashboard
        user_count = User.query.count()
        reservation_count = Reservation.query.count()
        order_count = Order.query.count()
        revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
        
        # Recent orders
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        
        # Upcoming reservations
        upcoming_reservations = Reservation.query.filter(
            Reservation.date >= datetime.now().date()
        ).order_by(Reservation.date.asc(), Reservation.time.asc()).limit(5).all()
        
        # Stats for dashboard
        stats = {
            'orders_count': order_count,
            'users_count': user_count,
            'reservations_count': reservation_count,
            'revenue': f"{revenue:.2f}",
            'orders_growth': 15,  # Example values
            'users_growth': 8,
            'reservations_growth': 12,
            'revenue_growth': 10
        }
        
        return render_template('admin/dashboard.html', 
                              stats=stats,
                              datetime=datetime,
                              recent_orders=recent_orders,
                              upcoming_reservations=upcoming_reservations)
    
    # Admin Menu Items
    @app.route('/admin/menu-items')
    @login_required
    @admin_required
    def admin_menu_items():
        categories = Category.query.order_by(Category.display_order).all()
        menu_items = MenuItem.query.all()
        return render_template('admin/menu_items.html', categories=categories, menu_items=menu_items, datetime=datetime)
    
    @app.route('/admin/menu-items/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_menu_item():
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        category_id = request.form.get('category_id')
        is_vegan = 'is_vegan' in request.form
        is_gluten_free = 'is_gluten_free' in request.form
        is_jain = 'is_jain' in request.form
        is_available = 'is_available' in request.form
        
        # Get image URL
        image_url = request.form.get('image_url', '')
            
        # Create new menu item
        menu_item = MenuItem(
            name=name,
            description=description,
            price=float(price),
            category_id=category_id,
            image_url=image_url,
            is_vegan=is_vegan,
            is_gluten_free=is_gluten_free,
            is_jain=is_jain,
            is_available=is_available
        )
        
        db.session.add(menu_item)
        db.session.commit()
        
        flash(f'Menu item "{name}" has been added successfully.', 'success')
        return redirect(url_for('admin_menu_items'))
    
    @app.route('/admin/menu-items/bulk-add', methods=['POST'])
    @login_required
    @admin_required
    def admin_bulk_add_menu_items():
        bulk_items = request.form.get('bulk_items', '')
        default_category_id = request.form.get('default_category_id', '')
        all_available = 'all_available' in request.form
        
        if not bulk_items.strip():
            flash('No items provided for bulk addition.', 'warning')
            return redirect(url_for('admin_menu_items'))
        
        # Process each line
        lines = bulk_items.strip().split('\n')
        added_count = 0
        error_count = 0
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = [part.strip() for part in line.split('|')]
            
            try:
                # Ensure we have at least name, description, price
                if len(parts) < 3:
                    error_count += 1
                    continue
                    
                name = parts[0]
                description = parts[1]
                price = float(parts[2])
                
                # Get category ID (use default if not provided)
                category_id = default_category_id
                if len(parts) > 3 and parts[3].strip():
                    category_id = parts[3]
                
                # Get image URL if provided
                image_url = ''
                if len(parts) > 4 and parts[4].strip():
                    image_url = parts[4]
                
                # Get dietary options if provided
                is_vegan = False
                if len(parts) > 5 and parts[5].strip() in ['1', 'true', 'True', 'yes', 'Yes']:
                    is_vegan = True
                    
                is_gluten_free = False
                if len(parts) > 6 and parts[6].strip() in ['1', 'true', 'True', 'yes', 'Yes']:
                    is_gluten_free = True
                    
                is_jain = False
                if len(parts) > 7 and parts[7].strip() in ['1', 'true', 'True', 'yes', 'Yes']:
                    is_jain = True
                
                # Create new menu item
                menu_item = MenuItem(
                    name=name,
                    description=description,
                    price=price,
                    category_id=category_id,
                    image_url=image_url,
                    is_vegan=is_vegan,
                    is_gluten_free=is_gluten_free,
                    is_jain=is_jain,
                    is_available=all_available
                )
                
                db.session.add(menu_item)
                added_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error adding item '{line}': {str(e)}")
        
        # Commit all changes at once
        if added_count > 0:
            db.session.commit()
            
        if error_count > 0:
            flash(f'Added {added_count} menu items successfully. {error_count} items had errors and were skipped.', 'warning')
        else:
            flash(f'Added {added_count} menu items successfully.', 'success')
            
        return redirect(url_for('admin_menu_items'))
    
    @app.route('/admin/menu-items/edit', methods=['POST'])
    @login_required
    @admin_required
    def admin_edit_menu_item():
        item_id = request.form.get('id')
        menu_item = MenuItem.query.get_or_404(item_id)
        
        menu_item.name = request.form.get('name')
        menu_item.description = request.form.get('description')
        menu_item.price = float(request.form.get('price'))
        menu_item.category_id = request.form.get('category_id')
        menu_item.is_vegan = 'is_vegan' in request.form
        menu_item.is_gluten_free = 'is_gluten_free' in request.form
        menu_item.is_jain = 'is_jain' in request.form
        menu_item.is_available = 'is_available' in request.form
        
        # Handle image URL
        image_url = request.form.get('image_url')
        if image_url:
            menu_item.image_url = image_url
            
        db.session.commit()
        
        flash(f'Menu item "{menu_item.name}" has been updated successfully.', 'success')
        return redirect(url_for('admin_menu_items'))
    
    @app.route('/admin/menu-items/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_menu_item():
        item_id = request.form.get('id')
        menu_item = MenuItem.query.get_or_404(item_id)
        
        name = menu_item.name
        db.session.delete(menu_item)
        db.session.commit()
        
        flash(f'Menu item "{name}" has been deleted successfully.', 'success')
        return redirect(url_for('admin_menu_items'))
    
    # Admin Categories
    @app.route('/admin/categories')
    @login_required
    @admin_required
    def admin_categories():
        categories = Category.query.order_by(Category.display_order).all()
        return render_template('admin/categories.html', categories=categories, datetime=datetime)
    
    @app.route('/admin/categories/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_category():
        name = request.form.get('name')
        description = request.form.get('description', '')
        display_order = request.form.get('display_order', 0)
        
        category = Category(
            name=name,
            description=description,
            display_order=int(display_order)
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category "{name}" has been added successfully.', 'success')
        return redirect(url_for('admin_categories'))
    
    @app.route('/admin/categories/edit', methods=['POST'])
    @login_required
    @admin_required
    def admin_edit_category():
        category_id = request.form.get('id')
        category = Category.query.get_or_404(category_id)
        
        category.name = request.form.get('name')
        category.description = request.form.get('description', '')
        category.display_order = int(request.form.get('display_order', 0))
        
        db.session.commit()
        
        flash(f'Category "{category.name}" has been updated successfully.', 'success')
        return redirect(url_for('admin_categories'))
    
    @app.route('/admin/categories/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_category():
        category_id = request.form.get('id')
        category = Category.query.get_or_404(category_id)
        
        # Check if category has menu items
        if category.menu_items:
            flash(f'Cannot delete category "{category.name}" because it contains menu items.', 'danger')
            return redirect(url_for('admin_categories'))
        
        name = category.name
        db.session.delete(category)
        db.session.commit()
        
        flash(f'Category "{name}" has been deleted successfully.', 'success')
        return redirect(url_for('admin_categories'))
    
    # Admin Reservations
    @app.route('/admin/reservations')
    @login_required
    @admin_required
    def admin_reservations():
        reservations = Reservation.query.order_by(Reservation.date.desc(), Reservation.time.desc()).all()
        return render_template('admin/reservations.html', reservations=reservations, datetime=datetime)
    
    @app.route('/admin/reservations/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_reservation():
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        guests = int(request.form.get('guests'))
        special_requests = request.form.get('special_requests', '')
        status = request.form.get('status', 'confirmed')
        
        reservation = Reservation(
            name=name,
            email=email,
            phone=phone,
            date=date,
            time=time,
            guests=guests,
            special_requests=special_requests,
            status=status
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        flash(f'Reservation for {name} on {date.strftime("%d %b %Y")} has been added successfully.', 'success')
        return redirect(url_for('admin_reservations'))
    
    @app.route('/admin/reservations/edit', methods=['POST'])
    @login_required
    @admin_required
    def admin_edit_reservation():
        reservation_id = request.form.get('id')
        reservation = Reservation.query.get_or_404(reservation_id)
        
        reservation.name = request.form.get('name')
        reservation.email = request.form.get('email')
        reservation.phone = request.form.get('phone')
        reservation.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        reservation.time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        reservation.guests = int(request.form.get('guests'))
        reservation.special_requests = request.form.get('special_requests', '')
        reservation.status = request.form.get('status')
        
        db.session.commit()
        
        flash(f'Reservation for {reservation.name} on {reservation.date.strftime("%d %b %Y")} has been updated successfully.', 'success')
        return redirect(url_for('admin_reservations'))
    
    @app.route('/admin/reservations/cancel', methods=['POST'])
    @login_required
    @admin_required
    def admin_cancel_reservation():
        reservation_id = request.form.get('id')
        reservation = Reservation.query.get_or_404(reservation_id)
        
        reservation.status = 'cancelled'
        db.session.commit()
        
        flash(f'Reservation for {reservation.name} has been cancelled.', 'success')
        return redirect(url_for('admin_reservations'))
    
    # Admin Banquet Bookings
    @app.route('/admin/banquets')
    @login_required
    @admin_required
    def admin_banquets():
        banquet_bookings = BanquetBooking.query.order_by(BanquetBooking.date.desc()).all()
        return render_template('admin/banquets.html', banquet_bookings=banquet_bookings, datetime=datetime)
    
    @app.route('/admin/banquets/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_banquet():
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        event_type = request.form.get('event_type')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        guests = int(request.form.get('guests'))
        requirements = request.form.get('requirements', '')
        status = request.form.get('status', 'pending')
        
        booking = BanquetBooking(
            name=name,
            email=email,
            phone=phone,
            event_type=event_type,
            date=date,
            time=time,
            guests=guests,
            requirements=requirements,
            status=status
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash(f'Banquet booking for {name} on {date.strftime("%d %b %Y")} has been added successfully.', 'success')
        return redirect(url_for('admin_banquets'))
    
    @app.route('/admin/banquets/edit', methods=['POST'])
    @login_required
    @admin_required
    def admin_edit_banquet():
        booking_id = request.form.get('id')
        booking = BanquetBooking.query.get_or_404(booking_id)
        
        booking.name = request.form.get('name')
        booking.email = request.form.get('email')
        booking.phone = request.form.get('phone')
        booking.event_type = request.form.get('event_type')
        booking.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        booking.time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        booking.guests = int(request.form.get('guests'))
        booking.requirements = request.form.get('requirements', '')
        booking.status = request.form.get('status')
        
        db.session.commit()
        
        flash(f'Banquet booking for {booking.name} on {booking.date.strftime("%d %b %Y")} has been updated successfully.', 'success')
        return redirect(url_for('admin_banquets'))
    
    @app.route('/admin/banquets/confirm', methods=['POST'])
    @login_required
    @admin_required
    def admin_confirm_banquet():
        booking_id = request.form.get('id')
        booking = BanquetBooking.query.get_or_404(booking_id)
        
        booking.status = 'confirmed'
        db.session.commit()
        
        flash(f'Banquet booking for {booking.name} has been confirmed.', 'success')
        return redirect(url_for('admin_banquets'))
    
    @app.route('/admin/banquets/cancel', methods=['POST'])
    @login_required
    @admin_required
    def admin_cancel_banquet():
        booking_id = request.form.get('id')
        booking = BanquetBooking.query.get_or_404(booking_id)
        
        booking.status = 'cancelled'
        db.session.commit()
        
        flash(f'Banquet booking for {booking.name} has been cancelled.', 'success')
        return redirect(url_for('admin_banquets'))
    
    # Admin Orders
    @app.route('/admin/orders')
    @login_required
    @admin_required
    def admin_orders():
        orders = Order.query.order_by(Order.created_at.desc()).all()
        categories = Category.query.order_by(Category.display_order).all()
        
        # Calculate today's revenue
        today = datetime.now().date()
        todays_orders = Order.query.filter(
            db.func.date(Order.created_at) == today,
            Order.status != 'cancelled'
        ).all()
        todays_revenue = sum(order.total_amount for order in todays_orders)
        
        # Calculate average order value
        completed_orders = Order.query.filter(Order.status != 'cancelled').all()
        total_orders = len(completed_orders)
        total_revenue = sum(order.total_amount for order in completed_orders)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return render_template('admin/orders.html', 
                              orders=orders,
                              categories=categories,
                              todays_revenue=f"{todays_revenue:.2f}",
                              avg_order_value=f"{avg_order_value:.2f}",
                              datetime=datetime)
    
    @app.route('/admin/orders/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_order():
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        order_type = request.form.get('order_type')
        special_instructions = request.form.get('special_instructions', '')
        payment_method = request.form.get('payment_method')
        payment_status = 'completed' if 'payment_completed' in request.form else 'pending'
        
        # Get order items from JSON
        order_items_json = request.form.get('order_items_json', '[]')
        order_items_data = json.loads(order_items_json)
        
        if not order_items_data:
            flash('Cannot create an order without items.', 'danger')
            return redirect(url_for('admin_orders'))
        
        # Calculate total amount
        total_amount = sum(item['price'] * item['quantity'] for item in order_items_data)
        
        # Create order
        order = Order(
            name=name,
            email=email,
            phone=phone,
            order_type=order_type,
            special_instructions=special_instructions,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status=payment_status,
            status='pending'
        )
        
        # Add table number for dine-in orders
        if order_type == 'dine-in':
            table_number = request.form.get('table_number')
            if table_number:
                order.table_number = int(table_number)
                
        # Add address for delivery orders
        if order_type == 'delivery':
            address = request.form.get('address')
            if address:
                # Create a temporary address for this order
                temp_address = Address(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    address_line1=address,
                    city="Delivery City",  # Default values
                    state="Delivery State",
                    postal_code="000000"
                )
                db.session.add(temp_address)
                db.session.flush()
                order.address_id = temp_address.id
        
        db.session.add(order)
        db.session.flush()  # To get the order ID
        
        # Add order items
        for item_data in order_items_data:
            menu_item = MenuItem.query.get(item_data['id'])
            if menu_item:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=item_data['quantity'],
                    price=menu_item.price,
                    notes=item_data.get('notes', '')
                )
                db.session.add(order_item)
        
        db.session.commit()
        
        flash(f'Order for {name} has been created successfully.', 'success')
        return redirect(url_for('admin_orders'))
    
    @app.route('/admin/orders/update-status', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_order_status():
        order_id = request.form.get('order_id')
        new_status = request.form.get('status')
        payment_status = request.form.get('payment_status')
        
        order = Order.query.get_or_404(order_id)
        old_status = order.status
        order.status = new_status
        order.payment_status = payment_status
        
        # If order is dine-in and status changed to completed, ready, or cancelled, update table status
        if order.order_type == 'dine-in' and order.table_number:
            should_update_table = False
            # Convert the integer to string for table lookup
            table_num_str = str(order.table_number)
            
            # If status changed to completed, free the table
            if new_status == 'completed' and old_status != 'completed':
                should_update_table = True
            # If status changed to cancelled, free the table  
            elif new_status == 'cancelled' and old_status != 'cancelled':
                should_update_table = True
            
            if should_update_table:
                table = Table.query.filter_by(table_number=table_num_str).first()
                if table and table.status == 'Occupied':
                    table.status = 'Available'
                    flash(f'Table {table_num_str} has been marked as Available.', 'info')
            
            # If status changed to active or ready, make sure table is occupied
            if (new_status == 'active' or new_status == 'ready') and old_status not in ['active', 'ready']:
                table = Table.query.filter_by(table_number=table_num_str).first()
                if table and table.status == 'Available':
                    table.status = 'Occupied'
                    flash(f'Table {table_num_str} has been marked as Occupied.', 'info')
        
        db.session.commit()
        
        flash(f'Order #{order_id} status has been updated to {new_status}.', 'success')
        return redirect(url_for('admin_orders'))
    
    @app.route('/admin/orders/cancel', methods=['POST'])
    @login_required
    @admin_required
    def admin_cancel_order():
        order_id = request.form.get('order_id')
        reason = request.form.get('reason', 'Cancelled by admin')
        
        order = Order.query.get_or_404(order_id)
        order.status = 'cancelled'
        order.special_instructions += f"\n\nCancellation reason: {reason}"
        
        # If it's a dine-in order, free up the table
        if order.order_type == 'dine-in' and order.table_number:
            # Convert integer to string for table lookup
            table_num_str = str(order.table_number)
            table = Table.query.filter_by(table_number=table_num_str).first()
            if table and table.status == 'Occupied':
                table.status = 'Available'
                flash(f'Table {table_num_str} has been marked as Available.', 'info')
        
        db.session.commit()
        
        flash(f'Order #{order_id} has been cancelled.', 'success')
        return redirect(url_for('admin_orders'))
    
    # Admin Users
    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        users = User.query.all()
        
        # Calculate stats (this would be more sophisticated in a real app)
        total_users_count = len(users)
        # Assume users from last 30 days are "new"
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_users_count = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        # Sample recent activities
        recent_activities = [
            {'description': 'New user registered', 'date': datetime.now() - timedelta(hours=2)},
            {'description': 'User updated profile', 'date': datetime.now() - timedelta(hours=5)},
            {'description': 'Password reset requested', 'date': datetime.now() - timedelta(hours=8)}
        ]
        
        return render_template('admin/users.html', 
                              users=users,
                              total_users_count=total_users_count,
                              new_users_count=new_users_count,
                              recent_activities=recent_activities,
                              datetime=datetime)
    
    @app.route('/admin/users/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_user():
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" is already taken.', 'danger')
            return redirect(url_for('admin_users'))
            
        if User.query.filter_by(email=email).first():
            flash(f'Email "{email}" is already registered.', 'danger')
            return redirect(url_for('admin_users'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            phone=phone,
            is_admin=is_admin
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{username}" has been created successfully.', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/edit', methods=['POST'])
    @login_required
    @admin_required
    def admin_edit_user():
        user_id = request.form.get('id')
        user = User.query.get_or_404(user_id)
        
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        # Check if username or email already exists (excluding current user)
        username_exists = User.query.filter(User.username == username, User.id != user_id).first()
        email_exists = User.query.filter(User.email == email, User.id != user_id).first()
        
        if username_exists:
            flash(f'Username "{username}" is already taken.', 'danger')
            return redirect(url_for('admin_users'))
            
        if email_exists:
            flash(f'Email "{email}" is already registered.', 'danger')
            return redirect(url_for('admin_users'))
        
        # Update user details
        user.username = username
        user.email = email
        user.phone = phone
        user.is_admin = is_admin
        
        # Update password if provided
        if password:
            user.set_password(password)
        
        db.session.commit()
        
        flash(f'User "{username}" has been updated successfully.', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_user():
        user_id = request.form.get('id')
        user = User.query.get_or_404(user_id)
        
        # Prevent deleting the current user
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('admin_users'))
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User "{username}" has been deleted successfully.', 'success')
        return redirect(url_for('admin_users'))
    
    # Admin Settings
    @app.route('/admin/settings')
    @login_required
    @admin_required
    def admin_settings():
        # Create a dummy form for CSRF protection
        class SettingsForm(FlaskForm):
            pass
        form = SettingsForm()
        return render_template('admin/settings.html', datetime=datetime, form=form)
    
    # Placeholder settings update routes
    @app.route('/admin/update-restaurant-settings', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_restaurant_settings():
        flash('Restaurant settings updated successfully.', 'success')
        return redirect(url_for('admin_settings'))
    
    @app.route('/admin/update-website-settings', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_website_settings():
        flash('Website settings updated successfully.', 'success')
        return redirect(url_for('admin_settings'))
    
    @app.route('/admin/update-notification-settings', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_notification_settings():
        flash('Notification settings updated successfully.', 'success')
        return redirect(url_for('admin_settings'))
        
    # Table Management Routes
    @app.route('/admin/tables')
    @login_required
    @admin_required
    def admin_tables():
        # Get filter parameters from query string
        status_filter = request.args.get('status', 'All')
        capacity_filter = request.args.get('capacity', 'All')
        
        # Base query
        query = Table.query
        
        # Apply filters
        if status_filter != 'All':
            query = query.filter_by(status=status_filter)
            
        if capacity_filter != 'All':
            if capacity_filter == '2':
                query = query.filter(Table.capacity == 2)
            elif capacity_filter == '4':
                query = query.filter(Table.capacity == 4)
            elif capacity_filter == '6+':
                query = query.filter(Table.capacity >= 6)
        
        # Get sort parameter
        sort_by = request.args.get('sort', 'table_number')
        
        # Apply sorting
        if sort_by == 'capacity':
            query = query.order_by(Table.capacity)
        elif sort_by == 'status':
            query = query.order_by(Table.status)
        else:
            query = query.order_by(Table.table_number)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        tables = query.paginate(page=page, per_page=10)
        
        return render_template('admin/tables.html', 
                               tables=tables, 
                               status_filter=status_filter,
                               capacity_filter=capacity_filter,
                               sort_by=sort_by,
                               datetime=datetime)
    
    @app.route('/admin/tables/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_add_table():
        form = TableForm()
        
        if form.validate_on_submit():
            # Check if table number already exists
            existing_table = Table.query.filter_by(table_number=form.table_number.data).first()
            if existing_table:
                flash(f'Table number {form.table_number.data} already exists.', 'danger')
                return redirect(url_for('admin_add_table'))
            
            # Create new table
            table = Table(
                table_number=form.table_number.data,
                capacity=form.capacity.data,
                status=form.status.data,
                description=form.description.data,
                qr_code_active=form.qr_code_active.data,
                position_x=form.position_x.data,
                position_y=form.position_y.data
            )
            
            db.session.add(table)
            db.session.commit()
            
            flash(f'Table {form.table_number.data} has been added successfully.', 'success')
            return redirect(url_for('admin_tables'))
            
        return render_template('admin/table_form.html', 
                               form=form, 
                               title='Add New Table',
                               datetime=datetime)
    
    @app.route('/admin/tables/edit/<int:table_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_table(table_id):
        table = Table.query.get_or_404(table_id)
        form = TableForm()
        
        if form.validate_on_submit():
            # Check if table number already exists (excluding this table)
            if form.table_number.data != table.table_number:
                existing_table = Table.query.filter_by(table_number=form.table_number.data).first()
                if existing_table:
                    flash(f'Table number {form.table_number.data} already exists.', 'danger')
                    return redirect(url_for('admin_edit_table', table_id=table_id))
            
            # Update table
            table.table_number = form.table_number.data
            table.capacity = form.capacity.data
            table.status = form.status.data
            table.description = form.description.data
            table.qr_code_active = form.qr_code_active.data
            table.position_x = form.position_x.data
            table.position_y = form.position_y.data
            
            db.session.commit()
            
            flash(f'Table {form.table_number.data} has been updated successfully.', 'success')
            return redirect(url_for('admin_tables'))
            
        elif request.method == 'GET':
            # Pre-populate form
            form.table_number.data = table.table_number
            form.capacity.data = table.capacity
            form.status.data = table.status
            form.description.data = table.description
            form.qr_code_active.data = table.qr_code_active
            form.position_x.data = table.position_x
            form.position_y.data = table.position_y
            
        return render_template('admin/table_form.html', 
                               form=form, 
                               title='Edit Table',
                               datetime=datetime)
    
    @app.route('/admin/tables/delete/<int:table_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_table(table_id):
        table = Table.query.get_or_404(table_id)
        
        # Store table number for flash message
        table_number = table.table_number
        
        db.session.delete(table)
        db.session.commit()
        
        flash(f'Table {table_number} has been deleted successfully.', 'success')
        return redirect(url_for('admin_tables'))
    
    @app.route('/admin/tables/qr/<int:table_id>')
    @login_required
    @admin_required
    def admin_table_qr(table_id):
        table = Table.query.get_or_404(table_id)
        
        # Generate QR code data
        base_url = request.host_url.rstrip('/')
        qr_url = f'{base_url}/qr-menu?table={table.table_number}'
        qr_code = generate_qr_code_data(qr_url)
        
        return render_template('admin/table_qr.html', 
                               table=table,
                               qr_code=qr_code,
                               qr_url=qr_url,
                               datetime=datetime)
    
    @app.route('/admin/tables/qr/generate-all', methods=['POST'])
    @login_required
    @admin_required
    def admin_generate_all_qr():
        # Get all active tables
        tables = Table.query.filter_by(qr_code_active=True).all()
        
        # Generate QR codes for each table
        base_url = request.host_url.rstrip('/')
        qr_codes = []
        
        for table in tables:
            qr_url = f'{base_url}/qr-menu?table={table.table_number}'
            qr_code = generate_qr_code_data(qr_url)
            qr_codes.append({
                'table': table,
                'qr_code': qr_code,
                'qr_url': qr_url
            })
        
        return render_template('admin/table_qr_all.html', 
                               qr_codes=qr_codes,
                               datetime=datetime)
    
    @app.route('/admin/tables/layout')
    @login_required
    @admin_required
    def admin_table_layout():
        # Get all tables
        tables = Table.query.all()
        
        return render_template('admin/table_layout.html', 
                               tables=tables,
                               datetime=datetime)
    
    @app.route('/admin/tables/update-status/<int:table_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_table_status(table_id):
        table = Table.query.get_or_404(table_id)
        
        # Get new status from form
        new_status = request.form.get('status')
        if new_status not in ['Available', 'Occupied', 'Reserved', 'Unavailable']:
            flash('Invalid table status.', 'danger')
            return redirect(url_for('admin_tables'))
        
        # Update status
        table.status = new_status
        db.session.commit()
        
        flash(f'Table {table.table_number} status updated to {new_status}.', 'success')
        return redirect(url_for('admin_tables'))
    
    @app.route('/admin/tables/update-layout', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_table_layout():
        # Get layout data from request
        layout_data = request.json
        
        if not layout_data or not isinstance(layout_data, list):
            return jsonify({'error': 'Invalid layout data.'}), 400
        
        # Update table positions
        for table_data in layout_data:
            table_id = table_data.get('id')
            position_x = table_data.get('x')
            position_y = table_data.get('y')
            
            if table_id is None or position_x is None or position_y is None:
                continue
                
            table = Table.query.get(table_id)
            if table:
                table.position_x = position_x
                table.position_y = position_y
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Table layout updated successfully.'})
    
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
        return render_template('reservation_success.html', reservation=reservation, datetime=datetime)
    
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
        return render_template('banquet_success.html', booking=booking, datetime=datetime)
    
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
    
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                flash('You do not have admin privileges.', 'danger')
                return redirect(url_for('home'))
        
        form = AdminLoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                if user.is_admin:
                    login_user(user, remember=form.remember.data)
                    next_page = request.args.get('next')
                    flash('You have been logged in as admin successfully!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
                else:
                    flash('This account does not have admin privileges.', 'danger')
            else:
                flash('Login unsuccessful. Please check your email and password.', 'danger')
        return render_template('admin_login.html', form=form)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash('You have been logged in successfully!', 'success')
                
                # Redirect admin users to admin dashboard
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                    
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
                              addresses=user_addresses,
                              datetime=datetime)
    
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
        
        # Get the table object to check its status
        table = Table.query.filter_by(table_number=table_id).first()
        
        # Get any existing active, ready or pending order for this table
        existing_order = None
        if table:
            # Try to find an active dining session for this table
            existing_order = Order.query.filter_by(
                table_number=int(table_id),
                order_type='dine-in'
            ).filter(
                Order.status.in_(['active', 'ready']),
                Order.payment_status == 'pending'  # Only unpaid orders
            ).order_by(Order.id.desc()).first()
            
            # If table is occupied but no active order is found, check for any recently created order
            if not existing_order and table.status == 'Occupied':
                # Look for any order created in the last 3 hours
                three_hours_ago = datetime.utcnow() - timedelta(hours=3)
                existing_order = Order.query.filter_by(
                    table_number=int(table_id),
                    order_type='dine-in'
                ).filter(
                    Order.created_at >= three_hours_ago,
                    Order.payment_status == 'pending'  # Only unpaid orders
                ).order_by(Order.id.desc()).first()
        
        categories = Category.query.order_by(Category.display_order).all()
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        
        return render_template('qr_menu.html', 
                              categories=categories, 
                              menu_items=menu_items, 
                              table_id=table_id,
                              existing_order=existing_order,
                              table=table,
                              datetime=datetime)
    
    @app.route('/qr-menu/order', methods=['POST'])
    def qr_menu_order():
        data = request.json
        table_id = data.get('table_id')
        items = data.get('items', [])
        existing_order_id = data.get('existing_order_id')
        
        if not items:
            return jsonify({'error': 'No items in order'}), 400
        
        # Get table
        table = Table.query.filter_by(table_number=table_id).first()
        if not table:
            return jsonify({'error': 'Table not found'}), 404
        
        # Check if we're updating an existing order or creating a new one
        if existing_order_id:
            # We're adding items to an existing order
            order = Order.query.get(existing_order_id)
            if not order or order.status not in ['active', 'ready']:
                return jsonify({'error': 'Existing order not found or not in an editable state'}), 404
            
            # Calculate additional amount
            additional_amount = 0
            for item in items:
                menu_item = MenuItem.query.get(item['id'])
                if not menu_item:
                    return jsonify({'error': f'Menu item {item["id"]} not found'}), 400
                additional_amount += menu_item.price * item['quantity']
            
            # Update total amount
            original_amount = order.total_amount
            order.total_amount += additional_amount
            
            # Add new order items
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
                'updated': True,
                'message': f'Added items to your existing order. Your new total is ₹{order.total_amount:.2f}.',
                'original_amount': original_amount,
                'additional_amount': additional_amount,
                'total_amount': order.total_amount
            })
        else:
            # Calculate total for new order
            total_amount = 0
            for item in items:
                menu_item = MenuItem.query.get(item['id'])
                if not menu_item:
                    return jsonify({'error': f'Menu item {item["id"]} not found'}), 400
                total_amount += menu_item.price * item['quantity']
            
            # Create new dine-in order
            order = Order(
                name=data.get('name', 'Table Customer'),
                email=data.get('email', 'table@example.com'),
                phone=data.get('phone', '0000000000'),
                order_type='dine-in',  # Changed to dine-in for table orders
                table_number=int(table_id),
                special_instructions=data.get('special_instructions', ''),
                total_amount=total_amount,
                payment_method='counter',  # Default to counter payment for dine-in
                payment_status='pending',
                status='active',  # Set as active instead of pending for dine-in orders
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
            
            # Update table status to Occupied
            if table and table.status == 'Available':
                table.status = 'Occupied'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'order_id': order.id,
                'updated': False,
                'message': 'Your order has been placed. You can continue to add items until your table is closed.'
            })
    
    @app.route('/takeaway', methods=['GET', 'POST'])
    def takeaway():
        categories = Category.query.order_by(Category.display_order).all()
        menu_items = MenuItem.query.filter_by(is_available=True).all()
        
        form = OrderForm()
        
        return render_template('takeaway.html', 
                              categories=categories, 
                              menu_items=menu_items,
                              form=form,
                              datetime=datetime)
    
    @app.route('/takeaway/place-order', methods=['POST'])
    def place_takeaway_order():
        form = OrderForm()
        
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
                
            # Create order - always takeaway
            order = Order(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                order_type='takeaway',
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
        # Get featured items for recommendations
        featured_items = MenuItem.query.filter_by(is_available=True).limit(3).all()
        return render_template('order_success.html', order=order, datetime=datetime, featured_items=featured_items)
    
    @app.route('/track-order', methods=['GET', 'POST'])
    def track_order():
        form = TrackOrderForm()
        order = None
        
        if form.validate_on_submit():
            order_id = form.order_id.data
            order = Order.query.get(order_id)
            if not order:
                flash('Order not found. Please check the order ID and try again.', 'danger')
        
        return render_template('track_order.html', form=form, order=order, datetime=datetime)
    
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
        
    @app.route('/api/order-details/<int:order_id>', methods=['GET'])
    def get_order_details(order_id):
        """Get detailed information about an order and its items"""
        order = Order.query.get_or_404(order_id)
        
        # Get order items
        order_items = []
        for item in order.items:
            menu_item = MenuItem.query.get(item.menu_item_id)
            if menu_item:
                order_items.append({
                    'id': item.id,
                    'name': menu_item.name,
                    'price': float(item.price),
                    'quantity': item.quantity,
                    'notes': item.notes,
                    'total': float(item.price * item.quantity)
                })
        
        # No delivery address needed - takeaway or dine-in only
        address = None
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'name': order.name,
                'email': order.email,
                'phone': order.phone,
                'order_type': order.order_type,
                'table_number': order.table_number,
                'special_instructions': order.special_instructions,
                'status': order.status,
                'payment_method': order.payment_method,
                'payment_status': order.payment_status,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'address': address
            },
            'items': order_items
        })
    
    # Error handlers
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_code=404, error_message='Page not found', datetime=datetime), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error_code=500, error_message='Server error', datetime=datetime), 500
        
    @app.route('/admin/orders/print-bill/<int:order_id>')
    @login_required
    @admin_required
    def print_bill(order_id):
        order = Order.query.get_or_404(order_id)
        # Eager load menu items to avoid N+1 query issues
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in order_items:
            item.menu_item = MenuItem.query.get(item.menu_item_id)
        
        return render_template('print_bill.html', order=order)

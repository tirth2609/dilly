import os
import base64
import qrcode
import io
from PIL import Image
from datetime import datetime

def save_image(form_picture):
    """Save uploaded image and return the filename"""
    # This is a placeholder as we're not handling image uploads
    # In a real application, you would save the uploaded image
    return None

def generate_qr_code_data(data):
    """Generate QR code image as base64 data URI"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_str}"

def format_currency(amount):
    """Format amount as INR currency"""
    if amount is None:
        return "₹0.00"
    return f"₹{amount:.2f}"

def format_date(date):
    """Format date as DD MMM YYYY"""
    if not date:
        return ""
    return date.strftime("%d %b %Y")

def format_time(time):
    """Format time as HH:MM AM/PM"""
    if not time:
        return ""
    return time.strftime("%I:%M %p")

def get_order_status_label(status):
    """Get Bootstrap label class for order status"""
    status_classes = {
        'pending': 'badge bg-warning',
        'preparing': 'badge bg-info',
        'ready': 'badge bg-primary',
        'completed': 'badge bg-success',
        'cancelled': 'badge bg-danger'
    }
    return status_classes.get(status, 'badge bg-secondary')

def get_payment_status_label(status):
    """Get Bootstrap label class for payment status"""
    status_classes = {
        'pending': 'badge bg-warning',
        'completed': 'badge bg-success',
        'failed': 'badge bg-danger'
    }
    return status_classes.get(status, 'badge bg-secondary')

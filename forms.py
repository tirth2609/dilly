from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms import IntegerField, DateField, TimeField, FloatField, RadioField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User
from datetime import datetime, time

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one or login.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ReservationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=128)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    time = SelectField('Time', validators=[DataRequired()], choices=[
        ('12:00', '12:00 PM'), ('12:30', '12:30 PM'), 
        ('13:00', '1:00 PM'), ('13:30', '1:30 PM'),
        ('14:00', '2:00 PM'), ('14:30', '2:30 PM'),
        ('19:00', '7:00 PM'), ('19:30', '7:30 PM'),
        ('20:00', '8:00 PM'), ('20:30', '8:30 PM'),
        ('21:00', '9:00 PM'), ('21:30', '9:30 PM')
    ])
    guests = IntegerField('Number of Guests', validators=[DataRequired()])
    special_requests = TextAreaField('Special Requests')
    submit = SubmitField('Make Reservation')
    
    def validate_date(self, date):
        if date.data < datetime.now().date():
            raise ValidationError('Reservation date cannot be in the past.')

class BanquetBookingForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=128)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    event_type = SelectField('Event Type', validators=[DataRequired()], choices=[
        ('wedding', 'Wedding Reception'),
        ('birthday', 'Birthday Celebration'),
        ('corporate', 'Corporate Event'),
        ('family', 'Family Gathering'),
        ('other', 'Other')
    ])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    time = SelectField('Time', validators=[DataRequired()], choices=[
        ('10:00', '10:00 AM'), ('11:00', '11:00 AM'), 
        ('12:00', '12:00 PM'), ('13:00', '1:00 PM'),
        ('16:00', '4:00 PM'), ('17:00', '5:00 PM'),
        ('18:00', '6:00 PM'), ('19:00', '7:00 PM')
    ])
    guests = IntegerField('Number of Guests', validators=[DataRequired()])
    requirements = TextAreaField('Special Requirements')
    submit = SubmitField('Submit Booking Request')
    
    def validate_date(self, date):
        if date.data < datetime.now().date():
            raise ValidationError('Event date cannot be in the past.')
        
    def validate_guests(self, guests):
        if guests.data < 25:
            raise ValidationError('Banquet bookings require a minimum of 25 guests.')
        if guests.data > 200:
            raise ValidationError('Maximum capacity is 200 guests. Please contact us for larger events.')

class AddressForm(FlaskForm):
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=128)])
    address_line2 = StringField('Address Line 2', validators=[Length(max=128)])
    city = StringField('City', validators=[DataRequired(), Length(max=64)])
    state = StringField('State', validators=[DataRequired(), Length(max=64)])
    postal_code = StringField('Postal Code', validators=[DataRequired(), Length(max=16)])
    is_default = BooleanField('Set as default address')
    submit = SubmitField('Save Address')

class OrderForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=128)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    order_type = RadioField('Order Type', choices=[('takeaway', 'Takeaway'), ('delivery', 'Delivery')], default='takeaway')
    address_id = SelectField('Delivery Address', coerce=int, validators=[Optional()])
    special_instructions = TextAreaField('Special Instructions')
    payment_method = RadioField('Payment Method', choices=[
        ('counter', 'Pay at Counter'), 
        ('cash-on-delivery', 'Cash on Delivery'),
        ('pickup', 'Pay on Pickup'),
        ('upi', 'UPI Payment')
    ], default='pickup')
    submit = SubmitField('Place Order')

class TrackOrderForm(FlaskForm):
    order_id = StringField('Order ID', validators=[DataRequired()])
    submit = SubmitField('Track Order')
    
class TableForm(FlaskForm):
    table_number = StringField('Table Number/ID', validators=[DataRequired(), Length(min=1, max=10)])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1, max=100)])
    status = SelectField('Status', choices=[
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Reserved', 'Reserved'),
        ('Unavailable', 'Unavailable')
    ], validators=[DataRequired()])
    description = TextAreaField('Description (Optional)', validators=[Optional(), Length(max=500)])
    qr_code_active = BooleanField('QR Code Active', default=True)
    position_x = IntegerField('Position X', validators=[Optional()])
    position_y = IntegerField('Position Y', validators=[Optional()])
    submit = SubmitField('Save Table')

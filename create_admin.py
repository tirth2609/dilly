from app import app, db
from models import User

def create_admin_user(username, email, password, phone):
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            return
        
        # Create new admin user
        admin = User(
            username=username,
            email=email,
            phone=phone
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user {username} with email {email} created successfully!")

if __name__ == "__main__":
    create_admin_user('admin', 'tanktirth030@gmail.com', '1104', '1234567890')
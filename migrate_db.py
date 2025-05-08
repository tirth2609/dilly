from app import app, db
from sqlalchemy import Column, Boolean, text

def add_is_admin_column():
    with app.app_context():
        # Check if the column already exists
        try:
            # Try to execute a query that uses the is_admin column
            db.session.execute(text("SELECT is_admin FROM \"user\" LIMIT 1"))
            print("Column is_admin already exists.")
            return
        except Exception as e:
            # If there's an error, the column doesn't exist
            print("Adding is_admin column to User table...")
            
        try:
            # Add the is_admin column with default value False
            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
            db.session.commit()
            print("Column is_admin added successfully.")
            
            # Set the admin user's is_admin flag to True
            db.session.execute(text("UPDATE \"user\" SET is_admin = TRUE WHERE email = 'tanktirth030@gmail.com'"))
            db.session.commit()
            print("Admin user tanktirth030@gmail.com updated with admin privileges.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_is_admin_column()
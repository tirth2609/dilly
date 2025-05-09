"""
Script to update the image_url column type in MenuItem table from VARCHAR(256) to TEXT
"""
from app import app, db
from sqlalchemy import text

def update_image_url_type():
    """Alter table to change image_url column type to TEXT"""
    with app.app_context():
        try:
            # Execute an ALTER TABLE statement
            sql = text("""
            ALTER TABLE menu_item 
            ALTER COLUMN image_url TYPE TEXT;
            """)
            
            db.session.execute(sql)
            db.session.commit()
            print("Successfully changed image_url type from VARCHAR(256) to TEXT")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating column type: {str(e)}")

if __name__ == "__main__":
    update_image_url_type()
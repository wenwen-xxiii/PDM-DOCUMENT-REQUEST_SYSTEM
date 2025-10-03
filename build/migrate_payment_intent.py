# migrate_payment_intent.py
import mysql.connector
from config import DB_CONFIG

def migrate_payment_intent_column():
    """Add payment_intent_id column to existing database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'document_requests' 
            AND column_name = 'payment_intent_id'
            AND table_schema = %s
        """, (DB_CONFIG['database'],))
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("Adding payment_intent_id column to document_requests table...")
            cursor.execute("""
                ALTER TABLE document_requests 
                ADD COLUMN payment_intent_id VARCHAR(255) AFTER payment_date
            """)
            connection.commit()
            print("✅ payment_intent_id column added successfully!")
        else:
            print("✅ payment_intent_id column already exists!")
            
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_payment_intent_column()
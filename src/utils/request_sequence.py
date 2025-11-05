# request_sequence.py
"""
Request Sequence Utility for generating unique request numbers
"""
import mysql.connector
from datetime import datetime
from config.config import DB_CONFIG


class RequestSequenceGenerator:
    """Utility class for generating unique sequential request numbers"""
    
    def __init__(self, db_connection=None):
        """
        Initialize RequestSequenceGenerator
        
        Args:
            db_connection: Optional database connection. If None, creates new connection.
        """
        self.db_connection = db_connection
    
    def get_db_connection(self):
        """Get database connection"""
        if self.db_connection and self.db_connection.is_connected():
            return self.db_connection
        return mysql.connector.connect(**DB_CONFIG)
    
    def generate_request_number(self, connection=None, prefix="PDM"):
        """
        Generate unique request number using request_sequences table
        
        Format: PDM-YYYY-MMDD-XXX
        Example: PDM-2024-1225-001
        
        Args:
            connection: Optional database connection to reuse
            prefix: Prefix for request number (default: "PDM")
        
        Returns:
            str: Unique request number
        """
        db_conn = connection or self.get_db_connection()
        cursor = db_conn.cursor()
        
        try:
            today = datetime.now()
            year = today.strftime("%Y")
            month_day = today.strftime("%m%d")
            
            # Get or create sequence for today and increment
            # This uses MySQL's INSERT ... ON DUPLICATE KEY UPDATE to ensure atomicity
            cursor.execute("""
                INSERT INTO request_sequences (sequence_date, last_number) 
                VALUES (CURDATE(), 1)
                ON DUPLICATE KEY UPDATE last_number = last_number + 1
            """)
            
            # Get the current sequence number after increment
            cursor.execute("""
                SELECT last_number FROM request_sequences 
                WHERE sequence_date = CURDATE()
            """)
            result = cursor.fetchone()
            daily_count = result[0] if result else 1
            
            # Format: PDM-YYYY-MMDD-XXX
            request_number = f"{prefix}-{year}-{month_day}-{daily_count:03d}"
            
            if not connection:
                cursor.close()
                db_conn.close()
            
            return request_number
            
        except Exception as e:
            print(f"Error generating request number: {e}")
            if not connection:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()
            # Fallback: return timestamp-based number
            return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def get_daily_count(self, date=None, connection=None):
        """
        Get the current daily count for a specific date
        
        Args:
            date: Date to check (default: today)
            connection: Optional database connection
        
        Returns:
            int: Current count for the date, or 0 if no sequence exists
        """
        db_conn = connection or self.get_db_connection()
        cursor = db_conn.cursor()
        
        try:
            if date:
                cursor.execute("""
                    SELECT last_number FROM request_sequences 
                    WHERE sequence_date = %s
                """, (date,))
            else:
                cursor.execute("""
                    SELECT last_number FROM request_sequences 
                    WHERE sequence_date = CURDATE()
                """)
            
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            if not connection:
                cursor.close()
                db_conn.close()
            
            return count
            
        except Exception as e:
            print(f"Error getting daily count: {e}")
            if not connection:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()
            return 0
    
    def reset_sequence(self, date=None, connection=None):
        """
        Reset sequence for a specific date (admin function)
        
        Args:
            date: Date to reset (default: today)
            connection: Optional database connection
        
        Returns:
            bool: True if successful, False otherwise
        """
        db_conn = connection or self.get_db_connection()
        cursor = db_conn.cursor()
        
        try:
            if date:
                cursor.execute("""
                    UPDATE request_sequences 
                    SET last_number = 0 
                    WHERE sequence_date = %s
                """, (date,))
            else:
                cursor.execute("""
                    UPDATE request_sequences 
                    SET last_number = 0 
                    WHERE sequence_date = CURDATE()
                """)
            
            db_conn.commit()
            success = cursor.rowcount > 0
            
            if not connection:
                cursor.close()
                db_conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error resetting sequence: {e}")
            if not connection:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()
            return False


# Global instance for easy access
request_sequence = RequestSequenceGenerator()


# audit_logger.py
"""
Audit Logger Utility for tracking system activities
"""
import mysql.connector
from datetime import datetime
import json
from config.config import DB_CONFIG


class AuditLogger:
    """Utility class for logging audit events in the system"""
    
    def __init__(self, db_connection=None):
        """
        Initialize AuditLogger
        
        Args:
            db_connection: Optional database connection. If None, creates new connection.
        """
        self.db_connection = db_connection
    
    def get_db_connection(self):
        """Get database connection"""
        if self.db_connection and self.db_connection.is_connected():
            return self.db_connection
        return mysql.connector.connect(**DB_CONFIG)
    
    def log_action(
        self,
        user_id,
        action,
        table_name=None,
        record_id=None,
        old_values=None,
        new_values=None,
        ip_address=None,
        user_agent=None,
        connection=None
    ):
        """
        Log an audit action
        
        Args:
            user_id: ID of user performing the action (can be None for system actions)
            action: Description of the action (e.g., 'CREATE_USER', 'UPDATE_REQUEST', 'DELETE_DOCUMENT')
            table_name: Name of the table affected (optional)
            record_id: ID of the record affected (optional)
            old_values: Dictionary of old values (optional)
            new_values: Dictionary of new values (optional)
            ip_address: IP address of the user (optional)
            user_agent: User agent string (optional)
            connection: Optional database connection to reuse
        
        Returns:
            audit_log_id if successful, None otherwise
        """
        db_conn = connection or self.get_db_connection()
        cursor = db_conn.cursor()
        
        try:
            # Convert dictionaries to JSON strings
            old_values_json = json.dumps(old_values) if old_values else None
            new_values_json = json.dumps(new_values) if new_values else None
            
            cursor.execute("""
                INSERT INTO audit_logs 
                (user_id, action, table_name, record_id, old_values, new_values, ip_address, user_agent, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                action,
                table_name,
                record_id,
                old_values_json,
                new_values_json,
                ip_address,
                user_agent,
                datetime.now()
            ))
            
            db_conn.commit()
            audit_log_id = cursor.lastrowid
            
            if not connection:
                cursor.close()
                db_conn.close()
            
            return audit_log_id
            
        except Exception as e:
            print(f"Error logging audit action: {e}")
            if not connection:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()
            return None
    
    def log_user_action(self, user_id, action, description=None, connection=None):
        """
        Convenience method for logging user actions
        
        Args:
            user_id: ID of user
            action: Action type (e.g., 'LOGIN', 'LOGOUT', 'CHANGE_PASSWORD')
            description: Optional description
            connection: Optional database connection
        """
        return self.log_action(
            user_id=user_id,
            action=f"{action}: {description}" if description else action,
            connection=connection
        )
    
    def log_create(self, user_id, table_name, record_id, new_values, connection=None):
        """
        Log a CREATE operation
        
        Args:
            user_id: ID of user creating the record
            table_name: Name of the table
            record_id: ID of the created record
            new_values: Dictionary of new values
            connection: Optional database connection
        """
        return self.log_action(
            user_id=user_id,
            action=f"CREATE_{table_name.upper()}",
            table_name=table_name,
            record_id=record_id,
            new_values=new_values,
            connection=connection
        )
    
    def log_update(self, user_id, table_name, record_id, old_values, new_values, connection=None):
        """
        Log an UPDATE operation
        
        Args:
            user_id: ID of user updating the record
            table_name: Name of the table
            record_id: ID of the updated record
            old_values: Dictionary of old values
            new_values: Dictionary of new values
            connection: Optional database connection
        """
        return self.log_action(
            user_id=user_id,
            action=f"UPDATE_{table_name.upper()}",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            connection=connection
        )
    
    def log_delete(self, user_id, table_name, record_id, old_values, connection=None):
        """
        Log a DELETE operation
        
        Args:
            user_id: ID of user deleting the record
            table_name: Name of the table
            record_id: ID of the deleted record
            old_values: Dictionary of old values (for recovery reference)
            connection: Optional database connection
        """
        return self.log_action(
            user_id=user_id,
            action=f"DELETE_{table_name.upper()}",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            connection=connection
        )
    
    def get_audit_logs(self, user_id=None, table_name=None, action=None, limit=100, connection=None):
        """
        Retrieve audit logs with optional filters
        
        Args:
            user_id: Filter by user ID (optional)
            table_name: Filter by table name (optional)
            action: Filter by action (optional)
            limit: Maximum number of records to return
            connection: Optional database connection
        
        Returns:
            List of audit log records
        """
        db_conn = connection or self.get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        try:
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            if table_name:
                query += " AND table_name = %s"
                params.append(table_name)
            
            if action:
                query += " AND action LIKE %s"
                params.append(f"%{action}%")
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            # Parse JSON fields
            for log in logs:
                if log.get('old_values'):
                    log['old_values'] = json.loads(log['old_values'])
                if log.get('new_values'):
                    log['new_values'] = json.loads(log['new_values'])
            
            if not connection:
                cursor.close()
                db_conn.close()
            
            return logs
            
        except Exception as e:
            print(f"Error retrieving audit logs: {e}")
            if not connection:
                if cursor:
                    cursor.close()
                if db_conn:
                    db_conn.close()
            return []


# Global instance for easy access
audit_logger = AuditLogger()


# Audit Logs and Request Sequences Implementation Guide

This guide explains how to use the `audit_logs` and `request_sequences` tables in the PDM Document Request System.

## 📊 Request Sequences

### Overview
The `request_sequences` table is **already implemented** and used to generate unique, sequential request numbers for document requests.

### How It Works
- Tracks daily sequence numbers (resets each day)
- Format: `PDM-YYYY-MMDD-XXX` (e.g., `PDM-2024-1225-001`)
- Automatically increments for each new request on the same day

### Current Implementation
**Location**: `src/views/requestform.py`

```python
def generate_request_number(self, connection):
    """Generate unique request number"""
    cursor = connection.cursor()
    
    today = datetime.now()
    year = today.strftime("%Y")
    month_day = today.strftime("%m%d")
    
    # Get or create sequence for today
    cursor.execute("""
        INSERT INTO request_sequences (sequence_date, last_number) 
        VALUES (CURDATE(), 1)
        ON DUPLICATE KEY UPDATE last_number = last_number + 1
    """)
    
    # Get the current sequence number
    cursor.execute("""
        SELECT last_number FROM request_sequences 
        WHERE sequence_date = CURDATE()
    """)
    result = cursor.fetchone()
    daily_count = result[0] if result else 1
    
    # Format: PDM-YYYY-MMDD-XXX
    return f"PDM-{year}-{month_day}-{daily_count:03d}"
```

### Usage Example
The request sequence is automatically used when creating a new document request. No additional code needed!

---

## 📝 Audit Logs

### Overview
The `audit_logs` table tracks all system activities for security, compliance, and debugging purposes.

### Table Structure
```sql
CREATE TABLE audit_logs (
    audit_log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
)
```

### Implementation
A utility class has been created: `src/utils/audit_logger.py`

### Usage Examples

#### 1. Basic Audit Logging

```python
from utils.audit_logger import audit_logger

# Log a user login
audit_logger.log_user_action(
    user_id=123,
    action="LOGIN",
    description="User logged in successfully"
)

# Log a logout
audit_logger.log_user_action(
    user_id=123,
    action="LOGOUT"
)
```

#### 2. Logging CREATE Operations

```python
# When creating a new document request
new_request_data = {
    'request_number': 'PDM-2024-1225-001',
    'student_id': 5,
    'document_type_id': 2,
    'total_amount': 150.00
}

audit_logger.log_create(
    user_id=5,
    table_name='document_requests',
    record_id=new_request_id,
    new_values=new_request_data
)
```

#### 3. Logging UPDATE Operations

```python
# When updating a request status
old_values = {
    'status': 'payment_pending',
    'payment_status': 'pending'
}

new_values = {
    'status': 'processing',
    'payment_status': 'paid',
    'processed_by': 10
}

audit_logger.log_update(
    user_id=10,  # Admin user ID
    table_name='document_requests',
    record_id=request_id,
    old_values=old_values,
    new_values=new_values
)
```

#### 4. Logging DELETE Operations

```python
# When deleting a record
old_values = {
    'request_id': 123,
    'request_number': 'PDM-2024-1225-001',
    'status': 'cancelled'
}

audit_logger.log_delete(
    user_id=10,
    table_name='document_requests',
    record_id=123,
    old_values=old_values
)
```

#### 5. Advanced Logging with IP and User Agent

```python
# Log with additional context
audit_logger.log_action(
    user_id=123,
    action='PASSWORD_CHANGE',
    old_values={'password_hash': 'old_hash'},
    new_values={'password_hash': 'new_hash'},
    ip_address='192.168.1.100',
    user_agent='Mozilla/5.0...'
)
```

#### 6. Reusing Database Connection

```python
# When you already have a connection, reuse it
db_connection = get_db_connection()

audit_logger.log_create(
    user_id=5,
    table_name='document_requests',
    record_id=new_request_id,
    new_values=new_request_data,
    connection=db_connection  # Reuse connection
)
```

### Retrieving Audit Logs

```python
from utils.audit_logger import audit_logger

# Get all recent logs
logs = audit_logger.get_audit_logs(limit=100)

# Filter by user
user_logs = audit_logger.get_audit_logs(user_id=123, limit=50)

# Filter by table
request_logs = audit_logger.get_audit_logs(
    table_name='document_requests',
    limit=50
)

# Filter by action
login_logs = audit_logger.get_audit_logs(
    action='LOGIN',
    limit=100
)
```

### Integration Examples

#### Example 1: Logging in Login Window

**File**: `src/views/login.py`

```python
from utils.audit_logger import audit_logger

def attempt_login(self):
    # ... existing login code ...
    
    if user and UtilityFunctions.verify_password(password, user['password_hash']):
        # Log successful login
        audit_logger.log_user_action(
            user_id=user['user_id'],
            action="LOGIN_SUCCESS",
            description=f"User logged in: {user['email']}"
        )
        
        # ... rest of login code ...
    else:
        # Log failed login attempt
        audit_logger.log_user_action(
            user_id=user['user_id'] if user else None,
            action="LOGIN_FAILED",
            description=f"Failed login attempt: {username_input}"
        )
```

#### Example 2: Logging in Admin Request Manager

**File**: `src/views/admin_request.py`

```python
from utils.audit_logger import audit_logger

def approve_request(self, request_id):
    db_connection = self.get_db_connection()
    cursor = db_connection.cursor(dictionary=True)
    
    # Get old values
    cursor.execute("SELECT * FROM document_requests WHERE request_id = %s", (request_id,))
    old_data = cursor.fetchone()
    
    # Update request
    cursor.execute("""
        UPDATE document_requests 
        SET status = 'processing', 
            processed_by = %s,
            processed_date = NOW()
        WHERE request_id = %s
    """, (self.current_user['user_id'], request_id))
    
    # Get new values
    cursor.execute("SELECT * FROM document_requests WHERE request_id = %s", (request_id,))
    new_data = cursor.fetchone()
    
    # Log the change
    audit_logger.log_update(
        user_id=self.current_user['user_id'],
        table_name='document_requests',
        record_id=request_id,
        old_values=dict(old_data),
        new_values=dict(new_data),
        connection=db_connection
    )
    
    db_connection.commit()
```

#### Example 3: Logging in User Management

**File**: `src/views/admin_user.py`

```python
from utils.audit_logger import audit_logger

def create_user(self, username, email, user_type, password):
    # Create user...
    new_user_id = cursor.lastrowid
    
    # Log user creation
    audit_logger.log_create(
        user_id=self.current_user['user_id'],
        table_name='users',
        record_id=new_user_id,
        new_values={
            'username': username,
            'email': email,
            'user_type': user_type,
            'is_active': True
        }
    )
```

### Best Practices

1. **Always log critical operations**:
   - User authentication (login/logout)
   - Password changes
   - User creation/deletion
   - Request status changes
   - Payment processing
   - Admin actions

2. **Include context**:
   - Always include user_id when available
   - Log old and new values for updates
   - Include IP address for security-sensitive actions

3. **Performance**:
   - Reuse database connections when possible
   - Don't log every single read operation
   - Focus on write operations and security events

4. **Data Privacy**:
   - Don't log sensitive data like passwords
   - Be mindful of what goes into old_values and new_values

---

## 🔍 Viewing Audit Logs

### Query Examples

```sql
-- Get all audit logs
SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100;

-- Get logs for a specific user
SELECT * FROM audit_logs 
WHERE user_id = 123 
ORDER BY timestamp DESC;

-- Get logs for document requests
SELECT * FROM audit_logs 
WHERE table_name = 'document_requests' 
ORDER BY timestamp DESC;

-- Get login attempts
SELECT * FROM audit_logs 
WHERE action LIKE '%LOGIN%' 
ORDER BY timestamp DESC;

-- Get recent changes to a specific record
SELECT * FROM audit_logs 
WHERE table_name = 'document_requests' 
AND record_id = 456 
ORDER BY timestamp DESC;
```

---

## 📋 Summary

- **Request Sequences**: ✅ Already implemented and working automatically
- **Audit Logs**: ⚠️ Utility class created, ready to integrate into your codebase

To fully implement audit logging, add audit log calls to your existing code where actions occur (login, create, update, delete operations).


# Request Sequences Implementation Guide

This guide explains how the `request_sequences` table works and how to use it in the PDM Document Request System.

## 📊 Overview

The `request_sequences` table tracks daily sequence numbers to generate unique request numbers for document requests.

### Table Structure
```sql
CREATE TABLE request_sequences (
    sequence_date DATE PRIMARY KEY,
    last_number INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

### Request Number Format
- **Format**: `PDM-YYYY-MMDD-XXX`
- **Example**: `PDM-2024-1225-001`
- **Explanation**:
  - `PDM` - Prefix (Pambayang Dalubhasaan ng Marilao)
  - `YYYY` - Year (e.g., 2024)
  - `MMDD` - Month and Day (e.g., 1225 for December 25)
  - `XXX` - Daily sequence number (001, 002, 003...)

---

## ✅ Current Implementation

The `request_sequences` table is **already implemented and working** in the system.

### Location
**File**: `src/views/requestform.py`

**Method**: `generate_request_number()`

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

### How It Works

1. **When a new request is created**, the system:
   - Checks if a sequence exists for today's date
   - If not, creates one starting at 1
   - If exists, increments the last_number by 1
   - Uses the incremented number to generate the request number

2. **Sequence resets daily**:
   - Each day gets its own sequence starting from 001
   - December 25, 2024: PDM-2024-1225-001, PDM-2024-1225-002, ...
   - December 26, 2024: PDM-2024-1226-001, PDM-2024-1226-002, ...

3. **Atomic operation**:
   - Uses `INSERT ... ON DUPLICATE KEY UPDATE` to ensure thread-safety
   - Prevents duplicate request numbers even with concurrent requests

---

## 🔧 Utility Class

A reusable utility class has been created: `src/utils/request_sequence.py`

### Features

- **Reusable**: Can be used anywhere in the system
- **Flexible**: Supports custom prefixes
- **Safe**: Handles errors gracefully
- **Connection reuse**: Can reuse existing database connections

### Usage Examples

#### Basic Usage

```python
from utils.request_sequence import request_sequence

# Generate a request number
request_number = request_sequence.generate_request_number()
print(request_number)  # Output: PDM-2024-1225-001
```

#### With Custom Prefix

```python
# Use custom prefix
request_number = request_sequence.generate_request_number(prefix="REQ")
print(request_number)  # Output: REQ-2024-1225-001
```

#### Reusing Database Connection

```python
# When you already have a connection
db_connection = get_db_connection()

request_number = request_sequence.generate_request_number(
    connection=db_connection
)

# Use the same connection for other operations
cursor = db_connection.cursor()
cursor.execute("INSERT INTO document_requests (request_number, ...) VALUES (%s, ...)", 
               (request_number, ...))
```

#### Get Daily Count

```python
# Check how many requests were created today
count = request_sequence.get_daily_count()
print(f"Requests created today: {count}")
```

#### Get Count for Specific Date

```python
from datetime import date

# Check count for a specific date
specific_date = date(2024, 12, 24)
count = request_sequence.get_daily_count(date=specific_date)
print(f"Requests on {specific_date}: {count}")
```

---

## 🔄 Refactoring Current Code (Optional)

You can optionally refactor the existing code to use the utility class:

### Before (Current Implementation)

```python
# In requestform.py
def generate_request_number(self, connection):
    cursor = connection.cursor()
    # ... implementation ...
    return f"PDM-{year}-{month_day}-{daily_count:03d}"
```

### After (Using Utility Class)

```python
# In requestform.py
from utils.request_sequence import request_sequence

def generate_request_number(self, connection):
    return request_sequence.generate_request_number(connection=connection)
```

**Benefits**:
- Cleaner code
- Reusable across the system
- Easier to maintain
- Consistent behavior

---

## 📋 Usage in Document Request Creation

### Current Flow

1. User fills out document request form
2. User clicks "Submit"
3. System calls `generate_request_number()` 
4. System creates request with generated number
5. Request number is displayed to user

### Example: Creating a Request

```python
# In requestform.py - submit_request method
def submit_request(self):
    connection = self.get_db_connection()
    cursor = connection.cursor()
    
    # Generate unique request number
    request_number = self.generate_request_number(connection)
    
    # Insert request
    cursor.execute("""
        INSERT INTO document_requests (
            request_number, student_id, document_type_id, ...
        ) VALUES (%s, %s, %s, ...)
    """, (request_number, student_id, document_type_id, ...))
    
    connection.commit()
    
    # Show success message with request number
    messagebox.showinfo("Success", 
        f"Request submitted successfully!\nRequest Number: {request_number}")
```

---

## 🔍 Database Queries

### View Current Sequences

```sql
-- View all sequences
SELECT * FROM request_sequences 
ORDER BY sequence_date DESC;

-- View today's sequence
SELECT * FROM request_sequences 
WHERE sequence_date = CURDATE();

-- View sequences for a date range
SELECT * FROM request_sequences 
WHERE sequence_date BETWEEN '2024-12-01' AND '2024-12-31'
ORDER BY sequence_date DESC;
```

### Statistics

```sql
-- Total requests created today
SELECT last_number as total_requests 
FROM request_sequences 
WHERE sequence_date = CURDATE();

-- Average requests per day (last 30 days)
SELECT AVG(last_number) as avg_daily_requests
FROM request_sequences 
WHERE sequence_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- Most requests in a single day
SELECT sequence_date, last_number as total_requests
FROM request_sequences 
ORDER BY last_number DESC 
LIMIT 1;
```

---

## 🛡️ Thread Safety

The implementation is **thread-safe** because:

1. **Atomic operation**: Uses `INSERT ... ON DUPLICATE KEY UPDATE` which is atomic
2. **Database-level locking**: MySQL handles concurrent access
3. **Unique constraint**: Request numbers are unique in `document_requests` table

### Handling Concurrent Requests

Even if multiple users submit requests at the exact same time:
- Each gets a unique sequence number
- No duplicate request numbers
- All requests are properly tracked

---

## ⚠️ Important Notes

1. **Daily Reset**: Sequences reset to 001 each day
2. **No Manual Edits**: Don't manually edit `request_sequences` table
3. **Date-Based**: Sequences are tied to calendar dates
4. **Unique Numbers**: Request numbers are unique system-wide

---

## 📊 Summary

- ✅ **Status**: Fully implemented and working
- ✅ **Location**: `src/views/requestform.py` → `generate_request_number()`
- ✅ **Utility Class**: Created in `src/utils/request_sequence.py`
- ✅ **Format**: `PDM-YYYY-MMDD-XXX`
- ✅ **Thread-Safe**: Yes, using atomic database operations
- ✅ **Auto-Resets**: Daily reset to 001

**No action required** - the system is already using `request_sequences` correctly!


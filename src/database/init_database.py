import mysql.connector
from mysql.connector import Error
import hashlib
import sys
import os

# Add the src directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config import DB_CONFIG

class DatabaseInitializer:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            print("✓ Connected to MySQL server successfully")
            return True
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            print("💡 Please check your MySQL server is running and credentials in config.py are correct")
            return False
    
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            print(f"✓ Database '{DB_CONFIG['database']}' created/verified successfully")
            return True
        except Error as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    def create_tables(self):
        """Create all necessary tables with consistent naming"""
        try:
            cursor = self.connection.cursor()
            
            # User Accounts table (for authentication)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    user_type ENUM('student', 'admin', 'registrar', 'cashier') DEFAULT 'student',
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    last_login TIMESTAMP NULL,
                    login_attempts INT DEFAULT 0,
                    locked_until TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Add login_attempts and locked_until columns to existing tables if they don't exist
            # MySQL doesn't support IF NOT EXISTS for ALTER TABLE, so we check first
            cursor.execute("SHOW COLUMNS FROM users LIKE 'login_attempts'")
            if not cursor.fetchone():
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN login_attempts INT DEFAULT 0")
                    print("✓ Added login_attempts column to users table")
                except Error as e:
                    print(f"⚠️ Could not add login_attempts column: {e}")
            
            cursor.execute("SHOW COLUMNS FROM users LIKE 'locked_until'")
            if not cursor.fetchone():
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP NULL")
                    print("✓ Added locked_until column to users table")
                except Error as e:
                    print(f"⚠️ Could not add locked_until column: {e}")
            
            # Students table (student-specific data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT UNIQUE,
                    student_number VARCHAR(20) UNIQUE NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    middle_name VARCHAR(50),
                    birth_date DATE,
                    gender ENUM('Male', 'Female', 'Other'),
                    course VARCHAR(100) NOT NULL,
                    year_level ENUM('1st Year', '2nd Year', '3rd Year', '4th Year', '5th Year') NOT NULL,
                    contact_number VARCHAR(20),
                    address TEXT,
                    enrollment_status ENUM('Enrolled', 'Inactive', 'Graduated', 'Transferred') DEFAULT 'Enrolled',
                    date_enrolled DATE,
                    has_obligations BOOLEAN DEFAULT FALSE,
                    obligations_details TEXT,
                    profile_picture longblob,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Registrar/Admin Staff table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staff (
                    staff_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT UNIQUE NOT NULL,
                    staff_number VARCHAR(20) UNIQUE NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    position VARCHAR(100) NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    contact_number VARCHAR(20),
                    office_location VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    hire_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Document Types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_types (
                    document_type_id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(10) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    fee_amount DECIMAL(10,2) DEFAULT 0.00,
                    processing_days INT DEFAULT 3,
                    requires_clearance BOOLEAN DEFAULT FALSE,
                    is_available BOOLEAN DEFAULT TRUE,
                    created_by INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            """)
            
            # Document Requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_requests (
                    request_id INT AUTO_INCREMENT PRIMARY KEY,
                    request_number VARCHAR(20) UNIQUE NOT NULL,
                    student_id INT NOT NULL,
                    document_type_id INT NOT NULL,
                    purpose_details TEXT,
                    quantity INT DEFAULT 1,
                    delivery_mode ENUM('pickup', 'online') DEFAULT 'pickup',
                    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    request_release_date DATE,
                    status ENUM('payment_pending', 'processing', 'ready_for_pickup', 'completed', 'cancelled', 'rejected') DEFAULT 'payment_pending',
                    rejection_reason TEXT,
                    total_amount DECIMAL(10,2) DEFAULT 0.00,
                    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
                    payment_method ENUM('online', 'cash', 'gcash', 'bank_transfer') DEFAULT 'online',
                    payment_date TIMESTAMP NULL,
                    payment_intent_id VARCHAR(255),
                    processed_by INT NULL,
                    processed_date TIMESTAMP NULL,
                    ready_date TIMESTAMP NULL,
                    completed_date TIMESTAMP NULL,
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (document_type_id) REFERENCES document_types(document_type_id),
                    FOREIGN KEY (processed_by) REFERENCES staff(staff_id)
                )
            """)
            
            # Document Attachments table (for file uploads)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_attachments (
                    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id INT NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_data LONGBLOB NOT NULL,
                    file_size INT NOT NULL,
                    file_type VARCHAR(100),
                    uploaded_by VARCHAR(100) NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    remarks TEXT,
                    FOREIGN KEY (request_id) REFERENCES document_requests(request_id) ON DELETE CASCADE
                )
            """)
            
            # Payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_method VARCHAR(50) NOT NULL,
                    reference_number VARCHAR(100) UNIQUE,
                    gateway_transaction_id VARCHAR(100),
                    status ENUM('pending', 'success', 'failed', 'cancelled', 'refunded') DEFAULT 'pending',
                    gateway_response JSON,
                    paid_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES document_requests(request_id) ON DELETE CASCADE
                )
            """)
            
            # Notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    notification_type ENUM('info', 'success', 'warning', 'error', 'payment', 'status_update') DEFAULT 'info',
                    is_read BOOLEAN DEFAULT FALSE,
                    related_request_id INT NULL,
                    action_url VARCHAR(500),
                    scheduled_at TIMESTAMP NULL,
                    sent_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (related_request_id) REFERENCES document_requests(request_id) ON DELETE SET NULL
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id INT NOT NULL,
                    rating INT CHECK (rating >= 1 AND rating <= 5),
                    comments TEXT,
                    is_anonymous BOOLEAN DEFAULT FALSE,
                    responded_to BOOLEAN DEFAULT FALSE,
                    response TEXT,
                    responded_by INT NULL,
                    responded_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES document_requests(request_id) ON DELETE CASCADE,
                    FOREIGN KEY (responded_by) REFERENCES staff(staff_id)
                )
            """)
            
            # Student Academic Records table (for verification)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS academic_records (
                    academic_record_id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    course VARCHAR(100) NOT NULL,
                    year_level VARCHAR(20) NOT NULL,
                    semester ENUM('1st', '2nd', 'Summer') NOT NULL,
                    academic_year VARCHAR(9) NOT NULL,
                    units_enrolled INT,
                    status ENUM('Regular', 'Irregular', 'Conditional') DEFAULT 'Regular',
                    gpa DECIMAL(3,2),
                    has_inc BOOLEAN DEFAULT FALSE,
                    has_dropped BOOLEAN DEFAULT FALSE,
                    record_date DATE NOT NULL,
                    verified_by INT NULL,
                    verified_at TIMESTAMP NULL,
                    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                    FOREIGN KEY (verified_by) REFERENCES staff(staff_id)
                )
            """)
            
            # System Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    setting_id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    data_type ENUM('string', 'integer', 'boolean', 'decimal', 'json') DEFAULT 'string',
                    description TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    updated_by INT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (updated_by) REFERENCES users(user_id)
                )
            """)
            
            # Audit Log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
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
            """)
            
            # Request Sequences table for generating request numbers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS request_sequences (
                    sequence_date DATE PRIMARY KEY,
                    last_number INT DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_document_requests_student ON document_requests(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_document_requests_status ON document_requests(status)",
                "CREATE INDEX IF NOT EXISTS idx_document_requests_date ON document_requests(request_date)",
                "CREATE INDEX IF NOT EXISTS idx_document_attachments_request ON document_attachments(request_id)",
                "CREATE INDEX IF NOT EXISTS idx_document_attachments_date ON document_attachments(upload_date)",
                "CREATE INDEX IF NOT EXISTS idx_students_number ON students(student_number)",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_document_types_available ON document_types(is_available)",
                "CREATE INDEX IF NOT EXISTS idx_students_user ON students(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_staff_user ON staff(user_id)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            print("✓ All tables created successfully with consistent naming")
            return True
        except Error as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    def get_or_create_user_id(self, cursor, username, email, password, user_type='student'):
        """Get existing user ID or create new user"""
        try:
            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email))
            result = cursor.fetchone()
            
            if result:
                return result[0]  # Return existing user ID
            
            # Create new user
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, user_type, is_verified) 
                VALUES (%s, %s, %s, %s, %s)
            """, (username, email, password_hash, user_type, True))
            
            return cursor.lastrowid
        except Error as e:
            print(f"❌ Error in get_or_create_user_id: {e}")
            return None
    
    def insert_initial_data(self):
        """Insert initial data into tables with consistent naming"""
        try:
            cursor = self.connection.cursor()
            
            # Create default users and get their IDs
            admin_user_id = self.get_or_create_user_id(cursor, 'admin', 'admin@pdm.edu.ph', 'admin123', 'admin')
            registrar_user_id = self.get_or_create_user_id(cursor, 'registrar', 'registrar@pdm.edu.ph', 'registrar123', 'registrar')
            cashier_user_id = self.get_or_create_user_id(cursor, 'cashier', 'cashier@pdm.edu.ph', 'cashier123', 'cashier')
            student_user_id = self.get_or_create_user_id(cursor, 'PDM-2023-003139', 'wenwenxiii@gmail.com', 'student123', 'student')
            
            if not all([admin_user_id, registrar_user_id, cashier_user_id, student_user_id]):
                raise Exception("Failed to create user accounts")
            
            # Create admin staff record
            cursor.execute("""
                INSERT IGNORE INTO staff (user_id, staff_number, first_name, last_name, position, department) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (admin_user_id, 'ADMIN001', 'System', 'Administrator', 'System Administrator', 'IT Department'))
            
            # Create registrar staff record
            cursor.execute("""
                INSERT IGNORE INTO staff (user_id, staff_number, first_name, last_name, position, department) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (registrar_user_id, 'REG001', 'Maria', 'Santos', 'Registrar', 'Registrar Office'))
            
            # Create cashier staff record
            cursor.execute("""
                INSERT IGNORE INTO staff (user_id, staff_number, first_name, last_name, position, department, office_location) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (cashier_user_id, 'CASH001', 'Juan', 'Dela Cruz', 'Cashier', 'Finance Office', 'Cashier\'s Office'))
            
            # Insert document types with codes
            document_types = [
                ('COE', 'Certificate of Enrollment/Registration', 'Current enrollment or registration certification', 50.00, 2, False),
                ('CG', 'Certificate of Grades', 'Current semester grades', 50.00, 2, False),
                ('DIPLOMA', 'Diploma (True Copy)', 'Graduation diploma', 100.00, 10, True),
                ('TOR', 'Transcript of Records (TOR)', 'Official academic transcript', 200.00, 5, True),
                ('CGrad', 'Certificate of Graduation/Completion', 'Proof of graduation or course completion', 50.00, 3, True),
                ('GMC', 'Certificate of Good Moral Character', 'Certificate of good moral character', 150.00, 3, True),
                ('TC', 'Honorable Dismissal/Transfer Credentials', 'Transfer or honorable dismissal document', 200.00, 7, True),
                ('RL', 'Recommendation Letter', 'Recommendation from faculty or school', 100.00, 2, False),
                ('CUE', 'Certificate of Units Earned', 'Document showing units earned', 50.00, 3, True),
                ('CL', 'Clearance', 'School clearance document', 0.00, 1, True)
            ]

            cursor.executemany("""
                INSERT IGNORE INTO document_types (code, name, description, fee_amount, processing_days, requires_clearance, created_by) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [(code, name, desc, fee, days, clearance, admin_user_id) for code, name, desc, fee, days, clearance in document_types])
            
            # Create user accounts for ALL sample students
            sample_students_data = [
                ('PDM-2025-000001', 'Juan', 'Dela Cruz', 'S.', '2003-02-15', 'Male', 'BS Information Technology', '1st Year', '09123456701', 'Marilao, Bulacan', '2025-06-01'),
                ('PDM-2025-000002', 'Maria', 'Santos', 'L.', '2003-05-20', 'Female', 'BS Computer Science', '1st Year', '09123456702', 'Malolos, Bulacan', '2025-06-01'),
                ('PDM-2025-000003', 'Jose', 'Reyes', 'M.', '2003-08-10', 'Male', 'BS Information Systems', '1st Year', '09123456703', 'Plaridel, Bulacan', '2025-06-01'),
                ('PDM-2025-000004', 'Ana', 'Lopez', 'R.', '2003-03-05', 'Female', 'BS Information Technology', '1st Year', '09123456704', 'Hagonoy, Bulacan', '2025-06-01'),
                ('PDM-2025-000005', 'Mark', 'Gonzales', 'T.', '2003-11-12', 'Male', 'BS Computer Science', '1st Year', '09123456705', 'Balagtas, Bulacan', '2025-06-01')
            ]
            
            student_user_ids = [student_user_id]  # Start with the main student
            
            # Create user accounts for other sample students
            for student_data in sample_students_data:
                student_number = student_data[0]
                email = f"{student_number.lower()}@pdm.edu.ph"
                user_id = self.get_or_create_user_id(cursor, student_number, email, 'student123', 'student')
                if user_id:
                    student_user_ids.append(user_id)
            
            # Insert student records with proper user_ids
            student_records = [
                # Wendell Rebusit (with user_id)
                (student_user_ids[0], 'PDM-2023-003139', 'Wendell', 'Rebusit', 'Fernandez', '1998-09-23', 'Male', 'BS Information Technology', '3rd Year', '09270786707', 'Iloilo City', 'Enrolled', '2023-06-01', False, None),
            ]
            
            # Add other students with their user_ids
            for i, student_data in enumerate(sample_students_data, 1):
                if i < len(student_user_ids):
                    student_records.append((
                        student_user_ids[i], student_data[0], student_data[1], student_data[2], student_data[3],
                        student_data[4], student_data[5], student_data[6], student_data[7], student_data[8],
                        student_data[9], 'Enrolled', student_data[10], False, None
                    ))
            
            cursor.executemany("""
                INSERT IGNORE INTO students (
                    user_id, student_number, first_name, last_name, middle_name,
                    birth_date, gender, course, year_level, contact_number, address,
                    enrollment_status, date_enrolled, has_obligations, obligations_details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, student_records)
            
            # Insert system settings by category
            settings = [
                ('general', 'system_name', 'Pambayang Dalubhasaan ng Marilao - Document Request System', 'string', 'System display name', True),
                ('general', 'institution_name', 'Pambayang Dalubhasaan ng Marilao', 'string', 'Institution full name', True),
                ('general', 'contact_email', 'registrar@pdm.edu.ph', 'string', 'Contact email for support', True),
                ('general', 'contact_phone', '(02) 1234-5678', 'string', 'Contact phone number', True),
                
                ('payments', 'online_payment_enabled', 'true', 'boolean', 'Enable online payments', True),
                ('payments', 'payment_currency', 'PHP', 'string', 'Payment currency', False),
                ('payments', 'cash_payment_enabled', 'true', 'boolean', 'Enable cash payments', True),
                
                ('documents', 'max_processing_days', '10', 'integer', 'Maximum processing days for documents', True),
                ('documents', 'allow_urgent_requests', 'true', 'boolean', 'Allow urgent processing requests', True),
                ('documents', 'max_requests_per_day', '3', 'integer', 'Maximum requests per student per day', False),
                
                ('notifications', 'email_notifications', 'true', 'boolean', 'Enable email notifications', False),
                ('notifications', 'sms_notifications', 'false', 'boolean', 'Enable SMS notifications', False),
                ('notifications', 'auto_reminder_days', '3', 'integer', 'Days before sending reminder', False)
            ]
            
            cursor.executemany("""
                INSERT IGNORE INTO system_settings (category, setting_key, setting_value, data_type, description, is_public) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, settings)
            
            self.connection.commit()
            print("✓ Initial data inserted successfully with consistent naming")
            
            # Display created accounts and students
            print("\n📋 Default Accounts Created:")
            print("👤 Admin Account: admin / admin123")
            print("👤 Registrar Account: registrar / registrar123")
            print("💰 Cashier Account: cashier / cashier123")
            print("👤 Student Account: PDM-2023-003139 / student123")
            print("🏢 Departments: Registrar Office, Finance Office")
            
            print("\n🎓 Sample Students Created:")
            print("• Wendell Rebusit (PDM-2023-003139) - BS Information Technology - 3rd Year")
            for student_data in sample_students_data:
                print(f"• {student_data[1]} {student_data[2]} ({student_data[0]}) - {student_data[6]} - {student_data[7]}")
            
            return True
        except Error as e:
            print(f"❌ Error inserting initial data: {e}")
            self.connection.rollback()
            return False
    
    def initialize_database(self):
        """Initialize the complete database"""
        print("🔧 Initializing database...")
        
        if not self.connect():
            return False
        
        if not self.create_database():
            return False
        
        # Reconnect to specific database
        self.connection.database = DB_CONFIG['database']
        
        if not self.create_tables():
            return False
        
        if not self.insert_initial_data():
            return False
        
        print("✅ Database initialization completed successfully!")
        return True
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Database connection closed")

def initialize_system_database():
    """Initialize the database system"""
    initializer = DatabaseInitializer()
    success = initializer.initialize_database()
    initializer.close()
    return success

if __name__ == "__main__":
    print("=" * 60)
    print("Pambayang Dalubhasaan ng Marilao")
    print("Database Initialization Tool")
    print("=" * 60)
    
    if initialize_system_database():
        print("\n✅ Database setup completed successfully!")
        print("\n📋 Default Accounts:")
        print("👤 Admin: admin / admin123")
        print("👤 Registrar: registrar / registrar123")
        print("💰 Cashier: cashier / cashier123")
        print("👤 Student: PDM-2023-003139 / student123")
        print("\n🎓 Sample Students: 6 records created")
        print("📎 Document Attachments: Table added for file uploads")
        print("📊 Document Types: 10 document types configured")
    else:
        print("❌ Database setup failed!")
        print("💡 Please check:")
        print("   - MySQL server is running")
        print("   - Database credentials in config.py are correct")
        print("   - You have sufficient privileges to create databases")
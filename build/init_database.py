import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
import hashlib

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
            return True
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return False
    
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            print("✓ Database created/verified successfully")
            return True
        except Error as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    def create_tables(self):
        """Create all necessary tables with normalized structure"""
        try:
            cursor = self.connection.cursor()
            
            # User Accounts table (for authentication)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    user_type ENUM('student', 'admin', 'registrar') DEFAULT 'student',
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    last_login TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Students table (student-specific data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
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
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Registrar/Admin Staff table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staff (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT UNIQUE NOT NULL,
                    staff_id VARCHAR(20) UNIQUE NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    position VARCHAR(100) NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    contact_number VARCHAR(20),
                    office_location VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    hire_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Document Types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_types (
                    id INT AUTO_INCREMENT PRIMARY KEY,
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
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """)
            
            # Document Requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_number VARCHAR(20) UNIQUE NOT NULL,
                    student_id INT NOT NULL,
                    document_type_id INT NOT NULL,
                    purpose ENUM('Employment', 'Further Studies', 'Scholarship', 'Personal Use', 'Transfer', 'Other') NOT NULL,
                    purpose_details TEXT,
                    quantity INT DEFAULT 1,
                    special_instructions TEXT,
                    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    preferred_pickup_date DATE,
                    actual_pickup_date DATE,
                    status ENUM('draft', 'submitted', 'under_review', 'payment_pending', 'processing', 'ready_for_pickup', 'completed', 'cancelled', 'rejected') DEFAULT 'draft',
                    rejection_reason TEXT,
                    total_amount DECIMAL(10,2) DEFAULT 0.00,
                    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
                    payment_method ENUM('online', 'cash', 'gcash', 'bank_transfer') DEFAULT 'online',
                    payment_reference VARCHAR(100),
                    payment_date TIMESTAMP NULL,
                    processed_by INT NULL,
                    processed_date TIMESTAMP NULL,
                    ready_date TIMESTAMP NULL,
                    completed_date TIMESTAMP NULL,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (document_type_id) REFERENCES document_types(id),
                    FOREIGN KEY (processed_by) REFERENCES staff(id)
                )
            """)
            
            # Payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
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
                    FOREIGN KEY (request_id) REFERENCES document_requests(id) ON DELETE CASCADE
                )
            """)
            
            # Notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
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
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (related_request_id) REFERENCES document_requests(id) ON DELETE SET NULL
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id INT NOT NULL,
                    rating INT CHECK (rating >= 1 AND rating <= 5),
                    comments TEXT,
                    suggestions TEXT,
                    is_anonymous BOOLEAN DEFAULT FALSE,
                    responded_to BOOLEAN DEFAULT FALSE,
                    response TEXT,
                    responded_by INT NULL,
                    responded_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES document_requests(id) ON DELETE CASCADE,
                    FOREIGN KEY (responded_by) REFERENCES staff(id)
                )
            """)
            
            # Student Academic Records table (for verification)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS academic_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
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
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (verified_by) REFERENCES staff(id)
                )
            """)
            
            # System Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    data_type ENUM('string', 'integer', 'boolean', 'decimal', 'json') DEFAULT 'string',
                    description TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    updated_by INT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (updated_by) REFERENCES users(id)
                )
            """)
            
            # Audit Log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    action VARCHAR(100) NOT NULL,
                    table_name VARCHAR(50),
                    record_id INT,
                    old_values JSON,
                    new_values JSON,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            print("✓ All tables created successfully with normalized structure")
            return True
        except Error as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    def insert_initial_data(self):
        """Insert initial data into tables with normalized structure"""
        try:
            cursor = self.connection.cursor()
            
            # Create default admin user account
            admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("""
                INSERT IGNORE INTO users (username, email, password_hash, user_type, is_verified) 
                VALUES (%s, %s, %s, %s, %s)
            """, ('admin', 'admin', admin_password, 'admin', True))
            admin_user_id = cursor.lastrowid if cursor.lastrowid else 1
            
            # Create default registrar user account
            registrar_password = hashlib.sha256('registrar123'.encode()).hexdigest()
            cursor.execute("""
                INSERT IGNORE INTO users (username, email, password_hash, user_type, is_verified) 
                VALUES (%s, %s, %s, %s, %s)
            """, ('registrar', 'registrar', registrar_password, 'registrar', True))
            registrar_user_id = cursor.lastrowid if cursor.lastrowid else 2
            
            # Create admin staff record
            cursor.execute("""
                INSERT IGNORE INTO staff (user_id, staff_id, first_name, last_name, position, department) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (admin_user_id, 'ADMIN001', 'System', 'Administrator', 'System Administrator', 'IT Department'))
            
            # Create registrar staff record
            cursor.execute("""
                INSERT IGNORE INTO staff (user_id, staff_id, first_name, last_name, position, department) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (registrar_user_id, 'REG001', 'Maria', 'Santos', 'Registrar', 'Registrar Office'))
            
            # Insert document types with codes
            document_types = [
                ('COE', 'Certificate of Enrollment', 'Current enrollment or registration certification', 100.00, 2, True),
                ('CG', 'Certificate of Grades', 'Current semester grades', 120.00, 2, False),
                ('DIPLOMA', 'Diploma (True Copy)', 'Graduation diploma', 500.00, 10, True),
                ('TOR', 'Transcript of Records (TOR)', 'Official academic transcript', 250.00, 5, True),
                ('CGrad', 'Certificate of Graduation/Completion', 'Proof of graduation or course completion', 200.00, 3, True),
                ('GMC', 'Certificate of Good Moral Character', 'Certificate of good moral character', 150.00, 3, True),
                ('HD', 'Honorable Dismissal/Transfer Credentials', 'Transfer or honorable dismissal document', 300.00, 7, True),
                ('RL', 'Recommendation Letter', 'Recommendation from faculty or school', 100.00, 2, False),
                ('CUE', 'Certificate of Units Earned', 'Document showing units earned', 150.00, 3, True),
                ('CL', 'Clearance', 'School clearance document', 50.00, 1, True)
            ]

            
            cursor.executemany("""
                INSERT IGNORE INTO document_types (code, name, description, fee_amount, processing_days, requires_clearance, created_by) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [(code, name, desc, fee, days, clearance, admin_user_id) for code, name, desc, fee, days, clearance in document_types])
            
            # Insert sample student records
            student_records = [
                (None, 'PDM-2025-000001', 'Juan', 'Dela Cruz', 'S.', '2003-02-15', 'Male', 'BS Information Technology', '1st Year', '09123456701', 'Marilao, Bulacan', 'Enrolled', '2025-06-01', False, None),
                (None, 'PDM-2025-000002', 'Maria', 'Santos', 'L.', '2003-05-20', 'Female', 'BS Computer Science', '1st Year', '09123456702', 'Malolos, Bulacan', 'Enrolled', '2025-06-01', False, None),
                (None, 'PDM-2025-000003', 'Jose', 'Reyes', 'M.', '2003-08-10', 'Male', 'BS Information Systems', '1st Year', '09123456703', 'Plaridel, Bulacan', 'Enrolled', '2025-06-01', False, None),
                (None, 'PDM-2025-000004', 'Ana', 'Lopez', 'R.', '2003-03-05', 'Female', 'BS Information Technology', '1st Year', '09123456704', 'Hagonoy, Bulacan', 'Enrolled', '2025-06-01', False, None),
                (None, 'PDM-2025-000005', 'Mark', 'Gonzales', 'T.', '2003-11-12', 'Male', 'BS Computer Science', '1st Year', '09123456705', 'Balagtas, Bulacan', 'Enrolled', '2025-06-01', False, None)
            ]
            
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
                ('general', 'contact_email', 'registrar', 'string', 'Contact email for support', True),
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
            print("✓ Initial data inserted successfully with normalized structure")
            
            # Display created accounts and students
            print("\n📋 Default Accounts Created:")
            print("👤 Admin Account: admin / admin123")
            print("👤 Registrar Account: registrar / registrar123")
            print("🏢 Department: Registrar Office")
            
            print("\n🎓 Sample Students Created:")
            print("• Juan Dela Cruz (PDM-2025-000001) - BS Information Technology")
            print("• Maria Santos (PDM-2025-000002) - BS Computer Science") 
            print("• Jose Reyes (PDM-2025-000003) - BS Information Systems")
            print("• Ana Lopez (PDM-2025-000004) - BS Information Technology")
            print("• Mark Gonzales (PDM-2025-000005) - BS Computer Science")
            
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
        print("✅ Database setup completed successfully!")
        print("\nDefault accounts created:")
        print("👤 Admin: admin / admin123")
        print("👤 Registrar: registrar / registrar123")
        print("\nSample students created (5 records)")
    else:
        print("❌ Database setup failed!")
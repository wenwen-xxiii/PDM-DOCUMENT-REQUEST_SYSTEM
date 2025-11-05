# PDM Document Request System

A comprehensive desktop application built with Python Tkinter for managing document requests in educational institutions. This system is designed for **Pambayang Dalubhasaan ng Marilao (PDM)** and facilitates students to request official documents, administrators to process requests, and handles payment processing through PayMongo integration.

The system supports multiple user roles with role-based access control, ensuring secure and efficient document request management for educational institutions.

## 🚀 Features

### Student Features
- **User Authentication**: Secure login/signup with OTP verification
- **Document Requests**: Submit requests for various official documents
- **Payment Processing**: Integrated PayMongo payment gateway
- **Request Tracking**: View request status and history
- **Profile Management**: Update personal information
- **Document Viewing**: Preview requested documents using built-in PDF viewer

### Admin Features
- **Dashboard**: Comprehensive overview with statistics and metrics
- **Request Management**: Process and approve/reject document requests
- **Student Management**: View and manage student records
- **Document Management**: Upload document attachments to requests and manage document types
- **Billing Management**: Track payments and view payment history
- **User Management**: Manage user accounts and permissions
- **Feedback System**: Handle student feedback and complaints

### User Roles & Permissions
The system supports multiple user roles with role-based access control:

- **Student**: Can request documents, view status, make payments, and manage profile
- **Admin**: Full access to all system features and management functions
- **Registrar**: Can manage requests, students, documents, and feedback (no billing access)
- **Cashier**: Can manage billing, payments, and view requests (limited to payment-related functions)

### System Features
- **Email Notifications**: Automated OTP emails, document ready notifications, request confirmations, and payment receipts via SMTP
- **File Attachments**: Support for document attachments with PDF viewing capability
- **Database Integration**: MySQL database with proper relationships and async support
- **Security**: Password hashing (SHA-256), rate limiting, account lockout, and input validation
- **Audit Logging**: Comprehensive activity tracking for all system operations (login, payments, requests, user management)
- **Request Sequencing**: Unique request number generation with daily reset (format: PDM-YYYY-MMDD-XXX)
- **Responsive UI**: Modern, user-friendly interface with custom graphics
- **Async Operations**: Support for asynchronous database operations using aiomysql
- **Password Recovery**: Secure password reset with OTP verification
- **Document Viewer**: Built-in PDF viewer for document attachments

## 🛠️ Technology Stack

- **Frontend**: Python Tkinter (GUI Framework)
- **Backend**: Python 3.8+
- **Database**: MySQL 5.7+ with async support (aiomysql)
- **Payment Gateway**: PayMongo API
- **Email Service**: SMTP (Gmail) with async support (aiosmtplib)
- **File Processing**: PyMuPDF (fitz) for PDF handling
- **Web Framework**: Flask/Quart for webhook server
- **HTTP Client**: aiohttp for async HTTP requests
- **Deployment**: PyInstaller for executable creation

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL Server 5.7 or higher
- Gmail account for email services
- PayMongo account for payment processing
- Ngrok account for webhook handling (optional)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PDM-DOCUMENT-REQUEST_SYSTEM
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   - Create a MySQL database
   - Update database credentials in `src/config/config.py` or create a `.env` file
   - Run the database initialization script:
   ```bash
   python src/database/init_database.py
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root with the following variables:
   ```env
   # Database Configuration
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=pdm_document_system
   DB_PORT=3306

   # Email Configuration
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password

   # PayMongo Configuration
   PAYMONGO_SECRET_KEY=your_secret_key
   PAYMONGO_PUBLIC_KEY=your_public_key
   PAYMONGO_SECRET_KEY_WEBHOOK=your_webhook_key
   PAYMONGO_API_URL=https://api.paymongo.com/v1

   # Ngrok Configuration (Optional)
   NGROK_AUTH_TOKEN=your_ngrok_token
   NGROK_PORT=5000

   # Application Configuration
   APP_DEBUG=True
   APP_SECRET_KEY=your_secret_key
   OTP_EXPIRY_MINUTES=10
   MAX_LOGIN_ATTEMPTS=3
   SESSION_TIMEOUT_MINUTES=30
   ACCOUNT_LOCKOUT_MINUTES=30
   ```

## 🚀 Running the Application

1. **Start the main application**
   ```bash
   python src/main.py
   ```

2. **For webhook server (if using PayMongo webhooks)**
   ```bash
   python src/scripts/run_webhook.py
   ```

3. **For Ngrok tunneling (if needed)**
   ```bash
   python src/scripts/run_ngrok.py
   ```

## 🔑 Default Credentials

After running the database initialization script, the following default accounts are created:

- **Admin Account**: 
  - Username: `admin`
  - Password: `admin123`
  - Access: Full system access

- **Registrar Account**: 
  - Username: `registrar`
  - Password: `registrar123`
  - Access: Request, student, document, and feedback management

- **Cashier Account**: 
  - Username: `cashier`
  - Password: `cashier123`
  - Access: Billing and payment management

**⚠️ Important**: Change these default passwords immediately after first login in a production environment!

## 📁 Project Structure

```
PDM-DOCUMENT-REQUEST_SYSTEM/
├── src/                           # Source code
│   ├── main.py                    # Application entry point
│   ├── views/                     # UI components (Tkinter windows)
│   │   ├── login.py               # Login interface
│   │   ├── signup.py              # Registration interface
│   │   ├── home.py                # Main dashboard
│   │   ├── profile.py             # User profile management
│   │   ├── document.py            # Document management
│   │   ├── requestform.py         # Document request form
│   │   ├── payment_window.py      # Payment processing window
│   │   ├── forgotpass.py          # Password recovery request
│   │   ├── passreset.py           # Password reset interface
│   │   ├── otp.py                 # OTP verification
│   │   ├── admin_dashboard.py     # Admin dashboard
│   │   ├── admin_request.py       # Admin request management
│   │   ├── admin_documents.py     # Admin document management
│   │   ├── admin_billing.py       # Admin billing management
│   │   ├── admin_student.py       # Admin student management
│   │   ├── admin_user.py          # Admin user management
│   │   ├── admin_feedback.py      # Admin feedback management
│   │   ├── admin_upload_docu.py   # Admin document attachment upload
│   │   └── view_docu_attachment.py # Document attachment viewer
│   ├── services/                  # External service integrations
│   │   ├── payment_processor.py   # Payment processing logic
│   │   └── webhook_server.py      # Webhook handling
│   ├── utils/                     # Utility functions
│   │   ├── utils.py               # General utilities
│   │   ├── async_utils.py         # Async utility functions
│   │   ├── audit_logger.py        # Audit logging utility
│   │   └── request_sequence.py    # Request number generation utility
│   ├── config/                    # Configuration
│   │   └── config.py              # Application settings
│   ├── database/                  # Database related
│   │   └── init_database.py       # Database initialization
│   └── scripts/                   # Standalone scripts
│       ├── run_webhook.py         # Webhook server runner
│       └── run_ngrok.py           # Ngrok tunnel runner
├── resources/                     # Application assets
│   └── assets/                    # UI images and graphics
├── tests/                         # Test files
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── LICENSE                        # License file
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── AUDIT_AND_SEQUENCES_GUIDE.md   # Guide for audit logging and request sequences
└── REQUEST_SEQUENCES_GUIDE.md     # Detailed guide for request sequence usage
```

## 🗄️ Database Schema

The system uses the following main tables:
- **users**: User authentication and account information (supports: student, admin, registrar, cashier roles)
- **students**: Student profile and academic information
- **staff**: Staff member information (admin, registrar, cashier)
- **document_requests**: Document request records with status tracking
- **document_types**: Available document types with pricing and processing details
- **document_attachments**: File attachments for document requests
- **payments**: Payment transaction records
- **feedback**: User feedback and complaints
- **otp_codes**: OTP verification codes with expiration
- **system_settings**: Application-wide configuration settings
- **audit_logs**: System activity audit logs (tracks all user actions, data changes, and security events)
- **request_sequences**: Sequence tracking for unique request number generation (daily reset)

## 🔐 Security Features

- **Password Security**: SHA-256 hashing for password storage
- **Input Validation**: Comprehensive input validation and sanitization
- **SQL Injection Prevention**: Parameterized queries throughout
- **OTP Verification**: Time-based OTP (expires in 10 minutes) for email verification
- **Rate Limiting**: Maximum login attempts (default: 3) with account lockout (30 minutes)
- **Role-Based Access Control**: Granular permissions for different user roles
- **Secure Password Reset**: OTP-based password recovery system
- **Audit Trail**: Comprehensive logging of all system activities including user actions, data changes, and security events

## 💳 Payment Integration

The system integrates with PayMongo for payment processing:
- Secure payment processing via PayMongo API
- Payment status tracking
- Webhook support for payment notifications (optional)
- Payment history tracking
- Automated payment receipt emails upon successful payment
- Support for both online (PayMongo) and offline (cash) payment methods

## 📧 Email Integration

Automated email notifications using async SMTP for:
- OTP verification codes (with expiration time)
- Document request confirmation emails
- Document ready notifications with attachments
- Password reset OTP codes
- Payment receipt emails (with transaction details)

## 🎨 User Interface

- Modern, responsive design
- Custom graphics and icons
- Intuitive navigation
- Consistent color scheme
- User-friendly forms and layouts

## 🔧 Configuration

The application can be configured through:
- Environment variables (`.env` file) - Copy `.env.example` to `.env` and fill in your values
- Configuration file (`src/config/config.py`)
- Database settings
- Email service settings
- Payment gateway settings

## 📱 Deployment

The application can be packaged as a standalone executable using PyInstaller:

```bash
# Windows
pyinstaller --onefile --windowed --add-data "resources;resources" --icon=resources/assets/PDMICON.ico src/main.py

# Linux/Mac
pyinstaller --onefile --windowed --add-data "resources:resources" --icon=resources/assets/PDMICON.ico src/main.py
```

**Note**: Make sure to:
1. Configure all environment variables in `.env` file before building
2. Test the executable in a clean environment
3. Include all required assets in the `resources` directory
4. Ensure MySQL server is accessible from the deployment environment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation
- See `AUDIT_AND_SEQUENCES_GUIDE.md` for audit logging and request sequence usage
- See `REQUEST_SEQUENCES_GUIDE.md` for detailed request sequence implementation

## 🔄 Version History

- **v1.1.0**: Enhanced features and security
  - Comprehensive audit logging system integrated across all operations
  - Request number sequencing with daily reset (PDM-YYYY-MMDD-XXX format)
  - Payment receipt email notifications
  - Rate limiting and account lockout mechanism
  - Enhanced security tracking and compliance

- **v1.0.0**: Initial release with core functionality
  - Document request system with multiple document types
  - PayMongo payment integration
  - Multi-role admin dashboard (Admin, Registrar, Cashier)
  - User management with role-based access control
  - OTP-based email verification
  - Password recovery system
  - Document attachment support
  - Feedback and complaint system
  - Async database operations
  - PDF document viewer

## 📞 Contact

For more information about this project, please contact the development team.

---

**Note**: Make sure to configure all environment variables before running the application. The system requires proper database setup and email service configuration to function correctly.

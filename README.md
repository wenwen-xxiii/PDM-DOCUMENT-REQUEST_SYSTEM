# PDM Document Request System

A comprehensive desktop application built with Python Tkinter for managing document requests in educational institutions. This system facilitates students to request official documents, administrators to process requests, and handles payment processing through PayMongo integration.

## 🚀 Features

### Student Features
- **User Authentication**: Secure login/signup with OTP verification
- **Document Requests**: Submit requests for various official documents
- **Payment Processing**: Integrated PayMongo payment gateway
- **Request Tracking**: View request status and history
- **Profile Management**: Update personal information
- **Document Viewing**: Preview and download requested documents

### Admin Features
- **Dashboard**: Comprehensive overview with statistics
- **Request Management**: Process and approve/reject document requests
- **Student Management**: View and manage student records
- **Document Management**: Upload and manage document templates
- **Billing Management**: Track payments and generate reports
- **User Management**: Manage user accounts and permissions
- **Feedback System**: Handle student feedback and complaints

### System Features
- **Email Notifications**: Automated OTP and status updates
- **File Attachments**: Support for document attachments
- **Database Integration**: MySQL database with proper relationships
- **Security**: Password hashing, session management, and input validation
- **Responsive UI**: Modern, user-friendly interface with custom graphics

## 🛠️ Technology Stack

- **Frontend**: Python Tkinter (GUI Framework)
- **Backend**: Python 3.x
- **Database**: MySQL
- **Payment Gateway**: PayMongo API
- **Email Service**: SMTP (Gmail)
- **File Processing**: PyMuPDF for PDF handling
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
│   │   ├── forgotpass.py          # Password recovery
│   │   ├── otp.py                 # OTP verification
│   │   ├── admin_dashboard.py     # Admin dashboard
│   │   ├── admin_request.py       # Admin request management
│   │   ├── admin_documents.py     # Admin document management
│   │   ├── admin_billing.py       # Admin billing management
│   │   ├── admin_student.py       # Admin student management
│   │   ├── admin_user.py          # Admin user management
│   │   ├── admin_feedback.py      # Admin feedback management
│   │   └── admin_upload_docu.py  # Admin document upload
│   ├── services/                  # External service integrations
│   │   ├── payment_processor.py   # Payment processing logic
│   │   └── webhook_server.py      # Webhook handling
│   ├── utils/                     # Utility functions
│   │   ├── utils.py               # General utilities
│   │   └── async_utils.py         # Async utility functions
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
└── README.md                      # This file
```

## 🗄️ Database Schema

The system uses the following main tables:
- **users**: User authentication and account information
- **students**: Student profile and academic information
- **document_requests**: Document request records
- **document_types**: Available document types
- **payments**: Payment transaction records
- **feedback**: User feedback and complaints
- **otp_codes**: OTP verification codes

## 🔐 Security Features

- Password hashing using SHA-256
- Session management with timeout
- Input validation and sanitization
- SQL injection prevention
- OTP-based email verification
- Rate limiting for login attempts

## 💳 Payment Integration

The system integrates with PayMongo for payment processing:
- Secure payment processing
- Real-time payment status updates
- Webhook support for payment notifications
- Payment history tracking

## 📧 Email Integration

Automated email notifications for:
- OTP verification codes
- Request status updates
- Payment confirmations
- System notifications

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
pyinstaller --onefile --windowed --add-data "resources;resources" src/main.py
```

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

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
- Document request system
- Payment integration
- Admin dashboard
- User management

## 📞 Contact

For more information about this project, please contact the development team.

---

**Note**: Make sure to configure all environment variables before running the application. The system requires proper database setup and email service configuration to function correctly.

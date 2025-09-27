import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'pdm_document_system'),
    'port': int(os.getenv('DB_PORT', '3306'))
}

# Email Configuration - MAKE SURE THESE ARE SET IN YOUR .env FILE
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'email_address': os.getenv('EMAIL_ADDRESS', ''),
    'email_password': os.getenv('EMAIL_PASSWORD', '')
}

# System Configuration
SYSTEM_CONFIG = {
    'otp_expiry_minutes': int(os.getenv('OTP_EXPIRY_MINUTES', '10')),
    'max_login_attempts': int(os.getenv('MAX_LOGIN_ATTEMPTS', '3')),
    'session_timeout_minutes': int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
}

# Application Configuration
APP_CONFIG = {
    'debug': os.getenv('APP_DEBUG', 'True').lower() == 'true',
    'secret_key': os.getenv('APP_SECRET_KEY', 'default-secret-key-change-in-production')
}
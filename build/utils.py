# utils.py
import hashlib
import random
import string
from datetime import datetime
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import APP_CONFIG, EMAIL_CONFIG

class UtilityFunctions:
    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password, hashed_password):
        """Verify password against hash"""
        return UtilityFunctions.hash_password(password) == hashed_password
    
    @staticmethod
    def generate_otp(length=6):
        """Generate numeric OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def generate_reference_number(prefix="REQ"):
        """Generate unique reference number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}{timestamp}{random_str}"
    
    @staticmethod
    def is_valid_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_pdm_student_number(student_number):
        """Validate PDM student number format: PDM-YYYY-NNNNNN"""
        import re
        pattern = r'^PDM-\d{4}-\d{6}$'
        return re.match(pattern, student_number.upper()) is not None
    
    @staticmethod
    def format_student_number(student_number):
        """Format student number to PDM standard format"""
        # Remove any existing hyphens and convert to uppercase
        cleaned = student_number.replace('-', '').upper()
        
        if cleaned.startswith('PDM') and len(cleaned) > 3:
            year_part = cleaned[3:7] if len(cleaned) > 7 else cleaned[3:]
            number_part = cleaned[7:13] if len(cleaned) > 7 else "000000"
            
            # Pad number part with zeros if needed
            number_part = number_part.ljust(6, '0')
            
            return f"PDM-{year_part}-{number_part}"
        
        return student_number.upper()


class EmailService:
    def __init__(self):
        self.smtp_server = EMAIL_CONFIG.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = EMAIL_CONFIG.get('smtp_port', 587)
        self.email_address = EMAIL_CONFIG.get('email_address', '')
        self.email_password = EMAIL_CONFIG.get('email_password', '')
        self.email_enabled = bool(self.email_address and self.email_password)
        
        if self.email_enabled:
            print(f"✓ Email service configured for: {self.email_address}")
        else:
            print("⚠️ Email service disabled - configure EMAIL_ADDRESS and EMAIL_PASSWORD in .env")
    
    def send_otp_email(self, to_email, otp_code):
        """Send OTP email using real SMTP"""
        try:
            if not self.email_enabled:
                return self._fallback_otp_email(to_email, otp_code, "SIMULATION")
            
            # Create message
            subject = "PDM Document System - OTP Verification"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">OTP Verification Code</h2>
                        <p>Dear User,</p>
                        <p>Your One-Time Password (OTP) for account verification is:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <span style="font-size: 32px; font-weight: bold; color: #800000; 
                                       background: #f5f5f5; padding: 15px 30px; 
                                       border-radius: 5px; letter-spacing: 5px;">
                                {otp_code}
                            </span>
                        </div>
                        
                        <p>This OTP will expire in 3 minutes.</p>
                        <p>If you did not request this verification, please ignore this email.</p>
                        
                        <hr style="margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email
            success = self._send_email(to_email, subject, body)
            
            if success:
                print(f"✓ OTP email sent to: {to_email}")
                return True
            else:
                print(f"⚠️ Failed to send OTP email, using fallback")
                return self._fallback_otp_email(to_email, otp_code, "FALLBACK")
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return self._fallback_otp_email(to_email, otp_code, "FALLBACK")
    
    def _send_email(self, to_email, subject, body):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"PDM Document System <{self.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML body
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable security
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP Authentication failed. Check email credentials.")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            print(f"❌ Email sending error: {e}")
            return False
    
    def send_request_confirmation(self, to_email, request_details):
        """Send document request confirmation email"""
        try:
            if not self.email_enabled:
                return self._fallback_confirmation_email(to_email, request_details)
            
            subject = f"PDM Document Request Confirmation - {request_details.get('reference_number', '')}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request Confirmation</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Request Received</h2>
                        <p>Dear {request_details.get('student_name', 'Student')},</p>
                        <p>Your document request has been received and is being processed.</p>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                            <p><strong>Reference Number:</strong> {request_details.get('reference_number', 'N/A')}</p>
                            <p><strong>Document Type:</strong> {request_details.get('document_name', 'N/A')}</p>
                            <p><strong>Quantity:</strong> {request_details.get('quantity', 1)}</p>
                            <p><strong>Total Fee:</strong> ₱{request_details.get('total_fee', 0):.2f}</p>
                            <p><strong>Request Date:</strong> {request_details.get('request_date', 'N/A')}</p>
                        </div>
                        
                        <p><strong>Next Steps:</strong></p>
                        <ol>
                            <li>Wait for payment verification</li>
                            <li>Track your request status in the system</li>
                            <li>You will be notified when your document is ready for pickup</li>
                        </ol>
                        
                        <hr style="margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated confirmation. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(to_email, subject, body)
            
        except Exception as e:
            print(f"❌ Confirmation email error: {e}")
            return self._fallback_confirmation_email(to_email, request_details)
    
    def _fallback_otp_email(self, to_email, otp_code, mode="SIMULATION"):
        """Fallback method for OTP email"""
        print("=" * 50)
        print(f"📧 OTP EMAIL ({mode})")
        print("=" * 50)
        print(f"To: {to_email}")
        print(f"Subject: PDM Document System - OTP Verification")
        print(f"OTP Code: {otp_code}")
        print("=" * 50)
        if mode == "SIMULATION":
            print("In production, this would be sent via real email")
        else:
            print("Email service unavailable - using fallback")
        print("=" * 50)
        return True
    
    def _fallback_confirmation_email(self, to_email, request_details):
        """Fallback for confirmation email"""
        print("=" * 50)
        print("📧 REQUEST CONFIRMATION SIMULATION")
        print("=" * 50)
        print(f"To: {to_email}")
        print(f"Document: {request_details.get('document_name', 'N/A')}")
        print(f"Reference: {request_details.get('reference_number', 'N/A')}")
        print("=" * 50)
        return True

class PaymentProcessor:
    @staticmethod
    def process_online_payment(amount, payment_method, reference_number):
        """Simulate payment processing"""
        print(f"💳 Processing payment: {amount} via {payment_method} - Ref: {reference_number}")
        
        # Always succeed in simulation mode
        return {
            'success': True,
            'transaction_id': f"TXN{reference_number}",
            'message': 'Payment processed successfully (Simulation Mode)'
        }

class ValidationHelper:
    @staticmethod
    def validate_student_clearance(db_connection, student_id):
        """Check if student has no outstanding obligations"""
        try:
            # Simulate clearance check - always pass in development
            if APP_CONFIG.get('debug', True):
                print(f"✅ Clearance check passed for student ID: {student_id}")
                return True
            
            # In production, this would check against actual clearance system
            cursor = db_connection.cursor()
            # Add actual clearance logic here
            return True
        except Exception as e:
            print(f"Error validating clearance: {e}")
            return False
    
    @staticmethod
    def validate_payment_status(db_connection, request_id):
        """Validate payment status for a request"""
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT payment_status FROM document_requests WHERE id = %s", (request_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error validating payment: {e}")
            return None

# Global utility instances
email_service = EmailService()
payment_processor = PaymentProcessor()
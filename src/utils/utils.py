# utils.py
import hashlib
import random
import string
from datetime import datetime
import re
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
import io
from config.config import APP_CONFIG, EMAIL_CONFIG
from utils.async_utils import safe_async_run

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
    
    @staticmethod
    def format_last_login(last_login):
        """Format last login timestamp for display"""
        if not last_login:
            return "Never logged in"
        
        try:
            if isinstance(last_login, str):
                # If it's already a string, try to parse and format it
                dt = datetime.strptime(last_login, '%Y-%m-%d %H:%M:%S')
                return dt.strftime('%B %d, %Y at %I:%M %p')
            else:
                # If it's a datetime object
                return last_login.strftime('%B %d, %Y at %I:%M %p')
        except Exception:
            # If parsing fails, return as is
            return str(last_login)


class EmailService:
    def __init__(self):
        self.smtp_server = EMAIL_CONFIG.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = EMAIL_CONFIG.get('smtp_port', 587)
        self.email_address = EMAIL_CONFIG.get('email_address', '')
        self.email_password = EMAIL_CONFIG.get('email_password', '')
        self.email_enabled = bool(self.email_address and self.email_password)
        
        if self.email_enabled:
            print(f"[OK] Email service configured for: {self.email_address}")
        else:
            print("[WARNING] Email service disabled - configure EMAIL_ADDRESS and EMAIL_PASSWORD in .env")
    
    async def send_otp_email(self, to_email, otp_code):
        """Send OTP email using async SMTP"""
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
            
            # Send email asynchronously
            success = await self._send_email(to_email, subject, body)
            
            if success:
                print(f"[OK] OTP email sent to: {to_email}")
                return True
            else:
                print(f"[WARNING] Failed to send OTP email, using fallback")
                return self._fallback_otp_email(to_email, otp_code, "FALLBACK")
            
        except Exception as e:
            print(f"[ERROR] Email error: {e}")
            return self._fallback_otp_email(to_email, otp_code, "FALLBACK")
    
    async def _send_email(self, to_email, subject, body):
        """Send email using async SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"PDM Document System <{self.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML body
            msg.attach(MIMEText(body, 'html'))
            
            # Use asyncio.to_thread to run synchronous SMTP in thread pool
            def send_sync():
                import smtplib
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_address, self.email_password)
                    server.send_message(msg)
                return True
            
            await asyncio.to_thread(send_sync)
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("[ERROR] SMTP Authentication failed. Check email credentials.")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Email sending error: {e}")
            return False

    async def send_email_with_attachments(self, to_email, subject, body, attachments_data):
        """Send email with attachments from database BLOB data using async SMTP"""
        try:
            if not self.email_enabled:
                return self._fallback_attachment_email(to_email, subject, body, attachments_data)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"PDM Document System <{self.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments from database BLOB data
            for attachment in attachments_data:
                file_name = attachment['file_name']
                file_data = attachment['file_data']  # This is the BLOB from database
                file_type = attachment.get('file_type', 'application/pdf')
                
                if file_data:
                    # Determine MIME type
                    maintype, subtype = file_type.split('/', 1) if '/' in file_type else ('application', 'octet-stream')
                    
                    # Create attachment
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(file_data)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{file_name}"'
                    )
                    msg.attach(part)
            
            # Use asyncio.to_thread to run synchronous SMTP in thread pool
            def send_sync():
                import smtplib
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_address, self.email_password)
                    server.send_message(msg)
                return True
            
            await asyncio.to_thread(send_sync)
            
            print(f"[OK] Email with attachments sent to: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("[ERROR] SMTP Authentication failed. Check email credentials.")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP error: {e}")
            return self._fallback_attachment_email(to_email, subject, body, attachments_data)
        except Exception as e:
            print(f"[ERROR] Email with attachments error: {e}")
            return self._fallback_attachment_email(to_email, subject, body, attachments_data)
    
    async def send_document_ready_email(self, to_email, request_details, db_connection):
        """Send email when document is ready with attachments using async SMTP"""
        try:
            # Get attachments from database
            cursor = db_connection.cursor()
            cursor.execute("""
                SELECT file_name, file_data, file_type 
                FROM document_attachments 
                WHERE request_id = %s
            """, (request_details.get('request_id'),))
            
            attachments = cursor.fetchall()
            cursor.close()
            
            # Prepare attachments data
            attachments_data = []
            for file_name, file_data, file_type in attachments:
                if file_data:  # Only include if BLOB data exists
                    attachments_data.append({
                        'file_name': file_name,
                        'file_data': file_data,
                        'file_type': file_type or 'application/pdf'
                    })
            
            subject = f"Request Completed - #{request_details.get('request_number', '')}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Request Completed</h2>
                        <p>Dear {request_details.get('student_name', 'Student')},</p>
                        
                        <p>Your document request <strong>#{request_details.get('request_number', '')}</strong> has been completed.</p>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                            <p><strong>Document:</strong> {request_details.get('document_name', 'N/A')}</p>
                            <p><strong>Delivery Method:</strong> {request_details.get('delivery_method', 'Email').title()}</p>
                            <p><strong>Completed Date:</strong> {request_details.get('completed_date', 'N/A')}</p>
                        </div>
                        
                        <p>Your document has been delivered to your email. Please check your inbox and spam folder.</p>
                        
                        <hr style="margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if attachments_data:
                return await self.send_email_with_attachments(to_email, subject, body, attachments_data)
            else:
                # Fallback to regular email if no attachments
                return await self._send_email(to_email, subject, body)
                
        except Exception as e:
            print(f"[ERROR] Document ready email error: {e}")
            return False
    
    async def send_request_confirmation(self, to_email, request_details):
        """Send document request confirmation email using async SMTP"""
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
            
            return await self._send_email(to_email, subject, body)
            
        except Exception as e:
            print(f"[ERROR] Confirmation email error: {e}")
            return self._fallback_confirmation_email(to_email, request_details)
    
    def _fallback_otp_email(self, to_email, otp_code, mode="SIMULATION"):
        """Fallback method for OTP email"""
        print("=" * 50)
        print(f"[EMAIL] OTP EMAIL ({mode})")
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
        print("[EMAIL] REQUEST CONFIRMATION SIMULATION")
        print("=" * 50)
        print(f"To: {to_email}")
        print(f"Document: {request_details.get('document_name', 'N/A')}")
        print(f"Reference: {request_details.get('reference_number', 'N/A')}")
        print("=" * 50)
        return True
    
    def _fallback_attachment_email(self, to_email, subject, body, attachments_data):
        """Fallback for email with attachments"""
        print("=" * 60)
        print("[EMAIL] EMAIL WITH ATTACHMENTS (FALLBACK)")
        print("=" * 60)
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Attachments: {[att['file_name'] for att in attachments_data]}")
        print(f"Body: {body[:100]}...")  # First 100 chars of body
        print("=" * 60)
        print("[OK] Email with attachments would be sent to", to_email)
        print("=" * 60)
        return True

    # Helper methods to run async functions from sync contexts
    def send_otp_email_sync(self, to_email, otp_code):
        """Synchronous wrapper for async send_otp_email"""
        return safe_async_run(self.send_otp_email, to_email, otp_code)

    def send_email_with_attachments_sync(self, to_email, subject, body, attachments_data):
        """Synchronous wrapper for async send_email_with_attachments"""
        return safe_async_run(self.send_email_with_attachments, to_email, subject, body, attachments_data)

    def send_document_ready_email_sync(self, to_email, request_details, db_connection):
        """Synchronous wrapper for async send_document_ready_email"""
        return safe_async_run(self.send_document_ready_email, to_email, request_details, db_connection)

    def send_request_confirmation_sync(self, to_email, request_details):
        """Synchronous wrapper for async send_request_confirmation"""
        return safe_async_run(self.send_request_confirmation, to_email, request_details)

    async def send_payment_receipt(self, to_email, payment_details):
        """Send payment receipt email using async SMTP with OTP email format"""
        try:
            if not self.email_enabled:
                return self._fallback_payment_receipt_email(to_email, payment_details)
            
            subject = f"Payment Receipt - {payment_details.get('request_number', '')}"
            
            # Format payment date
            payment_date = payment_details.get('payment_date', '')
            if payment_date:
                if isinstance(payment_date, str):
                    payment_date = payment_date
                else:
                    payment_date = payment_date.strftime('%B %d, %Y at %I:%M %p')
            else:
                payment_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
            
            # Format amount
            amount = payment_details.get('amount', 0)
            if isinstance(amount, (int, float)):
                amount_str = f"₱{amount:,.2f}"
            else:
                amount_str = str(amount)
            
            body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    .header {{
                        background-color: #792D1B;
                        padding: 30px 20px;
                        text-align: center;
                    }}
                    .header h1 {{
                        color: #FFD700;
                        font-size: 24px;
                        font-weight: bold;
                        margin: 0;
                        text-transform: uppercase;
                    }}
                    .header h2 {{
                        color: #ffffff;
                        font-size: 16px;
                        font-weight: bold;
                        margin: 10px 0 0 0;
                    }}
                    .body-content {{
                        padding: 30px;
                    }}
                    .receipt-title {{
                        color: #792D1B;
                        font-size: 20px;
                        font-weight: bold;
                        margin-bottom: 20px;
                    }}
                    .receipt-box {{
                        background-color: #f5f5f5;
                        border-radius: 8px;
                        padding: 25px;
                        margin: 30px 0;
                        text-align: center;
                    }}
                    .receipt-amount {{
                        font-size: 36px;
                        font-weight: bold;
                        color: #792D1B;
                        margin: 10px 0;
                        letter-spacing: 2px;
                    }}
                    .receipt-details {{
                        text-align: left;
                        margin-top: 20px;
                        line-height: 1.8;
                    }}
                    .receipt-details p {{
                        margin: 8px 0;
                        color: #333333;
                    }}
                    .receipt-details strong {{
                        color: #792D1B;
                    }}
                    .separator {{
                        border-top: 1px solid #e0e0e0;
                        margin: 25px 0;
                    }}
                    .footer-note {{
                        color: #666666;
                        font-size: 12px;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2>Document Request System</h2>
                    </div>
                    
                    <div class="body-content">
                        <div class="receipt-title">Payment Receipt</div>
                        
                        <p>Dear {payment_details.get('student_name', 'Student')},</p>
                        <p>Your payment has been successfully processed. Please find the receipt details below:</p>
                        
                        <div class="receipt-box">
                            <div class="receipt-amount">{amount_str}</div>
                        </div>
                        
                        <div class="receipt-details">
                            <p><strong>Request Number:</strong> {payment_details.get('request_number', 'N/A')}</p>
                            <p><strong>Payment Method:</strong> {payment_details.get('payment_method', 'Online').title()}</p>
                            <p><strong>Reference Number:</strong> {payment_details.get('reference_number', 'N/A')}</p>
                            <p><strong>Transaction ID:</strong> {payment_details.get('transaction_id', 'N/A')}</p>
                            <p><strong>Payment Date:</strong> {payment_date}</p>
                            <p><strong>Document Type:</strong> {payment_details.get('document_name', 'N/A')}</p>
                            <p><strong>Quantity:</strong> {payment_details.get('quantity', 1)}</p>
                        </div>
                        
                        <p>Your document request is now being processed. You will receive a notification once it's ready.</p>
                        
                        <div class="separator"></div>
                        
                        <p class="footer-note">This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return await self._send_email(to_email, subject, body)
            
        except Exception as e:
            print(f"[ERROR] Payment receipt email error: {e}")
            return self._fallback_payment_receipt_email(to_email, payment_details)
    
    def _fallback_payment_receipt_email(self, to_email, payment_details):
        """Fallback for payment receipt email"""
        print("=" * 50)
        print("[EMAIL] PAYMENT RECEIPT (FALLBACK)")
        print("=" * 50)
        print(f"To: {to_email}")
        print(f"Request: {payment_details.get('request_number', 'N/A')}")
        print(f"Amount: ₱{payment_details.get('amount', 0):.2f}")
        print(f"Reference: {payment_details.get('reference_number', 'N/A')}")
        print("=" * 50)
        return True

    def send_payment_receipt_sync(self, to_email, payment_details):
        """Synchronous wrapper for async send_payment_receipt"""
        return safe_async_run(self.send_payment_receipt, to_email, payment_details)

    def _send_email_sync(self, to_email, subject, body):
        """Synchronous wrapper for async _send_email"""
        return safe_async_run(self._send_email, to_email, subject, body)


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
            cursor.execute("SELECT payment_status FROM document_requests WHERE request_id = %s", (request_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error validating payment: {e}")
            return None


class DocumentGenerator:
    @staticmethod
    def generate_certificate_of_enrollment(student_data, request_data):
        """Generate Certificate of Enrollment PDF"""
        # This would generate the actual PDF document
        # For now, return a simulated PDF content
        pdf_content = f"""
        CERTIFICATE OF ENROLLMENT
        PAMBAYANG DALUBHASAAN NG MARILAO
        
        This is to certify that {student_data['first_name']} {student_data['last_name']}
        with Student Number {student_data['student_number']}
        is currently enrolled in {student_data['course']}
        for the {student_data['year_level']} for Academic Year 2024-2025.
        
        Request Number: {request_data['request_number']}
        Date Issued: {datetime.now().strftime('%Y-%m-%d')}
        
        Registrar's Office
        Pambayang Dalubhasaan ng Marilao
        """
        
        # In a real implementation, you would use a PDF generation library
        # like reportlab, weasyprint, or pdfkit here
        return pdf_content.encode('utf-8')


# Global utility instances
email_service = EmailService()
payment_processor = PaymentProcessor()
validation_helper = ValidationHelper()
document_generator = DocumentGenerator()
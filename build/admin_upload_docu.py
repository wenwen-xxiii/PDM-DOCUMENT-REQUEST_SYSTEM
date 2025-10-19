# admin_upload_docu.py - Admin Upload Document with Email Attachment
import os
import sys
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, messagebox, filedialog
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import re

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
from utils import email_service

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/adminuploaddoc/{path}"))

class AdminUploadDocumentWindow:
    def __init__(self, parent, request_data=None, refresh_callback=None):
        self.parent = parent
        self.request_data = request_data
        self.refresh_callback = refresh_callback 
        self.selected_file_path = None
        self.document_types = []
        
        # Store image references
        self.images = []
        
        self.setup_ui()
        self.load_document_types()
        self.populate_form()
        
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
    def setup_ui(self):
        self.window = Toplevel(self.parent)
        self.window.geometry("502x578")
        self.window.configure(bg="#FCECB7")
        self.window.title("Upload Document - PDM")
        self.window.resizable(False, False)
        
        # Center the window on screen
        self.center_window()
        self.window.transient(self.parent)  # Set as transient to main window
        self.window.grab_set()  # Make it modal

        self.canvas = Canvas(
            self.window,
            bg="#FCECB7",
            height=578,
            width=502,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        
        # UI elements
        self.create_ui_elements()
        
    def create_ui_elements(self):
        # Header rectangles
        self.canvas.create_rectangle(0.0, 0.0, 508.0, 98.0, fill="#792D1B", outline="")
        self.canvas.create_rectangle(0.0, 57.0, 508.0, 99.0, fill="#FFDA0C", outline="")
        self.canvas.create_rectangle(19.0, 122.0, 483.0, 554.0, fill="#FFFFFF", outline="")

        # Request Number Entry
        entry_image_1 = PhotoImage(file=relative_to_assets("entry_request_no.png"))
        self.images.append(entry_image_1)
        self.canvas.create_image(255.5, 182.5, image=entry_image_1)
        
        self.entry_request_no = Entry(
            self.window,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            state="readonly",
            readonlybackground="#FFF1C2"
        )
        self.entry_request_no.place(x=53.0, y=165.0, width=405.0, height=37.0)

        # Document Type Entry
        entry_image_2 = PhotoImage(file=relative_to_assets("entry_doctype.png"))
        self.images.append(entry_image_2)
        self.canvas.create_image(255.5, 269.5, image=entry_image_2)
        
        self.entry_doctype = Entry(
            self.window,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            state="readonly",
            readonlybackground="#FFF1C2"
        )
        self.entry_doctype.place(x=53.0, y=252.0, width=405.0, height=37.0)

        # File Browse Entry
        entry_image_3 = PhotoImage(file=relative_to_assets("entry_browse.png"))
        self.images.append(entry_image_3)
        self.canvas.create_image(317.0, 357.5, image=entry_image_3)
        
        self.entry_browse = Entry(
            self.window,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            state="readonly",
            readonlybackground="#FFF1C2"
        )
        self.entry_browse.place(x=176.0, y=340.0, width=282.0, height=37.0)

        # Remarks Text
        entry_image_4 = PhotoImage(file=relative_to_assets("entry_remarks.png"))
        self.images.append(entry_image_4)
        self.canvas.create_image(256.0, 477.0, image=entry_image_4)
        
        self.entry_remarks = Text(
            self.window,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            wrap="word"
        )
        self.entry_remarks.place(x=54.0, y=431.0, width=404.0, height=94.0)

        # Labels
        self.canvas.create_text(45.0, 134.0, anchor="nw", text="Request Number", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(45.0, 221.0, anchor="nw", text="Type of Document", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(45.0, 309.0, anchor="nw", text="Upload Digital Document", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(45.0, 396.0, anchor="nw", text="Remarks", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))

        # Buttons
        button_image_1 = PhotoImage(file=relative_to_assets("button_back.png"))
        self.images.append(button_image_1)
        self.button_back = Button(
            self.window,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.go_back,
            relief="flat"
        )
        self.button_back.place(x=27.0, y=19.0, width=15.0, height=18.0)

        button_image_2 = PhotoImage(file=relative_to_assets("button_submit.png"))
        self.images.append(button_image_2)
        self.button_submit = Button(
            self.window,
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.submit_document,
            relief="flat"
        )
        self.button_submit.place(x=389.0, y=9.0, width=94.0, height=40.0)

        button_image_3 = PhotoImage(file=relative_to_assets("button_browse.png"))
        self.images.append(button_image_3)
        self.button_browse = Button(
            self.window,
            image=button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.browse_file,
            relief="flat"
        )
        self.button_browse.place(x=45.0, y=338.0, width=116.0, height=39.0)

    def load_document_types(self):
        """Load available document types from database"""
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT document_type_id, code, name 
                FROM document_types 
                WHERE is_available = TRUE
                ORDER BY name
            """)
            
            self.document_types = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to load document types: {str(e)}")

    def populate_form(self):
        """Populate form with request data if available"""
        if self.request_data:
            self.entry_request_no.config(state="normal")
            self.entry_request_no.delete(0, "end")
            self.entry_request_no.insert(0, self.request_data.get('request_number', ''))
            self.entry_request_no.config(state="readonly")
            
            # Set document type if available
            doc_code = self.request_data.get('document_code', '')
            doc_name = self.request_data.get('document_name', '')
            if doc_code and doc_name:
                doc_display = f"{doc_code} - {doc_name}"
                self.entry_doctype.config(state="normal")
                self.entry_doctype.delete(0, "end")
                self.entry_doctype.insert(0, doc_display)
                self.entry_doctype.config(state="readonly")

    def browse_file(self):
        """Open file dialog to select document"""
        file_types = [
            ("PDF files", "*.pdf"),
            ("Word documents", "*.docx"),
            ("Text files", "*.txt"),
            ("Image files", "*.png *.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Document File",
            filetypes=file_types
        )
        
        if filename:
            self.selected_file_path = filename
            # Show only the filename in the entry
            file_name = os.path.basename(filename)
            self.entry_browse.config(state="normal")
            self.entry_browse.delete(0, "end")
            self.entry_browse.insert(0, file_name)
            self.entry_browse.config(state="readonly")

    def create_email_content(self, request_data, remarks):
        """Create email subject and body in PDM format"""
        student_name = request_data['student_name']
        request_number = request_data['request_number']
        document_name = request_data['document_name']
        delivery_mode = request_data.get('delivery_mode', 'pickup')

        if delivery_mode == 'online':
            subject = f"Your Document is Ready - Request #{request_number}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Document Ready for Download</h2>
                        <p>Dear {student_name},</p>
                        
                        <p>Your requested document is now ready for download.</p>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                            <p><strong>Request Number:</strong> #{request_number}</p>
                            <p><strong>Document:</strong> {document_name}</p>
                            <p><strong>Status:</strong> Ready for Download</p>
                            <p><strong>Completed Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                        </div>
                        
                        <p>Your document is attached to this email. You can also download it from the document request system.</p>
                        
                        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #856404; margin-top: 0;">Remarks from Registrar's Office:</h4>
                            <p style="color: #856404; margin: 0;">{remarks if remarks else 'No remarks provided.'}</p>
                        </div>
                        
                        <p>Thank you for using our document request system.</p>
                        
                        <hr style="margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            subject = f"Document Ready for Pickup - Request #{request_number}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Document Ready for Pickup</h2>
                        <p>Dear {student_name},</p>
                        
                        <p>Your document request has been processed and is ready for pickup.</p>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                            <p><strong>Request Number:</strong> #{request_number}</p>
                            <p><strong>Document:</strong> {document_name}</p>
                            <p><strong>Status:</strong> Ready for Pickup</p>
                            <p><strong>Ready Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                        </div>
                        
                        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #155724; margin-top: 0;">Pickup Information:</h4>
                            <p style="color: #155724; margin: 5px 0;"><strong>Location:</strong> Registrar's Office</p>
                            <p style="color: #155724; margin: 5px 0;"><strong>Hours:</strong> Monday-Friday, 8:00 AM - 5:00 PM</p>
                            <p style="color: #155724; margin: 5px 0;"><strong>Requirements:</strong> Please bring your student ID</p>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #856404; margin-top: 0;">Remarks from Registrar's Office:</h4>
                            <p style="color: #856404; margin: 0;">{remarks if remarks else 'No remarks provided.'}</p>
                        </div>
                        
                        <hr style="margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return subject, body

    def send_document_email(self, student_email, subject, body, attachment_path, request_id):
        """Send email with document attachment using your existing email service"""
        try:
            # Read the file data
            with open(attachment_path, 'rb') as file:
                file_data = file.read()
            
            file_name = os.path.basename(attachment_path)
            
            # Prepare attachments data in the format expected by your email service
            attachments_data = [{
                'file_name': file_name,
                'file_data': file_data,
                'file_type': self.get_file_type(file_name)
            }]
            
            # Use your existing email service to send with attachments
            success = email_service.send_email_with_attachments_sync(
                student_email, 
                subject, 
                body, 
                attachments_data
            )
            
            if success:
                print(f"✅ Email with attachment sent to {student_email}")
                return True
            else:
                print(f"❌ Failed to send email with attachment via email_service")
                return self.send_fallback_notification(student_email, subject, body, file_name)
                
        except Exception as e:
            print(f"❌ Error sending email with attachment: {str(e)}")
            file_name = os.path.basename(attachment_path)
            return self.send_fallback_notification(student_email, subject, body, file_name)

    def get_file_type(self, filename):
        """Determine file type based on extension"""
        extension = os.path.splitext(filename)[1].lower()
        file_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        return file_types.get(extension, 'application/octet-stream')

    def send_fallback_notification(self, student_email, subject, body, attachment_name):
        """Fallback notification when email with attachment fails"""
        try:
            # Convert HTML body to plain text for fallback
            plain_body = re.sub(r'<[^<]+?>', '', body)  # Remove HTML tags
            plain_body = re.sub(r'\n\s*\n', '\n\n', plain_body)  # Clean up spacing
            
            enhanced_body = f"""
{plain_body}

Important: Your document '{attachment_name}' is ready but we encountered an issue attaching it to this email.
Please log in to the document request system to download your document.

Best regards,
PDM Registrar's Office
"""
            
            # Use your existing email service for fallback (without attachment)
            success = email_service._send_email_sync(student_email, subject, enhanced_body)
            
            if success:
                print(f"✅ Fallback notification sent to {student_email}")
                return True
            else:
                print(f"❌ Fallback notification failed")
                self._print_fallback_notification(student_email, subject, enhanced_body, attachment_name)
                return False
                
        except Exception as e:
            print(f"❌ All notification methods failed: {str(e)}")
            self._print_fallback_notification(student_email, subject, body, attachment_name)
            return False

    def _print_fallback_notification(self, student_email, subject, body, attachment_name):
        """Print notification as last resort when all email methods fail"""
        print("=" * 70)
        print("📧 EMAIL NOTIFICATION (FALLBACK - PRINT ONLY)")
        print("=" * 70)
        print(f"To: {student_email}")
        print(f"Subject: {subject}")
        print(f"Attachment: {attachment_name}")
        print(f"Body: {body}")
        print("=" * 70)

    def submit_document(self):
        """Submit the uploaded document and send email with attachment"""
        # Validation
        if not self.entry_request_no.get().strip():
            messagebox.showerror("Error", "Request number is required")
            return
            
        if not self.entry_doctype.get().strip():
            messagebox.showerror("Error", "Document type is required")
            return
            
        if not self.selected_file_path:
            messagebox.showerror("Error", "Please select a document file to upload")
            return
            
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # Get request details including student email
            cursor.execute("""
                SELECT 
                    dr.request_id,
                    dr.delivery_mode,
                    s.student_id,
                    CONCAT(s.first_name, ' ', s.last_name) as student_name,
                    u.email as student_email
                FROM document_requests dr
                JOIN students s ON dr.student_id = s.student_id
                JOIN users u ON s.user_id = u.user_id
                WHERE dr.request_number = %s
            """, (self.entry_request_no.get().strip(),))
            result = cursor.fetchone()
            
            if not result:
                messagebox.showerror("Error", "Request number not found")
                return
                
            request_id, delivery_mode, student_id, student_name, student_email = result
            
            # Read file data
            with open(self.selected_file_path, 'rb') as file:
                file_data = file.read()
            
            file_name = os.path.basename(self.selected_file_path)
            file_size = len(file_data)
            remarks = self.entry_remarks.get("1.0", "end-1c").strip()
            
            # Create document_attachments table if not exists
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
            
            # Insert into document_attachments table
            cursor.execute("""
                INSERT INTO document_attachments 
                (request_id, file_name, file_data, file_size, uploaded_by, remarks)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (request_id, file_name, file_data, file_size, "Admin", remarks))
            
            # Update request status based on delivery mode
            if delivery_mode == 'online':
                # For online delivery, mark as completed and send email with attachment
                cursor.execute("""
                    UPDATE document_requests 
                    SET status = 'completed',
                        ready_date = NOW(),
                        completed_date = NOW()
                    WHERE request_id = %s
                """, (request_id,))
                
                status_message = "completed"
            else:
                # For pickup, mark as ready for pickup
                cursor.execute("""
                    UPDATE document_requests 
                    SET status = 'ready_for_pickup',
                        ready_date = NOW()
                    WHERE request_id = %s
                """, (request_id,))
                
                status_message = "ready for pickup"
            
            connection.commit()
            
            # Prepare request data for email
            request_data = {
                'student_name': student_name,
                'request_number': self.entry_request_no.get().strip(),
                'document_name': self.entry_doctype.get().strip(),
                'delivery_mode': delivery_mode
            }
            
            # Send email notification
            subject, body = self.create_email_content(request_data, remarks)
            email_sent = False
            
            if delivery_mode == 'online':
                # Send email with attachment for online delivery
                email_sent = self.send_document_email(
                    student_email, 
                    subject, 
                    body, 
                    self.selected_file_path,
                    request_id
                )
            else:
                # Send regular email for pickup (without attachment)
                email_sent = self.send_fallback_notification(
                    student_email,
                    subject,
                    body,
                    file_name
                )
            
            # Show success message
            success_msg = f"""
Document uploaded successfully!

• Request: {self.entry_request_no.get()}
• File: {file_name}
• Status: {status_message.title()}
• Student: {student_name}
"""

            if email_sent:
                success_msg += "\n✅ Email notification sent to student."
            else:
                success_msg += "\n⚠️ Note: Email notification failed, but document was uploaded successfully."

            messagebox.showinfo("Success", success_msg)
            
            # Call refresh callback if provided
            if self.refresh_callback:
                self.refresh_callback()
                
            self.go_back()
                
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to upload document: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def go_back(self):
        """Close the window"""
        self.window.destroy()
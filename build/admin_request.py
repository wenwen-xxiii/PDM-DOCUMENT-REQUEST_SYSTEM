# adminrequest.py - Admin Requests Manager for Integration
from pathlib import Path
from tkinter import Canvas, Frame, Label, Button, Entry, messagebox, Scrollbar
import mysql.connector
from mysql.connector import Error
import sys
import os
import asyncio
import threading
from datetime import datetime
import base64

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
from async_utils import safe_async_run
from utils import email_service
from admin_upload_docu import AdminUploadDocumentWindow
from view_docu_attachment import DocumentAttachmentViewer

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/adminrequest/{path}"))

class AdminRequestManager:
    def __init__(self, parent, get_db_connection=None, user_data=None):
        self.parent = parent
        self.get_db_connection = get_db_connection
        self.user_data = user_data or {}
        
        # Request data
        self.document_requests = []
        self.filtered_requests = []
        self.search_query = ""
        self.current_page = 1
        self.requests_per_page = 9
        
        # UI element storage
        self.images = []
        self.row_widgets = []
        
        self.setup_ui()
        self.load_document_requests()
        self.update_display()
        
    def setup_ui(self):
        """Setup the requests management UI inside the parent frame"""
        # Create a canvas that fits the content frame
        self.canvas = Canvas(
            self.parent,
            bg="#FFFFFF",
            width=895,
            height=574,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Create scrollbar
        self.scrollbar = Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create top section with "Req" label
        self.create_top_section()
        
        # Create search bar (top-right)
        self.create_searchbar()

        # Create table header
        self.create_table_headers()
        
        # Create navigation controls
        self.create_navigation_controls()
        
    def create_top_section(self):
        """Create the top section with Requests label"""
        # Add "Requests" label on the top-left
        self.canvas.create_text(
            20, 28, 
            anchor="w", 
            text="Requests Management", 
            fill="#792D1B", 
            font=("Inter", 18, "bold"),
        )
        
    def create_table_headers(self):
        """Create table header labels matching the image layout"""
        headers = [
            (40.0, "No.", "center"),
            (120.0, "Request No.", "center"),
            (250.0, "Student", "center"),
            (380.0, "Document", "center"),
            (470.0, "Qty", "center"),
            (520.0, "Date", "center"),
            (620.0, "Status", "center"),
            (770.0, "Actions", "center")
        ]
        
        # Header background - dark brown like in the image
        self.canvas.create_rectangle(20, 55, 875, 95, fill="#792D1B", outline="")
        
        for x, text, anchor in headers:
            self.canvas.create_text(
                x, 75, 
                anchor=anchor, 
                text=text, 
                fill="#FFFFFF", 
                font=("Inter", 12, "bold")
            )

    def create_searchbar(self):
        """Create a search entry on the top-right and bind filtering"""
        # Search entry sized to fit within the right side of header area
        self.search_entry = Entry(
            self.parent,
            bd=1,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=1,
            font=("Inter", 12)
        )
        # Place near the top-right inside the content frame, avoiding scrollbar
        # Content area width ~895; leave room for scrollbar and padding
        self.search_entry.place(x=525, y=18, width=350, height=30)
        self.search_entry.insert(0, "Search request...")
        # Simple placeholder behavior
        def _on_focus_in(event):
            if self.search_entry.get() == "Search request...":
                self.search_entry.delete(0, "end")
        def _on_focus_out(event):
            if not self.search_entry.get().strip():
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, "Search request...")
        self.search_entry.bind("<FocusIn>", _on_focus_in)
        self.search_entry.bind("<FocusOut>", _on_focus_out)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def create_navigation_controls(self):
        """Create page navigation controls"""
        # Previous button
        self.button_prev = Button(
            self.parent,
            text="Previous",
            font=("Inter", 10),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            command=self.previous_page
        )
        self.button_prev.place(x=250, y=530, width=80, height=30)

        # Page number display
        self.entry_page_no = Entry(
            self.parent,
            bd=1,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=1,
            justify="center",
            state="readonly",
            font=("Inter", 10)
        )
        self.entry_page_no.place(x=350, y=530, width=100, height=30)

        # Next button
        self.button_next = Button(
            self.parent,
            text="Next",
            font=("Inter", 10),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            command=self.next_page
        )
        self.button_next.place(x=470, y=530, width=80, height=30)

        # # Refresh button
        # self.button_refresh = Button(
        #     self.parent,
        #     text="Refresh",
        #     font=("Inter", 10),
        #     bg="#792D1B",
        #     fg="#FFDA0C",
        #     relief="flat",
        #     command=self.refresh_requests
        # )
        # self.button_refresh.place(x=570, y=530, width=80, height=30)

    async def load_document_requests_async(self):
        """Load document requests from database using your schema (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    dr.request_id,
                    dr.request_number,
                    CONCAT(s.first_name, ' ', s.last_name) as student_name,
                    s.student_number,
                    dt.code as document_code,
                    dt.name as document_name,
                    dr.quantity,
                    dr.request_date,
                    dr.status,
                    dr.payment_status,
                    dr.total_amount,
                    dr.request_release_date,
                    dr.processed_date,
                    dr.ready_date,
                    dr.completed_date,
                    dr.delivery_mode,
                    u.email as student_email
                FROM document_requests dr
                JOIN students s ON dr.student_id = s.student_id
                JOIN document_types dt ON dr.document_type_id = dt.document_type_id
                JOIN users u ON s.user_id = u.user_id
                ORDER BY dr.request_date DESC
            """)
            
            self.document_requests = cursor.fetchall()
            # Default filtered list is full list
            self.filtered_requests = list(self.document_requests)
            
            cursor.close()
            connection.close()
            
            print(f"✅ Loaded {len(self.document_requests)} document requests from database")
            
        except Error as e:
            print(f"❌ Error loading document requests: {e}")
            messagebox.showerror("Database Error", f"Failed to load document requests: {str(e)}")
            self.document_requests = []

    def load_document_requests(self):
        """Load document requests from database using your schema (sync wrapper)"""
        try:
            safe_async_run(self.load_document_requests_async)
        except Exception as e:
            print(f"❌ Error loading document requests: {e}")

    def update_display(self):
        """Update the display with current page data"""
        self.clear_table_rows()
        
        if not self.filtered_requests:
            self.show_no_requests_message()
            return
            
        self.display_current_requests()
        self.update_navigation()

    def clear_table_rows(self):
        """Clear all table rows"""
        # Remove existing row widgets
        for widget_list in self.row_widgets:
            for widget in widget_list:
                try:
                    widget.destroy()
                except:
                    pass
        self.row_widgets = []
        
        # Clear canvas items except headers
        self.canvas.delete("row")

    def display_current_requests(self):
        """Display requests for current page"""
        start_idx = (self.current_page - 1) * self.requests_per_page
        end_idx = start_idx + self.requests_per_page
        current_requests = self.filtered_requests[start_idx:end_idx]
        
        for i, request in enumerate(current_requests):
            self.create_table_row(i, request)

    def on_search_change(self, event=None):
        """Handle search text changes and filter the list"""
        query = self.search_entry.get().strip()
        # Ignore placeholder
        if query == "Search...":
            query = ""
        self.search_query = query.lower()
        self.apply_search_filter()

    def apply_search_filter(self):
        """Filter document_requests into filtered_requests based on search_query"""
        if not self.search_query:
            self.filtered_requests = list(self.document_requests)
        else:
            q = self.search_query
            def matches(req):
                values = [
                    str(req.get('request_number', '')),
                    str(req.get('student_name', '')),
                    str(req.get('student_number', '')),
                    str(req.get('document_code', '')),
                    str(req.get('document_name', '')),
                    str(req.get('status', '')),
                    str(req.get('payment_status', '')),
                ]
                text = " ".join(values).lower()
                return q in text
            self.filtered_requests = [r for r in self.document_requests if matches(r)]
        # Reset to first page after filtering
        self.current_page = 1
        self.update_display()

    def create_table_row(self, row_index, request):
        """Create a table row with data and action buttons matching the image layout"""
        y_position = 105 + (row_index * 45)
        
        # Row background (alternating colors like in the image)
        fill_color = "#FFFFFF" if row_index % 2 == 0 else "#F8F8F8"
        self.canvas.create_rectangle(
            20, y_position, 875, y_position + 40, 
            fill=fill_color, outline="#E0E0E0", tags="row"
        )
        
        # Calculate row number (global index)
        row_number = ((self.current_page - 1) * self.requests_per_page) + row_index + 1
        
        # Format request date
        request_date = request['request_date']
        if isinstance(request_date, datetime):
            formatted_date = request_date.strftime('%m/%d/%Y')
        else:
            formatted_date = str(request_date)
        
        # Create text elements for the row with proper alignment (centered like in image)
        text_configs = [
            (40.0, str(row_number), "center"),
            (120.0, request['request_number'], "center"),
            (250.0, f"{request['student_name']}", "center"),
            (380.0, request['document_code'], "center"),
            (470.0, str(request['quantity']), "center"),
            (520.0, formatted_date, "center"),
            (620.0, self.format_status_display_compact(request['status'], request['payment_status']), "center")
        ]
        
        for x, text, anchor in text_configs:
            self.canvas.create_text(
                x, y_position + 20, 
                anchor=anchor, 
                text=text,
                fill="#1E1E1E", 
                font=("Inter", 10), 
                tags="row"
            )
        
        # Create action buttons
        self.create_row_buttons_compact(row_index, request, y_position)

    def format_status_display_compact(self, status, payment_status):
        """Compact status display matching the image"""
        status_map = {
            'payment_pending': 'Payment Pending',
            'processing': 'Processing',
            'ready_for_pickup': 'Ready',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'rejected': 'Rejected'
        }
        
        base_status = status_map.get(status, status.replace('_', ' ').title())
        
        # For payment_pending status, show payment status
        if status == 'payment_pending':
            if payment_status == 'paid':
                return "Paid"
            else:
                return "Payment Pending"
        
        return base_status

    def create_row_buttons_compact(self, row_index, request, y_position):
        """Create action buttons with Pay/Ready/Complete centered and Upload button"""
        button_widgets = []
        
        # View button - always available (first button)
        view_button = Button(
            self.parent,
            text="View",
            font=("Inter", 9),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=lambda r=request: self.view_request(r)
        )
        view_button.place(x=690, y=y_position + 8, width=50, height=25)
        button_widgets.append(view_button)
        
        status = request['status']
        payment_status = request.get('payment_status', 'pending')
        
        # Action button position (centered in the actions column)
        # The actions column spans from ~690 to ~870, so center is around 780
        action_button_center_x = 775
        
        # Conditional button display:
        if status == 'payment_pending' and payment_status == 'pending':
            # Show Pay button centered
            pay_button = Button(
                self.parent,
                text="Pay",
                font=("Inter", 9),
                bg="#28a745",
                fg="#FFFFFF",
                relief="flat",
                command=lambda r=request: self.approve_payment(r)
            )
            # Center the Pay button (width 40)
            pay_button.place(x=action_button_center_x - 20, y=y_position + 8, width=40, height=25)
            button_widgets.append(pay_button)
            
        elif status == 'processing':
            # Show Ready button centered
            ready_button = Button(
                self.parent,
                text="Ready",
                font=("Inter", 9),
                bg="#ffc107",
                fg="#000000",
                relief="flat",
                command=lambda r=request: self.mark_ready(r)
            )
            # Center the Ready button (width 50)
            ready_button.place(x=action_button_center_x - 25, y=y_position + 8, width=50, height=25)
            button_widgets.append(ready_button)
            
        elif status == 'ready_for_pickup':
            # Show Complete button centered
            complete_button = Button(
                self.parent,
                text="Complete",
                font=("Inter", 9),
                bg="#28a745",
                fg="#FFFFFF",
                relief="flat",
                command=lambda r=request: self.complete_request(r)
            )
            # Center the Complete button (width 65)
            complete_button.place(x=action_button_center_x - 32.5, y=y_position + 8, width=65, height=25)
            button_widgets.append(complete_button)
            
        else:
            # For completed and other statuses, show disabled Pay button centered
            pay_button_disabled = Button(
                self.parent,
                text="Pay",
                font=("Inter", 9),
                bg="#CCCCCC",
                fg="#666666",
                relief="flat",
                state="disabled"
            )
            pay_button_disabled.place(x=action_button_center_x - 20, y=y_position + 8, width=40, height=25)
            button_widgets.append(pay_button_disabled)
        
        # Upload button - always shown but enabled only for specific statuses
        upload_enabled = status in ['processing', 'ready_for_pickup', 'completed']
        upload_button = Button(
            self.parent,
            text="Upload",
            font=("Inter", 9),
            bg="#6c757d" if upload_enabled else "#CCCCCC",
            fg="#FFFFFF",
            relief="flat",
            command=lambda r=request: self.upload_document(r),
            state="normal" if upload_enabled else "disabled"
        )
        upload_button.place(x=812, y=y_position + 8, width=50, height=25)
        button_widgets.append(upload_button)
        
        self.row_widgets.append(button_widgets)

    def get_document_attachments(self, request_id):
        """Get document attachments for a request"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return []
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    file_name,
                    file_data,
                    file_type,
                    file_size
                FROM document_attachments 
                WHERE request_id = %s
            """, (request_id,))
            
            attachments = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return attachments
            
        except Error as e:
            print(f"❌ Error loading document attachments: {e}")
            return []

    async def send_email_notification_async(self, student_email, subject, body, attachments=None):
        """Send email notification to student using enhanced email service (async version)"""
        try:
            if attachments:
                # Use the enhanced email service with attachments
                success = await email_service.send_email_with_attachments(
                    student_email, 
                    subject, 
                    body, 
                    attachments
                )
            else:
                # Use regular email service
                success = await email_service._send_email(
                    student_email, 
                    subject, 
                    body
                )
            
            if success:
                print(f"✅ PDM Email sent to {student_email}")
                if attachments:
                    print(f"📎 Sent {len(attachments)} attachment(s) with email")
                return True
            else:
                print(f"❌ Failed to send PDM email to {student_email}")
                return False
                
        except Exception as e:
            print(f"❌ PDM Email error: {e}")
            return False

    def send_email_notification(self, student_email, subject, body, attachments=None):
        """Send email notification to student using enhanced email service (sync wrapper)"""
        try:
            return safe_async_run(self.send_email_notification_async, student_email, subject, body, attachments)
        except Exception as e:
            print(f"❌ Error sending email notification: {e}")
            return False
    
    def _fallback_email_notification(self, student_email, subject, body, attachments=None):
        """Fallback email notification method"""
        print("=" * 60)
        print("📧 EMAIL NOTIFICATION (FALLBACK)")
        print("=" * 60)
        print(f"To: {student_email}")
        print(f"Subject: {subject}")
        if attachments:
            print(f"Attachments: {[att['file_name'] for att in attachments]}")
        print(f"Body: {body}")
        print("=" * 60)

    def create_notification_message(self, request, action, has_attachments=False, remarks=""):
        """Create appropriate notification message based on action using HTML PDM format"""
        student_name = request['student_name']
        request_number = request['request_number']
        document_name = request['document_name']
        delivery_mode = request.get('delivery_mode', 'pickup')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if action == "payment_approved":
            subject = f"Payment Approved - Request #{request_number}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Payment Approved</h2>
                        <p>Dear {student_name},</p>
                        
                        <p>Your payment for document request #{request_number} has been approved and your document is now being processed.</p>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                            <p><strong>Request Number:</strong> #{request_number}</p>
                            <p><strong>Document:</strong> {document_name}</p>
                            <p><strong>Amount Paid:</strong> ₱{request.get('total_amount', 0):.2f}</p>
                            <p><strong>Status:</strong> Under Review</p>
                            <p><strong>Approval Date:</strong> {current_date}</p>
                        </div>
                        
                        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #155724; margin-top: 0;">Next Steps:</h4>
                            <p style="color: #155724; margin: 5px 0;">Your document is now being processed by the Registrar's Office</p>
                            <p style="color: #155724; margin: 5px 0;">You will be notified when your document is ready for {delivery_mode}</p>
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
            
        elif action == "ready":
            if delivery_mode == 'online':
                subject = f"Document Ready for Download - Request #{request_number}"
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
                            
                            <p>Your document request has been processed and is ready for download.</p>
                            
                            <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                                <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                                <p><strong>Request Number:</strong> #{request_number}</p>
                                <p><strong>Document:</strong> {document_name}</p>
                                <p><strong>Status:</strong> Ready for Download</p>
                                <p><strong>Ready Date:</strong> {current_date}</p>
                            </div>
                            
                            <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <h4 style="color: #155724; margin-top: 0;">Download Information:</h4>
                                <p style="color: #155724; margin: 5px 0;">Your document is attached to this email</p>
                                <p style="color: #155724; margin: 5px 0;">Please download and save the document for your records</p>
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
                                <p><strong>Ready Date:</strong> {current_date}</p>
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
                
        elif action == "completed":
            subject = f"Request Completed - #{request_number}"
            if delivery_mode == 'online':
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
                            <p>Dear {student_name},</p>
                            
                            <p>Your document request has been completed and delivered.</p>
                            
                            <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                                <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                                <p><strong>Request Number:</strong> #{request_number}</p>
                                <p><strong>Document:</strong> {document_name}</p>
                                <p><strong>Status:</strong> Completed</p>
                                <p><strong>Completion Date:</strong> {current_date}</p>
                                <p><strong>Delivery Method:</strong> Online Delivery</p>
                            </div>
                            
                            <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <h4 style="color: #155724; margin-top: 0;">Delivery Information:</h4>
                                <p style="color: #155724; margin: 5px 0;">Your document has been delivered to your email</p>
                                <p style="color: #155724; margin: 5px 0;">Please check your inbox and spam folder</p>
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
            else:
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
                            <p>Dear {student_name},</p>
                            
                            <p>Your document request has been completed.</p>
                            
                            <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                                <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                                <p><strong>Request Number:</strong> #{request_number}</p>
                                <p><strong>Document:</strong> {document_name}</p>
                                <p><strong>Status:</strong> Completed</p>
                                <p><strong>Completion Date:</strong> {current_date}</p>
                                <p><strong>Delivery Method:</strong> Campus Pickup</p>
                            </div>
                            
                            <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <h4 style="color: #0c5460; margin-top: 0;">Thank You:</h4>
                                <p style="color: #0c5460; margin: 5px 0;">Thank you for using the PDM Document Request System</p>
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
        else:
            subject = f"Update on Request #{request_number}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Request Update</h2>
                        <p>Dear {student_name},</p>
                        
                        <p>There is an update on your document request #{request_number}.</p>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Request Details:</h3>
                            <p><strong>Request Number:</strong> #{request_number}</p>
                            <p><strong>Document:</strong> {document_name}</p>
                            <p><strong>Status:</strong> {self.format_status_display(request['status'], request.get('payment_status', 'pending'))}</p>
                            <p><strong>Update Date:</strong> {current_date}</p>
                        </div>
                        
                        <p>Please check the document request system for the latest status.</p>
                        
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

    async def send_document_ready_email_async(self, request):
        """Send email with document attachments when document is ready (async version)"""
        try:
            # Get attachments from database
            attachments = self.get_document_attachments(request['request_id'])
            
            if attachments:
                # Prepare attachments data for email service
                attachments_data = []
                for attachment in attachments:
                    if attachment['file_data']:  # Only include if BLOB data exists
                        attachments_data.append({
                            'file_name': attachment['file_name'],
                            'file_data': attachment['file_data'],
                            'file_type': attachment.get('file_type', 'application/pdf')
                        })
                
                # Create email content
                subject, body = self.create_notification_message(request, "completed", has_attachments=True)
                
                # Send email with attachments (async)
                success = await self.send_email_notification_async(
                    request.get('student_email'), 
                    subject, 
                    body, 
                    attachments_data
                )
                
                if success:
                    print(f"✅ Document ready email with attachments sent to {request.get('student_email')}")
                else:
                    print(f"❌ Failed to send document ready email with attachments")
                
                return success
            else:
                # No attachments, send regular notification
                subject, body = self.create_notification_message(request, "completed")
                return await self.send_email_notification_async(request.get('student_email'), subject, body)
                
        except Exception as e:
            print(f"❌ Error sending document ready email: {e}")
            return False

    def send_document_ready_email(self, request):
        """Send email with document attachments when document is ready (sync wrapper)"""
        try:
            return safe_async_run(self.send_document_ready_email_async, request)
        except Exception as e:
            print(f"❌ Error sending document ready email: {e}")
            return False

    def view_request(self, request):
        """View request details and attachments"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    dr.*,
                    CONCAT(s.first_name, ' ', s.last_name) as student_name,
                    s.student_number,
                    s.course,
                    s.year_level,
                    s.contact_number,
                    dt.name as document_name,
                    dt.code as document_code,
                    dt.fee_amount,
                    st.first_name as processed_by_first,
                    st.last_name as processed_by_last
                FROM document_requests dr
                JOIN students s ON dr.student_id = s.student_id
                JOIN document_types dt ON dr.document_type_id = dt.document_type_id
                LEFT JOIN staff st ON dr.processed_by = st.staff_id
                WHERE dr.request_id = %s
            """, (request['request_id'],))
            
            detailed_request = cursor.fetchone()
            
            # Check for attachments
            cursor.execute("""
                SELECT COUNT(*) as attachment_count 
                FROM document_attachments 
                WHERE request_id = %s
            """, (request['request_id'],))
            
            attachment_result = cursor.fetchone()
            attachment_count = attachment_result['attachment_count'] if attachment_result else 0
            
            cursor.close()
            connection.close()
            
            if detailed_request:
                # Show options dialog
                from tkinter import Toplevel, Label, Button
                
                options_dialog = Toplevel(self.parent)
                options_dialog.title("View Request Options")
                options_dialog.geometry("400x200")
                options_dialog.configure(bg="#FCECB7")
                options_dialog.transient(self.parent)
                options_dialog.grab_set()
                
                # Center the dialog
                options_dialog.update_idletasks()
                width, height = 400, 200
                screen_width = options_dialog.winfo_screenwidth()
                screen_height = options_dialog.winfo_screenheight()
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                options_dialog.geometry(f'{width}x{height}+{x}+{y}')
                
                # Header
                Label(
                    options_dialog,
                    text="View Request Options",
                    font=("Inter", 16, "bold"),
                    bg="#FCECB7",
                    fg="#792D1B"
                ).pack(pady=20)
                
                # Request info
                Label(
                    options_dialog,
                    text=f"Request #{detailed_request['request_number']}",
                    font=("Inter", 12),
                    bg="#FCECB7",
                    fg="#000000"
                ).pack(pady=5)
                
                Label(
                    options_dialog,
                    text=f"Student: {detailed_request['student_name']}",
                    font=("Inter", 10),
                    bg="#FCECB7",
                    fg="#666666"
                ).pack(pady=2)
                
                # Buttons frame
                buttons_frame = Frame(options_dialog, bg="#FCECB7")
                buttons_frame.pack(pady=20)
                
                # View Details button
                Button(
                    buttons_frame,
                    text="📋 View Details",
                    font=("Inter", 10),
                    bg="#007BFF",
                    fg="#FFFFFF",
                    relief="flat",
                    command=lambda: [options_dialog.destroy(), self.view_request_details(detailed_request)]
                ).pack(side="left", padx=10)
                
                # View Attachments button (if available)
                if attachment_count > 0:
                    Button(
                        buttons_frame,
                        text=f"📎 View Attachments ({attachment_count})",
                        font=("Inter", 10),
                        bg="#28A745",
                        fg="#FFFFFF",
                        relief="flat",
                        command=lambda: [options_dialog.destroy(), self.view_attachments(request['request_id'])]
                    ).pack(side="left", padx=10)
                else:
                    Button(
                        buttons_frame,
                        text="📎 No Attachments",
                        font=("Inter", 10),
                        bg="#6C757D",
                        fg="#FFFFFF",
                        relief="flat",
                        state="disabled"
                    ).pack(side="left", padx=10)
                
                # Close button
                Button(
                    buttons_frame,
                    text="✕ Close",
                    font=("Inter", 10),
                    bg="#DC3545",
                    fg="#FFFFFF",
                    relief="flat",
                    command=options_dialog.destroy
                ).pack(side="left", padx=10)
                
            else:
                messagebox.showerror("Error", "Could not load request details")
                
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to load request details: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open request options: {str(e)}")
    
    def view_request_details(self, detailed_request):
        """View request details in form format"""
        try:
            from requestform import DocumentRequestWindow
            
            def dummy_callback():
                pass
            
            request_window = DocumentRequestWindow(
                parent=self.parent,
                student_id=detailed_request['student_id'],
                show_dashboard_callback=dummy_callback
            )
            
            self.populate_request_form(request_window, detailed_request)
            
        except ImportError:
            messagebox.showerror("Error", "Request form module not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open request form: {str(e)}")
    
    def view_attachments(self, request_id):
        """View document attachments"""
        try:
            DocumentAttachmentViewer(
                parent=self.parent,
                request_id=request_id,
                get_db_connection=self.get_db_connection
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open attachment viewer: {str(e)}")
    
    def populate_request_form(self, request_window, request_data):
        """Populate the request form with existing data in read-only mode"""
        try:
            request_window.window.geometry("508x670")
            
            # Set document type
            doc_display = f"{request_data['document_code']} - {request_data['document_name']}"
            request_window.doc_type_var.set(doc_display)
            request_window.combobox_docType.config(state="disabled")
            
            # Set quantity
            request_window.quantity_var.set(str(request_data['quantity']))
            request_window.entry_quantity.config(
                state="readonly",
                readonlybackground="#FFF1C2"
            )
            
            # Set price
            request_window.price_var.set(f"₱{request_data['fee_amount']:.2f}")
            request_window.entry_price_per_copy.config(
                state="readonly",
                readonlybackground="#FFF1C2"
            )
            
            # Set total
            request_window.total_var.set(f"₱{request_data['total_amount']:.2f}")
            request_window.entry_total.config(
                state="readonly",
                readonlybackground="#FFF1C2"
            )
            
            # Set releasing date
            if request_data['request_release_date']:
                if isinstance(request_data['request_release_date'], datetime):
                    release_date = request_data['request_release_date'].strftime("%Y-%m-%d")
                else:
                    release_date = str(request_data['request_release_date'])
                request_window.releasing_date_var.set(release_date)
            
            request_window.entry_releasingDate.config(
                state="readonly",
                readonlybackground="#FFF1C2"
            )
            
            # Set delivery mode
            delivery_display = "Pickup" if request_data['delivery_mode'] == 'pickup' else "Online Delivery"
            request_window.delivery_var.set(delivery_display)
            request_window.combobox_deliveryType.config(state="disabled")
            
            # Set purpose
            request_window.text_purpose.delete("1.0", "end")
            if request_data['purpose_details']:
                request_window.text_purpose.insert("1.0", request_data['purpose_details'])
            request_window.text_purpose.config(
                state="disabled",
                bg="#FFF1C2"
            )
            
            # Disable quantity buttons
            request_window.button_numeridown_quantity.config(state="disabled")
            request_window.button_numericup_quantity.config(state="disabled")
            
            # HIDE the submit button instead of changing it to "Close"
            request_window.button_submit.place_forget()  # This completely removes it from the layout
            
            # Update window title
            request_window.window.title(f"View Request - {request_data['request_number']}")
            
            # Add status information
            self.add_status_info(request_window, request_data)
            
            # Optional: Add a close button in a different location if needed
            close_button = Button(
                request_window.window,
                text="Close",
                font=("Inter", 12, "bold"),
                bg="#792D1B",
                fg="#FFDA0C",
                relief="flat",
                command=request_window.window.destroy
            )
            close_button.place(x=200, y=620, width=120, height=40)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to populate form: {str(e)}")
            
    def add_status_info(self, request_window, request_data):
        """Add status information to the request form"""
        status_frame = Frame(
            request_window.window,
            bg="#FFDA0C",
            relief="solid",
            bd=1
        )
        status_frame.place(x=19, y=65, width=470, height=25)
        
        # Request Number
        request_label = Label(
            status_frame,
            text=f"Request #: {request_data['request_number']}",
            bg="#FFDA0C",
            fg="#792D1B",
            font=("Inter", 10, "bold")
        )
        request_label.place(x=10, y=4)
        
        # Status
        status_label = Label(
            status_frame,
            text="Status:",
            bg="#FFDA0C",
            fg="#792D1B",
            font=("Inter", 10, "bold")
        )
        status_label.place(x=180, y=4)
        
        status_text = Label(
            status_frame,
            text=self.format_status_display(request_data['status'], request_data['payment_status']),
            bg="#FFDA0C",
            fg="#1E1E1E",
            font=("Inter", 10)
        )
        status_text.place(x=225, y=4)
           
    def format_status_display(self, status, payment_status):
        """Full status display for detailed view"""
        status_map = {
            'payment_pending': 'Payment Pending',
            'processing': 'Processing',
            'ready_for_pickup': 'Ready for Pickup',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'rejected': 'Rejected'
        }
        
        base_status = status_map.get(status, status.replace('_', ' ').title())
        
        if status == 'payment_pending' and payment_status == 'paid':
            return f"{base_status} (Payment Verified)"
        elif status == 'payment_pending' and payment_status == 'pending':
            return f"{base_status} (Awaiting Payment)"
        
        return base_status

    async def _update_request_status_in_db_async(self, request_id, status=None, payment_status=None,
                                     processed_date=None, ready_date=None, completed_date=None):
        """Helper to update a document_requests row and refresh local cache/UI (async version)."""
        try:
            conn = self.get_db_connection()
            if not conn:
                print("❌ No DB connection available for updating request status.")
                return False
            cursor = conn.cursor()
            fields = []
            params = []
            if status is not None:
                fields.append("status = %s")
                params.append(status)
            if payment_status is not None:
                fields.append("payment_status = %s")
                params.append(payment_status)
            if processed_date is not None:
                fields.append("processed_date = %s")
                params.append(processed_date)
            if ready_date is not None:
                fields.append("ready_date = %s")
                params.append(ready_date)
            if completed_date is not None:
                fields.append("completed_date = %s")
                params.append(completed_date)
            if not fields:
                cursor.close()
                conn.close()
                return False
            params.append(request_id)
            sql = f"UPDATE document_requests SET {', '.join(fields)} WHERE request_id = %s"
            cursor.execute(sql, tuple(params))
            conn.commit()
            cursor.close()
            conn.close()
            
            # Reload data and update display
            await self.load_document_requests_async()
            # Schedule UI update on main thread
            self.parent.after(0, self.update_display)
            return True
        except Exception as e:
            print(f"❌ Failed to update request #{request_id}: {e}")
            return False

    def _update_request_status_in_db(self, request_id, status=None, payment_status=None,
                                     processed_date=None, ready_date=None, completed_date=None):
        """Helper to update a document_requests row and refresh local cache/UI (sync wrapper)."""
        try:
            return safe_async_run(self._update_request_status_in_db_async, request_id, status, payment_status, processed_date, ready_date, completed_date)
        except Exception as e:
            print(f"❌ Error updating request status: {e}")
            return False

    def approve_payment(self, request):
        """Approve payment and set status to processing"""
        if messagebox.askyesno("Approve Payment", 
                             f"Approve payment for request {request['request_number']}?\n"
                             f"Student: {request['student_name']}\n"
                             f"Document: {request['document_name']}\n"
                             f"Amount: ₱{request.get('total_amount', 0):.2f}"):
            
            # Use threading to avoid blocking UI
            def approve_thread():
                try:
                    request_id = request['request_id']
                    now = datetime.now()
                    updated = self._update_request_status_in_db(
                        request_id,
                        status='processing',
                        payment_status='paid',
                        processed_date=now
                    )
                    
                    # Schedule UI update on main thread
                    def update_ui():
                        if updated:
                            print(f"✅ Payment approved for request {request['request_number']}")
                            subject, body = self.create_notification_message(request, "payment_approved")
                            # Send email in background thread
                            def email_thread():
                                self.send_email_notification(request.get('student_email'), subject, body)
                            threading.Thread(target=email_thread, daemon=True).start()
                            messagebox.showinfo("Success", f"Payment approved for request {request['request_number']}")
                        else:
                            messagebox.showerror("Update Error", "Failed to approve payment.")
                    
                    self.parent.after(0, update_ui)
                    
                except Exception as e:
                    print(f"❌ Error approving payment: {e}")
                    self.parent.after(0, lambda: messagebox.showerror("Error", f"Failed to approve payment: {str(e)}"))
            
            # Run approve in background thread
            approve_thread_obj = threading.Thread(target=approve_thread, daemon=True)
            approve_thread_obj.start()

    def mark_ready(self, request):
        """Mark request as ready"""
        if messagebox.askyesno("Mark as Ready", 
                             f"Mark request {request['request_number']} as ready?\n"
                             f"Student: {request['student_name']}\n"
                             f"Document: {request['document_name']}"):
            
            # Use threading to avoid blocking UI
            def mark_ready_thread():
                try:
                    request_id = request['request_id']
                    delivery_mode = request.get('delivery_mode', 'pickup')
                    now = datetime.now()
                    
                    if delivery_mode == 'online':
                        success = self._update_request_status_in_db(
                            request_id,
                            status='completed',
                            ready_date=now,
                            completed_date=now
                        )
                        
                        # Schedule UI update on main thread
                        def update_ui():
                            if success:
                                print(f"✅ Request {request['request_number']} completed (online delivery).")
                                # For online delivery, send email with attachments in background thread
                                def email_thread():
                                    email_success = self.send_document_ready_email(request)
                                    if email_success:
                                        self.parent.after(0, lambda: messagebox.showinfo("Success", f"Request {request['request_number']} marked as completed and email sent with document"))
                                    else:
                                        self.parent.after(0, lambda: messagebox.showwarning("Partial Success", f"Request {request['request_number']} marked as completed but email failed to send"))
                                threading.Thread(target=email_thread, daemon=True).start()
                            else:
                                messagebox.showerror("Update Error", "Failed to mark request as completed.")
                        
                        self.parent.after(0, update_ui)
                    else:
                        success = self._update_request_status_in_db(
                            request_id,
                            status='ready_for_pickup',
                            ready_date=now
                        )
                        
                        # Schedule UI update on main thread
                        def update_ui():
                            if success:
                                print(f"✅ Request {request['request_number']} marked ready for pickup.")
                                subject, body = self.create_notification_message(request, "ready")
                                # Send email in background thread
                                def email_thread():
                                    self.send_email_notification(request.get('student_email'), subject, body)
                                threading.Thread(target=email_thread, daemon=True).start()
                                messagebox.showinfo("Success", f"Request {request['request_number']} marked as ready for pickup")
                            else:
                                messagebox.showerror("Update Error", "Failed to mark request as ready.")
                        
                        self.parent.after(0, update_ui)
                    
                except Exception as e:
                    print(f"❌ Error marking ready: {e}")
                    self.parent.after(0, lambda: messagebox.showerror("Error", f"Failed to mark request as ready: {str(e)}"))
            
            # Run mark ready in background thread
            mark_ready_thread_obj = threading.Thread(target=mark_ready_thread, daemon=True)
            mark_ready_thread_obj.start()

    def complete_request(self, request):
        """Complete request (for pickup delivery)"""
        if messagebox.askyesno("Complete Request", 
                             f"Mark request {request['request_number']} as completed?\n"
                             f"Student: {request['student_name']}\n"
                             f"Document: {request['document_name']}"):
            
            # Use threading to avoid blocking UI
            def complete_thread():
                try:
                    request_id = request['request_id']
                    now = datetime.now()
                    success = self._update_request_status_in_db(
                        request_id,
                        status='completed',
                        completed_date=now
                    )
                    
                    # Schedule UI update on main thread
                    def update_ui():
                        if success:
                            print(f"✅ Request {request['request_number']} marked completed.")
                            # For pickup completion, send notification without attachments in background thread
                            def email_thread():
                                subject, body = self.create_notification_message(request, "completed")
                                email_success = self.send_email_notification(request.get('student_email'), subject, body)
                                if email_success:
                                    self.parent.after(0, lambda: messagebox.showinfo("Success", f"Request {request['request_number']} marked as completed and notification sent"))
                                else:
                                    self.parent.after(0, lambda: messagebox.showwarning("Partial Success", f"Request {request['request_number']} marked as completed but notification failed to send"))
                            threading.Thread(target=email_thread, daemon=True).start()
                        else:
                            messagebox.showerror("Update Error", "Failed to mark request as completed.")
                    
                    self.parent.after(0, update_ui)
                    
                except Exception as e:
                    print(f"❌ Error completing request: {e}")
                    self.parent.after(0, lambda: messagebox.showerror("Error", f"Failed to complete request: {str(e)}"))
            
            # Run complete in background thread
            complete_thread_obj = threading.Thread(target=complete_thread, daemon=True)
            complete_thread_obj.start()

    def upload_document(self, request):
        """Handle document upload for a request with refresh callback"""
        try:
            # Try to import the upload module
            try:
                from admin_upload_docu import AdminUploadDocumentWindow
            except ImportError as e:
                print(f"❌ Import error: {e}")
                # Try alternative import path
                try:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    if current_dir not in sys.path:
                        sys.path.append(current_dir)
                    from admin_upload_docu import AdminUploadDocumentWindow
                except ImportError as e2:
                    print(f"❌ Alternative import failed: {e2}")
                    messagebox.showerror("Error", f"Upload document module not found: {str(e)}")
                    return
            
            print(f"🔄 Opening upload window for request {request['request_number']}")
            print(f"🔄 Refresh callback available: {hasattr(self, 'refresh_requests')}")
            
            upload_window = AdminUploadDocumentWindow(
                parent=self.parent,
                request_data=request,
                refresh_callback=self.refresh_requests
            )
            print("✅ Upload window opened successfully")
            
        except Exception as e:
            print(f"❌ Error opening upload window: {e}")
            messagebox.showerror("Error", f"Failed to open upload window: {str(e)}")

    def show_no_requests_message(self):
        """Show message when no requests exist"""
        self.canvas.create_text(
            450, 200, anchor="center", text="No document requests found",
            fill="#666666", font=("Inter", 14, "bold"), tags="row"
        )

    def update_navigation(self):
        """Update navigation elements"""
        total_pages = max(1, (len(self.filtered_requests) + self.requests_per_page - 1) // self.requests_per_page)
        self.entry_page_no.config(state="normal")
        self.entry_page_no.delete(0, "end")
        self.entry_page_no.insert(0, f"Page {self.current_page} of {total_pages}")
        self.entry_page_no.config(state="readonly")
        
        self.button_prev.config(state="normal" if self.current_page > 1 else "disabled")
        self.button_next.config(state="normal" if self.current_page < total_pages else "disabled")

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_display()

    def next_page(self):
        """Go to next page"""
        total_pages = max(1, (len(self.document_requests) + self.requests_per_page - 1) // self.requests_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()

    def refresh_requests(self):
        """Refresh the requests list"""
        print("🔄 Refreshing admin requests...")
        try:
            # Use threading to avoid blocking UI
            def refresh_thread():
                try:
                    self.load_document_requests()
                    self.current_page = 1
                    # Schedule UI update on main thread
                    self.parent.after(0, self.update_display)
                    print(f"✅ Refresh complete - {len(self.document_requests)} requests loaded")
                except Exception as e:
                    print(f"❌ Error during refresh: {e}")
            
            # Run refresh in background thread
            refresh_thread_obj = threading.Thread(target=refresh_thread, daemon=True)
            refresh_thread_obj.start()
            
        except Exception as e:
            print(f"❌ Error during refresh: {e}")
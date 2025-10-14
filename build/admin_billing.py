# adminbilling.py - Admin Billing/Payment Manager for Cashiers
from pathlib import Path
from tkinter import Canvas, Frame, Label, Button, Entry, messagebox, Scrollbar, Toplevel
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG

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

class AdminBillingManager:
    def __init__(self, parent, get_db_connection=None, user_data=None):
        self.parent = parent
        self.get_db_connection = get_db_connection
        self.user_data = user_data or {}
        
        # Payment data
        self.payments = []
        self.filtered_payments = []
        self.search_query = ""
        self.current_page = 1
        self.payments_per_page = 9
        
        # UI element storage
        self.images = []
        self.row_widgets = []
        
        self.setup_ui()
        self.load_payments()
        self.update_display()
        
    def setup_ui(self):
        """Setup the billing/payment management UI inside the parent frame"""
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
        
        # Create search bar (top right)
        self.create_searchbar()
        
        # Create title label (top left)
        self.create_title_label()
        
        # Create table header
        self.create_table_headers()
        
        # Create navigation controls
        self.create_navigation_controls()
        
    def create_searchbar(self):
        """Create a search entry at the top right"""
        # Search entry positioned at the top right
        self.search_entry = Entry(
            self.parent,
            bd=1,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=1,
            font=("Inter", 12)
        )
        # Place at the top right
        self.search_entry.place(x=525, y=18, width=350, height=30)
        self.search_entry.insert(0, "Search payments...")
        # Simple placeholder behavior
        def _on_focus_in(event):
            if self.search_entry.get() == "Search payments...":
                self.search_entry.delete(0, "end")
        def _on_focus_out(event):
            if not self.search_entry.get().strip():
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, "Search payments...")
        self.search_entry.bind("<FocusIn>", _on_focus_in)
        self.search_entry.bind("<FocusOut>", _on_focus_out)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def create_title_label(self):
        """Create a title label in the top left"""
        self.title_label = Label(
            self.parent,
            text="Billing Management",
            font=("Inter", 18, "bold"),
            bg="#FFFFFF",
            fg="#792D1B"
        )
        self.title_label.place(x=20, y=15)

    def create_table_headers(self):
        """Create table header labels for payments"""
        headers = [
            (40.0, "No.", "center"),
            (170.0, "Reference Number", "center"),
            (330.0, "Student", "center"),
            (480.0, "Amount", "center"),
            (570.0, "Method", "center"),
            (670.0, "Status", "center"),
            (790.0, "Actions", "center")
        ]
        
        # Header background - dark brown like in the image
        self.canvas.create_rectangle(20, 60, 875, 100, fill="#792D1B", outline="")
        
        for x, text, anchor in headers:
            self.canvas.create_text(
                x, 80, 
                anchor=anchor, 
                text=text, 
                fill="#FFFFFF", 
                font=("Inter", 11, "bold")
            )

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

    def load_payments(self):
        """Load payments from database with related request and student info"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    p.payment_id,
                    p.request_id,
                    p.amount,
                    p.payment_method,
                    p.reference_number,
                    p.gateway_transaction_id,
                    p.status,
                    p.gateway_response,
                    p.paid_at,
                    p.created_at,
                    p.updated_at,
                    dr.request_number,
                    CONCAT(s.first_name, ' ', s.last_name) as student_name,
                    s.student_number,
                    dt.name as document_name,
                    dt.code as document_code
                FROM payments p
                JOIN document_requests dr ON p.request_id = dr.request_id
                JOIN students s ON dr.student_id = s.student_id
                JOIN document_types dt ON dr.document_type_id = dt.document_type_id
                ORDER BY p.created_at DESC
            """)
            
            self.payments = cursor.fetchall()
            # Default filtered list is full list
            self.filtered_payments = list(self.payments)
            
            cursor.close()
            connection.close()
            
            print(f"✅ Loaded {len(self.payments)} payments from database")
            
        except Error as e:
            print(f"❌ Error loading payments: {e}")
            messagebox.showerror("Database Error", f"Failed to load payments: {str(e)}")
            self.payments = []

    def update_display(self):
        """Update the display with current page data"""
        self.clear_table_rows()
        
        if not self.filtered_payments:
            self.show_no_payments_message()
            return
            
        self.display_current_payments()
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

    def display_current_payments(self):
        """Display payments for current page"""
        start_idx = (self.current_page - 1) * self.payments_per_page
        end_idx = start_idx + self.payments_per_page
        current_payments = self.filtered_payments[start_idx:end_idx]
        
        for i, payment in enumerate(current_payments):
            self.create_table_row(i, payment)

    def on_search_change(self, event=None):
        """Handle search text changes and filter the list"""
        query = self.search_entry.get().strip()
        # Ignore placeholder
        if query == "Search payments...":
            query = ""
        self.search_query = query.lower()
        self.apply_search_filter()

    def apply_search_filter(self):
        """Filter payments into filtered_payments based on search_query"""
        if not self.search_query:
            self.filtered_payments = list(self.payments)
        else:
            q = self.search_query
            def matches(payment):
                values = [
                    str(payment.get('reference_number', '')),
                    str(payment.get('student_name', '')),
                    str(payment.get('student_number', '')),
                    str(payment.get('amount', '')),
                    str(payment.get('payment_method', '')),
                    str(payment.get('status', '')),
                    str(payment.get('payment_id', '')),
                    str(payment.get('request_number', '')),
                    str(payment.get('document_name', '')),
                ]
                text = " ".join(values).lower()
                return q in text
            self.filtered_payments = [p for p in self.payments if matches(p)]
        # Reset to first page after filtering
        self.current_page = 1
        self.update_display()

    def create_table_row(self, row_index, payment):
        """Create a table row with data and action buttons"""
        y_position = 110 + (row_index * 45)
        
        # Row background (alternating colors)
        fill_color = "#FFFFFF" if row_index % 2 == 0 else "#F8F8F8"
        self.canvas.create_rectangle(
            20, y_position, 875, y_position + 40, 
            fill=fill_color, outline="#E0E0E0", tags="row"
        )
        
        # Calculate row number (global index)
        row_number = ((self.current_page - 1) * self.payments_per_page) + row_index + 1
        
        # Format amount
        amount_text = f"₱{payment['amount']:.2f}"
        
        # Status display with color coding
        status_text = payment['status'].title()
        
        # Create text elements for the row with proper alignment
        text_configs = [
            (40.0, str(row_number), "center"),
            (170.0, payment['reference_number'] or "N/A", "center"),
            (340.0, payment['student_name'][:15] + "..." if len(payment['student_name']) > 15 else payment['student_name'], "center"),
            (480.0, amount_text, "center"),
            (570.0, payment['payment_method'].title(), "center"),
            (670.0, status_text, "center")
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
        self.create_row_buttons(row_index, payment, y_position)

    def create_row_buttons(self, row_index, payment, y_position):
        """Create action buttons for each row"""
        button_widgets = []
        
        status = payment['status']
        
        # View Details button - always available
        view_button = Button(
            self.parent,
            text="View",
            font=("Inter", 9),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=lambda p=payment: self.view_payment_details(p)
        )
        view_button.place(x=740, y=y_position + 8, width=50, height=25)
        button_widgets.append(view_button)
        
        # Status-specific action buttons
        if status == 'pending':
            # Approve payment button
            approve_button = Button(
                self.parent,
                text="Approve",
                font=("Inter", 9),
                bg="#28a745",
                fg="#FFFFFF",
                relief="flat",
                command=lambda p=payment: self.approve_payment(p)
            )
            approve_button.place(x=800, y=y_position + 8, width=60, height=25)
            button_widgets.append(approve_button)
            
        elif status == 'success':
            # Refund button
            refund_button = Button(
                self.parent,
                text="Refund",
                font=("Inter", 9),
                bg="#dc3545",
                fg="#FFFFFF",
                relief="flat",
                command=lambda p=payment: self.refund_payment(p)
            )
            refund_button.place(x=800, y=y_position + 8, width=60, height=25)
            button_widgets.append(refund_button)
            
        else:
            # Disabled button for other statuses
            disabled_button = Button(
                self.parent,
                text="N/A",
                font=("Inter", 9),
                bg="#CCCCCC",
                fg="#666666",
                relief="flat",
                state="disabled"
            )
            disabled_button.place(x=800, y=y_position + 8, width=60, height=25)
            button_widgets.append(disabled_button)
        
        self.row_widgets.append(button_widgets)

    def view_payment_details(self, payment):
        """Open payment details dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Payment Details - {payment['reference_number'] or 'No Reference'}")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Payment details
        details_frame = Frame(dialog, bg="#FFFFFF")
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = Label(details_frame, text="Payment Details", 
                           font=("Inter", 16, "bold"), bg="#FFFFFF", fg="#792D1B")
        title_label.pack(pady=(0, 20))
        
        # Payment information
        info_labels = [
            ("Payment ID:", str(payment['payment_id'])),
            ("Request Number:", payment['request_number']),
            ("Student:", payment['student_name']),
            ("Student Number:", payment['student_number']),
            ("Document:", f"{payment['document_code']} - {payment['document_name']}"),
            ("Amount:", f"₱{payment['amount']:.2f}"),
            ("Payment Method:", payment['payment_method'].title()),
            ("Status:", payment['status'].title()),
            ("Reference Number:", payment['reference_number'] or "N/A"),
            ("Gateway Transaction ID:", payment['gateway_transaction_id'] or "N/A"),
            ("Created At:", payment['created_at'].strftime('%Y-%m-%d %H:%M:%S') if payment['created_at'] else "N/A"),
            ("Paid At:", payment['paid_at'].strftime('%Y-%m-%d %H:%M:%S') if payment['paid_at'] else "N/A"),
        ]
        
        for label_text, value_text in info_labels:
            frame = Frame(details_frame, bg="#FFFFFF")
            frame.pack(fill="x", pady=5)
            
            label = Label(frame, text=label_text, font=("Inter", 10, "bold"), 
                         bg="#FFFFFF", fg="#333333", width=20, anchor="w")
            label.pack(side="left")
            
            value = Label(frame, text=value_text, font=("Inter", 10), 
                         bg="#FFFFFF", fg="#666666", anchor="w")
            value.pack(side="left", padx=(10, 0))
        
        # Close button
        Button(dialog, text="Close", font=("Inter", 10, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=dialog.destroy).pack(pady=20)

    def approve_payment(self, payment):
        """Approve a pending payment"""
        if messagebox.askyesno("Approve Payment", 
                             f"Approve payment with reference {payment['reference_number'] or 'N/A'}?\n"
                             f"Student: {payment['student_name']}\n"
                             f"Amount: ₱{payment['amount']:.2f}"):
            
            try:
                connection = self.get_db_connection()
                if not connection:
                    messagebox.showerror("Database Error", "Could not connect to database")
                    return
                    
                cursor = connection.cursor()
                
                # Update payment status
                cursor.execute("""
                    UPDATE payments 
                    SET status = 'success', paid_at = %s, updated_at = %s
                    WHERE payment_id = %s
                """, (datetime.now(), datetime.now(), payment['payment_id']))
                
                # Update document request payment status
                cursor.execute("""
                    UPDATE document_requests 
                    SET payment_status = 'paid', payment_date = %s
                    WHERE request_id = %s
                """, (datetime.now(), payment['request_id']))
                
                connection.commit()
                cursor.close()
                connection.close()
                
                print(f"✅ Payment {payment['reference_number'] or payment['payment_id']} approved successfully")
                messagebox.showinfo("Success", f"Payment {payment['reference_number'] or payment['payment_id']} approved successfully")
                
                # Refresh the display
                self.load_payments()
                self.update_display()
                
            except Error as e:
                print(f"❌ Error approving payment: {e}")
                messagebox.showerror("Database Error", f"Failed to approve payment: {str(e)}")

    def refund_payment(self, payment):
        """Refund a successful payment"""
        if messagebox.askyesno("Refund Payment", 
                             f"Refund payment with reference {payment['reference_number'] or 'N/A'}?\n"
                             f"Student: {payment['student_name']}\n"
                             f"Amount: ₱{payment['amount']:.2f}\n\n"
                             f"This action cannot be undone."):
            
            try:
                connection = self.get_db_connection()
                if not connection:
                    messagebox.showerror("Database Error", "Could not connect to database")
                    return
                    
                cursor = connection.cursor()
                
                # Update payment status
                cursor.execute("""
                    UPDATE payments 
                    SET status = 'refunded', updated_at = %s
                    WHERE payment_id = %s
                """, (datetime.now(), payment['payment_id']))
                
                # Update document request payment status
                cursor.execute("""
                    UPDATE document_requests 
                    SET payment_status = 'refunded'
                    WHERE request_id = %s
                """, (payment['request_id'],))
                
                connection.commit()
                cursor.close()
                connection.close()
                
                print(f"✅ Payment {payment['reference_number'] or payment['payment_id']} refunded successfully")
                messagebox.showinfo("Success", f"Payment {payment['reference_number'] or payment['payment_id']} refunded successfully")
                
                # Refresh the display
                self.load_payments()
                self.update_display()
                
            except Error as e:
                print(f"❌ Error refunding payment: {e}")
                messagebox.showerror("Database Error", f"Failed to refund payment: {str(e)}")

    def show_no_payments_message(self):
        """Show message when no payments exist"""
        self.canvas.create_text(
            450, 200, anchor="center", text="No payments found",
            fill="#666666", font=("Inter", 14, "bold"), tags="row"
        )

    def update_navigation(self):
        """Update navigation elements"""
        total_pages = max(1, (len(self.filtered_payments) + self.payments_per_page - 1) // self.payments_per_page)
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
        total_pages = max(1, (len(self.filtered_payments) + self.payments_per_page - 1) // self.payments_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()

    def refresh_payments(self):
        """Refresh the payments list"""
        print("🔄 Refreshing payments...")
        try:
            self.load_payments()
            self.current_page = 1
            self.update_display()
            print(f"✅ Refresh complete - {len(self.payments)} payments loaded")
        except Exception as e:
            print(f"❌ Error during refresh: {e}")

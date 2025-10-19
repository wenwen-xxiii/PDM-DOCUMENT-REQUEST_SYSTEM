
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox, StringVar, Toplevel
from tkinter import ttk
import mysql.connector
from datetime import datetime, timedelta
import sys
import os
import asyncio
import threading

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing modules
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
    return Path(resource_path(f"resources/assets/requestform/{path}"))

class DocumentRequestWindow:
    def __init__(self, parent, student_id, show_dashboard_callback):
        self.parent = parent
        self.student_id = student_id
        self.show_dashboard_callback = show_dashboard_callback
        self.document_types = []
        self.selected_document_type = None
        self.delivery_mode = "pickup"  # Default delivery mode
        
        # Store all image references to prevent garbage collection
        self.images = []
        
        self.setup_ui()
        self.load_document_types()
        self.setup_bindings()
        
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        width = 508
        height = 670
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_ui(self):
        # Use Toplevel instead of Tk for child windows
        self.window = Toplevel(self.parent)
        self.window.geometry("508x670")
        self.window.configure(bg="#FCECB7")
        self.window.title("Document Request - PDM")
        self.window.resizable(False, False)
        
        # Center the window on screen
        self.center_window()
        self.window.transient(self.parent)  # Set as transient to main window
        self.window.grab_set()  # Make it modal

        self.canvas = Canvas(
            self.window,
            bg="#FCECB7",
            height=670,
            width=508,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        
        # UI elements from the designer
        self.create_ui_elements()
        
    def create_ui_elements(self):
        # Header
        self.canvas.create_rectangle(0.0, 0.0, 508.0, 57.0, fill="#792D1B", outline="")
        self.canvas.create_rectangle(0.0, 57.0, 508.0, 99.0, fill="#FFDA0C", outline="")
        
        self.canvas.create_rectangle(
            0.0, 0.0, 508.0, 57.0,
            fill="#792D1B",
            outline=""
        )


        
        # Form container
        self.canvas.create_rectangle(19.0, 122.0, 483.0, 604.0, fill="#FFFFFF", outline="")
        
        # Labels
        self.canvas.create_text(45.0, 472.0, anchor="nw", text="Purpose", fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(45.0, 386.0, anchor="nw", text="Delivery Type", fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(271.0, 218.0, anchor="nw", text="Price per copy", fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(271.0, 302.0, anchor="nw", text="Date of Releasing", fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(45.0, 302.0, anchor="nw", text="Total to Pay", fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(46.0, 218.0, anchor="nw", text="Quantity", fill="#1E1E1E", font=("Inter", 16 * -1))
        self.canvas.create_text(45.0, 134.0, anchor="nw", text="Type of Document", fill="#1E1E1E", font=("Inter", 16 * -1))

        # Document Type Dropdown - Borderless with custom styling
        self.entry_image_5 = PhotoImage(file=relative_to_assets("entry_docType.png"))
        self.images.append(self.entry_image_5)  # Store reference
        self.canvas.create_image(255.5, 182.5, image=self.entry_image_5)
        
        self.doc_type_var = StringVar()
        
        # Create custom style for borderless combobox
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Borderless.TCombobox',
                        fieldbackground='#FFF1C2',
                        background='#FFF1C2',
                        foreground='#000716',
                        borderwidth=0,
                        focuscolor='none',
                        padding=10)
        style.map('Borderless.TCombobox',
                 fieldbackground=[('readonly', '#FFF1C2')],
                 background=[('readonly', '#FFF1C2')],
                 selectbackground=[('readonly', '#FFF1C2')],
                 selectforeground=[('readonly', '#000716')])
        
        self.combobox_docType = ttk.Combobox(
            self.window,
            textvariable=self.doc_type_var,
            state="readonly",
            font=("Inter", 12),
            style='Borderless.TCombobox'
        )
        self.combobox_docType.place(x=53.0, y=165.0, width=405.0, height=37.0)
        
        # Delivery Type Dropdown - Borderless with custom styling
        self.entry_image_6 = PhotoImage(file=relative_to_assets("entry_deliveryType.png"))
        self.images.append(self.entry_image_6)  # Store reference
        self.canvas.create_image(256.0, 434.0, image=self.entry_image_6)
        
        self.delivery_var = StringVar()
        self.combobox_deliveryType = ttk.Combobox(
            self.window,
            textvariable=self.delivery_var,
            state="readonly",
            font=("Inter", 12),
            style='Borderless.TCombobox',
            values=["Pickup", "Online Delivery"]
        )
        self.combobox_deliveryType.place(x=54.0, y=416.0, width=404.0, height=38.0)
        self.combobox_deliveryType.set("Pickup")  # Default value

        # Quantity Entry with increment/decrement buttons
        self.entry_image_3 = PhotoImage(file=relative_to_assets("entry_quantity.png"))
        self.images.append(self.entry_image_3)  # Store reference
        self.canvas.create_image(143.5, 266.0, image=self.entry_image_3)
        
        self.quantity_var = StringVar(value="1")
        self.entry_quantity = Entry(
            self.window,
            textvariable=self.quantity_var,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            justify="center",
            readonlybackground="#FFF1C2"
        )
        self.entry_quantity.place(x=54.0, y=248.0, width=179.0, height=38.0)
        self.entry_quantity.config(state='readonly')  # Make it readonly

        # Quantity buttons
        self.button_image_1 = PhotoImage(file=relative_to_assets("button_numeridown_quantity.png"))
        self.images.append(self.button_image_1)  # Store reference
        self.button_numeridown_quantity = Button(
            self.window,
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.decrement_quantity,
            relief="flat"
        )
        self.button_numeridown_quantity.place(x=208.0, y=266.5, width=18.0, height=15.0)

        self.button_image_3 = PhotoImage(file=relative_to_assets("button_numericup_quantity.png"))
        self.images.append(self.button_image_3)  # Store reference
        self.button_numericup_quantity = Button(
            self.window,
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.increment_quantity,
            relief="flat"
        )
        self.button_numericup_quantity.place(x=208.0, y=251.0, width=18.0, height=15.0)

        # Price per copy (readonly) - Centered text
        self.entry_image_1 = PhotoImage(file=relative_to_assets("entry_price_per_copy.png"))
        self.images.append(self.entry_image_1)  # Store reference
        self.canvas.create_image(368.5, 267.0, image=self.entry_image_1)
        
        self.price_var = StringVar(value="₱0.00")
        self.entry_price_per_copy = Entry(
            self.window,
            textvariable=self.price_var,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            state="readonly",
            justify="center",
            readonlybackground="#FFF1C2"
        )
        self.entry_price_per_copy.place(x=279.0, y=249.0, width=179.0, height=38.0)

        # Total to Pay (readonly) - Centered text
        self.entry_image_4 = PhotoImage(file=relative_to_assets("entry_total.png"))
        self.images.append(self.entry_image_4)  # Store reference
        self.canvas.create_image(143.5, 350.0, image=self.entry_image_4)
        
        self.total_var = StringVar(value="₱0.00")
        self.entry_total = Entry(
            self.window,
            textvariable=self.total_var,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            state="readonly",
            justify="center",
            readonlybackground="#FFF1C2"
        )
        self.entry_total.place(x=54.0, y=332.0, width=179.0, height=38.0)

        # Releasing Date - Centered text
        self.entry_image_2 = PhotoImage(file=relative_to_assets("entry_releasingDate.png"))
        self.images.append(self.entry_image_2)  # Store reference
        self.canvas.create_image(368.5, 351.0, image=self.entry_image_2)
        
        # Calculate default releasing date (3 business days from now)
        default_date = self.calculate_releasing_date()
        self.releasing_date_var = StringVar(value=default_date)
        self.entry_releasingDate = Entry(
            self.window,
            textvariable=self.releasing_date_var,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            justify="center",
            readonlybackground="#FFF1C2",
            state="readonly"
        )
        self.entry_releasingDate.place(x=279.0, y=333.0, width=179.0, height=38.0)

        # Purpose Text area
        self.entry_image_7 = PhotoImage(file=relative_to_assets("entry_purpose.png"))
        self.images.append(self.entry_image_7)  # Store reference
        self.canvas.create_image(256.0, 540.0, image=self.entry_image_7)
        
        self.text_purpose = Text(
            self.window,
            bd=0,
            bg="#FFF1C2",
            fg="#000716",
            highlightthickness=0,
            font=("Inter", 12),
            wrap="word"
        )
        self.text_purpose.place(x=54.0, y=502.0, width=404.0, height=78.0)

        # Buttons
        self.button_image_2 = PhotoImage(file=relative_to_assets("button_back.png"))
        self.images.append(self.button_image_2)  # Store reference
        self.button_back = Button(
            self.window,
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.go_back,
            relief="flat"
        )
        self.button_back.place(x=27.0, y=19.0, width=15.0, height=18.0)

        self.button_image_5 = PhotoImage(file=relative_to_assets("button_submit.png"))
        self.images.append(self.button_image_5)  # Store reference
        self.button_submit = Button(
            self.window,
            image=self.button_image_5,
            borderwidth=0,
            highlightthickness=0,
            command=self.submit_request,
            relief="flat"
        )
        self.button_submit.place(x=389.0, y=615.0, width=94.0, height=40.0)

        # Add title text
        self.canvas.create_text(
            254.0, 28.0, anchor="center",
            text="Document Request Form",
            fill="#FFFFFF",
            font=("Inter", 16, "bold")
        )

    def setup_bindings(self):
        """Setup event bindings"""
        self.combobox_docType.bind('<<ComboboxSelected>>', self.on_document_type_selected)
        self.combobox_deliveryType.bind('<<ComboboxSelected>>', self.on_delivery_type_selected)
        self.quantity_var.trace('w', self.calculate_total)
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self.go_back)

    async def load_document_types_async(self):
        """Load available document types from database (async version)"""
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT document_type_id, code, name, fee_amount, processing_days 
                FROM document_types 
                WHERE is_available = TRUE
                ORDER BY name
            """)
            
            self.document_types = cursor.fetchall()
            
            # Populate combobox
            doc_names = [f"{doc['code']} - {doc['name']} (₱{doc['fee_amount']:.2f})" for doc in self.document_types]
            self.combobox_docType['values'] = doc_names
            
            if self.document_types:
                self.combobox_docType.current(0)  # Select first item by default
                self.on_document_type_selected(None)  # Trigger calculation
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to load document types: {str(e)}")
            # Add default values if database fails
            self.combobox_docType['values'] = ["COE - Certificate of Enrollment (₱100.00)"]

    def load_document_types(self):
        """Load available document types from database (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, run in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.load_document_types_async())
                    return future.result()
            else:
                return loop.run_until_complete(self.load_document_types_async())
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self.load_document_types_async())

    def on_document_type_selected(self, event):
        """Handle document type selection"""
        selected_index = self.combobox_docType.current()
        if selected_index >= 0 and selected_index < len(self.document_types):
            self.selected_document_type = self.document_types[selected_index]
            self.price_var.set(f"₱{self.selected_document_type['fee_amount']:.2f}")
            self.calculate_total()
            
            # Update releasing date based on processing days
            processing_days = self.selected_document_type['processing_days']
            new_date = self.calculate_releasing_date(processing_days)
            self.releasing_date_var.set(new_date)

    def on_delivery_type_selected(self, event):
        """Handle delivery type selection"""
        delivery_type = self.combobox_deliveryType.get()
        self.delivery_mode = "online" if "Online" in delivery_type else "pickup"

    def increment_quantity(self):
        """Increase quantity by 1"""
        try:
            current = int(self.quantity_var.get())
            if current < 10:  # Maximum 10 copies
                self.quantity_var.set(str(current + 1))
        except ValueError:
            self.quantity_var.set("1")

    def decrement_quantity(self):
        """Decrease quantity by 1"""
        try:
            current = int(self.quantity_var.get())
            if current > 1:  # Minimum 1 copy
                self.quantity_var.set(str(current - 1))
        except ValueError:
            self.quantity_var.set("1")

    def calculate_total(self, *args):
        """Calculate total amount to pay"""
        try:
            if self.selected_document_type:
                quantity = int(self.quantity_var.get())
                price = float(self.selected_document_type['fee_amount'])
                total = quantity * price
                self.total_var.set(f"₱{total:.2f}")
            else:
                self.total_var.set("₱0.00")
        except ValueError:
            self.total_var.set("₱0.00")

    def calculate_releasing_date(self, processing_days=3):
        """Calculate estimated releasing date (skip weekends)"""
        today = datetime.now()
        days_added = 0
        current_date = today
        
        while days_added < processing_days:
            current_date += timedelta(days=1)
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                days_added += 1
        
        return current_date.strftime("%B %d, %Y")  # More readable format

    def generate_request_number(self, connection):
        """Generate unique request number"""
        cursor = connection.cursor()
        
        today = datetime.now()
        year = today.strftime("%Y")
        month_day = today.strftime("%m%d")
        
        # Get or create sequence for today
        cursor.execute("""
            INSERT INTO request_sequences (sequence_date, last_number) 
            VALUES (CURDATE(), 1)
            ON DUPLICATE KEY UPDATE last_number = last_number + 1
        """)
        
        # Get the current sequence number
        cursor.execute("""
            SELECT last_number FROM request_sequences 
            WHERE sequence_date = CURDATE()
        """)
        result = cursor.fetchone()
        daily_count = result[0] if result else 1
        
        # Format: PDM-YYYY-MMDD-XXX
        return f"PDM-{year}-{month_day}-{daily_count:03d}"

    def validate_form(self):
        """Validate all form fields"""
        errors = []
        
        if not self.selected_document_type:
            errors.append("Please select a document type")
        
        purpose_text = self.text_purpose.get("1.0", "end-1c").strip()
        if not purpose_text:
            errors.append("Please specify the purpose of the request")
        elif len(purpose_text) < 10:
            errors.append("Please provide a more detailed purpose (at least 10 characters)")
        
        try:
            quantity = int(self.quantity_var.get())
            if quantity < 1 or quantity > 10:
                errors.append("Quantity must be between 1 and 10")
        except ValueError:
            errors.append("Invalid quantity value")
        
        return errors

    async def submit_request_async(self):
        """Submit the document request (async version)"""
        # Validate form
        errors = self.validate_form()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            # Generate request number
            request_number = self.generate_request_number(connection)
            
            # Calculate total amount
            quantity = int(self.quantity_var.get())
            total_amount = float(self.selected_document_type['fee_amount']) * quantity
            
            # Insert document request
            cursor.execute("""
                INSERT INTO document_requests (
                    request_number, student_id, document_type_id, purpose_details,
                    quantity, delivery_mode, request_release_date,
                    total_amount, status, payment_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request_number,
                self.student_id,
                self.selected_document_type['document_type_id'],
                self.text_purpose.get("1.0", "end-1c").strip(),
                quantity,
                self.delivery_mode,
                datetime.strptime(self.releasing_date_var.get(), "%B %d, %Y").strftime("%Y-%m-%d"),
                total_amount,
                'payment_pending',
                'pending'
            ))
            
            # Get the inserted request ID
            request_id = cursor.lastrowid
            
            # Get user_id for the student to create notification
            cursor.execute("""
                SELECT user_id FROM students WHERE student_id = %s
            """, (self.student_id,))
            
            student_result = cursor.fetchone()
            
            if student_result and student_result.get('user_id'):
                # Create notification for the student
                cursor.execute("""
                    INSERT INTO notifications (
                        user_id, title, message, notification_type, related_request_id
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    student_result['user_id'],
                    "Document Request Submitted",
                    f"Your request for {self.selected_document_type['name']} has been submitted successfully. Request #: {request_number}",
                    "success",
                    request_id
                ))
                print(f"✓ Notification created for user_id: {student_result['user_id']}")
            else:
                print(f"⚠️ Warning: No user_id found for student_id: {self.student_id}")
                # Continue without notification rather than failing the entire request
            
            connection.commit()
            
            # Show success message
            self.show_success_message(request_number, quantity)
            
            # Return to dashboard
            self.go_back()
                
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to submit request: {str(e)}")
            if connection and connection.is_connected():
                connection.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            # Print detailed error for debugging
            import traceback
            print(f"Detailed error: {traceback.format_exc()}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def submit_request(self):
        """Submit the document request (sync wrapper)"""
        # Use threading to avoid blocking UI
        def submit_thread():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, run in thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.submit_request_async())
                        return future.result()
                else:
                    return loop.run_until_complete(self.submit_request_async())
            except RuntimeError:
                # No event loop running, create a new one
                return asyncio.run(self.submit_request_async())
        
        # Run submit in background thread
        submit_thread_obj = threading.Thread(target=submit_thread, daemon=True)
        submit_thread_obj.start()

    def show_success_message(self, request_number, quantity):
        """Show success message with request details"""
        messagebox.showinfo(
            "Request Submitted Successfully!", 
            f"✅ Your document request has been submitted!\n\n"
            f"📋 Request Number: {request_number}\n"
            f"📄 Document: {self.selected_document_type['name']}\n"
            f"🔢 Quantity: {quantity}\n"
            f"💰 Total Amount: {self.total_var.get()}\n"
            f"🚚 Delivery: {self.combobox_deliveryType.get()}\n"
            f"📅 Expected Release: {self.releasing_date_var.get()}\n\n"
            f"You can now proceed to payment from your dashboard."
        )

    def go_back(self):
        """Return to dashboard"""
        self.window.destroy()
        if hasattr(self, 'show_dashboard_callback') and self.show_dashboard_callback:
            self.show_dashboard_callback()

    def run(self):
        """Run the application"""
        # No need for mainloop since it's a Toplevel window
        # The window will be managed by the parent
        pass
    

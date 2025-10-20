from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox, StringVar, Frame
import mysql.connector
import aiomysql
import asyncio
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing modules
from config import DB_CONFIG
from requestform import DocumentRequestWindow
from payment_window import PaymentWindow
from view_docu_attachment import DocumentAttachmentViewer

class DocumentWindow:
    def __init__(self, parent, user_data=None, user_type=None, get_db_connection=None, navigation_callbacks=None):
        self.parent = parent
        self.user_data = user_data or {}
        self.user_type = user_type
        self.get_db_connection = get_db_connection
        self.navigation_callbacks = navigation_callbacks or {}
        
        self.student_id = self._get_student_id()
        self.current_page = 1
        self.requests_per_page = 4
        self.document_requests = []
        
        # UI element storage
        self.images = []
        self.card_images = []
        self.card_canvas_ids = []
        self.entry_bg_ids = []
        
        self._setup_ui()
        self.load_document_requests()
        self.update_display()

    async def get_async_db_connection(self):
        """Get async database connection"""
        try:
            connection = await aiomysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                db=DB_CONFIG['database'],
                port=DB_CONFIG['port']
            )
            return connection
        except Exception as e:
            print(f"Async database connection failed: {e}")
            return None

    def _get_student_id(self):
        """Get student_id from user_data - FIXED VERSION"""
        print(f"🔍 DEBUG: Getting student_id from user_data: {self.user_data}")
        
        # Method 1: Try to get student_id directly from user_data
        student_id = self.user_data.get('student_id')
        if student_id:
            print(f"✅ Found student_id from user_data['student_id']: {student_id}")
            return student_id
        
        # Method 2: Try to get from user_id lookup
        user_id = self.user_data.get('user_id')
        if user_id:
            print(f"🔍 Looking up student_id from user_id: {user_id}")
            looked_up_id = self._get_student_id_from_user_id(user_id)
            if looked_up_id:
                print(f"✅ Found student_id from user_id lookup: {looked_up_id}")
                return looked_up_id
        
        # Method 3: Try to get from student_number lookup
        student_number = self.user_data.get('student_number')
        if student_number:
            print(f"🔍 Looking up student_id from student_number: {student_number}")
            looked_up_id = self._get_student_id_from_number(student_number)
            if looked_up_id:
                print(f"✅ Found student_id from student_number lookup: {looked_up_id}")
                return looked_up_id
        
        print(f"❌ ERROR: Could not find student_id in user_data: {self.user_data}")
        return None

    async def _get_student_id_from_user_id_async(self, user_id):
        """Get student_id from user_id asynchronously"""
        try:
            db_connection = await self.get_async_db_connection()
            if db_connection:
                cursor = await db_connection.cursor()
                await cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (user_id,))
                result = await cursor.fetchone()
                await cursor.close()
                await db_connection.ensure_closed()
                
                if result:
                    student_id = result[0]
                    print(f"✅ Database lookup successful: user_id {user_id} -> student_id {student_id}")
                    return student_id
                else:
                    print(f"❌ No student found with user_id: {user_id}")
            else:
                print("❌ No database connection available")
        except Exception as e:
            print(f"❌ Error getting student_id from user_id: {e}")
        return None

    def _get_student_id_from_user_id(self, user_id):
        """Get student_id from user_id - OPTIMIZED FOR SPEED"""
        try:
            # Use synchronous database connection for speed
            db_connection = self.get_db_connection()
            if db_connection:
                cursor = db_connection.cursor()
                cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                cursor.close()
                db_connection.close()
                
                if result:
                    student_id = result[0]
                    print(f"✅ Database lookup successful: user_id {user_id} -> student_id {student_id}")
                    return student_id
                else:
                    print(f"❌ No student found with user_id: {user_id}")
            else:
                print("❌ No database connection available")
        except Exception as e:
            print(f"❌ Error getting student_id from user_id: {e}")
        return None

    async def _get_student_id_from_number_async(self, student_number):
        """Get student_id from student_number asynchronously"""
        try:
            db_connection = await self.get_async_db_connection()
            if db_connection:
                cursor = await db_connection.cursor()
                await cursor.execute("SELECT student_id FROM students WHERE student_number = %s", (student_number,))
                result = await cursor.fetchone()
                await cursor.close()
                await db_connection.ensure_closed()
                
                if result:
                    student_id = result[0]
                    print(f"✅ Database lookup successful: {student_number} -> {student_id}")
                    return student_id
                else:
                    print(f"❌ No student found with number: {student_number}")
            else:
                print("❌ No database connection available")
        except Exception as e:
            print(f"❌ Error getting student_id from number: {e}")
        return None

    def _get_student_id_from_number(self, student_number):
        """Get student_id from student_number - OPTIMIZED FOR SPEED"""
        try:
            # Use synchronous database connection for speed
            db_connection = self.get_db_connection()
            if db_connection:
                cursor = db_connection.cursor()
                cursor.execute("SELECT student_id FROM students WHERE student_number = %s", (student_number,))
                result = cursor.fetchone()
                cursor.close()
                db_connection.close()
                
                if result:
                    student_id = result[0]
                    print(f"✅ Database lookup successful: {student_number} -> {student_id}")
                    return student_id
                else:
                    print(f"❌ No student found with number: {student_number}")
            else:
                print("❌ No database connection available")
        except Exception as e:
            print(f"❌ Error getting student_id from number: {e}")
        return None

    def _setup_ui(self):
        """Setup the document content only"""
        self.main_frame = Frame(self.parent, bg="#FCECB7")
        self.main_frame.place(x=0, y=140, width=1270, height=650)
        
        self.canvas = Canvas(
            self.main_frame,
            bg="#FCECB7",
            height=650,
            width=1270,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)
        
        self._create_ui_elements()

    def _create_ui_elements(self):
        """Create all UI elements"""
        self._create_background_elements()
        self._create_header()
        self._create_cards_and_entries()
        self._create_buttons()
        self._create_navigation()

    def _create_background_elements(self):
        """Create background elements"""
        self.canvas.create_rectangle(47.0, 24.0, 1222.0, 590.0, fill="#FEFEFE", outline="")

    def _create_header(self):
        """Create header section"""
        header_img = PhotoImage(file=self._relative_to_assets("img_headergrid.png"))
        self.images.append(header_img)
        self.canvas.create_image(635.0, 125.5, image=header_img)

        header_labels = [
            (117.0, "Request Number"),
            (368.0, "Document Name"), 
            (658.0, "Release Date"),
            (797.0, "to Pay"),
            (790.0, "Amount"),
            (895.0, "Type"),
            (882.0, "Delivery"),
            (996.0, "Status"),
            (587.0, "No. of"),
            (591.0, "Days")
        ]
        
        for x, text in header_labels:
            y = 117.0 if "Request" in text or "Document" in text or "Release" in text or "Status" in text else (106.0 if "Amount" in text or "Delivery" in text or "No." in text else 128.0)
            self.canvas.create_text(x, y, anchor="nw", text=text, fill="#FEFEFE", font=("Inter", 16 * -1))

    def _create_cards_and_entries(self):
        """Create card backgrounds and entry fields"""
        # Card backgrounds
        y_centers = [202.5, 295.5, 387.5, 479.5]
        for y in y_centers:
            card_img = PhotoImage(file=self._relative_to_assets("img_card_bg.png"))
            self.images.append(card_img)
            card_id = self.canvas.create_image(635.0, y, image=card_img)
            self.card_canvas_ids.append(card_id)
            self.canvas.itemconfig(card_id, state='hidden')

        # Entry fields configuration
        self.entry_configs = [
            {'y_center': 203.0, 'y_pos': 183.0},
            {'y_center': 295.0, 'y_pos': 275.0}, 
            {'y_center': 387.0, 'y_pos': 367.0},
            {'y_center': 479.0, 'y_pos': 459.0}
        ]
        
        entry_types = [
            {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
            {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
            {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
            {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
            {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
            {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
            {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
        ]
        
        self.entry_fields = []
        for config in self.entry_configs:
            row_entries = {}
            row_bg_ids = []
            
            for entry_type in entry_types:
                # Create entry background
                entry_img = PhotoImage(file=self._relative_to_assets(f"entry_{entry_type['type']}.png"))
                self.images.append(entry_img)
                bg_id = self.canvas.create_image(entry_type['x_center'], config['y_center'], image=entry_img)
                row_bg_ids.append(bg_id)
                
                # Create entry field
                entry = Entry(
                    self.main_frame,
                    bd=0,
                    bg="#FDFDFD",
                    fg="#000716",
                    highlightthickness=0,
                    state="readonly",
                    justify="center",
                    readonlybackground="#FDFDFD"
                )
                entry.place(
                    x=entry_type['x_pos'],
                    y=config['y_pos'],
                    width=entry_type['width'],
                    height=38.0
                )
                
                row_entries[entry_type['type']] = entry
            
            self.entry_fields.append(row_entries)
            self.entry_bg_ids.append(row_bg_ids)

    def _create_buttons(self):
        """Create action buttons"""
        # New Request button
        button_image = PhotoImage(file=self._relative_to_assets("button_new_request.png"))
        self.images.append(button_image)
        self.button_new_request = Button(
            self.main_frame,
            image=button_image,
            borderwidth=0,
            highlightthickness=0,
            command=self.new_request,
            relief="flat"
        )
        self.button_new_request.place(x=1045.0, y=49.0, width=158.0, height=40.0)

        # Payment and View buttons
        self._create_row_buttons()

    def _create_row_buttons(self):
        """Create payment and view buttons for each row"""
        self.payment_buttons = []
        self.view_docu_buttons = []
        
        button_y_positions = [184.0, 276.0, 368.0, 460.0]
        
        button_pay_img = PhotoImage(file=self._relative_to_assets("button_pay.png"))
        self.images.append(button_pay_img)
        
        button_view_docu_img = PhotoImage(file=self._relative_to_assets("button_view_docu.png"))
        self.images.append(button_view_docu_img)
        
        for i, y_pos in enumerate(button_y_positions):
            # Payment button
            pay_button = Button(
                self.main_frame,
                image=button_pay_img,
                borderwidth=0,
                highlightthickness=0,
                command=lambda idx=i: self.make_payment(idx),
                relief="flat"
            )
            pay_button.place(x=1089.0, y=y_pos, width=96.0, height=40.0)
            self.payment_buttons.append(pay_button)
            
            # View document button
            view_button = Button(
                self.main_frame,
                image=button_view_docu_img,
                borderwidth=0,
                highlightthickness=0,
                command=lambda idx=i: self.view_document(idx),
                relief="flat"
            )
            view_button.place(x=1089.0, y=y_pos, width=96.0, height=40.0)
            self.view_docu_buttons.append(view_button)

    def _create_navigation(self):
        """Create page navigation elements"""
        # Previous page button
        prev_img = PhotoImage(file=self._relative_to_assets("button_prev_page.png"))
        self.images.append(prev_img)
        self.button_prev_page = Button(
            self.main_frame,
            image=prev_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.previous_page,
            relief="flat"
        )
        self.button_prev_page.place(x=460.0, y=540.0, width=113.0, height=32.0)

        # Next page button
        next_img = PhotoImage(file=self._relative_to_assets("button_next_page.png"))
        self.images.append(next_img)
        self.button_next_page = Button(
            self.main_frame,
            image=next_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.next_page,
            relief="flat"
        )
        self.button_next_page.place(x=732.0, y=540.0, width=84.0, height=32.0)

        # Page number display
        self.page_var = StringVar(value="1")
        page_bg_img = PhotoImage(file=self._relative_to_assets("entry_pageno.png"))
        self.images.append(page_bg_img)
        self.canvas.create_image(652.5, 558.0, image=page_bg_img)
        
        self.entry_pageno = Entry(
            self.main_frame,
            textvariable=self.page_var,
            bd=0,
            bg="#FEFEFE",
            fg="#000716",
            highlightthickness=0,
            justify="center",
            state="readonly"
        )
        self.entry_pageno.place(x=583.0, y=539.0, width=139.0, height=36.0)
        
    async def load_document_requests_async(self):
        """Load document requests from database asynchronously - FIXED VERSION"""
        try:
            print(f"🔍 DEBUG: Loading document requests for student_id: {self.student_id}")
            
            if not self.student_id:
                print("❌ ERROR: No student_id available")
                self.document_requests = []
                return
                
            db_connection = await self.get_async_db_connection()
            if not db_connection:
                print("❌ ERROR: Could not connect to database")
                self.document_requests = []
                return
                
            cursor = await db_connection.cursor(aiomysql.DictCursor)
            
            # First, let's verify what student_id we're using
            await cursor.execute("SELECT student_id, student_number FROM students WHERE student_id = %s", (self.student_id,))
            student_info = await cursor.fetchone()
            print(f"🔍 DEBUG: Student info from database: {student_info}")
            
            await cursor.execute("""
                SELECT 
                    dr.request_id,
                    dr.request_number,
                    dt.name as document_name,
                    dr.request_release_date,
                    dr.quantity,
                    dr.total_amount,
                    dr.delivery_mode,
                    dr.status,
                    dr.payment_status,
                    dr.payment_intent_id,
                    dr.student_id
                FROM document_requests dr
                JOIN document_types dt ON dr.document_type_id = dt.document_type_id
                WHERE dr.student_id = %s
                ORDER BY dr.request_date DESC
            """, (self.student_id,))
            
            self.document_requests = await cursor.fetchall()
            
            print(f"🔍 DEBUG: Found {len(self.document_requests)} document requests")
            for req in self.document_requests:
                print(f"🔍 DEBUG: Request {req['request_number']} belongs to student_id: {req['student_id']}")
            
            await cursor.close()
            await db_connection.ensure_closed()
            
        except Exception as e:
            print(f"❌ Unexpected error loading document requests: {str(e)}")
            messagebox.showerror("Database Error", f"Failed to load document requests: {str(e)}")
            self.document_requests = []

    def load_document_requests(self):
        """Synchronous wrapper for async document requests loading - FIXED"""
        try:
            # Use threading to avoid asyncio conflicts
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.load_document_requests_async())
                    result_queue.put("success")
                finally:
                    loop.close()
            
            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join(timeout=15)  # Increased timeout to 15 seconds for database operations
            
            if result_queue.empty():
                print(f"❌ Timeout loading document requests")
                self.document_requests = []
        except Exception as e:
            print(f"❌ Error in sync wrapper: {e}")
            self.document_requests = []

    def update_display(self):
        """Update the display with current page data"""
        self._clear_display()
        
        if not self.document_requests:
            self._show_no_records_message()
            return
        
        self._display_current_requests()
        self._update_navigation()

    def _clear_display(self):
        """Clear all display elements"""
        self.canvas.delete("no_records_text")
        
        # Clear entries
        for row in self.entry_fields:
            for entry in row.values():
                entry.config(state="normal")
                entry.delete(0, "end")
                entry.config(state="readonly")
        
        # Hide buttons
        for i in range(len(self.payment_buttons)):
            self.payment_buttons[i].place_forget()
            self.view_docu_buttons[i].place_forget()
        
        # Hide cards and entry backgrounds
        for card_id in self.card_canvas_ids:
            self.canvas.itemconfig(card_id, state='hidden')
        
        for row_bg_ids in self.entry_bg_ids:
            for bg_id in row_bg_ids:
                self.canvas.itemconfig(bg_id, state='hidden')
        
        for row in self.entry_fields:
            for entry_widget in row.values():
                entry_widget.place_forget()

    def _display_current_requests(self):
        """Display requests for current page"""
        start_idx = (self.current_page - 1) * self.requests_per_page
        end_idx = start_idx + self.requests_per_page
        current_requests = self.document_requests[start_idx:end_idx]
        
        for i, request in enumerate(current_requests):
            if i < len(self.entry_fields):
                self._show_row(i)
                self._populate_row_data(i, request)
                self._show_appropriate_button(i, request)

    def _show_row(self, row_index):
        """Show UI elements for a specific row"""
        if row_index < len(self.card_canvas_ids):
            self.canvas.itemconfig(self.card_canvas_ids[row_index], state='normal')
        
        if row_index < len(self.entry_bg_ids):
            for bg_id in self.entry_bg_ids[row_index]:
                self.canvas.itemconfig(bg_id, state='normal')
        
        # Place entry widgets
        config = self.entry_configs[row_index]
        for entry_type in [
            {'type': 'delivery_type', 'x_pos': 883.0, 'width': 64.0},
            {'type': 'requestno', 'x_pos': 93.0, 'width': 180.0},
            {'type': 'docu_type', 'x_pos': 304.0, 'width': 258.0},
            {'type': 'docu_status', 'x_pos': 978.0, 'width': 88.0},
            {'type': 'amount_pay', 'x_pos': 793.0, 'width': 59.0},
            {'type': 'docu_copy', 'x_pos': 593.0, 'width': 33.0},
            {'type': 'release_date', 'x_pos': 657.0, 'width': 105.0}
        ]:
            entry = self.entry_fields[row_index][entry_type['type']]
            entry.place(
                x=entry_type['x_pos'],
                y=config['y_pos'],
                width=entry_type['width'],
                height=38.0
            )

    def _populate_row_data(self, row_index, request):
        """Populate data for a specific row"""
        row = self.entry_fields[row_index]
        delivery_type = "Online" if request['delivery_mode'] == 'online' else "Pickup"
        status = request['status']
        payment_status = request.get('payment_status', 'pending')
        
        # If payment is completed but status hasn't updated, show a different status
        if payment_status == 'paid' and status == 'payment_pending':
            display_status = "Payment Verified"
        else:
            display_status = status.replace('_', ' ').title()
        
        data_mapping = [
            ('requestno', request['request_number']),
            ('docu_type', request['document_name']),
            ('release_date', request['request_release_date'].strftime('%Y-%m-%d') if request['request_release_date'] else "TBD"),
            ('docu_copy', str(request['quantity'])),
            ('amount_pay', f"₱{request['total_amount']:.2f}"),
            ('delivery_type', delivery_type),
            ('docu_status', display_status)
        ]
        
        for field_name, value in data_mapping:
            row[field_name].config(state="normal")
            row[field_name].delete(0, "end")
            row[field_name].insert(0, value)
            row[field_name].config(state="readonly")

    def _show_appropriate_button(self, row_index, request):
        """Show appropriate button based on request status"""
        button_y_positions = [184.0, 276.0, 368.0, 460.0]
        payment_status = request.get('payment_status', 'pending')
        status = request['status']
        
        # Hide both buttons first
        self.payment_buttons[row_index].place_forget()
        self.view_docu_buttons[row_index].place_forget()
        
        # Show payment button ONLY when payment is pending and status allows payment
        if (status == 'payment_pending' and payment_status == 'pending'):
            self.payment_buttons[row_index].config(state="normal")
            self.payment_buttons[row_index].place(x=1089.0, y=button_y_positions[row_index], width=96.0, height=40.0)
        # Show view document button when request is completed
        elif status == 'completed':
            self.view_docu_buttons[row_index].place(x=1089.0, y=button_y_positions[row_index], width=96.0, height=40.0)
        # For processing, and other statuses - show disabled payment button
        elif status in ['processing'] or (payment_status == 'paid' and status == 'payment_pending'):
            self.payment_buttons[row_index].config(state="disabled")
            self.payment_buttons[row_index].place(x=1089.0, y=button_y_positions[row_index], width=96.0, height=40.0)

    def _show_no_records_message(self):
        """Show message when no records exist"""
        self.canvas.create_text(
            635.0,
            300.0,
            text="No document requests found",
            fill="#666666",
            font=("Inter", 16, "bold"),
            anchor="center",
            tags="no_records_text"
        )
        
        self.page_var.set("Page 1 of 1")
        self.button_prev_page.config(state="disabled")
        self.button_next_page.config(state="disabled")

    def _update_navigation(self):
        """Update navigation elements"""
        total_pages = max(1, (len(self.document_requests) + self.requests_per_page - 1) // self.requests_per_page)
        self.page_var.set(f"Page {self.current_page} of {total_pages}")
        
        self.button_prev_page.config(state="normal" if self.current_page > 1 else "disabled")
        self.button_next_page.config(state="normal" if self.current_page < total_pages else "disabled")

    def new_request(self):
        """Open new document request form"""
        if not self.student_id:
            messagebox.showerror("Error", "Student ID not found. Please contact administrator.")
            return
            
        self.request_window = DocumentRequestWindow(
            parent=self.parent,
            student_id=self.student_id,
            show_dashboard_callback=self.refresh_requests
        )
        self.request_window.run()

    async def view_document_async(self, row_index):
        """View document details and attachments asynchronously"""
        start_idx = (self.current_page - 1) * self.requests_per_page
        actual_index = start_idx + row_index
        
        if actual_index < len(self.document_requests):
            request = self.document_requests[actual_index]
            
            # Check if document has attachments
            try:
                db_connection = await self.get_async_db_connection()
                if db_connection:
                    cursor = await db_connection.cursor()
                    await cursor.execute("""
                        SELECT COUNT(*) as attachment_count 
                        FROM document_attachments 
                        WHERE request_id = %s
                    """, (request['request_id'],))
                    
                    result = await cursor.fetchone()
                    attachment_count = result[0] if result else 0
                    await cursor.close()
                    await db_connection.ensure_closed()
                    
                    if attachment_count > 0:
                        # Open attachment viewer
                        DocumentAttachmentViewer(
                            parent=self.parent,
                            request_id=request['request_id'],
                            get_db_connection=self.get_db_connection
                        )
                    else:
                        # Show basic document info if no attachments
                        messagebox.showinfo(
                            "View Document", 
                            f"Document Details:\n\n"
                            f"Request Number: {request['request_number']}\n"
                            f"Document: {request['document_name']}\n"
                            f"Status: {request['status'].title()}\n"
                            f"Release Date: {request['request_release_date'].strftime('%Y-%m-%d')}\n\n"
                            f"No attachments available for this request."
                        )
                else:
                    messagebox.showerror("Error", "Could not connect to database")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to check attachments: {str(e)}")

    def view_document(self, row_index):
        """Synchronous wrapper for async document viewing - FIXED"""
        try:
            # Use threading to avoid asyncio conflicts
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.view_document_async(row_index))
                    result_queue.put("success")
                finally:
                    loop.close()
            
            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join(timeout=15)  # Increased timeout to 15 seconds for database operations
            
            if result_queue.empty():
                messagebox.showerror("Error", "Timeout viewing document")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view document: {str(e)}")

    def make_payment(self, row_index):
        """Process payment for document request"""
        start_idx = (self.current_page - 1) * self.requests_per_page
        actual_index = start_idx + row_index
        
        if actual_index < len(self.document_requests):
            request = self.document_requests[actual_index]
            
            if request.get('payment_status') in ['paid']:
                messagebox.showinfo("Payment Status", f"Payment for request {request['request_number']} is already paid.")
                return
            
            if request['status'] != 'payment_pending':
                messagebox.showinfo("Payment Status", f"Request {request['request_number']} is not in payment pending status.")
                return
            
            payment_window = PaymentWindow(
                parent=self.parent,
                request_data=request,
                student_data=self.user_data,
                refresh_callback=self.refresh_requests
            )

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
        """Refresh the document requests list - FIXED"""
        print("🔄 Refreshing document requests...")
        try:
            # Use threading to avoid asyncio conflicts
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.load_document_requests_async())
                    result_queue.put("success")
                finally:
                    loop.close()
            
            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join(timeout=15)  # Increased timeout to 15 seconds for database operations
            
            if result_queue.empty():
                print(f"❌ Timeout refreshing requests")
                self.document_requests = []
        except Exception as e:
            print(f"❌ Error refreshing requests: {e}")
            self.document_requests = []
        
        self.current_page = 1
        self.update_display()

    def destroy(self):
        """Clean up when window is closed"""
        try:
            self.main_frame.destroy()
        except:
            pass

    def _relative_to_assets(self, path: str):
        """Get path to assets"""
        return Path(resource_path(f"resources/assets/documents/{path}"))

def resource_path(relative_path):
    """Get absolute path to resource"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
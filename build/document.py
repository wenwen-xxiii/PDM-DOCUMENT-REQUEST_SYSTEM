from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox, StringVar, Frame
import mysql.connector
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing modules
from config import DB_CONFIG
from requestform import DocumentRequestWindow

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/documents/{path}"))

class DocumentWindow:
    def __init__(self, parent, user_data=None, user_type=None, get_db_connection=None, navigation_callbacks=None):
        self.parent = parent
        self.user_data = user_data or {}
        self.user_type = user_type
        self.get_db_connection = get_db_connection
        self.navigation_callbacks = navigation_callbacks or {}
        
        # Safely get student_id - handle case where 'id' might not exist
        self.student_id = user_data.get('id') if user_data else None
        
        # If student_id is not available, try to get it from student_number or other fields
        if not self.student_id and user_data and 'student_number' in user_data:
            # You might need to query the database to get the student_id from student_number
            self.student_id = self.get_student_id_from_number(user_data['student_number'])
        
        self.current_page = 1
        self.requests_per_page = 4
        self.document_requests = []
        
        # Store all image references to prevent garbage collection
        self.images = []
        
        # Store card references to show/hide them
        self.card_images = []
        self.card_canvas_ids = []
        
        # Store entry background references
        self.entry_bg_ids = []
        
        # Create main frame for document content only (starts below navigation)
        self.main_frame = Frame(self.parent, bg="#FCECB7")
        self.main_frame.place(x=0, y=140, width=1270, height=650)  # Start below navigation
        
        self.setup_ui()
        self.load_document_requests()
        self.update_display()

    def get_student_id_from_number(self, student_number):
        """Get student_id from student_number if not directly available in user_data"""
        try:
            if self.get_db_connection:
                connection = self.get_db_connection()
                cursor = connection.cursor()
                cursor.execute("SELECT id FROM students WHERE student_number = %s", (student_number,))
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting student_id: {e}")
        return None
        
    def setup_ui(self):
        """Setup the document content only (no header/navigation)"""
        
        # Create canvas for document content
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
        
        # UI elements from the designer
        self.create_ui_elements()
        
    def create_ui_elements(self):
        # Store all image references to prevent garbage collection
        self.images = []
        
        # Store entry background image references
        self.entry_bg_ids = []
        
        # Main content background
        self.canvas.create_rectangle(47.0, 24.0, 1222.0, 590.0, fill="#FEFEFE", outline="")  # Adjusted y-positions

        # Grid header
        header_img = PhotoImage(file=relative_to_assets("img_headergrid.png"))
        self.images.append(header_img)  # Store reference
        self.header_bg_id = self.canvas.create_image(635.0, 125.5, image=header_img)  # Store ID for header

        # Header labels (adjusted y-positions)
        self.canvas.create_text(117.0, 117.0, anchor="nw", text="Request Number", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(368.0, 117.0, anchor="nw", text="Document Name", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(658.0, 117.0, anchor="nw", text="Release Date", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(797.0, 128.0, anchor="nw", text="to Pay", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(790.0, 106.0, anchor="nw", text="Amount", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(895.0, 128.0, anchor="nw", text="Type", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(882.0, 106.0, anchor="nw", text="Delivery", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(996.0, 117.0, anchor="nw", text="Status", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(587.0, 106.0, anchor="nw", text="No. of", fill="#FEFEFE", font=("Inter", 16 * -1))
        self.canvas.create_text(591.0, 128.0, anchor="nw", text="Days", fill="#FEFEFE", font=("Inter", 16 * -1))

        # Card backgrounds (adjusted y-positions) - Create but don't show initially
        img_cards = []
        y_centers = [202.5, 295.5, 387.5, 479.5]  # Adjusted y-positions

        for i, y in enumerate(y_centers):
            card_img = PhotoImage(file=relative_to_assets("img_card_bg.png"))
            img_cards.append(card_img)
            self.images.append(card_img)  # Store reference
            # Store canvas ID for each card so we can show/hide them
            card_id = self.canvas.create_image(635.0, y, image=card_img)
            self.card_canvas_ids.append(card_id)
            # Hide all cards initially
            self.canvas.itemconfig(card_id, state='hidden')

        # Entry field configurations - using loops for all 4 rows (adjusted y-positions)
        entry_configs = [
            # Row 1 positions
            {
                'y_center': 203.0, 'y_pos': 183.0,  # Adjusted y-positions
                'entries': [
                    {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                    {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                    {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                    {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                    {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                    {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                    {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                ]
            },
            # Row 2 positions
            {
                'y_center': 295.0, 'y_pos': 275.0,  # Adjusted y-positions
                'entries': [
                    {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                    {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                    {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                    {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                    {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                    {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                    {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                ]
            },
            # Row 3 positions
            {
                'y_center': 387.0, 'y_pos': 367.0,  # Adjusted y-positions
                'entries': [
                    {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                    {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                    {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                    {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                    {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                    {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                    {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                ]
            },
            # Row 4 positions
            {
                'y_center': 479.0, 'y_pos': 459.0,  # Adjusted y-positions
                'entries': [
                    {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                    {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                    {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                    {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                    {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                    {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                    {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                ]
            }
        ]

        # Create entry fields using loops
        self.entry_fields = []
        
        for row_idx, config in enumerate(entry_configs):
            row_entries = {}
            row_bg_ids = []  # Store background IDs for this row
            
            for entry_config in config['entries']:
                # Create entry background image
                entry_img = PhotoImage(file=relative_to_assets(f"entry_{entry_config['type']}.png"))
                self.images.append(entry_img)  # Store reference
                bg_id = self.canvas.create_image(entry_config['x_center'], config['y_center'], image=entry_img)
                row_bg_ids.append(bg_id)  # Store background ID
                
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
                    x=entry_config['x_pos'],
                    y=config['y_pos'],
                    width=entry_config['width'],
                    height=38.0
                )
                
                # Store entry in row dictionary
                row_entries[entry_config['type']] = entry
            
            self.entry_fields.append(row_entries)
            self.entry_bg_ids.append(row_bg_ids)  # Store all background IDs for this row

        # Buttons (adjusted y-positions)
        button_image_1 = PhotoImage(file=relative_to_assets("button_new_request.png"))
        self.images.append(button_image_1)  # Store reference
        self.button_new_request = Button(
            self.main_frame,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.new_request,
            relief="flat"
        )
        self.button_new_request.place(x=1045.0, y=49.0, width=158.0, height=40.0)  # Adjusted y-position

        # Create payment and view document buttons for each row (adjusted y-positions)
        self.payment_buttons = []
        self.view_docu_buttons = []
        
        # Button positions for each row (y-coordinates) - adjusted
        button_y_positions = [184.0, 276.0, 368.0, 460.0]
        
        # Load button images
        button_pay_img = PhotoImage(file=relative_to_assets("button_pay.png"))
        self.images.append(button_pay_img)
        
        button_view_docu_img = PhotoImage(file=relative_to_assets("button_view_docu.png"))
        self.images.append(button_view_docu_img)
        
        # Create buttons for each row
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

        # Page navigation buttons (adjusted y-positions)
        button_image_3 = PhotoImage(file=relative_to_assets("button_prev_page.png"))
        self.images.append(button_image_3)  # Store reference
        self.button_prev_page = Button(
            self.main_frame,
            image=button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.previous_page,
            relief="flat"
        )
        self.button_prev_page.place(x=460.0, y=540.0, width=113.0, height=32.0)  # Adjusted y-position

        button_image_4 = PhotoImage(file=relative_to_assets("button_next_page.png"))
        self.images.append(button_image_4)  # Store reference
        self.button_next_page = Button(
            self.main_frame,
            image=button_image_4,
            borderwidth=0,
            highlightthickness=0,
            command=self.next_page,
            relief="flat"
        )
        self.button_next_page.place(x=732.0, y=540.0, width=84.0, height=32.0)  # Adjusted y-position

        # Page number display (adjusted y-positions)
        self.page_var = StringVar(value="1")
        entry_image_8 = PhotoImage(file=relative_to_assets("entry_pageno.png"))
        self.images.append(entry_image_8)  # Store reference
        self.canvas.create_image(652.5, 558.0, image=entry_image_8)  # Adjusted y-position
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
        self.entry_pageno.place(x=583.0, y=539.0, width=139.0, height=36.0)  # Adjusted y-position

    def load_document_requests(self):
        """Load document requests from database"""
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    dr.request_number,
                    dt.name as document_name,
                    dr.request_release_date,
                    dr.quantity,
                    dr.total_amount,
                    dr.delivery_mode,
                    dr.status,
                    dr.payment_status
                FROM document_requests dr
                JOIN document_types dt ON dr.document_type_id = dt.id
                WHERE dr.student_id = %s
                ORDER BY dr.request_date DESC
            """, (self.student_id,))
            
            self.document_requests = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Failed to load document requests: {str(e)}")
            self.document_requests = []

    def update_display(self):
        """Update the display with current page data"""
        # First, remove any existing "no records" text
        self.canvas.delete("no_records_text")
        
        # Clear all entries first
        for row in self.entry_fields:
            for entry in row.values():
                entry.config(state="normal")
                entry.delete(0, "end")
                entry.config(state="readonly")
        
        # Hide all buttons initially
        for i in range(len(self.payment_buttons)):
            self.payment_buttons[i].place_forget()
            self.view_docu_buttons[i].place_forget()
        
        # Hide all cards initially
        for card_id in self.card_canvas_ids:
            self.canvas.itemconfig(card_id, state='hidden')
        
        # Hide all entry field backgrounds and widgets initially
        for row_idx, row_bg_ids in enumerate(self.entry_bg_ids):
            for bg_id in row_bg_ids:
                self.canvas.itemconfig(bg_id, state='hidden')
        
        for row in self.entry_fields:
            for entry_name, entry_widget in row.items():
                # Hide the entry widgets themselves
                entry_widget.place_forget()
        
        # Show "No records found" message if no requests exist
        if not self.document_requests:
            self.show_no_records_message()
            return
        
        # Calculate start and end indices for current page
        start_idx = (self.current_page - 1) * self.requests_per_page
        end_idx = start_idx + self.requests_per_page
        current_requests = self.document_requests[start_idx:end_idx]
        
        # Show only the cards and entries that have data
        for i, request in enumerate(current_requests):
            if i < len(self.entry_fields):
                # Show the card for this row
                if i < len(self.card_canvas_ids):
                    self.canvas.itemconfig(self.card_canvas_ids[i], state='normal')
                
                # Show entry backgrounds for this row
                if i < len(self.entry_bg_ids):
                    for bg_id in self.entry_bg_ids[i]:
                        self.canvas.itemconfig(bg_id, state='normal')
                
                row = self.entry_fields[i]
                
                # Show all entry fields for this row by re-placing them
                entry_configs = [
                    # Row 1 positions
                    {
                        'y_center': 203.0, 'y_pos': 183.0,
                        'entries': [
                            {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                            {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                            {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                            {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                            {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                            {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                            {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                        ]
                    },
                    # Row 2 positions
                    {
                        'y_center': 295.0, 'y_pos': 275.0,
                        'entries': [
                            {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                            {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                            {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                            {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                            {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                            {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                            {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                        ]
                    },
                    # Row 3 positions
                    {
                        'y_center': 387.0, 'y_pos': 367.0,
                        'entries': [
                            {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                            {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                            {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                            {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                            {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                            {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                            {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                        ]
                    },
                    # Row 4 positions
                    {
                        'y_center': 479.0, 'y_pos': 459.0,
                        'entries': [
                            {'type': 'delivery_type', 'x_center': 915.0, 'x_pos': 883.0, 'width': 64.0},
                            {'type': 'requestno', 'x_center': 183.0, 'x_pos': 93.0, 'width': 180.0},
                            {'type': 'docu_type', 'x_center': 433.0, 'x_pos': 304.0, 'width': 258.0},
                            {'type': 'docu_status', 'x_center': 1022.0, 'x_pos': 978.0, 'width': 88.0},
                            {'type': 'amount_pay', 'x_center': 822.5, 'x_pos': 793.0, 'width': 59.0},
                            {'type': 'docu_copy', 'x_center': 609.5, 'x_pos': 593.0, 'width': 33.0},
                            {'type': 'release_date', 'x_center': 709.5, 'x_pos': 657.0, 'width': 105.0}
                        ]
                    }
                ]
                
                # Place each entry widget at its correct position
                for entry_config in entry_configs[i]['entries']:
                    entry_name = entry_config['type']
                    if entry_name in row:
                        row[entry_name].place(
                            x=entry_config['x_pos'],
                            y=entry_configs[i]['y_pos'],
                            width=entry_config['width'],
                            height=38.0
                        )
                
                # Format delivery type
                delivery_type = "Online" if request['delivery_mode'] == 'online' else "Pickup"
                
                # Format status with payment info
                status = request['status'].title()
                if request['payment_status'] == 'pending' and request['status'] == 'submitted':
                    status = "Payment Pending"
                
                # Update entries with actual data
                row['requestno'].config(state="normal")
                row['requestno'].delete(0, "end")
                row['requestno'].insert(0, request['request_number'])
                row['requestno'].config(state="readonly")
                
                row['docu_type'].config(state="normal")
                row['docu_type'].delete(0, "end")
                row['docu_type'].insert(0, request['document_name'])
                row['docu_type'].config(state="readonly")
                
                row['release_date'].config(state="normal")
                row['release_date'].delete(0, "end")
                row['release_date'].insert(0, request['request_release_date'].strftime('%Y-%m-%d'))
                row['release_date'].config(state="readonly")
                
                row['docu_copy'].config(state="normal")
                row['docu_copy'].delete(0, "end")
                row['docu_copy'].insert(0, str(request['quantity']))
                row['docu_copy'].config(state="readonly")
                
                row['amount_pay'].config(state="normal")
                row['amount_pay'].delete(0, "end")
                row['amount_pay'].insert(0, f"₱{request['total_amount']:.2f}")
                row['amount_pay'].config(state="readonly")
                
                row['delivery_type'].config(state="normal")
                row['delivery_type'].delete(0, "end")
                row['delivery_type'].insert(0, delivery_type)
                row['delivery_type'].config(state="readonly")
                
                row['docu_status'].config(state="normal")
                row['docu_status'].delete(0, "end")
                row['docu_status'].insert(0, status)
                row['docu_status'].config(state="readonly")
                
                # Show appropriate button based on status
                button_y_positions = [184.0, 276.0, 368.0, 460.0]
                
                if status.lower() == "payment pending":
                    # Show payment button
                    self.payment_buttons[i].place(x=1089.0, y=button_y_positions[i], width=96.0, height=40.0)
                elif status.lower() == "completed":
                    # Show view document button
                    self.view_docu_buttons[i].place(x=1089.0, y=button_y_positions[i], width=96.0, height=40.0)
        
        # Update page display
        total_pages = max(1, (len(self.document_requests) + self.requests_per_page - 1) // self.requests_per_page)
        self.page_var.set(f"Page {self.current_page} of {total_pages}")
        
        # Update button states
        self.button_prev_page.config(state="normal" if self.current_page > 1 else "disabled")
        self.button_next_page.config(state="normal" if self.current_page < total_pages else "disabled")

    def show_no_records_message(self):
        """Show a message when no document requests exist"""
        # Hide all cards
        for card_id in self.card_canvas_ids:
            self.canvas.itemconfig(card_id, state='hidden')
        
        # Hide all entry backgrounds
        for row_idx, row_bg_ids in enumerate(self.entry_bg_ids):
            for bg_id in row_bg_ids:
                self.canvas.itemconfig(bg_id, state='hidden')
        
        # Hide all entry fields
        for row in self.entry_fields:
            for entry_widget in row.values():
                entry_widget.place_forget()
        
        # Hide all buttons
        for i in range(len(self.payment_buttons)):
            self.payment_buttons[i].place_forget()
            self.view_docu_buttons[i].place_forget()
        
        # Remove any existing "no records" text and create new one
        self.canvas.delete("no_records_text")
        self.canvas.create_text(
            635.0,  # Center x
            300.0,  # Center y
            text="No document requests found",
            fill="#666666",
            font=("Inter", 16, "bold"),
            anchor="center",
            tags="no_records_text"
        )
        
        # Set page display
        self.page_var.set("Page 1 of 1")
        
        # Disable navigation buttons
        self.button_prev_page.config(state="disabled")
        self.button_next_page.config(state="disabled")

    def new_request(self):
        """Open new document request form"""
        if not self.student_id:
            messagebox.showerror("Error", "Student ID not found. Please contact administrator.")
            return
            
        # Create the request form window
        self.request_window = DocumentRequestWindow(
            parent=self.parent,  # Pass the main parent window
            student_id=self.student_id,
            show_dashboard_callback=self.refresh_requests  # Refresh the list after submission
        )
        
        # Run the request form
        self.request_window.run()

    def view_document(self, row_index):
        """View document details for specific row"""
        start_idx = (self.current_page - 1) * self.requests_per_page
        actual_index = start_idx + row_index
        
        if actual_index < len(self.document_requests):
            request = self.document_requests[actual_index]
            messagebox.showinfo(
                "View Document", 
                f"Document Details:\n\n"
                f"Request Number: {request['request_number']}\n"
                f"Document: {request['document_name']}\n"
                f"Status: {request['status'].title()}\n"
                f"Release Date: {request['request_release_date'].strftime('%Y-%m-%d')}"
            )

    def make_payment(self, row_index):
        """Process payment for a specific document request"""
        start_idx = (self.current_page - 1) * self.requests_per_page
        actual_index = start_idx + row_index
        
        if actual_index < len(self.document_requests):
            request = self.document_requests[actual_index]
            messagebox.showinfo(
                "Payment", 
                f"Payment for:\n\n"
                f"Request Number: {request['request_number']}\n"
                f"Document: {request['document_name']}\n"
                f"Amount: ₱{request['total_amount']:.2f}\n\n"
                f"Payment gateway would open here."
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
        """Refresh the document requests list"""
        self.load_document_requests()
        self.current_page = 1
        self.update_display()

    def destroy(self):
        """Clean up when window is closed"""
        try:
            self.main_frame.destroy()
        except:
            pass
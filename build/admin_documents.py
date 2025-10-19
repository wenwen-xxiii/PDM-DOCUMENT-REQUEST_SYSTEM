# admindocuments.py - Admin Document Types Manager
from pathlib import Path
from tkinter import Canvas, Frame, Label, Button, Entry, messagebox, Scrollbar, Toplevel
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime
import asyncio
import threading
import concurrent.futures

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

class AdminDocumentManager:
    def __init__(self, parent, get_db_connection=None, user_data=None):
        self.parent = parent
        self.get_db_connection = get_db_connection
        self.user_data = user_data or {}
        
        # Document types data
        self.document_types = []
        self.filtered_documents = []
        self.search_query = ""
        self.current_page = 1
        self.documents_per_page = 8
        
        # UI element storage
        self.images = []
        self.row_widgets = []
        
        # Loading indicator
        self.loading_label = None
        
        self.setup_ui()
        self.load_document_types()
        self.update_display()
        
    def setup_ui(self):
        """Setup the document types management UI inside the parent frame"""
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
        
        # Create search bar (top-right)
        self.create_searchbar()
        
        # Create title label (top left)
        self.create_title_label()
        
        # Create add document type button (above table header)
        self.create_add_button()
        
        # Create table header
        self.create_table_headers()
        
        # Create navigation controls
        self.create_navigation_controls()
        
    def create_add_button(self):
        """Create Add Document Type button below the title label"""
        self.button_add_document = Button(
            self.parent,
            text="Add Document Type",
            font=("Inter", 10, "bold"),
            bg="#28a745",
            fg="#FFFFFF",
            relief="flat",
            command=self.add_document_type
        )
        # Position below the title label (y=15 + height=18 + spacing=5 = y=38)
        self.button_add_document.place(x=725, y=60, width=150, height=35)
        
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
        self.search_entry.insert(0, "Search documents...")
        # Simple placeholder behavior
        def _on_focus_in(event):
            if self.search_entry.get() == "Search documents...":
                self.search_entry.delete(0, "end")
        def _on_focus_out(event):
            if not self.search_entry.get().strip():
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, "Search documents...")
        self.search_entry.bind("<FocusIn>", _on_focus_in)
        self.search_entry.bind("<FocusOut>", _on_focus_out)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def create_title_label(self):
        """Create a title label in the top left"""
        self.title_label = Label(
            self.parent,
            text="Document Management",
            font=("Inter", 18, "bold"),
            bg="#FFFFFF",
            fg="#792D1B"
        )
        self.title_label.place(x=20, y=15)

    def create_table_headers(self):
        """Create table header labels for document types"""
        headers = [
            (40.0, "No.", "center"),
            (100.0, "Code", "center"),
            (220.0, "Document Name", "center"),
            (350.0, "Fee Amount", "center"),
            (470.0, "Processing Days", "center"),
            (580.0, "Clearance", "center"),
            (660.0, "Status", "center"),
            (790.0, "Actions", "center")
        ]
        
        # Header background - dark brown like in the image
        self.canvas.create_rectangle(20, 110, 875, 150, fill="#792D1B", outline="")
        
        for x, text, anchor in headers:
            self.canvas.create_text(
                x, 130, 
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

    async def load_document_types_async(self):
        """Load document types from database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    document_type_id,
                    code,
                    name,
                    fee_amount,
                    description,
                    processing_days,
                    requires_clearance,
                    is_available,
                    created_by,
                    created_at,
                    updated_at
                FROM document_types
                ORDER BY created_at DESC
            """)
            
            self.document_types = cursor.fetchall()
            # Default filtered list is full list
            self.filtered_documents = list(self.document_types)
            
            cursor.close()
            connection.close()
            
            print(f"✅ Loaded {len(self.document_types)} document types from database")
            
        except Error as e:
            print(f"❌ Error loading document types: {e}")
            messagebox.showerror("Database Error", f"Failed to load document types: {str(e)}")
            self.document_types = []

    def load_document_types(self):
        """Load document types from database (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create a new one
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.load_document_types_async())
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async load_document_types: {e}")
                return asyncio.run(self.load_document_types_async())
        else:
            # Event loop exists, run in thread pool
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.load_document_types_async())
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async load_document_types: {e}")
                return asyncio.run(self.load_document_types_async())

    def update_display(self):
        """Update the display with current page data"""
        self.clear_table_rows()
        
        if not self.filtered_documents:
            self.show_no_documents_message()
            return
            
        self.display_current_documents()
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

    def display_current_documents(self):
        """Display document types for current page"""
        start_idx = (self.current_page - 1) * self.documents_per_page
        end_idx = start_idx + self.documents_per_page
        current_documents = self.filtered_documents[start_idx:end_idx]
        
        for i, document in enumerate(current_documents):
            self.create_table_row(i, document)

    def on_search_change(self, event=None):
        """Handle search text changes and filter the list"""
        query = self.search_entry.get().strip()
        # Ignore placeholder
        if query == "Search documents...":
            query = ""
        self.search_query = query.lower()
        self.apply_search_filter()

    def apply_search_filter(self):
        """Filter document_types into filtered_documents based on search_query"""
        if not self.search_query:
            self.filtered_documents = list(self.document_types)
        else:
            q = self.search_query
            def matches(doc):
                values = [
                    str(doc.get('code', '')),
                    str(doc.get('name', '')),
                    str(doc.get('description', '')),
                    str(doc.get('fee_amount', '')),
                    str(doc.get('processing_days', '')),
                    str(doc.get('requires_clearance', '')),
                    str(doc.get('is_available', '')),
                ]
                text = " ".join(values).lower()
                return q in text
            self.filtered_documents = [d for d in self.document_types if matches(d)]
        # Reset to first page after filtering
        self.current_page = 1
        self.update_display()

    def create_table_row(self, row_index, document):
        """Create a table row with data and action buttons"""
        y_position = 160 + (row_index * 45)
        
        # Row background (alternating colors)
        fill_color = "#FFFFFF" if row_index % 2 == 0 else "#F8F8F8"
        self.canvas.create_rectangle(
            20, y_position, 875, y_position + 40, 
            fill=fill_color, outline="#E0E0E0", tags="row"
        )
        
        # Calculate row number (global index)
        row_number = ((self.current_page - 1) * self.documents_per_page) + row_index + 1
        
        # Format fee amount
        fee_amount = f"₱{document['fee_amount']:.2f}"
        
        # Status display
        status_text = "Available" if document['is_available'] else "Unavailable"
        
        # Clearance display
        clearance_text = "Yes" if document['requires_clearance'] else "No"
        
        # Create text elements for the row with proper alignment
        text_configs = [
            (40.0, str(row_number), "center"),
            (100.0, document['code'], "center"),
            (200.0, document['name'][:20] + "..." if len(document['name']) > 20 else document['name'], "center"),
            (350.0, fee_amount, "center"),
            (470.0, str(document['processing_days']), "center"),
            (580.0, clearance_text, "center"),
            (660.0, status_text, "center")
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
        self.create_row_buttons(row_index, document, y_position)

    def create_row_buttons(self, row_index, document, y_position):
        """Create action buttons for each row"""
        button_widgets = []
        
        # Edit button
        edit_button = Button(
            self.parent,
            text="Edit",
            font=("Inter", 9),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=lambda d=document: self.edit_document_type(d)
        )
        edit_button.place(x=730, y=y_position + 8, width=50, height=25)
        button_widgets.append(edit_button)
        
        # Toggle status button
        status_text = "Deactivate" if document['is_available'] else "Activate"
        status_color = "#dc3545" if document['is_available'] else "#28a745"
        
        status_button = Button(
            self.parent,
            text=status_text,
            font=("Inter", 9),
            bg=status_color,
            fg="#FFFFFF",
            relief="flat",
            command=lambda d=document: self.toggle_document_status(d)
        )
        status_button.place(x=790, y=y_position + 8, width=70, height=25)
        button_widgets.append(status_button)
        
        self.row_widgets.append(button_widgets)

    def add_document_type(self):
        """Open add document type dialog"""
        self.open_document_form()

    def edit_document_type(self, document):
        """Open edit document type dialog"""
        self.open_document_form(document)

    def open_document_form(self, document=None):
        """Open document type form dialog"""
        dialog = Toplevel(self.parent)
        dialog.title("Add Document Type" if not document else f"Edit Document Type - {document['code']}")
        dialog.geometry("500x650")
        dialog.resizable(False, False)
        dialog.configure(bg="#FCECB7")
        
        # Center the dialog on screen
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the window on screen
        dialog.update_idletasks()
        width, height = 500, 650
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Force focus and ensure proper display
        dialog.focus_force()
        dialog.lift()
        
        # Create canvas for centered layout
        canvas = Canvas(
            dialog,
            bg="#FCECB7",
            height=650,
            width=500,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        canvas.place(x=0, y=0)
        
        # Header section
        canvas.create_rectangle(0.0, 0.0, 500.0, 80.0, fill="#792D1B", outline="")
        canvas.create_rectangle(0.0, 50.0, 500.0, 80.0, fill="#FFDA0C", outline="")
        
        # Header text
        title_text = "Add Document Type" if not document else "Edit Document Type"
        canvas.create_text(
            250.0, 65.0,
            text=title_text,
            fill="#000000",
            font=("Inter", 16, "bold"),
            anchor="center"
        )
        
        # White background panel
        canvas.create_rectangle(
            25.0, 100.0, 475.0, 625.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # Form fields - centered layout like payment window
        center_x = 250.0  # Center of the dialog
        field_y_start = 130
        field_spacing = 65
        
        # Document Code field
        canvas.create_text(
            center_x, field_y_start,
            text="Document Code:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        code_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        code_entry.place(x=150, y=field_y_start + 20, width=200, height=30)
        
        # Document Name field
        canvas.create_text(
            center_x, field_y_start + field_spacing,
            text="Document Name:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        name_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        name_entry.place(x=150, y=field_y_start + field_spacing + 20, width=200, height=30)
        
        # Fee Amount field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 2),
            text="Fee Amount:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        fee_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        fee_entry.place(x=150, y=field_y_start + (field_spacing * 2) + 20, width=200, height=30)
        
        # Processing Days field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 3),
            text="Processing Days:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        processing_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        processing_entry.place(x=150, y=field_y_start + (field_spacing * 3) + 20, width=200, height=30)
        
        # Description field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 4),
            text="Description:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        from tkinter import Text
        desc_text = Text(dialog, font=("Inter", 10), width=35, height=3, bg="#FFFFFF", relief="solid", bd=1)
        desc_text.place(x=100, y=field_y_start + (field_spacing * 4) + 20, width=300, height=60)
        
        # Status checkbox
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 5),
            text="Available:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        from tkinter import Checkbutton, BooleanVar
        status_var = BooleanVar()
        status_check = Checkbutton(dialog, text="Enable Availability", variable=status_var, font=("Inter", 10), bg="#FFFFFF")
        status_check.place(x=center_x - 80, y=field_y_start + (field_spacing * 5) + 20, width=160, height=20)
        
        # Clearance checkbox
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 6),
            text="Requires Clearance:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        clearance_var = BooleanVar()
        clearance_check = Checkbutton(dialog, text="Enable Clearance Requirement", variable=clearance_var, font=("Inter", 10), bg="#FFFFFF")
        clearance_check.place(x=center_x - 115, y=field_y_start + (field_spacing * 6) + 20, width=225, height=20)
        
        # Populate fields if editing
        if document:
            code_entry.insert(0, document['code'])
            name_entry.insert(0, document['name'])
            fee_entry.insert(0, str(document['fee_amount']))
            processing_entry.insert(0, str(document['processing_days']))
            desc_text.insert("1.0", document['description'])
            status_var.set(document['is_available'])
            clearance_var.set(document['requires_clearance'])
        
        # Buttons
        def save_document():
            code = code_entry.get().strip()
            name = name_entry.get().strip()
            fee_str = fee_entry.get().strip()
            processing_str = processing_entry.get().strip()
            description = desc_text.get("1.0", "end").strip()
            is_available = status_var.get()
            requires_clearance = clearance_var.get()
            
            if not all([code, name, fee_str, processing_str, description]):
                messagebox.showerror("Error", "All fields are required")
                return
            
            try:
                fee_amount = float(fee_str)
                processing_days = int(processing_str)
            except ValueError:
                messagebox.showerror("Error", "Fee amount and processing days must be valid numbers")
                return
            
            # Show loading indicator
            dialog.show_loading_indicator = lambda msg: None  # Disable loading for dialog
            self.show_loading_indicator("Saving document...")
            
            # Use threading to avoid blocking UI
            def save_thread():
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop running, create a new one
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            if document:
                                future = executor.submit(asyncio.run, self.update_document_type_async(document['document_type_id'], code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                            else:
                                future = executor.submit(asyncio.run, self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                            result = future.result()
                    except Exception as e:
                        print(f"❌ Error in async save_document: {e}")
                        if document:
                            result = asyncio.run(self.update_document_type_async(document['document_type_id'], code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                        else:
                            result = asyncio.run(self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                else:
                    # Event loop exists, run in thread pool
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            if document:
                                future = executor.submit(asyncio.run, self.update_document_type_async(document['document_type_id'], code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                            else:
                                future = executor.submit(asyncio.run, self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                            result = future.result()
                    except Exception as e:
                        print(f"❌ Error in async save_document: {e}")
                        if document:
                            result = asyncio.run(self.update_document_type_async(document['document_type_id'], code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                        else:
                            result = asyncio.run(self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                
                # Schedule UI update on main thread
                self.parent.after(0, lambda: self._update_ui_after_save(result, dialog))
            
            save_thread_obj = threading.Thread(target=save_thread, daemon=True)
            save_thread_obj.start()
        
        def cancel_form():
            dialog.destroy()
        
        # Save and Cancel buttons - centered
        Button(dialog, text="Save", font=("Inter", 12, "bold"), bg="#28a745", fg="#FFFFFF", 
               relief="flat", command=save_document).place(x=140, y=580, width=100, height=35)
        Button(dialog, text="Cancel", font=("Inter", 12, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=cancel_form).place(x=260, y=580, width=100, height=35)
    
    def _update_ui_after_save(self, success, dialog):
        """Update UI after save operation completes"""
        try:
            self.hide_loading_indicator()
            if success:
                dialog.destroy()
                self.load_document_types()
                self.update_display()
            else:
                messagebox.showerror("Error", "Failed to save document type")
        except Exception as e:
            print(f"❌ Error during UI update after save: {e}")

    async def add_new_document_type_async(self, code, name, fee_amount, processing_days, description, is_available, requires_clearance):
        """Add new document type to database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO document_types (code, name, fee_amount, processing_days, description, is_available, requires_clearance, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (code, name, fee_amount, processing_days, description, is_available, requires_clearance, datetime.now()))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Added new document type: {code}")
            return True
            
        except Error as e:
            print(f"❌ Error adding document type: {e}")
            return False

    def add_new_document_type(self, code, name, fee_amount, processing_days, description, is_available, requires_clearance):
        """Add new document type to database (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create a new one
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async add_new_document_type: {e}")
                return asyncio.run(self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))
        else:
            # Event loop exists, run in thread pool
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async add_new_document_type: {e}")
                return asyncio.run(self.add_new_document_type_async(code, name, fee_amount, processing_days, description, is_available, requires_clearance))

    async def update_document_type_async(self, document_id, code, name, fee_amount, processing_days, description, is_available, requires_clearance):
        """Update existing document type in database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE document_types 
                SET code = %s, name = %s, fee_amount = %s, processing_days = %s, description = %s, is_available = %s, requires_clearance = %s, updated_at = %s
                WHERE document_type_id = %s
            """, (code, name, fee_amount, processing_days, description, is_available, requires_clearance, datetime.now(), document_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Updated document type: {code}")
            return True
            
        except Error as e:
            print(f"❌ Error updating document type: {e}")
            return False

    def update_document_type(self, document_id, code, name, fee_amount, processing_days, description, is_available, requires_clearance):
        """Update existing document type in database (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create a new one
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.update_document_type_async(document_id, code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async update_document_type: {e}")
                return asyncio.run(self.update_document_type_async(document_id, code, name, fee_amount, processing_days, description, is_available, requires_clearance))
        else:
            # Event loop exists, run in thread pool
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.update_document_type_async(document_id, code, name, fee_amount, processing_days, description, is_available, requires_clearance))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async update_document_type: {e}")
                return asyncio.run(self.update_document_type_async(document_id, code, name, fee_amount, processing_days, description, is_available, requires_clearance))

    async def toggle_document_status_async(self, document):
        """Toggle document type active status (async version)"""
        new_status = not document['is_available']
        
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE document_types 
                SET is_available = %s, updated_at = %s
                WHERE document_type_id = %s
            """, (new_status, datetime.now(), document['document_type_id']))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Document type {document['code']} status changed to {'active' if new_status else 'inactive'}")
            await self.load_document_types_async()
            # Schedule UI update on main thread
            self.parent.after(0, self.update_display)
            
        except Error as e:
            print(f"❌ Error toggling document status: {e}")
            messagebox.showerror("Database Error", f"Failed to update status: {str(e)}")

    def toggle_document_status(self, document):
        """Toggle document type active status (sync wrapper)"""
        new_status = not document['is_available']
        status_text = "activate" if new_status else "deactivate"
        
        if messagebox.askyesno("Toggle Status", 
                             f"{status_text.title()} document type '{document['code']}'?"):
            
            self.show_loading_indicator(f"{status_text.title()}ing document...")
            
            # Use threading to avoid blocking UI
            def toggle_thread():
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop running, create a new one
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self.toggle_document_status_async(document))
                            return future.result()
                    except Exception as e:
                        print(f"❌ Error in async toggle_document_status: {e}")
                        return asyncio.run(self.toggle_document_status_async(document))
                else:
                    # Event loop exists, run in thread pool
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self.toggle_document_status_async(document))
                            return future.result()
                    except Exception as e:
                        print(f"❌ Error in async toggle_document_status: {e}")
                        return asyncio.run(self.toggle_document_status_async(document))
            
            toggle_thread_obj = threading.Thread(target=toggle_thread, daemon=True)
            toggle_thread_obj.start()

    def show_no_documents_message(self):
        """Show message when no document types exist"""
        self.canvas.create_text(
            450, 200, anchor="center", text="No document types found",
            fill="#666666", font=("Inter", 14, "bold"), tags="row"
        )

    def update_navigation(self):
        """Update navigation elements"""
        total_pages = max(1, (len(self.filtered_documents) + self.documents_per_page - 1) // self.documents_per_page)
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
        total_pages = max(1, (len(self.filtered_documents) + self.documents_per_page - 1) // self.documents_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()

    def refresh_documents(self):
        """Refresh the document types list (async version)"""
        print("🔄 Refreshing document types...")
        self.show_loading_indicator("Refreshing documents...")
        
        # Use threading to avoid blocking UI
        def refresh_thread():
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop running, create a new one
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.load_document_types_async())
                        result = future.result()
                except Exception as e:
                    print(f"❌ Error in async refresh_documents: {e}")
                    result = asyncio.run(self.load_document_types_async())
            else:
                # Event loop exists, run in thread pool
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.load_document_types_async())
                        result = future.result()
                except Exception as e:
                    print(f"❌ Error in async refresh_documents: {e}")
                    result = asyncio.run(self.load_document_types_async())
            
            # Schedule UI update on main thread
            self.parent.after(0, self._update_ui_after_refresh)
        
        refresh_thread_obj = threading.Thread(target=refresh_thread, daemon=True)
        refresh_thread_obj.start()
    
    def _update_ui_after_refresh(self):
        """Update UI after async refresh completes"""
        try:
            self.hide_loading_indicator()
            self.current_page = 1
            self.update_display()
            print(f"✅ Refresh complete - {len(self.document_types)} document types loaded")
        except Exception as e:
            print(f"❌ Error during UI update after refresh: {e}")
    
    def show_loading_indicator(self, message="Loading..."):
        """Show loading indicator"""
        if self.loading_label:
            self.loading_label.destroy()
        
        self.loading_label = Label(
            self.parent,
            text=message,
            font=("Inter", 12),
            bg="#FFFFFF",
            fg="#792D1B"
        )
        self.loading_label.place(x=400, y=200)
    
    def hide_loading_indicator(self):
        """Hide loading indicator"""
        if self.loading_label:
            self.loading_label.destroy()
            self.loading_label = None

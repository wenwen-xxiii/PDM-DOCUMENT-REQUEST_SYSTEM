# admindocuments.py - Admin Document Types Manager
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

    def load_document_types(self):
        """Load document types from database"""
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
        dialog.geometry("400x550")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Form fields
        Label(dialog, text="Document Code:", font=("Inter", 10, "bold")).place(x=20, y=20)
        code_entry = Entry(dialog, font=("Inter", 10), width=30)
        code_entry.place(x=20, y=45)
        
        Label(dialog, text="Document Name:", font=("Inter", 10, "bold")).place(x=20, y=80)
        name_entry = Entry(dialog, font=("Inter", 10), width=30)
        name_entry.place(x=20, y=105)
        
        Label(dialog, text="Fee Amount:", font=("Inter", 10, "bold")).place(x=20, y=140)
        fee_entry = Entry(dialog, font=("Inter", 10), width=30)
        fee_entry.place(x=20, y=165)
        
        Label(dialog, text="Processing Days:", font=("Inter", 10, "bold")).place(x=20, y=200)
        processing_entry = Entry(dialog, font=("Inter", 10), width=30)
        processing_entry.place(x=20, y=225)
        
        Label(dialog, text="Description:", font=("Inter", 10, "bold")).place(x=20, y=260)
        from tkinter import Text
        desc_text = Text(dialog, font=("Inter", 10), width=35, height=4)
        desc_text.place(x=20, y=285)
        
        # Status checkbox
        from tkinter import Checkbutton, BooleanVar
        status_var = BooleanVar()
        status_check = Checkbutton(dialog, text="Available", variable=status_var, font=("Inter", 10))
        status_check.place(x=20, y=360)
        
        # Clearance checkbox
        clearance_var = BooleanVar()
        clearance_check = Checkbutton(dialog, text="Requires Clearance", variable=clearance_var, font=("Inter", 10))
        clearance_check.place(x=20, y=385)
        
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
            
            if document:
                # Update existing document
                success = self.update_document_type(document['document_type_id'], code, name, fee_amount, processing_days, description, is_available, requires_clearance)
            else:
                # Add new document
                success = self.add_new_document_type(code, name, fee_amount, processing_days, description, is_available, requires_clearance)
            
            if success:
                dialog.destroy()
                self.load_document_types()
                self.update_display()
            else:
                messagebox.showerror("Error", "Failed to save document type")
        
        def cancel_form():
            dialog.destroy()
        
        Button(dialog, text="Save", font=("Inter", 10, "bold"), bg="#28a745", fg="#FFFFFF", 
               relief="flat", command=save_document).place(x=20, y=450, width=100, height=35)
        Button(dialog, text="Cancel", font=("Inter", 10, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=cancel_form).place(x=140, y=450, width=100, height=35)

    def add_new_document_type(self, code, name, fee_amount, processing_days, description, is_available, requires_clearance):
        """Add new document type to database"""
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

    def update_document_type(self, document_id, code, name, fee_amount, processing_days, description, is_available, requires_clearance):
        """Update existing document type in database"""
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

    def toggle_document_status(self, document):
        """Toggle document type active status"""
        new_status = not document['is_available']
        status_text = "activate" if new_status else "deactivate"
        
        if messagebox.askyesno("Toggle Status", 
                             f"{status_text.title()} document type '{document['code']}'?"):
            
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
                self.load_document_types()
                self.update_display()
                
            except Error as e:
                print(f"❌ Error toggling document status: {e}")
                messagebox.showerror("Database Error", f"Failed to update status: {str(e)}")

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
        """Refresh the document types list"""
        print("🔄 Refreshing document types...")
        try:
            self.load_document_types()
            self.current_page = 1
            self.update_display()
            print(f"✅ Refresh complete - {len(self.document_types)} document types loaded")
        except Exception as e:
            print(f"❌ Error during refresh: {e}")

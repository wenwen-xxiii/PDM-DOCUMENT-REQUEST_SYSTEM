# adminuser.py - Admin User Manager for User Management
from pathlib import Path
from tkinter import Canvas, Frame, Label, Button, Entry, StringVar, messagebox, Scrollbar, Toplevel, Checkbutton, BooleanVar
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime
from tkinter import ttk
import asyncio
import threading
import concurrent.futures

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import DB_CONFIG
from utils.async_utils import safe_async_run
from utils.audit_logger import audit_logger

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

class AdminUserManager:
    def __init__(self, parent, get_db_connection=None, user_data=None):
        self.parent = parent
        self.get_db_connection = get_db_connection
        self.user_data = user_data or {}
        
        # User data
        self.users = []
        self.filtered_users = []
        self.search_query = ""
        self.current_page = 1
        self.users_per_page = 8
        self.account_filter = "all"  # "all", "students", "admins"
        
        # UI element storage
        self.images = []
        self.row_widgets = []
        
        # Loading indicator
        self.loading_label = None
        
        self.setup_ui()
        self.load_users()
        self.update_display()
        
    def setup_ui(self):
        """Setup the user management UI inside the parent frame"""
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
        
        # Create search bar (top)
        self.create_searchbar()
        
        # Create title label (top left)
        self.create_title_label()
        
        # Create filter button (for switching between student/admin accounts)
        self.create_filter_button()
        
        # Create add user button (under search bar)
        self.create_add_user_button()
        
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
        self.search_entry.insert(0, "Search users...")
        # Simple placeholder behavior
        def _on_focus_in(event):
            if self.search_entry.get() == "Search users...":
                self.search_entry.delete(0, "end")
        def _on_focus_out(event):
            if not self.search_entry.get().strip():
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, "Search users...")
        self.search_entry.bind("<FocusIn>", _on_focus_in)
        self.search_entry.bind("<FocusOut>", _on_focus_out)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def create_title_label(self):
        """Create a title label in the top left"""
        self.title_label = Label(
            self.parent,
            text="User Management",
            font=("Inter", 18, "bold"),
            bg="#FFFFFF",
            fg="#792D1B"
        )
        self.title_label.place(x=20, y=15)

    def create_filter_button(self):
        """Create filter button to switch between student/admin accounts"""
        # Filter button group container
        self.filter_frame = Frame(self.parent, bg="#FFFFFF")
        self.filter_frame.place(x=525, y=60, width=200, height=35)
        
        # All Users button (default selected)
        self.button_all_users = Button(
            self.filter_frame,
            text="All Users",
            font=("Inter", 10, "bold"),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            cursor="hand2",
            command=lambda: self.set_filter("all")
        )
        self.button_all_users.pack(side="left", padx=2)
        
        # Students button
        self.button_students = Button(
            self.filter_frame,
            text="Students",
            font=("Inter", 10),
            bg="#FFFFFF",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=lambda: self.set_filter("students")
        )
        self.button_students.pack(side="left", padx=2)
        
        # Admins button
        self.button_admins = Button(
            self.filter_frame,
            text="Admins",
            font=("Inter", 10),
            bg="#FFFFFF",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=lambda: self.set_filter("admins")
        )
        self.button_admins.pack(side="left", padx=2)
        
        # Initialize filter state
        self.update_filter_buttons()
    
    def set_filter(self, filter_type):
        """Set the account filter type"""
        self.account_filter = filter_type
        self.update_filter_buttons()
        self.apply_search_filter()  # This will apply both search and account filter
    
    def update_filter_buttons(self):
        """Update filter button appearance based on current filter"""
        # Reset all buttons to default state
        self.button_all_users.config(
            bg="#FFFFFF", fg="#792D1B", font=("Inter", 10)
        )
        self.button_students.config(
            bg="#FFFFFF", fg="#792D1B", font=("Inter", 10)
        )
        self.button_admins.config(
            bg="#FFFFFF", fg="#792D1B", font=("Inter", 10)
        )
        
        # Highlight active filter button
        if self.account_filter == "all":
            self.button_all_users.config(
                bg="#792D1B", fg="#FFDA0C", font=("Inter", 10, "bold")
            )
        elif self.account_filter == "students":
            self.button_students.config(
                bg="#792D1B", fg="#FFDA0C", font=("Inter", 10, "bold")
            )
        elif self.account_filter == "admins":
            self.button_admins.config(
                bg="#792D1B", fg="#FFDA0C", font=("Inter", 10, "bold")
            )
    
    def create_add_user_button(self):
        """Create add new user button under the search bar"""
        self.button_add_user = Button(
            self.parent,
            text="Add New User",
            font=("Inter", 12, "bold"),
            bg="#28a745",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            command=self.add_new_user
        )
        # Position under the search bar with some spacing
        self.button_add_user.place(x=750, y=60, width=120, height=35)

    def create_table_headers(self):
        """Create table header labels for users"""
        headers = [
            (40.0, "No.", "center"),
            (120.0, "Username", "center"),
            (300.0, "Email", "center"),
            (500.0, "User Type", "center"),
            (620.0, "Status", "center"),
            (770.0, "Actions", "center")
        ]
        
        # Header background - dark brown like in the image
        self.canvas.create_rectangle(20, 110, 875, 150, fill="#792D1B", outline="")
        
        for x, text, anchor in headers:
            self.canvas.create_text(
                x, 130, 
                anchor=anchor, 
                text=text, 
                fill="#FFFFFF", 
                font=("Inter", 12, "bold")
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

    async def load_users_async(self):
        """Load users from database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    user_id,
                    username,
                    email,
                    user_type,
                    is_active,
                    is_verified,
                    last_login,
                    created_at
                FROM users 
                ORDER BY created_at DESC
            """)
            
            self.users = cursor.fetchall()
            # Default filtered list is full list
            self.filtered_users = list(self.users)
            
            cursor.close()
            connection.close()
            
            print(f"✅ Loaded {len(self.users)} users from database")
            
        except Error as e:
            print(f"❌ Error loading users: {e}")
            messagebox.showerror("Database Error", f"Failed to load users: {str(e)}")
            self.users = []

    def load_users(self):
        """Load users from database (sync wrapper)"""
        try:
            safe_async_run(self.load_users_async)
        except Exception as e:
            print(f"❌ Error in async load_users: {e}")

    def update_display(self):
        """Update the display with current page data"""
        self.clear_table_rows()
        
        if not self.filtered_users:
            self.show_no_users_message()
            return
            
        self.display_current_users()
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

    def display_current_users(self):
        """Display users for current page"""
        start_idx = (self.current_page - 1) * self.users_per_page
        end_idx = start_idx + self.users_per_page
        current_users = self.filtered_users[start_idx:end_idx]
        
        for i, user in enumerate(current_users):
            self.create_table_row(i, user)

    def on_search_change(self, event=None):
        """Handle search text changes and filter the list"""
        query = self.search_entry.get().strip()
        # Ignore placeholder
        if query == "Search users...":
            query = ""
        self.search_query = query.lower()
        self.apply_search_filter()

    def apply_search_filter(self):
        """Filter users into filtered_users based on search_query and account_filter"""
        # First apply account type filter
        if self.account_filter == "students":
            filtered_by_type = [u for u in self.users if u.get('user_type', '').lower() == 'student']
        elif self.account_filter == "admins":
            filtered_by_type = [u for u in self.users if u.get('user_type', '').lower() in ['admin', 'registrar', 'cashier']]
        else:  # "all"
            filtered_by_type = list(self.users)
        
        # Then apply search query filter
        if not self.search_query:
            self.filtered_users = filtered_by_type
        else:
            q = self.search_query
            def matches(user):
                values = [
                    str(user.get('username', '')),
                    str(user.get('email', '')),
                    str(user.get('user_type', '')),
                    "active" if user.get('is_active') else "inactive",
                    "verified" if user.get('is_verified') else "unverified"
                ]
                text = " ".join(values).lower()
                return q in text
            self.filtered_users = [u for u in filtered_by_type if matches(u)]
        
        # Reset to first page after filtering
        self.current_page = 1
        self.update_display()

    def create_table_row(self, row_index, user):
        """Create a table row with data and action buttons"""
        y_position = 160 + (row_index * 45)
        
        # Row background (alternating colors)
        fill_color = "#FFFFFF" if row_index % 2 == 0 else "#F8F8F8"
        self.canvas.create_rectangle(
            20, y_position, 875, y_position + 40, 
            fill=fill_color, outline="#E0E0E0", tags="row"
        )
        
        # Calculate row number (global index)
        row_number = ((self.current_page - 1) * self.users_per_page) + row_index + 1
        
        # Format status display
        status_text = "Active" if user['is_active'] else "Inactive"
        
        # Create text elements for the row with proper alignment
        text_configs = [
            (40.0, str(row_number), "center"),
            (120.0, user['username'][:15] + "..." if len(user['username']) > 15 else user['username'], "center"),
            (300.0, user['email'][:25] + "..." if len(user['email']) > 25 else user['email'], "center"),
            (500.0, user['user_type'].title(), "center"),
            (620.0, status_text, "center")
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
        self.create_row_buttons(row_index, user, y_position)

    def create_row_buttons(self, row_index, user, y_position):
        """Create action buttons for each row"""
        button_widgets = []
        
        # View Details button - always available
        view_button = Button(
            self.parent,
            text="View",
            font=("Inter", 9),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=lambda u=user: self.view_user_details(u)
        )
        view_button.place(x=680, y=y_position + 8, width=50, height=25)
        button_widgets.append(view_button)
        
        # Edit button - always available
        edit_button = Button(
            self.parent,
            text="Edit",
            font=("Inter", 9),
            bg="#28a745",
            fg="#FFFFFF",
            relief="flat",
            command=lambda u=user: self.edit_user(u)
        )
        edit_button.place(x=740, y=y_position + 8, width=50, height=25)
        button_widgets.append(edit_button)
        
        # Status-specific action buttons
        is_active = user['is_active']
        
        if is_active:
            # Deactivate button
            deactivate_button = Button(
                self.parent,
                text="Deactivate",
                font=("Inter", 9),
                bg="#dc3545",
                fg="#FFFFFF",
                relief="flat",
                command=lambda u=user: self.toggle_user_status(u, False)
            )
            deactivate_button.place(x=800, y=y_position + 8, width=70, height=25)
            button_widgets.append(deactivate_button)
            
        else:
            # Activate button
            activate_button = Button(
                self.parent,
                text="Activate",
                font=("Inter", 9),
                bg="#28a745",
                fg="#FFFFFF",
                relief="flat",
                command=lambda u=user: self.toggle_user_status(u, True)
            )
            activate_button.place(x=800, y=y_position + 8, width=70, height=25)
            button_widgets.append(activate_button)
        
        self.row_widgets.append(button_widgets)

    def view_user_details(self, user):
        """Open user details dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"User Details - {user['username']}")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.configure(bg="#FCECB7")
        
        # Center the dialog on screen
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the window on screen
        dialog.update_idletasks()
        width, height = 500, 600
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
            height=600,
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
        canvas.create_text(
            250.0, 65.0,
            text="User Details",
            fill="#000000",
            font=("Inter", 16, "bold"),
            anchor="center"
        )
        
        # White background panel
        canvas.create_rectangle(
            25.0, 100.0, 475.0, 550.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # User information - centered layout
        info_y_start = 130
        line_height = 35
        center_x = 250.0  # Center of the dialog
        
        info_labels = [
            ("Username:", user['username']),
            ("Email:", user['email']),
            ("User Type:", user['user_type'].title()),
            ("Account Status:", "Active" if user['is_active'] else "Inactive"),
            ("Email Verified:", "Yes" if user['is_verified'] else "No"),
            ("Last Login:", user['last_login'].strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else "Never"),
            ("Created At:", user['created_at'].strftime('%Y-%m-%d %H:%M:%S') if user['created_at'] else "N/A"),
        ]
        
        for i, (label_text, value_text) in enumerate(info_labels):
            # Create centered text for each detail
            detail_text = f"{label_text} {value_text}"
            canvas.create_text(
                center_x, info_y_start + (i * line_height),
                text=detail_text, fill="#000000", font=("Inter", 12, "bold"), anchor="center"
            )
        
        # Close button
        close_button = Button(
            dialog,
            text="Close",
            font=("Inter", 12, "bold"),
            bg="#6c757d",
            fg="#FFFFFF",
            relief="flat",
            command=dialog.destroy
        )
        close_button.place(x=200, y=500, width=100, height=35)

    def edit_user(self, user):
        """Open edit user dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Edit User - {user['username']}")
        dialog.geometry("500x700")
        dialog.resizable(False, False)
        dialog.configure(bg="#FCECB7")
        
        # Center the dialog on screen
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the window on screen
        dialog.update_idletasks()
        width, height = 500, 700
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
            height=700,
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
        canvas.create_text(
            250.0, 65.0,
            text="Edit User",
            fill="#000000",
            font=("Inter", 16, "bold"),
            anchor="center"
        )
        
        # White background panel
        canvas.create_rectangle(
            25.0, 100.0, 475.0, 650.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # Form fields - centered layout like payment window
        center_x = 250.0  # Center of the dialog
        field_y_start = 130
        field_spacing = 70
        
        # Username field
        canvas.create_text(
            center_x, field_y_start,
            text="Username:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        username_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        username_entry.place(x=150, y=field_y_start + 20, width=200, height=30)
        username_entry.insert(0, user['username'])
        username_entry.config(state="readonly")
        
        # Email field
        canvas.create_text(
            center_x, field_y_start + field_spacing,
            text="Email:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        email_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        email_entry.place(x=150, y=field_y_start + field_spacing + 20, width=200, height=30)
        email_entry.insert(0, user['email'])
        
        # User Type field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 2),
            text="User Type:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        user_type_var = StringVar()
        user_type_combo = ttk.Combobox(dialog, textvariable=user_type_var, width=27, state="readonly")
        user_type_combo['values'] = ('student', 'admin', 'registrar', 'cashier')
        user_type_combo.place(x=150, y=field_y_start + (field_spacing * 2) + 20, width=200, height=30)
        user_type_var.set(user['user_type'])
        
        # Email Verified field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 3),
            text="Email Verified:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        verified_var = BooleanVar(value=user['is_verified'])  # Change to BooleanVar
        verified_check = Checkbutton(
            dialog, 
            variable=verified_var, 
            font=("Inter", 10), 
            bg="#FFFFFF",
            onvalue=True,
            offvalue=False
        )
        verified_check.place(x=center_x - 10, y=field_y_start + (field_spacing * 3) + 20, width=20, height=20)
        
        # Password fields
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 4),
            text="New Password:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        password_entry = Entry(dialog, font=("Inter", 10), width=30, show="*", justify="center", bg="#FFFFFF", relief="solid", bd=1)
        password_entry.place(x=150, y=field_y_start + (field_spacing * 4) + 20, width=200, height=30)
        
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 5),
            text="Confirm Password:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        confirm_password_entry = Entry(dialog, font=("Inter", 10), width=30, show="*", justify="center", bg="#FFFFFF", relief="solid", bd=1)
        confirm_password_entry.place(x=150, y=field_y_start + (field_spacing * 5) + 20, width=200, height=30)
        
        # Password update checkbox
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 6),
            text="Update Password:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        update_password_var = BooleanVar(value=True)  # Changed to True to make it checked by default
        update_password_check = Checkbutton(
            dialog, 
            text="Enable Password Update", 
            variable=update_password_var, 
            font=("Inter", 10), 
            bg="#FFFFFF",
            onvalue=True,
            offvalue=False
        )
        update_password_check.place(x=center_x - 90, y=field_y_start + (field_spacing * 6) + 20, width=180, height=20)
        
        # Buttons
        def save_user():
            email = email_entry.get().strip()
            user_type = user_type_var.get()
            is_verified = verified_var.get()  # Now directly using Boolean value
            new_password = password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            update_password = update_password_var.get()  # Now directly using Boolean value
            
            if not email:
                messagebox.showerror("Error", "Email is required")
                return
            
            # Validate password if updating
            if update_password:
                if not new_password:
                    messagebox.showerror("Error", "New password is required")
                    return
                if len(new_password) < 6:
                    messagebox.showerror("Error", "Password must be at least 6 characters long")
                    return
                if new_password != confirm_password:
                    messagebox.showerror("Error", "Passwords do not match")
                    return
            
            # Show loading indicator
            self.show_loading_indicator("Updating user...")
            
            # Use threading to avoid blocking UI
            def save_thread():
                try:
                    result = safe_async_run(self.update_user_async, user['user_id'], email, user_type, is_verified, new_password if update_password else None)
                except Exception as e:
                    print(f"❌ Error in async save_user: {e}")
                    result = None
                
                # Schedule UI update on main thread
                self.parent.after(0, lambda: self._update_ui_after_save(result, dialog))
            
            save_thread_obj = threading.Thread(target=save_thread, daemon=True)
            save_thread_obj.start()
        
        def cancel_form():
            dialog.destroy()
        
        # Save and Cancel buttons
        Button(dialog, text="Save", font=("Inter", 12, "bold"), bg="#28a745", fg="#FFFFFF", 
               relief="flat", command=save_user).place(x=140, y=600, width=100, height=35)
        Button(dialog, text="Cancel", font=("Inter", 12, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=cancel_form).place(x=260, y=600, width=100, height=35)
    
    def _update_ui_after_save(self, success, dialog):
        """Update UI after save operation completes"""
        try:
            self.hide_loading_indicator()
            if success:
                dialog.destroy()
                self.load_users()
                self.update_display()
            else:
                messagebox.showerror("Error", "Failed to update user")
        except Exception as e:
            print(f"❌ Error during UI update after save: {e}")

    async def update_user_async(self, user_id, email, user_type, is_verified, new_password=None):
        """Update user information in database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
                
            cursor = connection.cursor(dictionary=True)
            
            # Get old values for audit log
            cursor.execute("SELECT email, user_type, is_verified FROM users WHERE user_id = %s", (user_id,))
            old_data = cursor.fetchone()
            
            if new_password:
                # Import hashlib for password hashing
                import hashlib
                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                
                cursor.execute("""
                    UPDATE users 
                    SET email = %s, user_type = %s, is_verified = %s, password_hash = %s
                    WHERE user_id = %s
                """, (email, user_type, is_verified, hashed_password, user_id))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET email = %s, user_type = %s, is_verified = %s
                    WHERE user_id = %s
                """, (email, user_type, is_verified, user_id))
            
            # Get new values for audit log
            cursor.execute("SELECT email, user_type, is_verified FROM users WHERE user_id = %s", (user_id,))
            new_data = cursor.fetchone()
            
            connection.commit()
            
            # Log user update
            admin_user_id = self.user_data.get('user_id') if hasattr(self, 'user_data') and self.user_data else None
            if admin_user_id and old_data and new_data:
                old_values = dict(old_data)
                new_values = dict(new_data)
                if old_values != new_values:
                    audit_logger.log_update(
                        user_id=admin_user_id,
                        table_name='users',
                        record_id=user_id,
                        old_values=old_values,
                        new_values=new_values,
                        connection=connection
                    )
            
            cursor.close()
            connection.close()
            
            print(f"✅ Updated user: {email}")
            return True
            
        except Error as e:
            print(f"❌ Error updating user: {e}")
            return False

    def update_user(self, user_id, email, user_type, is_verified, new_password=None):
        """Update user information in database (sync wrapper)"""
        try:
            return safe_async_run(self.update_user_async, user_id, email, user_type, is_verified, new_password)
        except Exception as e:
            print(f"❌ Error in async update_user: {e}")
            return False

    async def toggle_user_status_async(self, user, new_status):
        """Change user active status (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # Get old status
            cursor.execute("SELECT is_active FROM users WHERE user_id = %s", (user['user_id'],))
            old_data = cursor.fetchone()
            old_status = old_data.get('is_active') if old_data else None
            
            cursor.execute("""
                UPDATE users 
                SET is_active = %s
                WHERE user_id = %s
            """, (new_status, user['user_id']))
            
            connection.commit()
            
            # Log status change
            admin_user_id = self.user_data.get('user_id') if hasattr(self, 'user_data') and self.user_data else None
            if admin_user_id and old_status is not None and old_status != new_status:
                audit_logger.log_update(
                    user_id=admin_user_id,
                    table_name='users',
                    record_id=user['user_id'],
                    old_values={'is_active': old_status},
                    new_values={'is_active': new_status},
                    connection=connection
                )
            
            cursor.close()
            connection.close()
            
            print(f"✅ User {user['username']} status changed to {'Active' if new_status else 'Inactive'}")
            await self.load_users_async()
            # Schedule UI update on main thread
            self.parent.after(0, self.update_display)
            
        except Error as e:
            print(f"❌ Error changing user status: {e}")
            messagebox.showerror("Database Error", f"Failed to update status: {str(e)}")

    def toggle_user_status(self, user, new_status):
        """Change user active status (sync wrapper)"""
        status_text = "deactivate" if not new_status else "activate"
        
        if messagebox.askyesno("Change Status", 
                             f"{status_text.title()} user {user['username']}?\n"
                             f"Email: {user['email']}\n"
                             f"Type: {user['user_type']}"):
            
            self.show_loading_indicator(f"{status_text.title()}ing user...")
            
            # Use threading to avoid blocking UI
            def toggle_status_thread():
                try:
                    safe_async_run(self.toggle_user_status_async, user, new_status)
                except Exception as e:
                    print(f"❌ Error in async toggle_user_status: {e}")
            
            toggle_status_thread_obj = threading.Thread(target=toggle_status_thread, daemon=True)
            toggle_status_thread_obj.start()

    def show_no_users_message(self):
        """Show message when no users exist"""
        self.canvas.create_text(
            450, 200, anchor="center", text="No users found",
            fill="#666666", font=("Inter", 14, "bold"), tags="row"
        )

    def update_navigation(self):
        """Update navigation elements"""
        total_pages = max(1, (len(self.filtered_users) + self.users_per_page - 1) // self.users_per_page)
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
        total_pages = max(1, (len(self.filtered_users) + self.users_per_page - 1) // self.users_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()

    def refresh_users(self):
        """Refresh the users list (async version)"""
        print("🔄 Refreshing users...")
        self.show_loading_indicator("Refreshing users...")
        
        # Use threading to avoid blocking UI
        def refresh_thread():
            try:
                safe_async_run(self.load_users_async)
            except Exception as e:
                print(f"❌ Error in async refresh_users: {e}")
            
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
            print(f"✅ Refresh complete - {len(self.users)} users loaded")
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

    def add_new_user(self):
        """Open add new user dialog"""
        dialog = Toplevel(self.parent)
        dialog.title("Add New User")
        dialog.geometry("500x700")
        dialog.resizable(False, False)
        dialog.configure(bg="#FCECB7")
        
        # Center the dialog on screen
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the window on screen
        dialog.update_idletasks()
        width, height = 500, 700
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
            height=700,
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
        canvas.create_text(
            250.0, 65.0,
            text="Add New User",
            fill="#000000",
            font=("Inter", 16, "bold"),
            anchor="center"
        )
        
        # White background panel
        canvas.create_rectangle(
            25.0, 100.0, 475.0, 650.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # Form fields - centered layout
        center_x = 250.0  # Center of the dialog
        field_y_start = 130
        field_spacing = 70
        
        # Username field
        canvas.create_text(
            center_x, field_y_start,
            text="Username:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        username_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        username_entry.place(x=150, y=field_y_start + 20, width=200, height=30)
        
        # Email field
        canvas.create_text(
            center_x, field_y_start + field_spacing,
            text="Email:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        email_entry = Entry(dialog, font=("Inter", 10), width=30, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        email_entry.place(x=150, y=field_y_start + field_spacing + 20, width=200, height=30)
        
        # User Type field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 2),
            text="User Type:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        user_type_var = StringVar()
        user_type_combo = ttk.Combobox(dialog, textvariable=user_type_var, width=27, state="readonly")
        user_type_combo['values'] = ('student', 'admin', 'registrar', 'cashier')
        user_type_combo.place(x=150, y=field_y_start + (field_spacing * 2) + 20, width=200, height=30)
        user_type_var.set('student')  # Default to student
        
        # Password field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 3),
            text="Password:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        password_entry = Entry(dialog, font=("Inter", 10), width=30, show="*", justify="center", bg="#FFFFFF", relief="solid", bd=1)
        password_entry.place(x=150, y=field_y_start + (field_spacing * 3) + 20, width=200, height=30)
        
        # Confirm Password field
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 4),
            text="Confirm Password:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        confirm_password_entry = Entry(dialog, font=("Inter", 10), width=30, show="*", justify="center", bg="#FFFFFF", relief="solid", bd=1)
        confirm_password_entry.place(x=150, y=field_y_start + (field_spacing * 4) + 20, width=200, height=30)
        
        # Email Verified checkbox
        canvas.create_text(
            center_x, field_y_start + (field_spacing * 5),
            text="Email Verified:", fill="#000000", font=("Inter", 12, "bold"), anchor="center"
        )
        verified_var = BooleanVar(value=False)
        verified_check = Checkbutton(
            dialog, 
            variable=verified_var, 
            font=("Inter", 10), 
            bg="#FFFFFF",
            onvalue=True,
            offvalue=False
        )
        verified_check.place(x=center_x - 10, y=field_y_start + (field_spacing * 5) + 20, width=20, height=20)
        
        # Buttons
        def save_new_user():
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            user_type = user_type_var.get()
            password = password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            is_verified = verified_var.get()
            
            # Validation
            if not username:
                messagebox.showerror("Error", "Username is required")
                return
            if not email:
                messagebox.showerror("Error", "Email is required")
                return
            if not password:
                messagebox.showerror("Error", "Password is required")
                return
            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters long")
                return
            if password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            # Show loading indicator
            self.show_loading_indicator("Creating user...")
            
            # Use threading to avoid blocking UI
            def create_thread():
                try:
                    result = self.create_user_async(username, email, user_type, password, is_verified)
                    # Schedule UI update on main thread
                    self.parent.after(0, lambda: self._update_ui_after_create(result, dialog))
                except Exception as e:
                    print(f"❌ Error creating user: {e}")
                    self.parent.after(0, lambda: self._update_ui_after_create(False, dialog))
            
            create_thread_obj = threading.Thread(target=create_thread, daemon=True)
            create_thread_obj.start()
        
        def cancel_form():
            dialog.destroy()
        
        # Save and Cancel buttons
        Button(dialog, text="Create User", font=("Inter", 12, "bold"), bg="#28a745", fg="#FFFFFF", 
               relief="flat", command=save_new_user).place(x=140, y=600, width=120, height=35)
        Button(dialog, text="Cancel", font=("Inter", 12, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=cancel_form).place(x=280, y=600, width=100, height=35)
    
    def create_user_async(self, username, email, user_type, password, is_verified):
        """Create new user in database"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Import hashlib for password hashing
            import hashlib
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # Check if username or email already exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", "Username or email already exists")
                return False
            
            cursor.execute("""
                INSERT INTO users (username, email, user_type, password_hash, is_active, is_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (username, email, user_type, hashed_password, True, is_verified))
            
            new_user_id = cursor.lastrowid
            connection.commit()
            
            # Log user creation
            admin_user_id = self.user_data.get('user_id') if hasattr(self, 'user_data') and self.user_data else None
            if admin_user_id:
                audit_logger.log_create(
                    user_id=admin_user_id,
                    table_name='users',
                    record_id=new_user_id,
                    new_values={
                        'username': username,
                        'email': email,
                        'user_type': user_type,
                        'is_active': True,
                        'is_verified': is_verified
                    },
                    connection=connection
                )
            
            cursor.close()
            connection.close()
            
            print(f"✅ Created new user: {username}")
            return True
            
        except Error as e:
            print(f"❌ Error creating user: {e}")
            messagebox.showerror("Database Error", f"Failed to create user: {str(e)}")
            return False
    
    def _update_ui_after_create(self, success, dialog):
        """Update UI after create operation completes"""
        try:
            self.hide_loading_indicator()
            if success:
                dialog.destroy()
                self.load_users()
                self.update_display()
                messagebox.showinfo("Success", "User created successfully!")
            else:
                messagebox.showerror("Error", "Failed to create user")
        except Exception as e:
            print(f"❌ Error during UI update after create: {e}")

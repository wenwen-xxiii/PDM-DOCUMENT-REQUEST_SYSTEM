# adminstudent.py - Admin Student Manager for Registrars
from pathlib import Path
from tkinter import Canvas, Frame, Label, Button, Entry, StringVar, messagebox, Scrollbar, Toplevel
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

class AdminStudentManager:
    def __init__(self, parent, get_db_connection=None, user_data=None):
        self.parent = parent
        self.get_db_connection = get_db_connection
        self.user_data = user_data or {}
        
        # Student data
        self.students = []
        self.filtered_students = []
        self.search_query = ""
        self.current_page = 1
        self.students_per_page = 9
        
        # UI element storage
        self.images = []
        self.row_widgets = []
        
        # Loading indicator
        self.loading_label = None
        
        self.setup_ui()
        self.load_students()
        self.update_display()
        
    def setup_ui(self):
        """Setup the student management UI inside the parent frame"""
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
        
        # Create action buttons (under search bar)
        self.create_action_buttons()
        
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
        self.search_entry.insert(0, "Search students...")
        # Simple placeholder behavior
        def _on_focus_in(event):
            if self.search_entry.get() == "Search students...":
                self.search_entry.delete(0, "end")
        def _on_focus_out(event):
            if not self.search_entry.get().strip():
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, "Search students...")
        self.search_entry.bind("<FocusIn>", _on_focus_in)
        self.search_entry.bind("<FocusOut>", _on_focus_out)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def create_title_label(self):
        """Create a title label in the top left"""
        self.title_label = Label(
            self.parent,
            text="Student Management",
            font=("Inter", 18, "bold"),
            bg="#FFFFFF",
            fg="#792D1B"
        )
        self.title_label.place(x=20, y=15)

    def create_action_buttons(self):
        """Create action buttons under the search bar"""
        # Add Student button
        self.button_add_student = Button(
            self.parent,
            text="Add Student",
            font=("Inter", 10, "bold"),
            bg="#28a745",
            fg="#FFFFFF",
            relief="flat",
            command=self.add_student
        )
        self.button_add_student.place(x=625, y=60, width=120, height=35)
        
        # Import CSV button
        self.button_import_csv = Button(
            self.parent,
            text="Import CSV",
            font=("Inter", 10, "bold"),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=self.import_csv_file
        )
        self.button_import_csv.place(x=755, y=60, width=120, height=35)

    def create_table_headers(self):
        """Create table header labels for students"""
        headers = [
            (40.0, "No.", "center"),
            (120.0, "Student No.", "center"),
            (260.0, "Name", "center"),
            (420.0, "Course", "center"),
            (560.0, "Year Level", "center"),
            (640.0, "Status", "center"),
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

    async def load_students_async(self):
        """Load students from database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    s.student_id,
                    s.student_number,
                    s.first_name,
                    s.last_name,
                    s.middle_name,
                    s.birth_date,
                    s.gender,
                    s.course,
                    s.year_level,
                    s.contact_number,
                    s.address,
                    s.enrollment_status,
                    s.date_enrolled,
                    s.has_obligations,
                    s.obligations_details,
                    u.email,
                    u.is_active,
                    u.last_login
                FROM students s
                LEFT JOIN users u ON s.user_id = u.user_id
                ORDER BY s.student_number ASC
            """)
            
            self.students = cursor.fetchall()
            # Default filtered list is full list
            self.filtered_students = list(self.students)
            
            cursor.close()
            connection.close()
            
            print(f"✅ Loaded {len(self.students)} students from database")
            
        except Error as e:
            print(f"❌ Error loading students: {e}")
            messagebox.showerror("Database Error", f"Failed to load students: {str(e)}")
            self.students = []

    def load_students(self):
        """Load students from database (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create a new one
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.load_students_async())
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async load_students: {e}")
                return asyncio.run(self.load_students_async())
        else:
            # Event loop exists, run in thread pool
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.load_students_async())
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async load_students: {e}")
                return asyncio.run(self.load_students_async())

    def update_display(self):
        """Update the display with current page data"""
        self.clear_table_rows()
        
        if not self.filtered_students:
            self.show_no_students_message()
            return
            
        self.display_current_students()
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

    def display_current_students(self):
        """Display students for current page"""
        start_idx = (self.current_page - 1) * self.students_per_page
        end_idx = start_idx + self.students_per_page
        current_students = self.filtered_students[start_idx:end_idx]
        
        for i, student in enumerate(current_students):
            self.create_table_row(i, student)

    def on_search_change(self, event=None):
        """Handle search text changes and filter the list"""
        query = self.search_entry.get().strip()
        # Ignore placeholder
        if query == "Search students...":
            query = ""
        self.search_query = query.lower()
        self.apply_search_filter()

    def apply_search_filter(self):
        """Filter students into filtered_students based on search_query"""
        if not self.search_query:
            self.filtered_students = list(self.students)
        else:
            q = self.search_query
            def matches(student):
                values = [
                    str(student.get('student_number', '')),
                    str(student.get('first_name', '')),
                    str(student.get('last_name', '')),
                    str(student.get('middle_name', '')),
                    str(student.get('course', '')),
                    str(student.get('year_level', '')),
                    str(student.get('enrollment_status', '')),
                    str(student.get('contact_number', '')),
                    str(student.get('email', '')),
                ]
                text = " ".join(values).lower()
                return q in text
            self.filtered_students = [s for s in self.students if matches(s)]
        # Reset to first page after filtering
        self.current_page = 1
        self.update_display()

    def create_table_row(self, row_index, student):
        """Create a table row with data and action buttons"""
        y_position = 160 + (row_index * 45)
        
        # Row background (alternating colors)
        fill_color = "#FFFFFF" if row_index % 2 == 0 else "#F8F8F8"
        self.canvas.create_rectangle(
            20, y_position, 875, y_position + 40, 
            fill=fill_color, outline="#E0E0E0", tags="row"
        )
        
        # Calculate row number (global index)
        row_number = ((self.current_page - 1) * self.students_per_page) + row_index + 1
        
        # Format student name
        full_name = f"{student['first_name']} {student['last_name']}"
        if student['middle_name']:
            full_name = f"{student['first_name']} {student['middle_name']} {student['last_name']}"
        
        # Status display with color coding
        status_text = student['enrollment_status']
        
        # Create text elements for the row with proper alignment
        text_configs = [
            (40.0, str(row_number), "center"),
            (120.0, student['student_number'], "center"),
            (260.0, full_name[:20] + "..." if len(full_name) > 20 else full_name, "center"),
            (420.0, student['course'][:25] + "..." if len(student['course']) > 25 else student['course'], "center"),
            (560.0, student['year_level'], "center"),
            (640.0, status_text, "center")
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
        self.create_row_buttons(row_index, student, y_position)

    def create_row_buttons(self, row_index, student, y_position):
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
            command=lambda s=student: self.view_student_details(s)
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
            command=lambda s=student: self.edit_student(s)
        )
        edit_button.place(x=740, y=y_position + 8, width=50, height=25)
        button_widgets.append(edit_button)
        
        # Status-specific action buttons
        enrollment_status = student['enrollment_status']
        
        if enrollment_status == 'Enrolled':
            # Deactivate button
            deactivate_button = Button(
                self.parent,
                text="Deactivate",
                font=("Inter", 9),
                bg="#dc3545",
                fg="#FFFFFF",
                relief="flat",
                command=lambda s=student: self.change_enrollment_status(s, 'Inactive')
            )
            deactivate_button.place(x=800, y=y_position + 8, width=70, height=25)
            button_widgets.append(deactivate_button)
            
        elif enrollment_status == 'Inactive':
            # Reactivate button
            reactivate_button = Button(
                self.parent,
                text="Reactivate",
                font=("Inter", 9),
                bg="#28a745",
                fg="#FFFFFF",
                relief="flat",
                command=lambda s=student: self.change_enrollment_status(s, 'Enrolled')
            )
            reactivate_button.place(x=800, y=y_position + 8, width=70, height=25)
            button_widgets.append(reactivate_button)
            
        else:
            # Disabled button for graduated/transferred
            disabled_button = Button(
                self.parent,
                text="N/A",
                font=("Inter", 9),
                bg="#CCCCCC",
                fg="#666666",
                relief="flat",
                state="disabled"
            )
            disabled_button.place(x=800, y=y_position + 8, width=70, height=25)
            button_widgets.append(disabled_button)
        
        self.row_widgets.append(button_widgets)

    def add_student(self):
        """Open add student dialog"""
        self.open_student_form()

    def import_csv_file(self):
        """Open CSV import dialog"""
        from tkinter import filedialog
        import csv
        
        # Open file dialog to select CSV file
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Read CSV file
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                rows = list(csv_reader)
            
            if not rows:
                messagebox.showerror("Error", "CSV file is empty")
                return
            
            # Show preview dialog
            self.show_csv_preview(rows, file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV file: {str(e)}")
    
    def show_csv_preview(self, rows, file_path):
        """Show CSV preview dialog"""
        dialog = Toplevel(self.parent)
        dialog.title("CSV Import Preview")
        dialog.geometry("800x600")
        dialog.resizable(True, True)
        dialog.configure(bg="#FCECB7")
        
        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the window on screen
        dialog.update_idletasks()
        width, height = 800, 600
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Force focus
        dialog.focus_force()
        dialog.lift()
        
        # Create canvas
        canvas = Canvas(
            dialog,
            bg="#FCECB7",
            height=600,
            width=800,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        canvas.place(x=0, y=0)
        
        # Header section
        canvas.create_rectangle(0.0, 0.0, 800.0, 80.0, fill="#792D1B", outline="")
        canvas.create_rectangle(0.0, 50.0, 800.0, 80.0, fill="#FFDA0C", outline="")
        
        # Header text
        canvas.create_text(
            400.0, 65.0,
            text="CSV Import Preview",
            fill="#000000",
            font=("Inter", 16, "bold"),
            anchor="center"
        )
        
        # White background panel
        canvas.create_rectangle(
            25.0, 100.0, 775.0, 500.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # File info
        canvas.create_text(
            400.0, 120.0,
            text=f"File: {file_path.split('/')[-1]} | Records: {len(rows)}",
            fill="#000000",
            font=("Inter", 12, "bold"),
            anchor="center"
        )
        
        # Create scrollable frame for preview
        from tkinter import Frame, Scrollbar
        
        preview_frame = Frame(dialog, bg="#FFFFFF")
        preview_frame.place(x=30, y=140, width=740, height=350)
        
        # Create scrollbar
        scrollbar = Scrollbar(preview_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        # Create text widget for preview
        from tkinter import Text
        preview_text = Text(
            preview_frame,
            font=("Courier", 9),
            bg="#FFFFFF",
            fg="#000000",
            wrap="none",
            yscrollcommand=scrollbar.set
        )
        preview_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=preview_text.yview)
        
        # Show first 10 rows as preview
        preview_content = "Column Headers:\n"
        if rows:
            headers = list(rows[0].keys())
            preview_content += " | ".join(headers) + "\n\n"
            preview_content += "Sample Data (first 10 rows):\n"
            
            for i, row in enumerate(rows[:10]):
                values = [str(row.get(header, '')) for header in headers]
                preview_content += f"Row {i+1}: {' | '.join(values)}\n"
            
            if len(rows) > 10:
                preview_content += f"\n... and {len(rows) - 10} more rows"
        
        preview_text.insert("1.0", preview_content)
        preview_text.config(state="disabled")
        
        # Import options
        canvas.create_text(
            400.0, 510.0,
            text="Import Options:",
            fill="#000000",
            font=("Inter", 12, "bold"),
            anchor="center"
        )
        
        # Checkboxes for import options
        from tkinter import Checkbutton, BooleanVar
        
        skip_duplicates_var = BooleanVar(value=True)
        skip_duplicates_check = Checkbutton(
            dialog,
            text="Skip duplicate student numbers",
            variable=skip_duplicates_var,
            font=("Inter", 10),
            bg="#FCECB7"
        )
        skip_duplicates_check.place(x=50, y=530, width=200, height=20)
        
        create_accounts_var = BooleanVar(value=True)
        create_accounts_check = Checkbutton(
            dialog,
            text="Create user accounts for students",
            variable=create_accounts_var,
            font=("Inter", 10),
            bg="#FCECB7"
        )
        create_accounts_check.place(x=300, y=530, width=200, height=20)
        
        # Buttons
        def start_import():
            dialog.destroy()
            self.process_csv_import(rows, skip_duplicates_var.get(), create_accounts_var.get())
        
        def cancel_import():
            dialog.destroy()
        
        Button(dialog, text="Import", font=("Inter", 12, "bold"), bg="#28a745", fg="#FFFFFF", 
               relief="flat", command=start_import).place(x=300, y=560, width=100, height=35)
        Button(dialog, text="Cancel", font=("Inter", 12, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=cancel_import).place(x=420, y=560, width=100, height=35)
    
    def process_csv_import(self, rows, skip_duplicates=True, create_accounts=True):
        """Process CSV import"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
            
            cursor = connection.cursor()
            
            imported_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            
            # Progress dialog
            progress_dialog = Toplevel(self.parent)
            progress_dialog.title("Importing CSV")
            progress_dialog.geometry("400x200")
            progress_dialog.resizable(False, False)
            progress_dialog.configure(bg="#FCECB7")
            
            # Center progress dialog
            progress_dialog.update_idletasks()
            width, height = 400, 200
            screen_width = progress_dialog.winfo_screenwidth()
            screen_height = progress_dialog.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            progress_dialog.geometry(f'{width}x{height}+{x}+{y}')
            
            progress_dialog.transient(self.parent)
            progress_dialog.grab_set()
            
            # Progress label
            progress_label = Label(
                progress_dialog,
                text="Processing CSV import...",
                font=("Inter", 12, "bold"),
                bg="#FCECB7",
                fg="#792D1B"
            )
            progress_label.pack(pady=20)
            
            # Progress bar (simple text-based)
            progress_text = Label(
                progress_dialog,
                text="",
                font=("Inter", 10),
                bg="#FCECB7",
                fg="#000000"
            )
            progress_text.pack(pady=10)
            
            progress_dialog.update()
            
            for i, row in enumerate(rows):
                try:
                    # Update progress
                    progress_text.config(text=f"Processing row {i+1} of {len(rows)}")
                    progress_dialog.update()
                    
                    # Extract data from CSV row
                    student_number = str(row.get('student_number', '')).strip()
                    first_name = str(row.get('first_name', '')).strip()
                    last_name = str(row.get('last_name', '')).strip()
                    middle_name = str(row.get('middle_name', '')).strip()
                    course = str(row.get('course', '')).strip()
                    year_level = str(row.get('year_level', '')).strip()
                    contact_number = str(row.get('contact_number', '')).strip()
                    address = str(row.get('address', '')).strip()
                    email = str(row.get('email', '')).strip()
                    
                    # Validate required fields
                    if not all([student_number, first_name, last_name, course, year_level]):
                        errors.append(f"Row {i+1}: Missing required fields")
                        error_count += 1
                        continue
                    
                    # Check for duplicates if skip_duplicates is True
                    if skip_duplicates:
                        cursor.execute("SELECT student_id FROM students WHERE student_number = %s", (student_number,))
                        if cursor.fetchone():
                            errors.append(f"Row {i+1}: Student number {student_number} already exists")
                            skipped_count += 1
                            continue
                    
                    # Create user account if requested
                    user_id = None
                    if create_accounts and email:
                        try:
                            cursor.execute("""
                                INSERT INTO users (username, email, password_hash, user_type, is_active, is_verified, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (student_number, email, 'default_password_hash', 'student', True, False, datetime.now()))
                            user_id = cursor.lastrowid
                        except Exception as e:
                            # User might already exist, continue without account
                            pass
                    
                    # Insert student record
                    cursor.execute("""
                        INSERT INTO students (user_id, student_number, first_name, last_name, middle_name, 
                                           course, year_level, contact_number, address, enrollment_status, 
                                           date_enrolled, has_obligations, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, student_number, first_name, last_name, middle_name, course, year_level, 
                          contact_number, address, 'Enrolled', datetime.now(), False, datetime.now()))
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
                    error_count += 1
            
            # Commit changes
            connection.commit()
            cursor.close()
            connection.close()
            
            # Close progress dialog
            progress_dialog.destroy()
            
            # Show results
            result_message = f"CSV Import Complete!\n\n"
            result_message += f"✅ Imported: {imported_count} students\n"
            result_message += f"⏭️ Skipped: {skipped_count} duplicates\n"
            result_message += f"❌ Errors: {error_count} rows\n\n"
            
            if errors:
                result_message += "Errors:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    result_message += f"\n... and {len(errors) - 10} more errors"
            
            messagebox.showinfo("Import Results", result_message)
            
            # Refresh the student list
            self.load_students()
            self.update_display()
            
        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.destroy()
            messagebox.showerror("Import Error", f"Failed to import CSV: {str(e)}")

    def open_student_form(self, student=None):
        """Open student form dialog"""
        dialog = Toplevel(self.parent)
        dialog.title("Add Student" if not student else f"Edit Student - {student['student_number']}")
        dialog.geometry("500x750")
        dialog.resizable(False, False)
        dialog.configure(bg="#FCECB7")
        
        # Center the dialog on screen
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the window on screen
        dialog.update_idletasks()
        width, height = 500, 750
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
            height=750,
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
        title_text = "Add Student" if not student else "Edit Student"
        canvas.create_text(
            250.0, 65.0,
            text=title_text,
            fill="#000000",
            font=("Inter", 16, "bold"),
            anchor="center"
        )
        
        # White background panel
        canvas.create_rectangle(
            25.0, 100.0, 475.0, 700.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # Form fields - two column layout with centered design
        field_y_start = 130
        field_spacing = 70
        left_column_x = 50
        right_column_x = 265
        field_width = 180
        
        # Left Column Fields
        # Student Number field
        canvas.create_text(
            left_column_x, field_y_start,
            text="Student Number:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        student_no_entry = Entry(dialog, font=("Inter", 10), width=20, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        student_no_entry.place(x=left_column_x, y=field_y_start + 20, width=field_width, height=30)
        
        # First Name field
        canvas.create_text(
            left_column_x, field_y_start + field_spacing,
            text="First Name:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        first_name_entry = Entry(dialog, font=("Inter", 10), width=20, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        first_name_entry.place(x=left_column_x, y=field_y_start + field_spacing + 20, width=field_width, height=30)
        
        # Last Name field
        canvas.create_text(
            left_column_x, field_y_start + (field_spacing * 2),
            text="Last Name:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        last_name_entry = Entry(dialog, font=("Inter", 10), width=20, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        last_name_entry.place(x=left_column_x, y=field_y_start + (field_spacing * 2) + 20, width=field_width, height=30)
        
        # Middle Name field
        canvas.create_text(
            left_column_x, field_y_start + (field_spacing * 3),
            text="Middle Name:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        middle_name_entry = Entry(dialog, font=("Inter", 10), width=20, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        middle_name_entry.place(x=left_column_x, y=field_y_start + (field_spacing * 3) + 20, width=field_width, height=30)
        
        # Course field
        canvas.create_text(
            left_column_x, field_y_start + (field_spacing * 4),
            text="Course:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        course_entry = Entry(dialog, font=("Inter", 10), width=20, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        course_entry.place(x=left_column_x, y=field_y_start + (field_spacing * 4) + 20, width=field_width, height=30)
        
        # Right Column Fields
        # Year Level field
        canvas.create_text(
            right_column_x, field_y_start,
            text="Year Level:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        from tkinter import ttk
        year_level_var = StringVar()
        year_level_combo = ttk.Combobox(dialog, textvariable=year_level_var, width=18, state="readonly")
        year_level_combo['values'] = ('1st Year', '2nd Year', '3rd Year', '4th Year', '5th Year')
        year_level_combo.place(x=right_column_x, y=field_y_start + 20, width=field_width, height=30)
        
        # Contact Number field
        canvas.create_text(
            right_column_x, field_y_start + field_spacing,
            text="Contact Number:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        contact_entry = Entry(dialog, font=("Inter", 10), width=20, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        contact_entry.place(x=right_column_x, y=field_y_start + field_spacing + 20, width=field_width, height=30)
        
        # Email field
        canvas.create_text(
            right_column_x, field_y_start + (field_spacing * 2),
            text="Email:", fill="#000000", font=("Inter", 11, "bold"), anchor="w"
        )
        email_entry = Entry(dialog, font=("Inter", 10), width=20, justify="center", bg="#FFFFFF", relief="solid", bd=1)
        email_entry.place(x=right_column_x, y=field_y_start + (field_spacing * 2) + 20, width=field_width, height=30)
        
        # Address field (spans both columns)
        canvas.create_text(
            250, field_y_start + (field_spacing * 5),
            text="Address:", fill="#000000", font=("Inter", 11, "bold"), anchor="center"
        )
        from tkinter import Text
        address_text = Text(dialog, font=("Inter", 10), width=35, height=3, bg="#FFFFFF", relief="solid", bd=1)
        address_text.place(x=80, y=field_y_start + (field_spacing * 5) + 20, width=340, height=60)
        
        # Populate fields if editing
        if student:
            student_no_entry.insert(0, student['student_number'])
            student_no_entry.config(state="readonly")
            first_name_entry.insert(0, student['first_name'])
            last_name_entry.insert(0, student['last_name'])
            middle_name_entry.insert(0, student['middle_name'] or "")
            course_entry.insert(0, student['course'])
            year_level_var.set(student['year_level'])
            contact_entry.insert(0, student['contact_number'] or "")
            address_text.insert("1.0", student['address'] or "")
            email_entry.insert(0, student['email'] or "")
        
        # Buttons
        def save_student():
            student_number = student_no_entry.get().strip()
            first_name = first_name_entry.get().strip()
            last_name = last_name_entry.get().strip()
            middle_name = middle_name_entry.get().strip()
            course = course_entry.get().strip()
            year_level = year_level_var.get()
            contact_number = contact_entry.get().strip()
            address = address_text.get("1.0", "end").strip()
            email = email_entry.get().strip()
            
            if not all([student_number, first_name, last_name, course, year_level]):
                messagebox.showerror("Error", "Student number, first name, last name, course, and year level are required")
                return
            
            # Show loading indicator
            self.show_loading_indicator("Saving student...")
            
            # Use threading to avoid blocking UI
            def save_thread():
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop running, create a new one
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            if student:
                                future = executor.submit(asyncio.run, self.update_student_async(student['student_id'], first_name, last_name, middle_name, course, year_level, contact_number, address))
                            else:
                                future = executor.submit(asyncio.run, self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))
                            result = future.result()
                    except Exception as e:
                        print(f"❌ Error in async save_student: {e}")
                        if student:
                            result = asyncio.run(self.update_student_async(student['student_id'], first_name, last_name, middle_name, course, year_level, contact_number, address))
                        else:
                            result = asyncio.run(self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))
                else:
                    # Event loop exists, run in thread pool
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            if student:
                                future = executor.submit(asyncio.run, self.update_student_async(student['student_id'], first_name, last_name, middle_name, course, year_level, contact_number, address))
                            else:
                                future = executor.submit(asyncio.run, self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))
                            result = future.result()
                    except Exception as e:
                        print(f"❌ Error in async save_student: {e}")
                        if student:
                            result = asyncio.run(self.update_student_async(student['student_id'], first_name, last_name, middle_name, course, year_level, contact_number, address))
                        else:
                            result = asyncio.run(self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))
                
                # Schedule UI update on main thread
                self.parent.after(0, lambda: self._update_ui_after_save(result, dialog))
            
            save_thread_obj = threading.Thread(target=save_thread, daemon=True)
            save_thread_obj.start()
        
        def cancel_form():
            dialog.destroy()
        
        # Save and Cancel buttons - centered
        Button(dialog, text="Save", font=("Inter", 12, "bold"), bg="#28a745", fg="#FFFFFF", 
               relief="flat", command=save_student).place(x=140, y=650, width=100, height=35)
        Button(dialog, text="Cancel", font=("Inter", 12, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=cancel_form).place(x=260, y=650, width=100, height=35)
    
    def _update_ui_after_save(self, success, dialog):
        """Update UI after save operation completes"""
        try:
            self.hide_loading_indicator()
            if success:
                dialog.destroy()
                self.load_students()
                self.update_display()
            else:
                messagebox.showerror("Error", "Failed to save student")
        except Exception as e:
            print(f"❌ Error during UI update after save: {e}")

    def view_student_details(self, student):
        """Open student details dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Student Details - {student['student_number']}")
        dialog.geometry("500x700")
        dialog.resizable(False, False)
        dialog.configure(bg="#FCECB7")
        
        # Center the dialog on screen
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the window on screen
        dialog.update_idletasks()
        width, height = 500, 720
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
            height=720,
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
            text="Student Details",
            fill="#000000",
            font=("Inter", 16, "bold"),
            anchor="center"
        )
        
        # White background panel
        canvas.create_rectangle(
            25.0, 100.0, 475.0, 700.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # Student information - centered layout
        info_y_start = 130
        line_height = 35
        center_x = 250.0  # Center of the dialog
        
        # Format student name
        full_name = f"{student['first_name']} {student['last_name']}"
        if student['middle_name']:
            full_name = f"{student['first_name']} {student['middle_name']} {student['last_name']}"
        
        info_labels = [
            ("Student Number:", student['student_number']),
            ("Full Name:", full_name),
            ("Birth Date:", student['birth_date'].strftime('%Y-%m-%d') if student['birth_date'] else "N/A"),
            ("Gender:", student['gender'] or "N/A"),
            ("Course:", student['course']),
            ("Year Level:", student['year_level']),
            ("Contact Number:", student['contact_number'] or "N/A"),
            ("Address:", student['address'] or "N/A"),
            ("Enrollment Status:", student['enrollment_status']),
            ("Date Enrolled:", student['date_enrolled'].strftime('%Y-%m-%d') if student['date_enrolled'] else "N/A"),
            ("Has Obligations:", "Yes" if student['has_obligations'] else "No"),
            ("Obligations Details:", student['obligations_details'] or "None"),
            ("Email:", student['email'] or "N/A"),
            ("Account Active:", "Yes" if student['is_active'] else "No"),
            ("Last Login:", student['last_login'].strftime('%Y-%m-%d %H:%M:%S') if student['last_login'] else "Never"),
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
        close_button.place(x=200, y=650, width=100, height=35)

    def edit_student(self, student):
        """Open edit student dialog"""
        self.open_student_form(student)

    async def update_student_async(self, student_id, first_name, last_name, middle_name, course, year_level, contact_number, address):
        """Update student information in database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE students 
                SET first_name = %s, last_name = %s, middle_name = %s, course = %s, 
                    year_level = %s, contact_number = %s, address = %s
                WHERE student_id = %s
            """, (first_name, last_name, middle_name, course, year_level, contact_number, address, student_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Updated student: {first_name} {last_name}")
            return True
            
        except Error as e:
            print(f"❌ Error updating student: {e}")
            return False

    def update_student(self, student_id, first_name, last_name, middle_name, course, year_level, contact_number, address):
        """Update student information in database (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create a new one
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.update_student_async(student_id, first_name, last_name, middle_name, course, year_level, contact_number, address))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async update_student: {e}")
                return asyncio.run(self.update_student_async(student_id, first_name, last_name, middle_name, course, year_level, contact_number, address))
        else:
            # Event loop exists, run in thread pool
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.update_student_async(student_id, first_name, last_name, middle_name, course, year_level, contact_number, address))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async update_student: {e}")
                return asyncio.run(self.update_student_async(student_id, first_name, last_name, middle_name, course, year_level, contact_number, address))

    async def add_new_student_async(self, student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email):
        """Add new student to database (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # First, create a user account for the student
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, user_type, is_active, is_verified, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (student_number, email, 'default_password_hash', 'student', True, False, datetime.now()))
            
            user_id = cursor.lastrowid
            
            # Then create the student record
            cursor.execute("""
                INSERT INTO students (user_id, student_number, first_name, last_name, middle_name, 
                                   course, year_level, contact_number, address, enrollment_status, 
                                   date_enrolled, has_obligations, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, student_number, first_name, last_name, middle_name, course, year_level, 
                  contact_number, address, 'Enrolled', datetime.now(), False, datetime.now()))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Added new student: {first_name} {last_name} ({student_number})")
            return True
            
        except Error as e:
            print(f"❌ Error adding student: {e}")
            return False

    def add_new_student(self, student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email):
        """Add new student to database (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop running, create a new one
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async add_new_student: {e}")
                return asyncio.run(self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))
        else:
            # Event loop exists, run in thread pool
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))
                    return future.result()
            except Exception as e:
                print(f"❌ Error in async add_new_student: {e}")
                return asyncio.run(self.add_new_student_async(student_number, first_name, last_name, middle_name, course, year_level, contact_number, address, email))

    async def change_enrollment_status_async(self, student, new_status):
        """Change student enrollment status (async version)"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE students 
                SET enrollment_status = %s
                WHERE student_id = %s
            """, (new_status, student['student_id']))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Student {student['student_number']} status changed to {new_status}")
            await self.load_students_async()
            # Schedule UI update on main thread
            self.parent.after(0, self.update_display)
            
        except Error as e:
            print(f"❌ Error changing student status: {e}")
            messagebox.showerror("Database Error", f"Failed to update status: {str(e)}")

    def change_enrollment_status(self, student, new_status):
        """Change student enrollment status (sync wrapper)"""
        status_text = "deactivate" if new_status == 'Inactive' else "reactivate"
        
        if messagebox.askyesno("Change Status", 
                             f"{status_text.title()} student {student['student_number']}?\n"
                             f"Name: {student['first_name']} {student['last_name']}\n"
                             f"Course: {student['course']}"):
            
            self.show_loading_indicator(f"{status_text.title()}ing student...")
            
            # Use threading to avoid blocking UI
            def change_status_thread():
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # No event loop running, create a new one
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self.change_enrollment_status_async(student, new_status))
                            return future.result()
                    except Exception as e:
                        print(f"❌ Error in async change_enrollment_status: {e}")
                        return asyncio.run(self.change_enrollment_status_async(student, new_status))
                else:
                    # Event loop exists, run in thread pool
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self.change_enrollment_status_async(student, new_status))
                            return future.result()
                    except Exception as e:
                        print(f"❌ Error in async change_enrollment_status: {e}")
                        return asyncio.run(self.change_enrollment_status_async(student, new_status))
            
            change_status_thread_obj = threading.Thread(target=change_status_thread, daemon=True)
            change_status_thread_obj.start()

    def show_no_students_message(self):
        """Show message when no students exist"""
        self.canvas.create_text(
            450, 200, anchor="center", text="No students found",
            fill="#666666", font=("Inter", 14, "bold"), tags="row"
        )

    def update_navigation(self):
        """Update navigation elements"""
        total_pages = max(1, (len(self.filtered_students) + self.students_per_page - 1) // self.students_per_page)
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
        total_pages = max(1, (len(self.filtered_students) + self.students_per_page - 1) // self.students_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()

    def refresh_students(self):
        """Refresh the students list (async version)"""
        print("🔄 Refreshing students...")
        self.show_loading_indicator("Refreshing students...")
        
        # Use threading to avoid blocking UI
        def refresh_thread():
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop running, create a new one
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.load_students_async())
                        result = future.result()
                except Exception as e:
                    print(f"❌ Error in async refresh_students: {e}")
                    result = asyncio.run(self.load_students_async())
            else:
                # Event loop exists, run in thread pool
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.load_students_async())
                        result = future.result()
                except Exception as e:
                    print(f"❌ Error in async refresh_students: {e}")
                    result = asyncio.run(self.load_students_async())
            
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
            print(f"✅ Refresh complete - {len(self.students)} students loaded")
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

# adminstudent.py - Admin Student Manager for Registrars
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
        
        # Create table header
        self.create_table_headers()
        
        # Create navigation controls
        self.create_navigation_controls()
        
    def create_searchbar(self):
        """Create a search entry at the top with more space"""
        # Search entry positioned at the top with more space
        self.search_entry = Entry(
            self.parent,
            bd=1,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=1,
            font=("Inter", 12)
        )
        # Place at the top, centered with more space
        self.search_entry.place(x=20, y=15, width=400, height=30)
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
        self.canvas.create_rectangle(20, 60, 875, 100, fill="#792D1B", outline="")
        
        for x, text, anchor in headers:
            self.canvas.create_text(
                x, 80, 
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

    def load_students(self):
        """Load students from database"""
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
        y_position = 110 + (row_index * 45)
        
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

    def view_student_details(self, student):
        """Open student details dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Student Details - {student['student_number']}")
        dialog.geometry("500x700")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Student details
        details_frame = Frame(dialog, bg="#FFFFFF")
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = Label(details_frame, text="Student Details", 
                           font=("Inter", 16, "bold"), bg="#FFFFFF", fg="#792D1B")
        title_label.pack(pady=(0, 20))
        
        # Student information
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
        
        for label_text, value_text in info_labels:
            frame = Frame(details_frame, bg="#FFFFFF")
            frame.pack(fill="x", pady=3)
            
            label = Label(frame, text=label_text, font=("Inter", 10, "bold"), 
                         bg="#FFFFFF", fg="#333333", width=20, anchor="w")
            label.pack(side="left")
            
            value = Label(frame, text=value_text, font=("Inter", 10), 
                         bg="#FFFFFF", fg="#666666", anchor="w", wraplength=300)
            value.pack(side="left", padx=(10, 0))
        
        # Close button
        Button(dialog, text="Close", font=("Inter", 10, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=dialog.destroy).pack(pady=20)

    def edit_student(self, student):
        """Open edit student dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Edit Student - {student['student_number']}")
        dialog.geometry("400x600")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Form fields
        Label(dialog, text="Student Number:", font=("Inter", 10, "bold")).place(x=20, y=20)
        student_no_entry = Entry(dialog, font=("Inter", 10), width=30)
        student_no_entry.place(x=20, y=45)
        student_no_entry.insert(0, student['student_number'])
        student_no_entry.config(state="readonly")
        
        Label(dialog, text="First Name:", font=("Inter", 10, "bold")).place(x=20, y=80)
        first_name_entry = Entry(dialog, font=("Inter", 10), width=30)
        first_name_entry.place(x=20, y=105)
        first_name_entry.insert(0, student['first_name'])
        
        Label(dialog, text="Last Name:", font=("Inter", 10, "bold")).place(x=20, y=140)
        last_name_entry = Entry(dialog, font=("Inter", 10), width=30)
        last_name_entry.place(x=20, y=165)
        last_name_entry.insert(0, student['last_name'])
        
        Label(dialog, text="Middle Name:", font=("Inter", 10, "bold")).place(x=20, y=200)
        middle_name_entry = Entry(dialog, font=("Inter", 10), width=30)
        middle_name_entry.place(x=20, y=225)
        middle_name_entry.insert(0, student['middle_name'] or "")
        
        Label(dialog, text="Course:", font=("Inter", 10, "bold")).place(x=20, y=260)
        course_entry = Entry(dialog, font=("Inter", 10), width=30)
        course_entry.place(x=20, y=285)
        course_entry.insert(0, student['course'])
        
        Label(dialog, text="Year Level:", font=("Inter", 10, "bold")).place(x=20, y=320)
        from tkinter import ttk
        year_level_var = StringVar()
        year_level_combo = ttk.Combobox(dialog, textvariable=year_level_var, width=27, state="readonly")
        year_level_combo['values'] = ('1st Year', '2nd Year', '3rd Year', '4th Year', '5th Year')
        year_level_combo.place(x=20, y=345)
        year_level_var.set(student['year_level'])
        
        Label(dialog, text="Contact Number:", font=("Inter", 10, "bold")).place(x=20, y=380)
        contact_entry = Entry(dialog, font=("Inter", 10), width=30)
        contact_entry.place(x=20, y=405)
        contact_entry.insert(0, student['contact_number'] or "")
        
        Label(dialog, text="Address:", font=("Inter", 10, "bold")).place(x=20, y=440)
        from tkinter import Text
        address_text = Text(dialog, font=("Inter", 10), width=35, height=3)
        address_text.place(x=20, y=465)
        address_text.insert("1.0", student['address'] or "")
        
        # Buttons
        def save_student():
            first_name = first_name_entry.get().strip()
            last_name = last_name_entry.get().strip()
            middle_name = middle_name_entry.get().strip()
            course = course_entry.get().strip()
            year_level = year_level_var.get()
            contact_number = contact_entry.get().strip()
            address = address_text.get("1.0", "end").strip()
            
            if not all([first_name, last_name, course, year_level]):
                messagebox.showerror("Error", "First name, last name, course, and year level are required")
                return
            
            success = self.update_student(student['student_id'], first_name, last_name, middle_name, 
                                        course, year_level, contact_number, address)
            
            if success:
                dialog.destroy()
                self.load_students()
                self.update_display()
            else:
                messagebox.showerror("Error", "Failed to update student")
        
        def cancel_form():
            dialog.destroy()
        
        Button(dialog, text="Save", font=("Inter", 10, "bold"), bg="#28a745", fg="#FFFFFF", 
               relief="flat", command=save_student).place(x=20, y=550, width=100, height=35)
        Button(dialog, text="Cancel", font=("Inter", 10, "bold"), bg="#6c757d", fg="#FFFFFF", 
               relief="flat", command=cancel_form).place(x=140, y=550, width=100, height=35)

    def update_student(self, student_id, first_name, last_name, middle_name, course, year_level, contact_number, address):
        """Update student information in database"""
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

    def change_enrollment_status(self, student, new_status):
        """Change student enrollment status"""
        status_text = "deactivate" if new_status == 'Inactive' else "reactivate"
        
        if messagebox.askyesno("Change Status", 
                             f"{status_text.title()} student {student['student_number']}?\n"
                             f"Name: {student['first_name']} {student['last_name']}\n"
                             f"Course: {student['course']}"):
            
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
                self.load_students()
                self.update_display()
                
            except Error as e:
                print(f"❌ Error changing student status: {e}")
                messagebox.showerror("Database Error", f"Failed to update status: {str(e)}")

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
        """Refresh the students list"""
        print("🔄 Refreshing students...")
        try:
            self.load_students()
            self.current_page = 1
            self.update_display()
            print(f"✅ Refresh complete - {len(self.students)} students loaded")
        except Exception as e:
            print(f"❌ Error during refresh: {e}")

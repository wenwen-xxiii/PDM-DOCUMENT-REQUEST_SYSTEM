from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, messagebox
import mysql.connector
from utils import UtilityFunctions, EmailService
from otp import OTPVerificationWindow
import sys
import os

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/frame1/{path}"))

class SignupWindow:
    def __init__(self, parent, show_login_callback, get_db_connection):
        self.parent = parent
        self.show_login_callback = show_login_callback
        self.get_db_connection = get_db_connection
        self.otp_code = None
        self.user_data = None
        
        # Placeholder texts
        self.email_placeholder = "example@pdm.edu.ph"
        self.studentno_placeholder = "PDM-2025-001234"
        
        self.setup_ui()
        
    def setup_ui(self):
        self.canvas = Canvas(
            self.parent,
            bg="#FFFFFF",
            height=400,
            width=670,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        
        # Background and design elements
        self.canvas.create_rectangle(0.0, 0.0, 670.0, 400.0, fill="#FFA500", outline="")
        self.canvas.create_rectangle(0.0, 0.0, 335.0, 400.0, fill="#800000", outline="")
        
        self.canvas.create_text(
            51.0, 293.0, anchor="nw",
            text="Where quality education is a right, not privilege.",
            fill="#FFFFFF", font=("Inter Italic", 10 * -1)
        )
        
        self.canvas.create_text(
            41.0, 263.0, anchor="nw",
            text="PAMBAYANG DALUBHASAAN NG MARILAO",
            fill="#FFD700", font=("Inter Bold", 12 * -1)
        )

        # Logo
        self.image_image_1 = PhotoImage(file=relative_to_assets("image_logo.png"))
        self.canvas.create_image(164.0, 171.0, image=self.image_image_1)

        # Form labels and entries
        self.canvas.create_text(
            383.0, 151.0, anchor="nw",
            text="Password",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        # Email entry
        self.entry_image_1 = PhotoImage(file=relative_to_assets("entry_email.png"))
        self.canvas.create_image(505.5, 121.0, image=self.entry_image_1)
        self.entry_email = Entry(
            bd=0, bg="#F5C56E", fg="#666666", highlightthickness=0,  # Lighter gray for placeholder
            font=("Inter", 12)
        )
        self.entry_email.place(x=391.0, y=101.0, width=229.0, height=38.0)
        # Add email placeholder
        self.entry_email.insert(0, self.email_placeholder)
        self.entry_email.bind('<FocusIn>', lambda e: self.clear_placeholder(self.entry_email, self.email_placeholder))
        self.entry_email.bind('<FocusOut>', lambda e: self.restore_placeholder(self.entry_email, self.email_placeholder))

        self.canvas.create_text(
            383.0, 79.0, anchor="nw",
            text="Email",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        self.canvas.create_text(
            378.0, 24.0, anchor="nw",
            text="Signup",
            fill="#FFFFFF", font=("Inter Bold", 32 * -1)
        )

        # Password entry
        self.entry_image_2 = PhotoImage(file=relative_to_assets("entry_pass.png"))
        self.canvas.create_image(505.5, 193.0, image=self.entry_image_2)
        self.entry_pass = Entry(
            bd=0, bg="#F5C56E", fg="#000716", highlightthickness=0,
            show="*", font=("Inter", 12)
        )
        self.entry_pass.place(x=391.0, y=173.0, width=229.0, height=38.0)

        self.canvas.create_text(
            383.0, 222.0, anchor="nw",
            text="Student No.",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        # Student number entry
        self.entry_image_3 = PhotoImage(file=relative_to_assets("entry_studentno.png"))
        self.canvas.create_image(505.5, 264.0, image=self.entry_image_3)
        self.entry_studentno = Entry(
            bd=0, bg="#F5C56E", fg="#666666", highlightthickness=0,  # Lighter gray for placeholder
            font=("Inter", 12)
        )
        self.entry_studentno.place(x=391.0, y=244.0, width=229.0, height=38.0)
        # Add student number placeholder and format validation
        self.entry_studentno.insert(0, self.studentno_placeholder)
        self.entry_studentno.bind('<FocusIn>', lambda e: self.clear_placeholder(self.entry_studentno, self.studentno_placeholder))
        self.entry_studentno.bind('<FocusOut>', lambda e: self.restore_placeholder(self.entry_studentno, self.studentno_placeholder))
        self.entry_studentno.bind('<KeyRelease>', self.validate_student_number_format)
        
        # Signup button
        self.button_image_1 = PhotoImage(file=relative_to_assets("button_signup.png"))
        self.button_signup = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.attempt_signup,
            relief="flat"
        )
        self.button_signup.place(x=383.0, y=303.0, width=245.0, height=40.0)

        # Login link button
        self.button_image_2 = PhotoImage(file=relative_to_assets("buttonLbl_login.png"))
        self.buttonLbl_login = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_login_callback,
            relief="flat"
        )
        self.buttonLbl_login.place(x=412.0, y=350.0, width=187.0, height=18.0)

    def clear_placeholder(self, entry, placeholder_text):
        """Clear placeholder text when entry is focused"""
        if entry.get() == placeholder_text:
            entry.delete(0, 'end')
            entry.config(fg="#000716")  # Normal text color
            if entry == self.entry_pass:
                entry.config(show="*")

    def restore_placeholder(self, entry, placeholder_text):
        """Restore placeholder text when entry loses focus and is empty"""
        if entry.get().strip() == "":
            entry.insert(0, placeholder_text)
            entry.config(fg="#666666")  # Lighter gray for placeholder
            if entry == self.entry_pass:
                entry.config(show="")  # Show placeholder text clearly

    def validate_student_number_format(self, event=None):
        """Validate student number format in real-time"""
        student_number = self.entry_studentno.get().strip()
        
        # Skip validation if it's placeholder text
        if student_number == self.studentno_placeholder:
            return
        
        # Auto-format as user types
        if len(student_number) > 0:
            # Remove any existing hyphens and convert to uppercase
            cleaned = student_number.replace('-', '').upper()
            
            # Auto-format: PDM-YYYY-NNNNNN
            if cleaned.startswith('PDM') and len(cleaned) > 3:
                year_part = cleaned[3:7] if len(cleaned) > 7 else cleaned[3:]
                number_part = cleaned[7:13] if len(cleaned) > 7 else ""
                
                formatted = f"PDM-{year_part}"
                if number_part:
                    formatted += f"-{number_part}"
                
                # Prevent infinite loop by checking if change is needed
                if formatted != student_number:
                    current_pos = self.entry_studentno.index('insert')
                    self.entry_studentno.delete(0, 'end')
                    self.entry_studentno.insert(0, formatted)
                    # Try to maintain cursor position
                    try:
                        self.entry_studentno.icursor(min(current_pos, len(formatted)))
                    except:
                        pass
            
            # Validate format and change text color accordingly
            if student_number and student_number != self.studentno_placeholder:
                if self.is_valid_pdm_student_number(student_number):
                    self.entry_studentno.config(fg="#006400")  # Dark green for valid
                else:
                    self.entry_studentno.config(fg="#8B0000")  # Dark red for invalid

    def is_valid_pdm_student_number(self, student_number):
        """Validate PDM student number format: PDM-YYYY-NNNNNN"""
        import re
        # Pattern: PDM- followed by 4 digits, then hyphen, then 6 digits
        pattern = r'^PDM-\d{4}-\d{6}$'
        return re.match(pattern, student_number.upper()) is not None

    def attempt_signup(self):
        email = self.entry_email.get().strip()
        password = self.entry_pass.get().strip()
        student_number = self.entry_studentno.get().strip().upper()

        # Remove placeholder values if they weren't changed
        if email == self.email_placeholder:
            email = ""
        if student_number == self.studentno_placeholder:
            student_number = ""

        # Validation
        if not all([email, password, student_number]):
            messagebox.showerror("Error", "Please fill in all fields")
            # Restore placeholders for empty fields
            if not email:
                self.restore_placeholder(self.entry_email, self.email_placeholder)
            if not student_number:
                self.restore_placeholder(self.entry_studentno, self.studentno_placeholder)
            return

        if not UtilityFunctions.is_valid_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            self.entry_email.focus()
            return

        # Use the new PDM-specific validation
        if not self.is_valid_pdm_student_number(student_number):
            messagebox.showerror("Error", "Please enter a valid student number in format: PDM-YYYY-NNNNNN\n\nExample: PDM-2025-001234")
            self.entry_studentno.focus()
            return

        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            self.entry_pass.focus()
            return

        db_connection = self.get_db_connection()
        if not db_connection:
            messagebox.showerror("Database Error", "Cannot connect to database")
            return

        try:
            cursor = db_connection.cursor(dictionary=True)

            # Check if email or username already exists in users table
            cursor.execute(
                "SELECT * FROM users WHERE email = %s OR username = %s",
                (email, student_number)
            )
            existing_user = cursor.fetchone()

            if existing_user:
                messagebox.showerror("Error", "Email or student number already registered")
                return

            # Check if student number already exists in students table
            cursor.execute(
                "SELECT * FROM students WHERE student_number = %s",
                (student_number,)
            )
            existing_student = cursor.fetchone()

            if existing_student:
                messagebox.showerror("Error", "Student number already registered")
                return

            # Generate OTP and store temporary user data
            self.otp_code = UtilityFunctions.generate_otp()
            self.user_data = {
                'email': email,
                'password': password,
                'student_number': student_number,
                'username': student_number  # Use student number as username
            }

            # Send OTP email
            email_service = EmailService()
            if email_service.send_otp_email(email, self.otp_code):
                self.show_otp_verification()
            else:
                messagebox.showerror("Error", "Failed to send OTP. Please try again.")

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Registration failed: {str(e)}")
        finally:
            if db_connection and db_connection.is_connected():
                cursor.close()

    def show_otp_verification(self):
        """Show OTP verification window"""
        self.destroy()
        OTPVerificationWindow(
            self.parent, 
            self.user_data, 
            self.otp_code, 
            self.complete_registration,
            self.show_login_callback,
            self.get_db_connection
        )

    def complete_registration(self):
        """Complete the registration process with proper transaction handling"""
        db_connection = self.get_db_connection()
        if not db_connection or not self.user_data:
            messagebox.showerror("Error", "Registration failed")
            return

        cursor = None
        try:
            cursor = db_connection.cursor()
            
            # Check if there's an active transaction and rollback if needed
            try:
                if db_connection.in_transaction:
                    db_connection.rollback()
                    print("✓ Rolled back existing transaction")
            except:
                pass  # Some MySQL connectors don't have in_transaction attribute
            
            # Hash password
            hashed_password = UtilityFunctions.hash_password(self.user_data['password'])
            
            # Start fresh transaction
            db_connection.start_transaction()
            
            # 1. Insert into users table (authentication)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, user_type, is_verified) 
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.user_data['username'],
                self.user_data['email'],
                hashed_password,
                'student',
                True
            ))
            
            user_id = cursor.lastrowid
            
            # Extract year from student number (PDM-2025-001234 -> 2025)
            try:
                admission_year = self.user_data['student_number'].split('-')[1]
                # Convert to actual date for date_enrolled
                from datetime import datetime
                enrollment_date = datetime(int(admission_year), 6, 1)  # June 1st of admission year
                expected_graduation = datetime(int(admission_year) + 4, 6, 1)  # 4 years later
            except (IndexError, ValueError):
                admission_year = "2024"  # Default fallback
                enrollment_date = datetime.now()
                expected_graduation = datetime.now().replace(year=datetime.now().year + 4)
            
            # 2. Insert into students table with normalized structure
            cursor.execute("""
                INSERT INTO students (
                    user_id, student_number, first_name, last_name, middle_name,
                    course, year_level, enrollment_status, date_enrolled, expected_graduation
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                self.user_data['student_number'],
                self.user_data.get('first_name', 'New'),  # Use provided name or placeholder
                self.user_data.get('last_name', 'Student'),  # Use provided name or placeholder
                self.user_data.get('middle_name', ''),  # Middle name if provided
                self.user_data.get('course', 'Undecided'),  # Course if provided
                self.user_data.get('year_level', '1st Year'),  # Year level if provided
                'Active',
                enrollment_date,
                expected_graduation
            ))
            
            # 3. Insert initial academic record
            cursor.execute("""
                INSERT INTO academic_records (
                    student_id, course, year_level, semester, academic_year, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                cursor.lastrowid,  # This gets the student ID just inserted
                self.user_data.get('course', 'Undecided'),
                self.user_data.get('year_level', '1st Year'),
                '1st',  # Default semester
                f"{admission_year}-{int(admission_year)+1}",  # Academic year format: 2024-2025
                'Regular'
            ))
            
            db_connection.commit()
            
            # Show success message with login instructions
            success_message = f"""
            Registration completed successfully!

            Student Information:
            • Name: {self.user_data.get('first_name', 'New')} {self.user_data.get('last_name', 'Student')}
            • Student Number: {self.user_data['student_number']}
            • Email: {self.user_data['email']}
            • Username: {self.user_data['username']}

            Please complete your profile information after login.
            You can now login using your student number or email.
            """
            
            messagebox.showinfo("Success", success_message.strip())
            self.show_login_callback()
            
        except mysql.connector.Error as e:
            try:
                db_connection.rollback()
                print("✓ Transaction rolled back due to error")
            except:
                pass
            
            error_message = f"Registration failed: {str(e)}"
            if "Duplicate entry" in str(e):
                if "email" in str(e):
                    error_message = "Email already registered. Please use a different email address."
                elif "student_number" in str(e):
                    error_message = "Student number already registered. Please contact the registrar if this is an error."
                elif "username" in str(e):
                    error_message = "Username already taken. Please choose a different username."
                elif "users.username" in str(e):
                    error_message = "Username already taken. Please choose a different username."
                elif "users.email" in str(e):
                    error_message = "Email already registered. Please use a different email address."
                elif "students.student_number" in str(e):
                    error_message = "Student number already registered. Please contact the registrar if this is an error."
            
            messagebox.showerror("Registration Error", error_message)
            
        except Exception as e:
            try:
                db_connection.rollback()
                print("✓ Transaction rolled back due to unexpected error")
            except:
                pass
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
            
        finally:
            if cursor:
                cursor.close()
            
    def destroy(self):
        """Clean up the window"""
        for widget in self.parent.winfo_children():
            widget.destroy()
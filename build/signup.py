# signup.py
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, messagebox
import mysql.connector
from utils import UtilityFunctions, EmailService
from otp import OTPVerificationWindow
import sys
import os
import re
from datetime import datetime

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/{path}"))

class SignupWindow:
    def __init__(self, parent, show_login_callback, get_db_connection):
        self.parent = parent
        self.show_login_callback = show_login_callback
        self.get_db_connection = get_db_connection
        self.otp_code = None
        self.user_data = None
        
        # Placeholder texts
        self.email_placeholder = "example@gmail.com"
        self.studentno_placeholder = "PDM-2025-001234"
        
        self.button_hidden_img = PhotoImage(file=relative_to_assets("button_hidden.png"))   
        self.button_view_img = PhotoImage(file=relative_to_assets("button_view.png"))
        
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
            bd=0, bg="#F5C56E", fg="#666666", highlightthickness=0,
            font=("Inter", 12)
        )
        self.entry_email.place(x=391.0, y=101.0, width=229.0, height=38.0)
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
            show="●", font=("Inter", 12)
        )
        self.entry_pass.place(x=391.0, y=173.0, width=229.0, height=38.0)

        self.canvas.create_text(
            383.0, 222.0, anchor="nw",
            text="Student No.",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )
        
        # Password toggle button
        self.button_toggle_pass = Button(
            image=self.button_view_img,
            borderwidth=0, highlightthickness=0,
            command=lambda: self.toggle_password_visibility(self.entry_pass, self.button_toggle_pass),
            relief="flat", cursor="hand2"
        )
        self.button_toggle_pass.place(x=600.0, y=183.0, width=20.0, height=19.0)

        # Student number entry
        self.entry_image_3 = PhotoImage(file=relative_to_assets("entry_studentno.png"))
        self.canvas.create_image(505.5, 264.0, image=self.entry_image_3)
        self.entry_studentno = Entry(
            bd=0, bg="#F5C56E", fg="#666666", highlightthickness=0,
            font=("Inter", 12)
        )
        self.entry_studentno.place(x=391.0, y=244.0, width=229.0, height=38.0)
        self.entry_studentno.insert(0, self.studentno_placeholder)
        self.entry_studentno.bind('<FocusIn>', lambda e: self.clear_placeholder(self.entry_studentno, self.studentno_placeholder))
        self.entry_studentno.bind('<FocusOut>', lambda e: self.restore_placeholder(self.entry_studentno, self.studentno_placeholder))
        self.entry_studentno.bind('<KeyRelease>', self.force_uppercase_and_validate)
        
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

    def toggle_password_visibility(self, entry_widget, button_widget):
        """Toggle the visibility of the password field"""
        if entry_widget.cget('show') == "●":
            entry_widget.config(show="")
            button_widget.config(image=self.button_hidden_img)
        else:
            entry_widget.config(show="●")
            button_widget.config(image=self.button_view_img)
            
    def clear_placeholder(self, entry, placeholder_text):
        """Clear placeholder text when entry is focused"""
        if entry.get() == placeholder_text:
            entry.delete(0, 'end')
            entry.config(fg="#000716")
            if entry == self.entry_pass:
                entry.config(show="*")

    def restore_placeholder(self, entry, placeholder_text):
        """Restore placeholder text when entry loses focus and is empty"""
        if entry.get().strip() == "":
            entry.insert(0, placeholder_text)
            entry.config(fg="#666666")
            if entry == self.entry_pass:
                entry.config(show="")

    def is_valid_pdm_student_number(self, student_number):
        """Validate PDM student number format: PDM-YYYY-NNNNNN"""
        pattern = r'^PDM-\d{4}-\d{6}$'
        return re.match(pattern, student_number.upper()) is not None
    
    def force_uppercase_and_validate(self, event=None):
        """Force uppercase and run validation"""
        current_text = self.entry_studentno.get()
        upper_text = current_text.upper()

        if current_text != upper_text:
            cursor_pos = self.entry_studentno.index("insert")
            self.entry_studentno.delete(0, "end")
            self.entry_studentno.insert(0, upper_text)
            try:
                self.entry_studentno.icursor(cursor_pos)
            except:
                self.entry_studentno.icursor("end")

        self.validate_student_number_format()

    def validate_student_number_format(self, event=None):
        """Validate student number format in real-time"""
        student_number = self.entry_studentno.get().strip()

        if student_number == self.studentno_placeholder:
            return

        if len(student_number) > 0:
            student_number = student_number.upper()
            cleaned = re.sub(r'[^A-Z0-9-]', '', student_number)
            raw = cleaned.replace("-", "")

            if raw.startswith("PDM") and len(raw) > 3:
                year_part = raw[3:7] if len(raw) > 7 else raw[3:]
                number_part = raw[7:13] if len(raw) > 7 else ""

                formatted = f"PDM-{year_part}"

                if cleaned.endswith("-") and not number_part:
                    formatted += "-"
                elif number_part:
                    formatted += f"-{number_part}"

                if formatted != cleaned:
                    current_pos = self.entry_studentno.index('insert')
                    self.entry_studentno.delete(0, 'end')
                    self.entry_studentno.insert(0, formatted)

                    try:
                        self.entry_studentno.icursor(min(current_pos, len(formatted)))
                    except:
                        self.entry_studentno.icursor('end')

            if student_number and student_number != self.studentno_placeholder:
                if self.is_valid_pdm_student_number(student_number):
                    self.entry_studentno.config(fg="#006400")
                else:
                    self.entry_studentno.config(fg="#8B0000")

    def attempt_signup(self):
        """Attempt to sign up the user"""
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
            if not email:
                self.restore_placeholder(self.entry_email, self.email_placeholder)
            if not student_number:
                self.restore_placeholder(self.entry_studentno, self.studentno_placeholder)
            return

        if not UtilityFunctions.is_valid_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            self.entry_email.focus()
            return

        if not self.is_valid_pdm_student_number(student_number):
            messagebox.showerror(
                "Error",
                "Please enter a valid student number in format: PDM-YYYY-NNNNNN\n\nExample: PDM-2025-001234"
            )
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

            # Check if email already exists in users table
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                messagebox.showerror("Error", "Email already registered")
                return

            # Check if student number exists and is not already linked
            cursor.execute("SELECT student_id, user_id FROM students WHERE student_number = %s", (student_number,))
            student_record = cursor.fetchone()

            if student_record and student_record['user_id']:
                messagebox.showerror(
                    "Error",
                    "This student number is already linked to an existing account. Please login or contact the registrar."
                )
                return

            # Generate OTP and store temporary user data
            self.otp_code = UtilityFunctions.generate_otp()
            self.user_data = {
                'email': email,
                'password': password,
                'student_number': student_number,
                'username': student_number
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
            cursor = db_connection.cursor(dictionary=True)
            
            # Check for active transaction and rollback if needed
            try:
                if db_connection.in_transaction:
                    db_connection.rollback()
            except:
                pass
            
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
            
            # Extract year from student number for enrollment date
            try:
                admission_year = self.user_data['student_number'].split('-')[1]
                enrollment_date = datetime(int(admission_year), 6, 1)
            except (IndexError, ValueError):
                admission_year = "2025"
                enrollment_date = datetime.now()
            
            # 2. Check if student record already exists without user_id
            cursor.execute("""
                SELECT student_id, first_name, last_name, middle_name, course, year_level 
                FROM students 
                WHERE student_number = %s AND user_id IS NULL
            """, (self.user_data['student_number'],))
            
            existing_student = cursor.fetchone()
            
            if existing_student:
                # Link existing student record to the new user account
                cursor.execute("""
                    UPDATE students 
                    SET user_id = %s, date_enrolled = %s 
                    WHERE student_id = %s
                """, (user_id, enrollment_date, existing_student['student_id']))
                
                student_id = existing_student['student_id']
                first_name = existing_student['first_name']
                last_name = existing_student['last_name']
                middle_name = existing_student['middle_name']
                course = existing_student['course']
                year_level = existing_student['year_level']
            else:
                # Insert new student record
                first_name = 'New'
                last_name = 'Student'
                middle_name = ''
                course = 'Undecided'
                year_level = '1st Year'

                cursor.execute("""
                    INSERT INTO students (
                        user_id, student_number, first_name, last_name, middle_name,
                        course, year_level, enrollment_status, date_enrolled
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    self.user_data['student_number'],
                    first_name,
                    last_name,
                    middle_name,
                    course,
                    year_level,
                    'Enrolled',
                    enrollment_date
                ))
                student_id = cursor.lastrowid
            
            # 3. Insert initial academic record
            academic_year = f"{admission_year}-{int(admission_year)+1}"
            cursor.execute("""
                INSERT INTO academic_records (
                    student_id, course, year_level, semester, academic_year, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                student_id,
                course,
                year_level,
                '1st',
                academic_year,
                'Regular'
            ))
            
            db_connection.commit()
            
            # Show success message
            success_message = f"""
            Registration completed successfully!

            Student Information:
            • Name: {first_name} {last_name}
            • Student Number: {self.user_data['student_number']}
            • Email: {self.user_data['email']}
            • Course: {course}
            • Year Level: {year_level}

            You can now login using your student number or email.
            """
            
            messagebox.showinfo("Success", success_message.strip())
            self.show_login_callback()
            
        except mysql.connector.Error as e:
            try:
                db_connection.rollback()
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
            
            messagebox.showerror("Registration Error", error_message)
            
        except Exception as e:
            try:
                db_connection.rollback()
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
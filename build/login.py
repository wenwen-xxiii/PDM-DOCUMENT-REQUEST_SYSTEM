#login.py
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, messagebox
import mysql.connector
import aiomysql
import asyncio
from utils import UtilityFunctions
from config import DB_CONFIG
import sys
import os

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
    return Path(resource_path(f"resources/assets/{path}"))

class LoginWindow:
    def __init__(self, parent, login_callback, show_signup_callback, show_forgot_password_callback, get_db_connection):
        self.parent = parent
        self.login_callback = login_callback
        self.show_signup_callback = show_signup_callback
        self.show_forgot_password_callback = show_forgot_password_callback
        self.get_db_connection = get_db_connection
        
        self.button_hidden_img = PhotoImage(file=relative_to_assets("button_hidden.png"))
        self.button_view_img = PhotoImage(file=relative_to_assets("button_view.png"))
        
        self.setup_ui()
        
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
        
    def setup_ui(self):
        # Clear any existing widgets first
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Create canvas that fits exactly in 670x400
        self.canvas = Canvas(
            self.parent,
            bg="#FFFFFF",
            height=400,
            width=670,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Background and design elements - EXACTLY THE SAME as your original design
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

        # Logo - EXACTLY THE SAME as your original design
        self.image_image_1 = PhotoImage(file=relative_to_assets("image_logo.png"))
        self.canvas.create_image(164.0, 171.0, image=self.image_image_1)

        # Signup button - EXACTLY THE SAME as your original design
        self.button_image_1 = PhotoImage(file=relative_to_assets("buttonLbl_signup.png"))
        self.buttonLbl_signup = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_signup_callback,
            relief="flat",
            cursor="hand2"  # Added for better UX
        )
        self.buttonLbl_signup.place(x=430.0, y=326.0, width=158.0, height=18.0)

        # Forgot password button - EXACTLY THE SAME as your original design
        self.button_image_2 = PhotoImage(file=relative_to_assets("buttonLbl_forgotpass.png"))
        self.buttonLbl_forgotpass = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_forgot_password_callback,
            relief="flat",
            cursor="hand2"  # Added for better UX
        )
        self.buttonLbl_forgotpass.place(x=527.0, y=238.0, width=106.0, height=15.0)

        # Username/Email/Student No entry - EXACTLY THE SAME as your original design
        self.entry_image_1 = PhotoImage(file=relative_to_assets("entry_email.png"))
        self.canvas.create_image(505.5, 131.0, image=self.entry_image_1)
        self.entry_username = Entry(
            bd=0, bg="#F5C56E", fg="#000716", highlightthickness=0,
            font=("Inter", 12)
        )
        self.entry_username.place(x=391.0, y=111.0, width=229.0, height=38.0)
        self.entry_username.bind('<Return>', lambda e: self.entry_pass.focus())

        self.canvas.create_text(
            383.0, 89.0, anchor="nw",
            text="Email or Student No.",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        # Password entry - EXACTLY THE SAME as your original design
        self.entry_image_2 = PhotoImage(file=relative_to_assets("entry_pass.png"))
        self.canvas.create_image(505.5, 209.0, image=self.entry_image_2)
        self.entry_pass = Entry(
            bd=0, bg="#F5C56E", fg="#000716", highlightthickness=0,
            show="●", font=("Inter", 12)
        )
        self.entry_pass.place(x=391.0, y=189.0, width=229.0, height=38.0)
        self.entry_pass.bind('<Return>', lambda e: self.attempt_login())

        self.canvas.create_text(
            383.0, 167.0, anchor="nw",
            text="Password",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        self.canvas.create_text(
            378.0, 24.0, anchor="nw",
            text="Login",
            fill="#FFFFFF", font=("Inter Bold", 32 * -1)
        )
        
        self.button_toggle_pass = Button(
            image=self.button_view_img,
            borderwidth=0, highlightthickness=0,
            command=lambda: self.toggle_password_visibility(self.entry_pass, self.button_toggle_pass),
            relief="flat", cursor="hand2"
        )
        
        self.button_toggle_pass.place(x=600.0, y=199.0, width=20.0, height=19.0)
        
        # Login button - EXACTLY THE SAME as your original design
        self.button_image_3 = PhotoImage(file=relative_to_assets("button_login.png"))
        self.button_login = Button(
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.attempt_login,
            relief="flat",
            cursor="hand2"  # Added for better UX
        )
        self.button_login.place(x=383.0, y=270.0, width=245.0, height=40.0)

        # Set focus to username entry for better UX
        self.entry_username.focus()
        
    def toggle_password_visibility(self, entry_widget, button_widget):
        """Toggle the visibility of the password field"""
        if entry_widget.cget('show') == "●":
            entry_widget.config(show="")
            button_widget.config(image=self.button_hidden_img)
        else:
            entry_widget.config(show="●")
            button_widget.config(image=self.button_view_img)

    async def attempt_login_async(self):
        """Attempt login asynchronously"""
        username_input = self.entry_username.get().strip()
        password = self.entry_pass.get().strip()

        if not username_input or not password:
            messagebox.showerror("Error", "Please enter both username/email and password")
            return

        db_connection = await self.get_async_db_connection()
        if not db_connection:
            messagebox.showerror("Database Error", "Cannot connect to database")
            return

        try:
            cursor = await db_connection.cursor(aiomysql.DictCursor)
            
            # Determine if input is email or student number
            if UtilityFunctions.is_valid_email(username_input):
                # Input is an email - search by email
                await cursor.execute("""
                    SELECT u.*, s.student_number, s.first_name, s.last_name, s.course, s.year_level
                    FROM users u 
                    LEFT JOIN students s ON u.user_id = s.user_id 
                    WHERE u.email = %s AND u.is_verified = TRUE AND u.is_active = TRUE
                """, (username_input,))
            else:
                # Input is likely a student number - search by student number or username
                await cursor.execute("""
                    SELECT u.*, s.student_number, s.first_name, s.last_name, s.course, s.year_level
                    FROM users u 
                    LEFT JOIN students s ON u.user_id = s.user_id 
                    WHERE (u.username = %s OR s.student_number = %s) 
                    AND u.is_verified = TRUE AND u.is_active = TRUE
                """, (username_input, username_input))
            
            user = await cursor.fetchone()

            if user and UtilityFunctions.verify_password(password, user['password_hash']):
                # Prepare user data for session
                user_data = {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'student_number': user.get('student_number', ''),
                    'course': user.get('course', ''),
                    'year_level': user.get('year_level', ''),
                    'user_type': user['user_type']
                }
                
                # Check if student has outstanding obligations
                if user['user_type'] == 'student':
                    from utils import ValidationHelper
                    if not ValidationHelper.validate_student_clearance(db_connection, user['user_id']):
                        messagebox.showerror(
                            "Clearance Issue", 
                            "Cannot proceed. You have outstanding obligations. Please contact the registrar's office."
                        )
                        return

                self.login_callback(user_data, user['user_type'])
            else:
                messagebox.showerror("Login Failed", "Invalid username/email or password")

        except Exception as e:
            messagebox.showerror("Database Error", f"Login failed: {str(e)}")
        finally:
            if db_connection:
                await db_connection.ensure_closed()

    def attempt_login(self):
        """Synchronous wrapper for async login attempt"""
        try:
            # Run the async function in a new event loop
            asyncio.run(self.attempt_login_async())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to login: {str(e)}")

    def destroy(self):
        """Clean up the window"""
        for widget in self.parent.winfo_children():
            widget.destroy()
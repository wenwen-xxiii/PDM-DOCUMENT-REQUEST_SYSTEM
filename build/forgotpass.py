#forgotpass.py
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
    return Path(resource_path(f"resources/assets/frame3/{path}"))

class ForgotPasswordWindow:
    def __init__(self, parent, show_login_callback, get_db_connection):
        self.parent = parent
        self.show_login_callback = show_login_callback
        self.get_db_connection = get_db_connection
        self.otp_code = None
        self.user_email = None
        
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

        self.canvas.create_text(
            383.0, 169.0, anchor="nw",
            text="Email",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        self.canvas.create_text(
            374.0, 100.0, anchor="nw",
            text="Forgot Password",
            fill="#FFFFFF", font=("Inter Bold", 32 * -1)
        )

        # Submit button
        self.button_image_1 = PhotoImage(file=relative_to_assets("button_forgotpass.png"))
        self.button_forgotpass = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.send_reset_email,
            relief="flat"
        )
        self.button_forgotpass.place(x=383.0, y=262.0, width=245.0, height=40.0)

        # Email entry
        self.entry_image_1 = PhotoImage(file=relative_to_assets("entry_email.png"))
        self.canvas.create_image(505.5, 212.0, image=self.entry_image_1)
        self.entry_email = Entry(
            bd=0, bg="#F5C56E", fg="#000716", highlightthickness=0,
            font=("Inter", 12)
        )
        self.entry_email.place(x=391.0, y=192.0, width=229.0, height=38.0)
        self.entry_email.bind('<Return>', lambda e: self.send_reset_email())

        # Back button
        self.button_image_2 = PhotoImage(file=relative_to_assets("button_back.png"))
        self.button_back = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.go_back,
            relief="flat"
        )
        self.button_back.place(x=624.0, y=16.0, width=30.0, height=30.0)

    def send_reset_email(self):
        """Send password reset OTP email"""
        email = self.entry_email.get().strip()
        
        if not email:
            messagebox.showerror("Error", "Please enter your email address")
            return
            
        if not UtilityFunctions.is_valid_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        db_connection = self.get_db_connection()
        if not db_connection:
            messagebox.showerror("Database Error", "Cannot connect to database")
            return

        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                messagebox.showerror("Error", "No account found with this email address")
                return

            # Generate OTP
            self.otp_code = UtilityFunctions.generate_otp()
            self.user_email = email

            # Send OTP email
            email_service = EmailService()
            if email_service.send_otp_email(email, self.otp_code):
                self.show_otp_verification()
            else:
                messagebox.showerror("Error", "Failed to send OTP. Please try again.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process request: {str(e)}")
        finally:
            if db_connection and db_connection.is_connected():
                cursor.close()

    def show_otp_verification(self):
        """Show OTP verification for password reset"""
        user_data = {'email': self.user_email}
        
        self.destroy()
        OTPVerificationWindow(
            self.parent,
            user_data,
            self.otp_code,
            self.show_password_reset,
            self.show_login_callback,
            self.get_db_connection
        )

    def show_password_reset(self):
        """Show password reset screen after OTP verification"""
        from passreset import PasswordResetWindow
        self.destroy()
        PasswordResetWindow(
            self.parent,
            self.user_email,
            self.show_login_callback,
            self.get_db_connection
        )

    def go_back(self):
        """Return to login screen"""
        self.destroy()
        self.show_login_callback()

    def destroy(self):
        """Clean up the window"""
        for widget in self.parent.winfo_children():
            widget.destroy()
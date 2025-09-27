from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, messagebox
from utils import UtilityFunctions
import mysql.connector
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
    return Path(resource_path(f"resources/assets/frame2/{path}"))

class PasswordResetWindow:
    def __init__(self, parent, user_email, show_login_callback, get_db_connection):
        self.parent = parent
        self.user_email = user_email
        self.show_login_callback = show_login_callback
        self.get_db_connection = get_db_connection
        
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
            383.0, 133.0, anchor="nw",
            text="New Password",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        self.canvas.create_text(
            378.0, 62.0, anchor="nw",
            text="Password Reset",
            fill="#FFFFFF", font=("Inter Bold", 32 * -1)
        )

        # Reset password button
        self.button_image_1 = PhotoImage(file=relative_to_assets("button_resetpass.png"))
        self.button_resetpass = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.reset_password,
            relief="flat"
        )
        self.button_resetpass.place(x=383.0, y=298.0, width=245.0, height=40.0)

        # New password entry
        self.entry_image_1 = PhotoImage(file=relative_to_assets("entry_newpass.png"))
        self.canvas.create_image(505.5, 176.0, image=self.entry_image_1)
        self.entry_newpass = Entry(
            bd=0, bg="#F5C56E", fg="#000716", highlightthickness=0,
            show="*", font=("Inter", 12)
        )
        self.entry_newpass.place(x=391.0, y=156.0, width=229.0, height=38.0)
        self.entry_newpass.bind('<Return>', lambda e: self.entry_confirmpass.focus())

        self.canvas.create_text(
            383.0, 204.0, anchor="nw",
            text="Confirm Password",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        # Confirm password entry
        self.entry_image_2 = PhotoImage(file=relative_to_assets("entry_confirmpass.png"))
        self.canvas.create_image(505.5, 246.0, image=self.entry_image_2)
        self.entry_confirmpass = Entry(
            bd=0, bg="#F5C56E", fg="#000716", highlightthickness=0,
            show="*", font=("Inter", 12)
        )
        self.entry_confirmpass.place(x=391.0, y=226.0, width=229.0, height=38.0)
        self.entry_confirmpass.bind('<Return>', lambda e: self.reset_password())

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

    def reset_password(self):
        """Reset the user's password"""
        new_password = self.entry_newpass.get().strip()
        confirm_password = self.entry_confirmpass.get().strip()

        if not new_password or not confirm_password:
            messagebox.showerror("Error", "Please fill in both password fields")
            return

        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if len(new_password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return

        db_connection = self.get_db_connection()
        if not db_connection:
            messagebox.showerror("Database Error", "Cannot connect to database")
            return

        try:
            cursor = db_connection.cursor()
            
            # Hash the new password
            hashed_password = UtilityFunctions.hash_password(new_password)
            
            # Update password in database
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE email = %s",
                (hashed_password, self.user_email)
            )
            
            if cursor.rowcount == 0:
                messagebox.showerror("Error", "Failed to reset password. User not found.")
                return
            
            db_connection.commit()
            messagebox.showinfo("Success", "Password reset successfully!")
            self.show_login_callback()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset password: {str(e)}")
            db_connection.rollback()
        finally:
            if db_connection and db_connection.is_connected():
                cursor.close()

    def go_back(self):
        """Return to login screen"""
        self.destroy()
        self.show_login_callback()

    def destroy(self):
        """Clean up the window"""
        for widget in self.parent.winfo_children():
            widget.destroy()
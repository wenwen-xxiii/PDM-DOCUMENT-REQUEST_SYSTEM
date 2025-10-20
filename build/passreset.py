# passreset.py
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, messagebox
from utils import UtilityFunctions
from config import DB_CONFIG
import mysql.connector
import aiomysql
import asyncio
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
    return Path(resource_path(f"resources/assets/{path}"))

class PasswordResetWindow:
    def __init__(self, parent, user_email, show_login_callback, get_db_connection):
        self.parent = parent
        self.user_email = user_email
        self.show_login_callback = show_login_callback
        self.get_db_connection = get_db_connection
        
        # Load eye images for toggle
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
        self.canvas.create_text(51.0, 293.0, anchor="nw",
                                text="Where quality education is a right, not privilege.",
                                fill="#FFFFFF", font=("Inter Italic", 10 * -1))
        self.canvas.create_text(41.0, 263.0, anchor="nw",
                                text="PAMBAYANG DALUBHASAAN NG MARILAO",
                                fill="#FFD700", font=("Inter Bold", 12 * -1))

        # Logo
        self.image_image_1 = PhotoImage(file=relative_to_assets("image_logo.png"))
        self.canvas.create_image(164.0, 171.0, image=self.image_image_1)

        self.canvas.create_text(383.0, 133.0, anchor="nw",
                                text="New Password", fill="#FFFFFF", font=("Inter Bold", 16 * -1))
        self.canvas.create_text(378.0, 62.0, anchor="nw",
                                text="Password Reset", fill="#FFFFFF", font=("Inter Bold", 32 * -1))

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
            show="●", font=("Inter", 12)
        )
        self.entry_newpass.place(x=391.0, y=156.0, width=229.0, height=38.0)
        self.entry_newpass.bind('<Return>', lambda e: self.entry_confirmpass.focus())

        # New password toggle button
        self.button_toggle_new = Button(
            image=self.button_hidden_img,
            borderwidth=0, highlightthickness=0,
            command=lambda: self.toggle_password_visibility(self.entry_newpass, self.button_toggle_new),
            relief="flat", cursor="hand2"
        )
        self.button_toggle_new.place(x=600.0, y=166.0, width=20.0, height=19.0)

        self.canvas.create_text(383.0, 204.0, anchor="nw",
                                text="Confirm Password", fill="#FFFFFF", font=("Inter Bold", 16 * -1))

        # Confirm password entry
        self.entry_image_2 = PhotoImage(file=relative_to_assets("entry_confirmpass.png"))
        self.canvas.create_image(505.5, 246.0, image=self.entry_image_2)
        self.entry_confirmpass = Entry(
            bd=0, bg="#F5C56E", fg="#000716", highlightthickness=0,
            show="●", font=("Inter", 12)
        )
        self.entry_confirmpass.place(x=391.0, y=226.0, width=229.0, height=38.0)
        self.entry_confirmpass.bind('<Return>', lambda e: self.reset_password())

        # Confirm password toggle button
        self.button_toggle_confirm = Button(
            image=self.button_view_img,
            borderwidth=0, highlightthickness=0,
            command=lambda: self.toggle_password_visibility(self.entry_confirmpass, self.button_toggle_confirm),
            relief="flat", cursor="hand2"
        )
        self.button_toggle_confirm.place(x=600.0, y=236.0, width=20.0, height=19.0)

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
        
        # Set initial focus and configure tab order
        self.entry_newpass.focus()
        
        # Configure tab order for proper keyboard navigation
        # Tab order: New Password -> Confirm Password -> Reset Button -> Back Button
        self.parent.bind('<Tab>', self.on_tab_key)
        self.parent.bind('<Shift-Tab>', self.on_shift_tab_key)
        
        # Add keyboard shortcuts
        self.parent.bind('<Control-r>', lambda e: self.reset_password())  # Ctrl+R to reset
        self.parent.bind('<Escape>', lambda e: self.go_back())  # Escape to go back

    def on_tab_key(self, event):
        """Handle Tab key navigation"""
        focused_widget = self.parent.focus_get()
        
        if focused_widget == self.entry_newpass:
            self.entry_confirmpass.focus()
        elif focused_widget == self.entry_confirmpass:
            self.button_resetpass.focus()
        elif focused_widget == self.button_resetpass:
            self.button_back.focus()
        elif focused_widget == self.button_back:
            self.entry_newpass.focus()  # Cycle back to start
        
        return "break"  # Prevent default tab behavior
    
    def on_shift_tab_key(self, event):
        """Handle Shift+Tab key navigation (reverse order)"""
        focused_widget = self.parent.focus_get()
        
        if focused_widget == self.entry_newpass:
            self.button_back.focus()
        elif focused_widget == self.entry_confirmpass:
            self.entry_newpass.focus()
        elif focused_widget == self.button_resetpass:
            self.entry_confirmpass.focus()
        elif focused_widget == self.button_back:
            self.button_resetpass.focus()
        
        return "break"  # Prevent default tab behavior

    def toggle_password_visibility(self, entry_widget, button_widget):
        """Toggle the visibility of the password field"""
        if entry_widget.cget('show') == "●":
            entry_widget.config(show="")
            button_widget.config(image=self.button_hidden_img)
        else:
            entry_widget.config(show="●")
            button_widget.config(image=self.button_view_img)

    async def reset_password_async(self):
        """Reset the user's password asynchronously"""
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

        # Debug: Print the email being used for password reset
        print(f"Attempting password reset for email: '{self.user_email}'")
        print(f"Email type: {type(self.user_email)}")
        print(f"Email length: {len(self.user_email) if self.user_email else 'None'}")
        
        db_connection = await self.get_async_db_connection()
        if not db_connection:
            messagebox.showerror("Database Error", "Cannot connect to database")
            return

        try:
            cursor = await db_connection.cursor()
            
            # First verify the user exists and is verified/active
            query = "SELECT user_id FROM users WHERE email = %s AND is_verified = TRUE AND is_active = TRUE"
            print(f"Executing query: {query}")
            print(f"With email parameter: '{self.user_email}'")
            
            await cursor.execute(query, (self.user_email,))
            user = await cursor.fetchone()
            
            print(f"User lookup result: {user}")  # Debug
            
            if not user:
                # Additional debug: Check if user exists without verification check
                await cursor.execute(
                    "SELECT user_id, is_verified, is_active FROM users WHERE email = %s",
                    (self.user_email,)
                )
                debug_user = await cursor.fetchone()
                print(f"Debug user info: {debug_user}")  # Debug
                
                messagebox.showerror("Error", "Failed to reset password. User not found or account not verified.")
                return
            
            # Update the password
            hashed_password = UtilityFunctions.hash_password(new_password)
            await cursor.execute(
                "UPDATE users SET password_hash = %s WHERE email = %s AND is_verified = TRUE AND is_active = TRUE",
                (hashed_password, self.user_email)
            )
            
            if cursor.rowcount == 0:
                messagebox.showerror("Error", "Failed to reset password. User not found.")
                return
                
            await db_connection.commit()
            messagebox.showinfo("Success", "Password reset successfully!")
            self.show_login_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset password: {str(e)}")
            await db_connection.rollback()
        finally:
            if db_connection:
                await db_connection.ensure_closed()

    def reset_password(self):
        """Synchronous wrapper for async password reset"""
        try:
            # Run the async function in a new event loop
            asyncio.run(self.reset_password_async())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset password: {str(e)}")

    def go_back(self):
        """Return to login screen"""
        self.destroy()
        self.show_login_callback()

    def destroy(self):
        """Clean up the window"""
        # Unbind all event bindings
        try:
            self.parent.unbind('<Tab>')
            self.parent.unbind('<Shift-Tab>')
            self.parent.unbind('<Control-r>')
            self.parent.unbind('<Escape>')
        except:
            pass
        
        # Destroy all widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

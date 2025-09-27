import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from login import LoginWindow
from signup import SignupWindow
from forgotpass import ForgotPasswordWindow
from home import HomeWindow
from config import DB_CONFIG, APP_CONFIG
import os

class DocumentRequestSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDM - Document Request System")
        self.root.configure(bg='#f0f0f0')
        
        # Set application icon if exists
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            if APP_CONFIG['debug']:
                print(f"Icon loading failed: {e}")
        
        # Set initial window size for login
        self.login_size = (670, 400)
        self.home_size = (1200, 800)
        self.current_size = self.login_size
        
        self.center_window(*self.login_size)
        
        self.current_user = None
        self.user_type = None
        self.db_connection = None
        
        # Check if database configuration is available
        if not DB_CONFIG['host']:
            messagebox.showerror(
                "Configuration Error", 
                "Database configuration not found. Please check your .env file."
            )
            self.root.quit()
            return
            
        self.setup_database()
        self.show_login()
        
    def center_window(self, width, height):
        """Center the window on the screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.current_size = (width, height)
    
    def resize_window(self, width, height):
        """Resize the window to new dimensions"""
        print(f"Resizing window to: {width}x{height}")  # Debug
        self.center_window(width, height)
    
    def setup_database(self):
        """Initialize database connection"""
        try:
            self.db_connection = mysql.connector.connect(**DB_CONFIG)
            if self.db_connection.is_connected():
                print("✓ Database connection established successfully")
                
                # Test if database exists
                try:
                    cursor = self.db_connection.cursor()
                    cursor.execute("USE {}".format(DB_CONFIG['database']))
                    cursor.close()
                except Error as e:
                    if e.errno == 1049:  # Database doesn't exist
                        response = messagebox.askyesno(
                            "Database Setup", 
                            "Database not found. Would you like to initialize the database now?"
                        )
                        if response:
                            self.initialize_database()
                        else:
                            messagebox.showinfo(
                                "Information",
                                "Please run init_database.py manually to set up the database."
                            )
                            self.root.quit()
                    else:
                        raise e
                        
        except Error as e:
            error_msg = f"Failed to connect to database: {str(e)}"
            if APP_CONFIG['debug']:
                error_msg += f"\n\nDebug info: {e}"
            
            messagebox.showerror("Database Error", error_msg)
            self.root.quit()
    
    def initialize_database(self):
        """Initialize the database schema"""
        try:
            from init_database import initialize_system_database
            if initialize_system_database():
                messagebox.showinfo("Success", "Database initialized successfully!")
                # Reconnect to the new database
                if self.db_connection and self.db_connection.is_connected():
                    self.db_connection.close()
                self.db_connection = mysql.connector.connect(**DB_CONFIG)
            else:
                messagebox.showerror("Error", "Failed to initialize database.")
                self.root.quit()
        except ImportError as e:
            messagebox.showerror("Error", f"Cannot import database initializer: {e}")
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Database initialization failed: {e}")
            self.root.quit()
    
    def get_db_connection(self):
        """Get database connection with reconnection handling"""
        try:
            if self.db_connection is None or not self.db_connection.is_connected():
                self.db_connection = mysql.connector.connect(**DB_CONFIG)
                # Set autocommit to True to avoid transaction conflicts
                self.db_connection.autocommit = True
            return self.db_connection
        except Error as e:
            error_msg = f"Database connection failed: {str(e)}"
            if APP_CONFIG['debug']:
                error_msg += f"\n\nDebug info: {e}"
            
            messagebox.showerror("Database Error", error_msg)
            return None
    
    def show_login(self):
        """Show login window and resize to login size"""
        self.clear_window()
        
        # Set exact window size and make non-resizable
        self.root.geometry("670x400")
        self.root.resizable(False, False)
        self.center_window(670, 400)
        
        LoginWindow(
            self.root, 
            self.login_success_callback, 
            self.show_signup, 
            self.show_forgot_password, 
            self.get_db_connection
        )
    
    def show_signup(self):
        """Show signup window (same size as login)"""
        self.clear_window()
        self.resize_window(*self.login_size)
        SignupWindow(self.root, self.show_login, self.get_db_connection)
    
    def show_forgot_password(self):
        """Show forgot password flow (same size as login)"""
        self.clear_window()
        self.resize_window(*self.login_size)
        ForgotPasswordWindow(self.root, self.show_login, self.get_db_connection)
    
    def login_success_callback(self, user_data, user_type):
        """Callback after successful login - resize to home size"""
        self.current_user = user_data
        self.user_type = user_type
        
        # Log login activity
        if APP_CONFIG['debug']:
            print(f"✓ User logged in: {user_data['email']} ({user_type})")
        
        self.show_home()
    
    def show_home(self):
        """Show home window and resize to home size"""
        self.clear_window()
        self.resize_window(*self.home_size)
        HomeWindow(
            self.root, 
            self.current_user, 
            self.user_type, 
            self.logout, 
            self.get_db_connection
        )
    
    def logout(self):
        """Logout user and return to login - resize to login size"""
        if self.current_user and APP_CONFIG['debug']:
            print(f"✓ User logged out: {self.current_user['email']}")
        
        self.current_user = None
        self.user_type = None
        
        # Force exact size and non-resizable
        self.root.resizable(False, False)
        self.root.geometry("670x400")
        self.center_window(670, 400)
        
        self.show_login()
    
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            if self.db_connection and self.db_connection.is_connected():
                self.db_connection.close()
                print("✓ Database connection closed")
            self.root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            # Set closing protocol
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Make window non-resizable during login phase
            self.root.resizable(False, False)
            
            # Start the main loop
            self.root.mainloop()
            
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            if APP_CONFIG['debug']:
                error_msg += f"\n\nTechnical details: {e}"
            
            messagebox.showerror("Application Error", error_msg)
        
        finally:
            # Ensure database connection is closed
            if self.db_connection and self.db_connection.is_connected():
                self.db_connection.close()
                print("✓ Database connection closed on exit")

def main():
    """Main entry point for the application"""
    print("=" * 60)
    print("Pambayang Dalubhasaan ng Marilao")
    print("Document Request System")
    print("=" * 60)
    
    if APP_CONFIG['debug']:
        print("🚀 Starting application in DEBUG mode")
        print(f"📊 Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
        print(f"👤 Default Admin: admin / admin123")
        print(f"👤 Default Registrar: registrar / registrar123")
        print("=" * 60)
    
    try:
        app = DocumentRequestSystem()
        app.run()
    except KeyboardInterrupt:
        print("\n⚠️  Application interrupted by user")
    except Exception as e:
        print(f"💥 Critical error: {e}")
        messagebox.showerror("Fatal Error", f"The application encountered a critical error:\n\n{str(e)}")

if __name__ == "__main__":
    main()
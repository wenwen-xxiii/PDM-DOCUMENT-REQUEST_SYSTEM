from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Frame, Label, messagebox
from document_request import DocumentRequestWindow
from profile import ProfileWindow
import sys
import os
import tkinter as tk
from tkinter import messagebox
import mysql.connector

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
    return Path(resource_path(f"resources/assets/frame6/{path}"))

class HomeWindow:
    def __init__(self, parent, user_data, user_type, logout_callback, get_db_connection):
        
        self.logout_callback = logout_callback
        self.parent = parent
        self.user_data = user_data
        self.user_type = user_type
        self.logout_callback = logout_callback
        self.get_db_connection = get_db_connection
        self.current_content = None
        
        # Make window resizable
        self.parent.resizable(True, True)
        self.parent.minsize(1000, 600) 
        
        # Bind resize event
        self.parent.bind('<Configure>', self.on_resize)
        
        self.setup_ui()
        
    def on_resize(self, event):
        """Handle window resize events"""
        if event.widget == self.parent:
            self.update_layout()
            
    def update_layout(self):
        """Update the layout based on current window size"""
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return  # canvas already destroyed → skip

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()

        # Update header and main bg
        self.canvas.coords("header_bg", 0, 0, width, 77)
        self.canvas.coords("main_bg", 0, 77, width, height)
        
        # Update button positions based on window width
        button_spacing = width * 0.15  # 15% of window width between buttons
        start_x = width * 0.52
        
        self.button_home.place(relx=0.52, rely=0.03, anchor="n")
        self.button_reqdocu.place(relx=0.67, rely=0.03, anchor="n")
        self.button_profile.place(relx=0.82, rely=0.03, anchor="n")
        self.button_logout.place(relx=0.97, rely=0.03, anchor="n")
        
        # Update welcome text position
        self.canvas.coords("welcome_text", 29, 10)
        self.canvas.coords("user_role", 29, 39)
        
        # Update content area
        if self.current_content == "dashboard":
            self.show_dashboard()
        elif self.current_content == "document_request":
            self.show_document_request()
        elif self.current_content == "profile":
            self.show_profile()
        
    def setup_ui(self):
        # Clear previous widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
            
        # Create main canvas that fills the window
        self.canvas = Canvas(
            self.parent,
            bg="#FFFFFF",
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Get initial window size
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        
        # Create scalable background rectangles
        self.canvas.create_rectangle(0, 77, width, height, fill="#FFA500", outline="", tags="main_bg")
        self.canvas.create_rectangle(0, 0, width, 77, fill="#800000", outline="", tags="header_bg")
        
        # Welcome text
        welcome_text = f"Welcome, {self.user_data['first_name']} {self.user_data['last_name']}!"
        user_role = self.user_type.title()
        
        self.canvas.create_text(29, 10, anchor="nw", text=welcome_text, 
                               fill="#FFD700", font=("Inter Bold", 24), tags="welcome_text")
        self.canvas.create_text(29, 39, anchor="nw", text=user_role, 
                               fill="#FFD700", font=("Inter Bold", 24), tags="user_role")

        # Load images using resource_path
        self.img_reqdocu = PhotoImage(file=relative_to_assets("button_reqdocu.png"))
        self.img_profile = PhotoImage(file=relative_to_assets("button_profile.png"))
        self.img_home = PhotoImage(file=relative_to_assets("button_home.png"))
        self.img_logout = PhotoImage(file=relative_to_assets("button_logout.png"))

        # Create buttons
        self.button_home = Button(
            self.parent,
            image=self.img_home,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_home,
            relief="flat",
            cursor="hand2"
        )

        self.button_reqdocu = Button(
            self.parent,
            image=self.img_reqdocu,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_document_request,
            relief="flat",
            cursor="hand2"
        )

        self.button_profile = Button(
            self.parent,
            image=self.img_profile,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_profile,
            relief="flat",
            cursor="hand2"
        )

        self.button_logout = Button(
            self.parent,
            image=self.img_logout,
            borderwidth=0,
            highlightthickness=0,
            command=self.logout,
            relief="flat",
            cursor="hand2"
        )

        # Place buttons with relative positioning
        self.button_home.place(relx=0.52, rely=0.03, anchor="n")
        self.button_reqdocu.place(relx=0.67, rely=0.03, anchor="n")
        self.button_profile.place(relx=0.82, rely=0.03, anchor="n")
        self.button_logout.place(relx=0.97, rely=0.03, anchor="n")

        # Show dashboard content
        self.show_dashboard()

    def show_dashboard(self):
        """Show the main dashboard content"""
        self.current_content = "dashboard"
        
        # Clear previous content
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_reqdocu, 
                            self.button_profile, self.button_logout]:
                widget.destroy()
        
        # Get current window size for responsive layout
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        
        # Dashboard content frame with responsive sizing
        dashboard_frame = Frame(self.parent, bg="#FFFFFF")
        dashboard_frame.place(relx=0.5, rely=0.55, anchor="center", 
                            width=min(1200, width * 0.9), 
                            height=min(600, height * 0.8))
        
        # Welcome message with responsive font size
        font_size = max(20, min(28, int(width / 50)))  # Responsive font size
        welcome_label = Label(
            dashboard_frame,
            text=f"Document Request System Dashboard",
            font=("Inter Bold", font_size),
            bg="#FFFFFF",
            fg="#800000"
        )
        welcome_label.pack(pady=20)
        
        # User info with responsive font size
        info_font_size = max(10, min(14, int(width / 80)))
        info_text = f"""
        User Information:
        • Name: {self.user_data['first_name']} {self.user_data['last_name']}
        • Student Number: {self.user_data.get('student_number', 'N/A')}
        • Email: {self.user_data['email']}
        • Course: {self.user_data.get('course', 'N/A')}
        • Year Level: {self.user_data.get('year_level', 'N/A')}
        • User Type: {self.user_type.title()}
        """
        
        info_label = Label(
            dashboard_frame,
            text=info_text,
            font=("Inter", info_font_size),
            bg="#FFFFFF",
            fg="#000000",
            justify="left"
        )
        info_label.pack(pady=20)
        
        # Quick actions based on user type
        action_font_size = max(10, min(12, int(width / 100)))
        if self.user_type == 'student':
            action_text = "Quick Actions:\n• Request a new document\n• View your request history\n• Update your profile information"
        else:
            action_text = "Quick Actions:\n• Process pending requests\n• View system reports\n• Manage user accounts"
        
        action_label = Label(
            dashboard_frame,
            text=action_text,
            font=("Inter", action_font_size),
            bg="#FFFFFF",
            fg="#666666",
            justify="left"
        )
        action_label.pack(pady=20)

    def show_home(self):
        """Show home dashboard"""
        self.show_dashboard()

    def show_document_request(self):
        """Show document request interface"""
        self.current_content = "document_request"
        
        # Clear current window content but keep navigation
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_reqdocu, 
                            self.button_profile, self.button_logout]:
                widget.destroy()
        
        # Create responsive content area
        content_frame = Frame(self.parent, bg="#FFFFFF")
        content_frame.place(relx=0.5, rely=0.55, anchor="center", 
                          width=min(1200, self.parent.winfo_width() * 0.9), 
                          height=min(600, self.parent.winfo_height() * 0.8))
        
        # Placeholder for document request content
        placeholder_label = Label(
            content_frame,
            text="Document Request Interface\n\nThis area will contain the document request form,\ndocument selection, and request history.",
            font=("Inter Bold", 18),
            bg="#FFFFFF",
            fg="#800000",
            justify="center"
        )
        placeholder_label.pack(expand=True)
        
        # You can replace this with your actual DocumentRequestWindow integration
        # For now, add a back button
        back_button = Button(
            content_frame,
            text="Back to Dashboard",
            font=("Inter", 12),
            bg="#800000",
            fg="#FFFFFF",
            command=self.show_dashboard,
            cursor="hand2"
        )
        back_button.pack(pady=20)

    def show_profile(self):
        """Show user profile"""
        self.current_content = "profile"
        
        # Clear current window content but keep navigation
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_reqdocu, 
                            self.button_profile, self.button_logout]:
                widget.destroy()
        
        # Create responsive content area
        content_frame = Frame(self.parent, bg="#FFFFFF")
        content_frame.place(relx=0.5, rely=0.55, anchor="center", 
                          width=min(1200, self.parent.winfo_width() * 0.9), 
                          height=min(600, self.parent.winfo_height() * 0.8))
        
        # Placeholder for profile content
        placeholder_label = Label(
            content_frame,
            text="Profile Management Interface\n\nThis area will contain user profile information,\nedit forms, and account settings.",
            font=("Inter Bold", 18),
            bg="#FFFFFF",
            fg="#800000",
            justify="center"
        )
        placeholder_label.pack(expand=True)
        
        # Back button
        back_button = Button(
            content_frame,
            text="Back to Dashboard",
            font=("Inter", 12),
            bg="#800000",
            fg="#FFFFFF",
            command=self.show_dashboard,
            cursor="hand2"
        )
        back_button.pack(pady=20)

    def logout(self):
        """Logout user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.logout_callback()




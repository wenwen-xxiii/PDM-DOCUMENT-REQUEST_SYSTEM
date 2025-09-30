
from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Frame, Label, messagebox
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
    return Path(resource_path(f"resources/assets/frame0/{path}"))

class HomeWindow:
    def __init__(self, parent, user_data, user_type, logout_callback, get_db_connection):
        self.parent = parent
        self.user_data = user_data
        self.user_type = user_type
        self.logout_callback = logout_callback
        self.get_db_connection = get_db_connection
        self.current_content = None
        
        # Make window resizable
        self.parent.resizable(True, True)
        self.parent.minsize(1280, 720) 
        
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
        self.canvas.coords("header_bg", 0, 0, width, 98)
        self.canvas.coords("nav_bg", 0, 98, width, 140)
        self.canvas.coords("main_bg", 0, 140, width, height)
        
        # Update navigation button positions based on window width
        nav_y = 108
        total_width = width
        button_spacing = total_width / 5  # Evenly distribute 4 buttons
        
        self.button_home.place(x=button_spacing * 1 - 40, y=nav_y, width=80, height=24)
        self.button_programs.place(x=button_spacing * 2 - 50, y=nav_y, width=100, height=24)
        self.button_documents.place(x=button_spacing * 3 - 55, y=nav_y, width=110, height=24)
        self.button_profile.place(x=button_spacing * 4 - 40, y=nav_y, width=80, height=24)
        
        # Update user interface button positions
        self.button_logout.place(relx=0.97, rely=0.03, anchor="n")
        
        # Update welcome text position
        self.canvas.coords("welcome_text", 29, 24)
        self.canvas.coords("user_role", 29, 57)
        
        # Update university text positions - BOTH texts aligned to same x position
        self.canvas.coords("university_text", 128, 24)
        self.canvas.coords("motto_text", 128, 57)
        
        # Update background image if it exists
        if hasattr(self, 'bg_image_id'):
            self.resize_background()
        
        # Update content area
        if self.current_content == "dashboard":
            self.show_dashboard()
        elif self.current_content == "document_request":
            self.show_document_request()
        elif self.current_content == "profile":
            self.show_profile()
        elif self.current_content == "programs":
            self.show_programs()
        
    def resize_background(self, event=None):
        """Resize background image to fit the window"""
        try:
            if hasattr(self, 'pil_bg_image'):
                # Get current window size
                width = self.parent.winfo_width()
                height = self.parent.winfo_height()
                
                # Calculate the area to fill (below the header and nav)
                bg_width = width
                bg_height = max(1, height - 140)  # Ensure positive value
                
                if bg_width > 0 and bg_height > 0:
                    # Resize image to fill the entire area
                    from PIL import Image, ImageTk
                    resized_image = self.pil_bg_image.resize((bg_width, bg_height), Image.Resampling.LANCZOS)
                    self.image_2_resized = ImageTk.PhotoImage(resized_image)  # FIXED: ImageTk.PhotoImage
                    
                    # Update the canvas image
                    self.canvas.itemconfig(self.bg_image_id, image=self.image_2_resized)
        except Exception as e:
            print(f"Error resizing background: {e}")
        
    def setup_ui(self):
        # Clear previous widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
            
        # Create main canvas that fills the window
        self.canvas = Canvas(
            self.parent,
            bg="#FCECB7",
            bd=0,
            highlightthickness=0,
            relief="ridge",
            
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Get initial window size
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        
        # Load background image
        try:
            from PIL import Image, ImageTk
            
            # Load the background image using PIL
            bg_path = resource_path("resources/assets/frame0/image_2.png")
            self.pil_bg_image = Image.open(bg_path)
            
            # Create initial resized image
            bg_width = width
            bg_height = max(1, height - 140)
            resized_image = self.pil_bg_image.resize((bg_width, bg_height), Image.Resampling.LANCZOS)
            self.image_2_resized = ImageTk.PhotoImage(resized_image)
            
            # Create the background image
            self.bg_image_id = self.canvas.create_image(0, 140, image=self.image_2_resized, anchor="nw", tags="bg_image")
            
        except ImportError:
            print("PIL not available, using basic background image")
            try:
                image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
                self.image_2 = image_image_2  # Keep reference
                self.bg_image_id = self.canvas.create_image(0, 140, image=image_image_2, anchor="nw", tags="bg_image")
            except Exception as e:
                print(f"Could not load background image: {e}")
                # Fallback: create a colored rectangle
                self.canvas.create_rectangle(0, 140, width, height, fill="#FCECB7", outline="", tags="bg_fallback")
        except Exception as e:
            print(f"Could not load background image: {e}")
            # Fallback: create a colored rectangle
            self.canvas.create_rectangle(0, 140, width, height, fill="#FCECB7", outline="", tags="bg_fallback")
        
        # Create scalable background rectangles
        self.canvas.create_rectangle(0, 98, width, 140, fill="#FFDA0C", outline="", tags="nav_bg")
        self.canvas.create_rectangle(0, 0, width, 98, fill="#792D1B", outline="", tags="header_bg")
        
        # Welcome text and university info
        welcome_text = f"Welcome, {self.user_data['first_name']} {self.user_data['last_name']}!"
        user_role = self.user_type.title()
        
        # University header text - BOTH texts aligned to same x position
        self.canvas.create_text(128, 24, anchor="nw", text="PAMBAYANG DALUBHAASAAN NG MARILAO", 
                               fill="#FFDA0C", font=("Inter SemiBold", 24 * -1), tags="university_text")
        self.canvas.create_text(128, 57, anchor="nw", text="\"Where quality education is a right, not a privilege\"", 
                               fill="#FFDA0C", font=("Inter SemiBold", 14 * -1), tags="motto_text")
    
      
        # University logo (if available)
        try:
            image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
            self.image_1 = image_image_1  # Keep reference
            self.canvas.create_image(79.0, 49.0, image=image_image_1, tags="logo")
        except Exception as e:
            print(f"Could not load logo: {e}")

        # Create navigation text buttons (Home, Programs, Documents, Profile)
        self.button_home = Button(
            self.parent,
            text="Home",
            font=("Inter", 16),
            bg="#FFDA0C",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=self.show_home
        )

        self.button_programs = Button(
            self.parent,
            text="Programs",
            font=("Inter", 16),
            bg="#FFDA0C",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=self.show_programs
        )

        self.button_documents = Button(
            self.parent,
            text="Documents",
            font=("Inter", 16),
            bg="#FFDA0C",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=self.show_document_request
        )

        self.button_profile = Button(
            self.parent,
            text="Profile",
            font=("Inter", 16),
            bg="#FFDA0C",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=self.show_profile
        )

        self.button_logout = Button(
            self.parent,
            text="Logout",
            font=("Inter", 12),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            cursor="hand2",
            command=self.logout
        )

        # Initial button placement
        self.update_layout()

        # Show dashboard content
        self.show_dashboard()
        
        

    def show_dashboard(self):
        """Show the main dashboard content"""
        self.current_content = "dashboard"
        
        # Clear previous content
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_programs, 
                            self.button_documents, self.button_profile, 
                            self.button_logout]:
                widget.destroy()
        
        # Get current window size for responsive layout
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        
        #Dashboard content frame with responsive sizing
        dashboard_frame = Frame(self.parent, bg="#FCECB7")
        dashboard_frame.place(relx=0.5, rely=0.6, anchor="center", 
                            width=min(1000, width * 0.9), 
                            height=min(500, height * 0.7))
        
        # Welcome message with responsive font size
        font_size = max(20, min(28, int(width / 50)))
        welcome_label = Label(
            dashboard_frame,
            text="Document Request System Dashboard",
            font=("Inter Bold", font_size),
            bg="#FCECB7",
            fg="#792D1B"
        )
        welcome_label.pack(pady=30)
        
        # User info with responsive font size
        info_font_size = max(12, min(16, int(width / 80)))
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
            bg="#FCECB7",
            fg="#000000",
            justify="left"
        )
        info_label.pack(pady=20)
        
        # Quick actions based on user type
        action_font_size = max(12, min(14, int(width / 100)))
        if self.user_type == 'student':
            action_text = "Quick Actions:\n• Request a new document\n• View your request history\n• Update your profile information"
        else:
            action_text = "Quick Actions:\n• Process pending requests\n• View system reports\n• Manage user accounts"
        
        action_label = Label(
            dashboard_frame,
            text=action_text,
            font=("Inter", action_font_size),
            bg="#FCECB7",
            fg="#666666",
            justify="left"
        )
        action_label.pack(pady=20)

    def show_home(self):
        """Show home dashboard"""
        self.show_dashboard()

    def show_programs(self):
        """Show programs interface"""
        self.current_content = "programs"
        
        # Clear current window content but keep navigation
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_programs, 
                            self.button_documents, self.button_profile,
                            self.button_logout]:
                widget.destroy()
        
        # Create responsive content area
        content_frame = Frame(self.parent, bg="#FCECB7")
        content_frame.place(relx=0.5, rely=0.6, anchor="center", 
                          width=min(1000, self.parent.winfo_width() * 0.9), 
                          height=min(500, self.parent.winfo_height() * 0.7))
        
        # Programs content
        programs_label = Label(
            content_frame,
            text="Academic Programs\n\nThis area will contain information about\navailable academic programs and courses.",
            font=("Inter Bold", 18),
            bg="#FCECB7",
            fg="#792D1B",
            justify="center"
        )
        programs_label.pack(expand=True)

    def show_document_request(self):
        """Show document request interface"""
        self.current_content = "document_request"
        
        # Clear current window content but keep navigation
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_programs, 
                            self.button_documents, self.button_profile,
                             self.button_logout]:
                widget.destroy()
        
        # Create responsive content area
        content_frame = Frame(self.parent, bg="#FCECB7")
        content_frame.place(relx=0.5, rely=0.6, anchor="center", 
                          width=min(1000, self.parent.winfo_width() * 0.9), 
                          height=min(500, self.parent.winfo_height() * 0.7))
        
        # Document request content
        doc_label = Label(
            content_frame,
            text="Document Request Interface\n\nThis area will contain the document request form,\ndocument selection, and request history.",
            font=("Inter Bold", 18),
            bg="#FCECB7",
            fg="#792D1B",
            justify="center"
        )
        doc_label.pack(expand=True)

    def show_profile(self):
        """Show user profile"""
        self.current_content = "profile"
        
        # Clear current window content but keep navigation
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_programs, 
                            self.button_documents, self.button_profile,
                            self.button_logout]:
                widget.destroy()
        
        # Create responsive content area
        content_frame = Frame(self.parent, bg="#FCECB7")
        content_frame.place(relx=0.5, rely=0.6, anchor="center", 
                          width=min(1000, self.parent.winfo_width() * 0.9), 
                          height=min(500, self.parent.winfo_height() * 0.7))
        
        # Profile content
        profile_label = Label(
            content_frame,
            text="Profile Management Interface\n\nThis area will contain user profile information,\nedit forms, and account settings.",
            font=("Inter Bold", 18),
            bg="#FCECB7",
            fg="#792D1B",
            justify="center"
        )
        profile_label.pack(expand=True)

    def logout(self):
        """Logout user and return to login"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.logout_callback()
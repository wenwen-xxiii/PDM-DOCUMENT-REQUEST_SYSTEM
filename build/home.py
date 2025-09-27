from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Frame, Label, messagebox
from document_request import DocumentRequestWindow
from profile import ProfileWindow
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
    return Path(resource_path(f"resources/assets/frame6/{path}"))

class HomeWindow:
    def __init__(self, parent, user_data, user_type, logout_callback, get_db_connection):
        self.parent = parent
        self.user_data = user_data
        self.user_type = user_type
        self.logout_callback = logout_callback
        self.get_db_connection = get_db_connection
        
        self.setup_ui()
        
    def setup_ui(self):
        # Clear previous widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
            
        self.canvas = Canvas(
            self.parent,
            bg="#FFFFFF",
            height=768,
            width=1366,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Background
        self.canvas.create_rectangle(0, 0, 1366, 768, fill="#FFA500", outline="")
        self.canvas.create_rectangle(0, 0, 1366, 77, fill="#800000", outline="")
        
        # Welcome text
        welcome_text = f"Welcome, {self.user_data['first_name']} {self.user_data['last_name']}!"
        user_role = self.user_type.title()
        
        self.canvas.create_text(29, 10, anchor="nw", text=welcome_text, 
                               fill="#FFD700", font=("Inter Bold", 24))
        self.canvas.create_text(29, 39, anchor="nw", text=user_role, 
                               fill="#FFD700", font=("Inter Bold", 24))

        # Load images
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
            relief="flat"
        )

        self.button_reqdocu = Button(
            self.parent,
            image=self.img_reqdocu,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_document_request,
            relief="flat"
        )

        self.button_profile = Button(
            self.parent,
            image=self.img_profile,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_profile,
            relief="flat"
        )

        self.button_logout = Button(
            self.parent,
            image=self.img_logout,
            borderwidth=0,
            highlightthickness=0,
            command=self.logout,
            relief="flat"
        )

        # Place buttons
        self.button_home.place(relx=0.52, rely=0.03, anchor="n")
        self.button_reqdocu.place(relx=0.67, rely=0.03, anchor="n")
        self.button_profile.place(relx=0.82, rely=0.03, anchor="n")
        self.button_logout.place(relx=0.97, rely=0.03, anchor="n")

        # Show dashboard content
        self.show_dashboard()

    def show_dashboard(self):
        """Show the main dashboard content"""
        # Clear previous content
        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_reqdocu, 
                            self.button_profile, self.button_logout]:
                widget.destroy()
        
        # Dashboard content frame
        dashboard_frame = Frame(self.parent, bg="#FFFFFF", width=1200, height=600)
        dashboard_frame.place(relx=0.5, rely=0.55, anchor="center")
        
        # Welcome message
        welcome_label = Label(
            dashboard_frame,
            text=f"Document Request System Dashboard",
            font=("Inter Bold", 28),
            bg="#FFFFFF",
            fg="#800000"
        )
        welcome_label.pack(pady=20)
        
        # User info
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
            font=("Inter", 14),
            bg="#FFFFFF",
            fg="#000000",
            justify="left"
        )
        info_label.pack(pady=20)
        
        # Quick actions based on user type
        if self.user_type == 'student':
            action_text = "Quick Actions:\n• Request a new document\n• View your request history\n• Update your profile information"
        else:
            action_text = "Quick Actions:\n• Process pending requests\n• View system reports\n• Manage user accounts"
        
        action_label = Label(
            dashboard_frame,
            text=action_text,
            font=("Inter", 12),
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
        from document_request import DocumentRequestWindow
        # Clear current window
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Open document request window
        DocumentRequestWindow(self.parent, self.user_data, self.show_home, self.get_db_connection)

    def show_profile(self):
        """Show user profile"""
        from profile import ProfileWindow
        # Clear current window
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Open profile window
        ProfileWindow(self.parent, self.user_data, self.show_home, self.get_db_connection)

    def logout(self):
        """Logout user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.logout_callback()

    def destroy(self):
        """Clean up the window"""
        for widget in self.parent.winfo_children():
            widget.destroy()
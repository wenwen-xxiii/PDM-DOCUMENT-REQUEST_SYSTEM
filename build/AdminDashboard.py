# admindashboard.py
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Frame, messagebox
import mysql.connector
from mysql.connector import Error
import sys
import os

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/admindashboard/{path}"))

class AdminDashboard:
    def __init__(self, parent, user_data=None, logout_callback=None, get_db_connection=None):
        self.parent = parent
        self.user_data = user_data or {}
        self.logout_callback = logout_callback
        self.get_db_connection = get_db_connection
        
        # Store all image references to prevent garbage collection
        self.images = []
        
        # Statistics data
        self.stats_data = {
            'total_students': 0,
            'total_requests': 0,
            'pending_requests': 0,
            'total_feedback': 0
        }
        
        self.setup_ui()
        self.load_statistics()
        self.update_display()
        
    def setup_ui(self):
        """Setup the admin dashboard UI"""
        self.canvas = Canvas(
            self.parent,
            bg="#FCECB7",
            height=790,
            width=1270,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)
        
        self.create_ui_elements()
        
    def create_ui_elements(self):
        """Create all UI elements"""
        # Store all image references
        self.images = []
        
        # Header
        self.canvas.create_rectangle(0.0, 0.0, 1270.0, 98.0, fill="#792D1B", outline="")
        
        self.canvas.create_text(
            128.0, 24.0, anchor="nw", text="PAMBAYANG DALUBHAASAAN NG MARILAO",
            fill="#FFDA0C", font=("Inter SemiBold", 24 * -1)
        )
        
        self.canvas.create_text(
            128.0, 47.0, anchor="nw", text="\"Where quality education is a right, not a privilege\"",
            fill="#FFDA0C", font=("Inter SemiBold", 14 * -1)
        )

        # University logo
        image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
        self.images.append(image_image_1)
        self.canvas.create_image(79.0, 49.0, image=image_image_1)

        # Navigation bar
        self.canvas.create_rectangle(0.0, 98.0, 1270.0, 140.0, fill="#FFDA0C", outline="")

        # Side navigation background
        image_sidenav_bg = PhotoImage(file=relative_to_assets("image_sidenav_bg.png"))
        self.images.append(image_sidenav_bg)
        self.canvas.create_image(168.0, 510.0, image=image_sidenav_bg)

        # Profile section
        image_profile_bg = PhotoImage(file=relative_to_assets("image_profile_bg.png"))
        self.images.append(image_profile_bg)
        self.canvas.create_image(168.0, 218.0, image=image_profile_bg)

        # Profile picture
        image_profile_pic = PhotoImage(file=relative_to_assets("image_profile_pic.png"))
        self.images.append(image_profile_pic)
        self.canvas.create_image(77.0, 218.0, image=image_profile_pic)

        # Main content area
        self.canvas.create_rectangle(326.0, 179.0, 1221.0, 753.0, fill="#FFFFFF", outline="")

        # Admin info
        admin_name = f"{self.user_data.get('first_name', 'Admin')} {self.user_data.get('last_name', 'User')}"
        self.canvas.create_text(128.0, 193.0, anchor="nw", text=admin_name,
                               fill="#F2F2F2", font=("Inter", 20 * -1))
        self.canvas.create_text(128.0, 220.0, anchor="nw", text="Admin",
                               fill="#F2F2F2", font=("Inter", 16 * -1))

        # Dashboard title
        self.canvas.create_text(351.0, 202.0, anchor="nw", text="Dashboard",
                               fill="#303030", font=("Inter SemiBold", 24 * -1))

        # Create navigation buttons
        self.create_navigation_buttons()
        
        # Create dashboard panels
        self.create_dashboard_panels()
        
    def create_navigation_buttons(self):
        """Create navigation buttons"""
        # Dashboard button
        button_dashboard_img = PhotoImage(file=relative_to_assets("button_dashboard.png"))
        self.images.append(button_dashboard_img)
        self.button_dashboard = Button(
            self.parent,
            image=button_dashboard_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_dashboard,
            relief="flat"
        )
        self.button_dashboard.place(x=49.0, y=286.0, width=239.0, height=47.0)

        # Students button
        button_students_img = PhotoImage(file=relative_to_assets("button_students.png"))
        self.images.append(button_students_img)
        self.button_students = Button(
            self.parent,
            image=button_students_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_students,
            relief="flat"
        )
        self.button_students.place(x=49.0, y=346.0, width=239.0, height=47.0)

        # Documents button
        button_documents_img = PhotoImage(file=relative_to_assets("button_documents.png"))
        self.images.append(button_documents_img)
        self.button_documents = Button(
            self.parent,
            image=button_documents_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_documents,
            relief="flat"
        )
        self.button_documents.place(x=49.0, y=406.0, width=239.0, height=47.0)

        # Requests button
        button_requests_img = PhotoImage(file=relative_to_assets("button_requests.png"))
        self.images.append(button_requests_img)
        self.button_requests = Button(
            self.parent,
            image=button_requests_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_requests,
            relief="flat"
        )
        self.button_requests.place(x=49.0, y=466.0, width=239.0, height=47.0)

        # Billing button
        button_billing_img = PhotoImage(file=relative_to_assets("button_billing.png"))
        self.images.append(button_billing_img)
        self.button_billing = Button(
            self.parent,
            image=button_billing_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_billing,
            relief="flat"
        )
        self.button_billing.place(x=49.0, y=526.0, width=239.0, height=47.0)

        # Feedback button
        button_feedback_img = PhotoImage(file=relative_to_assets("button_feedback.png"))
        self.images.append(button_feedback_img)
        self.button_feedback = Button(
            self.parent,
            image=button_feedback_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_feedback,
            relief="flat"
        )
        self.button_feedback.place(x=49.0, y=586.0, width=239.0, height=47.0)

        # Users button
        button_users_img = PhotoImage(file=relative_to_assets("button_users.png"))
        self.images.append(button_users_img)
        self.button_users = Button(
            self.parent,
            image=button_users_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_users,
            relief="flat"
        )
        self.button_users.place(x=49.0, y=646.0, width=239.0, height=47.0)

    def create_dashboard_panels(self):
        """Create dashboard statistic panels"""
        # Panel backgrounds
        image_panel_students = PhotoImage(file=relative_to_assets("image_dashboard_panel_no_students.png"))
        self.images.append(image_panel_students)
        self.canvas.create_image(480.0, 310.0, image=image_panel_students)

        image_panel_requests = PhotoImage(file=relative_to_assets("image_dashboard_panel_no_request.png"))
        self.images.append(image_panel_requests)
        self.canvas.create_image(782.0, 310.0, image=image_panel_requests)

        image_panel_feedback = PhotoImage(file=relative_to_assets("image_dashboard_panel_no_feedback.png"))
        self.images.append(image_panel_feedback)
        self.canvas.create_image(1067.0, 310.0, image=image_panel_feedback)

        image_panel2 = PhotoImage(file=relative_to_assets("image_dashboard_panel2.png"))
        self.images.append(image_panel2)
        self.canvas.create_image(617.0, 514.0, image=image_panel2)

        image_panel5 = PhotoImage(file=relative_to_assets("image_dashboard_panel5.png"))
        self.images.append(image_panel5)
        self.canvas.create_image(1048.0, 514.0, image=image_panel5)

        image_panel_footer = PhotoImage(file=relative_to_assets("image_dashboard_panel_footer.png"))
        self.images.append(image_panel_footer)
        self.canvas.create_image(774.0, 694.0, image=image_panel_footer)

        # Icons
        image_icon_user = PhotoImage(file=relative_to_assets("image_icon_user.png"))
        self.images.append(image_icon_user)
        self.canvas.create_image(547.0, 330.0, image=image_icon_user)

        image_icon_request = PhotoImage(file=relative_to_assets("image_icon_request.png"))
        self.images.append(image_icon_request)
        self.canvas.create_image(861.0, 327.0, image=image_icon_request)

        image_icon_feedback = PhotoImage(file=relative_to_assets("image_icon_feedback.png"))
        self.images.append(image_icon_feedback)
        self.canvas.create_image(1153.0, 330.0, image=image_icon_feedback)

        # Statistics text (will be updated with real data)
        self.students_text = self.canvas.create_text(480.0, 310.0, text="0", 
                                                    fill="#FFFFFF", font=("Inter", 24 * -1, "bold"))
        self.requests_text = self.canvas.create_text(782.0, 310.0, text="0", 
                                                   fill="#FFFFFF", font=("Inter", 24 * -1, "bold"))
        self.feedback_text = self.canvas.create_text(1067.0, 310.0, text="0", 
                                                   fill="#FFFFFF", font=("Inter", 24 * -1, "bold"))
        self.pending_text = self.canvas.create_text(617.0, 514.0, text="0", 
                                                  fill="#FFFFFF", font=("Inter", 24 * -1, "bold"))

    def load_statistics(self):
        """Load statistics from database"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # Total students
            cursor.execute("SELECT COUNT(*) as total FROM students WHERE is_active = TRUE")
            result = cursor.fetchone()
            self.stats_data['total_students'] = result['total'] if result else 0
            
            # Total requests
            cursor.execute("SELECT COUNT(*) as total FROM document_requests")
            result = cursor.fetchone()
            self.stats_data['total_requests'] = result['total'] if result else 0
            
            # Pending requests
            cursor.execute("SELECT COUNT(*) as total FROM document_requests WHERE status = 'submitted'")
            result = cursor.fetchone()
            self.stats_data['pending_requests'] = result['total'] if result else 0
            
            # Total feedback (if you have a feedback table)
            cursor.execute("SELECT COUNT(*) as total FROM feedback")
            result = cursor.fetchone()
            self.stats_data['total_feedback'] = result['total'] if result else 0
            
            cursor.close()
            connection.close()
            
        except Error as e:
            print(f"Error loading statistics: {e}")
            # Use default values if database error occurs

    def update_display(self):
        """Update the display with current statistics"""
        self.canvas.itemconfig(self.students_text, text=str(self.stats_data['total_students']))
        self.canvas.itemconfig(self.requests_text, text=str(self.stats_data['total_requests']))
        self.canvas.itemconfig(self.feedback_text, text=str(self.stats_data['total_feedback']))
        self.canvas.itemconfig(self.pending_text, text=str(self.stats_data['pending_requests']))

    # Navigation methods
    def show_dashboard(self):
        """Show dashboard (refresh statistics)"""
        self.load_statistics()
        self.update_display()
        messagebox.showinfo("Dashboard", "Dashboard refreshed!")

    def show_students(self):
        """Show students management"""
        messagebox.showinfo("Students", "Student management feature coming soon!")

    def show_documents(self):
        """Show document types management"""
        messagebox.showinfo("Documents", "Document types management feature coming soon!")

    def show_requests(self):
        """Show document requests management"""
        messagebox.showinfo("Requests", "Document requests management feature coming soon!")

    def show_billing(self):
        """Show billing and payments"""
        messagebox.showinfo("Billing", "Billing and payments feature coming soon!")

    def show_feedback(self):
        """Show feedback management"""
        messagebox.showinfo("Feedback", "Feedback management feature coming soon!")

    def show_users(self):
        """Show user management"""
        messagebox.showinfo("Users", "User management feature coming soon!")

    def logout(self):
        """Logout admin"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            if self.logout_callback:
                self.logout_callback()

    def destroy(self):
        """Clean up when window is closed"""
        try:
            self.canvas.destroy()
        except:
            pass
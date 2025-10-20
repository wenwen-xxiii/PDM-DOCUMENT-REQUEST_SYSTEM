# admindashboard.py
from pathlib import Path
from tkinter import (
    Tk,
    Canvas,
    Entry,
    Text,
    Button,
    PhotoImage,
    Frame,
    messagebox,
    Label,
)
import mysql.connector
from mysql.connector import Error
import sys
import os
from admin_request import AdminRequestManager
from admin_documents import AdminDocumentManager
from admin_billing import AdminBillingManager
from admin_student import AdminStudentManager
from admin_user import AdminUserManager

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build.admin_feedback import AdminFeedbackManager
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
    def __init__(
        self, parent, user_data=None, logout_callback=None, get_db_connection=None
    ):
        self.parent = parent
        self.user_data = user_data or {}
        self.logout_callback = logout_callback
        self.get_db_connection = get_db_connection

        # Store all image references to prevent garbage collection
        self.images = []

        # Statistics data
        self.stats_data = {
            "total_students": 0,
            "total_requests": 0,
            "pending_requests": 0,
            "completed_requests": 0,
            "total_feedback": 0,
        }

        # Content management
        self.current_content = "dashboard"
        self.content_frame = None

        self.setup_ui()
        self.load_statistics()
        self.update_display()
        # Track chart items drawn on the main canvas so we can clear/redraw
        self.chart_items = []

    def setup_ui(self):
        """Setup the admin dashboard UI"""
        self.canvas = Canvas(
            self.parent,
            bg="#FCECB7",
            height=790,
            width=1270,
            bd=0,
            highlightthickness=0,
            relief="ridge",
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
            128.0,
            24.0,
            anchor="nw",
            text="PAMBAYANG DALUBHAASAAN NG MARILAO",
            fill="#FFDA0C",
            font=("Inter SemiBold", 24 * -1),
        )

        self.canvas.create_text(
            128.0,
            47.0,
            anchor="nw",
            text='"Where quality education is a right, not a privilege"',
            fill="#FFDA0C",
            font=("Inter SemiBold", 14 * -1),
        )

        # University logo
        image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
        self.images.append(image_image_1)
        self.canvas.create_image(79.0, 49.0, image=image_image_1)

        # Navigation bar
        self.canvas.create_rectangle(
            0.0, 98.0, 1270.0, 140.0, fill="#FFDA0C", outline=""
        )

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
        image_image_5 = PhotoImage(file=relative_to_assets("image_content.png"))
        self.images.append(image_image_5)
        self.image_content = self.canvas.create_image(773.0, 466.0, image=image_image_5)

        # Admin info
        admin_name = f"{self.user_data.get('first_name', 'Admin')} {self.user_data.get('last_name', 'User')}"
        self.canvas.create_text(
            128.0,
            193.0,
            anchor="nw",
            text=admin_name,
            fill="#F2F2F2",
            font=("Inter", 20 * -1),
        )
        self.canvas.create_text(
            128.0,
            220.0,
            anchor="nw",
            text="Admin",
            fill="#F2F2F2",
            font=("Inter", 16 * -1),
        )

        # Dashboard title
        self.title_text = self.canvas.create_text(
            351.0,
            202.0,
            anchor="nw",
            text="Dashboard",
            fill="#303030",
            font=("Inter SemiBold", 24 * -1),
        )

        # Create navigation buttons
        self.create_navigation_buttons()

        # Create dashboard panels
        self.create_dashboard_panels()

        # Add text-based logout button in header
        self.create_header_logout_button()

        # Create content frame
        self.create_content_frame()

    def create_content_frame(self):
        """Create the main content frame where all content will be displayed"""
        self.content_frame = Frame(
            self.parent, bg="#FFFFFF", bd=0, highlightthickness=0
        )
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)
        # Initially hide the content frame so dashboard panels are visible
        self.content_frame.place_forget()

    def create_header_logout_button(self):
        """Create text-based logout button in header"""
        self.button_logout = Button(
            self.parent,
            text="Logout",
            font=("Inter", 12),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            cursor="hand2",
            command=self.logout,
        )
        self.button_logout.place(relx=0.95, rely=0.03, anchor="ne")

    def create_navigation_buttons(self):
        """Create navigation buttons"""
        # Dashboard button
        button_dashboard_img = PhotoImage(
            file=relative_to_assets("button_dashboard.png")
        )
        self.images.append(button_dashboard_img)
        self.button_dashboard = Button(
            self.parent,
            image=button_dashboard_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_dashboard,
            relief="flat",
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
            relief="flat",
        )
        self.button_students.place(x=49.0, y=346.0, width=239.0, height=47.0)

        # Documents button
        button_documents_img = PhotoImage(
            file=relative_to_assets("button_documents.png")
        )
        self.images.append(button_documents_img)
        self.button_documents = Button(
            self.parent,
            image=button_documents_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_documents,
            relief="flat",
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
            relief="flat",
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
            relief="flat",
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
            relief="flat",
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
            relief="flat",
        )
        self.button_users.place(x=49.0, y=646.0, width=239.0, height=47.0)

    def create_dashboard_panels(self):
        """Create dashboard statistic panels matching the Figma layout"""
        # Card backgrounds (top row and middle row)
        # Students
        self.canvas.create_rectangle(
            351.0, 252.0, 610.0, 369.0, fill="#F5F5F5", outline=""
        )
        # Total Request
        self.canvas.create_rectangle(
            652.0, 252.0, 912.0, 369.0, fill="#F5F5F5", outline=""
        )
        # Total Feedback
        self.canvas.create_rectangle(
            938.0, 252.0, 1197.0, 369.0, fill="#F5F5F5", outline=""
        )
        # Pending Request
        self.canvas.create_rectangle(
            351.0, 394.0, 610.0, 511.0, fill="#F5F5F5", outline=""
        )
        # Payment Pending
        self.canvas.create_rectangle(
            653.0, 394.0, 912.0, 511.0, fill="#F5F5F5", outline=""
        )
        # Completed Request
        self.canvas.create_rectangle(
            938.0, 396.0, 1197.0, 513.0, fill="#F5F5F5", outline=""
        )

        # Bottom large panels
        # Top Request Document
        self.canvas.create_rectangle(
            351.0, 539.0, 754.0, 731.0, fill="#F5F5F5", outline=""
        )
        # Monthly Document Request
        self.canvas.create_rectangle(
            803.0, 540.0, 1197.0, 732.0, fill="#F5F5F5", outline=""
        )

        # Labels
        self.canvas.create_text(
            376.0,
            269.0,
            anchor="nw",
            text="Students",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            672.0,
            269.0,
            anchor="nw",
            text="Total Request",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            954.0,
            271.0,
            anchor="nw",
            text="Total Feedback",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            376.0,
            414.0,
            anchor="nw",
            text="Payment Pending",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            678.0,
            414.0,
            anchor="nw",
            text="Total Processing",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            963.0,
            416.0,
            anchor="nw",
            text="Completed Request",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            382.0,
            564.0,
            anchor="nw",
            text="Top Request Document",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            838.0,
            564.0,
            anchor="nw",
            text="Montly Document Request",
            fill="#000000",
            font=("Inter", 16 * -1),
        )

        # Numeric values (wired to existing stats where available)
        self.students_text = self.canvas.create_text(
            387.0, 310.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.requests_text = self.canvas.create_text(
            683.0, 310.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.feedback_text = self.canvas.create_text(
            965.0, 312.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.pending_text = self.canvas.create_text(
            387.0, 455.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        # Processing is not yet computed separately; initialize to 0 for now
        self.processing_text = self.canvas.create_text(
            689.0, 455.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.completed_text = self.canvas.create_text(
            974.0, 457.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )

    def add_card_labels(self):
        """Add proper labels and descriptions for all cards"""
        # Card labels with better styling and positioning
        self.canvas.create_text(
            450.0,
            340.0,
            text="Total Students",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            750.0,
            340.0,
            text="Total Requests",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            1050.0,
            340.0,
            text="Total Feedback",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            600.0,
            540.0,
            text="Pending Requests",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            900.0,
            540.0,
            text="Completed Requests",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )

        # Add section header - Changed to "Dashboard"
        self.canvas.create_text(
            400.0,
            200.0,
            text="Dashboard",
            fill="#2C3E50",
            font=("Inter", 18 * -1, "bold"),
        )

        # Add decorative elements
        self.add_decorative_elements()

    def add_decorative_elements(self):
        """Add decorative elements and visual enhancements"""
        # Add subtle borders around cards for better definition
        card_positions = [
            (450, 300),  # Students
            (750, 300),  # Requests
            (1050, 300),  # Feedback
            (600, 500),  # Pending
            (900, 500),  # Completed
        ]

        for x, y in card_positions:
            # Add subtle shadow effect
            self.canvas.create_rectangle(
                x - 100, y - 30, x + 100, y + 30, fill="", outline="#E8F4FD", width=2
            )

        # Add status indicators
        status_colors = ["#27AE60", "#3498DB", "#9C27B0", "#F39C12", "#4CAF50"]
        for i, (x, y) in enumerate(card_positions):
            self.canvas.create_oval(
                x + 60, y - 20, x + 70, y - 10, fill=status_colors[i], outline=""
            )

    def load_statistics(self):
        """Load statistics from database - FIXED VERSION"""
        try:
            connection = self.get_db_connection()
            if not connection:
                print("❌ No database connection available")
                return

            cursor = connection.cursor(dictionary=True)

            # Total students - FIXED: Use enrollment_status instead of is_active
            cursor.execute(
                "SELECT COUNT(*) as total FROM students WHERE enrollment_status = 'Enrolled'"
            )
            result = cursor.fetchone()
            self.stats_data["total_students"] = result["total"] if result else 0
            print(f"✅ Total students: {self.stats_data['total_students']}")

            # Total requests
            cursor.execute("SELECT COUNT(*) as total FROM document_requests")
            result = cursor.fetchone()
            self.stats_data["total_requests"] = result["total"] if result else 0
            print(f"✅ Total requests: {self.stats_data['total_requests']}")

            # Pending requests - FIXED: Use correct status values from your schema
            cursor.execute(
                """
                SELECT COUNT(*) as total FROM document_requests
                WHERE status IN ('under_review', 'payment_pending', 'processing')
            """
            )
            result = cursor.fetchone()
            self.stats_data["pending_requests"] = result["total"] if result else 0
            print(f"✅ Pending requests: {self.stats_data['pending_requests']}")

            # Completed requests - NEW CARD
            cursor.execute(
                """
                SELECT COUNT(*) as total FROM document_requests
                WHERE status = 'completed'
            """
            )
            result = cursor.fetchone()
            self.stats_data["completed_requests"] = result["total"] if result else 0
            print(f"✅ Completed requests: {self.stats_data['completed_requests']}")

            # Total feedback
            cursor.execute("SELECT COUNT(*) as total FROM feedback")
            result = cursor.fetchone()
            self.stats_data["total_feedback"] = result["total"] if result else 0
            print(f"✅ Total feedback: {self.stats_data['total_feedback']}")

            cursor.close()
            connection.close()

            print("✅ Statistics loaded successfully")

        except Error as e:
            print(f"❌ Error loading statistics: {e}")
            # Use default values if database error occurs
            self.stats_data = {
                "total_students": 0,
                "total_requests": 0,
                "pending_requests": 0,
                "completed_requests": 0,
                "total_feedback": 0,
            }

    def update_display(self):
        """Update the display with current statistics"""
        try:
            self.canvas.itemconfig(
                self.students_text, text=str(self.stats_data["total_students"])
            )
            self.canvas.itemconfig(
                self.requests_text, text=str(self.stats_data["total_requests"])
            )
            self.canvas.itemconfig(
                self.feedback_text, text=str(self.stats_data["total_feedback"])
            )
            self.canvas.itemconfig(
                self.pending_text, text=str(self.stats_data["pending_requests"])
            )
            self.canvas.itemconfig(
                self.completed_text, text=str(self.stats_data["completed_requests"])
            )
            print("✅ Display updated with statistics")
        except Exception as e:
            print(f"❌ Error updating display: {e}")

    def clear_content(self):
        """Clear the content frame"""
        if self.content_frame:
            for widget in self.content_frame.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass

    def show_dashboard_content(self):
        """Show dashboard content in the content frame"""
        self.clear_content()

        # Hide content frame to show dashboard panels
        self.content_frame.place_forget()

        # Update title
        self.canvas.itemconfig(self.title_text, text="Dashboard")

        # Show statistics panels
        self.canvas.itemconfig(self.students_text, state="normal")
        self.canvas.itemconfig(self.requests_text, state="normal")
        self.canvas.itemconfig(self.feedback_text, state="normal")
        self.canvas.itemconfig(self.pending_text, state="normal")
        self.canvas.itemconfig(self.completed_text, state="normal")
        # Ensure processing count is also visible if present
        try:
            self.canvas.itemconfig(self.processing_text, state="normal")
        except Exception:
            pass

        # Load fresh statistics
        self.load_statistics()
        self.update_display()
        # Draw charts for requests by type (bar) and monthly requests (line)
        self.update_charts()

    def clear_charts(self):
        """Remove previously drawn chart items from the canvas"""
        try:
            # Delete by tag first to ensure all chart elements are removed
            try:
                self.canvas.delete("chart")
            except Exception:
                pass
            for item_id in getattr(self, "chart_items", []):
                try:
                    self.canvas.delete(item_id)
                except Exception:
                    pass
            self.chart_items = []
        except Exception:
            self.chart_items = []

    def update_charts(self):
        """Fetch data and render dashboard charts"""
        # Always clear previous charts before drawing new ones
        self.clear_charts()
        try:
            by_type = self.fetch_request_counts_by_type(limit=6)
            self.draw_bar_chart_requests_by_type(by_type)
        except Exception as e:
            print(f"❌ Error drawing requests-by-type bar chart: {e}")
        try:
            monthly = self.fetch_monthly_request_counts(months=6)
            self.draw_line_chart_monthly_requests(monthly)
        except Exception as e:
            print(f"❌ Error drawing monthly requests line chart: {e}")
        # Bring charts to the very front
        try:
            self.canvas.tag_raise("chart")
        except Exception:
            pass

    def fetch_request_counts_by_type(self, limit=6):
        """Return list of tuples [(type_name, count), ...] limited to top N by count"""
        data = []
        try:
            connection = self.get_db_connection()
            if not connection:
                return data
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT COALESCE(dt.code, dt.name) AS label, COUNT(dr.request_id) AS total
                FROM document_requests dr
                JOIN document_types dt ON dt.document_type_id = dr.document_type_id
                GROUP BY dt.document_type_id, label
                ORDER BY total DESC
                LIMIT %s
                """,
                (limit,),
            )
            for row in cursor.fetchall():
                # row: (type_name, total)
                data.append((row[0], int(row[1] or 0)))
            cursor.close()
            connection.close()
        except Error as e:
            print(f"❌ Error fetching request counts by type: {e}")
        return data

    def fetch_monthly_request_counts(self, months=6):
        """Return list of tuples [(label, count)] for last N months including current.
        Label format: MMM (e.g., Jan)
        """
        # Build default zeroed series in case DB returns sparse data
        import datetime

        today = datetime.date.today().replace(day=1)
        month_keys = []
        for i in range(months - 1, -1, -1):
            m = (today - datetime.timedelta(days=31 * i)).replace(day=1)
            key = m.strftime("%Y-%m")
            label = m.strftime("%b")
            month_keys.append((key, label))

        counts = {key: 0 for key, _ in month_keys}

        try:
            connection = self.get_db_connection()
            if not connection:
                return [(label, counts[key]) for key, label in month_keys]
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT DATE_FORMAT(request_date, '%Y-%m') AS ym, COUNT(*) AS total
                FROM document_requests
                WHERE request_date >= DATE_SUB(DATE_FORMAT(NOW(), '%Y-%m-01'), INTERVAL %s MONTH)
                GROUP BY ym
                ORDER BY ym
                """,
                (months - 1,),
            )
            for ym, total in cursor.fetchall():
                counts[str(ym)] = int(total or 0)
            cursor.close()
            connection.close()
        except Error as e:
            print(f"❌ Error fetching monthly request counts: {e}")

        return [(label, counts[key]) for key, label in month_keys]

    def draw_bar_chart_requests_by_type(self, data):
        """Draw a simple bar chart in the left bottom panel (Top Request Document)."""
        # Panel bounds from create_dashboard_panels: (351,539) to (754,731)
        x0, y0, x1, y1 = 351.0, 539.0, 754.0, 731.0
        padding_left, padding_right = 20, 16
        padding_top, padding_bottom = 56, 28

        plot_x0 = x0 + padding_left
        plot_x1 = x1 - padding_right
        plot_y0 = y0 + padding_top
        plot_y1 = y1 - padding_bottom

        # Axes
        axis_color = "#A0A0A0"
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y1, plot_x1, plot_y1, fill=axis_color, tags=("chart",)
            )
        )
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y0, plot_x0, plot_y1, fill=axis_color, tags=("chart",)
            )
        )

        if not data:
            self.chart_items.append(
                self.canvas.create_text(
                    (plot_x0 + plot_x1) / 2,
                    (plot_y0 + plot_y1) / 2,
                    text="No data",
                    fill="#808080",
                    font=("Inter", 12),
                    tags=("chart",),
                )
            )
            return

        max_val = max((c for _, c in data), default=0) or 1
        n = len(data)
        bar_gap = 8
        total_width = plot_x1 - plot_x0
        bar_width = max(12, (total_width - (n + 1) * bar_gap) / max(n, 1))

        # Draw bars and labels
        fill_color = "#3498DB"
        label_color = "#303030"
        value_color = "#505050"

        for i, (name, count) in enumerate(data):
            bx0 = plot_x0 + bar_gap + i * (bar_width + bar_gap)
            bx1 = bx0 + bar_width
            height_ratio = float(count) / float(max_val)
            by1 = plot_y1
            by0 = plot_y1 - height_ratio * (plot_y1 - plot_y0)
            rect = self.canvas.create_rectangle(
                bx0, by0, bx1, by1, fill=fill_color, outline="", tags=("chart",)
            )
            self.chart_items.append(rect)
            # Value label above bar
            val = self.canvas.create_text(
                (bx0 + bx1) / 2,
                by0 - 8,
                text=str(count),
                fill=value_color,
                font=("Inter", 10),
                tags=("chart",),
            )
            self.chart_items.append(val)
            # X label (truncate)
            short = name if len(name) <= 10 else name[:9] + "…"
            lbl = self.canvas.create_text(
                (bx0 + bx1) / 2,
                by1 + 10,
                text=short,
                fill=label_color,
                font=("Inter", 9),
                tags=("chart",),
            )
            self.chart_items.append(lbl)

    def draw_line_chart_monthly_requests(self, data):
        """Draw a simple line chart in the right bottom panel (Monthly Document Request)."""
        # Panel bounds from create_dashboard_panels: (803,540) to (1197,732)
        x0, y0, x1, y1 = 803.0, 540.0, 1197.0, 732.0
        padding_left, padding_right = 36, 16
        padding_top, padding_bottom = 56, 28

        plot_x0 = x0 + padding_left
        plot_x1 = x1 - padding_right
        plot_y0 = y0 + padding_top
        plot_y1 = y1 - padding_bottom

        # Axes
        axis_color = "#A0A0A0"
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y1, plot_x1, plot_y1, fill=axis_color, tags=("chart",)
            )
        )
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y0, plot_x0, plot_y1, fill=axis_color, tags=("chart",)
            )
        )

        if not data:
            self.chart_items.append(
                self.canvas.create_text(
                    (plot_x0 + plot_x1) / 2,
                    (plot_y0 + plot_y1) / 2,
                    text="No data",
                    fill="#808080",
                    font=("Inter", 12),
                    tags=("chart",),
                )
            )
            return

        labels = [label for (label, _) in data]
        values = [val for (_, val) in data]
        max_val = max(values or [0]) or 1

        n = len(values)
        if n == 1:
            xs = [plot_x0 + (plot_x1 - plot_x0) / 2]
        else:
            step = (plot_x1 - plot_x0) / float(max(n - 1, 1))
            xs = [plot_x0 + i * step for i in range(n)]
        ys = [plot_y1 - (v / float(max_val)) * (plot_y1 - plot_y0) for v in values]

        # Grid lines (optional)
        grid_color = "#E0E0E0"
        for g in range(1, 4):
            gy = plot_y0 + g * (plot_y1 - plot_y0) / 4.0
            self.chart_items.append(
                self.canvas.create_line(
                    plot_x0, gy, plot_x1, gy, fill=grid_color, tags=("chart",)
                )
            )

        # Polyline
        line_color = "#E67E22"
        dot_color = "#D35400"
        for i in range(n - 1):
            seg = self.canvas.create_line(
                xs[i],
                ys[i],
                xs[i + 1],
                ys[i + 1],
                fill=line_color,
                width=2,
                tags=("chart",),
            )
            self.chart_items.append(seg)
        for i in range(n):
            dot = self.canvas.create_oval(
                xs[i] - 3,
                ys[i] - 3,
                xs[i] + 3,
                ys[i] + 3,
                fill=dot_color,
                outline="",
                tags=("chart",),
            )
            self.chart_items.append(dot)
            # Value labels
            val = self.canvas.create_text(
                xs[i],
                ys[i] - 10,
                text=str(values[i]),
                fill="#505050",
                font=("Inter", 10),
                tags=("chart",),
            )
            self.chart_items.append(val)
            # X labels
            lbl = self.canvas.create_text(
                xs[i],
                plot_y1 + 12,
                text=labels[i],
                fill="#303030",
                font=("Inter", 9),
                tags=("chart",),
            )
            self.chart_items.append(lbl)

    def show_requests_content(self):
        """Show requests management content in the content frame"""
        self.clear_content()
        # Hide charts when leaving dashboard panels
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Requests")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create requests management interface
        self.create_requests_interface()

    def create_requests_interface(self):
        """Create the requests management interface inside content frame"""
        try:
            # Create requests manager inside the content frame
            self.requests_manager = AdminRequestManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Requests interface loaded successfully")
        except Exception as e:
            print(f"❌ Error creating requests interface: {e}")
            messagebox.showerror(
                "Error", f"Failed to load requests interface: {str(e)}"
            )

    # Navigation methods
    def show_dashboard(self):
        """Show dashboard"""
        print("🔄 Showing dashboard...")
        self.current_content = "dashboard"
        self.show_dashboard_content()

    def show_students(self):
        """Show students management"""
        self.current_content = "students"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Students Management")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create and show student manager
        try:
            self.student_manager = AdminStudentManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Student manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading student manager: {e}")
            messagebox.showerror("Error", f"Failed to load student manager: {str(e)}")

    def show_documents(self):
        """Show document types management"""
        self.current_content = "documents"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Document Types")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create and show document types manager
        try:
            self.document_manager = AdminDocumentManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Document types manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading document types manager: {e}")
            messagebox.showerror(
                "Error", f"Failed to load document types manager: {str(e)}"
            )

    def show_requests(self):
        """Show document requests management"""
        print("🔄 Showing requests management...")
        self.current_content = "requests"
        self.show_requests_content()

    def show_billing(self):
        """Show billing and payments"""
        self.current_content = "billing"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Billing & Payments")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create and show billing manager
        try:
            self.billing_manager = AdminBillingManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Billing manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading billing manager: {e}")
            messagebox.showerror("Error", f"Failed to load billing manager: {str(e)}")

    def show_feedback(self):
        """Show feedback management"""
        self.current_content = "feedback"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Feedback Management")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")

        try:
            self.feedback_manager = AdminFeedbackManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Feedback manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading feedback manager: {e}")
            messagebox.showerror("Error", f"Failed to load feedback manager: {str(e)}")

    def show_users(self):
        """Show user management"""
        self.current_content = "users"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="User Management")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")

        # Create and show user manager
        try:
            self.user_manager = AdminUserManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ User manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading user manager: {e}")
            messagebox.showerror("Error", f"Failed to load user manager: {str(e)}")

    def logout(self):
        """Logout admin"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            print("🚪 Logging out admin...")
            if self.logout_callback:
                self.logout_callback()

    def destroy(self):
        """Clean up when window is closed"""
        try:
            self.canvas.destroy()
        except:
            pass


# admindashboard.py
from pathlib import Path
from tkinter import (
    Tk,
    Canvas,
    Entry,
    Text,
    Button,
    PhotoImage,
    Frame,
    messagebox,
    Label,
)
import mysql.connector
from mysql.connector import Error
import sys
import os
from admin_request import AdminRequestManager
from admin_documents import AdminDocumentManager
from admin_billing import AdminBillingManager
from admin_student import AdminStudentManager
from admin_user import AdminUserManager

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build.admin_feedback import AdminFeedbackManager
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
    def __init__(
        self, parent, user_data=None, logout_callback=None, get_db_connection=None
    ):
        self.parent = parent
        self.user_data = user_data or {}
        self.logout_callback = logout_callback
        self.get_db_connection = get_db_connection

        # Store all image references to prevent garbage collection
        self.images = []

        # Statistics data
        self.stats_data = {
            "total_students": 0,
            "total_requests": 0,
            "pending_requests": 0,
            "completed_requests": 0,
            "total_feedback": 0,
        }

        # Content management
        self.current_content = "dashboard"
        self.content_frame = None

        self.setup_ui()
        self.load_statistics()
        self.update_display()
        # Track chart items drawn on the main canvas so we can clear/redraw
        self.chart_items = []
        # Draw charts immediately on login
        self.update_charts()

    def setup_ui(self):
        """Setup the admin dashboard UI"""
        self.canvas = Canvas(
            self.parent,
            bg="#FCECB7",
            height=790,
            width=1270,
            bd=0,
            highlightthickness=0,
            relief="ridge",
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
            128.0,
            24.0,
            anchor="nw",
            text="PAMBAYANG DALUBHAASAAN NG MARILAO",
            fill="#FFDA0C",
            font=("Inter SemiBold", 24 * -1),
        )

        self.canvas.create_text(
            128.0,
            47.0,
            anchor="nw",
            text='"Where quality education is a right, not a privilege"',
            fill="#FFDA0C",
            font=("Inter SemiBold", 14 * -1),
        )

        # University logo
        image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
        self.images.append(image_image_1)
        self.canvas.create_image(79.0, 49.0, image=image_image_1)

        # Navigation bar
        self.canvas.create_rectangle(
            0.0, 98.0, 1270.0, 140.0, fill="#FFDA0C", outline=""
        )

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
        image_image_5 = PhotoImage(file=relative_to_assets("image_content.png"))
        self.images.append(image_image_5)
        self.image_content = self.canvas.create_image(773.0, 466.0, image=image_image_5)

        # Admin info
        admin_name = f"{self.user_data.get('first_name', 'Admin')} {self.user_data.get('last_name', 'User')}"
        self.canvas.create_text(
            128.0,
            193.0,
            anchor="nw",
            text=admin_name,
            fill="#F2F2F2",
            font=("Inter", 20 * -1),
        )
        self.canvas.create_text(
            128.0,
            220.0,
            anchor="nw",
            text="Admin",
            fill="#F2F2F2",
            font=("Inter", 16 * -1),
        )

        # Dashboard title
        self.title_text = self.canvas.create_text(
            351.0,
            202.0,
            anchor="nw",
            text="Dashboard",
            fill="#303030",
            font=("Inter SemiBold", 24 * -1),
        )

        # Create navigation buttons
        self.create_navigation_buttons()

        # Create dashboard panels
        self.create_dashboard_panels()

        # Add text-based logout button in header
        self.create_header_logout_button()

        # Create content frame
        self.create_content_frame()

    def create_content_frame(self):
        """Create the main content frame where all content will be displayed"""
        self.content_frame = Frame(
            self.parent, bg="#FFFFFF", bd=0, highlightthickness=0
        )
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)
        # Initially hide the content frame so dashboard panels are visible
        self.content_frame.place_forget()

    def create_header_logout_button(self):
        """Create text-based logout button in header"""
        self.button_logout = Button(
            self.parent,
            text="Logout",
            font=("Inter", 12),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            cursor="hand2",
            command=self.logout,
        )
        self.button_logout.place(relx=0.95, rely=0.03, anchor="ne")

    def create_navigation_buttons(self):
        """Create navigation buttons"""
        # Dashboard button
        button_dashboard_img = PhotoImage(
            file=relative_to_assets("button_dashboard.png")
        )
        self.images.append(button_dashboard_img)
        self.button_dashboard = Button(
            self.parent,
            image=button_dashboard_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_dashboard,
            relief="flat",
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
            relief="flat",
        )
        self.button_students.place(x=49.0, y=346.0, width=239.0, height=47.0)

        # Documents button
        button_documents_img = PhotoImage(
            file=relative_to_assets("button_documents.png")
        )
        self.images.append(button_documents_img)
        self.button_documents = Button(
            self.parent,
            image=button_documents_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.show_documents,
            relief="flat",
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
            relief="flat",
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
            relief="flat",
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
            relief="flat",
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
            relief="flat",
        )
        self.button_users.place(x=49.0, y=646.0, width=239.0, height=47.0)

    def create_dashboard_panels(self):
        """Create dashboard statistic panels matching the Figma layout"""
        # Card backgrounds (top row and middle row)
        # Students
        self.canvas.create_rectangle(
            351.0, 252.0, 610.0, 369.0, fill="#F5F5F5", outline=""
        )
        # Total Request
        self.canvas.create_rectangle(
            652.0, 252.0, 912.0, 369.0, fill="#F5F5F5", outline=""
        )
        # Total Feedback
        self.canvas.create_rectangle(
            938.0, 252.0, 1197.0, 369.0, fill="#F5F5F5", outline=""
        )
        # Pending Request
        self.canvas.create_rectangle(
            351.0, 394.0, 610.0, 511.0, fill="#F5F5F5", outline=""
        )
        # Total Processing
        self.canvas.create_rectangle(
            653.0, 394.0, 912.0, 511.0, fill="#F5F5F5", outline=""
        )
        # Completed Request
        self.canvas.create_rectangle(
            938.0, 396.0, 1197.0, 513.0, fill="#F5F5F5", outline=""
        )

        # Bottom large panels
        # Top Request Document
        self.canvas.create_rectangle(
            351.0, 539.0, 754.0, 731.0, fill="#F5F5F5", outline=""
        )
        # Monthly Document Request
        self.canvas.create_rectangle(
            803.0, 540.0, 1197.0, 732.0, fill="#F5F5F5", outline=""
        )

        # Labels
        self.canvas.create_text(
            376.0,
            269.0,
            anchor="nw",
            text="Students",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            672.0,
            269.0,
            anchor="nw",
            text="Total Request",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            954.0,
            271.0,
            anchor="nw",
            text="Total Feedback",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            376.0,
            414.0,
            anchor="nw",
            text="Pending Request",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            678.0,
            414.0,
            anchor="nw",
            text="Total Processing",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            963.0,
            416.0,
            anchor="nw",
            text="Completed Request",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            382.0,
            564.0,
            anchor="nw",
            text="Top Request Document",
            fill="#000000",
            font=("Inter", 16 * -1),
        )
        self.canvas.create_text(
            838.0,
            564.0,
            anchor="nw",
            text="Montly Document Request",
            fill="#000000",
            font=("Inter", 16 * -1),
        )

        # Numeric values (wired to existing stats where available)
        self.students_text = self.canvas.create_text(
            387.0, 310.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.requests_text = self.canvas.create_text(
            683.0, 310.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.feedback_text = self.canvas.create_text(
            965.0, 312.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.pending_text = self.canvas.create_text(
            387.0, 455.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        # Processing is not yet computed separately; initialize to 0 for now
        self.processing_text = self.canvas.create_text(
            689.0, 455.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )
        self.completed_text = self.canvas.create_text(
            974.0, 457.0, anchor="nw", text="0", fill="#000000", font=("Inter", 32 * -1)
        )

    def add_card_labels(self):
        """Add proper labels and descriptions for all cards"""
        # Card labels with better styling and positioning
        self.canvas.create_text(
            450.0,
            340.0,
            text="Total Students",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            750.0,
            340.0,
            text="Total Requests",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            1050.0,
            340.0,
            text="Total Feedback",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            600.0,
            540.0,
            text="Pending Requests",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )
        self.canvas.create_text(
            900.0,
            540.0,
            text="Completed Requests",
            fill="#34495E",
            font=("Inter", 12 * -1, "bold"),
        )

        # Add section header - Changed to "Dashboard"
        self.canvas.create_text(
            400.0,
            200.0,
            text="Dashboard",
            fill="#2C3E50",
            font=("Inter", 18 * -1, "bold"),
        )

        # Add decorative elements
        self.add_decorative_elements()

    def add_decorative_elements(self):
        """Add decorative elements and visual enhancements"""
        # Add subtle borders around cards for better definition
        card_positions = [
            (450, 300),  # Students
            (750, 300),  # Requests
            (1050, 300),  # Feedback
            (600, 500),  # Pending
            (900, 500),  # Completed
        ]

        for x, y in card_positions:
            # Add subtle shadow effect
            self.canvas.create_rectangle(
                x - 100, y - 30, x + 100, y + 30, fill="", outline="#E8F4FD", width=2
            )

        # Add status indicators
        status_colors = ["#27AE60", "#3498DB", "#9C27B0", "#F39C12", "#4CAF50"]
        for i, (x, y) in enumerate(card_positions):
            self.canvas.create_oval(
                x + 60, y - 20, x + 70, y - 10, fill=status_colors[i], outline=""
            )

    def load_statistics(self):
        """Load statistics from database - FIXED VERSION"""
        try:
            connection = self.get_db_connection()
            if not connection:
                print("❌ No database connection available")
                return

            cursor = connection.cursor(dictionary=True)

            # Total students - FIXED: Use enrollment_status instead of is_active
            cursor.execute(
                "SELECT COUNT(*) as total FROM students WHERE enrollment_status = 'Enrolled'"
            )
            result = cursor.fetchone()
            self.stats_data["total_students"] = result["total"] if result else 0
            print(f"✅ Total students: {self.stats_data['total_students']}")

            # Total requests
            cursor.execute("SELECT COUNT(*) as total FROM document_requests")
            result = cursor.fetchone()
            self.stats_data["total_requests"] = result["total"] if result else 0
            print(f"✅ Total requests: {self.stats_data['total_requests']}")

            # Pending requests - FIXED: Use correct status values from your schema
            cursor.execute(
                """
                SELECT COUNT(*) as total FROM document_requests
                WHERE status IN ('under_review', 'payment_pending', 'processing')
            """
            )
            result = cursor.fetchone()
            self.stats_data["pending_requests"] = result["total"] if result else 0
            print(f"✅ Pending requests: {self.stats_data['pending_requests']}")

            # Completed requests - NEW CARD
            cursor.execute(
                """
                SELECT COUNT(*) as total FROM document_requests
                WHERE status = 'completed'
            """
            )
            result = cursor.fetchone()
            self.stats_data["completed_requests"] = result["total"] if result else 0
            print(f"✅ Completed requests: {self.stats_data['completed_requests']}")

            # Total feedback
            cursor.execute("SELECT COUNT(*) as total FROM feedback")
            result = cursor.fetchone()
            self.stats_data["total_feedback"] = result["total"] if result else 0
            print(f"✅ Total feedback: {self.stats_data['total_feedback']}")

            cursor.close()
            connection.close()

            print("✅ Statistics loaded successfully")

        except Error as e:
            print(f"❌ Error loading statistics: {e}")
            # Use default values if database error occurs
            self.stats_data = {
                "total_students": 0,
                "total_requests": 0,
                "pending_requests": 0,
                "completed_requests": 0,
                "total_feedback": 0,
            }

    def update_display(self):
        """Update the display with current statistics"""
        try:
            self.canvas.itemconfig(
                self.students_text, text=str(self.stats_data["total_students"])
            )
            self.canvas.itemconfig(
                self.requests_text, text=str(self.stats_data["total_requests"])
            )
            self.canvas.itemconfig(
                self.feedback_text, text=str(self.stats_data["total_feedback"])
            )
            self.canvas.itemconfig(
                self.pending_text, text=str(self.stats_data["pending_requests"])
            )
            self.canvas.itemconfig(
                self.completed_text, text=str(self.stats_data["completed_requests"])
            )
            print("✅ Display updated with statistics")
        except Exception as e:
            print(f"❌ Error updating display: {e}")

    def clear_content(self):
        """Clear the content frame"""
        if self.content_frame:
            for widget in self.content_frame.winfo_children():
                try:
                    widget.destroy()
                except:
                    pass

    def show_dashboard_content(self):
        """Show dashboard content in the content frame"""
        self.clear_content()

        # Hide content frame to show dashboard panels
        self.content_frame.place_forget()

        # Update title
        self.canvas.itemconfig(self.title_text, text="Dashboard")

        # Show statistics panels
        self.canvas.itemconfig(self.students_text, state="normal")
        self.canvas.itemconfig(self.requests_text, state="normal")
        self.canvas.itemconfig(self.feedback_text, state="normal")
        self.canvas.itemconfig(self.pending_text, state="normal")
        self.canvas.itemconfig(self.completed_text, state="normal")
        # Ensure processing count is also visible if present
        try:
            self.canvas.itemconfig(self.processing_text, state="normal")
        except Exception:
            pass

        # Load fresh statistics
        self.load_statistics()
        self.update_display()
        # Draw charts for requests by type (bar) and monthly requests (line)
        self.update_charts()

    def clear_charts(self):
        """Remove previously drawn chart items from the canvas"""
        try:
            # Delete by tag first to ensure all chart elements are removed
            try:
                self.canvas.delete("chart")
            except Exception:
                pass
            for item_id in getattr(self, "chart_items", []):
                try:
                    self.canvas.delete(item_id)
                except Exception:
                    pass
            self.chart_items = []
        except Exception:
            self.chart_items = []

    def update_charts(self):
        """Fetch data and render dashboard charts"""
        # Always clear previous charts before drawing new ones
        self.clear_charts()
        try:
            by_type = self.fetch_request_counts_by_type(limit=6)
            self.draw_bar_chart_requests_by_type(by_type)
        except Exception as e:
            print(f"❌ Error drawing requests-by-type bar chart: {e}")
        try:
            monthly = self.fetch_monthly_request_counts(months=6)
            self.draw_line_chart_monthly_requests(monthly)
        except Exception as e:
            print(f"❌ Error drawing monthly requests line chart: {e}")
        # Bring charts to the very front
        try:
            self.canvas.tag_raise("chart")
        except Exception:
            pass

    def fetch_request_counts_by_type(self, limit=6):
        """Return list of tuples [(type_name, count), ...] limited to top N by count"""
        data = []
        try:
            connection = self.get_db_connection()
            if not connection:
                return data
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT COALESCE(dt.code, dt.name) AS label, COUNT(dr.request_id) AS total
                FROM document_requests dr
                JOIN document_types dt ON dt.document_type_id = dr.document_type_id
                GROUP BY dt.document_type_id, label
                ORDER BY total DESC
                LIMIT %s
                """,
                (limit,),
            )
            for row in cursor.fetchall():
                # row: (type_name, total)
                data.append((row[0], int(row[1] or 0)))
            cursor.close()
            connection.close()
        except Error as e:
            print(f"❌ Error fetching request counts by type: {e}")
        return data

    def fetch_monthly_request_counts(self, months=6):
        """Return list of tuples [(label, count)] for last N months including current.
        Label format: MMM (e.g., Jan)
        """
        # Build default zeroed series in case DB returns sparse data
        import datetime

        today = datetime.date.today().replace(day=1)
        month_keys = []
        for i in range(months - 1, -1, -1):
            m = (today - datetime.timedelta(days=31 * i)).replace(day=1)
            key = m.strftime("%Y-%m")
            label = m.strftime("%b")
            month_keys.append((key, label))

        counts = {key: 0 for key, _ in month_keys}

        try:
            connection = self.get_db_connection()
            if not connection:
                return [(label, counts[key]) for key, label in month_keys]
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT DATE_FORMAT(request_date, '%Y-%m') AS ym, COUNT(*) AS total
                FROM document_requests
                WHERE request_date >= DATE_SUB(DATE_FORMAT(NOW(), '%Y-%m-01'), INTERVAL %s MONTH)
                GROUP BY ym
                ORDER BY ym
                """,
                (months - 1,),
            )
            for ym, total in cursor.fetchall():
                counts[str(ym)] = int(total or 0)
            cursor.close()
            connection.close()
        except Error as e:
            print(f"❌ Error fetching monthly request counts: {e}")

        return [(label, counts[key]) for key, label in month_keys]

    def draw_bar_chart_requests_by_type(self, data):
        """Draw a simple bar chart in the left bottom panel (Top Request Document)."""
        # Panel bounds from create_dashboard_panels: (351,539) to (754,731)
        x0, y0, x1, y1 = 351.0, 539.0, 754.0, 731.0
        padding_left, padding_right = 20, 16
        padding_top, padding_bottom = 56, 28

        plot_x0 = x0 + padding_left
        plot_x1 = x1 - padding_right
        plot_y0 = y0 + padding_top
        plot_y1 = y1 - padding_bottom

        # Axes
        axis_color = "#A0A0A0"
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y1, plot_x1, plot_y1, fill=axis_color, tags=("chart",)
            )
        )
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y0, plot_x0, plot_y1, fill=axis_color, tags=("chart",)
            )
        )

        if not data:
            self.chart_items.append(
                self.canvas.create_text(
                    (plot_x0 + plot_x1) / 2,
                    (plot_y0 + plot_y1) / 2,
                    text="No data",
                    fill="#808080",
                    font=("Inter", 12),
                    tags=("chart",),
                )
            )
            return

        max_val = max((c for _, c in data), default=0) or 1
        n = len(data)
        bar_gap = 8
        total_width = plot_x1 - plot_x0
        bar_width = max(12, (total_width - (n + 1) * bar_gap) / max(n, 1))

        # Draw bars and labels
        fill_color = "#3498DB"
        label_color = "#303030"
        value_color = "#505050"

        for i, (name, count) in enumerate(data):
            bx0 = plot_x0 + bar_gap + i * (bar_width + bar_gap)
            bx1 = bx0 + bar_width
            height_ratio = float(count) / float(max_val)
            by1 = plot_y1
            by0 = plot_y1 - height_ratio * (plot_y1 - plot_y0)
            rect = self.canvas.create_rectangle(
                bx0, by0, bx1, by1, fill=fill_color, outline="", tags=("chart",)
            )
            self.chart_items.append(rect)
            # Value label above bar
            val = self.canvas.create_text(
                (bx0 + bx1) / 2,
                by0 - 8,
                text=str(count),
                fill=value_color,
                font=("Inter", 10),
                tags=("chart",),
            )
            self.chart_items.append(val)
            # X label (truncate)
            short = name if len(name) <= 10 else name[:9] + "…"
            lbl = self.canvas.create_text(
                (bx0 + bx1) / 2,
                by1 + 10,
                text=short,
                fill=label_color,
                font=("Inter", 9),
                tags=("chart",),
            )
            self.chart_items.append(lbl)

    def draw_line_chart_monthly_requests(self, data):
        """Draw a simple line chart in the right bottom panel (Monthly Document Request)."""
        # Panel bounds from create_dashboard_panels: (803,540) to (1197,732)
        x0, y0, x1, y1 = 803.0, 540.0, 1197.0, 732.0
        padding_left, padding_right = 36, 16
        padding_top, padding_bottom = 56, 28

        plot_x0 = x0 + padding_left
        plot_x1 = x1 - padding_right
        plot_y0 = y0 + padding_top
        plot_y1 = y1 - padding_bottom

        # Axes
        axis_color = "#A0A0A0"
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y1, plot_x1, plot_y1, fill=axis_color, tags=("chart",)
            )
        )
        self.chart_items.append(
            self.canvas.create_line(
                plot_x0, plot_y0, plot_x0, plot_y1, fill=axis_color, tags=("chart",)
            )
        )

        if not data:
            self.chart_items.append(
                self.canvas.create_text(
                    (plot_x0 + plot_x1) / 2,
                    (plot_y0 + plot_y1) / 2,
                    text="No data",
                    fill="#808080",
                    font=("Inter", 12),
                    tags=("chart",),
                )
            )
            return

        labels = [label for (label, _) in data]
        values = [val for (_, val) in data]
        max_val = max(values or [0]) or 1

        n = len(values)
        if n == 1:
            xs = [plot_x0 + (plot_x1 - plot_x0) / 2]
        else:
            step = (plot_x1 - plot_x0) / float(max(n - 1, 1))
            xs = [plot_x0 + i * step for i in range(n)]
        ys = [plot_y1 - (v / float(max_val)) * (plot_y1 - plot_y0) for v in values]

        # Grid lines (optional)
        grid_color = "#E0E0E0"
        for g in range(1, 4):
            gy = plot_y0 + g * (plot_y1 - plot_y0) / 4.0
            self.chart_items.append(
                self.canvas.create_line(
                    plot_x0, gy, plot_x1, gy, fill=grid_color, tags=("chart",)
                )
            )

        # Polyline
        line_color = "#E67E22"
        dot_color = "#D35400"
        for i in range(n - 1):
            seg = self.canvas.create_line(
                xs[i],
                ys[i],
                xs[i + 1],
                ys[i + 1],
                fill=line_color,
                width=2,
                tags=("chart",),
            )
            self.chart_items.append(seg)
        for i in range(n):
            dot = self.canvas.create_oval(
                xs[i] - 3,
                ys[i] - 3,
                xs[i] + 3,
                ys[i] + 3,
                fill=dot_color,
                outline="",
                tags=("chart",),
            )
            self.chart_items.append(dot)
            # Value labels
            val = self.canvas.create_text(
                xs[i],
                ys[i] - 10,
                text=str(values[i]),
                fill="#505050",
                font=("Inter", 10),
                tags=("chart",),
            )
            self.chart_items.append(val)
            # X labels
            lbl = self.canvas.create_text(
                xs[i],
                plot_y1 + 12,
                text=labels[i],
                fill="#303030",
                font=("Inter", 9),
                tags=("chart",),
            )
            self.chart_items.append(lbl)

    def show_requests_content(self):
        """Show requests management content in the content frame"""
        self.clear_content()
        # Hide charts when leaving dashboard panels
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Requests")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create requests management interface
        self.create_requests_interface()

    def create_requests_interface(self):
        """Create the requests management interface inside content frame"""
        try:
            # Create requests manager inside the content frame
            self.requests_manager = AdminRequestManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Requests interface loaded successfully")
        except Exception as e:
            print(f"❌ Error creating requests interface: {e}")
            messagebox.showerror(
                "Error", f"Failed to load requests interface: {str(e)}"
            )

    # Navigation methods
    def show_dashboard(self):
        """Show dashboard"""
        print("🔄 Showing dashboard...")
        self.current_content = "dashboard"
        self.show_dashboard_content()

    def show_students(self):
        """Show students management"""
        self.current_content = "students"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Students Management")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create and show student manager
        try:
            self.student_manager = AdminStudentManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Student manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading student manager: {e}")
            messagebox.showerror("Error", f"Failed to load student manager: {str(e)}")

    def show_documents(self):
        """Show document types management"""
        self.current_content = "documents"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Document Types")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create and show document types manager
        try:
            self.document_manager = AdminDocumentManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Document types manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading document types manager: {e}")
            messagebox.showerror(
                "Error", f"Failed to load document types manager: {str(e)}"
            )

    def show_requests(self):
        """Show document requests management"""
        print("🔄 Showing requests management...")
        self.current_content = "requests"
        self.show_requests_content()

    def show_billing(self):
        """Show billing and payments"""
        self.current_content = "billing"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Billing & Payments")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")
        try:
            self.canvas.itemconfig(self.processing_text, state="hidden")
        except Exception:
            pass

        # Create and show billing manager
        try:
            self.billing_manager = AdminBillingManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Billing manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading billing manager: {e}")
            messagebox.showerror("Error", f"Failed to load billing manager: {str(e)}")

    def show_feedback(self):
        """Show feedback management"""
        self.current_content = "feedback"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="Feedback Management")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")

        try:
            self.feedback_manager = AdminFeedbackManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ Feedback manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading feedback manager: {e}")
            messagebox.showerror("Error", f"Failed to load feedback manager: {str(e)}")

    def show_users(self):
        """Show user management"""
        self.current_content = "users"
        self.clear_content()
        self.clear_charts()

        # Show content frame for other content
        self.content_frame.place(x=326.0, y=179.0, width=895.0, height=574.0)

        # Update title
        self.canvas.itemconfig(self.title_text, text="User Management")

        # Hide dashboard statistics
        self.canvas.itemconfig(self.students_text, state="hidden")
        self.canvas.itemconfig(self.requests_text, state="hidden")
        self.canvas.itemconfig(self.feedback_text, state="hidden")
        self.canvas.itemconfig(self.pending_text, state="hidden")
        self.canvas.itemconfig(self.completed_text, state="hidden")

        # Create and show user manager
        try:
            self.user_manager = AdminUserManager(
                parent=self.content_frame,
                get_db_connection=self.get_db_connection,
                user_data=self.user_data,
            )
            print("✅ User manager loaded successfully")
        except Exception as e:
            print(f"❌ Error loading user manager: {e}")
            messagebox.showerror("Error", f"Failed to load user manager: {str(e)}")

    def logout(self):
        """Logout admin"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            print("🚪 Logging out admin...")
            if self.logout_callback:
                self.logout_callback()

    def destroy(self):
        """Clean up when window is closed"""
        try:
            self.canvas.destroy()
        except:
            pass

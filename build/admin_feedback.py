# adminfeedback.py - Admin Feedback Manager for Feedback Management
from pathlib import Path
from tkinter import (
    Canvas,
    Frame,
    Label,
    Button,
    Entry,
    StringVar,
    messagebox,
    Scrollbar,
    Toplevel,
    Text,
    PhotoImage,
)
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG
from utils import EmailService

OUTPUT_PATH = Path(__file__).parent


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/adminrequest/{path}"))


class AdminFeedbackManager:
    def __init__(self, parent, get_db_connection=None, user_data=None):
        self.parent = parent
        self.get_db_connection = get_db_connection
        self.user_data = user_data or {}

        # Feedback data
        self.feedbacks = []
        self.filtered_feedbacks = []
        self.search_query = ""
        self.current_page = 1
        self.feedbacks_per_page = 10

        # UI element storage
        self.images = []
        self.row_widgets = []

        # Email service
        self.email_service = EmailService()

        self.setup_ui()
        self.load_feedbacks()
        self.update_display()

    def setup_ui(self):
        """Setup the feedback management UI inside the parent frame"""
        # Create a canvas that fits the content frame
        self.canvas = Canvas(
            self.parent,
            bg="#FFFFFF",
            width=895,
            height=574,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        self.canvas.pack(fill="both", expand=True)

        # Create scrollbar
        self.scrollbar = Scrollbar(
            self.parent, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create search bar (top)
        self.create_searchbar()

        # Create table header
        self.create_table_headers()

        # Create navigation controls
        self.create_navigation_controls()

    def create_searchbar(self):
        """Create a search entry at the top right"""
        # Search entry positioned at the top right
        self.search_entry = Entry(
            self.parent,
            bd=1,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=1,
            font=("Inter", 12),
        )
        # Place at the top right
        self.search_entry.place(x=475, y=15, width=400, height=30)
        self.search_entry.insert(0, "Search feedback...")

        # Simple placeholder behavior
        def _on_focus_in(event):
            if self.search_entry.get() == "Search feedback...":
                self.search_entry.delete(0, "end")

        def _on_focus_out(event):
            if not self.search_entry.get().strip():
                self.search_entry.delete(0, "end")
                self.search_entry.insert(0, "Search feedback...")

        self.search_entry.bind("<FocusIn>", _on_focus_in)
        self.search_entry.bind("<FocusOut>", _on_focus_out)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def create_table_headers(self):
        """Create table header labels for feedback"""
        # Add title label on the top left
        title_label = Label(
            self.parent,
            text="Feedback Management",
            font=("Inter", 16, "bold"),
            bg="#FFFFFF",
            fg="#792D1B",
        )
        title_label.place(x=20, y=15)

        headers = [
            (40.0, "No.", "center"),
            (120.0, "Request No.", "center"),
            (240.0, "Student", "center"),
            (360.0, "Document", "center"),
            (440.0, "Rating", "center"),
            (520.0, "Date", "center"),
            (600.0, "Status", "center"),
            (770.0, "Actions", "center"),
        ]

        # Header background - dark brown like in the image
        self.canvas.create_rectangle(20, 60, 875, 100, fill="#792D1B", outline="")

        for x, text, anchor in headers:
            self.canvas.create_text(
                x,
                80,
                anchor=anchor,
                text=text,
                fill="#FFFFFF",
                font=("Inter", 12, "bold"),
            )

    def create_navigation_controls(self):
        """Create page navigation controls"""
        # Previous button
        self.button_prev = Button(
            self.parent,
            text="Previous",
            font=("Inter", 10),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            command=self.previous_page,
        )
        self.button_prev.place(x=250, y=530, width=80, height=30)

        # Page number display
        self.entry_page_no = Entry(
            self.parent,
            bd=1,
            bg="#FFFFFF",
            fg="#000716",
            highlightthickness=1,
            justify="center",
            state="readonly",
            font=("Inter", 10),
        )
        self.entry_page_no.place(x=350, y=530, width=100, height=30)

        # Next button
        self.button_next = Button(
            self.parent,
            text="Next",
            font=("Inter", 10),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            command=self.next_page,
        )
        self.button_next.place(x=470, y=530, width=80, height=30)

    def load_feedbacks(self):
        """Load feedbacks from database with joins"""
        try:
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Database Error", "Could not connect to database")
                return

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    f.feedback_id, f.request_id, f.rating, f.comments,
                    f.is_anonymous, f.responded_to, f.response, f.created_at,
                    dr.request_number,
                    CONCAT(s.first_name, ' ', s.last_name) as student_name,
                    s.student_number, u.email as student_email,
                    dt.code as document_code, dt.name as document_name,
                    st.first_name as responded_by_first, st.last_name as responded_by_last,
                    f.responded_at
                FROM feedback f
                JOIN document_requests dr ON f.request_id = dr.request_id
                JOIN students s ON dr.student_id = s.student_id
                JOIN users u ON s.user_id = u.user_id
                JOIN document_types dt ON dr.document_type_id = dt.document_type_id
                LEFT JOIN staff st ON f.responded_by = st.staff_id
                ORDER BY f.created_at DESC
            """
            )

            self.feedbacks = cursor.fetchall()
            # Default filtered list is full list
            self.filtered_feedbacks = list(self.feedbacks)

            cursor.close()
            connection.close()

            print(f"✅ Loaded {len(self.feedbacks)} feedbacks from database")

        except Error as e:
            print(f"❌ Error loading feedbacks: {e}")
            messagebox.showerror(
                "Database Error", f"Failed to load feedbacks: {str(e)}"
            )
            self.feedbacks = []

    def update_display(self):
        """Update the display with current page data"""
        self.clear_table_rows()

        if not self.filtered_feedbacks:
            self.show_no_feedbacks_message()
            return

        self.display_current_feedbacks()
        self.update_navigation()

    def clear_table_rows(self):
        """Clear all table rows"""
        # Remove existing row widgets
        for widget_list in self.row_widgets:
            for widget in widget_list:
                try:
                    widget.destroy()
                except:
                    pass
        self.row_widgets = []

        # Clear canvas items except headers
        self.canvas.delete("row")

    def display_current_feedbacks(self):
        """Display feedbacks for current page"""
        start_idx = (self.current_page - 1) * self.feedbacks_per_page
        end_idx = start_idx + self.feedbacks_per_page
        current_feedbacks = self.filtered_feedbacks[start_idx:end_idx]

        for i, feedback in enumerate(current_feedbacks):
            self.create_table_row(i, feedback)

    def on_search_change(self, event=None):
        """Handle search text changes and filter the list"""
        query = self.search_entry.get().strip()
        # Ignore placeholder
        if query == "Search feedback...":
            query = ""
        self.search_query = query.lower()
        self.apply_search_filter()

    def apply_search_filter(self):
        """Filter feedbacks into filtered_feedbacks based on search_query"""
        if not self.search_query:
            self.filtered_feedbacks = list(self.feedbacks)
        else:
            q = self.search_query

            def matches(feedback):
                values = [
                    str(feedback.get("request_number", "")),
                    str(feedback.get("student_name", "")),
                    str(feedback.get("student_number", "")),
                    str(feedback.get("document_code", "")),
                    str(feedback.get("document_name", "")),
                    str(feedback.get("rating", "")),
                    "responded" if feedback.get("responded_to") else "pending",
                    str(feedback.get("comments", "")),
                ]
                text = " ".join(values).lower()
                return q in text

            self.filtered_feedbacks = [f for f in self.feedbacks if matches(f)]
        # Reset to first page after filtering
        self.current_page = 1
        self.update_display()

    def create_table_row(self, row_index, feedback):
        """Create a table row with data and action buttons"""
        y_position = 110 + (row_index * 45)

        # Row background (alternating colors)
        fill_color = "#FFFFFF" if row_index % 2 == 0 else "#F8F8F8"
        self.canvas.create_rectangle(
            20,
            y_position,
            875,
            y_position + 40,
            fill=fill_color,
            outline="#E0E0E0",
            tags="row",
        )

        # Calculate row number (global index)
        row_number = ((self.current_page - 1) * self.feedbacks_per_page) + row_index + 1

        # Format feedback date
        feedback_date = feedback["created_at"]
        if isinstance(feedback_date, datetime):
            formatted_date = feedback_date.strftime("%m/%d/%Y")
        else:
            formatted_date = str(feedback_date)

        # Format student name (show Anonymous if is_anonymous)
        student_display = (
            "Anonymous" if feedback["is_anonymous"] else feedback["student_name"]
        )

        # Format rating as stars
        rating_stars = self.format_rating_stars(feedback["rating"])

        # Format status
        status_text = "Responded" if feedback["responded_to"] else "Pending"

        # Create text elements for the row with proper alignment
        text_configs = [
            (40.0, str(row_number), "center"),
            (120.0, feedback["request_number"], "center"),
            (
                240.0,
                (
                    student_display[:15] + "..."
                    if len(student_display) > 15
                    else student_display
                ),
                "center",
            ),
            (360.0, feedback["document_code"], "center"),
            (440.0, rating_stars, "center"),
            (520.0, formatted_date, "center"),
            (600.0, status_text, "center"),
        ]

        for x, text, anchor in text_configs:
            self.canvas.create_text(
                x,
                y_position + 20,
                anchor=anchor,
                text=text,
                fill="#1E1E1E",
                font=("Inter", 10),
                tags="row",
            )

        # Create action buttons
        self.create_row_buttons(row_index, feedback, y_position)

    def format_rating_stars(self, rating):
        """Format rating as stars (1-5)"""
        if not rating:
            return "☆☆☆☆☆"

        filled_stars = "★" * rating
        empty_stars = "☆" * (5 - rating)
        return filled_stars + empty_stars

    def create_row_buttons(self, row_index, feedback, y_position):
        """Create action buttons for each row"""
        button_widgets = []

        # View Details button - always available
        view_button = Button(
            self.parent,
            text="View Feedback",
            font=("Inter", 9),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=lambda f=feedback: self.view_feedback_details(f),
        )
        view_button.place(x=660, y=y_position + 8, width=100, height=25)
        button_widgets.append(view_button)

        # Respond/View Response button
        responded_to = feedback["responded_to"]

        if responded_to:
            # View Response button (gray)
            view_response_button = Button(
                self.parent,
                text="View Response",
                font=("Inter", 9),
                bg="#6c757d",
                fg="#FFFFFF",
                relief="flat",
                command=lambda f=feedback: self.view_response(f),
            )
            view_response_button.place(x=770, y=y_position + 8, width=100, height=25)
            button_widgets.append(view_response_button)

        else:
            # Respond button (green)
            respond_button = Button(
                self.parent,
                text="Respond",
                font=("Inter", 9),
                bg="#28a745",
                fg="#FFFFFF",
                relief="flat",
                command=lambda f=feedback: self.respond_to_feedback(f),
            )
            respond_button.place(x=770, y=y_position + 8, width=100, height=25)
            button_widgets.append(respond_button)

        self.row_widgets.append(button_widgets)

    def view_feedback_details(self, feedback):
        """Open feedback details dialog with payment_window.py layout style"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Feedback Details - {feedback['request_number']}")
        dialog.geometry("600x720")
        dialog.configure(bg="#FCECB7")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        self._center_feedback_dialog(dialog)

        # Create main canvas
        canvas = Canvas(
            dialog,
            bg="#FCECB7",
            height=720,
            width=600,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        canvas.place(x=0, y=0)

        # Create header section
        self._create_feedback_header(canvas, dialog)

        # Create content section
        self._create_feedback_content(canvas, feedback)

    def _center_feedback_dialog(self, dialog):
        """Center the feedback dialog on screen"""
        dialog.update_idletasks()
        width, height = 600, 720
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _create_feedback_header(self, canvas, dialog):
        """Create header section matching payment_window.py style"""
        # Header rectangle
        canvas.create_rectangle(0.0, 0.0, 600.0, 98.0, fill="#792D1B", outline="")

        # Yellow header strip
        canvas.create_rectangle(0.0, 57.0, 600.0, 99.0, fill="#FFDA0C", outline="")

        # Header text
        canvas.create_text(
            300.0,
            78.0,
            text="Feedback Details",
            fill="#000000",
            font=("Arial", 16, "bold"),
            anchor="center",
        )

    def _create_feedback_content(self, canvas, feedback):
        """Create feedback content section"""
        # White background panel
        canvas.create_rectangle(
            25.0, 120.0, 575.0, 650.0, fill="#FFFFFF", outline="#DDDDDD", width=2
        )

        # Student name (or Anonymous)
        student_display = (
            "Anonymous" if feedback["is_anonymous"] else feedback["student_name"]
        )

        # Rating display
        rating_stars = self.format_rating_stars(feedback["rating"])

        # Feedback information - centered layout
        info_y_start = 150
        line_height = 30
        center_x = 300.0  # Center of the dialog (600/2)

        details = [
            ("Request Number:", feedback["request_number"]),
            ("Student:", student_display),
            ("Document:", f"{feedback['document_code']} - {feedback['document_name']}"),
            ("Rating:", rating_stars),
            (
                "Date:",
                (
                    feedback["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                    if feedback["created_at"]
                    else "N/A"
                ),
            ),
        ]

        for i, (label, value) in enumerate(details):
            detail_text = f"{label} {value}"
            canvas.create_text(
                center_x,
                info_y_start + (i * line_height),
                text=detail_text,
                fill="#000000",
                font=("Arial", 12, "bold"),
                anchor="center",
            )

        # Comments section
        comments_y = info_y_start + (len(details) * line_height) + 20
        canvas.create_text(
            center_x,
            comments_y,
            text="Comments:",
            fill="#792D1B",
            font=("Arial", 14, "bold"),
            anchor="center",
        )

        # Comments text area
        comments_frame = Frame(canvas, bg="#FFFFFF")
        comments_frame.place(x=50, y=comments_y + 20, width=500, height=120)

        comments_text = Text(
            comments_frame,
            font=("Arial", 10),
            wrap="word",
            state="disabled",
            bg="#F8F8F8",
            relief="solid",
            bd=1,
        )
        comments_text.pack(fill="both", expand=True, padx=10, pady=10)
        comments_text.config(state="normal")
        comments_text.insert("1.0", feedback["comments"] or "No comments provided.")
        comments_text.config(state="disabled")

        # Response section (if exists)
        response_y = comments_y + 160
        if feedback["responded_to"] and feedback["response"]:
            canvas.create_text(
                center_x,
                response_y,
                text="Admin Response:",
                fill="#792D1B",
                font=("Arial", 14, "bold"),
                anchor="center",
            )

            # Response text area
            response_frame = Frame(canvas, bg="#FFFFFF")
            response_frame.place(x=50, y=response_y + 20, width=500, height=100)

            response_text = Text(
                response_frame,
                font=("Arial", 10),
                wrap="word",
                state="disabled",
                bg="#E8F5E8",
                relief="solid",
                bd=1,
            )
            response_text.pack(fill="both", expand=True, padx=10, pady=10)
            response_text.config(state="normal")
            response_text.insert("1.0", feedback["response"])
            response_text.config(state="disabled")

            # Response info
            responder_name = (
                f"{feedback['responded_by_first']} {feedback['responded_by_last']}"
                if feedback["responded_by_first"]
                else "Admin"
            )
            response_date = (
                feedback["responded_at"].strftime("%Y-%m-%d %H:%M:%S")
                if feedback["responded_at"]
                else "N/A"
            )

            canvas.create_text(
                center_x,
                response_y + 140,
                text=f"Responded by: {responder_name} on {response_date}",
                fill="#666666",
                font=("Arial", 10, "italic"),
                anchor="center",
            )

            # Close button position
            button_y = response_y + 180
        else:
            # Close button position when no response
            button_y = comments_y + 180

        # Close button
        close_button = Button(
            canvas,
            text="Close",
            font=("Arial", 12, "bold"),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            command=canvas.master.destroy,
            width=15,
            height=2,
        )
        close_button.place(x=center_x - 75, y=button_y)

    def _relative_to_assets(self, path: str):
        """Get path to assets"""
        import os
        import sys

        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "resources", "assets", path)

    def respond_to_feedback(self, feedback):
        """Open respond to feedback dialog with payment_window.py layout style"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Respond to Feedback - {feedback['request_number']}")
        dialog.geometry("600x720")
        dialog.configure(bg="#FCECB7")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        self._center_respond_dialog(dialog)

        # Create main canvas
        canvas = Canvas(
            dialog,
            bg="#FCECB7",
            height=720,
            width=600,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        canvas.place(x=0, y=0)

        # Create header section
        self._create_respond_header(canvas, dialog)

        # Create content section
        self._create_respond_content(canvas, feedback)

    def _center_respond_dialog(self, dialog):
        """Center the respond dialog on screen"""
        dialog.update_idletasks()
        width, height = 600, 720
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _create_respond_header(self, canvas, dialog):
        """Create header section matching payment_window.py style"""
        # Header rectangle
        canvas.create_rectangle(0.0, 0.0, 600.0, 98.0, fill="#792D1B", outline="")

        # Back button
        #self._create_respond_back_button(canvas, dialog)

        # Yellow header strip
        canvas.create_rectangle(0.0, 57.0, 600.0, 99.0, fill="#FFDA0C", outline="")

        # Header text
        canvas.create_text(
            300.0,
            78.0,
            text="Respond to Feedback",
            fill="#000000",
            font=("Arial", 16, "bold"),
            anchor="center",
        )

    def _create_respond_back_button(self, canvas, dialog):
        """Create back button for respond dialog"""
        try:
            button_image = PhotoImage(file=self._relative_to_assets("button_back.png"))
            back_button = Button(
                dialog,
                image=button_image,
                borderwidth=0,
                highlightthickness=0,
                command=dialog.destroy,
                relief="flat",
                bg="#792D1B",
                activebackground="#792D1B",
            )
            back_button.place(x=27, y=19, width=15, height=18)
            back_button.image = button_image
        except Exception:
            # Fallback text button
            back_button = Button(
                dialog,
                text="←",
                font=("Arial", 14, "bold"),
                command=dialog.destroy,
                bg="#792D1B",
                fg="white",
                borderwidth=0,
                relief="flat",
            )
            back_button.place(x=20, y=15, width=30, height=30)

    def _create_respond_content(self, canvas, feedback):
        """Create respond content section"""
        # White background panel
        canvas.create_rectangle(
            25.0, 120.0, 575.0, 700.0, fill="#FFFFFF", outline="#DDDDDD", width=2
        )

        # Student name (or Anonymous)
        student_display = (
            "Anonymous" if feedback["is_anonymous"] else feedback["student_name"]
        )

        # Rating display
        rating_stars = self.format_rating_stars(feedback["rating"])

        # Feedback information - centered layout
        info_y_start = 150
        line_height = 30
        center_x = 300.0  # Center of the dialog (600/2)

        details = [
            ("Request Number:", feedback["request_number"]),
            ("Student:", student_display),
            ("Document:", f"{feedback['document_code']} - {feedback['document_name']}"),
            ("Rating:", rating_stars),
            (
                "Date:",
                (
                    feedback["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                    if feedback["created_at"]
                    else "N/A"
                ),
            ),
        ]

        for i, (label, value) in enumerate(details):
            detail_text = f"{label} {value}"
            canvas.create_text(
                center_x,
                info_y_start + (i * line_height),
                text=detail_text,
                fill="#000000",
                font=("Arial", 12, "bold"),
                anchor="center",
            )

        # Comments section
        comments_y = info_y_start + (len(details) * line_height) + 20
        canvas.create_text(
            center_x,
            comments_y,
            text="Student Comments:",
            fill="#792D1B",
            font=("Arial", 14, "bold"),
            anchor="center",
        )

        # Comments text area
        comments_frame = Frame(canvas, bg="#FFFFFF")
        comments_frame.place(x=50, y=comments_y + 20, width=500, height=80)

        comments_text = Text(
            comments_frame,
            font=("Arial", 10),
            wrap="word",
            state="disabled",
            bg="#F8F8F8",
            relief="solid",
            bd=1,
        )
        comments_text.pack(fill="both", expand=True, padx=10, pady=10)
        comments_text.config(state="normal")
        comments_text.insert("1.0", feedback["comments"] or "No comments provided.")
        comments_text.config(state="disabled")

        # Response input section
        response_input_y = comments_y + 120
        canvas.create_text(
            center_x,
            response_input_y,
            text="Your Response:",
            fill="#792D1B",
            font=("Arial", 14, "bold"),
            anchor="center",
        )

        # Response text area
        response_frame = Frame(canvas, bg="#FFFFFF")
        response_frame.place(x=50, y=response_input_y + 20, width=500, height=120)

        self.response_text = Text(
            response_frame,
            font=("Arial", 10),
            wrap="word",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
        )
        self.response_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Buttons
        button_y = response_input_y + 160
        button_frame = Frame(canvas, bg="#FFFFFF")
        button_frame.place(x=80, y=button_y, width=450, height=50)

        # Submit button
        submit_button = Button(
            button_frame,
            text="Submit Response",
            font=("Arial", 12, "bold"),
            bg="#28a745",
            fg="#FFFFFF",
            relief="flat",
            command=lambda: self._submit_feedback_response(canvas, feedback),
            width=15,
            height=2,
        )
        submit_button.pack(side="left", padx=(50, 20))

        # Cancel button
        cancel_button = Button(
            button_frame,
            text="Cancel",
            font=("Arial", 12, "bold"),
            bg="#6c757d",
            fg="#FFFFFF",
            relief="flat",
            command=canvas.master.destroy,
            width=15,
            height=2,
        )
        cancel_button.pack(side="left")

    def _submit_feedback_response(self, canvas, feedback):
        """Submit feedback response"""
        response_content = self.response_text.get("1.0", "end-1c").strip()

        if not response_content:
            messagebox.showerror("Error", "Please enter a response")
            return

        success = self.submit_feedback_response(
            feedback["feedback_id"], response_content
        )

        if success:
            canvas.master.destroy()
            self.load_feedbacks()
            self.update_display()
            messagebox.showinfo("Success", "Response submitted successfully")
        else:
            messagebox.showerror("Error", "Failed to submit response")

    def submit_feedback_response(self, feedback_id, response_content):
        """Submit feedback response to database and send email notification"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False

            cursor = connection.cursor(dictionary=True)

            # Get feedback details and student email
            cursor.execute(
                """
                SELECT
                    f.feedback_id, f.request_id, f.rating, f.comments,
                    dr.request_number,
                    CONCAT(s.first_name, ' ', s.last_name) as student_name,
                    s.student_number, u.email as student_email,
                    dt.code as document_code, dt.name as document_name
                FROM feedback f
                JOIN document_requests dr ON f.request_id = dr.request_id
                JOIN students s ON dr.student_id = s.student_id
                JOIN users u ON s.user_id = u.user_id
                JOIN document_types dt ON dr.document_type_id = dt.document_type_id
                WHERE f.feedback_id = %s
            """,
                (feedback_id,),
            )

            feedback_data = cursor.fetchone()
            if not feedback_data:
                print(f"❌ Feedback not found: {feedback_id}")
                return False

            # Get current admin staff_id
            cursor.execute(
                """
                SELECT s.staff_id, CONCAT(s.first_name, ' ', s.last_name) as staff_name
                FROM staff s
                JOIN users u ON s.user_id = u.user_id
                WHERE u.user_type = 'admin' AND u.is_active = TRUE
                LIMIT 1
            """
            )
            staff_result = cursor.fetchone()
            staff_id = staff_result["staff_id"] if staff_result else None
            staff_name = staff_result["staff_name"] if staff_result else "Administrator"

            # Update feedback with response
            cursor.execute(
                """
                UPDATE feedback
                SET response = %s, responded_to = TRUE, responded_by = %s, responded_at = NOW()
                WHERE feedback_id = %s
            """,
                (response_content, staff_id, feedback_id),
            )

            connection.commit()
            cursor.close()
            connection.close()

            # Send email notification to student
            self.send_feedback_response_email(
                feedback_data, response_content, staff_name
            )

            print(f"✅ Response submitted for feedback {feedback_id}")
            return True

        except Error as e:
            print(f"❌ Error submitting response: {e}")
            return False

    def send_feedback_response_email(self, feedback_data, response_content, staff_name):
        """Send feedback response email to student"""
        try:
            student_email = feedback_data["student_email"]
            if not student_email:
                print("❌ No student email found for feedback response")
                return False

            # Create email content
            subject = f"Feedback Response - Request #{feedback_data['request_number']}"

            # Format rating as stars
            rating_stars = "★" * feedback_data["rating"] + "☆" * (
                5 - feedback_data["rating"]
            )

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>

                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Feedback Response</h2>
                        <p>Dear {feedback_data['student_name']},</p>

                        <p>Thank you for your feedback regarding your document request. We have reviewed your comments and provided a response below.</p>

                        <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Your Feedback Details:</h3>
                            <p><strong>Request Number:</strong> {feedback_data['request_number']}</p>
                            <p><strong>Document:</strong> {feedback_data['document_code']} - {feedback_data['document_name']}</p>
                            <p><strong>Rating:</strong> {rating_stars} ({feedback_data['rating']}/5)</p>
                            <p><strong>Your Comments:</strong></p>
                            <div style="background: white; padding: 15px; border-left: 4px solid #800000; margin: 10px 0;">
                                {feedback_data['comments']}
                            </div>
                        </div>

                        <div style="background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Our Response:</h3>
                            <div style="background: white; padding: 15px; border-left: 4px solid #28a745; margin: 10px 0;">
                                {response_content}
                            </div>
                            <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">
                                <em>Responded by: {staff_name}</em>
                            </p>
                        </div>

                        <p>We appreciate your feedback and are committed to continuously improving our services.</p>

                        <p>If you have any further questions or concerns, please don't hesitate to contact us.</p>

                        <p style="margin-top: 30px;">
                            Best regards,<br>
                            <strong>Pambayang Dalubhasaan ng Marilao</strong><br>
                            Registrar Office
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Send email
            success = self.email_service._send_email_sync(student_email, subject, body)

            if success:
                print(f"✅ Feedback response email sent to {student_email}")
            else:
                print(f"❌ Failed to send feedback response email to {student_email}")
                # Fallback notification
                self._fallback_feedback_email(
                    student_email, subject, response_content, feedback_data
                )

            return success

        except Exception as e:
            print(f"❌ Error sending feedback response email: {e}")
            return False

    def _fallback_feedback_email(
        self, student_email, subject, response_content, feedback_data
    ):
        """Fallback feedback email notification"""
        print("=" * 60)
        print("📧 FEEDBACK RESPONSE EMAIL (FALLBACK)")
        print("=" * 60)
        print(f"To: {student_email}")
        print(f"Subject: {subject}")
        print(f"Request: {feedback_data['request_number']}")
        print(
            f"Document: {feedback_data['document_code']} - {feedback_data['document_name']}"
        )
        print(
            f"Rating: {'★' * feedback_data['rating']}{'☆' * (5 - feedback_data['rating'])}"
        )
        print(f"Student Comments: {feedback_data['comments']}")
        print(f"Admin Response: {response_content}")
        print("=" * 60)

    def view_response(self, feedback):
        """View existing response with payment_window.py layout style"""
        dialog = Toplevel(self.parent)
        dialog.title(f"View Response - {feedback['request_number']}")
        dialog.geometry("600x700")
        dialog.configure(bg="#FCECB7")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        self._center_response_dialog(dialog)

        # Create main canvas
        canvas = Canvas(
            dialog,
            bg="#FCECB7",
            height=700,
            width=600,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        canvas.place(x=0, y=0)

        # Create header section
        self._create_response_header(canvas, dialog)

        # Create content section
        self._create_response_content(canvas, feedback)

    def _center_response_dialog(self, dialog):
        """Center the response dialog on screen"""
        dialog.update_idletasks()
        width, height = 600, 700
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _create_response_header(self, canvas, dialog):
        """Create header section matching payment_window.py style"""
        # Header rectangle
        canvas.create_rectangle(0.0, 0.0, 600.0, 98.0, fill="#792D1B", outline="")

        # Yellow header strip
        canvas.create_rectangle(0.0, 57.0, 600.0, 99.0, fill="#FFDA0C", outline="")

        # Header text
        canvas.create_text(
            300.0,
            78.0,
            text="Admin Response",
            fill="#000000",
            font=("Arial", 16, "bold"),
            anchor="center",
        )

    def _create_response_content(self, canvas, feedback):
        """Create response content section"""
        # White background panel
        canvas.create_rectangle(
            25.0, 120.0, 575.0, 650.0, fill="#FFFFFF", outline="#DDDDDD", width=2
        )

        # Response information - centered layout
        info_y_start = 150
        line_height = 30
        center_x = 300.0  # Center of the dialog (600/2)

        # Response info
        responder_name = (
            f"{feedback['responded_by_first']} {feedback['responded_by_last']}"
            if feedback["responded_by_first"]
            else "Admin"
        )
        response_date = (
            feedback["responded_at"].strftime("%Y-%m-%d %H:%M:%S")
            if feedback["responded_at"]
            else "N/A"
        )

        # Request details
        details = [
            ("Request Number:", feedback["request_number"]),
            ("Responded by:", responder_name),
            ("Response Date:", response_date),
        ]

        for i, (label, value) in enumerate(details):
            detail_text = f"{label} {value}"
            canvas.create_text(
                center_x,
                info_y_start + (i * line_height),
                text=detail_text,
                fill="#000000",
                font=("Arial", 12, "bold"),
                anchor="center",
            )

        # Response content section
        response_y = info_y_start + (len(details) * line_height) + 20
        canvas.create_text(
            center_x,
            response_y,
            text="Response Content:",
            fill="#792D1B",
            font=("Arial", 14, "bold"),
            anchor="center",
        )

        # Response text area
        response_frame = Frame(canvas, bg="#FFFFFF")
        response_frame.place(x=50, y=response_y + 20, width=500, height=200)

        response_text = Text(
            response_frame,
            font=("Arial", 10),
            wrap="word",
            state="disabled",
            bg="#E8F5E8",
            relief="solid",
            bd=1,
        )
        response_text.pack(fill="both", expand=True, padx=10, pady=10)
        response_text.config(state="normal")
        response_text.insert("1.0", feedback["response"] or "No response available.")
        response_text.config(state="disabled")

        # Close button
        close_button = Button(
            canvas,
            text="Close",
            font=("Arial", 12, "bold"),
            bg="#792D1B",
            fg="#FFDA0C",
            relief="flat",
            command=canvas.master.destroy,
            width=15,
            height=2,
        )
        close_button.place(x=center_x - 75, y=response_y + 250)

    def show_no_feedbacks_message(self):
        """Show message when no feedbacks exist"""
        self.canvas.create_text(
            450,
            200,
            anchor="center",
            text="No feedback found",
            fill="#666666",
            font=("Inter", 14, "bold"),
            tags="row",
        )

    def update_navigation(self):
        """Update navigation elements"""
        total_pages = max(
            1,
            (len(self.filtered_feedbacks) + self.feedbacks_per_page - 1)
            // self.feedbacks_per_page,
        )
        self.entry_page_no.config(state="normal")
        self.entry_page_no.delete(0, "end")
        self.entry_page_no.insert(0, f"Page {self.current_page} of {total_pages}")
        self.entry_page_no.config(state="readonly")

        self.button_prev.config(state="normal" if self.current_page > 1 else "disabled")
        self.button_next.config(
            state="normal" if self.current_page < total_pages else "disabled"
        )

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_display()

    def next_page(self):
        """Go to next page"""
        total_pages = max(
            1,
            (len(self.filtered_feedbacks) + self.feedbacks_per_page - 1)
            // self.feedbacks_per_page,
        )
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()

    def refresh_feedbacks(self):
        """Refresh the feedbacks list"""
        print("🔄 Refreshing feedbacks...")
        try:
            self.load_feedbacks()
            self.current_page = 1
            self.update_display()
            print(f"✅ Refresh complete - {len(self.feedbacks)} feedbacks loaded")
        except Exception as e:
            print(f"❌ Error during refresh: {e}")

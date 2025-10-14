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
)
import mysql.connector
from mysql.connector import Error
import sys
import os
from datetime import datetime

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
            (480.0, "Rating", "center"),
            (560.0, "Date", "center"),
            (640.0, "Status", "center"),
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
                    f.feedback_id, f.request_id, f.rating, f.comments, f.suggestions,
                    f.is_anonymous, f.responded_to, f.response, f.created_at,
                    dr.request_number,
                    CONCAT(s.first_name, ' ', s.last_name) as student_name,
                    s.student_number,
                    dt.code as document_code, dt.name as document_name,
                    st.first_name as responded_by_first, st.last_name as responded_by_last,
                    f.responded_at
                FROM feedback f
                JOIN document_requests dr ON f.request_id = dr.request_id
                JOIN students s ON dr.student_id = s.student_id
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
                    str(feedback.get("suggestions", "")),
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
            (480.0, rating_stars, "center"),
            (560.0, formatted_date, "center"),
            (640.0, status_text, "center"),
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
            text="View",
            font=("Inter", 9),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=lambda f=feedback: self.view_feedback_details(f),
        )
        view_button.place(x=680, y=y_position + 8, width=50, height=25)
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
            view_response_button.place(x=740, y=y_position + 8, width=80, height=25)
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
            respond_button.place(x=740, y=y_position + 8, width=60, height=25)
            button_widgets.append(respond_button)

        self.row_widgets.append(button_widgets)

    def view_feedback_details(self, feedback):
        """Open feedback details dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Feedback Details - {feedback['request_number']}")
        dialog.geometry("600x700")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()

        # Feedback details
        details_frame = Frame(dialog, bg="#FFFFFF")
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = Label(
            details_frame,
            text="Feedback Details",
            font=("Inter", 16, "bold"),
            bg="#FFFFFF",
            fg="#792D1B",
        )
        title_label.pack(pady=(0, 20))

        # Student name (or Anonymous)
        student_display = (
            "Anonymous" if feedback["is_anonymous"] else feedback["student_name"]
        )

        # Rating display
        rating_stars = self.format_rating_stars(feedback["rating"])

        # Feedback information
        info_labels = [
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

        for label_text, value_text in info_labels:
            frame = Frame(details_frame, bg="#FFFFFF")
            frame.pack(fill="x", pady=3)

            label = Label(
                frame,
                text=label_text,
                font=("Inter", 10, "bold"),
                bg="#FFFFFF",
                fg="#333333",
                width=20,
                anchor="w",
            )
            label.pack(side="left")

            value = Label(
                frame,
                text=value_text,
                font=("Inter", 10),
                bg="#FFFFFF",
                fg="#666666",
                anchor="w",
                wraplength=400,
            )
            value.pack(side="left", padx=(10, 0))

        # Comments section
        comments_frame = Frame(details_frame, bg="#FFFFFF")
        comments_frame.pack(fill="x", pady=(20, 10))

        comments_label = Label(
            comments_frame,
            text="Comments:",
            font=("Inter", 10, "bold"),
            bg="#FFFFFF",
            fg="#333333",
        )
        comments_label.pack(anchor="w")

        comments_text = Text(
            comments_frame,
            font=("Inter", 10),
            width=60,
            height=4,
            wrap="word",
            state="disabled",
            bg="#F8F8F8",
        )
        comments_text.pack(fill="x", pady=(5, 0))
        comments_text.config(state="normal")
        comments_text.insert("1.0", feedback["comments"] or "No comments provided.")
        comments_text.config(state="disabled")

        # Suggestions section
        suggestions_frame = Frame(details_frame, bg="#FFFFFF")
        suggestions_frame.pack(fill="x", pady=(10, 20))

        suggestions_label = Label(
            suggestions_frame,
            text="Suggestions:",
            font=("Inter", 10, "bold"),
            bg="#FFFFFF",
            fg="#333333",
        )
        suggestions_label.pack(anchor="w")

        suggestions_text = Text(
            suggestions_frame,
            font=("Inter", 10),
            width=60,
            height=4,
            wrap="word",
            state="disabled",
            bg="#F8F8F8",
        )
        suggestions_text.pack(fill="x", pady=(5, 0))
        suggestions_text.config(state="normal")
        suggestions_text.insert(
            "1.0", feedback["suggestions"] or "No suggestions provided."
        )
        suggestions_text.config(state="disabled")

        # Response section (if exists)
        if feedback["responded_to"] and feedback["response"]:
            response_frame = Frame(details_frame, bg="#FFFFFF")
            response_frame.pack(fill="x", pady=(10, 20))

            response_label = Label(
                response_frame,
                text="Admin Response:",
                font=("Inter", 10, "bold"),
                bg="#FFFFFF",
                fg="#333333",
            )
            response_label.pack(anchor="w")

            response_text = Text(
                response_frame,
                font=("Inter", 10),
                width=60,
                height=4,
                wrap="word",
                state="disabled",
                bg="#E8F5E8",
            )
            response_text.pack(fill="x", pady=(5, 0))
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

            response_info = Label(
                response_frame,
                text=f"Responded by: {responder_name} on {response_date}",
                font=("Inter", 9),
                bg="#FFFFFF",
                fg="#666666",
            )
            response_info.pack(anchor="w", pady=(5, 0))

        # Close button
        Button(
            dialog,
            text="Close",
            font=("Inter", 10, "bold"),
            bg="#6c757d",
            fg="#FFFFFF",
            relief="flat",
            command=dialog.destroy,
        ).pack(pady=20)

    def respond_to_feedback(self, feedback):
        """Open respond to feedback dialog"""
        dialog = Toplevel(self.parent)
        dialog.title(f"Respond to Feedback - {feedback['request_number']}")
        dialog.geometry("500x600")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()

        # Title
        title_label = Label(
            dialog,
            text="Respond to Feedback",
            font=("Inter", 14, "bold"),
            bg="#FFFFFF",
            fg="#792D1B",
        )
        title_label.pack(pady=20)

        # Feedback details (read-only)
        details_frame = Frame(dialog, bg="#F8F8F8", relief="solid", bd=1)
        details_frame.pack(fill="x", padx=20, pady=(0, 20))

        student_display = (
            "Anonymous" if feedback["is_anonymous"] else feedback["student_name"]
        )
        rating_stars = self.format_rating_stars(feedback["rating"])

        Label(
            details_frame,
            text=f"Request: {feedback['request_number']}",
            font=("Inter", 10, "bold"),
            bg="#F8F8F8",
        ).pack(anchor="w", padx=10, pady=(10, 5))
        Label(
            details_frame,
            text=f"Student: {student_display}",
            font=("Inter", 10),
            bg="#F8F8F8",
        ).pack(anchor="w", padx=10, pady=2)
        Label(
            details_frame,
            text=f"Document: {feedback['document_code']}",
            font=("Inter", 10),
            bg="#F8F8F8",
        ).pack(anchor="w", padx=10, pady=2)
        Label(
            details_frame,
            text=f"Rating: {rating_stars}",
            font=("Inter", 10),
            bg="#F8F8F8",
        ).pack(anchor="w", padx=10, pady=2)

        # Comments display
        Label(
            details_frame, text="Comments:", font=("Inter", 10, "bold"), bg="#F8F8F8"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        comments_text = Text(
            details_frame,
            font=("Inter", 9),
            width=50,
            height=3,
            wrap="word",
            state="disabled",
            bg="#FFFFFF",
        )
        comments_text.pack(fill="x", padx=10, pady=(0, 10))
        comments_text.config(state="normal")
        comments_text.insert("1.0", feedback["comments"] or "No comments provided.")
        comments_text.config(state="disabled")

        # Response input
        Label(dialog, text="Your Response:", font=("Inter", 10, "bold")).pack(
            anchor="w", padx=20, pady=(0, 5)
        )
        response_text = Text(
            dialog, font=("Inter", 10), width=50, height=8, wrap="word"
        )
        response_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Buttons
        def submit_response():
            response_content = response_text.get("1.0", "end-1c").strip()

            if not response_content:
                messagebox.showerror("Error", "Please enter a response")
                return

            success = self.submit_feedback_response(
                feedback["feedback_id"], response_content
            )

            if success:
                dialog.destroy()
                self.load_feedbacks()
                self.update_display()
                messagebox.showinfo("Success", "Response submitted successfully")
            else:
                messagebox.showerror("Error", "Failed to submit response")

        def cancel_form():
            dialog.destroy()

        button_frame = Frame(dialog, bg="#FFFFFF")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        Button(
            button_frame,
            text="Submit Response",
            font=("Inter", 10, "bold"),
            bg="#28a745",
            fg="#FFFFFF",
            relief="flat",
            command=submit_response,
        ).pack(side="left", padx=(0, 10))
        Button(
            button_frame,
            text="Cancel",
            font=("Inter", 10, "bold"),
            bg="#6c757d",
            fg="#FFFFFF",
            relief="flat",
            command=cancel_form,
        ).pack(side="left")

    def submit_feedback_response(self, feedback_id, response_content):
        """Submit feedback response to database"""
        try:
            connection = self.get_db_connection()
            if not connection:
                return False

            cursor = connection.cursor()

            # Get current admin staff_id (assuming admin user has staff record)
            cursor.execute(
                """
                SELECT s.staff_id FROM staff s
                JOIN users u ON s.user_id = u.user_id
                WHERE u.user_type = 'admin' AND u.is_active = TRUE
                LIMIT 1
            """
            )
            staff_result = cursor.fetchone()
            staff_id = staff_result[0] if staff_result else None

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

            print(f"✅ Response submitted for feedback {feedback_id}")
            return True

        except Error as e:
            print(f"❌ Error submitting response: {e}")
            return False

    def view_response(self, feedback):
        """View existing response"""
        dialog = Toplevel(self.parent)
        dialog.title(f"View Response - {feedback['request_number']}")
        dialog.geometry("500x400")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.parent)
        dialog.grab_set()

        # Title
        title_label = Label(
            dialog,
            text="Admin Response",
            font=("Inter", 14, "bold"),
            bg="#FFFFFF",
            fg="#792D1B",
        )
        title_label.pack(pady=20)

        # Response content
        response_text = Text(
            dialog,
            font=("Inter", 10),
            width=50,
            height=12,
            wrap="word",
            state="disabled",
            bg="#E8F5E8",
        )
        response_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        response_text.config(state="normal")
        response_text.insert("1.0", feedback["response"] or "No response available.")
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

        info_label = Label(
            dialog,
            text=f"Responded by: {responder_name} on {response_date}",
            font=("Inter", 9),
            bg="#FFFFFF",
            fg="#666666",
        )
        info_label.pack(pady=(0, 20))

        # Close button
        Button(
            dialog,
            text="Close",
            font=("Inter", 10, "bold"),
            bg="#6c757d",
            fg="#FFFFFF",
            relief="flat",
            command=dialog.destroy,
        ).pack(pady=20)

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

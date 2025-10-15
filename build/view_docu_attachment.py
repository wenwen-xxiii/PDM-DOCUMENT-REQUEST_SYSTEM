import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import Canvas, Button, PhotoImage, Frame, Label, Scrollbar
import mysql.connector
from mysql.connector import Error
import sys
import os
from pathlib import Path
import tempfile
from PIL import Image, ImageTk
import io
import base64

# Add the parent directory to the path to import your modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing modules
from config import DB_CONFIG

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/{path}"))

class DocumentAttachmentViewer:
    def __init__(self, parent, request_id=None, get_db_connection=None):
        self.parent = parent
        self.request_id = request_id
        self.get_db_connection = get_db_connection
        self.attachments = []
        self.current_attachment_index = 0
        self.temp_files = []  # Store temp file paths for cleanup
        
        # PDF navigation variables
        self.current_pdf_document = None
        self.current_pdf_page = 0
        self.total_pdf_pages = 0
        self.is_viewing_pdf = False
        
        # Store image references to prevent garbage collection
        self.images = []
        
        self.setup_ui()
        self.load_attachments()
        
    def setup_ui(self):
        """Setup the main UI window"""
        self.window = tk.Toplevel(self.parent)
        self.window.geometry("1000x700")
        self.window.configure(bg="#FCECB7")
        self.window.title("Document Attachments Viewer - PDM")
        self.window.resizable(True, True)
        
        # Center the window on screen
        self.center_window()
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Create main canvas
        self.canvas = Canvas(
            self.window,
            bg="#FCECB7",
            height=700,
            width=1000,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)
        
        self.create_ui_elements()
        
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        width = 1000
        height = 720
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_ui_elements(self):
        """Create all UI elements"""
        # Header section
        self.canvas.create_rectangle(0.0, 0.0, 1000.0, 80.0, fill="#792D1B", outline="")
        self.canvas.create_rectangle(0.0, 50.0, 1000.0, 80.0, fill="#FFDA0C", outline="")
        
        # Header text
        self.canvas.create_text(
            500.0, 65.0,
            text="Document Attachments Viewer",
            fill="#000000",
            font=("Inter", 18, "bold"),
            anchor="center"
        )
        
        # Main content area
        self.canvas.create_rectangle(
            25.0, 100.0, 975.0, 670.0,
            fill="#FFFFFF", outline="#DDDDDD", width=2
        )
        
        # File info section
        self.canvas.create_rectangle(
            50.0, 120.0, 950.0, 180.0,
            fill="#F8F9FA", outline="#DDDDDD", width=1
        )
        
        # File name label
        self.canvas.create_text(
            70.0, 140.0,
            text="File Name:",
            fill="#000000",
            font=("Inter", 12, "bold"),
            anchor="nw"
        )
        
        self.file_name_label = Label(
            self.window,
            text="No file selected",
            font=("Inter", 12),
            bg="#F8F9FA",
            fg="#000000",
            anchor="w"
        )
        self.file_name_label.place(x=150, y=140, width=750, height=20)
        
        # File info labels
        self.canvas.create_text(
            70.0, 160.0,
            text="File Size:",
            fill="#000000",
            font=("Inter", 10),
            anchor="nw"
        )
        
        self.file_size_label = Label(
            self.window,
            text="",
            font=("Inter", 10),
            bg="#F8F9FA",
            fg="#666666",
            anchor="w"
        )
        self.file_size_label.place(x=150, y=160, width=200, height=15)
        
        # Navigation buttons
        self.create_navigation_buttons()
        
        # Preview area
        self.create_preview_area()
        
        # Action buttons
        self.create_action_buttons()
        
    def create_navigation_buttons(self):
        """Create navigation buttons for multiple attachments"""
        # Previous button
        self.prev_button = Button(
            self.window,
            text="◀ Previous",
            font=("Inter", 10),
            bg="#792D1B",
            fg="#FFFFFF",
            relief="flat",
            command=self.previous_attachment,
            state="disabled"
        )
        self.prev_button.place(x=330, y=200, width=100, height=30)
        
        # Next button
        self.next_button = Button(
            self.window,
            text="Next ▶",
            font=("Inter", 10),
            bg="#792D1B",
            fg="#FFFFFF",
            relief="flat",
            command=self.next_attachment,
            state="disabled"
        )
        self.next_button.place(x=570, y=200, width=100, height=30)
        
        # File counter
        self.file_counter_label = Label(
            self.window,
            text="0 / 0",
            font=("Inter", 10),
            bg="#FFFFFF",
            fg="#666666"
        )
        self.file_counter_label.place(x=450, y=205, width=100, height=20)
        
    def create_preview_area(self):
        """Create the preview area for documents"""
        # Preview frame
        self.preview_frame = Frame(
            self.window,
            bg="#FFFFFF",
            relief="sunken",
            bd=2
        )
        self.preview_frame.place(x=50, y=250, width=900, height=350)
        
        # Preview canvas
        self.preview_canvas = Canvas(
            self.preview_frame,
            bg="#FFFFFF",
            height=350,
            width=900,
            bd=0,
            highlightthickness=0
        )
        self.preview_canvas.pack(fill="both", expand=True)
        
        # Scrollbars for preview
        self.v_scrollbar = Scrollbar(
            self.preview_frame,
            orient="vertical",
            command=self.preview_canvas.yview
        )
        self.v_scrollbar.pack(side="right", fill="y")
        
        self.h_scrollbar = Scrollbar(
            self.preview_frame,
            orient="horizontal",
            command=self.preview_canvas.xview
        )
        self.h_scrollbar.pack(side="bottom", fill="x")
        
        self.preview_canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )
        
        # Initial message
        self.preview_canvas.create_text(
            450, 175,
            text="No document selected for preview",
            fill="#999999",
            font=("Inter", 14),
            anchor="center"
        )
        
    def create_action_buttons(self):
        """Create action buttons"""
        # Download button
        self.download_button = Button(
            self.window,
            text="📥 Download",
            font=("Inter", 10),
            bg="#28A745",
            fg="#FFFFFF",
            relief="flat",
            command=self.download_attachment,
            state="disabled"
        )
        self.download_button.place(x=300, y=620, width=120, height=35)
        
        # Feedback button
        self.feedback_button = Button(
            self.window,
            text="💬 Feedback",
            font=("Inter", 10),
            bg="#007BFF",
            fg="#FFFFFF",
            relief="flat",
            command=self.open_feedback_dialog,
            state="disabled"
        )
        self.feedback_button.place(x=440, y=620, width=120, height=35)
        
        # Close button
        self.close_button = Button(
            self.window,
            text="✕ Close",
            font=("Inter", 10),
            bg="#DC3545",
            fg="#FFFFFF",
            relief="flat",
            command=self.close_window
        )
        self.close_button.place(x=580, y=620, width=100, height=35)
        
    def load_attachments(self):
        """Load attachments from database"""
        try:
            if not self.request_id:
                messagebox.showwarning("Warning", "No request ID provided")
                return
                
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    attachment_id,
                    file_name,
                    file_data,
                    file_size,
                    file_type,
                    uploaded_by,
                    upload_date,
                    remarks
                FROM document_attachments 
                WHERE request_id = %s
                ORDER BY upload_date DESC
            """, (self.request_id,))
            
            self.attachments = cursor.fetchall()
            cursor.close()
            connection.close()
            
            if not self.attachments:
                messagebox.showinfo("Info", "No attachments found for this request")
                return
                
            # Update UI
            self.update_navigation_buttons()
            self.show_attachment(0)
            
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to load attachments: {str(e)}")
            
    def update_navigation_buttons(self):
        """Update navigation button states"""
        if self.is_viewing_pdf and self.current_pdf_document:
            # PDF page navigation
            self.prev_button.config(state="normal" if self.current_pdf_page > 0 else "disabled")
            self.next_button.config(state="normal" if self.current_pdf_page < self.total_pdf_pages - 1 else "disabled")
            
            # Update file counter to show PDF page info
            self.file_counter_label.config(text=f"Page {self.current_pdf_page + 1} / {self.total_pdf_pages}")
        else:
            # Attachment navigation
            if len(self.attachments) <= 1:
                self.prev_button.config(state="disabled")
                self.next_button.config(state="disabled")
            else:
                self.prev_button.config(state="normal")
                self.next_button.config(state="normal")
                
            # Update file counter
            self.file_counter_label.config(text=f"{self.current_attachment_index + 1} / {len(self.attachments)}")
        
    def show_attachment(self, index):
        """Show the attachment at the given index"""
        if not self.attachments or index < 0 or index >= len(self.attachments):
            return
            
        self.current_attachment_index = index
        attachment = self.attachments[index]
        
        # Update file info
        self.file_name_label.config(text=attachment['file_name'])
        self.file_size_label.config(text=f"{attachment['file_size']:,} bytes")
        
        # Update navigation
        self.update_navigation_buttons()
        
        # Enable action buttons
        self.download_button.config(state="normal")
        self.feedback_button.config(state="normal")
        
        # Show preview
        self.show_preview(attachment)
        
    def show_preview(self, attachment):
        """Show preview of the attachment"""
        try:
            # Clear previous content
            self.preview_canvas.delete("all")
            
            file_data = attachment['file_data']
            file_type = attachment['file_type'] or 'application/octet-stream'
            file_name = attachment['file_name'].lower()
            
            # Handle different file types
            if file_type.startswith('image/') or file_name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.is_viewing_pdf = False
                self.show_image_preview(file_data)
            elif file_type == 'application/pdf' or file_name.endswith('.pdf'):
                self.is_viewing_pdf = True
                self.show_pdf_preview(file_data)
            else:
                self.is_viewing_pdf = False
                self.show_text_preview(file_data, file_name)
                
        except Exception as e:
            self.preview_canvas.create_text(
                450, 175,
                text=f"Error loading preview: {str(e)}",
                fill="#FF0000",
                font=("Inter", 12),
                anchor="center"
            )
            
    def show_image_preview(self, file_data):
        """Show image preview"""
        try:
            # Convert binary data to PIL Image
            image = Image.open(io.BytesIO(file_data))
            
            # Calculate display size (fit within preview area)
            display_width = 800
            display_height = 300
            
            # Calculate scaling factor
            img_width, img_height = image.size
            scale_w = display_width / img_width
            scale_h = display_height / img_height
            scale = min(scale_w, scale_h, 1.0)  # Don't scale up
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            self.images.append(photo)  # Keep reference
            
            # Center the image
            x = (900 - new_width) // 2
            y = (350 - new_height) // 2
            
            self.preview_canvas.create_image(x, y, image=photo, anchor="nw")
            
            # Update scroll region
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
            
        except Exception as e:
            self.preview_canvas.create_text(
                450, 175,
                text=f"Error loading image: {str(e)}",
                fill="#FF0000",
                font=("Inter", 12),
                anchor="center"
            )
            
    def show_pdf_preview(self, file_data):
        """Show PDF preview with page navigation"""
        try:
            # Try to convert PDF to image using PIL (if available)
            try:
                from PIL import Image
                import fitz  # PyMuPDF
                
                # Close previous PDF document if exists
                if self.current_pdf_document:
                    self.current_pdf_document.close()
                
                # Open PDF from bytes
                self.current_pdf_document = fitz.open(stream=file_data, filetype="pdf")
                self.total_pdf_pages = len(self.current_pdf_document)
                self.current_pdf_page = 0  # Reset to first page
                
                if self.total_pdf_pages > 0:
                    self.show_current_pdf_page()
                else:
                    self.preview_canvas.create_text(
                        450, 175,
                        text="PDF is empty or corrupted",
                        fill="#FF0000",
                        font=("Inter", 12),
                        anchor="center"
                    )
                    
            except ImportError:
                # PyMuPDF not available, show message
                self.preview_canvas.create_text(
                    450, 175,
                    text="PDF Preview requires PyMuPDF library\nClick Download to view the PDF",
                    fill="#FFA500",
                    font=("Inter", 12),
                    anchor="center"
                )
                
        except Exception as e:
            self.preview_canvas.create_text(
                450, 175,
                text=f"Error loading PDF: {str(e)}",
                fill="#FF0000",
                font=("Inter", 12),
                anchor="center"
            )
    
    def show_current_pdf_page(self):
        """Show the current PDF page"""
        try:
            if not self.current_pdf_document or self.total_pdf_pages == 0:
                return
                
            from PIL import Image
            import fitz  # PyMuPDF
            
            # Clear previous content
            self.preview_canvas.delete("all")
            
            # Get current page
            page = self.current_pdf_document[self.current_pdf_page]
            
            # Convert to image
            mat = fitz.Matrix(2.0, 2.0)  # Scale factor for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            
            # Calculate display size
            display_width = 800
            display_height = 300
            
            img_width, img_height = image.size
            scale_w = display_width / img_width
            scale_h = display_height / img_height
            scale = min(scale_w, scale_h, 1.0)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            self.images.append(photo)
            
            # Center the image
            x = (900 - new_width) // 2
            y = (350 - new_height) // 2
            
            self.preview_canvas.create_image(x, y, image=photo, anchor="nw")
            
            # Add page info
            self.preview_canvas.create_text(
                450, 320,
                text=f"Page {self.current_pdf_page + 1} of {self.total_pdf_pages} (PDF Preview)",
                fill="#666666",
                font=("Inter", 10),
                anchor="center"
            )
            
        except Exception as e:
            self.preview_canvas.create_text(
                450, 175,
                text=f"Error loading PDF page: {str(e)}",
                fill="#FF0000",
                font=("Inter", 12),
                anchor="center"
            )
            
    def show_text_preview(self, file_data, file_name):
        """Show text preview for text files"""
        try:
            # Try to decode as text
            text_content = file_data.decode('utf-8', errors='ignore')
            
            # Limit preview length
            if len(text_content) > 2000:
                text_content = text_content[:2000] + "\n\n... (truncated)"
                
            # Create text widget for better text display
            text_widget = tk.Text(
                self.preview_canvas,
                wrap="word",
                font=("Consolas", 10),
                bg="#FFFFFF",
                fg="#000000",
                padx=10,
                pady=10
            )
            
            text_widget.insert("1.0", text_content)
            text_widget.config(state="disabled")
            
            # Add text widget to canvas
            self.preview_canvas.create_window(
                450, 175,
                window=text_widget,
                width=850,
                height=300
            )
            
        except Exception as e:
            self.preview_canvas.create_text(
                450, 175,
                text=f"Cannot preview this file type\nClick Download to save the file",
                fill="#666666",
                font=("Inter", 12),
                anchor="center"
            )
            
    def previous_attachment(self):
        """Show previous attachment or PDF page"""
        if self.is_viewing_pdf and self.current_pdf_document:
            # Navigate PDF pages
            if self.current_pdf_page > 0:
                self.current_pdf_page -= 1
                self.show_current_pdf_page()
                self.update_navigation_buttons()
        else:
            # Navigate attachments
            if self.current_attachment_index > 0:
                self.show_attachment(self.current_attachment_index - 1)
            
    def next_attachment(self):
        """Show next attachment or PDF page"""
        if self.is_viewing_pdf and self.current_pdf_document:
            # Navigate PDF pages
            if self.current_pdf_page < self.total_pdf_pages - 1:
                self.current_pdf_page += 1
                self.show_current_pdf_page()
                self.update_navigation_buttons()
        else:
            # Navigate attachments
            if self.current_attachment_index < len(self.attachments) - 1:
                self.show_attachment(self.current_attachment_index + 1)
            
    def download_attachment(self):
        """Download the current attachment"""
        if not self.attachments or self.current_attachment_index >= len(self.attachments):
            return
            
        attachment = self.attachments[self.current_attachment_index]
        
        # Ask user for save location
        file_path = filedialog.asksaveasfilename(
            title="Save Attachment",
            defaultextension="",
            filetypes=[("All files", "*.*")],
            initialfile=attachment['file_name']
        )
        
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(attachment['file_data'])
                messagebox.showinfo("Success", f"File saved successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def open_feedback_dialog(self):
        """Open feedback dialog with the layout shown in the image"""
        try:
            # Create feedback dialog
            feedback_dialog = tk.Toplevel(self.window)
            feedback_dialog.title("Feedback")
            feedback_dialog.geometry("400x300")
            feedback_dialog.configure(bg="#FCECB7")
            feedback_dialog.resizable(False, False)
            
            # Center the dialog
            feedback_dialog.transient(self.window)
            feedback_dialog.grab_set()
            
            # Center the window on screen
            feedback_dialog.update_idletasks()
            width, height = 400, 300
            screen_width = feedback_dialog.winfo_screenwidth()
            screen_height = feedback_dialog.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            feedback_dialog.geometry(f'{width}x{height}+{x}+{y}')
            
            # Force focus
            feedback_dialog.focus_force()
            feedback_dialog.lift()
            
            # Create canvas for layout
            canvas = Canvas(
                feedback_dialog,
                bg="#FCECB7",
                height=300,
                width=400,
                bd=0,
                highlightthickness=0,
                relief="ridge"
            )
            canvas.pack(fill="both", expand=True)
            
            # Title "Feedback" - matching the image layout
            canvas.create_text(
                20, 20,
                text="Feedback",
                fill="#000000",
                font=("Inter", 16, "bold"),
                anchor="nw"
            )
            
            # Text area background (light yellow/cream color with rounded corners)
            canvas.create_rectangle(
                20, 50, 380, 200,
                fill="#FFF1C2",  # Light yellow/cream color
                outline="#D4AF37",  # Light brown border
                width=2
            )
            
            # Text input area
            self.feedback_text = tk.Text(
                feedback_dialog,
                wrap="word",
                font=("Inter", 11),
                bg="#FFF1C2",
                fg="#000000",
                bd=0,
                highlightthickness=0,
                padx=10,
                pady=10
            )
            self.feedback_text.place(x=20, y=50, width=360, height=150)
            
            # Star rating system
            self.create_star_rating(canvas, 20, 220)
            
            # Submit and Cancel buttons
            submit_button = Button(
                feedback_dialog,
                text="Submit",
                font=("Inter", 10),
                bg="#28A745",
                fg="#FFFFFF",
                relief="flat",
                command=lambda: self.submit_feedback(feedback_dialog)
            )
            submit_button.place(x=225, y=260, width=80, height=30)
            
            cancel_button = Button(
                feedback_dialog,
                text="Cancel",
                font=("Inter", 10),
                bg="#6C757D",
                fg="#FFFFFF",
                relief="flat",
                command=feedback_dialog.destroy
            )
            cancel_button.place(x=315, y=260, width=60, height=30)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open feedback dialog: {str(e)}")
    
    def create_star_rating(self, canvas, x, y):
        """Create 5-star rating system matching the image"""
        self.star_rating = 0
        self.star_buttons = []
        
        # Create 5 star buttons
        for i in range(5):
            star_x = x + (i * 35)  # Space stars 35 pixels apart
            
            # Create star outline (matching the image - outline only)
            star_button = Button(
                canvas.master,
                text="★",
                font=("Arial", 20),
                bg="#FCECB7",
                fg="#D4AF37",  # Light brown/gray color
                relief="flat",
                bd=0,
                command=lambda rating=i+1: self.set_star_rating(rating)
            )
            star_button.place(x=star_x, y=y, width=30, height=30)
            self.star_buttons.append(star_button)
    
    def set_star_rating(self, rating):
        """Set the star rating and update visual feedback"""
        self.star_rating = rating
        
        # Update star colors
        for i, star_button in enumerate(self.star_buttons):
            if i < rating:
                # Filled star
                star_button.config(fg="#FFD700", text="★")  # Gold color
            else:
                # Outline star
                star_button.config(fg="#D4AF37", text="☆")  # Light brown/gray
    
    def submit_feedback(self, dialog):
        """Submit feedback to database"""
        try:
            if not self.request_id:
                messagebox.showerror("Error", "No request ID available")
                return
            
            # Get feedback data
            comments = self.feedback_text.get("1.0", "end-1c").strip()
            rating = self.star_rating
            
            if rating == 0:
                messagebox.showwarning("Warning", "Please select a rating")
                return
            
            if not comments:
                messagebox.showwarning("Warning", "Please enter your feedback comments")
                return
            
            # Check if feedback already exists for this request
            connection = self.get_db_connection()
            if not connection:
                messagebox.showerror("Error", "Could not connect to database")
                return
            
            cursor = connection.cursor()
            
            # Check for existing feedback
            cursor.execute("""
                SELECT feedback_id FROM feedback 
                WHERE request_id = %s
            """, (self.request_id,))
            
            existing_feedback = cursor.fetchone()
            
            if existing_feedback:
                # Update existing feedback
                cursor.execute("""
                    UPDATE feedback 
                    SET rating = %s, comments = %s, created_at = CURRENT_TIMESTAMP
                    WHERE request_id = %s
                """, (rating, comments, self.request_id))
                message = "Feedback updated successfully!"
            else:
                # Insert new feedback
                cursor.execute("""
                    INSERT INTO feedback (request_id, rating, comments, is_anonymous)
                    VALUES (%s, %s, %s, %s)
                """, (self.request_id, rating, comments, False))
                message = "Feedback submitted successfully!"
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messagebox.showinfo("Success", message)
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit feedback: {str(e)}")
                
    def close_window(self):
        """Close the window and cleanup"""
        # Cleanup PDF document
        if self.current_pdf_document:
            try:
                self.current_pdf_document.close()
            except:
                pass
            self.current_pdf_document = None
        
        # Cleanup temp files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
                
        self.window.destroy()

# Example usage function
def open_document_attachment_viewer(parent, request_id, get_db_connection):
    """Open the document attachment viewer"""
    try:
        viewer = DocumentAttachmentViewer(parent, request_id, get_db_connection)
        return viewer
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open attachment viewer: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the viewer
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    def get_db_connection():
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    # Test with a sample request ID
    viewer = open_document_attachment_viewer(root, 1, get_db_connection)
    
    if viewer:
        root.mainloop()

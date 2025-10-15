# Example usage of DocumentAttachmentViewer

"""
This file demonstrates how to use the DocumentAttachmentViewer in your application.

The DocumentAttachmentViewer provides:
- PDF preview functionality (requires PyMuPDF)
- Image preview for common formats (PNG, JPG, etc.)
- Text file preview
- Download functionality
- Navigation between multiple attachments
- Database integration with document_attachments table

Integration Examples:
"""

import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from view_docu_attachment import DocumentAttachmentViewer

def example_usage():
    """Example of how to integrate the attachment viewer"""
    
    # Create a test window
    root = tk.Tk()
    root.title("Attachment Viewer Example")
    root.geometry("400x300")
    
    def get_db_connection():
        """Example database connection function"""
        try:
            # Replace with your actual database configuration
            config = {
                'host': 'localhost',
                'user': 'your_username',
                'password': 'your_password',
                'database': 'your_database'
            }
            return mysql.connector.connect(**config)
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def open_viewer():
        """Open the attachment viewer for a specific request"""
        try:
            # Replace with actual request ID
            request_id = 1
            
            viewer = DocumentAttachmentViewer(
                parent=root,
                request_id=request_id,
                get_db_connection=get_db_connection
            )
            
            if viewer:
                print("✅ Attachment viewer opened successfully")
            else:
                print("❌ Failed to open attachment viewer")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open viewer: {str(e)}")
    
    # Create a button to test the viewer
    test_button = tk.Button(
        root,
        text="Open Attachment Viewer",
        command=open_viewer,
        font=("Arial", 12),
        bg="#007BFF",
        fg="white",
        relief="flat",
        padx=20,
        pady=10
    )
    test_button.pack(expand=True)
    
    # Instructions
    instructions = tk.Label(
        root,
        text="Click the button above to test the attachment viewer.\n\nMake sure you have:\n1. Database connection configured\n2. PyMuPDF installed for PDF preview\n3. Valid request_id with attachments",
        font=("Arial", 10),
        justify="left",
        wraplength=350
    )
    instructions.pack(pady=20)
    
    root.mainloop()

def integration_in_document_window():
    """
    Example of how to integrate in DocumentWindow (already implemented)
    
    In document.py, the view_document method now:
    1. Checks if the request has attachments
    2. Opens DocumentAttachmentViewer if attachments exist
    3. Shows basic info if no attachments
    """
    pass

def integration_in_admin_request():
    """
    Example of how to integrate in AdminRequestManager (already implemented)
    
    In admin_request.py, the view_request method now:
    1. Shows an options dialog
    2. Allows viewing request details OR attachments
    3. Displays attachment count
    """
    pass

def database_schema():
    """
    Required database table structure:
    
    CREATE TABLE IF NOT EXISTS document_attachments (
        attachment_id INT AUTO_INCREMENT PRIMARY KEY,
        request_id INT NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_data LONGBLOB NOT NULL,
        file_size INT NOT NULL,
        file_type VARCHAR(100),
        uploaded_by VARCHAR(100) NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        remarks TEXT,
        FOREIGN KEY (request_id) REFERENCES document_requests(request_id) ON DELETE CASCADE
    );
    """
    pass

def features():
    """
    Features of the DocumentAttachmentViewer:
    
    1. PDF Preview:
       - Converts first page of PDF to image
       - Shows page count
       - Requires PyMuPDF library
    
    2. Image Preview:
       - Supports PNG, JPG, JPEG, GIF, BMP
       - Auto-scales to fit preview area
       - Maintains aspect ratio
    
    3. Text Preview:
       - Shows content of text files
       - Truncates long content
       - Uses monospace font
    
    4. Navigation:
       - Previous/Next buttons for multiple attachments
       - File counter display
       - Disabled buttons when appropriate
    
    5. Download:
       - Save attachment to local file
       - Preserves original filename
       - User chooses save location
    
    6. Error Handling:
       - Graceful fallbacks for unsupported files
       - Database connection error handling
       - File corruption handling
    
    7. UI Features:
       - Responsive design
       - Scrollable preview area
       - File information display
       - Professional styling matching PDM theme
    """
    pass

if __name__ == "__main__":
    print("DocumentAttachmentViewer Example")
    print("=" * 40)
    print("This example shows how to use the attachment viewer.")
    print("Make sure to configure your database connection first.")
    print()
    
    # Uncomment the line below to run the example
    # example_usage()
    
    print("To run the example, uncomment the example_usage() call above.")

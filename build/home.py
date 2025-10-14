from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Frame, Label, messagebox
import sys
import os
import tkinter as tk
from tkinter import messagebox
from profile import ProfileWindow
from document import DocumentWindow
import mysql.connector

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
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
        self.profile_window = None

        # Make window resizable
        self.parent.resizable(True, True)
        self.parent.minsize(1270, 790)

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
            return

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()

        # Update header and main bg
        self.canvas.coords("header_bg", 0, 0, width, 98)
        self.canvas.coords("nav_bg", 0, 98, width, 140)
        self.canvas.coords("main_bg", 0, 140, width, height)

        # Update navigation button positions based on window width
        nav_y = 108
        total_width = width
        button_spacing = total_width / 5

        self.button_home.place(x=button_spacing * 1 - 40, y=nav_y, width=80, height=24)
        self.button_programs.place(x=button_spacing * 2 - 50, y=nav_y, width=100, height=24)
        self.button_documents.place(x=button_spacing * 3 - 55, y=nav_y, width=110, height=24)
        self.button_profile.place(x=button_spacing * 4 - 40, y=nav_y, width=80, height=24)

        # Update user interface button positions
        self.button_logout.place(relx=0.95, rely=0.03, anchor="n")

        # Update university text positions
        self.canvas.coords("university_text", 128, 24)
        self.canvas.coords("motto_text", 128, 57)

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

        # Create scalable background rectangles
        self.canvas.create_rectangle(0, 0, width, 98, fill="#792D1B", outline="", tags="header_bg")
        self.canvas.create_rectangle(0, 98, width, 140, fill="#FFDA0C", outline="", tags="nav_bg")
        self.canvas.create_rectangle(0, 140, width, height, fill="#F5F5F5", outline="", tags="main_bg")

        # University header text
        self.canvas.create_text(128, 24, anchor="nw", text="PAMBAYANG DALUBHAASAAN NG MARILAO",
                               fill="#FFDA0C", font=("Inter SemiBold", 24 * -1), tags="university_text")
        self.canvas.create_text(128, 57, anchor="nw", text="\"Where quality education is a right, not a privilege\"",
                               fill="#FFDA0C", font=("Inter SemiBold", 14 * -1), tags="motto_text")

        # University logo
        try:
            image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
            self.image_1 = image_image_1
            self.canvas.create_image(79.0, 49.0, image=image_image_1, tags="logo")
        except Exception as e:
            print(f"Could not load logo: {e}")

        # Create navigation buttons
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
        self.show_dashboard()

    def show_dashboard(self):
        """Show the main dashboard content with hero image"""
        self.current_content = "dashboard"

        # Clear previous content
        self.clear_content()

        # Get current window size for responsive layout
        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        content_height = height - 140

        # Main content frame
        main_frame = Frame(self.parent, bg="#000000")
        main_frame.place(x=0, y=140, width=width, height=content_height)

        # Hero container
        hero_container = Canvas(main_frame, bg="#000000", bd=0, highlightthickness=0)
        hero_container.pack(fill="both", expand=True)

        try:
            from PIL import Image, ImageTk

            # Load background image (building - image_2.png)
            bg_path = resource_path("resources/assets/frame0/image_2.png")
            bg_image = Image.open(bg_path)

            # Resize background to fit content area
            hero_width = width
            hero_height = max(1, content_height)
            bg_resized = bg_image.resize((hero_width, hero_height), Image.Resampling.LANCZOS)

            # Load and composite student images on top
            # Try to load student images: image_4.png (blue), image_5.png (dark), image_3.png (white)
            student_positions = []
            student_images = []

            try:
                # Student 1 - image_5.png (dark shirt) - left side (no stretch, maintain aspect ratio)
                img5_path = resource_path("resources/assets/frame0/image_5.png")
                img5 = Image.open(img5_path)
                img5_height = int(hero_height * 0.75)
                img5_width = int(img5_height * img5.width / img5.height)
                img5_resized = img5.resize((img5_width, img5_height), Image.Resampling.LANCZOS)
                student_images.append((img5_resized, (int(hero_width * 0.08), int(hero_height * 0.25))))

                # Student 2 - image_4.png (blue shirt) - center (no stretch, maintain aspect ratio)
                img4_path = resource_path("resources/assets/frame0/image_4.png")
                img4 = Image.open(img4_path)
                img4_height = int(hero_height * 0.85)
                img4_width = int(img4_height * img4.width / img4.height)
                img4_resized = img4.resize((img4_width, img4_height), Image.Resampling.LANCZOS)
                student_images.append((img4_resized, (int(hero_width * 0.2), int(hero_height * 0.15))))

                # Student 3 - image_3.png (white shirt) - right of students area (no stretch, maintain aspect ratio)
                img3_path = resource_path("resources/assets/frame0/image_3.png")
                img3 = Image.open(img3_path)
                img3_height = int(hero_height * 0.75)
                img3_width = int(img3_height * img3.width / img3.height)
                img3_resized = img3.resize((img3_width, img3_height), Image.Resampling.LANCZOS)
                student_images.append((img3_resized, (int(hero_width * 0.42), int(hero_height * 0.25))))

            except Exception as e:
                print(f"Could not load student images: {e}")
                student_images = []

            # Composite the images - layer them so blue shirt guy is on top
            composite = bg_resized.convert('RGB')

            # First paste the side students (they go behind)
            for i, (student_img, pos) in enumerate(student_images):
                if i != 1:  # Skip the blue shirt guy for now (index 1)
                    student_img_rgb = student_img.convert('RGB')
                    composite.paste(student_img_rgb, pos, student_img if student_img.mode == 'RGBA' else None)

            # Then paste the blue shirt guy on top (index 1)
            if len(student_images) > 1:
                blue_shirt_img, blue_shirt_pos = student_images[1]
                blue_shirt_rgb = blue_shirt_img.convert('RGB')
                composite.paste(blue_shirt_rgb, blue_shirt_pos, blue_shirt_img if blue_shirt_img.mode == 'RGBA' else None)

            self.hero_image = ImageTk.PhotoImage(composite)

            # Display composite image on canvas
            hero_container.create_image(0, 0, image=self.hero_image, anchor="nw")

            # Calculate overlay box dimensions
            overlay_width = int(width * 0.38)
            overlay_height_box1 = int(content_height * 0.28)
            overlay_height_box2 = int(content_height * 0.28)

            # Right side starting position
            overlay_x_start = width - overlay_width - 20
            overlay_y_box1 = int(content_height * 0.12)
            overlay_y_box2 = int(content_height * 0.52)

            # First text box (top right)
            hero_container.create_rectangle(
                overlay_x_start, overlay_y_box1,
                overlay_x_start + overlay_width, overlay_y_box1 + overlay_height_box1,
                fill="#9B6B54",
                outline="",
                tags="text_box1"
            )

            # First description text
            desc_text_1 = """The Pambayang Dalubhasa'an ng Marilao (PDNM), one of the premier higher educational institutions in the region in Bulacan, officially organized in 1952. The institution continues to work towards providing quality subsidized tertiary education and teacher training programmes committed to produce competitive, competitive, capable, and skilled graduates who will be successful in their chosen field."""

            hero_container.create_text(
                overlay_x_start + 15, overlay_y_box1 + 15,
                text=desc_text_1,
                font=("Inter", 9),
                fill="white",
                anchor="nw",
                width=overlay_width - 30,
                justify="left"
            )

            # Second text box (bottom right)
            hero_container.create_rectangle(
                overlay_x_start, overlay_y_box2,
                overlay_x_start + overlay_width, overlay_y_box2 + overlay_height_box2,
                fill="#9B6B54",
                outline="",
                tags="text_box2"
            )

            # Second description text
            desc_text_2 = """Cognizant of the importance of contributing to the realization of national development goals and right of every citizen to quality education, PDNM commit itself to the provision of quality education, and must be students into productive and responsible citizens who are imbued with virtues, aware of their national heritage and proud of their local culture."""

            hero_container.create_text(
                overlay_x_start + 15, overlay_y_box2 + 15,
                text=desc_text_2,
                font=("Inter", 9),
                fill="white",
                anchor="nw",
                width=overlay_width - 30,
                justify="left"
            )

        except Exception as e:
            print(f"Could not load background image: {e}")
            # Fallback
            hero_container.create_rectangle(0, 0, width, content_height, fill="#2a2a2a")
            hero_container.create_text(
                width // 2, content_height // 2,
                text="Welcome to Document Request System",
                font=("Inter Bold", 24),
                fill="#FFDA0C"
            )

    def show_home(self):
        """Show home dashboard"""
        self.show_dashboard()

    def show_programs(self):
        """Show programs interface"""
        self.current_content = "programs"
        self.clear_content()



        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        content_height = height - 140

        content_frame = Frame(self.parent, bg="#F5F5F5")
        content_frame.place(x=0, y=140, width=width, height=content_height)

        programs_label = Label(
            content_frame,
            text="Academic Programs\n\nThis area will contain information about\navailable academic programs and courses.",
            font=("Inter Bold", 18),
            bg="#F5F5F5",
            fg="#792D1B",
            justify="center"
        )
        programs_label.pack(expand=True)

    def show_document_request(self):
        """Show document request to user using separate window"""
        self.current_content = "document"
        self.clear_content()

        print(f"🔍 DEBUG: Passing user_data to DocumentWindow: {self.user_data}")
        print(f"🔍 DEBUG: User ID in user_data: {self.user_data.get('user_id')}")
        print(f"🔍 DEBUG: Student number in user_data: {self.user_data.get('student_number')}")

        navigation_callbacks = {
            'home': self.show_home,
            'programs': self.show_programs,
            'documents': self.show_document_request,
            'logout': self.logout
        }

        self.document_window = DocumentWindow(
            parent=self.parent,
            user_data=self.user_data,
            user_type=self.user_type,
            get_db_connection=self.get_db_connection,
            navigation_callbacks=navigation_callbacks
        )

    def show_profile(self):
        """Show user profile using the separate ProfileWindow"""
        self.current_content = "profile"
        self.clear_content()

        navigation_callbacks = {
            'home': self.show_home,
            'programs': self.show_programs,
            'documents': self.show_document_request,
            'logout': self.logout
        }

        self.profile_window = ProfileWindow(
            parent=self.parent,
            user_data=self.user_data,
            user_type=self.user_type,
            get_db_connection=self.get_db_connection,
            navigation_callbacks=navigation_callbacks
        )

    def clear_content(self):
        """Clear current content but keep navigation"""
        if hasattr(self, 'profile_window') and self.profile_window:
            try:
                self.profile_window.destroy()
            except:
                pass
            self.profile_window = None

        for widget in self.parent.winfo_children():
            if widget not in [self.canvas, self.button_home, self.button_programs,
                            self.button_documents, self.button_profile,
                            self.button_logout]:
                try:
                    widget.destroy()
                except:
                    pass

    def logout(self):
        """Logout user and return to login"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.logout_callback()
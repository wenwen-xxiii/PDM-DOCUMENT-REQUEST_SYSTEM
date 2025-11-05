from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Frame, Label, messagebox
import sys
import os
import tkinter as tk
import asyncio
from tkinter import messagebox
from views.profile import ProfileWindow
from views.document import DocumentWindow
import mysql.connector
import aiomysql
from config.config import DB_CONFIG

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
    def __init__(
        self, parent, user_data, user_type, logout_callback, get_db_connection
    ):
        self.parent = parent
        self.user_data = user_data
        self.user_type = user_type
        self.logout_callback = logout_callback
        self.get_db_connection = get_db_connection
        self.current_content = None
        self.profile_window = None

        # Store references to background images to prevent garbage collection
        self.home_bg_image = None
        self.programs_bg_image = None
        self.home_bg_image_id = None
        self.programs_bg_image_id = None

        # Make window resizable
        self.parent.resizable(True, True)
        self.parent.minsize(1270, 790)

        # Bind resize event
        self.parent.bind("<Configure>", self.on_resize)

        self.setup_ui()

    async def get_async_db_connection(self):
        """Get async database connection"""
        try:
            connection = await aiomysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                db=DB_CONFIG['database'],
                port=DB_CONFIG['port']
            )
            return connection
        except Exception as e:
            print(f"Async database connection failed: {e}")
            return None

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

        # Update navigation button positions based on window width
        nav_y = 108
        total_width = width
        button_spacing = total_width / 5

        self.button_home.place(x=button_spacing * 1 - 40, y=nav_y, width=80, height=24)
        self.button_programs.place(
            x=button_spacing * 2 - 50, y=nav_y, width=100, height=24
        )
        self.button_documents.place(
            x=button_spacing * 3 - 55, y=nav_y, width=110, height=24
        )
        self.button_profile.place(
            x=button_spacing * 4 - 40, y=nav_y, width=80, height=24
        )

        # Update user interface button positions
        self.button_logout.place(relx=0.95, rely=0.03, anchor="n")

        # Update university text positions
        self.canvas.coords("university_text", 128, 24)
        self.canvas.coords("motto_text", 128, 57)

        # Resize background image based on current content
        content_height = max(1, height - 140)

        if self.current_content == "home" and hasattr(self, 'pil_home_bg_image'):
            self.resize_and_display_image(
                self.pil_home_bg_image,
                "home_bg_image",
                width,
                content_height
            )
        elif self.current_content == "programs" and hasattr(self, 'pil_programs_bg_image'):
            self.resize_and_display_image(
                self.pil_programs_bg_image,
                "programs_bg_image",
                width,
                content_height
            )

    def resize_and_display_image(self, pil_image, tag, width, height):
        """
        Resize and display an image on the canvas to fit the available space.
        """
        try:
            from PIL import Image, ImageTk

            # Resize the image to fit the content area
            resized_image = pil_image.resize(
                (width, height),
                Image.Resampling.LANCZOS
            )

            # Convert to PhotoImage
            photo_image = ImageTk.PhotoImage(resized_image)

            # Update or create the image on canvas
            if self.canvas.find_withtag(tag):
                # Image exists, update it
                self.canvas.itemconfig(tag, image=photo_image)
            else:
                # Create new image
                self.canvas.create_image(
                    0, 140,
                    image=photo_image,
                    anchor="nw",
                    tags=tag
                )

            # Store reference to prevent garbage collection
            if tag == "home_bg_image":
                self.home_bg_image = photo_image
            elif tag == "programs_bg_image":
                self.programs_bg_image = photo_image

        except Exception as e:
            print(f"Could not resize image: {e}")

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
        self.canvas.create_rectangle(
            0, 98, width, 140, fill="#FFDA0C", outline="", tags="nav_bg"
        )
        self.canvas.create_rectangle(
            0, 0, width, 98, fill="#792D1B", outline="", tags="header_bg"
        )

        # University header text
        self.canvas.create_text(
            128,
            24,
            anchor="nw",
            text="PAMBAYANG DALUBHAASAAN NG MARILAO",
            fill="#FFDA0C",
            font=("Inter SemiBold", 24 * -1),
            tags="university_text",
        )
        self.canvas.create_text(
            128,
            57,
            anchor="nw",
            text='"Where quality education is a right, not a privilege"',
            fill="#FFDA0C",
            font=("Inter SemiBold", 14 * -1),
            tags="motto_text",
        )

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
            command=self.show_home,
        )

        self.button_programs = Button(
            self.parent,
            text="Programs",
            font=("Inter", 16),
            bg="#FFDA0C",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=self.show_programs,
        )

        self.button_documents = Button(
            self.parent,
            text="Documents",
            font=("Inter", 16),
            bg="#FFDA0C",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=self.show_document_request,
        )

        self.button_profile = Button(
            self.parent,
            text="Profile",
            font=("Inter", 16),
            bg="#FFDA0C",
            fg="#792D1B",
            relief="flat",
            cursor="hand2",
            command=self.show_profile,
        )

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

        # Initial button placement and show home
        self.update_layout()
        self.show_home()

    async def show_home_async(self):
        """Show home dashboard asynchronously"""
        self.current_content = "home"
        self.clear_content()

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        content_height = max(1, height - 140)

        # Hide programs background if it exists
        if self.canvas.find_withtag('programs_bg_image'):
            self.canvas.itemconfig('programs_bg_image', state='hidden')

        # Load and display the home background image
        try:
            from PIL import Image, ImageTk

            bg_path = resource_path("resources/assets/frame0/image_10.png")
            self.pil_home_bg_image = Image.open(bg_path)

            # Resize the image
            resized_image = self.pil_home_bg_image.resize(
                (width, content_height),
                Image.Resampling.LANCZOS
            )
            self.home_bg_image = ImageTk.PhotoImage(resized_image)

            # Create or update the image on canvas
            if self.canvas.find_withtag('home_bg_image'):
                self.canvas.itemconfig('home_bg_image', image=self.home_bg_image, state='normal')
            else:
                self.home_bg_image_id = self.canvas.create_image(
                    0, 140,
                    image=self.home_bg_image,
                    anchor="nw",
                    tags="home_bg_image"
                )

        except Exception as e:
            print(f"Could not load home background image: {e}")
            if not self.canvas.find_withtag('home_bg_image'):
                self.canvas.create_rectangle(
                    0, 140, width, height, fill="#FCECB7", outline="", tags="home_bg_image"
                )

    def show_home(self):
        """Show home interface - OPTIMIZED FOR SPEED"""
        self.current_content = "home"
        self.clear_content()

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        content_height = max(1, height - 140)

        # Hide programs background if it exists
        if self.canvas.find_withtag('programs_bg_image'):
            self.canvas.itemconfig('programs_bg_image', state='hidden')

        # Load and display the home background image
        try:
            from PIL import Image, ImageTk

            bg_path = resource_path("resources/assets/frame0/image_10.png")
            self.pil_home_bg_image = Image.open(bg_path)

            # Resize the image
            resized_image = self.pil_home_bg_image.resize(
                (width, content_height),
                Image.Resampling.LANCZOS
            )
            self.home_bg_image = ImageTk.PhotoImage(resized_image)

            # Create or update the image on canvas
            if self.canvas.find_withtag('home_bg_image'):
                self.canvas.itemconfig('home_bg_image', image=self.home_bg_image, state='normal')
            else:
                self.home_bg_image_id = self.canvas.create_image(
                    0, 140,
                    image=self.home_bg_image,
                    anchor="nw",
                    tags="home_bg_image"
                )

        except Exception as e:
            print(f"Could not load home background image: {e}")
            if not self.canvas.find_withtag('home_bg_image'):
                self.canvas.create_rectangle(
                    0, 140, width, height, fill="#FCECB7", outline="", tags="home_bg_image"
                )

    async def show_programs_async(self):
        """Show programs interface asynchronously"""
        self.current_content = "programs"
        self.clear_content()

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        content_height = max(1, height - 140)

        # Hide home background if it exists
        if self.canvas.find_withtag('home_bg_image'):
            self.canvas.itemconfig('home_bg_image', state='hidden')

        # Load and display the programs background image
        try:
            from PIL import Image, ImageTk

            bg_path = resource_path("resources/assets/frame0/image_11.png")
            self.pil_programs_bg_image = Image.open(bg_path)

            # Resize the image
            resized_image = self.pil_programs_bg_image.resize(
                (width, content_height),
                Image.Resampling.LANCZOS
            )
            self.programs_bg_image = ImageTk.PhotoImage(resized_image)

            # Create or update the image on canvas
            if self.canvas.find_withtag('programs_bg_image'):
                self.canvas.itemconfig('programs_bg_image', image=self.programs_bg_image, state='normal')
            else:
                self.programs_bg_image_id = self.canvas.create_image(
                    0, 140,
                    image=self.programs_bg_image,
                    anchor="nw",
                    tags="programs_bg_image"
                )

        except Exception as e:
            print(f"Could not load programs background image: {e}")
            if not self.canvas.find_withtag('programs_bg_image'):
                self.canvas.create_rectangle(
                    0, 140, width, height, fill="white", outline="", tags="programs_bg_image"
                )

    def show_programs(self):
        """Show programs interface - OPTIMIZED FOR SPEED"""
        self.current_content = "programs"
        self.clear_content()

        width = self.parent.winfo_width()
        height = self.parent.winfo_height()
        content_height = max(1, height - 140)

        # Hide home background if it exists
        if self.canvas.find_withtag('home_bg_image'):
            self.canvas.itemconfig('home_bg_image', state='hidden')

        # Load and display the programs background image
        try:
            from PIL import Image, ImageTk

            bg_path = resource_path("resources/assets/frame0/image_11.png")
            self.pil_programs_bg_image = Image.open(bg_path)

            # Resize the image
            resized_image = self.pil_programs_bg_image.resize(
                (width, content_height),
                Image.Resampling.LANCZOS
            )
            self.programs_bg_image = ImageTk.PhotoImage(resized_image)

            # Create or update the image on canvas
            if self.canvas.find_withtag('programs_bg_image'):
                self.canvas.itemconfig('programs_bg_image', image=self.programs_bg_image, state='normal')
            else:
                self.programs_bg_image_id = self.canvas.create_image(
                    0, 140,
                    image=self.programs_bg_image,
                    anchor="nw",
                    tags="programs_bg_image"
                )

        except Exception as e:
            print(f"Could not load programs background image: {e}")
            if not self.canvas.find_withtag('programs_bg_image'):
                self.canvas.create_rectangle(
                    0, 140, width, height, fill="white", outline="", tags="programs_bg_image"
                )

    async def show_document_request_async(self):
        """Show document request asynchronously"""
        self.current_content = "document"
        self.clear_content()

        print(f"🔍 DEBUG: Passing user_data to DocumentWindow: {self.user_data}")
        print(f"🔍 DEBUG: User ID in user_data: {self.user_data.get('user_id')}")
        print(
            f"🔍 DEBUG: Student number in user_data: {self.user_data.get('student_number')}"
        )

        navigation_callbacks = {
            "home": self.show_home,
            "programs": self.show_programs,
            "documents": self.show_document_request,
            "logout": self.logout,
        }

        self.document_window = DocumentWindow(
            parent=self.parent,
            user_data=self.user_data,
            user_type=self.user_type,
            get_db_connection=self.get_db_connection,
            navigation_callbacks=navigation_callbacks,
        )

    def show_document_request(self):
        """Show document request interface - ULTRA FAST WITH CACHING"""
        self.current_content = "document"
        
        # Check if document window already exists and just show it
        if hasattr(self, 'document_window') and self.document_window:
            try:
                # Always refresh data FIRST when navigating to document window to get latest status
                print("📋 Navigating to document window - refreshing data...")
                self.document_window.refresh_if_needed()
                # Then show the existing window (instant)
                self.document_window.main_frame.lift()
                self.document_window.main_frame.tkraise()
                # Force UI update after showing
                self.parent.update_idletasks()
                return
            except Exception as e:
                print(f"Error showing cached document window: {e}")
                # If cached window is corrupted, recreate it
                if hasattr(self, 'document_window'):
                    try:
                        self.document_window.destroy()
                    except:
                        pass
                    self.document_window = None
        
        # Clear current content
        self.clear_content()

        print(f"🔍 DEBUG: Creating new DocumentWindow with user_data: {self.user_data}")
        
        # Add student_id to user_data if not present (cached for speed)
        if 'student_id' not in self.user_data:
            user_id = self.user_data.get('user_id')
            if user_id:
                try:
                    # Use synchronous database connection for speed
                    db_connection = self.get_db_connection()
                    if db_connection:
                        cursor = db_connection.cursor()
                        cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (user_id,))
                        result = cursor.fetchone()
                        cursor.close()
                        db_connection.close()
                        
                        if result:
                            self.user_data['student_id'] = result[0]
                            print(f"✅ Found student_id: {result[0]}")
                except Exception as e:
                    print(f"❌ Error getting student_id: {e}")

        navigation_callbacks = {
            "home": self.show_home,
            "programs": self.show_programs,
            "documents": self.show_document_request,
            "logout": self.logout,
        }

        # Create new document window
        self.document_window = DocumentWindow(
            parent=self.parent,
            user_data=self.user_data,
            user_type=self.user_type,
            get_db_connection=self.get_db_connection,
            navigation_callbacks=navigation_callbacks,
        )

    async def show_profile_async(self):
        """Show user profile asynchronously"""
        self.current_content = "profile"
        self.clear_content()

        navigation_callbacks = {
            "home": self.show_home,
            "programs": self.show_programs,
            "documents": self.show_document_request,
            "logout": self.logout,
        }

        self.profile_window = ProfileWindow(
            parent=self.parent,
            user_data=self.user_data,
            user_type=self.user_type,
            get_db_connection=self.get_db_connection,
            navigation_callbacks=navigation_callbacks,
        )

    def show_profile(self):
        """Show profile interface - ULTRA FAST WITH CACHING"""
        self.current_content = "profile"
        
        # Check if profile window already exists and just show it
        if hasattr(self, 'profile_window') and self.profile_window:
            try:
                # Just show the existing window (instant)
                self.profile_window.main_frame.lift()
                self.profile_window.main_frame.tkraise()
                return
            except Exception as e:
                print(f"Error showing cached profile window: {e}")
                # If cached window is corrupted, recreate it
                if hasattr(self, 'profile_window'):
                    try:
                        self.profile_window.destroy()
                    except:
                        pass
                    self.profile_window = None
        
        # Clear current content
        self.clear_content()

        navigation_callbacks = {
            "home": self.show_home,
            "programs": self.show_programs,
            "documents": self.show_document_request,
            "logout": self.logout,
        }

        from views.profile import ProfileWindow
        self.profile_window = ProfileWindow(
            parent=self.parent,
            user_data=self.user_data,
            user_type=self.user_type,
            get_db_connection=self.get_db_connection,
            navigation_callbacks=navigation_callbacks,
        )

    def clear_content(self):
        """Clear current content but keep navigation - OPTIMIZED WITH CACHING"""
        # Only hide windows, don't destroy them for instant switching
        if hasattr(self, "profile_window") and self.profile_window:
            try:
                self.profile_window.main_frame.lower()
            except Exception as e:
                print(f"Error hiding profile window: {e}")

        if hasattr(self, "document_window") and self.document_window:
            try:
                self.document_window.main_frame.lower()
            except Exception as e:
                print(f"Error hiding document window: {e}")

        if hasattr(self, "programs_content_frame") and self.programs_content_frame:
            try:
                self.programs_content_frame.lower()
            except Exception as e:
                print(f"Error hiding programs content: {e}")

        # Hide any other content frames but don't destroy them
        for widget in self.parent.winfo_children():
            if widget not in [
                self.canvas,
                self.button_home,
                self.button_programs,
                self.button_documents,
                self.button_profile,
                self.button_logout,
            ]:
                try:
                    # Only hide, don't destroy for caching
                    if hasattr(widget, 'lower'):
                        widget.lower()
                except:
                    pass

    def clear_all_cached_windows(self):
        """Clear all cached windows (used on logout)"""
        if hasattr(self, "profile_window") and self.profile_window:
            try:
                self.profile_window.destroy()
            except:
                pass
            self.profile_window = None

        if hasattr(self, "document_window") and self.document_window:
            try:
                self.document_window.destroy()
            except:
                pass
            self.document_window = None

        if hasattr(self, "programs_content_frame") and self.programs_content_frame:
            try:
                self.programs_content_frame.destroy()
            except:
                pass
            self.programs_content_frame = None

    def logout(self):
        """Logout user and return to login"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            # Clear all cached windows on logout
            self.clear_all_cached_windows()
            self.logout_callback()
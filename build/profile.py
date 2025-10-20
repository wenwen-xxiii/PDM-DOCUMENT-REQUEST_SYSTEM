from pathlib import Path
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox
from tkinter import ttk, filedialog, Frame, Label
from PIL import Image, ImageTk
import datetime
import os, sys
import mysql.connector
from mysql.connector import Error
import io

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/profile/{path}"))

class ProfileWindow:
    def __init__(self, parent, user_data=None, user_type=None, get_db_connection=None, navigation_callbacks=None):
        self.parent = parent
        self.user_data = user_data or {}
        self.user_type = user_type
        self.get_db_connection = get_db_connection
        self.navigation_callbacks = navigation_callbacks or {}
        self.is_edit_mode = False
        self.profile_image_data = None
        self.entry_fullname = None  # Initialize as None
        
        # Create main frame for profile content only (starts below navigation)
        self.main_frame = Frame(self.parent, bg="#FCECB7")
        self.main_frame.place(x=0, y=140, width=1270, height=650)  # Start below navigation
        
        # Setup custom styles
        self.setup_styles()
        self.setup_ui()
        self.load_user_data()

    def setup_styles(self):
        """Setup custom styles for comboboxes"""
        self.style = ttk.Style()
        self.style.theme_use("default")
        
        # Configure normal state
        self.style.configure("Custom.TCombobox",
                            fieldbackground="#FFF1C2",
                            background="#FFF1C2",
                            foreground="#000716",
                            borderwidth=0,
                            focuscolor="none")
        
        # Configure disabled state
        self.style.map("Custom.TCombobox",
                      fieldbackground=[("disabled", "#FFF1C2")],
                      background=[("disabled", "#FFF1C2")],
                      foreground=[("disabled", "#000716")])

    def setup_ui(self):
        """Setup the profile content only (no header/navigation)"""
        
        # Create canvas for profile content
        self.canvas = Canvas(
            self.main_frame,
            bg="#FCECB7",
            height=650,
            width=1270,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.pack(fill="both", expand=True)

        # ---------------- LEFT PANEL ----------------
        # Profile picture box (adjusted y-positions by -140)
        self.canvas.create_rectangle(71.0, 42.0, 386.0, 255.0, fill="#FFFFFF", outline="")
        
        # Student info box (adjusted y-positions by -140)
        self.canvas.create_rectangle(71.0, 279.0, 386.0, 602.0, fill="#FFFFFF", outline="")

        # ---------------- RIGHT PANEL ----------------
        self.canvas.create_rectangle(419.0, 42.0, 1217.0, 602.0, fill="#FFFFFF", outline="")

        # Setup profile picture (with adjusted positions)
        self.setup_profile_picture()
        
        # Setup all input fields (with adjusted positions)
        self.setup_input_fields()
        
        # Setup buttons (with adjusted positions)
        self.setup_buttons()

    def proper_case_name(self, name):
        """Convert name to proper case handling special cases"""
        if not name:
            return ""
        
        # List of common prefixes and particles that should be handled specially
        lowercase_particles = {'de', 'del', 'de la', 'van', 'von', 'y', 'e', 'di', 'da', 'dos', 'das', 'do'}
        uppercase_particles = {'II', 'III', 'IV', 'V', 'VI', 'JR', 'SR', 'IIII'}
        
        # Split the name into parts
        parts = name.split()
        proper_parts = []
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
                
            # Handle particles and special cases
            part_lower = part.lower()
            if part_lower in lowercase_particles:
                # Keep particles in lowercase unless they're at the start
                if i == 0:
                    proper_parts.append(part.title())
                else:
                    proper_parts.append(part_lower)
            elif part.upper() in uppercase_particles:
                # Keep roman numerals and suffixes in uppercase
                proper_parts.append(part.upper())
            elif "'" in part or "-" in part:
                # Handle names with apostrophes or hyphens (like O'Connor, Smith-Jones)
                if "-" in part:
                    # Handle hyphenated names
                    hyphen_parts = part.split('-')
                    proper_hyphen_parts = []
                    for hp in hyphen_parts:
                        if hp.lower() in lowercase_particles:
                            proper_hyphen_parts.append(hp.lower())
                        else:
                            proper_hyphen_parts.append(hp.capitalize())
                    proper_parts.append('-'.join(proper_hyphen_parts))
                elif "'" in part:
                    # Handle names with apostrophes
                    apostrophe_parts = part.split("'")
                    proper_apostrophe_parts = []
                    for ap in apostrophe_parts:
                        if ap:
                            proper_apostrophe_parts.append(ap.capitalize())
                        else:
                            proper_apostrophe_parts.append("'")
                    proper_parts.append("'".join(proper_apostrophe_parts))
                else:
                    proper_parts.append(part.capitalize())
            else:
                # Standard capitalization for regular names
                proper_parts.append(part.capitalize())
        
        return ' '.join(proper_parts)

    def format_display_name(self, first_name, middle_name, last_name):
        """Format name for display: Firstname MiddleInitial. Lastname with proper casing"""
        if not first_name:
            return ""
        
        # Apply proper casing to all name components
        first_name = self.proper_case_name(first_name)
        middle_name = self.proper_case_name(middle_name)
        last_name = self.proper_case_name(last_name)
        
        display_name = first_name
        
        if middle_name:
            # Get first character of middle name and add period
            middle_initial = middle_name[0].upper() + "."
            display_name += f" {middle_initial}"
        
        if last_name:
            display_name += f" {last_name}"
            
        return display_name

    def parse_full_name(self, full_name):
        """Parse full name into first, middle, and last names with proper casing"""
        name_parts = full_name.strip().split()
        
        if len(name_parts) == 0:
            return "", "", ""
        elif len(name_parts) == 1:
            return self.proper_case_name(name_parts[0]), "", ""
        elif len(name_parts) == 2:
            return (self.proper_case_name(name_parts[0]), 
                    "", 
                    self.proper_case_name(name_parts[1]))
        else:
            # First name, middle name(s), last name
            first_name = self.proper_case_name(name_parts[0])
            last_name = self.proper_case_name(name_parts[-1])
            middle_name = " ".join(name_parts[1:-1])
            middle_name = self.proper_case_name(middle_name)
            return first_name, middle_name, last_name

    def calculate_font_size(self, name):
        """Calculate adaptive font size based on name length"""
        name_length = len(name)
        
        if name_length <= 15:
            return 24
        elif name_length <= 20:
            return 20
        elif name_length <= 25:
            return 18
        elif name_length <= 30:
            return 16
        else:
            return 14

    def setup_profile_picture(self):
        """Setup profile picture with border and upload functionality"""
        def center_crop(img: Image.Image) -> Image.Image:
            w, h = img.size
            min_side = min(w, h)
            left = (w - min_side) // 2
            top = (h - min_side) // 2
            return img.crop((left, top, left + min_side, top + min_side))

        # Load default profile picture initially
        self.load_profile_picture()

        # Border (adjusted y from 263 to 123)
        border_size = 2
        x, y = 230, 123  # Adjusted for content area
        w, h = 140, 140
        self.canvas.create_rectangle(
            x - w/2 - border_size, y - h/2 - border_size,
            x + w/2 + border_size, y + h/2 + border_size,
            outline="#792D1B", width=border_size
        )
        self.image_profilepic_id = self.canvas.create_image(x, y, image=self.profile_pic)

        # Student Name display (adjusted y from 355 to 215) - CENTERED position
        display_name = self.format_display_name(
            self.user_data.get('first_name', ''),
            self.user_data.get('middle_name', ''),
            self.user_data.get('last_name', '')
        )
        # Calculate adaptive font size
        font_size = self.calculate_font_size(display_name)
        
        # Center position for name (x=230, y=215)
        self.name_display_id = self.canvas.create_text(
            230.0, 215.0, 
            anchor="center",  # Center anchor for proper centering
            text=display_name, 
            fill="#000000", 
            font=("Inter", font_size * -1), 
            tags="student_name"
        )

        # Name entry field background (always visible but entry field will be shown only during edit)
        try:
            entry_img_name = PhotoImage(file=relative_to_assets("entry_fullname.png"))
            self.entry_img_name = entry_img_name
            self.name_entry_bg = self.canvas.create_image(230.0, 220.0, image=entry_img_name, state="hidden")
        except Exception as e:
            print(f"Could not load name entry background: {e}")

        # Upload New Profile Button (adjusted y from 194 to 54)
        def upload_new_profile_pic():
            file_path = filedialog.askopenfilename(
                title="Select Profile Picture",
                filetypes=[
                    ("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff;*.tif"),
                    ("JPEG Files", "*.jpg;*.jpeg"),
                    ("PNG Files", "*.png"),
                    ("All Files", "*.*")
                ]
            )
            if file_path:
                try:
                    img = Image.open(file_path)
                    img = center_crop(img).resize((140, 140), Image.LANCZOS)
                    new_img = ImageTk.PhotoImage(img)
                    self.profile_pic = new_img
                    self.canvas.itemconfig(self.image_profilepic_id, image=new_img)
                    
                    # Store image data for database
                    with open(file_path, 'rb') as file:
                        self.profile_image_data = file.read()
                    
                    # Automatically save the profile picture to database
                    if self.save_profile_picture_to_db():
                        messagebox.showinfo("Success", "Profile picture updated successfully!")
                    else:
                        messagebox.showerror("Error", "Failed to save profile picture to database.")
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to load image: {e}")

        try:
            button_img_newpic = PhotoImage(file=relative_to_assets("button_newprofilepic.png"))
            self.button_img_newpic = button_img_newpic
            self.button_newprofilepic = Button(
                self.main_frame,
                image=button_img_newpic,
                borderwidth=0,
                highlightthickness=0,
                command=upload_new_profile_pic,
                relief="flat"
            )
            self.button_newprofilepic.place(x=273.0, y=54.0, width=26.0, height=26.0)
        except Exception as e:
            print(f"Could not load new profile pic button: {e}")

    def save_profile_picture_to_db(self):
        """Save profile picture to database immediately after upload"""
        try:
            if not self.get_db_connection:
                return False

            connection = self.get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE students 
                SET profile_picture = %s
                WHERE student_number = %s
            """, (
                self.profile_image_data,
                self.user_data.get('student_number', '')
            ))

            connection.commit()
            cursor.close()
            connection.close()
            return True

        except Error as e:
            print(f"Error saving profile picture to database: {e}")
            return False

    def load_profile_picture(self):
        """Load profile picture from database or use default"""
        # Try to load from database first
        if self.get_db_connection and self.user_data.get('student_number'):
            try:
                connection = self.get_db_connection()
                cursor = connection.cursor()
                
                cursor.execute("""
                    SELECT profile_picture FROM students WHERE student_number = %s
                """, (self.user_data['student_number'],))
                
                result = cursor.fetchone()
                if result and result[0]:
                    # Convert BLOB data to image
                    image_data = result[0]
                    image = Image.open(io.BytesIO(image_data))
                    image = image.resize((140, 140), Image.LANCZOS)
                    self.profile_pic = ImageTk.PhotoImage(image)
                    # Store the image data for future use
                    self.profile_image_data = image_data
                    cursor.close()
                    connection.close()
                    return
                
                cursor.close()
                connection.close()
            except Error as e:
                print(f"Error loading profile picture from database: {e}")
        
        # Load default profile picture if no image in database or error
        try:
            img = Image.open(relative_to_assets("image_profilepic.png"))
            img = img.resize((140, 140), Image.LANCZOS)
            self.profile_pic = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Could not load default profile picture: {e}")
            # Create a default blank image
            img = Image.new('RGB', (140, 140), color='#FFF1C2')
            self.profile_pic = ImageTk.PhotoImage(img)

    def setup_input_fields(self):
        """Setup all input fields with adjusted positions"""
        
        # ---------------- LEFT PANEL FIELDS ----------------
        
        # Student Number (adjusted y from 462 to 322)
        self.canvas.create_text(110.0, 322.0, anchor="nw", text="Student No.", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_studentno = PhotoImage(file=relative_to_assets("entry_studentno1.png"))
            self.entry_img_studentno = entry_img_studentno
            self.canvas.create_image(230.0, 377.0, image=entry_img_studentno)
        except Exception as e:
            print(f"Could not load student number entry background: {e}")
        
        self.entry_studentno = Entry(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                   relief="flat", bg="#FFF1C2", font=("Inter", 10))
        self.entry_studentno.place(x=117.0, y=359.0, width=224.0, height=38.0)

        # Email (adjusted y from 560 to 420)
        self.canvas.create_text(110.0, 420.0, anchor="nw", text="Email", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_email = PhotoImage(file=relative_to_assets("entry_email1.png"))
            self.entry_img_email = entry_img_email
            self.canvas.create_image(230.0, 475.0, image=entry_img_email)
        except Exception as e:
            print(f"Could not load email entry background: {e}")
        
        self.entry_email = Entry(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                               relief="flat", bg="#FFF1C2", font=("Inter", 10))
        self.entry_email.place(x=118.0, y=457.0, width=224.0, height=38.0)

        # ---------------- RIGHT PANEL FIELDS ----------------
        
        # Contact Number (adjusted y from 219 to 79)
        self.canvas.create_text(437.0, 79.0, anchor="nw", text="Contact No.", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_contact = PhotoImage(file=relative_to_assets("entry_contactno.png"))
            self.entry_img_contact = entry_img_contact
            self.canvas.create_image(557.0, 128.0, image=entry_img_contact)
        except Exception as e:
            print(f"Could not load contact number entry background: {e}")
        
        self.entry_contact = Entry(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                 relief="flat", bg="#FFF1C2", font=("Inter", 10))
        self.entry_contact.place(x=445.0, y=110.0, width=224.0, height=38.0)
        
        # Ensure the widget is properly initialized
        try:
            self.entry_contact.update_idletasks()
            self.entry_contact.winfo_exists()
        except Exception as e:
            print(f"Warning: entry_contact initialization issue: {e}")
            # Try to recreate it
            self.entry_contact.destroy()
            self.entry_contact = Entry(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                     relief="flat", bg="#FFF1C2", font=("Inter", 10))
            self.entry_contact.place(x=445.0, y=110.0, width=224.0, height=38.0)

        # Date of Birth (adjusted y from 219 to 79)
        self.canvas.create_text(698.0, 79.0, anchor="nw", text="Date Of Birth", 
                            fill="#1E1E1E", font=("Inter", 16 * -1))

        # Date components with proper entry backgrounds (adjusted y from 268 to 128)
        try:
            entry_img_dob_month = PhotoImage(file=relative_to_assets("entry_bdaymonth.png"))
            self.entry_img_dob_month = entry_img_dob_month
            self.canvas.create_image(740.0, 128.0, image=entry_img_dob_month)
        except Exception as e:
            print(f"Could not load DOB month entry background: {e}")

        self.dob_month = ttk.Combobox(self.main_frame, values=["January","February","March","April","May","June",
            "July","August","September","October","November","December"], 
            state="readonly", style="Custom.TCombobox", width=10)
        self.dob_month.place(x=706.0, y=110.0, width=75.0, height=38.0)

        try:
            entry_img_dob_day = PhotoImage(file=relative_to_assets("entry_bdayday.png"))
            self.entry_img_dob_day = entry_img_dob_day
            self.canvas.create_image(830.0, 128.0, image=entry_img_dob_day)
        except Exception as e:
            print(f"Could not load DOB day entry background: {e}")

        self.dob_day = ttk.Combobox(self.main_frame, values=[str(i) for i in range(1, 32)],
                                state="readonly", style="Custom.TCombobox", width=6)
        self.dob_day.place(x=805.0, y=110.0, width=65.0, height=38.0)

        try:
            entry_img_dob_year = PhotoImage(file=relative_to_assets("entry_bdayyear.png"))
            self.entry_img_dob_year = entry_img_dob_year
            self.canvas.create_image(923.0, 128.0, image=entry_img_dob_year)
        except Exception as e:
            print(f"Could not load DOB year entry background: {e}")

        current_year = datetime.datetime.now().year
        self.dob_year = ttk.Combobox(self.main_frame, values=[str(y) for y in range(current_year - 40, current_year + 1)],
                                    state="readonly", style="Custom.TCombobox", width=8)
        self.dob_year.place(x=900.0, y=110.0, width=64.0, height=38.0)

        # Gender (adjusted y from 219 to 79)
        self.canvas.create_text(998.0, 79.0, anchor="nw", text="Gender", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_gender = PhotoImage(file=relative_to_assets("entry_gender.png"))
            self.entry_img_gender = entry_img_gender
            self.canvas.create_image(1093.0, 128.0, image=entry_img_gender)
        except Exception as e:
            print(f"Could not load gender entry background: {e}")
        
        self.gender = ttk.Combobox(self.main_frame, values=["Male", "Female", "Other"],
                                  state="readonly", style="Custom.TCombobox")
        self.gender.place(x=998.0, y=110.0, width=195.0, height=38.0)

        # Address (adjusted y from 317 to 177)
        self.canvas.create_text(437.0, 177.0, anchor="nw", text="Address", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_address = PhotoImage(file=relative_to_assets("entry_address.png"))
            self.entry_img_address = entry_img_address
            self.canvas.create_image(818.0, 229.0, image=entry_img_address)
        except Exception as e:
            print(f"Could not load address entry background: {e}")
        
        self.entry_address = Entry(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                 relief="flat", bg="#FFF1C2", font=("Inter", 10))
        self.entry_address.place(x=445.0, y=207.0, width=746.0, height=38.0)

        # Course (adjusted y from 428 to 288)
        self.canvas.create_text(437.0, 288.0, anchor="nw", text="Course", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_course = PhotoImage(file=relative_to_assets("entry_course.png"))
            self.entry_img_course = entry_img_course
            self.canvas.create_image(557.0, 337.0, image=entry_img_course)
        except Exception as e:
            print(f"Could not load course entry background: {e}")
        
        self.course = ttk.Combobox(self.main_frame, values=[
            "Bachelor of Science in Information Technology", "Bachelor of Science in Computer Science",
            "Bachelor of Early Childhood Education", "Bachelor of Technology and Livelihood Education",
            "Bachelor of Science in Office Administration", "Bachelor of Science in Tourism Management",
            "Bachelor of Science in Hospitality Management"], state="readonly", style="Custom.TCombobox")
        self.course.place(x=445.0, y=319.0, width=230.0, height=38.0)

        # Year Level (adjusted y from 428 to 288)
        self.canvas.create_text(698.0, 288.0, anchor="nw", text="Year Level", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        
        try:
            entry_img_yearlevel = PhotoImage(file=relative_to_assets("entry_yrlevel.png"))
            self.entry_img_yearlevel = entry_img_yearlevel
            self.canvas.create_image(818.0, 337.0, image=entry_img_yearlevel)
        except Exception as e:
            print(f"Could not load year level entry background: {e}")
        
        self.year_level = ttk.Combobox(self.main_frame, values=["1st Year", "2nd Year", "3rd Year", "4th Year"],
                                      state="readonly", style="Custom.TCombobox")
        self.year_level.place(x=706.0, y=319.0, width=230.0, height=38.0)

        # Enrollment Status (adjusted y from 429 to 289)
        self.canvas.create_text(959.0, 289.0, anchor="nw", text="Enrollment Status", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        
        try:
            entry_img_enrollment = PhotoImage(file=relative_to_assets("entry_enrollmentstatus.png"))
            self.entry_img_enrollment = entry_img_enrollment
            self.canvas.create_image(1079.0, 337.0, image=entry_img_enrollment)
        except Exception as e:
            print(f"Could not load enrollment status entry background: {e}")
        
        self.enrollment_status = ttk.Combobox(self.main_frame, values=["Enrolled", "Inactive", "Graduated", "Transferred"],
                                            state="readonly", style="Custom.TCombobox")
        self.enrollment_status.place(x=967.0, y=319.0, width=230.0, height=38.0)

        # Clearance & Obligations (adjusted y from 529 to 389)
        self.canvas.create_text(437.0, 389.0, anchor="nw", text="CLEARANCE & OBLIGATIONS", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_obligations = PhotoImage(file=relative_to_assets("entry_obligations.png"))
            self.entry_img_obligations = entry_img_obligations
            self.canvas.create_image(818.0, 500.0, image=entry_img_obligations)
        except Exception as e:
            print(f"Could not load obligations entry background: {e}")
        
        self.entry_obligations = Text(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                    relief="flat", bg="#FFF1C2", font=("Inter", 10),
                                    wrap="word")
        self.entry_obligations.place(x=445.0, y=424.0, width=746.0, height=153.0)
        # Set obligations to permanently readonly
        self.entry_obligations.config(state="disabled")

    def setup_buttons(self):
        """Setup edit/save button (adjusted y from 667 to 527)"""
        try:
            button_edit_img = PhotoImage(file=relative_to_assets("button_edit.png"))
            button_save_img = PhotoImage(file=relative_to_assets("button_save.png"))
            
            self.button_edit_img = button_edit_img
            self.button_save_img = button_save_img
            
            self.button_save = Button(
                self.main_frame,
                image=button_edit_img,
                borderwidth=0,
                highlightthickness=0,
                command=self.toggle_edit_save,
                relief="flat"
            )
            self.button_save.place(x=110.0, y=527.0, width=240.0, height=40.0)
            
        except Exception as e:
            print(f"Could not load button images: {e}")
            # Fallback text button
            self.button_save = Button(
                self.main_frame,
                text="Edit Profile",
                font=("Inter", 12, "bold"),
                bg="#792D1B",
                fg="#FFFFFF",
                command=self.toggle_edit_save,
                relief="flat"
            )
            self.button_save.place(x=110.0, y=527.0, width=240.0, height=40.0)

    def toggle_edit_save(self):
        """Toggle between edit and save modes"""
        if not self.is_edit_mode:
            # Switch to edit mode
            self.set_fields_editable(True)
            if hasattr(self, 'button_save_img'):
                self.button_save.config(image=self.button_save_img)
            else:
                self.button_save.config(text="Save Profile")
            self.is_edit_mode = True
        else:
            # Save and switch back to view mode
            if self.save_data():
                messagebox.showinfo("Success", "Profile updated successfully!")
                self.set_fields_editable(False)
                if hasattr(self, 'button_edit_img'):
                    self.button_save.config(image=self.button_edit_img)
                else:
                    self.button_save.config(text="Edit Profile")
                self.is_edit_mode = False

    def set_fields_editable(self, editable):
        """Set all fields to editable or readonly"""
        state = "normal" if editable else "readonly"
        combo_state = "readonly" if editable else "disabled"
        
        # Show/hide name field based on edit mode
        if editable:
            # Hide the name display text and show the entry field
            self.canvas.itemconfig(self.name_display_id, state="hidden")
            self.canvas.itemconfig(self.name_entry_bg, state="normal")
            
            # Create the entry field only when needed (during edit mode)
            if self.entry_fullname is None:
                self.entry_fullname = Entry(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                          relief="flat", bg="#FFF1C2", font=("Inter", 14),
                                          justify="center")
                # Populate with full name for editing
                full_name = self.get_full_name_for_editing()
                self.entry_fullname.delete(0, 'end')
                self.entry_fullname.insert(0, full_name)
            
            # Center the entry field in the same position as the display name
            self.entry_fullname.place(x=120.0, y=202.0, width=220.0, height=38.0)
        else:
            # Hide the entry field and show the name display text
            if self.entry_fullname is not None:
                self.entry_fullname.place_forget()
                # Destroy the entry widget to completely remove it
                self.entry_fullname.destroy()
                self.entry_fullname = None
            
            self.canvas.itemconfig(self.name_display_id, state="normal")
            self.canvas.itemconfig(self.name_entry_bg, state="hidden")
        
        # Entry fields - with safety checks
        entry_fields = []
        if hasattr(self, 'entry_studentno') and self.entry_studentno:
            entry_fields.append(self.entry_studentno)
        if hasattr(self, 'entry_email') and self.entry_email:
            entry_fields.append(self.entry_email)
        if hasattr(self, 'entry_contact') and self.entry_contact:
            entry_fields.append(self.entry_contact)
        if hasattr(self, 'entry_address') and self.entry_address:
            entry_fields.append(self.entry_address)
        
        for entry in entry_fields:
            try:
                if editable:
                    entry.config(state="normal", bg="#FFF1C2")
                else:
                    entry.config(state="readonly", readonlybackground="#FFF1C2")
            except Exception as e:
                print(f"Error setting entry field state: {e}")
        
        # Obligations field remains permanently disabled (readonly)
        # No need to change its state
        
        # Combobox fields - with safety checks
        combo_fields = []
        if hasattr(self, 'dob_month') and self.dob_month:
            combo_fields.append(self.dob_month)
        if hasattr(self, 'dob_day') and self.dob_day:
            combo_fields.append(self.dob_day)
        if hasattr(self, 'dob_year') and self.dob_year:
            combo_fields.append(self.dob_year)
        if hasattr(self, 'gender') and self.gender:
            combo_fields.append(self.gender)
        if hasattr(self, 'course') and self.course:
            combo_fields.append(self.course)
        if hasattr(self, 'year_level') and self.year_level:
            combo_fields.append(self.year_level)
        if hasattr(self, 'enrollment_status') and self.enrollment_status:
            combo_fields.append(self.enrollment_status)
        
        for combo in combo_fields:
            try:
                combo.config(state=combo_state)
            except Exception as e:
                print(f"Error setting combo field state: {e}")

    def get_full_name_for_editing(self):
        """Get full name in format for editing: Firstname Middlename Lastname"""
        first_name = self.user_data.get('first_name', '')
        middle_name = self.user_data.get('middle_name', '')
        last_name = self.user_data.get('last_name', '')
        
        name_parts = []
        if first_name:
            name_parts.append(first_name)
        if middle_name:
            name_parts.append(middle_name)
        if last_name:
            name_parts.append(last_name)
            
        return " ".join(name_parts)

    def load_user_data(self):
        """Load user data from database into the form fields"""
        if not self.get_db_connection:
            self.load_default_data()
            return

        try:
            connection = self.get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Get student data with user email
            cursor.execute("""
                SELECT s.*, u.email 
                FROM students s 
                JOIN users u ON s.user_id = u.user_id 
                WHERE s.student_number = %s
            """, (self.user_data.get('student_number'),))
            
            student_data = cursor.fetchone()
            
            if student_data:
                self.user_data.update(student_data)
                self.populate_form_fields()
            else:
                messagebox.showwarning("Warning", "Student data not found in database.")
                self.load_default_data()
            
            cursor.close()
            connection.close()
            
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to load user data: {e}")
            self.load_default_data()

    def load_default_data(self):
        """Load default data when database is not available"""
        self.populate_form_fields()

    def validate_and_fix_combobox_widgets(self):
        """Validate and fix Combobox widgets if they're in invalid state"""
        comboboxes = [
            ('dob_month', self.dob_month),
            ('dob_day', self.dob_day), 
            ('dob_year', self.dob_year),
            ('gender', self.gender),
            ('course', self.course),
            ('year_level', self.year_level),
            ('enrollment_status', self.enrollment_status)
        ]
        
        for name, widget in comboboxes:
            try:
                if hasattr(self, name) and widget:
                    # Test if widget is working
                    widget.winfo_exists()
            except Exception as e:
                print(f"Combobox {name} validation failed: {e}")
                # Try to recreate the widget
                self.recreate_combobox(name)
    
    def recreate_combobox(self, name):
        """Recreate a specific combobox widget if it's corrupted"""
        try:
            # Destroy the old widget if it exists
            if hasattr(self, name):
                old_widget = getattr(self, name)
                if old_widget:
                    old_widget.destroy()
            
            # Recreate based on the widget type
            if name == 'gender':
                self.gender = ttk.Combobox(self.main_frame, values=["Male", "Female", "Other"],
                                      state="readonly", style="Custom.TCombobox")
                self.gender.place(x=998.0, y=110.0, width=195.0, height=38.0)
            elif name == 'course':
                self.course = ttk.Combobox(self.main_frame, values=[
                    "Bachelor of Science in Information Technology", "Bachelor of Science in Computer Science",
                    "Bachelor of Early Childhood Education", "Bachelor of Technology and Livelihood Education",
                    "Bachelor of Science in Office Administration", "Bachelor of Science in Tourism Management",
                    "Bachelor of Science in Hospitality Management"], state="readonly", style="Custom.TCombobox")
                self.course.place(x=445.0, y=319.0, width=230.0, height=38.0)
            elif name == 'year_level':
                self.year_level = ttk.Combobox(self.main_frame, values=["1st Year", "2nd Year", "3rd Year", "4th Year"],
                                          state="readonly", style="Custom.TCombobox")
                self.year_level.place(x=706.0, y=319.0, width=230.0, height=38.0)
            elif name == 'enrollment_status':
                self.enrollment_status = ttk.Combobox(self.main_frame, values=["Enrolled", "Inactive", "Graduated", "Transferred"],
                                                state="readonly", style="Custom.TCombobox")
                self.enrollment_status.place(x=967.0, y=319.0, width=230.0, height=38.0)
            
            print(f"✅ Recreated {name} combobox widget")
        except Exception as e:
            print(f"Error recreating {name} combobox: {e}")

    def validate_and_fix_entry_widgets(self):
        """Validate and fix Entry widgets if they're in invalid state"""
        try:
            # Test if entry_contact is working properly
            if hasattr(self, 'entry_contact') and self.entry_contact:
                # Try a simple operation to test the widget
                self.entry_contact.winfo_exists()
        except Exception as e:
            print(f"Entry widget validation failed: {e}")
            # Recreate the problematic entry widget
            self.recreate_entry_contact()
    
    def recreate_entry_contact(self):
        """Recreate the entry_contact widget if it's corrupted"""
        try:
            # Destroy the old widget if it exists
            if hasattr(self, 'entry_contact') and self.entry_contact:
                self.entry_contact.destroy()
            
            # Create a new entry_contact widget
            self.entry_contact = Entry(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                     relief="flat", bg="#FFF1C2", font=("Inter", 10))
            self.entry_contact.place(x=445.0, y=110.0, width=224.0, height=38.0)
            print("✅ Recreated entry_contact widget")
        except Exception as e:
            print(f"Error recreating entry_contact: {e}")

    def populate_form_fields(self):
        """Populate form fields with user data"""
        # Validate and fix entry widgets first
        self.validate_and_fix_entry_widgets()
        
        # Validate and fix combobox widgets
        self.validate_and_fix_combobox_widgets()
        
        # Clear any existing data first
        self.clear_fields()
        
        # Student info - with comprehensive safety checks
        try:
            if hasattr(self, 'entry_studentno') and self.entry_studentno:
                self.entry_studentno.insert(0, self.user_data.get('student_number', ''))
        except Exception as e:
            print(f"Error populating student number: {e}")
        
        try:
            if hasattr(self, 'entry_email') and self.entry_email:
                self.entry_email.insert(0, self.user_data.get('email', ''))
        except Exception as e:
            print(f"Error populating email: {e}")
        
        try:
            if hasattr(self, 'entry_contact') and self.entry_contact:
                # Use a safer method to insert text
                contact_value = self.user_data.get('contact_number', '')
                if contact_value:
                    # Clear first, then insert
                    self.entry_contact.delete(0, 'end')
                    self.entry_contact.insert(0, contact_value)
        except Exception as e:
            print(f"Error populating contact number: {e}")
            # Try alternative method
            try:
                if hasattr(self, 'entry_contact') and self.entry_contact:
                    contact_value = self.user_data.get('contact_number', '')
                    # Create a StringVar for the entry
                    from tkinter import StringVar
                    contact_var = StringVar(value=contact_value)
                    self.entry_contact.config(textvariable=contact_var)
            except Exception as e2:
                print(f"Alternative method also failed: {e2}")
        
        try:
            if hasattr(self, 'entry_address') and self.entry_address:
                self.entry_address.insert(0, self.user_data.get('address', ''))
        except Exception as e:
            print(f"Error populating address: {e}")
        
        # Date of birth - with comprehensive safety checks
        birth_date = self.user_data.get('birth_date')
        if birth_date:
            try:
                if hasattr(birth_date, 'strftime'):
                    # It's a datetime object
                    try:
                        if hasattr(self, 'dob_month') and self.dob_month:
                            self.dob_month.set(birth_date.strftime('%B'))
                    except Exception as e:
                        print(f"Error setting DOB month: {e}")
                    
                    try:
                        if hasattr(self, 'dob_day') and self.dob_day:
                            self.dob_day.set(str(birth_date.day))
                    except Exception as e:
                        print(f"Error setting DOB day: {e}")
                    
                    try:
                        if hasattr(self, 'dob_year') and self.dob_year:
                            self.dob_year.set(str(birth_date.year))
                    except Exception as e:
                        print(f"Error setting DOB year: {e}")
                else:
                    # It's a string, try to parse
                    try:
                        date_obj = datetime.datetime.strptime(str(birth_date), '%Y-%m-%d')
                        try:
                            if hasattr(self, 'dob_month') and self.dob_month:
                                self.dob_month.set(date_obj.strftime('%B'))
                        except Exception as e:
                            print(f"Error setting DOB month from string: {e}")
                        
                        try:
                            if hasattr(self, 'dob_day') and self.dob_day:
                                self.dob_day.set(str(date_obj.day))
                        except Exception as e:
                            print(f"Error setting DOB day from string: {e}")
                        
                        try:
                            if hasattr(self, 'dob_year') and self.dob_year:
                                self.dob_year.set(str(date_obj.year))
                        except Exception as e:
                            print(f"Error setting DOB year from string: {e}")
                    except Exception as e:
                        print(f"Error parsing birth date: {e}")
            except Exception as e:
                print(f"Error processing birth date: {e}")
        
        # Other fields - with comprehensive safety checks
        try:
            if hasattr(self, 'gender') and self.gender:
                gender_value = self.user_data.get('gender', '')
                if gender_value:
                    self.gender.set(gender_value)
        except Exception as e:
            print(f"Error setting gender: {e}")
        
        try:
            if hasattr(self, 'course') and self.course:
                course_value = self.user_data.get('course', '')
                if course_value:
                    self.course.set(course_value)
        except Exception as e:
            print(f"Error setting course: {e}")
        
        try:
            if hasattr(self, 'year_level') and self.year_level:
                year_value = self.user_data.get('year_level', '')
                if year_value:
                    self.year_level.set(year_value)
        except Exception as e:
            print(f"Error setting year level: {e}")
        
        try:
            if hasattr(self, 'enrollment_status') and self.enrollment_status:
                status_value = self.user_data.get('enrollment_status', '')
                if status_value:
                    self.enrollment_status.set(status_value)
        except Exception as e:
            print(f"Error setting enrollment status: {e}")
        
        # Obligations - always readonly - with safety checks
        obligations_text = "No outstanding obligations."
        if self.user_data.get('has_obligations'):
            obligations_text = self.user_data.get('obligations_details', 'Has obligations. Please contact registrar.')
        
        # Temporarily enable to insert text, then disable again
        if hasattr(self, 'entry_obligations') and self.entry_obligations:
            try:
                self.entry_obligations.config(state="normal")
                self.entry_obligations.delete('1.0', 'end')
                self.entry_obligations.insert("1.0", obligations_text)
                self.entry_obligations.config(state="disabled")
            except Exception as e:
                print(f"Error setting obligations text: {e}")
        
        # Update name display
        self.update_name_display()
        
        # Set all fields to readonly initially (except obligations which is permanently readonly)
        self.set_fields_editable(False)

    def save_data(self):
        """Save the form data to database"""
        try:
            if not self.get_db_connection:
                return self.save_to_memory()

            connection = self.get_db_connection()
            cursor = connection.cursor()

            # Parse full name from the entry field with proper casing
            full_name = self.entry_fullname.get().strip()
            first_name, middle_name, last_name = self.parse_full_name(full_name)

            # Parse date of birth
            birth_date = None
            if self.dob_month.get() and self.dob_day.get() and self.dob_year.get():
                try:
                    month_num = datetime.datetime.strptime(self.dob_month.get(), '%B').month
                    birth_date = f"{self.dob_year.get()}-{month_num:02d}-{int(self.dob_day.get()):02d}"
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid date of birth")

            # Update student record (excluding profile_picture since it's saved separately)
            cursor.execute("""
                UPDATE students 
                SET first_name = %s,
                    middle_name = %s,
                    last_name = %s,
                    contact_number = %s,
                    address = %s,
                    birth_date = %s,
                    gender = %s,
                    course = %s,
                    year_level = %s,
                    enrollment_status = %s
                WHERE student_number = %s
            """, (
                first_name,
                middle_name,
                last_name,
                self.entry_contact.get(),
                self.entry_address.get(),
                birth_date,
                self.gender.get(),
                self.course.get(),
                self.year_level.get(),
                self.enrollment_status.get(),
                self.user_data['student_number']
            ))

            # Update user email if changed
            if self.entry_email.get() != self.user_data.get('email'):
                cursor.execute("""
                    UPDATE users 
                    SET email = %s 
                    WHERE user_id = (SELECT user_id FROM students WHERE student_number = %s)
                """, (self.entry_email.get(), self.user_data['student_number']))

            connection.commit()
            cursor.close()
            connection.close()

            # Update local user data
            self.user_data.update({
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'email': self.entry_email.get(),
                'contact_number': self.entry_contact.get(),
                'address': self.entry_address.get(),
                'birth_date': birth_date,
                'gender': self.gender.get(),
                'course': self.course.get(),
                'year_level': self.year_level.get(),
                'enrollment_status': self.enrollment_status.get()
            })

            self.update_name_display()
            return True

        except Error as e:
            messagebox.showerror("Database Error", f"Failed to save data: {e}")
            return False

    def save_to_memory(self):
        """Save data to memory when database is not available"""
        try:
            # Parse full name from the entry field with proper casing
            full_name = self.entry_fullname.get().strip()
            first_name, middle_name, last_name = self.parse_full_name(full_name)

            # Parse date of birth
            birth_date = None
            if self.dob_month.get() and self.dob_day.get() and self.dob_year.get():
                try:
                    month_num = datetime.datetime.strptime(self.dob_month.get(), '%B').month
                    birth_date = f"{self.dob_year.get()}-{month_num:02d}-{int(self.dob_day.get()):02d}"
                except ValueError:
                    pass

            # Update user data
            self.user_data.update({
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'student_number': self.entry_studentno.get(),
                'email': self.entry_email.get(),
                'contact_number': self.entry_contact.get(),
                'address': self.entry_address.get(),
                'birth_date': birth_date,
                'gender': self.gender.get(),
                'course': self.course.get(),
                'year_level': self.year_level.get(),
                'enrollment_status': self.enrollment_status.get()
            })

            self.update_name_display()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")
            return False

    def update_name_display(self):
        """Update the name display on the profile with adaptive font size"""
        display_name = self.format_display_name(
            self.user_data.get('first_name', ''),
            self.user_data.get('middle_name', ''),
            self.user_data.get('last_name', '')
        )
        
        # Calculate adaptive font size based on name length
        font_size = self.calculate_font_size(display_name)
        
        # Update the canvas text with new font size while keeping it centered
        self.canvas.itemconfig(self.name_display_id, text=display_name, font=("Inter", font_size * -1))

    def refresh_data(self):
        """Refresh data from database"""
        # Reload profile picture from database
        self.load_profile_picture()
        self.canvas.itemconfig(self.image_profilepic_id, image=self.profile_pic)
        
        # Reload other data
        self.load_user_data()

    def clear_fields(self):
        """Clear all form fields"""
        # Clear entry fields with safety checks
        entry_fields = []
        if hasattr(self, 'entry_studentno') and self.entry_studentno:
            entry_fields.append(self.entry_studentno)
        if hasattr(self, 'entry_email') and self.entry_email:
            entry_fields.append(self.entry_email)
        if hasattr(self, 'entry_contact') and self.entry_contact:
            entry_fields.append(self.entry_contact)
        if hasattr(self, 'entry_address') and self.entry_address:
            entry_fields.append(self.entry_address)
        
        for entry in entry_fields:
            try:
                entry.delete(0, 'end')
            except Exception as e:
                print(f"Error clearing entry field: {e}")
        
        # Only clear the name entry if it exists
        if hasattr(self, 'entry_fullname') and self.entry_fullname is not None:
            try:
                self.entry_fullname.delete(0, 'end')
            except Exception as e:
                print(f"Error clearing name entry: {e}")
        
        # Clear combobox fields with safety checks
        combo_fields = []
        if hasattr(self, 'dob_month') and self.dob_month:
            combo_fields.append(self.dob_month)
        if hasattr(self, 'dob_day') and self.dob_day:
            combo_fields.append(self.dob_day)
        if hasattr(self, 'dob_year') and self.dob_year:
            combo_fields.append(self.dob_year)
        if hasattr(self, 'gender') and self.gender:
            combo_fields.append(self.gender)
        if hasattr(self, 'course') and self.course:
            combo_fields.append(self.course)
        if hasattr(self, 'year_level') and self.year_level:
            combo_fields.append(self.year_level)
        if hasattr(self, 'enrollment_status') and self.enrollment_status:
            combo_fields.append(self.enrollment_status)
        
        for combo in combo_fields:
            try:
                combo.set('')
            except Exception as e:
                print(f"Error clearing combo field: {e}")
        
        # Clear obligations (temporarily enable to clear, then disable)
        if hasattr(self, 'entry_obligations') and self.entry_obligations:
            try:
                self.entry_obligations.config(state="normal")
                self.entry_obligations.delete('1.0', 'end')
                self.entry_obligations.config(state="disabled")
            except Exception as e:
                print(f"Error clearing obligations field: {e}")

    def destroy(self):
        """Clean up when window is closed"""
        try:
            self.main_frame.destroy()
        except:
            pass
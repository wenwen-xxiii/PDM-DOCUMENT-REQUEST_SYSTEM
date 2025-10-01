from pathlib import Path
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox
from tkinter import ttk, filedialog, Frame, Label
from PIL import Image, ImageTk
import datetime
import os, sys

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

    def setup_profile_picture(self):
        """Setup profile picture with border and upload functionality"""
        def center_crop(img: Image.Image) -> Image.Image:
            w, h = img.size
            min_side = min(w, h)
            left = (w - min_side) // 2
            top = (h - min_side) // 2
            return img.crop((left, top, left + min_side, top + min_side))

        # Load default profile picture
        try:
            img = Image.open(relative_to_assets("image_profilepic.png"))
            img = img.resize((140, 140), Image.LANCZOS)
            self.profile_pic = ImageTk.PhotoImage(img)
        except:
            # Create a default blank image
            img = Image.new('RGB', (140, 140), color='#FFF1C2')
            self.profile_pic = ImageTk.PhotoImage(img)

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

        # Student Name (adjusted y from 355 to 215)
        student_name = f"{self.user_data.get('first_name', '')} {self.user_data.get('last_name', '')}"
        self.canvas.create_text(144.0, 215.0, anchor="nw", text=student_name, 
                               fill="#000000", font=("Inter", 24 * -1))

        # Upload New Profile Button (adjusted y from 194 to 54)
        def upload_new_profile_pic():
            file_path = filedialog.askopenfilename(
                title="Select Profile Picture",
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
            )
            if file_path:
                try:
                    img = Image.open(file_path)
                    img = center_crop(img).resize((140, 140), Image.LANCZOS)
                    new_img = ImageTk.PhotoImage(img)
                    self.profile_pic = new_img
                    self.canvas.itemconfig(self.image_profilepic_id, image=new_img)
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
        except:
            pass
        
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
        except:
            pass
        
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
        except:
            pass
        
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
        except:
            pass

        self.dob_month = ttk.Combobox(self.main_frame, values=["January","February","March","April","May","June",
            "July","August","September","October","November","December"], 
            state="readonly", style="Custom.TCombobox", width=10)
        self.dob_month.place(x=706.0, y=110.0, width=75.0, height=38.0)

        try:
            entry_img_dob_day = PhotoImage(file=relative_to_assets("entry_bdayday.png"))
            self.entry_img_dob_day = entry_img_dob_day
            self.canvas.create_image(830.0, 128.0, image=entry_img_dob_day)
        except:
            pass

        self.dob_day = ttk.Combobox(self.main_frame, values=[str(i) for i in range(1, 32)],
                                state="readonly", style="Custom.TCombobox", width=6)
        self.dob_day.place(x=795.0, y=110.0, width=75.0, height=38.0)

        try:
            entry_img_dob_year = PhotoImage(file=relative_to_assets("entry_bdayyear.png"))
            self.entry_img_dob_year = entry_img_dob_year
            self.canvas.create_image(923.0, 128.0, image=entry_img_dob_year)
        except:
            pass

        current_year = datetime.datetime.now().year
        self.dob_year = ttk.Combobox(self.main_frame, values=[str(y) for y in range(current_year - 40, current_year + 1)],
                                    state="readonly", style="Custom.TCombobox", width=8)
        self.dob_year.place(x=910.0, y=110.0, width=54.0, height=38.0)

        # Gender (adjusted y from 219 to 79)
        self.canvas.create_text(998.0, 79.0, anchor="nw", text="Gender", 
                               fill="#1E1E1E", font=("Inter", 16 * -1))
        try:
            entry_img_gender = PhotoImage(file=relative_to_assets("entry_gender.png"))
            self.entry_img_gender = entry_img_gender
            self.canvas.create_image(1093.0, 128.0, image=entry_img_gender)
        except:
            pass
        
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
        except:
            pass
        
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
        except:
            pass
        
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
        except:
            pass
        
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
        except:
            pass
        
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
        except:
            pass
        
        self.entry_obligations = Text(self.main_frame, bd=0, fg="#000716", highlightthickness=0, 
                                    relief="flat", bg="#FFF1C2", font=("Inter", 10),
                                    wrap="word")
        self.entry_obligations.place(x=445.0, y=424.0, width=746.0, height=153.0)

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
        text_state = "normal" if editable else "disabled"
        combo_state = "readonly" if editable else "disabled"
        
        # Entry fields
        for entry in [self.entry_studentno, self.entry_email, self.entry_contact, self.entry_address]:
            if editable:
                entry.config(state="normal", bg="#FFF1C2")
            else:
                entry.config(state="readonly", readonlybackground="#FFF1C2")
        
        # Text field
        self.entry_obligations.config(state=text_state)
        
        # Combobox fields
        for combo in [self.dob_month, self.dob_day, self.dob_year, self.gender, 
                     self.course, self.year_level, self.enrollment_status]:
            combo.config(state=combo_state)

    def load_user_data(self):
        """Load user data into the form fields"""
        # Clear any existing data first
        self.clear_fields()
        
        # Student info
        self.entry_studentno.insert(0, self.user_data.get('student_number', ''))
        self.entry_email.insert(0, self.user_data.get('email', ''))
        self.entry_contact.insert(0, self.user_data.get('contact_number', ''))
        self.entry_address.insert(0, self.user_data.get('address', ''))
        
        # Date of birth
        birth_date = self.user_data.get('birth_date')
        if birth_date:
            if hasattr(birth_date, 'strftime'):
                # It's a datetime object
                self.dob_month.set(birth_date.strftime('%B'))
                self.dob_day.set(str(birth_date.day))
                self.dob_year.set(str(birth_date.year))
            else:
                # It's a string, try to parse
                try:
                    date_obj = datetime.datetime.strptime(str(birth_date), '%Y-%m-%d')
                    self.dob_month.set(date_obj.strftime('%B'))
                    self.dob_day.set(str(date_obj.day))
                    self.dob_year.set(str(date_obj.year))
                except:
                    pass
        
        # Other fields
        self.gender.set(self.user_data.get('gender', ''))
        self.course.set(self.user_data.get('course', ''))
        self.year_level.set(self.user_data.get('year_level', ''))
        self.enrollment_status.set(self.user_data.get('enrollment_status', ''))
        
        # Obligations
        obligations_text = "No outstanding obligations."
        if self.user_data.get('has_obligations'):
            obligations_text = self.user_data.get('obligations_details', 'Has obligations. Please contact registrar.')
        self.entry_obligations.insert("1.0", obligations_text)
        
        # Set all fields to readonly initially
        self.set_fields_editable(False)

    def save_data(self):
        """Save the form data"""
        try:
            # Here you would save to database
            # For now, just update the user_data dictionary
            self.user_data.update({
                'student_number': self.entry_studentno.get(),
                'email': self.entry_email.get(),
                'contact_number': self.entry_contact.get(),
                'address': self.entry_address.get(),
                'gender': self.gender.get(),
                'course': self.course.get(),
                'year_level': self.year_level.get(),
                'enrollment_status': self.enrollment_status.get(),
                'obligations_details': self.entry_obligations.get("1.0", "end-1c")
            })
            
            # Update name display
            self.canvas.delete("student_name")
            student_name = f"{self.user_data.get('first_name', '')} {self.user_data.get('last_name', '')}"
            self.canvas.create_text(144.0, 215.0, anchor="nw", text=student_name, 
                                   fill="#000000", font=("Inter", 24 * -1), tags="student_name")
            
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")
            return False

    def refresh_data(self):
        """Refresh data from database"""
        if self.get_db_connection:
            try:
                connection = self.get_db_connection()
                cursor = connection.cursor(dictionary=True)
                
                if self.user_type == 'student':
                    cursor.execute("""
                        SELECT s.*, u.email 
                        FROM students s 
                        JOIN users u ON s.user_id = u.id 
                        WHERE s.student_number = %s
                    """, (self.user_data['student_number'],))
                    user_data = cursor.fetchone()
                    
                    if user_data:
                        self.user_data.update(user_data)
                        # Clear all fields and reload
                        self.clear_fields()
                        self.load_user_data()
                
                cursor.close()
                connection.close()
                
            except Exception as e:
                print(f"Error refreshing data: {e}")

    def clear_fields(self):
        """Clear all form fields"""
        for entry in [self.entry_studentno, self.entry_email, self.entry_contact, self.entry_address]:
            entry.delete(0, 'end')
        
        for combo in [self.dob_month, self.dob_day, self.dob_year, self.gender, 
                     self.course, self.year_level, self.enrollment_status]:
            combo.set('')
        
        self.entry_obligations.delete('1.0', 'end')

    def destroy(self):
        """Clean up when window is closed"""
        try:
            self.main_frame.destroy()
        except:
            pass
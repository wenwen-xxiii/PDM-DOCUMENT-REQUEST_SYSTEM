from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, messagebox
import time
import sys
import os

OUTPUT_PATH = Path(__file__).parent

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def relative_to_assets(path: str) -> Path:
    return Path(resource_path(f"resources/assets/frame4/{path}"))


class OTPVerificationWindow:
    def __init__(self, parent, user_data, otp_code, verification_callback, back_callback, get_db_connection):
        self.parent = parent
        self.user_data = user_data
        self.otp_code = otp_code
        self.verification_callback = verification_callback
        self.back_callback = back_callback
        self.get_db_connection = get_db_connection
        self.otp_entries = []
        self.otp_expiry_time = time.time() + 600  # 10 minutes
        
        self.setup_ui()
        self.start_otp_timer()
        
    def setup_ui(self):
        self.canvas = Canvas(
            self.parent,
            bg="#FFFFFF",
            height=400,
            width=670,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        
        # Background and design elements
        self.canvas.create_rectangle(0.0, 0.0, 670.0, 400.0, fill="#FFA500", outline="")
        self.canvas.create_rectangle(0.0, 0.0, 335.0, 400.0, fill="#800000", outline="")
        
        self.canvas.create_text(
            51.0, 293.0, anchor="nw",
            text="Where quality education is a right, not privilege.",
            fill="#FFFFFF", font=("Inter Italic", 10 * -1)
        )
        
        self.canvas.create_text(
            41.0, 263.0, anchor="nw",
            text="PAMBAYANG DALUBHASAAN NG MARILAO",
            fill="#FFD700", font=("Inter Bold", 12 * -1)
        )

        # Logo
        self.image_image_1 = PhotoImage(file=relative_to_assets("image_logo.png"))
        self.canvas.create_image(164.0, 171.0, image=self.image_image_1)

        self.canvas.create_text(
            378.0, 102.0, anchor="nw",
            text="OTP Verification",
            fill="#FFFFFF", font=("Inter Bold", 32 * -1)
        )

        # Verify button
        self.button_image_1 = PhotoImage(file=relative_to_assets("button_verify.png"))
        self.button_verify = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.verify_otp,
            relief="flat"
        )
        self.button_verify.place(x=373.0, y=283.0, width=265.0, height=40.0)

        # Resend OTP button
        self.button_image_2 = PhotoImage(file=relative_to_assets("buttonLbl_resendotp.png"))
        self.buttonLbl_resendotp = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.resend_otp,
            relief="flat"
        )
        self.buttonLbl_resendotp.place(x=400.0, y=347.0, width=212.0, height=18.0)

        # Email icon
        self.image_image_2 = PhotoImage(file=relative_to_assets("image_otpmail.png"))
        self.canvas.create_image(505.0, 82.0, image=self.image_image_2)

        # OTP entry fields
        self.setup_otp_entries()

        # Email display text
        self.email_text = self.canvas.create_text(
            383.0, 154.0, anchor="nw",
            text=f"A verification code was sent to:\n{self.user_data['email']}",
            fill="#FFFFFF", font=("Inter Bold", 16 * -1)
        )

        # Back button
        self.button_image_3 = PhotoImage(file=relative_to_assets("button_back.png"))
        self.button_back = Button(
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.go_back,
            relief="flat"
        )
        self.button_back.place(x=624.0, y=16.0, width=30.0, height=30.0)

    def setup_otp_entries(self):
        """Setup the 6 OTP entry fields with proper alignment"""
        # Adjusted positions for better alignment
        entry_positions = [
            (393.0, 237.0), (438.0, 237.0), (483.0, 237.0),
            (528.0, 237.0), (573.0, 237.0), (618.0, 237.0)  # Fixed y-position to be consistent
        ]
        
        entry_images = [
            "entry_otp1.png", "entry_otp2.png", "entry_otp3.png",
            "entry_otp4.png", "entry_otp5.png", "entry_otp6.png"
        ]
        
        for i, (x, y) in enumerate(entry_positions):
            # Create the background image first
            entry_image = PhotoImage(file=relative_to_assets(entry_images[i]))
            self.canvas.create_image(x, y, image=entry_image)
            
            # Store the image reference to prevent garbage collection
            setattr(self, f"entry_image_{i}", entry_image)
            
            # Create the entry widget with exact positioning
            entry = Entry(
                bd=0, 
                bg="#F5C56E", 
                fg="#000716", 
                highlightthickness=0,
                font=("Inter Bold", 16), 
                justify='center', 
                width=2,
                relief="flat"
            )
            
            # Calculate precise positioning based on the image
            # Adjust these values based on your actual image sizes
            entry_width = 24
            entry_height = 30
            entry_x = x - (entry_width / 2)  # Center horizontally
            entry_y = y - (entry_height / 2) + 5  # Center vertically with slight adjustment
            
            entry.place(x=entry_x, y=entry_y, width=entry_width, height=entry_height)
            
            # Bind events for navigation
            entry.bind('<KeyRelease>', lambda e, idx=i: self.on_otp_keyrelease(e, idx))
            entry.bind('<FocusIn>', lambda e, entry=entry: self.on_otp_focusin(entry))
            
            self.otp_entries.append(entry)

    def on_otp_keyrelease(self, event, current_index):
        """Handle OTP entry navigation"""
        entry = self.otp_entries[current_index]
        
        if event.keysym in ('BackSpace', 'Delete'):
            if current_index > 0 and not entry.get():
                self.otp_entries[current_index - 1].focus()
            return
        
        if entry.get() and len(entry.get()) == 1:
            if current_index < len(self.otp_entries) - 1:
                self.otp_entries[current_index + 1].focus()
            else:
                entry.focus()  # Stay on last entry

    def on_otp_focusin(self, entry):
        """Select all text when focusing on OTP entry"""
        entry.select_range(0, 'end')

    def get_entered_otp(self):
        """Get the complete OTP from all entry fields"""
        return ''.join(entry.get() for entry in self.otp_entries)

    def verify_otp(self):
        """Verify the entered OTP"""
        entered_otp = self.get_entered_otp()
        
        if time.time() > self.otp_expiry_time:
            messagebox.showerror("Error", "OTP has expired. Please request a new one.")
            return
        
        if len(entered_otp) != 6:
            messagebox.showerror("Error", "Please enter the complete 6-digit OTP")
            return
        
        if entered_otp == self.otp_code:
            messagebox.showinfo("Success", "OTP verified successfully!")
            self.verification_callback()
        else:
            messagebox.showerror("Error", "Invalid OTP. Please try again.")

    def resend_otp(self):
        """Resend OTP code"""
        from utils import UtilityFunctions, EmailService
        
        self.otp_code = UtilityFunctions.generate_otp()
        self.otp_expiry_time = time.time() + 600  # Reset to 10 minutes
        
        # Clear OTP entries
        for entry in self.otp_entries:
            entry.delete(0, 'end')
        
        # Resend email
        email_service = EmailService()
        if email_service.send_otp_email(self.user_data['email'], self.otp_code):
            messagebox.showinfo("Success", "New OTP sent to your email!")
            if self.otp_entries:
                self.otp_entries[0].focus()
        else:
            messagebox.showerror("Error", "Failed to send OTP. Please try again.")

    def start_otp_timer(self):
        """Start timer to check OTP expiry"""
        self.check_otp_expiry()

    def check_otp_expiry(self):
        """Check if OTP has expired"""
        remaining_time = self.otp_expiry_time - time.time()
        if remaining_time <= 0:
            self.buttonLbl_resendotp.config(state='normal')
        else:
            self.parent.after(1000, self.check_otp_expiry)

    def go_back(self):
        """Go back to previous screen"""
        self.destroy()
        self.back_callback()

    def destroy(self):
        """Clean up the window"""
        for widget in self.parent.winfo_children():
            widget.destroy()
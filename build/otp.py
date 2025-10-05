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
    return Path(resource_path(f"resources/assets/{path}"))


class OTPVerificationWindow:
    def __init__(self, parent, user_data, otp_code, verification_callback, back_callback, get_db_connection):
        self.parent = parent
        self.user_data = user_data
        self.otp_code = otp_code
        self.verification_callback = verification_callback
        self.back_callback = back_callback
        self.get_db_connection = get_db_connection
        self.otp_entries = []
        self.otp_expiry_time = time.time() + 180  # 3 minutes
        self._is_destroyed = False  # Track if window is destroyed
        self._timer_id = None  # Track the timer
        
        # Store references to all widgets we create
        self.widgets = []
        
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
        self.widgets.append(self.canvas)
        
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
        self.widgets.append(self.button_verify)

        # Resend OTP button
        self.button_image_2 = PhotoImage(file=relative_to_assets("buttonLbl_resendotp.png"))
        self.buttonLbl_resendotp = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.resend_otp,
            relief="flat",
            state='disabled'  # Initially disabled
        )
        self.buttonLbl_resendotp.place(x=400.0, y=347.0, width=212.0, height=18.0)
        self.widgets.append(self.buttonLbl_resendotp)

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
        self.widgets.append(self.button_back)

        # Set tab order for proper navigation
        self.setup_tab_order()

    def setup_tab_order(self):
        """Setup proper tab navigation order"""
        # Set tab order: OTP1 -> OTP2 -> OTP3 -> OTP4 -> OTP5 -> OTP6 -> Verify Button -> Resend Button -> Back Button
        if len(self.otp_entries) >= 6:
            for i in range(5):  # Link OTP1 to OTP5 to their next fields
                self.otp_entries[i].bind('<Tab>', lambda e, idx=i: self.focus_next_otp(e, idx))
                self.otp_entries[i].bind('<Shift-Tab>', lambda e, idx=i: self.focus_prev_otp(e, idx))
            
            # OTP6 should tab to Verify button
            self.otp_entries[5].bind('<Tab>', lambda e: self.focus_verify_button(e))
            self.otp_entries[5].bind('<Shift-Tab>', lambda e, idx=4: self.focus_prev_otp(e, idx))
            
            # Verify button tab order
            self.button_verify.bind('<Tab>', self.focus_resend_button)
            self.button_verify.bind('<Shift-Tab>', lambda e: self.focus_prev_from_verify(e))
            
            # Resend button tab order
            self.buttonLbl_resendotp.bind('<Tab>', self.focus_back_button)
            self.buttonLbl_resendotp.bind('<Shift-Tab>', lambda e: self.focus_verify_button(e))
            
            # Back button tab order
            self.button_back.bind('<Tab>', lambda e: self.focus_first_otp(e))
            self.button_back.bind('<Shift-Tab>', lambda e: self.focus_resend_button(e))
        
        # Also handle Enter key for quick submission
        for entry in self.otp_entries:
            entry.bind('<Return>', lambda e: self.verify_otp())
        
        self.button_verify.bind('<Return>', lambda e: self.verify_otp())

    def focus_next_otp(self, event, current_index):
        """Focus on next OTP field when Tab is pressed"""
        if current_index < len(self.otp_entries) - 1:
            self.otp_entries[current_index + 1].focus()
        return "break"  # Prevent default tab behavior

    def focus_prev_otp(self, event, current_index):
        """Focus on previous OTP field when Shift+Tab is pressed"""
        if current_index > 0:
            self.otp_entries[current_index - 1].focus()
        return "break"  # Prevent default tab behavior

    def focus_verify_button(self, event):
        """Focus on verify button"""
        self.button_verify.focus()
        return "break"

    def focus_resend_button(self, event):
        """Focus on resend button"""
        self.buttonLbl_resendotp.focus()
        return "break"

    def focus_back_button(self, event):
        """Focus on back button"""
        self.button_back.focus()
        return "break"

    def focus_prev_from_verify(self, event):
        """Focus on last OTP field from verify button"""
        if self.otp_entries:
            self.otp_entries[-1].focus()
        return "break"

    def focus_first_otp(self, event):
        """Focus on first OTP field"""
        if self.otp_entries:
            self.otp_entries[0].focus()
        return "break"

    def setup_otp_entries(self):
        """Setup the 6 OTP entry fields with proper alignment"""
        # Adjusted positions for better alignment
        entry_positions = [
            (393.0, 237.0), (438.0, 237.0), (483.0, 237.0),
            (528.0, 237.0), (573.0, 237.0), (618.0, 237.0)
        ]
        
        vcmd = (self.parent.register(self.validate_numeric), '%P')
        
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
                relief="flat",
                validate='key',
                validatecommand=vcmd
            )
            
            # Calculate precise positioning
            entry_width = 24
            entry_height = 27
            entry_x = x - (entry_width / 2)
            entry_y = y - (entry_height / 2) + 5
            
            entry.place(x=entry_x, y=entry_y, width=entry_width, height=entry_height)
            
            # Bind events for navigation
            entry.bind('<KeyRelease>', lambda e, idx=i: self.on_otp_keyrelease(e, idx))
            entry.bind('<FocusIn>', lambda e, entry=entry: self.on_otp_focusin(entry))
            
            self.otp_entries.append(entry)
            self.widgets.append(entry)

        # Focus on first OTP entry when window loads
        if self.otp_entries:
            self.parent.after(100, lambda: self.otp_entries[0].focus())
            
    def validate_numeric(self, new_value):
        """Validate that the entry contains only numeric input"""
        if new_value == "":
            return True
        return new_value.isdigit()

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
                # Last OTP field filled, auto-focus verify button
                self.button_verify.focus()

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
            # Focus on first empty OTP field
            for i, entry in enumerate(self.otp_entries):
                if not entry.get():
                    entry.focus()
                    break
            return
        
        if entered_otp == self.otp_code:
            messagebox.showinfo("Success", "OTP verified successfully!")
            self.verification_callback()
        else:
            messagebox.showerror("Error", "Invalid OTP. Please try again.")
            # Clear all fields and focus on first one
            for entry in self.otp_entries:
                entry.delete(0, 'end')
            if self.otp_entries:
                self.otp_entries[0].focus()

    def resend_otp(self):
        """Resend OTP code"""
        from utils import UtilityFunctions, EmailService
        
        self.otp_code = UtilityFunctions.generate_otp()
        self.otp_expiry_time = time.time() + 180  # Reset to 3 minutes
        
        # Clear OTP entries
        for entry in self.otp_entries:
            entry.delete(0, 'end')
        
        # Resend email
        email_service = EmailService()
        if email_service.send_otp_email(self.user_data['email'], self.otp_code):
            messagebox.showinfo("Success", "New OTP sent to your email!")
            if self.otp_entries:
                self.otp_entries[0].focus()
            
            # Reset timer and disable resend button
            self.buttonLbl_resendotp.config(state='disabled')
            self.start_otp_timer()
        else:
            messagebox.showerror("Error", "Failed to send OTP. Please try again.")

    def start_otp_timer(self):
        """Start timer to check OTP expiry"""
        # Cancel any existing timer
        if self._timer_id:
            self.parent.after_cancel(self._timer_id)
        self._timer_id = self.parent.after(1000, self.check_otp_expiry)

    def check_otp_expiry(self):
        """Check if OTP has expired"""
        # Check if window is destroyed before accessing widgets
        if self._is_destroyed:
            return
            
        remaining_time = self.otp_expiry_time - time.time()
        if remaining_time <= 0:
            # Enable resend button only if window still exists and widget exists
            if (not self._is_destroyed and 
                hasattr(self, 'buttonLbl_resendotp') and 
                self.buttonLbl_resendotp.winfo_exists()):
                self.buttonLbl_resendotp.config(state='normal')
        else:
            # Schedule next check only if window still exists
            if not self._is_destroyed:
                self._timer_id = self.parent.after(1000, self.check_otp_expiry)

    def go_back(self):
        """Go back to previous screen"""
        self.destroy()
        self.back_callback()

    def destroy(self):
        """Clean up only the OTP window widgets"""
        # Mark as destroyed to prevent timer callbacks
        self._is_destroyed = True
        
        # Cancel any pending timers
        if self._timer_id:
            try:
                self.parent.after_cancel(self._timer_id)
            except:
                pass  # Timer might already be cancelled
        
        # Destroy only the widgets we created, not all widgets in parent
        for widget in self.widgets:
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except:
                pass  # Widget might already be destroyed
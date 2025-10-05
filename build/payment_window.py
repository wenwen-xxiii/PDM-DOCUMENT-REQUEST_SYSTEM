import tkinter as tk
from tkinter import messagebox
import webbrowser
from pathlib import Path
import mysql.connector
from datetime import datetime

from config import DB_CONFIG
from payment_processor import PayMongoProcessor

class PaymentWindow:
    def __init__(self, parent, request_data, student_data, refresh_callback=None):
        self.parent = parent
        self.request_data = request_data
        self.student_data = student_data
        self.refresh_callback = refresh_callback
        self.payment_processor = PayMongoProcessor()
        
        self.create_window()
        
    def create_window(self):
        """Create payment window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Document Request Payment")
        self.window.geometry("508x623")
        self.window.configure(bg="#FCECB7")
        self.window.resizable(False, False)
        
        self.window.transient(self.parent)
        self._center_window()
        self.window.grab_set()
        
        self._create_canvas()
        self._create_ui_elements()
        
    def _center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width, height = 508, 623
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def _create_canvas(self):
        """Create main canvas"""
        self.canvas = tk.Canvas(
            self.window,
            bg="#FCECB7",
            height=623,
            width=508,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        
    def _create_ui_elements(self):
        """Create all UI elements"""
        self._create_header()
        self._create_payment_details()
        
    def _create_header(self):
        """Create header section"""
        # Header rectangle
        self.canvas.create_rectangle(0.0, 0.0, 508.0, 98.0, fill="#792D1B", outline="")
        
        # Back button
        self._create_back_button()
        
        # Yellow header strip
        self.canvas.create_rectangle(0.0, 57.0, 508.0, 99.0, fill="#FFDA0C", outline="")
        
        # Header text
        self.canvas.create_text(
            254.0, 78.0,
            text="Payment Details",
            fill="#000000",
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        
    def _create_back_button(self):
        """Create back button"""
        try:
            button_image = tk.PhotoImage(file=self._relative_to_assets("button_back.png"))
            self.back_button = tk.Button(
                self.window,
                image=button_image,
                borderwidth=0,
                highlightthickness=0,
                command=self.window.destroy,
                relief="flat",
                bg="#792D1B",
                activebackground="#792D1B"
            )
            self.back_button.place(x=27, y=19, width=15, height=18)
            self.back_button.image = button_image
        except Exception:
            # Fallback text button
            self.back_button = tk.Button(
                self.window,
                text="←",
                font=("Arial", 14, "bold"),
                command=self.window.destroy,
                bg="#792D1B",
                fg="white",
                borderwidth=0,
                relief="flat"
            )
            self.back_button.place(x=20, y=15, width=30, height=30)
        
    def _create_payment_details(self):
        """Create payment details section"""
        self._create_background_panel()
        self._create_request_info()
        self._create_payment_methods()
        self._create_payment_button()
        
    def _create_background_panel(self):
        """Create white background panel"""
        try:
            img_panel = tk.PhotoImage(file=self._relative_to_assets("img_whitebg.png"))
            self.canvas.create_image(251.0, 363.0, image=img_panel)
            self.img_panel = img_panel
        except Exception:
            self.canvas.create_rectangle(
                25.0, 120.0, 483.0, 550.0,
                fill="#FFFFFF", outline="#DDDDDD", width=2
            )
        
    def _create_request_info(self):
        """Create request information display"""
        info_y_start = 140
        line_height = 30
        
        details = [
            ("Request Number:", self.request_data['request_number']),
            ("Document:", self.request_data['document_name']),
            ("Quantity:", str(self.request_data['quantity'])),
            ("Delivery:", self.request_data['delivery_mode'].title()),
        ]
        
        for i, (label, value) in enumerate(details):
            self.canvas.create_text(
                50.0, info_y_start + (i * line_height),
                text=label, fill="#000000", font=("Arial", 12, "bold"), anchor="w"
            )
            self.canvas.create_text(
                200.0, info_y_start + (i * line_height),
                text=value, fill="#000000", font=("Arial", 12), anchor="w"
            )
        
        # Amount display
        amount_y = info_y_start + (len(details) * line_height) + 20
        self.canvas.create_text(
            254.0, amount_y,
            text=f"Total Amount: ₱{self.request_data['total_amount']:.2f}",
            fill="#792D1B",
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        
    def _create_payment_methods(self):
        """Create payment method selection"""
        method_y = 320
        self.canvas.create_text(
            50.0, method_y,
            text="Payment Method:",
            fill="#000000",
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        
        self.payment_method = tk.StringVar(value="online")
        
        radio_y = method_y + 30
        online_radio = tk.Radiobutton(
            self.window,
            text="Online Payment (GCash, Credit Card, etc.)",
            variable=self.payment_method,
            value="online",
            bg="#FFFFFF",
            font=("Arial", 10),
            anchor="w"
        )
        online_radio.place(x=50, y=radio_y, width=400, height=25)
        
        cash_radio = tk.Radiobutton(
            self.window,
            text="Cash Payment",
            variable=self.payment_method,
            value="cash",
            bg="#FFFFFF",
            font=("Arial", 10),
            anchor="w"
        )
        cash_radio.place(x=50, y=radio_y + 30, width=400, height=25)
        
    def _create_payment_button(self):
        """Create payment button"""
        button_y = 420
        try:
            pay_button_img = tk.PhotoImage(file=self._relative_to_assets("button_pay.png"))
            self.pay_button = tk.Button(
                self.window,
                image=pay_button_img,
                borderwidth=0,
                highlightthickness=0,
                command=self.process_payment,
                relief="flat",
                bg="#FFFFFF",
                activebackground="#FFFFFF"
            )
            self.pay_button.place(x=154.0, y=button_y, width=200.0, height=50.0)
            self.pay_button.image = pay_button_img
        except Exception:
            self.pay_button = tk.Button(
                self.window,
                text="Proceed to Payment",
                font=("Arial", 12, "bold"),
                command=self.process_payment,
                bg="#792D1B",
                fg="white",
                borderwidth=0,
                relief="flat",
                width=20,
                height=2
            )
            self.pay_button.place(x=154.0, y=button_y, width=200.0, height=50.0)
        
        # Status label
        self.status_label = tk.Label(
            self.window,
            text="",
            fg="#792D1B",
            bg="#FFFFFF",
            font=("Arial", 10, "italic")
        )
        self.status_label.place(x=50, y=button_y + 70, width=400, height=20)
        
    def process_payment(self):
        """Process payment based on selected method"""
        payment_method = self.payment_method.get()
        
        if payment_method == "cash":
            self._process_cash_payment()
        else:
            self._process_online_payment()
    
    def _process_online_payment(self):
        """Process online payment with webhook support"""
        try:
            # Disable payment button immediately to prevent multiple clicks
            self.pay_button.config(state="disabled")
            self.status_label.config(text="Creating payment link...")
            self.window.update()
            
            description = f"Document: {self.request_data['document_name']} - Request: {self.request_data['request_number']}"
            student_name = f"{self.student_data.get('first_name', '')} {self.student_data.get('last_name', '')}"
            
            metadata = {
                'student_name': student_name,
                'student_number': self.student_data.get('student_number', ''),
                'request_number': self.request_data['request_number'],
                'document_name': self.request_data['document_name'],
                'purpose': 'Document Request Payment'
            }
            
            # Use request_id from request_data (should be the primary key)
            request_id = self.request_data['request_id']
            
            result = self.payment_processor.create_checkout_session(
                request_id=request_id,
                amount=self.request_data['total_amount'],
                description=description,
                metadata=metadata,
                success_url="https://araneiform-daisey-transthalamic.ngrok-free.dev/success",
                cancel_url="https://araneiform-daisey-transthalamic.ngrok-free.dev/cancel"
            )
            
            if result['success']:
                self.checkout_id = result['checkout_id']
                checkout_url = result['checkout_url']
                self.status_label.config(text="Opening payment page...")
                
                webbrowser.open(checkout_url)
                
                messagebox.showinfo(
                    "Payment Processing",
                    f"✅ Payment page opened in your browser!\n\n"
                    f"🔗 Please complete the payment in the opened window.\n"
                    f"📧 Payment status will update automatically via webhook.\n"
                    f"🔄 The system will refresh when payment is confirmed.\n\n"
                    f"Checkout ID: {self.checkout_id}"
                )
                
                # Close payment window
                self.window.destroy()
                
                # Refresh the main window to show "Payment Verified" status
                if self.refresh_callback:
                    self.refresh_callback()
                    
            else:
                messagebox.showerror("Payment Error", f"Failed to create payment: {result['error']}")
                self.status_label.config(text="Payment failed")
                # Re-enable button if payment creation failed
                self.pay_button.config(state="normal")
                    
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.config(text="Error occurred")
            # Re-enable button if error occurred
            self.pay_button.config(state="normal")
        
    def _process_cash_payment(self):
        """Process cash payment"""
        try:
            # Disable payment button immediately
            self.pay_button.config(state="disabled")
            self.status_label.config(text="Processing cash payment...")
            self.window.update()
            
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            reference_number = f"CASH{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Use request_id instead of id
            cursor.execute("""
                INSERT INTO payments 
                (request_id, amount, payment_method, reference_number, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.request_data['request_id'], self.request_data['total_amount'], 'cash', reference_number, 'pending'))
            
            # Use request_id instead of id
            cursor.execute("""
                UPDATE document_requests 
                SET payment_status = 'pending', 
                    payment_method = 'cash',
                    status = 'under_review'
                WHERE request_id = %s
            """, (self.request_data['request_id'],))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messagebox.showinfo(
                "Cash Payment",
                f"✅ Cash payment recorded successfully!\n\n"
                f"🏦 Please proceed to the cashier's office to complete your payment.\n"
                f"📋 Reference Number: {reference_number}\n"
                f"💰 Amount: ₱{self.request_data['total_amount']:.2f}"
            )
            
            self.window.destroy()
            
            if self.refresh_callback:
                self.refresh_callback()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record cash payment: {str(e)}")
            # Re-enable button if error occurred
            self.pay_button.config(state="normal")

    def _relative_to_assets(self, path: str):
        """Get path to assets"""
        assets_path = Path(__file__).parent / "assets" / "paymentform"
        return assets_path / Path(path)
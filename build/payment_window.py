import tkinter as tk
from tkinter import messagebox
import webbrowser
from pathlib import Path
import mysql.connector
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from config import DB_CONFIG
from payment_processor import PayMongoProcessor
from async_utils import safe_async_run

class PaymentWindow:
    def __init__(self, parent, request_data, student_data, refresh_callback=None):
        self.parent = parent
        self.request_data = request_data
        self.student_data = student_data
        self.refresh_callback = refresh_callback
        self.payment_processor = PayMongoProcessor()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
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
        info_y_start = 150
        line_height = 30
        
        details = [
            ("Request Number:", self.request_data['request_number']),
            ("Document:", self.request_data['document_name']),
            ("Quantity:", str(self.request_data['quantity'])),
            ("Delivery:", self.request_data['delivery_mode'].title()),
        ]
        
        # Center the details section
        center_x = 254.0  # Center of the window (508/2)
        
        for i, (label, value) in enumerate(details):
            # Create centered text for each detail
            detail_text = f"{label} {value}"
            self.canvas.create_text(
                center_x, info_y_start + (i * line_height),
                text=detail_text, fill="#000000", font=("Arial", 12, "bold"), anchor="center"
            )
        
        # Amount display
        amount_y = info_y_start + (len(details) * line_height) + 20
        self.canvas.create_text(
            center_x, amount_y,
            text=f"Total Amount: ₱{self.request_data['total_amount']:.2f}",
            fill="#792D1B",
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        
    def _create_payment_methods(self):
        """Create payment method selection"""
        method_y = 330
        center_x = 254.0  # Center of the window
        
        self.canvas.create_text(
            center_x, method_y,
            text="Payment Method:",
            fill="#000000",
            font=("Arial", 12, "bold"),
            anchor="center"
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
            anchor="center"
        )
        online_radio.place(x=54, y=radio_y, width=400, height=25)
        
        cash_radio = tk.Radiobutton(
            self.window,
            text="Cash Payment",
            variable=self.payment_method,
            value="cash",
            bg="#FFFFFF",
            font=("Arial", 10),
            anchor="center"
        )
        cash_radio.place(x=54, y=radio_y + 30, width=400, height=25)
        
    def _create_payment_button(self):
        """Create payment button"""
        button_y = 440
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
            font=("Arial", 10, "italic"),
            anchor="center"
        )
        self.status_label.place(x=54, y=button_y + 70, width=400, height=20)
        
    def process_payment(self):
        """Synchronous wrapper for async payment processing"""
        # Run in background thread to avoid blocking UI
        def payment_thread():
            safe_async_run(self.process_payment_async)
        
        threading.Thread(target=payment_thread, daemon=True).start()

    async def process_payment_async(self):
        """Process payment based on selected method asynchronously"""
        payment_method = self.payment_method.get()
        
        if payment_method == "cash":
            await self._process_cash_payment_async()
        else:
            await self._process_online_payment_async()
    
    async def _process_online_payment_async(self):
        """Process online payment with webhook support asynchronously"""
        try:
            # Disable payment button immediately to prevent multiple clicks
            await self.run_in_main_thread(lambda: self.pay_button.config(state="disabled"))
            await self.run_in_main_thread(lambda: self.status_label.config(text="Creating payment link..."))
            await self.run_in_main_thread(lambda: self.window.update())
            
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
            
            # Run payment processor in thread pool
            result = await self.run_in_thread_pool(
                lambda: self.payment_processor.create_checkout_session(
                    request_id=request_id,
                    amount=self.request_data['total_amount'],
                    description=description,
                    metadata=metadata,
                    success_url="https://araneiform-daisey-transthalamic.ngrok-free.dev/success",
                    cancel_url="https://araneiform-daisey-transthalamic.ngrok-free.dev/cancel"
                )
            )
            
            if result['success']:
                self.checkout_id = result['checkout_id']
                checkout_url = result['checkout_url']
                await self.run_in_main_thread(lambda: self.status_label.config(text="Opening payment page..."))
                
                # Open browser in main thread
                await self.run_in_main_thread(lambda: webbrowser.open(checkout_url))
                
                await self.run_in_main_thread(lambda: messagebox.showinfo(
                    "Payment Processing",
                    f"✅ Payment page opened in your browser!\n\n"
                    f"🔗 Please complete the payment in the opened window.\n"
                    f"📧 Payment status will update automatically via webhook.\n"
                    f"🔄 The system will refresh when payment is confirmed.\n\n"
                    f"Checkout ID: {self.checkout_id}"
                ))
                
                # Close payment window
                await self.run_in_main_thread(lambda: self.window.destroy())
                
                # Refresh the main window to show "Payment Verified" status
                if self.refresh_callback:
                    await self.run_in_main_thread(self.refresh_callback)
                    
            else:
                await self.run_in_main_thread(
                    lambda: messagebox.showerror("Payment Error", f"Failed to create payment: {result['error']}")
                )
                await self.run_in_main_thread(lambda: self.status_label.config(text="Payment failed"))
                # Re-enable button if payment creation failed
                await self.run_in_main_thread(lambda: self.pay_button.config(state="normal"))
                    
        except Exception as e:
            await self.run_in_main_thread(
                lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}")
            )
            await self.run_in_main_thread(lambda: self.status_label.config(text="Error occurred"))
            # Re-enable button if error occurred
            await self.run_in_main_thread(lambda: self.pay_button.config(state="normal"))
        
        finally:
            # Cleanup resources
            self.cleanup()
        
    async def _process_cash_payment_async(self):
        """Process cash payment with email notification asynchronously"""
        try:
            # Disable payment button immediately
            await self.run_in_main_thread(lambda: self.pay_button.config(state="disabled"))
            await self.run_in_main_thread(lambda: self.status_label.config(text="Processing cash payment..."))
            await self.run_in_main_thread(lambda: self.window.update())
            
            # Run database operations in thread pool
            result = await self.run_in_thread_pool(
                lambda: self._record_cash_payment()
            )
            
            if result['success']:
                reference_number = result['reference_number']
                
                # Send email notification for cash payment asynchronously
                await self._send_cash_payment_email(reference_number)
                
                await self.run_in_main_thread(lambda: messagebox.showinfo(
                    "Cash Payment",
                    f"✅ Cash payment recorded successfully!\n\n"
                    f"🏦 Please proceed to the cashier's office to complete your payment.\n"
                    f"📋 Reference Number: {reference_number}\n"
                    f"💰 Amount: ₱{self.request_data['total_amount']:.2f}\n\n"
                    f"📧 A confirmation email has been sent with payment details."
                ))
                
                await self.run_in_main_thread(lambda: self.window.destroy())
                
                if self.refresh_callback:
                    await self.run_in_main_thread(self.refresh_callback)
            else:
                await self.run_in_main_thread(
                    lambda: messagebox.showerror("Error", f"Failed to record cash payment: {result['error']}")
                )
                # Re-enable button if error occurred
                await self.run_in_main_thread(lambda: self.pay_button.config(state="normal"))
                
        except Exception as e:
            await self.run_in_main_thread(
                lambda: messagebox.showerror("Error", f"Failed to record cash payment: {str(e)}")
            )
            # Re-enable button if error occurred
            await self.run_in_main_thread(lambda: self.pay_button.config(state="normal"))
        
        finally:
            # Cleanup resources
            self.cleanup()

    def _record_cash_payment(self):
        """Record cash payment in database (runs in thread pool)"""
        try:
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
                    status = 'processing'
                WHERE request_id = %s
            """, (self.request_data['request_id'],))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {'success': True, 'reference_number': reference_number}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _send_cash_payment_email(self, reference_number):
        """Send email notification for cash payment with fallback using async"""
        try:
            # Try to import email service
            try:
                from utils import email_service
                has_email_service = True
            except ImportError:
                has_email_service = False
                
            student_email = self.student_data.get('email')
            if not student_email:
                print("[ERROR] No email found for student")
                return False
                
            student_name = f"{self.student_data.get('first_name', '')} {self.student_data.get('last_name', '')}"
            request_number = self.request_data['request_number']
            document_name = self.request_data['document_name']
            amount = self.request_data['total_amount']
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            subject = f"Cash Payment Instructions - Request #{request_number}"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: #800000; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: #FFD700; margin: 0;">PAMBAYANG DALUBHASAAN NG MARILAO</h1>
                        <h2 style="color: white; margin: 10px 0 0 0;">Document Request System</h2>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #800000;">Cash Payment Instructions</h2>
                        <p>Dear {student_name},</p>
                        
                        <p>Your cash payment for document request #{request_number} has been recorded. Please proceed with the payment following the instructions below.</p>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #800000; margin-top: 0;">Payment Details:</h3>
                            <p><strong>Request Number:</strong> #{request_number}</p>
                            <p><strong>Document:</strong> {document_name}</p>
                            <p><strong>Amount Due:</strong> ₱{amount:.2f}</p>
                            <p><strong>Payment Method:</strong> Cash</p>
                            <p><strong>Reference Number:</strong> {reference_number}</p>
                            <p><strong>Payment Date:</strong> {current_date}</p>
                        </div>
                        
                        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #155724; margin-top: 0;">Payment Instructions:</h4>
                            <p style="color: #155724; margin: 5px 0;"><strong>1. Location:</strong> Cashier's Office</p>
                            <p style="color: #155724; margin: 5px 0;"><strong>2. Office Hours:</strong> Monday-Friday, 8:00 AM - 5:00 PM</p>
                            <p style="color: #155724; margin: 5px 0;"><strong>3. Required:</strong> Present this reference number: <strong>{reference_number}</strong></p>
                            <p style="color: #155724; margin: 5px 0;"><strong>4. Payment:</strong> Exact amount of ₱{amount:.2f}</p>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #856404; margin-top: 0;">Important Notes:</h4>
                            <p style="color: #856404; margin: 5px 0;">• Please pay within 3 working days to avoid cancellation</p>
                            <p style="color: #856404; margin: 5px 0;">• Keep this reference number for your records</p>
                            <p style="color: #856404; margin: 5px 0;">• Your document will be processed after payment confirmation</p>
                        </div>
                        
                        <div style="background: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #0c5460; margin-top: 0;">Next Steps:</h4>
                            <p style="color: #0c5460; margin: 5px 0;">After payment, your document request will be processed</p>
                            <p style="color: #0c5460; margin: 5px 0;">You will receive another email when your document is ready</p>
                        </div>
                        
                        <hr style="margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if has_email_service:
                # Send email using async email service
                success = await email_service._send_email(student_email, subject, body)
                if success:
                    print(f"[OK] Cash payment email sent to {student_email}")
                    return True
                else:
                    print(f"[ERROR] Failed to send cash payment email to {student_email}")
                    # Fall through to fallback method
                    
            # Fallback: Print email details
            print("=" * 60)
            print("[EMAIL] CASH PAYMENT EMAIL (FALLBACK)")
            print("=" * 60)
            print(f"To: {student_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body}")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"[ERROR] Error in cash payment email: {e}")
            return False

    async def run_in_main_thread(self, func):
        """Run function in main thread"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func)

    async def run_in_thread_pool(self, func):
        """Run function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func)

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

    def _relative_to_assets(self, path: str):
        """Get path to assets"""
        assets_path = Path(__file__).parent / "assets" / "paymentform"
        return assets_path / Path(path)
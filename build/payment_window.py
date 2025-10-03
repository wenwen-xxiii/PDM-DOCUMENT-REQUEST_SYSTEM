import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from payment_processor import PayMongoProcessor
import mysql.connector
from config import DB_CONFIG
from datetime import datetime 

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
        self.window.geometry("500x450")
        self.window.configure(bg="white")
        self.window.resizable(False, False)
        
        # Center the window
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Payment details frame
        details_frame = ttk.LabelFrame(self.window, text="Payment Details", padding=20)
        details_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Request information
        ttk.Label(details_frame, text=f"Request Number: {self.request_data['request_number']}").grid(
            row=0, column=0, sticky="w", pady=5)
        ttk.Label(details_frame, text=f"Document: {self.request_data['document_name']}").grid(
            row=1, column=0, sticky="w", pady=5)
        ttk.Label(details_frame, text=f"Quantity: {self.request_data['quantity']}").grid(
            row=2, column=0, sticky="w", pady=5)
        ttk.Label(details_frame, text=f"Delivery: {self.request_data['delivery_mode'].title()}").grid(
            row=3, column=0, sticky="w", pady=5)
        
        # Amount
        amount_label = ttk.Label(details_frame, 
                               text=f"Total Amount: ₱{self.request_data['total_amount']:.2f}",
                               font=("Arial", 14, "bold"),
                               foreground="green")
        amount_label.grid(row=4, column=0, sticky="w", pady=15)
        
        # Payment method selection
        ttk.Label(details_frame, text="Payment Method:").grid(row=5, column=0, sticky="w", pady=5)
        self.payment_method = tk.StringVar(value="online")
        
        payment_frame = ttk.Frame(details_frame)
        payment_frame.grid(row=6, column=0, sticky="w", pady=5)
        
        ttk.Radiobutton(payment_frame, text="Online Payment (GCash, Credit Card, etc.)", 
                       variable=self.payment_method, value="online").pack(anchor="w")
        ttk.Radiobutton(payment_frame, text="Cash Payment", 
                       variable=self.payment_method, value="cash").pack(anchor="w")
        
        # Payment button
        pay_button = ttk.Button(
            details_frame,
            text="Proceed to Payment",
            command=self.process_payment,
            style="Accent.TButton"
        )
        pay_button.grid(row=7, column=0, pady=20)
        
        # Status label
        self.status_label = ttk.Label(details_frame, text="", foreground="blue")
        self.status_label.grid(row=8, column=0, pady=10)
        
        # Configure style for accent button
        style = ttk.Style()
        style.configure("Accent.TButton", background="#007ACC", foreground="white")
        
    def process_payment(self):
        """Process payment based on selected method"""
        payment_method = self.payment_method.get()
        
        if payment_method == "cash":
            self.process_cash_payment()
        else:
            self.process_online_payment()
    
    def process_online_payment(self):
        """Process online payment through PayMongo Checkout Sessions"""
        try:
            description = f"Document: {self.request_data['document_name']} - Request: {self.request_data['request_number']}"
            student_name = f"{self.student_data.get('first_name', '')} {self.student_data.get('last_name', '')}"
            
            # FLAT metadata (no nested objects)
            metadata = {
                'student_name': student_name,
                'student_number': self.student_data.get('student_number', ''),
                'request_number': self.request_data['request_number'],
                'document_name': self.request_data['document_name'],
                'purpose': 'Document Request Payment'
            }
            
            # Define success and cancel URLs (you can customize these later)
            success_url = "https://www.facebook.com/"  # Change to your actual success page
            cancel_url = "https://www.youtube.com/"    # Change to your actual cancel page
            
            self.status_label.config(text="Creating payment link...")
            self.window.update()
            
            # Use the actual request ID from the database
            request_id = self.request_data['id']
            
            # Create checkout session with PayMongo
            result = self.payment_processor.create_checkout_session(
                request_id=request_id,
                amount=self.request_data['total_amount'],
                description=description,
                metadata=metadata,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            if result['success']:
                # Create payment record in database
                payment_id = self.payment_processor.create_payment_record(
                    request_id=request_id,
                    payment_intent_id=result['payment_intent_id'],
                    amount=self.request_data['total_amount'],
                    payment_method="online"
                )
                
                # Store checkout ID for later verification
                self.checkout_id = result['checkout_id']
                
                # Open checkout URL in browser
                checkout_url = result['checkout_url']
                self.status_label.config(text="Opening payment page...")
                
                print(f"🔗 Opening checkout URL: {checkout_url}")
                
                # Open browser for payment
                webbrowser.open(checkout_url)
                
                # Show success message with instructions
                messagebox.showinfo(
                    "Payment Processing",
                    f"Payment page opened in your browser.\n\n"
                    f"Please complete the payment process in the opened window.\n"
                    f"Your request status will update automatically once payment is confirmed.\n\n"
                    f"Checkout ID: {self.checkout_id}"
                )
                
                # Close payment window
                self.window.destroy()
                
                # Refresh the main window
                if self.refresh_callback:
                    self.refresh_callback()
                    
            else:
                messagebox.showerror("Payment Error", f"Failed to create payment: {result['error']}")
                self.status_label.config(text="Payment failed")
                    
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.config(text="Error occurred")
        
    def process_cash_payment(self):
        """Process cash payment"""
        try:
            # Create cash payment record
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()
            
            # Generate reference number
            reference_number = f"CASH{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Insert into payments table
            cursor.execute("""
                INSERT INTO payments 
                (request_id, amount, payment_method, reference_number, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.request_data['id'], self.request_data['total_amount'], 'cash', reference_number, 'pending'))
            
            # Update document_requests table
            cursor.execute("""
                UPDATE document_requests 
                SET payment_status = 'pending', 
                    payment_method = 'cash',
                    status = 'under_review'
                WHERE id = %s
            """, (self.request_data['id'],))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messagebox.showinfo(
                "Cash Payment",
                f"Cash payment recorded successfully!\n\n"
                f"Please proceed to the cashier's office to complete your payment.\n"
                f"Reference Number: {reference_number}\n"
                f"Amount: ₱{self.request_data['total_amount']:.2f}"
            )
            
            self.window.destroy()
            
            # Refresh the main window
            if self.refresh_callback:
                self.refresh_callback()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record cash payment: {str(e)}")
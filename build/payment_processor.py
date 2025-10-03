import requests
import json
import base64
from config import DB_CONFIG, PAYMONGO_CONFIG
import mysql.connector
from datetime import datetime


class PayMongoProcessor:
    def __init__(self):
        self.secret_key = PAYMONGO_CONFIG['secret_key']
        self.base_url = "https://api.paymongo.com/v1"
        
    def get_db_connection(self):
        return mysql.connector.connect(**DB_CONFIG)
        
    def get_auth_header(self):
        """Generate Base64 encoded authorization header"""
        auth_string = f"{self.secret_key}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        return f"Basic {encoded_auth}"
    
    
    def create_checkout_session(self, request_id, amount, description, metadata=None, success_url=None, cancel_url=None):
        """Create a checkout session with PayMongo"""
        url = f"{self.base_url}/checkout_sessions"
        
        # Validate amount
        if amount <= 0:
            return {
                'success': False,
                'error': 'Amount must be greater than 0'
            }
        
        # Convert to cents and ensure it's an integer
        amount_in_cents = int(round(amount * 100))
        
        # PayMongo requires minimum amount of 100 cents (₱1.00)
        if amount_in_cents < 100:
            return {
                'success': False,
                'error': 'Minimum payment amount is ₱1.00'
            }
        
        # Default URLs if not provided
        if not success_url:
            success_url = "https://pdm.edu.ph/success"
        if not cancel_url:
            cancel_url = "https://pdm.edu.ph/cancel"
        
        # FLAT metadata
        flat_metadata = {}
        if metadata:
            for key, value in metadata.items():
                flat_metadata[str(key)] = str(value)
        
        # Checkout Session payload
        payload = {
            "data": {
                "attributes": {
                    "send_email_receipt": False,
                    "show_description": True,
                    "show_line_items": True,
                    "cancel_url": cancel_url,
                    "success_url": success_url,
                    "payment_method_types": ["card", "gcash", "grab_pay"],
                    "line_items": [
                        {
                            "amount": amount_in_cents,
                            "currency": "PHP",
                            "name": description[:100],
                            "quantity": 1
                        }
                    ],
                    "description": description[:255],
                    "metadata": flat_metadata
                }
            }
        }
        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": self.get_auth_header()
        }
        
        try:
            print(f"🔧 PayMongo Checkout Session Request:")
            print(f"   URL: {url}")
            print(f"   Amount: ₱{amount:.2f} ({amount_in_cents} cents)")
            print(f"   Description: {description}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            print(f"🔧 PayMongo Checkout Session Response:")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error Response: {response.text}")
                
            response.raise_for_status()
            
            result = response.json()
            
            # Extract data from PayMongo response
            checkout_session = result['data']
            checkout_id = checkout_session['id']
            checkout_url = checkout_session['attributes']['checkout_url']
            
            print(f"✅ Checkout Session Created:")
            print(f"   ID: {checkout_id}")
            print(f"   Checkout URL: {checkout_url}")
            print(f"   Status: {checkout_session['attributes']['status']}")
            
            # FIX: Checkout sessions don't have payment_intent_id directly
            # We'll use the checkout_id as the reference instead
            return {
                'success': True,
                'checkout_id': checkout_id,
                'checkout_url': checkout_url,
                'payment_intent_id': checkout_id,  # Use checkout_id as reference
                'response_data': result
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.text:
                try:
                    error_data = e.response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {e.response.text}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'status_code': e.response.status_code
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def create_payment_record(self, request_id, payment_intent_id, amount, payment_method="online"):
        """Create a payment record in the payments table and update document_requests"""
        connection = self.get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Generate reference number
            reference_number = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Insert into payments table
            cursor.execute("""
                INSERT INTO payments 
                (request_id, amount, payment_method, reference_number, gateway_transaction_id, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (request_id, amount, payment_method, reference_number, payment_intent_id, 'pending'))
            
            payment_id = cursor.lastrowid
            
            # Update document_requests table with payment_intent_id
            cursor.execute("""
                UPDATE document_requests 
                SET payment_status = 'pending', 
                    payment_method = %s,
                    payment_intent_id = %s
                WHERE id = %s
            """, (payment_method, payment_intent_id, request_id))
            
            connection.commit()
            print(f"✅ Payment record created: {payment_id}")
            print(f"✅ Payment intent ID stored in document_requests: {payment_intent_id}")
            return payment_id
            
        except Exception as e:
            connection.rollback()
            print(f"❌ Failed to create payment record: {e}")
            raise e
        finally:
            cursor.close()
            connection.close()
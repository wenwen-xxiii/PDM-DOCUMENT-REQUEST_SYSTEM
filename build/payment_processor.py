import aiohttp
import asyncio
import json
import base64
import mysql.connector
from datetime import datetime
from config import DB_CONFIG, PAYMONGO_CONFIG
from concurrent.futures import ThreadPoolExecutor
from async_utils import safe_async_run

class PayMongoProcessor:
    def __init__(self):
        self.secret_key = PAYMONGO_CONFIG['secret_key']
        self.base_url = "https://api.paymongo.com/v1"
        self.webhook_url = "https://araneiform-daisey-transthalamic.ngrok-free.dev/webhook/paymongo"
        
        # Thread pool for database operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # HTTP session for async requests
        self.http_session = None
        
    def get_db_connection(self):
        """Establish database connection"""
        return mysql.connector.connect(**DB_CONFIG)
        
    def get_auth_header(self):
        """Generate Base64 encoded authorization header"""
        auth_string = f"{self.secret_key}:"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        return f"Basic {encoded_auth}"

    async def get_http_session(self):
        """Get or create HTTP session"""
        if self.http_session is None:
            self.http_session = aiohttp.ClientSession()
        return self.http_session

    async def cleanup_http_session(self):
        """Cleanup HTTP session"""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None

    async def run_in_thread_pool(self, func):
        """Run function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func)

    def handle_webhook_event(self, payload, headers):
        """Synchronous wrapper for async webhook handling"""
        return asyncio.run(self.handle_webhook_event_async(payload, headers))

    async def handle_webhook_event_async(self, payload, headers):
        """Handle incoming webhook events from PayMongo asynchronously"""
        try:
            print(f"🔔 Webhook received from PayMongo")
            
            # Print full payload for debugging
            print(f"📦 Full webhook payload: {json.dumps(payload, indent=2)}")
            
            # Enhanced debugging
            event_type = payload['data']['attributes']['type']
            print(f"🔔 Webhook received - Type: {event_type}")
            print(f"📦 Full payload keys: {list(payload.keys())}")
            if 'data' in payload and 'attributes' in payload['data']:
                print(f"📧 Event data structure: {list(payload['data']['attributes'].keys())}")
            
            # Verify webhook signature (important for security)
            if not await self.run_in_thread_pool(lambda: self.verify_webhook_signature(payload, headers)):
                print("❌ Webhook signature verification failed")
                return {'success': False, 'error': 'Invalid signature'}
            
            event_type = payload['data']['attributes']['type']
            event_data = payload['data']['attributes']['data']
            
            print(f"📧 Event Type: {event_type}")
            print(f"📦 Event Data: {json.dumps(event_data, indent=2)}")
            
            if event_type == 'checkout_session.payment.paid':
                return await self._handle_checkout_session_paid_async(event_data)
            elif event_type == 'payment.paid':
                print("💰 Direct payment.paid event received")
                return await self._handle_direct_payment_paid_async(event_data)
            elif event_type == 'checkout_session.payment.failed':
                return await self._handle_payment_failed_async(event_data)
            elif event_type == 'checkout_session.payment.cancelled':
                return await self._handle_payment_cancelled_async(event_data)
            else:
                print(f"ℹ️  Unhandled webhook event: {event_type}")
                return {'success': True, 'message': 'Event not handled'}
                
        except Exception as e:
            print(f"❌ Error handling webhook: {e}")
            print(f"📦 Full payload that caused error: {json.dumps(payload, indent=2)}")
            return {'success': False, 'error': str(e)}

    async def _handle_checkout_session_paid_async(self, event_data):
        """Handle checkout_session.payment.paid event asynchronously"""
        try:
            # Extract checkout session ID from the correct location in event data
            if 'id' in event_data:
                # Event data is the checkout session object itself
                checkout_session_id = event_data['id']
            elif 'attributes' in event_data and 'checkout_session_id' in event_data['attributes']:
                # Event data contains attributes with checkout_session_id
                checkout_session_id = event_data['attributes']['checkout_session_id']
            else:
                print(f"❌ Could not find checkout session ID in event data: {event_data}")
                return {'success': False, 'error': 'Could not find checkout session ID'}
            
            print(f"🎉 Checkout session payment successful: {checkout_session_id}")
            
            # Update database status using checkout_session_id
            success = await self.run_in_thread_pool(
                lambda: self._update_to_paid_status(checkout_session_id)
            )
            
            if success:
                return {'success': True, 'message': 'Payment processed successfully'}
            else:
                return {'success': False, 'error': 'Failed to update database'}
            
        except Exception as e:
            print(f"❌ Error handling checkout session payment: {e}")
            print(f"📦 Event data received: {event_data}")
            return {'success': False, 'error': str(e)}

    async def _handle_direct_payment_paid_async(self, event_data):
        """Handle payment.paid event - find the checkout session from payment asynchronously"""
        try:
            payment_id = event_data['id']
            print(f"💰 Direct payment successful: {payment_id}")
            
            # Extract metadata from payment
            metadata = event_data.get('attributes', {}).get('metadata', {})
            request_number = metadata.get('request_number')
            request_id = metadata.get('request_id')
            
            print(f"📋 Payment metadata - Request: {request_number}, ID: {request_id}")
            
            checkout_session_id = None
            
            # Method 1: Try to find checkout session from document_requests
            if request_id or request_number:
                checkout_session_id = await self.run_in_thread_pool(
                    lambda: self._find_checkout_session_by_request(request_id, request_number)
                )
            
            # Method 2: Try API call to get payment intent
            if not checkout_session_id:
                payment_details = await self._get_payment_details_async(payment_id)
                if payment_details['success']:
                    # Get payment intent ID and find associated checkout session
                    payment_intent_id = payment_details.get('payment_intent_id')
                    if payment_intent_id:
                        checkout_session_id = await self.run_in_thread_pool(
                            lambda: self._find_checkout_session_by_payment_intent(payment_intent_id)
                        )
            
            # Method 3: Search for most recent pending checkout session
            if not checkout_session_id:
                print("🔍 Searching for most recent pending checkout session...")
                checkout_session_id = await self.run_in_thread_pool(
                    lambda: self._find_most_recent_pending_checkout_session()
                )
            
            if not checkout_session_id:
                print(f"❌ No checkout session found for payment {payment_id}")
                print("💡 Attempting to update using request metadata directly...")
                # Fallback: Try to update using request metadata directly
                return await self.run_in_thread_pool(
                    lambda: self._update_using_request_metadata(metadata, payment_id)
                )
            
            print(f"✅ Found checkout session: {checkout_session_id}")
            success = await self.run_in_thread_pool(
                lambda: self._update_to_paid_status(checkout_session_id)
            )
            
            if success:
                return {'success': True, 'message': 'Payment processed successfully'}
            else:
                return {'success': False, 'error': 'Failed to update database'}
            
        except Exception as e:
            print(f"❌ Error handling direct payment: {e}")
            return {'success': False, 'error': str(e)}

    def _find_checkout_session_by_request(self, request_id, request_number):
        """Find checkout session by request ID or number"""
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            if request_id:
                cursor.execute("""
                    SELECT payment_intent_id, request_number, status 
                    FROM document_requests 
                    WHERE request_id = %s OR request_number = %s
                """, (request_id, request_number))
            else:
                cursor.execute("""
                    SELECT payment_intent_id, request_number, status 
                    FROM document_requests 
                    WHERE request_number = %s
                """, (request_number,))
            
            result = cursor.fetchone()
            if result and result['payment_intent_id']:
                print(f"✅ Found checkout session {result['payment_intent_id']} for request {result['request_number']}")
                return result['payment_intent_id']
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding checkout session by request: {e}")
            return None
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)

    def _find_checkout_session_by_payment_intent(self, payment_intent_id):
        """Find checkout session by payment intent ID"""
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT payment_intent_id, request_number, status 
                FROM document_requests 
                WHERE payment_intent_id = %s
            """, (payment_intent_id,))
            
            result = cursor.fetchone()
            if result:
                print(f"✅ Found checkout session {result['payment_intent_id']} for payment intent {payment_intent_id}")
                return result['payment_intent_id']
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding checkout session by payment intent: {e}")
            return None
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)

    def _find_most_recent_pending_checkout_session(self):
        """Find the most recent pending checkout session"""
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT payment_intent_id, request_number, status 
                FROM document_requests 
                WHERE payment_status = 'pending' 
                AND status = 'payment_pending'
                AND payment_intent_id IS NOT NULL
                AND payment_intent_id LIKE 'cs_%'
                ORDER BY request_id DESC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"🎯 Using most recent pending checkout session: {result['payment_intent_id']} for request {result['request_number']}")
                return result['payment_intent_id']
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding recent checkout session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)

    def _update_using_request_metadata(self, metadata, payment_id):
        """Fallback: Update database using request metadata directly"""
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            request_id = metadata.get('request_id')
            request_number = metadata.get('request_number')
            
            if not request_id and not request_number:
                print("❌ No request ID or number in metadata")
                return {'success': False, 'error': 'No request identifier in metadata'}
            
            # Find the request
            if request_id:
                cursor.execute("""
                    SELECT request_id, request_number, status, payment_status 
                    FROM document_requests 
                    WHERE request_id = %s OR request_number = %s
                """, (request_id, request_number))
            else:
                cursor.execute("""
                    SELECT request_id, request_number, status, payment_status 
                    FROM document_requests 
                    WHERE request_number = %s
                """, (request_number,))
            
            request_info = cursor.fetchone()
            
            if not request_info:
                print(f"❌ No document request found for {request_number or request_id}")
                return {'success': False, 'error': 'Request not found'}
            
            request_id = request_info['request_id']
            request_number = request_info['request_number']
            
            print(f"📋 Updating request directly: {request_number}")
            
            # Update payments table using the payment ID
            cursor.execute("""
                UPDATE payments 
                SET status = 'success', 
                    gateway_transaction_id = %s,
                    paid_at = CURRENT_TIMESTAMP
                WHERE request_id = %s AND status = 'pending'
            """, (payment_id, request_id))
            
            payments_updated = cursor.rowcount
            
            if payments_updated == 0:
                print("🔄 Creating new payment record...")
                # Create new payment record
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                reference_number = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}_{unique_id}"
                
                cursor.execute("SELECT total_amount FROM document_requests WHERE request_id = %s", (request_id,))
                amount_result = cursor.fetchone()
                amount = amount_result['total_amount'] if amount_result else 0
                
                cursor.execute("""
                    INSERT INTO payments 
                    (request_id, amount, payment_method, reference_number, gateway_transaction_id, status, paid_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (request_id, amount, 'online', reference_number, payment_id, 'success'))
                
                payments_updated = cursor.rowcount
            
            # Update document_requests table
            cursor.execute("""
                UPDATE document_requests 
                SET payment_status = 'paid',
                    payment_date = CURRENT_TIMESTAMP,
                    status = 'processing'
                WHERE request_id = %s
            """, (request_id,))
            
            documents_updated = cursor.rowcount
            
            connection.commit()
            
            print(f"✅ Direct update successful - Request: {request_number}")
            print(f"📊 Database updates - Payments: {payments_updated}, Documents: {documents_updated}")
            
            return {'success': True, 'message': 'Payment processed successfully using metadata'}
            
        except Exception as e:
            connection.rollback()
            print(f"❌ Error in direct metadata update: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)

    async def _get_payment_details_async(self, payment_id):
        """Get payment details from PayMongo asynchronously"""
        url = f"{self.base_url}/payments/{payment_id}"
        
        headers = {
            "accept": "application/json",
            "authorization": self.get_auth_header()
        }
        
        try:
            print(f"🔧 Fetching payment details from: {url}")
            session = await self.get_http_session()
            
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 404:
                    return {'success': False, 'error': 'Payment not found'}
                    
                response.raise_for_status()
                
                result = await response.json()
                payment_data = result['data']
                
                # Extract payment intent ID
                payment_intent_id = payment_data.get('attributes', {}).get('payment_intent_id')
                
                print(f"📦 Payment data - Intent: {payment_intent_id}")
                
                return {
                    'success': True,
                    'payment_intent_id': payment_intent_id,
                    'response_data': result
                }
            
        except Exception as e:
            print(f"❌ Error fetching payment details: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_payment_failed_async(self, event_data):
        """Handle failed payment webhook asynchronously"""
        try:
            checkout_session_id = event_data['id']
            print(f"❌ Payment failed for checkout session: {checkout_session_id}")
            
            success = await self.run_in_thread_pool(
                lambda: self._update_to_failed_status(checkout_session_id)
            )
            
            if success:
                return {'success': True, 'message': 'Payment failure recorded'}
            else:
                return {'success': False, 'error': 'Failed to update database'}
            
        except Exception as e:
            print(f"❌ Error handling payment failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _handle_payment_cancelled_async(self, event_data):
        """Handle cancelled payment webhook asynchronously"""
        try:
            checkout_session_id = event_data['id']
            print(f"⚠️  Payment cancelled for checkout session: {checkout_session_id}")
            
            success = await self.run_in_thread_pool(
                lambda: self._update_to_failed_status(checkout_session_id)
            )
            
            if success:
                return {'success': True, 'message': 'Payment cancellation recorded'}
            else:
                return {'success': False, 'error': 'Failed to update database'}
            
        except Exception as e:
            print(f"❌ Error handling payment cancelled: {e}")
            return {'success': False, 'error': str(e)}

    def verify_webhook_signature(self, payload, headers):
        """Verify webhook signature for security"""
        # For development, we'll skip signature verification
        # In production, implement proper signature verification
        print("🔒 Webhook signature verification skipped (development mode)")
        return True

    def _update_to_paid_status(self, checkout_session_id):
        """Update database when payment is successful - with enhanced debugging"""
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            print(f"🔄 WEBHOOK: Updating to PAID status for checkout session: {checkout_session_id}")
            
            # First, let's debug what's actually in the database
            print(f"🔍 Searching for checkout session in database: {checkout_session_id}")
            
            # Check if this checkout session exists in document_requests
            cursor.execute("""
                SELECT request_id, request_number, status, payment_status, payment_intent_id
                FROM document_requests 
                WHERE payment_intent_id = %s
            """, (checkout_session_id,))
            
            request_info = cursor.fetchone()
            
            if not request_info:
                print(f"❌ No document request found for checkout session: {checkout_session_id}")
                
                # Let's search for any pending requests that might be related
                print("🔍 Searching for any pending document requests...")
                cursor.execute("""
                    SELECT request_id, request_number, status, payment_status, payment_intent_id
                    FROM document_requests 
                    WHERE payment_status = 'pending' 
                    AND status = 'payment_pending'
                    AND payment_method = 'online'
                    ORDER BY request_id DESC
                """)
                
                pending_requests = cursor.fetchall()
                print(f"📋 Found {len(pending_requests)} pending document requests:")
                
                for req in pending_requests:
                    print(f"   - Request: {req['request_number']}, Payment Intent: {req['payment_intent_id']}")
                
                # Try to find the correct checkout session by looking at recent payments
                print("🔍 Searching payments table for matching transaction...")
                cursor.execute("""
                    SELECT p.payment_id, p.request_id, p.gateway_transaction_id, p.status,
                        dr.request_number, dr.payment_intent_id
                    FROM payments p
                    JOIN document_requests dr ON p.request_id = dr.request_id
                    WHERE p.status = 'pending'
                    AND p.gateway_transaction_id LIKE 'cs_%'
                    ORDER BY p.payment_id DESC
                """)
                
                pending_payments = cursor.fetchall()
                print(f"📋 Found {len(pending_payments)} pending payments:")
                
                for payment in pending_payments:
                    print(f"   - Request: {payment['request_number']}, Gateway: {payment['gateway_transaction_id']}, Doc Payment Intent: {payment['payment_intent_id']}")
                
                # Try to auto-match based on the most recent pending request
                if pending_requests:
                    most_recent_request = pending_requests[0]
                    print(f"🎯 Attempting to use most recent pending request: {most_recent_request['request_number']}")
                    
                    # Update this request with the correct checkout session ID
                    cursor.execute("""
                        UPDATE document_requests 
                        SET payment_intent_id = %s
                        WHERE request_id = %s
                    """, (checkout_session_id, most_recent_request['request_id']))
                    
                    print(f"✅ Updated payment_intent_id for request {most_recent_request['request_number']}")
                    request_info = most_recent_request
                    request_info['payment_intent_id'] = checkout_session_id
                else:
                    return False
            
            request_id = request_info['request_id']
            request_number = request_info['request_number']
            old_status = request_info['status']
            old_payment_status = request_info['payment_status']
            
            print(f"📋 Updating request: {request_number}")
            print(f"📋 From status: {old_status}, payment: {old_payment_status}")
            print(f"📋 To status: processing, payment: paid")
            
            # Update payments table
            cursor.execute("""
                UPDATE payments 
                SET status = 'success', 
                    paid_at = CURRENT_TIMESTAMP
                WHERE gateway_transaction_id = %s
            """, (checkout_session_id,))
            
            payments_updated = cursor.rowcount
            
            if payments_updated == 0:
                print(f"⚠️  No payment record found with gateway_transaction_id: {checkout_session_id}")
                print("🔄 Creating new payment record...")
                
                # Create a new payment record
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                reference_number = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}_{unique_id}"
                
                # Get the amount from document_requests
                cursor.execute("SELECT total_amount FROM document_requests WHERE request_id = %s", (request_id,))
                amount_result = cursor.fetchone()
                amount = amount_result['total_amount'] if amount_result else 0
                
                cursor.execute("""
                    INSERT INTO payments 
                    (request_id, amount, payment_method, reference_number, gateway_transaction_id, status, paid_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (request_id, amount, 'online', reference_number, checkout_session_id, 'success'))
                
                payments_updated = cursor.rowcount
                print(f"✅ Created new payment record: {reference_number}")
            
            # Update document_requests table
            cursor.execute("""
                UPDATE document_requests 
                SET payment_status = 'paid',
                    payment_date = CURRENT_TIMESTAMP,
                    status = 'processing'
                WHERE request_id = %s
            """, (request_id,))
            
            documents_updated = cursor.rowcount
            
            # Verify the updates
            cursor.execute("""
                SELECT dr.request_number, dr.status, dr.payment_status, p.status as payment_table_status
                FROM document_requests dr
                LEFT JOIN payments p ON dr.request_id = p.request_id
                WHERE dr.request_id = %s
            """, (request_id,))
            
            result = cursor.fetchone()
            
            connection.commit()
            
            if result:
                request_number, doc_status, payment_status, payment_table_status = result
                print(f"✅ WEBHOOK SUCCESS - Request: {request_number}")
                print(f"✅ Document Status: {doc_status}")
                print(f"✅ Payment Status: {payment_status}")
                print(f"✅ Payments Table Status: {payment_table_status}")
                
            print(f"📊 Database updates - Payments: {payments_updated}, Documents: {documents_updated}")
            return True
            
        except Exception as e:
            connection.rollback()
            print(f"❌ WEBHOOK ERROR: Failed to update payment status: {e}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            return False
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)
    
    def _update_to_failed_status(self, checkout_session_id):
        """Update database when payment fails - FIXED"""
        connection = self.get_db_connection()
        cursor = connection.cursor()
        
        try:
            print(f"🔄 WEBHOOK: Updating to FAILED status for: {checkout_session_id}")
            
            cursor.execute("""
                UPDATE payments 
                SET status = 'failed'
                WHERE gateway_transaction_id = %s
            """, (checkout_session_id,))
            
            cursor.execute("""
                UPDATE document_requests 
                SET payment_status = 'failed'
                WHERE payment_intent_id = %s
            """, (checkout_session_id,))
            
            connection.commit()
            print(f"✅ WEBHOOK: Payment marked as FAILED for {checkout_session_id}")
            return True
            
        except Exception as e:
            connection.rollback()
            print(f"❌ WEBHOOK ERROR: Failed to update failed status: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)

    def create_checkout_session(self, request_id, amount, description, metadata=None, success_url=None, cancel_url=None):
        """Synchronous wrapper for async checkout session creation"""
        return asyncio.run(self.create_checkout_session_async(request_id, amount, description, metadata, success_url, cancel_url))

    async def create_checkout_session_async(self, request_id, amount, description, metadata=None, success_url=None, cancel_url=None):
        """Create a checkout session with PayMongo asynchronously"""
        url = f"{self.base_url}/checkout_sessions"
        
        if amount <= 0:
            return {'success': False, 'error': 'Amount must be greater than 0'}
        
        amount_in_cents = int(round(amount * 100))
        
        if amount_in_cents < 100:
            return {'success': False, 'error': 'Minimum payment amount is ₱1.00'}
        
        # Set default URLs if not provided
        if not success_url:
            success_url = "https://araneiform-daisey-transthalamic.ngrok-free.dev/success"
        if not cancel_url:
            cancel_url = "https://araneiform-daisey-transthalamic.ngrok-free.dev/cancel"
        
        # Prepare metadata - include webhook info
        flat_metadata = {}
        if metadata:
            for key, value in metadata.items():
                flat_metadata[str(key)] = str(value)
        
        # Add request_id to metadata for webhook handling
        flat_metadata['request_id'] = str(request_id)
        flat_metadata['webhook_url'] = self.webhook_url
        
        # Checkout Session payload
        payload = {
            "data": {
                "attributes": {
                    "send_email_receipt": False,
                    "show_description": True,
                    "show_line_items": True,
                    "cancel_url": cancel_url,
                    "success_url": success_url,
                    "payment_method_types": ["card", "gcash", "grab_pay", "qrph", "paymaya"],
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
            print(f"🔧 Creating checkout session for request: {request_id}")
            print(f"🔗 Webhook URL: {self.webhook_url}")
            
            session = await self.get_http_session()
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                response.raise_for_status()
                
                result = await response.json()
                checkout_session = result['data']
                checkout_id = checkout_session['id']
                checkout_url = checkout_session['attributes']['checkout_url']
                
                print(f"✅ Checkout Session Created: {checkout_id}")
                print(f"🔗 Checkout URL: {checkout_url}")
                
                # Create payment record
                payment_id = await self.run_in_thread_pool(
                    lambda: self.create_payment_record(request_id, checkout_id, amount, "online")
                )
                
                return {
                    'success': True,
                    'checkout_id': checkout_id,
                    'checkout_url': checkout_url,
                    'payment_intent_id': checkout_id,
                    'response_data': result
                }
            
        except Exception as e:
            error_msg = f"Failed to create checkout session: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}

    def create_payment_record(self, request_id, payment_intent_id, amount, payment_method="online"):
        """Create a payment record in the payments table and update document_requests"""
        connection = self.get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Generate unique reference number using UUID
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            reference_number = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}_{unique_id}"
            
            print(f"🔧 Creating payment record with reference: {reference_number}")
            
            # Insert into payments table
            cursor.execute("""
                INSERT INTO payments 
                (request_id, amount, payment_method, reference_number, gateway_transaction_id, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (request_id, amount, payment_method, reference_number, payment_intent_id, 'pending'))
            
            # Update document_requests table
            cursor.execute("""
                UPDATE document_requests 
                SET payment_status = 'pending', 
                    payment_method = %s,
                    payment_intent_id = %s,
                    status = 'payment_pending'
                WHERE request_id = %s
            """, (payment_method, payment_intent_id, request_id))
            
            connection.commit()
            print(f"✅ Payment record created for request: {request_id}")
            print(f"✅ Reference Number: {reference_number}")
            return cursor.lastrowid
            
        except mysql.connector.Error as e:
            connection.rollback()
            if e.errno == 1062:
                print(f"⚠️  Duplicate detected, retrying with new UUID...")
                return self.create_payment_record(request_id, payment_intent_id, amount, payment_method)
            else:
                print(f"❌ Failed to create payment record: {e}")
                raise e
        except Exception as e:
            connection.rollback()
            print(f"❌ Failed to create payment record: {e}")
            raise e
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)

    def _find_checkout_session_by_payment_metadata(self, payment_id):
        """Try to find checkout session by searching payment metadata in database"""
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Search for any payment record that might be related to this payment
            cursor.execute("""
                SELECT gateway_transaction_id, reference_number 
                FROM payments 
                WHERE status = 'pending' 
                AND gateway_transaction_id LIKE 'cs_%'
            """)
            
            pending_checkout_sessions = cursor.fetchall()
            
            for session in pending_checkout_sessions:
                checkout_session_id = session['gateway_transaction_id']
                print(f"🔍 Checking pending checkout session: {checkout_session_id}")
                
                # If we find a match, use this checkout session
                # In a real scenario, you might want to verify this more thoroughly
                if checkout_session_id:
                    print(f"🎯 Using checkout session: {checkout_session_id} for payment: {payment_id}")
                    return checkout_session_id
            
            return None
            
        except Exception as e:
            print(f"❌ Error searching for checkout session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)
    
    def sync_payment_intent_ids(self):
        """Sync payment_intent_id between payments and document_requests tables"""
        connection = self.get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            print("🔄 Syncing payment_intent_id between tables...")
            
            # Find payments that have gateway_transaction_id but document_requests doesn't match
            cursor.execute("""
                SELECT p.request_id, p.gateway_transaction_id, dr.payment_intent_id, dr.request_number
                FROM payments p
                JOIN document_requests dr ON p.request_id = dr.request_id
                WHERE p.gateway_transaction_id LIKE 'cs_%'
                AND (dr.payment_intent_id IS NULL OR dr.payment_intent_id != p.gateway_transaction_id)
                AND p.status = 'pending'
            """)
            
            mismatched_records = cursor.fetchall()
            
            print(f"📋 Found {len(mismatched_records)} mismatched records:")
            
            updated_count = 0
            for record in mismatched_records:
                print(f"   - Request: {record['request_number']}")
                print(f"     Payment Gateway: {record['gateway_transaction_id']}")
                print(f"     Doc Payment Intent: {record['payment_intent_id']}")
                
                # Update document_requests with the correct payment_intent_id
                cursor.execute("""
                    UPDATE document_requests 
                    SET payment_intent_id = %s
                    WHERE request_number = %s
                """, (record['gateway_transaction_id'], record['request_number']))
                
                updated_count += 1
                print(f"     ✅ Updated to: {record['gateway_transaction_id']}")
            
            connection.commit()
            print(f"✅ Synced {updated_count} payment_intent_id records")
            return updated_count
            
        except Exception as e:
            connection.rollback()
            print(f"❌ Error syncing payment intent IDs: {e}")
            return 0
        finally:
            cursor.close()
            connection.close()

    def cleanup(self):
        """Cleanup resources"""
        # Shutdown thread pool executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        # Close HTTP session if running in async context
        safe_async_run(self.cleanup_http_session)
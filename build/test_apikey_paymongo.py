# test_paymongo_payment_fixed.py
from payment_processor import PayMongoProcessor
from config import DB_CONFIG
import mysql.connector

def get_actual_request_ids():
    """Get actual request IDs from the database"""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id, request_number, document_name, total_amount 
        FROM document_requests 
        WHERE status = 'payment_pending' 
        LIMIT 2
    """)
    
    requests = cursor.fetchall()
    cursor.close()
    connection.close()
    
    print("📋 Available document requests in database:")
    for req in requests:
        print(f"   ID: {req['id']}, Request#: {req['request_number']}, Document: {req['document_name']}, Amount: ₱{req['total_amount']:.2f}")
    
    return requests

def test_payment_creation():
    print("🧪 Testing PayMongo Payment Creation - WITH REAL REQUESTS")
    print("=" * 50)
    
    # Get actual requests from database
    actual_requests = get_actual_request_ids()
    
    if not actual_requests:
        print("❌ No payment_pending requests found in database!")
        print("   Please create some document requests first.")
        return
    
    processor = PayMongoProcessor()
    
    for i, request in enumerate(actual_requests, 1):
        print(f"\n📦 Test Case {i} (Real Request):")
        print(f"   Request ID: {request['id']}")
        print(f"   Request#: {request['request_number']}")
        print(f"   Amount: ₱{request['total_amount']:.2f}")
        print(f"   Document: {request['document_name']}")
        
        # FLAT metadata (no nested objects)
        metadata = {
            'request_id': str(request['id']),
            'request_number': request['request_number'],
            'document_name': request['document_name'],
            'payment_type': 'document_request'
        }
        
        result = processor.create_payment_intent(
            request_id=request['id'],  # Use actual ID from database
            amount=request['total_amount'],
            description=f"Document Request: {request['document_name']} - {request['request_number']}",
            metadata=metadata
        )
        
        if result['success']:
            print(f"✅ SUCCESS: Payment intent created!")
            print(f"   ID: {result['payment_intent_id']}")
            print(f"   URL: {result['payment_url']}")
            
            # Test creating payment record
            try:
                payment_id = processor.create_payment_record(
                    request_id=request['id'],  # Use actual ID
                    payment_intent_id=result['payment_intent_id'],
                    amount=request['total_amount']
                )
                print(f"   Database Record Created: {payment_id}")
            except Exception as e:
                print(f"❌ Database record failed: {e}")
        else:
            print(f"❌ FAILED: {result['error']}")

if __name__ == "__main__":
    test_payment_creation()
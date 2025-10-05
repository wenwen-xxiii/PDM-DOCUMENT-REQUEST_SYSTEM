from flask import Flask, request, jsonify
import json
from payment_processor import PayMongoProcessor

app = Flask(__name__)
payment_processor = PayMongoProcessor()

@app.route('/webhook/paymongo', methods=['GET', 'POST'])
def handle_paymongo_webhook():
    """Handle PayMongo webhook events (both GET and POST)"""
    try:
        if request.method == 'GET':
            # PayMongo is testing the webhook URL or it's a browser request
            print("🔔 GET request received - Webhook endpoint is active")
            return jsonify({
                'status': 'active',
                'message': 'PDM Document System Webhook Server is running',
                'service': 'PDM Document Request System',
                'webhook_url': 'https://araneiform-daisey-transthalamic.ngrok-free.dev/webhook/paymongo'
            }), 200
        
        elif request.method == 'POST':
            # Actual webhook event from PayMongo
            raw_payload = request.get_data(as_text=True)
            payload = request.json
            headers = dict(request.headers)
            
            print(f"🔔 Webhook received from PayMongo")
            print(f"📧 Event Type: {payload['data']['attributes']['type'] if payload else 'Unknown'}")
            
            # Process the webhook
            result = payment_processor.handle_webhook_event(payload, headers)
            
            if result['success']:
                print(f"✅ Webhook processed successfully")
                return jsonify({'status': 'success'}), 200
            else:
                print(f"❌ Webhook processing failed: {result.get('error')}")
                return jsonify({'status': 'error', 'message': result.get('error')}), 400
            
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/success')
def success_page():
    """Success page after payment"""
    return """
    <html>
        <head>
            <title>Payment Successful - PDM Document System</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
                h1 { color: #28a745; margin-bottom: 20px; }
                p { color: #666; margin-bottom: 30px; line-height: 1.6; }
                .button { padding: 12px 30px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; }
                .button:hover { background: #218838; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ Payment Successful!</h1>
                <p>Your payment has been processed successfully and your document request is now being processed.</p>
                <p>You can close this window and return to the PDM Document Request System.</p>
                <button class="button" onclick="window.close()">Close Window</button>
            </div>
        </body>
    </html>
    """

@app.route('/cancel')
def cancel_page():
    """Cancel page when payment is cancelled"""
    return """
    <html>
        <head>
            <title>Payment Cancelled - PDM Document System</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
                h1 { color: #ffc107; margin-bottom: 20px; }
                p { color: #666; margin-bottom: 30px; line-height: 1.6; }
                .button { padding: 12px 30px; background: #ffc107; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; }
                .button:hover { background: #e0a800; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ Payment Cancelled</h1>
                <p>Your payment was cancelled. No charges have been made to your account.</p>
                <p>You can close this window and try again in the PDM Document Request System.</p>
                <button class="button" onclick="window.close()">Close Window</button>
            </div>
        </body>
    </html>
    """

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'PDM Document System Webhook Server',
        'webhook_url': 'https://araneiform-daisey-transthalamic.ngrok-free.dev/webhook/paymongo',
        'endpoints': {
            'webhook': '/webhook/paymongo (GET/POST)',
            'health': '/health (GET)',
            'success': '/success (GET)',
            'cancel': '/cancel (GET)'
        }
    }), 200

@app.route('/')
def home():
    """Home page"""
    return """
    <html>
        <head>
            <title>PDM Document System - Webhook Server</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }
                h1 { color: #792D1B; margin-bottom: 20px; }
                .status { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 20px 0; }
                .endpoint { text-align: left; background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .method { display: inline-block; background: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin-right: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏫 PDM Document System</h1>
                <h2>Webhook Server</h2>
                
                <div class="status">
                    <strong>✅ Server is running</strong>
                </div>
                
                <p>This server handles payment webhooks from PayMongo for the PDM Document Request System.</p>
                
                <h3>Available Endpoints:</h3>
                
                <div class="endpoint">
                    <span class="method">GET/POST</span>
                    <strong>/webhook/paymongo</strong><br>
                    <small>PayMongo webhook endpoint for payment notifications</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span>
                    <strong>/health</strong><br>
                    <small>Health check endpoint</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span>
                    <strong>/success</strong><br>
                    <small>Payment success page</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span>
                    <strong>/cancel</strong><br>
                    <small>Payment cancellation page</small>
                </div>
                
                <p><small>Server time: """ + str(__import__('datetime').datetime.now()) + """</small></p>
            </div>
        </body>
    </html>
    """

if __name__ == '__main__':
    print("🚀 Starting PDM Document System Webhook Server...")
    print("🔗 Webhook URL: https://araneiform-daisey-transthalamic.ngrok-free.dev/webhook/paymongo")
    print("🏠 Home Page: https://araneiform-daisey-transthalamic.ngrok-free.dev/")
    print("✅ Success Page: https://araneiform-daisey-transthalamic.ngrok-free.dev/success")
    print("❌ Cancel Page: https://araneiform-daisey-transthalamic.ngrok-free.dev/cancel")
    print("❤️  Health Check: https://araneiform-daisey-transthalamic.ngrok-free.dev/health")
    print("\n📋 Make sure to configure PayMongo webhook with the URL above")
    app.run(host='0.0.0.0', port=5000, debug=True)
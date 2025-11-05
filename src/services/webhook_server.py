from quart import Quart, request, jsonify
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from services.payment_processor import PayMongoProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)
payment_processor = PayMongoProcessor()

# Global session for HTTP requests
http_session = None

async def get_http_session():
    """Get or create HTTP session"""
    global http_session
    if http_session is None:
        http_session = aiohttp.ClientSession()
    return http_session

async def cleanup_session():
    """Cleanup HTTP session"""
    global http_session
    if http_session:
        await http_session.close()
        http_session = None

@app.route('/webhook/paymongo', methods=['GET', 'POST'])
async def handle_paymongo_webhook():
    """Handle PayMongo webhook events (both GET and POST) asynchronously"""
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
            raw_payload = await request.get_data(as_text=True)
            payload = await request.get_json()
            headers = dict(request.headers)
            
            print(f"🔔 Webhook received from PayMongo")
            print(f"📧 Event Type: {payload['data']['attributes']['type'] if payload else 'Unknown'}")
            
            # Process the webhook asynchronously
            result = await process_webhook_async(payload, headers)
            
            if result['success']:
                print(f"✅ Webhook processed successfully")
                return jsonify({'status': 'success'}), 200
            else:
                print(f"❌ Webhook processing failed: {result.get('error')}")
                return jsonify({'status': 'error', 'message': result.get('error')}), 400
            
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

async def process_webhook_async(payload, headers):
    """Process webhook event asynchronously"""
    try:
        # Log webhook event
        logger.info(f"Processing webhook event: {payload.get('data', {}).get('attributes', {}).get('type', 'Unknown')}")
        
        # Run payment processor in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            payment_processor.handle_webhook_event, 
            payload, 
            headers
        )
        
        # Log result
        if result['success']:
            logger.info("Webhook processed successfully")
        else:
            logger.error(f"Webhook processing failed: {result.get('error')}")
            
        return result
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.before_serving
async def startup():
    """Startup tasks"""
    logger.info("Starting async webhook server...")
    await get_http_session()

@app.after_serving
async def shutdown():
    """Shutdown tasks"""
    logger.info("Shutting down async webhook server...")
    await cleanup_session()

@app.route('/success')
async def success_page():
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
async def cancel_page():
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
async def health_check():
    """Health check endpoint with async capabilities"""
    try:
        # Test database connection (if needed)
        health_status = {
            'status': 'healthy',
            'service': 'PDM Document System Async Webhook Server',
            'timestamp': datetime.now().isoformat(),
            'webhook_url': 'https://araneiform-daisey-transthalamic.ngrok-free.dev/webhook/paymongo',
            'endpoints': {
                'webhook': '/webhook/paymongo (GET/POST)',
                'health': '/health (GET)',
                'success': '/success (GET)',
                'cancel': '/cancel (GET)'
            },
            'async_features': {
                'webhook_processing': 'async',
                'http_session': 'active' if http_session else 'inactive',
                'thread_pool': 'available'
            }
        }
        
        # Test external connectivity (optional)
        try:
            session = await get_http_session()
            async with session.get('https://httpbin.org/get', timeout=5) as response:
                if response.status == 200:
                    health_status['external_connectivity'] = 'ok'
                else:
                    health_status['external_connectivity'] = 'limited'
        except Exception as e:
            health_status['external_connectivity'] = f'error: {str(e)}'
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/')
async def home():
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
                    <strong>✅ Async Server is running</strong>
                </div>
                
                <p>This async server handles payment webhooks from PayMongo for the PDM Document Request System with improved performance and non-blocking operations.</p>
                
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

async def startup_tasks():
    """Async startup tasks"""
    print("🚀 Starting PDM Document System Async Webhook Server...")
    print("🔗 Webhook URL: https://araneiform-daisey-transthalamic.ngrok-free.dev/webhook/paymongo")
    print("🏠 Home Page: https://araneiform-daisey-transthalamic.ngrok-free.dev/")
    print("✅ Success Page: https://araneiform-daisey-transthalamic.ngrok-free.dev/success")
    print("❌ Cancel Page: https://araneiform-daisey-transthalamic.ngrok-free.dev/cancel")
    print("❤️  Health Check: https://araneiform-daisey-transthalamic.ngrok-free.dev/health")
    print("\n📋 Make sure to configure PayMongo webhook with the URL above")
    print("⚡ Server is running in async mode for better performance")

if __name__ == '__main__':
    # Run startup tasks
    asyncio.run(startup_tasks())
    
    # Start the async server
    app.run(host='0.0.0.0', port=5000, debug=True)
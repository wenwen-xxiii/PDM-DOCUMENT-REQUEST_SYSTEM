from webhook_server import app

if __name__ == '__main__':
    print("🚀 PDM Document System - Webhook Server")
    print("=" * 50)
    print("🔗 Webhook URL: https://araneiform-daisey-transthalamic.ngrok-free.dev/webhook/paymongo")
    print("📋 Next steps:")
    print("1. Make sure ngrok is running on port 5000")
    print("2. Configure PayMongo webhook with the URL above")
    print("3. Select events: checkout_session.payment.paid, checkout_session.payment.failed")
    print("4. Test the system!")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
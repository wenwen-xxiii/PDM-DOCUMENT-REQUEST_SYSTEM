import subprocess
import time
import requests
import threading
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import NGROK_CONFIG

class NgrokManager:
    def __init__(self):
        self.process = None
        self.public_url = None
        self.is_running = False
        
    def start_ngrok(self, port=None):
        """Start ngrok tunnel with better error handling"""
        if port is None:
            port = NGROK_CONFIG.get('port', 5000)
            
        try:
            print("🚀 Starting ngrok tunnel...")
            
            # Start ngrok in the background
            self.process = subprocess.Popen(
                ['ngrok', 'http', str(port)], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.is_running = True
            
            # Wait for ngrok to start and get URL
            self.public_url = self._wait_for_ngrok_url()
            
            if self.public_url:
                print(f"✅ Ngrok tunnel started: {self.public_url}")
                return self.public_url
            else:
                print("❌ Failed to get ngrok URL")
                return None
                
        except FileNotFoundError:
            print("❌ Ngrok not found. Please install ngrok and make sure it's in your PATH.")
            return None
        except Exception as e:
            print(f"❌ Failed to start ngrok: {e}")
            return None
    
    def _wait_for_ngrok_url(self, max_attempts=10):
        """Wait for ngrok to be ready and return the public URL"""
        for attempt in range(max_attempts):
            try:
                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    if tunnels:
                        public_url = tunnels[0]['public_url']
                        return public_url
                
                time.sleep(1)  # Wait before retrying
                
            except requests.exceptions.ConnectionError:
                if attempt < max_attempts - 1:
                    time.sleep(1)  # Ngrok might not be ready yet
                    continue
                else:
                    print("❌ Could not connect to ngrok API. Is ngrok running?")
                    return None
            except Exception as e:
                print(f"❌ Error getting ngrok URL: {e}")
                return None
        
        print("❌ Timed out waiting for ngrok URL")
        return None
    
    def stop_ngrok(self):
        """Stop the ngrok process"""
        if self.process:
            print("🛑 Stopping ngrok tunnel...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.is_running = False
            self.public_url = None
            print("✅ Ngrok tunnel stopped")
    
    def get_webhook_url(self, endpoint="/webhook/paymongo"):
        """Get the full webhook URL"""
        if self.public_url:
            return f"{self.public_url}{endpoint}"
        return None
    
    def is_ngrok_ready(self):
        """Check if ngrok is ready and return the URL"""
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                if tunnels:
                    return tunnels[0]['public_url']
        except:
            pass
        return None

# Global ngrok manager instance
ngrok_manager = NgrokManager()

def start_ngrok_tunnel(port=None):
    """Start ngrok tunnel and return webhook URL"""
    global ngrok_manager
    
    # First check if ngrok is already running
    existing_url = ngrok_manager.is_ngrok_ready()
    if existing_url:
        print(f"✅ Using existing ngrok tunnel: {existing_url}")
        ngrok_manager.public_url = existing_url
        ngrok_manager.is_running = True
        return ngrok_manager.get_webhook_url()
    
    # Start new tunnel
    public_url = ngrok_manager.start_ngrok(port)
    if public_url:
        return ngrok_manager.get_webhook_url()
    return None

def stop_ngrok_tunnel():
    """Stop the ngrok tunnel"""
    global ngrok_manager
    ngrok_manager.stop_ngrok()

def get_webhook_url():
    """Get the current webhook URL"""
    global ngrok_manager
    return ngrok_manager.get_webhook_url()

# Example usage with your PayMongo config
def setup_webhooks():
    """Setup webhooks for payment processing"""
    webhook_url = start_ngrok_tunnel()
    
    if webhook_url:
        print(f"🔗 Webhook URL: {webhook_url}")
        
        # Update PayMongo configuration
        from config.config import PAYMONGO_CONFIG
        if PAYMONGO_CONFIG:
            PAYMONGO_CONFIG['webhook_url'] = webhook_url
        
        return webhook_url
    else:
        print("❌ Failed to setup webhooks")
        return None

# Auto-start ngrok when this module is imported (optional)
if __name__ == "__main__":
    # Test ngrok functionality
    url = setup_webhooks()
    if url:
        print(f"✅ Webhook setup complete: {url}")
        
        # Keep the script running to maintain the tunnel
        try:
            print("📡 Ngrok tunnel is active. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping ngrok...")
            stop_ngrok_tunnel()
    else:
        print("❌ Webhook setup failed")
        sys.exit(1)
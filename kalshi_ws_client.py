import asyncio
import json
import time
import hmac
import hashlib
import base64
import os
import websockets
from typing import Dict, List, Optional, Callable, Any
from dotenv import load_dotenv

load_dotenv()

class KalshiWSClient:
    """
    WebSocket client for Kalshi API v2.
    Handles authentication, heartbeats, and channel subscriptions.
    """
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("KALSHI_API_KEY")
        self.api_secret = os.getenv("KALSHI_API_SECRET")
        print(f"DEBUG: API Key present: {bool(self.api_key)}")
        print(f"DEBUG: API Secret present: {bool(self.api_secret)}")
        # Production WS URL: wss://api.elections.kalshi.com/trade-api/ws/v2
        # Demo WS URL: wss://demo-api.kalshi.co/trade-api/ws/v2
        base_url = os.getenv("KALSHI_API_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")
        if "demo" in base_url:
            self.ws_url = "wss://demo-api.kalshi.co/trade-api/ws/v2"
        else:
            self.ws_url = "wss://api.elections.kalshi.com/trade-api/ws/v2"
            
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: Dict[str, List[str]] = {}
        self.handlers: Dict[str, List[Callable[[Dict], Any]]] = {}
        self.is_running = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60

    def _get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers for WebSocket handshake."""
        timestamp = str(int(time.time() * 1000))
        # Message for WS signature: timestamp + method + path
        # Documentation says: timestamp + "GET" + "/trade-api/ws/v2"
        # We need to make sure the path matches exactly what the server expects
        path = "/trade-api/ws/v2"
        msg = timestamp + "GET" + path
        
        # If the secret is a file path, read it
        secret = self.api_secret
        if os.path.isfile(secret):
            with open(secret, 'r') as f:
                secret = f.read()
        
        secret = secret.strip()
        # If it contains spaces, it's likely a single-line string that needs to be space-separated
        if " " in secret and not secret.startswith("-----BEGIN"):
            secret = secret.replace(" ", "")

        if not secret.startswith("-----BEGIN"):
            # If it's a raw base64 string, wrap it in PEM headers
            # Note: For PKCS#1 (RSA), the header is different from PKCS#8
            if len(secret) > 1000: # Likely an RSA key
                secret = f"-----BEGIN RSA PRIVATE KEY-----\n{secret}\n-----END RSA PRIVATE KEY-----"
        
        # Ensure the key is properly formatted with newlines
        if secret.startswith("-----BEGIN"):
            # Remove any existing headers/footers to re-wrap
            content = secret.replace("-----BEGIN RSA PRIVATE KEY-----", "") \
                            .replace("-----END RSA PRIVATE KEY-----", "") \
                            .replace("-----BEGIN PRIVATE KEY-----", "") \
                            .replace("-----END PRIVATE KEY-----", "") \
                            .replace("\n", "").replace(" ", "").strip()
            
            # Wrap body to 64 chars
            wrapped_body = '\n'.join([content[i:i+64] for i in range(0, len(content), 64)])
            # Try RSA PRIVATE KEY first as it's common for Kalshi keys
            secret = f"-----BEGIN RSA PRIVATE KEY-----\n{wrapped_body}\n-----END RSA PRIVATE KEY-----"

        # HMAC-SHA256 signature
        # Note: Kalshi V2 uses RSA-PSS for signatures with a PEM private key,
        # not HMAC-SHA256. The kalshi_client.py uses the official SDK or a custom auth.
        # Let's check how kalshi_client.py handles it.
        
        # If we have the official SDK, we should use its signing logic.
        # Otherwise, we need to implement RSA-PSS signing.
        
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import serialization
            
            private_key = serialization.load_pem_private_key(
                secret.encode('utf-8'),
                password=None
            )
            
            # Kalshi V2 uses standard RSA-PSS signing
            signature = private_key.sign(
                msg.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            signature_b64 = base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            # If it's not a PEM, it might be a raw key for HMAC (though unlikely for V2)
            # Or the PEM is malformed.
            print(f"DEBUG: RSA signing failed: {e}")
            signature = hmac.new(
                secret.encode('utf-8'),
                msg.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature_b64,
            "KALSHI-ACCESS-TIMESTAMP": timestamp
        }

    async def connect(self):
        """Establish WebSocket connection with authentication."""
        print(f"DEBUG: Attempting to connect to {self.ws_url}")
        headers = self._get_auth_headers()
        print(f"DEBUG: Handshake headers: {list(headers.keys())}")
        try:
            # Use additional_headers instead of extra_headers for newer websockets versions
            # and ensure we catch connection errors properly
            self.ws = await websockets.connect(self.ws_url, additional_headers=headers)
            print(f"Connected to Kalshi WebSocket at {self.ws_url}")
            self.is_running = True
            self._reconnect_delay = 1
            # Start message listener
            asyncio.create_task(self._listen())
            # Re-subscribe to existing channels if any
            await self._resubscribe()
        except Exception as e:
            print(f"Connection failed: {e}")
            if self.is_running: # Only reconnect if we haven't been stopped
                await self._handle_reconnect()

    async def _listen(self):
        """Listen for incoming messages and handle heartbeats."""
        try:
            async for message in self.ws:
                # Debug: Print raw message type
                if isinstance(message, str):
                    if message == "heartbeat":
                        continue
                    try:
                        data = json.loads(message)
                    except:
                        print(f"DEBUG WS: Received non-JSON string: {message[:100]}")
                        continue
                else:
                    data = message
                
                if not isinstance(data, dict):
                    continue
                
                # Kalshi uses "type" field instead of "channel"
                msg_type = data.get("type")
                
                # Route to handlers based on message type
                if msg_type in self.handlers:
                    for handler in self.handlers[msg_type]:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
        except websockets.ConnectionClosed:
            print("WebSocket connection closed")
            self.is_running = False
            await self._handle_reconnect()
        except Exception as e:
            print(f"Error in WebSocket listener: {e}")
            self.is_running = False
            await self._handle_reconnect()

    async def _handle_reconnect(self):
        """Reconnect with exponential backoff."""
        if not self.is_running:
            print(f"Reconnecting in {self._reconnect_delay} seconds...")
            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
            await self.connect()

    async def subscribe(self, channel: str, tickers: List[str], handler: Callable[[Dict], Any]):
        """Subscribe to a channel for specific tickers."""
        if channel not in self.handlers:
            self.handlers[channel] = []
        self.handlers[channel].append(handler)
        
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        
        new_tickers = [t for t in tickers if t not in self.subscriptions[channel]]
        if new_tickers:
            self.subscriptions[channel].extend(new_tickers)
            if self.ws:
                subscribe_msg = {
                    "id": int(time.time()),
                    "cmd": "subscribe",
                    "params": {
                        "channels": [channel],
                        "market_tickers": new_tickers
                    }
                }
                await self.ws.send(json.dumps(subscribe_msg))

    async def _resubscribe(self):
        """Re-subscribe to all active channels after reconnection."""
        if not self.subscriptions:
            return
        
        for channel, tickers in self.subscriptions.items():
            subscribe_msg = {
                "id": int(time.time()),
                "cmd": "subscribe",
                "params": {
                    "channels": [channel],
                    "market_tickers": tickers
                }
            }
            await self.ws.send(json.dumps(subscribe_msg))

    async def stop(self):
        """Stop the WebSocket client."""
        self.is_running = False
        if self.ws:
            await self.ws.close()

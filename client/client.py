# client.py
import socket
import json
import threading
from crypto_utils import CryptoUtils
from gui import ChatGUI

class ChatClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.username = None
        self.crypto = CryptoUtils()
        self.gui = None
        self.receiving = False
        
    def set_gui(self, gui):
        """Set the GUI reference"""
        self.gui = gui
        
    def connect(self, host, port, username):
        """Connect to the chat server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            self.username = username
            
            # Generate RSA keys
            self.crypto.generate_rsa_keys()
            public_key_pem = self.crypto.get_public_key_pem().decode()
            
            # Send handshake
            handshake = {
                "type": "handshake",
                "username": username,
                "public_key": public_key_pem
            }
            self._send_json(handshake)
            
            # Start receiving thread
            self.receiving = True
            threading.Thread(target=self._receive_messages, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from server"""
        self.receiving = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
    def _send_json(self, data):
        """Send JSON data to server"""
        try:
            json_data = json.dumps(data)
            self.socket.sendall(json_data.encode() + b'\n')
        except Exception as e:
            print(f"Send error: {e}")
            self.disconnect()
            
    def send_message(self, message):
        """Send chat message to server"""
        if not self.connected:
            return
            
        print(f"Attempting to send message. Fernet available: {self.crypto.fernet is not None}")
        
        # Encrypt message if symmetric key is available
        if self.crypto.fernet:
            try:
                encrypted_msg = self.crypto.encrypt_message(message)
                payload = {
                    "type": "message",
                    "message": encrypted_msg,
                    "encrypted": True
                }
                print("Message encrypted successfully")
            except Exception as e:
                print(f"Encryption error: {e}")
                # Fallback to unencrypted
                payload = {
                    "type": "message", 
                    "message": message,
                    "encrypted": False
                }
        else:
            print("No symmetric key available, sending unencrypted")
            payload = {
                "type": "message",
                "message": message,
                "encrypted": False
            }
            
        self._send_json(payload)
        
    def _receive_messages(self):
        """Receive messages from server"""
        buffer = ""
        while self.receiving:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self._process_message(line)
                    
            except Exception as e:
                if self.receiving:
                    print(f"Receive error: {e}")
                break
                
        self.disconnect()
        if self.gui:
            self.gui.root.after(0, lambda: self.gui.display_message("System", "Disconnected from server"))
            
    def _process_message(self, message_data):
        """Process incoming message"""
        try:
            data = json.loads(message_data)
            msg_type = data.get("type")
            
            if msg_type == "key_exchange":
                self._handle_key_exchange(data)
            elif msg_type == "user_list":
                if self.gui:
                    self.gui.root.after(0, lambda: self.gui.update_users_list(data["users"]))
            elif msg_type == "message":
                self._handle_chat_message(data)
            elif msg_type == "system":
                if self.gui:
                    self.gui.root.after(0, lambda: self.gui.display_message("System", data["message"]))
                    
        except json.JSONDecodeError as e:
            print(f"Invalid JSON received: {e}")
            
    def _handle_key_exchange(self, data):
        """Handle symmetric key exchange"""
        try:
            encrypted_key = data["encrypted_key"]
            print(f"Received encrypted key: {encrypted_key[:50]}...")
            
            # Decrypt the symmetric key
            decrypted_key = self.crypto.decrypt_with_private_key(encrypted_key)
            print(f"Decrypted key length: {len(decrypted_key)}")
            
            # Import the symmetric key
            self.crypto.import_symmetric_key(decrypted_key)
            print("Symmetric key imported successfully")
            
            if self.gui:
                self.gui.root.after(0, lambda: self.gui.display_message("System", "Secure connection established! You can now send encrypted messages."))
                
        except Exception as e:
            print(f"Key exchange error: {e}")
            import traceback
            traceback.print_exc()
            
    def _handle_chat_message(self, data):
        """Handle incoming chat message"""
        sender = data.get("sender", "Unknown")
        message = data["message"]
        encrypted = data.get("encrypted", False)
        
        if self.gui:
            if encrypted and self.crypto.fernet:
                try:
                    decrypted_msg = self.crypto.decrypt_message(message)
                    self.gui.root.after(0, lambda: self.gui.display_message(sender, decrypted_msg))
                except Exception as e:
                    print(f"Decryption error: {e}")
                    self.gui.root.after(0, lambda: self.gui.display_message(sender, f"[Decryption failed: {message}]", True))
            else:
                self.gui.root.after(0, lambda: self.gui.display_message(sender, message, encrypted))

def main():
    client = ChatClient()
    gui = ChatGUI(client)
    client.set_gui(gui)
    gui.run()

if __name__ == "__main__":
    main()
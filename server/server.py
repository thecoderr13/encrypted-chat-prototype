# server.py

import socket
import threading
import json
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from user_manager import UserManager
from shared.protocol import Protocol

class ChatServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.user_manager = UserManager()
        # Generate a global symmetric key for the chat room
        self.symmetric_key = Fernet.generate_key()
        print(f"Server symmetric key generated: {self.symmetric_key[:20]}...")
        
    def start(self):
        """Start the chat server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"Chat server started on {self.host}:{self.port}")
            print("Waiting for connections...")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    print(f"New connection from {address}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error:
                    if self.running:
                        print("Socket error occurred")
                    break
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("Server stopped")
        
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        buffer = ""
        username = None
        
        try:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():  # Ignore empty lines
                        username = self.process_client_message(line, client_socket, username)
                        
        except Exception as e:
            print(f"Client handling error from {address}: {e}")
        finally:
            if username:
                self.user_manager.remove_user(username)
                # Notify all users
                self.user_manager.broadcast_user_list()
                leave_msg = json.dumps({
                    "type": "system",
                    "message": f"{username} has left the chat"
                })
                self.user_manager.broadcast(leave_msg)
                print(f"User {username} disconnected")
                
            client_socket.close()
            
    def process_client_message(self, message_data, client_socket, current_username):
        """Process message from client"""
        try:
            data = json.loads(message_data)
            msg_type = data.get("type")
            
            if msg_type == "handshake" and not current_username:
                return self.handle_handshake(data, client_socket)
            elif msg_type == "message" and current_username:
                self.handle_chat_message(data, current_username)
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from client: {e}")
            
        return current_username
        
    def handle_handshake(self, data, client_socket):
        """Handle client handshake and registration"""
        username = data["username"]
        public_key_pem = data["public_key"]
        
        # Add user to manager
        if self.user_manager.add_user(username, client_socket, public_key_pem):
            print(f"User {username} registered successfully")
            
            # Send welcome message first
            welcome_msg = json.dumps({
                "type": "system", 
                "message": "Welcome to the secure chat! Establishing secure connection..."
            })
            client_socket.sendall((welcome_msg + '\n').encode())
            
            # Encrypt symmetric key with user's public key
            try:
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode(),
                    backend=default_backend()
                )
                
                print(f"Encrypting symmetric key for {username}")
                encrypted_key = public_key.encrypt(
                    self.symmetric_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                encrypted_key_b64 = base64.b64encode(encrypted_key).decode()
                print(f"Encrypted key length: {len(encrypted_key_b64)}")
                
                # Send key exchange message
                key_exchange_msg = json.dumps({
                    "type": "key_exchange",
                    "encrypted_key": encrypted_key_b64
                })
                client_socket.sendall((key_exchange_msg + '\n').encode())
                print(f"Key exchange sent to {username}")
                
                # Send connection established message
                secure_msg = json.dumps({
                    "type": "system",
                    "message": "Secure connection established! You can now send encrypted messages."
                })
                client_socket.sendall((secure_msg + '\n').encode())
                
            except Exception as e:
                print(f"Key encryption error for {username}: {e}")
                import traceback
                traceback.print_exc()
                error_msg = json.dumps({
                    "type": "system",
                    "message": "Error establishing secure connection"
                })
                client_socket.sendall((error_msg + '\n').encode())
                return username
            
            # Update all users with new user list
            self.user_manager.broadcast_user_list()
            
            # Broadcast join message to all OTHER users
            join_msg = json.dumps({
                "type": "system", 
                "message": f"{username} has joined the chat"
            })
            self.user_manager.broadcast(join_msg, exclude_user=username)
            
            return username
        else:
            error_msg = json.dumps({
                "type": "system",
                "message": "Username already taken"
            })
            client_socket.sendall((error_msg + '\n').encode())
            return None
            
    def handle_chat_message(self, data, username):
        """Handle incoming chat message"""
        message = data["message"]
        encrypted = data.get("encrypted", False)
        
        print(f"Received message from {username}: {message[:50]}... (encrypted: {encrypted})")
        
        # Broadcast message to all OTHER users
        chat_msg = json.dumps({
            "type": "message",
            "sender": username,
            "message": message,
            "encrypted": encrypted
        })
        
        disconnected = self.user_manager.broadcast(chat_msg, exclude_user=username)
        
        # Also send the message back to the sender so they can see their own message
        self.user_manager.send_to_user(username, chat_msg)
        
        # Update user list if any users disconnected
        if disconnected:
            self.user_manager.broadcast_user_list()

def main():
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()

if __name__ == "__main__":
    main()
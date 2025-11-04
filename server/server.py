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

from shared import protocol


from user_manager import UserManager
from shared.protocol import Protocol

class ChatServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.user_manager = UserManager()
        self.symmetric_key = Fernet.generate_key()
        self.fernet = Fernet(self.symmetric_key)
        
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
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
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
        
    def handle_client(self, client_socket):
        """Handle individual client connection"""
        buffer = ""
        username = None
        
        try:
            while self.running:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                    
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    response, username = self.process_client_message(line, client_socket, username)
                    if response:
                        client_socket.sendall((response + '\n').encode())
                        
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            if username:
                self.user_manager.remove_user(username)
                # Notify other users
                user_list = self.user_manager.get_all_users()
                broadcast_msg = json.dumps(Protocol.create_user_list(user_list))
                self.user_manager.broadcast(broadcast_msg)
                self.user_manager.broadcast(
                    json.dumps(Protocol.create_system_message(f"{username} has left the chat"))
                )
                print(f"User {username} disconnected")
                
            client_socket.close()
            
    def process_client_message(self, message_data, client_socket, current_username):
        """Process message from client"""
        try:
            data = json.loads(message_data)
            msg_type = data.get("type")
            
            if msg_type == "handshake":
                return self.handle_handshake(data, client_socket), data["username"]
                
            elif msg_type == "message" and current_username:
                return self.handle_chat_message(data, current_username), current_username
                
        except json.JSONDecodeError:
            print(f"Invalid JSON from client: {message_data}")
            
        return None, current_username
        
    def handle_handshake(self, data, client_socket):
        """Handle client handshake and registration"""
        username = data["username"]
        public_key_pem = data["public_key"]
        
        # Add user to manager
        if self.user_manager.add_user(username, client_socket, public_key_pem):
            print(f"User {username} registered successfully")
            
            # Encrypt symmetric key with user's public key
            try:
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode(),
                    backend=default_backend()
                )
                
                encrypted_key = public_key.encrypt(
                    self.symmetric_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                encrypted_key_b64 = base64.b64encode(encrypted_key).decode()
                
                # Send key exchange message
                key_exchange_msg = json.dumps(
                    Protocol.create_key_exchange(encrypted_key_b64)
                )
                client_socket.sendall((key_exchange_msg + '\n').encode())
                
            except Exception as e:
                print(f"Key encryption error for {username}: {e}")
                return json.dumps(
                    Protocol.create_system_message("Error establishing secure connection")
                )
            
            # Notify all users
            user_list = self.user_manager.get_all_users()
            user_list_msg = json.dumps(Protocol.create_user_list(user_list))
            self.user_manager.broadcast(user_list_msg)
            
            # Broadcast join message
            join_msg = json.dumps(
                Protocol.create_system_message(f"{username} has joined the chat")
            )
            self.user_manager.broadcast(join_msg, exclude_user=username)
            
            return json.dumps(
                Protocol.create_system_message("Welcome to the secure chat!")
            )
        else:
            return json.dumps(
                Protocol.create_system_message("Username already taken")
            )
            
    def handle_chat_message(self, data, username):
        """Handle incoming chat message"""
        message = data["message"]
        encrypted = data.get("encrypted", False)
        
        # Broadcast message to all users
        chat_msg = json.dumps(
            Protocol.create_message(username, message, encrypted)
        )
        disconnected = self.user_manager.broadcast(chat_msg, exclude_user=username)
        
        # Update user list if any users disconnected
        if disconnected:
            user_list_msg = json.dumps(
                Protocol.create_user_list(self.user_manager.get_all_users())
            )
            self.user_manager.broadcast(user_list_msg)
            
        return None

def main():
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()

if __name__ == "__main__":
    main()
# user_manager.py

import threading
import json
from cryptography.fernet import Fernet
from shared.protocol import Protocol

class UserManager:
    def __init__(self):
        self.users = {}  # username -> (socket, public_key, symmetric_key)
        self.lock = threading.Lock()
        
    def add_user(self, username, socket, public_key):
        """Add a new user to the manager"""
        with self.lock:
            if username in self.users:
                return False
                
            self.users[username] = {
                'socket': socket,
                'public_key': public_key,
                'symmetric_key': None
            }
            return True
            
    def remove_user(self, username):
        """Remove a user from the manager"""
        with self.lock:
            if username in self.users:
                del self.users[username]
                return True
            return False
            
    def get_user(self, username):
        """Get user information"""
        with self.lock:
            return self.users.get(username)
            
    def get_all_users(self):
        """Get all usernames"""
        with self.lock:
            return list(self.users.keys())
            
    def set_symmetric_key(self, username, symmetric_key):
        """Set symmetric key for a user"""
        with self.lock:
            if username in self.users:
                self.users[username]['symmetric_key'] = symmetric_key
                return True
            return False
            
    def broadcast(self, message, exclude_user=None):
        """Broadcast message to all users"""
        with self.lock:
            disconnected_users = []
            for username, user_info in self.users.items():
                if username == exclude_user:
                    continue
                    
                try:
                    # Ensure message ends with newline
                    if not message.endswith('\n'):
                        message_to_send = message + '\n'
                    else:
                        message_to_send = message
                    user_info['socket'].sendall(message_to_send.encode())
                    print(f"Broadcasted to {username}")
                except Exception as e:
                    print(f"Failed to send to {username}: {e}")
                    disconnected_users.append(username)
                    
            # Remove disconnected users
            for username in disconnected_users:
                del self.users[username]
                
            return disconnected_users
            
    def send_to_user(self, username, message):
        """Send message to specific user"""
        user_info = self.get_user(username)
        if user_info:
            try:
                if not message.endswith('\n'):
                    message += '\n'
                user_info['socket'].sendall(message.encode())
                return True
            except Exception as e:
                print(f"Failed to send to {username}: {e}")
                self.remove_user(username)
        return False
        
    def broadcast_user_list(self):
        """Broadcast updated user list to all users"""
        user_list = self.get_all_users()
        user_list_msg = json.dumps({
            "type": "user_list",
            "users": user_list
        })
        self.broadcast(user_list_msg)
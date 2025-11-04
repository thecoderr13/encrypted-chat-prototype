# user_manager.py

import threading
from cryptography.fernet import Fernet

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
                    user_info['socket'].sendall((message + '\n').encode())
                except:
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
                user_info['socket'].sendall((message + '\n').encode())
                return True
            except:
                self.remove_user(username)
        return False
        
    def initiate_key_exchange(self):
        """Initiate key exchange between all users"""
        symmetric_key = Fernet.generate_key()
        
        with self.lock:
            for username, user_info in self.users.items():
                if user_info['public_key']:
                    # In a real implementation, we'd encrypt the symmetric key
                    # with each user's public key and send it to them
                    self.set_symmetric_key(username, symmetric_key)
                    
        return symmetric_key
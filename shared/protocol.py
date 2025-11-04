# protocol.py

"""
Shared protocol definitions for client-server communication
"""

# Message types
HANDSHAKE = "handshake"
KEY_EXCHANGE = "key_exchange"
MESSAGE = "message"
USER_LIST = "user_list"
SYSTEM = "system"

class Protocol:
    @staticmethod
    def create_handshake(username, public_key):
        return {
            "type": HANDSHAKE,
            "username": username,
            "public_key": public_key
        }
    
    @staticmethod
    def create_key_exchange(encrypted_key):
        return {
            "type": KEY_EXCHANGE,
            "encrypted_key": encrypted_key
        }
    
    @staticmethod
    def create_message(sender, message, encrypted=False):
        return {
            "type": MESSAGE,
            "sender": sender,
            "message": message,
            "encrypted": encrypted
        }
    
    @staticmethod
    def create_user_list(users):
        return {
            "type": USER_LIST,
            "users": users
        }
    
    @staticmethod
    def create_system_message(message):
        return {
            "type": SYSTEM,
            "message": message
        }
# crypto_utils.py
import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

class CryptoUtils:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.symmetric_key = None
        self.fernet = None
        
    def generate_rsa_keys(self):
        """Generate RSA key pair for asymmetric encryption"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
    def get_public_key_pem(self):
        """Get public key in PEM format"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
    def load_public_key_from_pem(self, pem_data):
        """Load public key from PEM data"""
        if isinstance(pem_data, str):
            pem_data = pem_data.encode()
        self.public_key = serialization.load_pem_public_key(
            pem_data,
            backend=default_backend()
        )
        
    def generate_symmetric_key(self):
        """Generate symmetric key for AES encryption"""
        self.symmetric_key = Fernet.generate_key()
        self.fernet = Fernet(self.symmetric_key)
        
    def encrypt_with_public_key(self, data):
        """Encrypt data with RSA public key"""
        if isinstance(data, str):
            data = data.encode()
            
        encrypted = self.public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode()
        
    def decrypt_with_private_key(self, encrypted_data):
        """Decrypt data with RSA private key"""
        if isinstance(encrypted_data, str):
            encrypted_data = base64.b64decode(encrypted_data)
        
        decrypted = self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
        
    def encrypt_message(self, message):
        """Encrypt message with symmetric key"""
        if self.fernet is None:
            raise ValueError("Symmetric key not generated")
        if isinstance(message, str):
            message = message.encode()
        encrypted = self.fernet.encrypt(message)
        return base64.b64encode(encrypted).decode()
        
    def decrypt_message(self, encrypted_message):
        """Decrypt message with symmetric key"""
        if self.fernet is None:
            raise ValueError("Symmetric key not generated")
        if isinstance(encrypted_message, str):
            encrypted_message = base64.b64decode(encrypted_message)
        decrypted = self.fernet.decrypt(encrypted_message)
        return decrypted.decode()
        
    def export_symmetric_key(self):
        """Export symmetric key for sharing"""
        return base64.b64encode(self.symmetric_key).decode()
        
    def import_symmetric_key(self, key_data):
        """Import symmetric key from bytes or string"""
        if isinstance(key_data, str):
            key_data = base64.b64decode(key_data)
        self.symmetric_key = key_data
        self.fernet = Fernet(self.symmetric_key)
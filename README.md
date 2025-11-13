# Secure Encrypted Chat Prototype

A **Python-based secure chat application** featuring **end-to-end encryption**, **password-protected server access**, and **real-time messaging** with a **graphical user interface (GUI)**.

---

## Features

### Security Features
- **End-to-End Encryption** using RSA-2048 and AES-256  
- **Secure Key Exchange** with RSA public key cryptography  
- **Password-Protected Server** – Only authorized users can connect  
- **Encrypted Message Transmission** – All messages encrypted in transit  
- **Forward Secrecy** – Unique session keys for each connection  

### User Features
- **Real-time Chat Interface** with GUI  
- **Online User List** – See who's connected  
- **Multi-User Support** – Multiple clients can chat simultaneously  
- **Cross-Platform** – Works on Windows, macOS, and Linux  
- **Simple Setup** – Easy to deploy and use  

---

## System Architecture

```text
encrypted_chat/
├── client/                 # Client-side application
│   ├── client.py           # Main client logic
│   ├── crypto_utils.py     # Encryption/decryption functions
│   └── gui.py              # Graphical user interface
├── server/                 # Server-side application
│   ├── server.py           # Main server logic
│   └── user_manager.py     # User connection management
├── shared/
│   └── protocol.py         # Communication protocol definitions
└── requirements.txt        # Python dependencies
```

## Installation

### Prerequisites

- Python **3.7 or higher**
- **pip** (Python package manager)

---

### Step 1: Create Project Structure

```bash
# Create project directory
mkdir encrypted_chat
cd encrypted_chat

# Create directory structure
mkdir client server shared
```

### Step 2: Install Dependencies
```bash
pip install cryptography
```

## Usage

### Starting the Server
### Step 1: Navigate to server directory:
```bash
cd server
```
### Step 2: Run the server:
```bash
python server.py
```
### Step 3: Server will display:

```text
Chat Server Started
Server Address: localhost:8888
Server Password: secret123
Waiting for connections...
```
### Connecting Clients
### Step 1: Navigate to client directory:
```bash
cd client
```
### Step 2: Run the client:
```bash
python client.py
```
### Step 3: In the GUI:
- Enter your username
- Server: localhost
- Port: 8888
- Password: secret123 (default server password)
- Click Connect

## Configuration
### Changing Server Password
Edit server.py and modify this line:
```python
self.server_password = "your-new-password-here"
```
### Changing Server Port
Edit server.py and modify the constructor:
```python
def __init__(self, host='localhost', port=9999):  # Change port number
```
## Security Implementation
### Encryption Flow
1. Key Generation
- Client generates RSA-2048 key pair on connection
- Server generates Fernet symmetric key for session

2. Key Exchange
- Client sends public key to server during handshake
- Server encrypts symmetric key with client's public key
- Client decrypts symmetric key with private key

3. Message Encryption
- All messages encrypted with AES-256 (Fernet)
- Each message individually encrypted
- Encryption status displayed in chat

### Protocol Messages
- handshake: Initial connection with credentials and public key
- key_exchange: Secure symmetric key delivery
- message: Encrypted/decrypted chat messages
- user_list: Online users update
- system: Server notifications

## Troubleshooting
### Common Issues
1. Connection Refused
- Ensure server is running before clients connect
- Check firewall settings for port 8888

2. Authentication Failed
- Verify server password matches
- Check for typos in password

3. Encryption Errors
- Ensure cryptography library is properly installed
- Check Python version compatibility (3.7+)

4. Port Already in Use
- Change server port in server.py
- Update client connection settings accordingly

## Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Technical Report
You can read the full project documentation here:
[**Secure Encrypted Chat Prototype – Technical Report (PDF)**](./Secure%20Encrypted%20Chat%20Prototype%20-%20Technical%20Report%20(3).pdf)


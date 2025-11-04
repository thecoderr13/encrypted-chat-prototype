# gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

class ChatGUI:
    def __init__(self, client):
        self.client = client
        self.root = tk.Tk()
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the chat interface"""
        self.root.title("Secure Chat Client")
        self.root.geometry("600x500")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(conn_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(conn_frame, width=15)
        self.username_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(conn_frame, text="Server:").grid(row=0, column=2, padx=(20,0))
        self.server_entry = ttk.Entry(conn_frame, width=15)
        self.server_entry.insert(0, "localhost")
        self.server_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=4)
        self.port_entry = ttk.Entry(conn_frame, width=8)
        self.port_entry.insert(0, "8888")
        self.port_entry.grid(row=0, column=5, padx=5)
        
        self.connect_button = ttk.Button(conn_frame, text="Connect", 
                                       command=self.toggle_connection)
        self.connect_button.grid(row=0, column=6, padx=10)
        
        # Chat area
        chat_frame = ttk.LabelFrame(main_frame, text="Chat", padding="5")
        chat_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, width=70, height=20, state=tk.DISABLED)
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Message input
        ttk.Label(chat_frame, text="Message:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.message_entry = ttk.Entry(chat_frame, width=50)
        self.message_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        self.send_button = ttk.Button(chat_frame, text="Send", 
                                    command=self.send_message, state=tk.DISABLED)
        self.send_button.grid(row=1, column=2, padx=5)
        
        # Users list
        users_frame = ttk.LabelFrame(main_frame, text="Online Users", padding="5")
        users_frame.grid(row=0, column=2, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.users_listbox = tk.Listbox(users_frame, width=20, height=25)
        self.users_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status
        self.status_var = tk.StringVar(value="Disconnected")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                               foreground="red")
        status_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        chat_frame.columnconfigure(1, weight=1)
        users_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        users_frame.rowconfigure(0, weight=1)
        
    def toggle_connection(self):
        """Connect or disconnect from server"""
        if not self.client.connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()
            
    def connect_to_server(self):
        """Connect to the chat server"""
        username = self.username_entry.get().strip()
        server = self.server_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return
            
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
            
        # Connect in a separate thread
        def connect_thread():
            if self.client.connect(server, port, username):
                self.root.after(0, self.on_connect_success)
            else:
                self.root.after(0, self.on_connect_failure)
                
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def on_connect_success(self):
        """Handle successful connection"""
        self.connect_button.config(text="Disconnect")
        self.send_button.config(state=tk.NORMAL)
        self.username_entry.config(state=tk.DISABLED)
        self.server_entry.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.DISABLED)
        self.status_var.set("Connected")
        self.root.title(f"Secure Chat - {self.username_entry.get()}")
        
    def on_connect_failure(self):
        """Handle connection failure"""
        messagebox.showerror("Error", "Failed to connect to server")
        
    def disconnect_from_server(self):
        """Disconnect from server"""
        self.client.disconnect()
        self.connect_button.config(text="Connect")
        self.send_button.config(state=tk.DISABLED)
        self.username_entry.config(state=tk.NORMAL)
        self.server_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.status_var.set("Disconnected")
        self.root.title("Secure Chat Client")
        self.users_listbox.delete(0, tk.END)
        
    def send_message(self):
        """Send message to server"""
        message = self.message_entry.get().strip()
        if message and self.client.connected:
            self.client.send_message(message)
            self.message_entry.delete(0, tk.END)
            
    def display_message(self, sender, message, encrypted=False):
        """Display message in chat area"""
        self.chat_display.config(state=tk.NORMAL)
        
        if encrypted:
            self.chat_display.insert(tk.END, f"[ENCRYPTED] {sender}: {message}\n")
        else:
            if sender == "System":
                self.chat_display.insert(tk.END, f"*** {message} ***\n")
            else:
                self.chat_display.insert(tk.END, f"{sender}: {message}\n")
                
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def update_users_list(self, users):
        """Update the online users list"""
        self.users_listbox.delete(0, tk.END)
        for user in users:
            self.users_listbox.insert(tk.END, user)
            
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
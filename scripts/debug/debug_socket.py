import socket
import sys
import time

HOST = '127.0.0.1'
PORT = 2121

print(f"Attempting raw socket connection to {HOST}:{PORT}...")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect((HOST, PORT))
        print("Connected successfully!")
        
        # Try to read welcome message
        data = s.recv(1024)
        print(f"Received: {data.decode('utf-8', errors='ignore')}")
        
        # Send command
        print("Sending 'status' command...")
        s.sendall(b"status\n")
        
        # Read response
        time.sleep(0.5)
        data = s.recv(4096)
        print(f"Response: {data.decode('utf-8', errors='ignore')}")
        
except ConnectionRefusedError:
    print("Connection refused. Port is closed.")
except TimeoutError:
    print("Connection timed out.")
except Exception as e:
    print(f"An error occurred: {e}")

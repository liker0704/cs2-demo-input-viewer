import socket
import time

HOST = '127.0.0.1'
PORT = 2121

print(f"Connecting to {HOST}:{PORT}...")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect((HOST, PORT))
        print("Connected!")
        
        # Read any initial data
        s.settimeout(1)
        try:
            initial = s.recv(4096)
            print(f"Initial data: {initial.decode('utf-8', errors='ignore')}")
        except socket.timeout:
            print("No initial data")
        
        # Send demo_info command
        print("\nSending 'demo_info' command...")
        s.sendall(b"demo_info\n")
        
        # Read response
        time.sleep(0.5)
        s.settimeout(2)
        response = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass
        
        print(f"\n=== Full Response ===")
        print(response.decode('utf-8', errors='ignore'))
        print("=== End Response ===")
        
except Exception as e:
    print(f"Error: {e}")

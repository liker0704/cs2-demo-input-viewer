import socket
import time

HOST = '127.0.0.1'
PORT = 2121

def send_command(s, cmd):
    print(f"\n=== Sending: {cmd} ===")
    s.sendall(f"{cmd}\n".encode())
    time.sleep(0.3)
    s.settimeout(1)
    response = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
    except socket.timeout:
        pass
    
    result = response.decode('utf-8', errors='ignore')
    print(result if result else "(no response)")
    return result

print(f"Connecting to {HOST}:{PORT}...")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect((HOST, PORT))
        print("Connected!")
        
        # Clear initial data
        s.settimeout(0.5)
        try:
            s.recv(4096)
        except:
            pass
        
        # Try various commands
        commands = [
            "demo_pause",
            "demo_resume", 
            "demo_info",
            "status",
            "help demo"
        ]
        
        for cmd in commands:
            send_command(s, cmd)
        
except Exception as e:
    print(f"Error: {e}")

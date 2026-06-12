import asyncio
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.network.telnet_client import CS2TelnetClient

async def main():
    client = CS2TelnetClient("127.0.0.1", 2121)
    print("Connecting to CS2...")
    try:
        await client.connect()
        print("Connected!")
        
        print("Reading ticks for 5 seconds...")
        for i in range(5):
            # We can't easily get the raw response from here without modifying the class
            # So we rely on the class printing "Failed to parse tick from response: <response>"
            # which it already does.
            tick = await client.get_current_tick()
            print(f"Current tick: {tick}")
            await asyncio.sleep(1)
            
        await client.disconnect()
        print("Test complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

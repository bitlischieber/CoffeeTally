#!/usr/bin/env python3
"""
Test Card Reader Connection
Simple script to test if the card reader is working
"""
import json
import os
import sys
import time
from card_reader import CardReader


def load_config():
    """Load configuration"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        print("ERROR: config.json not found")
        return None
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load config.json: {e}")
        return None


def main():
    """Main function"""
    print("="*50)
    print("Card Reader Connection Test")
    print("="*50)
    
    # Load configuration
    config = load_config()
    if not config:
        sys.exit(1)
    
    # Initialize card reader
    print(f"\nAttempting to connect to card reader...")
    print(f"Port: {config['card_reader']['port']}")
    print(f"Baudrate: {config['card_reader']['baudrate']}")
    
    reader = CardReader(
        port=config['card_reader']['port'],
        baudrate=config['card_reader']['baudrate'],
        timeout=config['card_reader']['timeout']
    )
    
    if not reader.connect():
        print("\n✗ Failed to connect to card reader")
        print("Please check:")
        print("  1. Card reader is connected")
        print("  2. COM port is correct in config.json")
        print("  3. No other program is using the port")
        sys.exit(1)
    
    print("\n✓ Successfully connected to card reader")
    print("\nWaiting for cards... (Press Ctrl+C to exit)")
    print("-" * 50)
    
    try:
        while True:
            card_id = reader.read_card()
            if card_id:
                print(f"\n✓ Card detected: {card_id}")
                reader.beep()
                time.sleep(1)  # Debounce
            else:
                # Show a dot every second to indicate the program is running
                print(".", end="", flush=True)
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    
    finally:
        reader.close()
        print("Card reader connection closed")


if __name__ == '__main__':
    main()

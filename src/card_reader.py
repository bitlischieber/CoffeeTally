"""
Card Reader Module
Handles communication with Eltatec TWN4 card reader via serial port
"""
import logging
import serial
import time
import sys
from threading import Lock

logger = logging.getLogger(__name__)


class CardReader:
    """Class for communicating with the Eltatec TWN4 card reader"""
    
    def __init__(self, port, baudrate=9600, timeout=0.1):
        """
        Initialize the card reader
        
        Args:
            port: COM port (e.g., "COM10" on Windows or "/dev/ttyUSB0" on Linux)
            baudrate: Serial communication speed (default: 9600)
            timeout: Read timeout in seconds (default: 0.1)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.last_card_id = None
        self.last_read_time = 0
        self.lock = Lock()
        
    def connect(self):
        """
        Establish connection to the card reader
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Handle platform-specific port naming
            if sys.platform == 'win32':
                # Windows: COM ports
                if self.port.upper().startswith('COM'):
                    port = self.port.upper()
                elif self.port.isdigit():
                    port = f'COM{self.port}'
                else:
                    port = self.port
            else:
                # Linux/Raspberry Pi: /dev/ttyUSB0 or similar
                if self.port.startswith('/dev/'):
                    port = self.port
                else:
                    port = f'/dev/{self.port}'
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            print(f"✓ Connected to card reader on {port}")
            return True
        except Exception as e:
            logger.exception("Cannot connect to card reader: %s", e)
            print(f"ERROR: Cannot connect to card reader: {e}")
            print(f"Hint: Check the COM port in config.json")
            return False
    
    def read_card(self):
        """
        Read a card from the reader using Eltatec TWN4 protocol
        
        Protocol:
        - Send search command: "050020\r"
        - Response "0000" means no card present
        - Response with card data contains card ID in hex format
        
        Returns:
            str: Card ID in hex format (uppercase) or None if no card present
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        try:
            with self.lock:
                # Send search command to card reader
                search_command = "050020\r"
                self.serial_connection.write(search_command.encode('ascii'))
                self.serial_connection.flush()
                
                # Wait for response
                time.sleep(0.05)
                
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline()
                    if response:
                        response_str = response.decode('ascii', errors='ignore').strip()
                        
                        # "0000" means no card present
                        if response_str == "0000":
                            return None
                        
                        # Parse card ID from response
                        if len(response_str) >= 8:
                            # Check if valid card response (byte 2-3 should be "01")
                            if len(response_str) >= 4 and response_str[2:4] == "01":
                                try:
                                    # Extract ID bit count (byte 6-7)
                                    id_bit_count_hex = response_str[6:8]
                                    id_bit_count = int(id_bit_count_hex, 16)
                                    id_bytes = id_bit_count // 8
                                    
                                    # Calculate minimum response length
                                    min_length = 10 + (id_bytes * 2)
                                    
                                    if len(response_str) >= min_length:
                                        # Extract card ID (starts at byte 10)
                                        id_start = 10
                                        id_hex = response_str[id_start:id_start + (id_bytes * 2)]
                                        
                                        if id_hex and len(id_hex) > 0:
                                            card_id = id_hex.upper()
                                            self.last_card_id = card_id
                                            self.last_read_time = time.time()
                                            return card_id
                                            
                                except (ValueError, IndexError) as e:
                                    logger.exception(
                                        "Error parsing card response (%s): %s",
                                        response_str,
                                        e,
                                    )
                                    print(f"Error parsing card response: {e}, response: {response_str}")
                                    return None
                
                return None
                
        except Exception as e:
            logger.exception("Error reading card: %s", e)
            print(f"Error reading card: {e}")
            return None
    
    def beep(self):
        """
        Send a beep command to the card reader
        Provides audio feedback when card is successfully read
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            return
        
        try:
            with self.lock:
                # Beep command for Eltatec TWN4
                beep_command = "040728600964006400\r"
                self.serial_connection.write(beep_command.encode('ascii'))
                self.serial_connection.flush()
        except Exception as e:
            logger.exception("Error sending beep command: %s", e)
            print(f"Error sending beep command: {e}")
    
    def close(self):
        """Close the serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Card reader connection closed")

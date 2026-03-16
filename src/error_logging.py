"""Error logging setup for CoffeeTally."""
import logging
import os
import sys

def setup_error_logging(enable_file_logging=False):
    """Configure error logging.
    
    Args:
        enable_file_logging: If True, log to file. If False, only log to console.
        
    Note: We don't set up exception hooks here because Kivy has its own logging system
    and they can conflict. Use normal logging calls instead.
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Only configure if not already configured (avoid conflicts with Kivy)
    if root_logger.handlers:
        # Already configured, possibly by Kivy
        pass
    else:
        root_logger.setLevel(logging.DEBUG)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler only if enabled
    if enable_file_logging:
        try:
            log_path = os.path.join(os.path.dirname(__file__), "error.log")
            file_handler = logging.FileHandler(log_path, mode='a')
            file_handler.setLevel(logging.WARNING)  # Only log WARNING and above
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            print(f"File logging enabled: {log_path}")
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)
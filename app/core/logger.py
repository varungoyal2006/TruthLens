import logging
import sys

def setup_logging() -> None:
    """
    Configures the root logger for the entire application.
    This should be called exactly once at the entry point of the app (e.g., main.py).
    """
    logging.basicConfig(
        # Set the minimum log level to capture (INFO, WARNING, ERROR, CRITICAL)
        level=logging.INFO, 
        
        # Define the standardized log structure for easy parsing by monitoring tools
        # Example: 2026-07-03 19:45:00,123 - services.youtube - [youtube.py:45] - download() - INFO - Task started
        format="%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(levelname)s - %(message)s",
        
        # Route logs to standard output (stdout) instead of stderr. 
        # This is a 12-Factor App best practice so Docker and CI/CD tools capture logs correctly.
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
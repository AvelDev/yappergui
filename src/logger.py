"""
Logging System Module

This module implements a singleton logger for the YapperGUI application, providing
consistent logging across all components. It sets up both file and console logging
with appropriate formatting and log levels.

Features:
- Daily rotating log files
- Console output for immediate feedback
- Different log levels (DEBUG, INFO, ERROR)
- Singleton pattern for consistent logging
- Automatic log directory creation

Example:
    >>> from logger import logger
    >>> logger.info("Application started")
    >>> logger.error("An error occurred", exc_info=True)
    >>> logger.debug("Debug information")
"""

import logging
import os
from datetime import datetime

class Logger:
    _instance = None
    
    def __new__(cls):
        """
        Create a new Logger instance if one doesn't exist (singleton pattern).
        
        Returns:
            Logger: The singleton Logger instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        """
        Initialize the logger with file and console handlers.
        Sets up formatting and creates necessary directories.
        """
        self.logger = logging.getLogger('YapperGUI')
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # File handler
        log_file = os.path.join(logs_dir, f"yapper_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @classmethod
    def get_logger(cls):
        """
        Get the singleton logger instance.
        
        Returns:
            logging.Logger: The configured logger instance
        """
        return cls().logger

logger = Logger.get_logger()

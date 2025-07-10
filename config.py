#!/usr/bin/env python3
"""
SpotEye Configuration Module
Centralized configuration for all application components
"""

import os
from typing import Dict


def load_env_file():
    """Load environment variables from .env file if it exists"""
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def get_config() -> Dict:
    """Get complete configuration for SpotEye application"""
    # Load environment variables from .env file if available
    load_env_file()
    
    return {
        'email': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': os.environ.get('SMTP_USER', 'tanga6998@gmail.com'),  # Sender email address
            'smtp_password': os.environ.get('SMTP_PASSWORD', ''),  # Gmail app-specific password from env
            'recipient_email': os.environ.get('RECIPIENT_EMAIL', 'tr1173309602@gmail.com')  # Recipient email address
        },
        
        'monitoring': {
            'target_url': 'https://www.apartments-hn.de/en/book-apartment',
            'check_interval': 3,  # Check interval in minutes (changed to 3 minutes for immediate notifications)
            'retry_attempts': 3,   # Number of retry attempts on failure
            'timeout': 30,         # Page load timeout in seconds
            'wait_for_data': 10    # Wait time for data loading in seconds
        },
        
        'data_storage': {
            'file_path': 'apartment_data.json',
            'backup_enabled': True,
            'backup_interval': 24  # Hours between backups
        },
        
        'browser': {
            'headless': True,      # Headless mode (background execution)
            'window_size': '1920,1080',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'chromedriver_path': None  # Set to specific path if using manual ChromeDriver
        },
        
        'logging': {
            'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'file': 'spotEye.log'
        }
    }


# Legacy support for existing configurations
EMAIL_CONFIG = get_config()['email']
MONITOR_CONFIG = get_config()['monitoring']
DATA_CONFIG = {
    'data_file': get_config()['data_storage']['file_path'],
    'log_file': get_config()['logging']['file']
}
BROWSER_CONFIG = get_config()['browser'] 
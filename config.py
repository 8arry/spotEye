# SpotEye Configuration File

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # Gmail SMTP server
    'smtp_port': 587,
    'email': 'your_email@gmail.com',  # Sender email address
    'password': 'your_app_password',  # Gmail app-specific password
    'to_email': 'your_email@gmail.com'  # Recipient email address (can be same as sender)
}

# Monitor Configuration
MONITOR_CONFIG = {
    'url': 'https://www.apartments-hn.de/en/book-apartment',
    'check_interval': 30,  # Check interval in minutes
    'retry_attempts': 3,   # Number of retry attempts on failure
    'timeout': 30,         # Page load timeout in seconds
    'wait_for_data': 10    # Wait time for data loading in seconds
}

# Data Storage Configuration
DATA_CONFIG = {
    'data_file': 'apartment_data.json',
    'log_file': 'spotEye.log'
}

# Chrome Browser Configuration
BROWSER_CONFIG = {
    'headless': False,     # Headless mode (background execution) - Set to False for testing
    'window_size': '1920,1080',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'chromedriver_path': None  # Set to specific path if using manual ChromeDriver (e.g., './drivers/chromedriver.exe')
} 
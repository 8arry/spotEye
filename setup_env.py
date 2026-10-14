#!/usr/bin/env python3
"""
Environment Setup Script for SpotEye
Creates .env file with necessary environment variables
"""

import os


def create_env_file():
    """Create .env file with default values"""
    
    env_content = """# SpotEye Environment Variables
# Email Configuration
SMTP_USER=your-sender@gmail.com
SMTP_PASSWORD=your-gmail-app-password
RECIPIENT_EMAIL=your-recipient@example.com

# Optional: Override default monitoring settings
# MONITORING_INTERVAL=30
# MONITORING_TIMEOUT=30
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print("📧 Email configuration:")
    print("   Edit .env and fill in SMTP_USER, SMTP_PASSWORD and RECIPIENT_EMAIL")
    print("")
    print("🔒 Security note: .env file contains sensitive information")
    print("   Make sure it's in .gitignore to avoid committing passwords")


def load_env_file():
    """Load environment variables from .env file"""
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Environment variables loaded from .env file")
    else:
        print("⚠️ .env file not found")


if __name__ == "__main__":
    create_env_file()
    load_env_file() 
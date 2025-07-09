#!/usr/bin/env python3
"""
Manual ChromeDriver download utility for SpotEye
"""

import os
import platform
import zipfile
import requests
import subprocess
import json
from pathlib import Path

def get_chrome_version():
    """Get installed Chrome version"""
    try:
        if platform.system() == "Windows":
            # Try to get Chrome version from registry or executable
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                return version
            except:
                # Alternative method using command line
                result = subprocess.run([
                    "powershell", "-command", 
                    "(Get-Item 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe').VersionInfo.ProductVersion"
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
        
        elif platform.system() == "Darwin":  # macOS
            result = subprocess.run([
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.split()[-1]
                
        elif platform.system() == "Linux":
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.split()[-1]
                
    except Exception as e:
        print(f"Could not detect Chrome version: {e}")
        
    return None

def get_chromedriver_url(chrome_version):
    """Get the appropriate ChromeDriver download URL"""
    # Get the major version
    major_version = chrome_version.split('.')[0]
    
    # Get available versions
    url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    response = requests.get(url)
    data = response.json()
    
    # Find matching version
    for version_info in data['versions']:
        if version_info['version'].startswith(major_version + '.'):
            downloads = version_info.get('downloads', {}).get('chromedriver', [])
            
            # Select appropriate platform
            system = platform.system().lower()
            arch = platform.machine().lower()
            
            platform_map = {
                'windows': 'win32' if '32' in arch else 'win64',
                'darwin': 'mac-arm64' if 'arm' in arch else 'mac-x64',
                'linux': 'linux64'
            }
            
            platform_key = platform_map.get(system, 'win64')  # Default to win64
            
            for download in downloads:
                if download['platform'] == platform_key:
                    return download['url'], version_info['version']
    
    return None, None

def download_chromedriver():
    """Download and setup ChromeDriver manually"""
    print("=== Manual ChromeDriver Download ===")
    
    # Detect Chrome version
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("Could not detect Chrome version. Please ensure Chrome is installed.")
        return False
    
    print(f"Detected Chrome version: {chrome_version}")
    
    # Get download URL
    url, driver_version = get_chromedriver_url(chrome_version)
    if not url:
        print("Could not find matching ChromeDriver version.")
        return False
    
    print(f"Found ChromeDriver version: {driver_version}")
    print(f"Download URL: {url}")
    
    # Create drivers directory
    drivers_dir = Path("drivers")
    drivers_dir.mkdir(exist_ok=True)
    
    # Download ChromeDriver
    print("Downloading ChromeDriver...")
    response = requests.get(url)
    zip_path = drivers_dir / "chromedriver.zip"
    
    with open(zip_path, 'wb') as f:
        f.write(response.content)
    
    # Extract ChromeDriver
    print("Extracting ChromeDriver...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(drivers_dir)
    
    # Find the chromedriver executable
    chromedriver_path = None
    for root, dirs, files in os.walk(drivers_dir):
        for file in files:
            if file.startswith('chromedriver') and (file.endswith('.exe') or not '.' in file):
                chromedriver_path = Path(root) / file
                break
        if chromedriver_path:
            break
    
    if chromedriver_path:
        # Make executable on Unix systems
        if platform.system() != "Windows":
            os.chmod(chromedriver_path, 0o755)
        
        print(f"ChromeDriver installed at: {chromedriver_path.absolute()}")
        print("\nTo use this ChromeDriver, either:")
        print("1. Add the drivers directory to your PATH")
        print("2. Update config.py to specify the path")
        
        # Clean up zip file
        zip_path.unlink()
        
        return True
    else:
        print("Failed to find ChromeDriver executable after extraction.")
        return False

if __name__ == "__main__":
    success = download_chromedriver()
    if success:
        print("\nChromeDriver download completed successfully!")
    else:
        print("\nChromeDriver download failed.") 
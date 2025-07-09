#!/usr/bin/env python3
"""
SpotEye - Apartment Monitoring System
Monitor W|27 student apartments for new listings and send email notifications
"""

import json
import logging
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import EMAIL_CONFIG, MONITOR_CONFIG, DATA_CONFIG, BROWSER_CONFIG


class SpotEyeMonitor:
    """Main apartment monitoring class"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.data_file = DATA_CONFIG['data_file']
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.DEBUG,  # Changed to DEBUG for testing
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(DATA_CONFIG['log_file'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def create_driver(self) -> webdriver.Chrome:
        """Create Chrome browser driver"""
        self.logger.info("Setting up Chrome browser driver...")
        
        # Setup Chrome options
        options = Options()
        if BROWSER_CONFIG['headless']:
            options.add_argument('--headless')
        options.add_argument(f'--window-size={BROWSER_CONFIG["window_size"]}')
        options.add_argument(f'--user-agent={BROWSER_CONFIG["user_agent"]}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Create driver with multiple fallback methods
        driver = None
        
        # Method 1: Try manual ChromeDriver path if specified
        if BROWSER_CONFIG.get('chromedriver_path'):
            try:
                self.logger.info(f"Using manual ChromeDriver path: {BROWSER_CONFIG['chromedriver_path']}")
                service = Service(BROWSER_CONFIG['chromedriver_path'])
                driver = webdriver.Chrome(service=service, options=options)
                self.logger.info("Successfully created driver with manual path")
            except Exception as e:
                self.logger.warning(f"Manual path method failed: {e}")
        
        # Method 2: Try automatic webdriver management
        if not driver:
            try:
                import platform
                os_type = platform.system().lower()
                arch = platform.machine().lower()
                
                self.logger.info(f"Detected OS: {os_type}, Architecture: {arch}")
                
                # Use ChromeDriverManager with better configuration
                chrome_manager = ChromeDriverManager()
                driver_path = chrome_manager.install()
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
                self.logger.info("Successfully created driver with webdriver-manager")
                
            except Exception as e:
                self.logger.warning(f"Webdriver-manager method failed: {e}")
        
        # Method 3: Try without service (assumes ChromeDriver in PATH)
        if not driver:
            try:
                self.logger.info("Trying to use system ChromeDriver...")
                driver = webdriver.Chrome(options=options)
                self.logger.info("Successfully created driver using system ChromeDriver")
            except Exception as e:
                self.logger.warning(f"System ChromeDriver method failed: {e}")
        
        if not driver:
            raise Exception("Failed to create ChromeDriver with all methods. Please try running: python download_chromedriver.py")
        
        # Additional stealth settings
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.logger.info("Chrome driver setup completed")
        return driver
    
    def scrape_apartments(self) -> List[Dict]:
        """Scrape apartment data from website"""
        self.logger.info("Starting apartment data scraping...")
        
        driver = None
        apartments = []
        
        try:
            # Create browser driver
            driver = self.create_driver()
            
            # Navigate to the website
            self.logger.info(f"Loading website: {MONITOR_CONFIG['url']}")
            driver.get(MONITOR_CONFIG['url'])
            
            # Wait for page to load
            WebDriverWait(driver, MONITOR_CONFIG['timeout']).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait additional time for JavaScript to load apartment data
            self.logger.info("Waiting for apartment data to load...")
            time.sleep(MONITOR_CONFIG['wait_for_data'])
            
            # Try to find apartment data elements
            # This is a basic implementation - we'll need to analyze the actual page structure
            try:
                # Look for common apartment listing selectors
                apartment_elements = self._find_apartment_elements(driver)
                
                if not apartment_elements:
                    self.logger.warning("No apartment elements found - checking page source")
                    # Log part of page source for debugging
                    page_source = driver.page_source[:1000] + "..."
                    self.logger.debug(f"Page source preview: {page_source}")
                
                for element in apartment_elements:
                    try:
                        apartment_data = self._extract_apartment_data(element)
                        if apartment_data:
                            apartments.append(apartment_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to extract data from apartment element: {e}")
                
                self.logger.info(f"Successfully scraped {len(apartments)} apartments")
                
            except Exception as e:
                self.logger.error(f"Error finding apartment elements: {e}")
                
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            raise
            
        finally:
            if driver:
                driver.quit()
                self.logger.info("Browser driver closed")
        
        return apartments
    
    def _find_apartment_elements(self, driver):
        """Find apartment listing elements on the page"""
        # Try multiple selectors to find apartment listings
        selectors = [
            'tr[data-apartment]',  # Table rows with apartment data
            '.apartment-row',      # Apartment rows
            '.apartment-item',     # Apartment items  
            'tbody tr',            # Table body rows
            '[class*="apartment"]', # Any element with apartment in class name
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.logger.info(f"Found {len(elements)} apartment elements using selector: {selector}")
                    return elements
            except Exception as e:
                self.logger.debug(f"Selector '{selector}' failed: {e}")
        
        return []
    
    def _extract_apartment_data(self, element) -> Optional[Dict]:
        """Extract apartment data from a single element"""
        try:
            # This is a basic implementation - will need to be adjusted based on actual page structure
            apartment_data = {
                'id': None,
                'floor': None,
                'type': None,
                'price': None,
                'location': None,
                'availability': None,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Try to extract text content and look for patterns
            text_content = element.text.strip()
            
            if not text_content:
                return None
            
            # Basic pattern matching for apartment info
            # This will need to be refined based on actual website structure
            apartment_data['raw_text'] = text_content
            apartment_data['id'] = hash(text_content)  # Temporary ID based on content
            
            # Log the raw content for analysis
            self.logger.debug(f"Extracted apartment text: {text_content[:100]}...")
            
            return apartment_data
            
        except Exception as e:
            self.logger.error(f"Error extracting apartment data: {e}")
            return None
    
    def load_historical_data(self) -> Dict:
        """Load historical data from file"""
        # TODO: Implement in step 3
        pass
    
    def save_data(self, data: Dict):
        """Save data to file"""
        # TODO: Implement in step 3
        pass
    
    def detect_changes(self, current_data: List[Dict], historical_data: Dict) -> List[Dict]:
        """Detect changes between current and historical data"""
        # TODO: Implement in step 3
        pass
    
    def send_notification(self, new_apartments: List[Dict]):
        """Send email notification for new apartments"""
        # TODO: Implement in step 4
        pass
    
    def run_once(self):
        """Execute monitoring once"""
        self.logger.info("Starting monitoring execution...")
        
        try:
            # 1. Scrape current data
            current_apartments = self.scrape_apartments()
            self.logger.info(f"Retrieved {len(current_apartments)} apartment listings")
            
            # 2. Load historical data
            historical_data = self.load_historical_data()
            
            # 3. Detect changes
            new_apartments = self.detect_changes(current_apartments, historical_data)
            
            # 4. Send notifications
            if new_apartments:
                self.logger.info(f"Found {len(new_apartments)} new apartments")
                self.send_notification(new_apartments)
            else:
                self.logger.info("No new apartments found")
            
            # 5. Save current data
            updated_data = {
                'last_check': datetime.now().isoformat(),
                'apartments': current_apartments
            }
            self.save_data(updated_data)
            
        except Exception as e:
            self.logger.error(f"Monitoring execution failed: {e}")
            raise


def main():
    """Main function"""
    print("=== SpotEye Apartment Monitoring System ===")
    print("Initializing...")
    
    monitor = SpotEyeMonitor()
    
    # Execute monitoring once (for testing)
    monitor.run_once()
    print("Monitoring completed!")


if __name__ == "__main__":
    main() 
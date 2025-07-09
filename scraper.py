#!/usr/bin/env python3
"""
SpotEye Web Scraper Module
Handles apartment data scraping and parsing from apartments-hn.de
"""

import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class ApartmentScraper:
    """Web scraper for apartment data from apartments-hn.de"""
    
    def __init__(self, config: Dict, logger: logging.Logger):
        """Initialize scraper with configuration and logger"""
        self.config = config
        self.logger = logger
        self.target_url = config['monitoring']['target_url']
        
    def create_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver with stealth options"""
        try:
            chrome_options = Options()
            
            # Basic Chrome options for stealth and performance
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Stealth options to avoid detection
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Multiple driver creation strategies
            driver = None
            
            # Strategy 1: Try manual chromedriver path if configured
            manual_path = self.config['browser'].get('chromedriver_path')
            if manual_path and os.path.exists(manual_path):
                try:
                    self.logger.info(f"Trying manual ChromeDriver path: {manual_path}")
                    service = webdriver.chrome.service.Service(manual_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.logger.info("Successfully created driver with manual path")
                except Exception as e:
                    self.logger.warning(f"Manual path failed: {e}")
            
            # Strategy 2: Try webdriver-manager
            if not driver:
                try:
                    self.logger.info("Trying webdriver-manager...")
                    service = webdriver.chrome.service.Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.logger.info("Successfully created driver with webdriver-manager")
                except Exception as e:
                    self.logger.warning(f"webdriver-manager failed: {e}")
            
            # Strategy 3: Try system PATH
            if not driver:
                try:
                    self.logger.info("Trying system PATH...")
                    driver = webdriver.Chrome(options=chrome_options)
                    self.logger.info("Successfully created driver from system PATH")
                except Exception as e:
                    self.logger.error(f"All ChromeDriver strategies failed: {e}")
                    raise
            
            # Configure additional stealth settings
            if driver:
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create Chrome driver: {e}")
            raise

    def scrape_apartments(self) -> List[Dict]:
        """Scrape apartment data from the website"""
        self.logger.info(f"Starting to scrape apartments from {self.target_url}")
        
        driver = None
        try:
            # Create driver
            driver = self.create_driver()
            
            # Navigate to target URL
            driver.get(self.target_url)
            self.logger.info("Successfully loaded the page")
            
            # Wait for dynamic content to load
            self._wait_for_content_load(driver)
            
            # Find apartment elements
            apartment_elements = self._find_apartment_elements(driver)
            self.logger.info(f"Found {len(apartment_elements)} apartment elements")
            
            # Extract data from each element
            apartments = []
            for i, element in enumerate(apartment_elements, 1):
                apartment_data = self._extract_apartment_data(element)
                if apartment_data:
                    apartments.append(apartment_data)
                    self.logger.debug(f"Extracted apartment {i}: {apartment_data.get('id', 'Unknown')}")
            
            self.logger.info(f"Successfully extracted {len(apartments)} apartment records")
            return apartments
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            raise
        
        finally:
            if driver:
                driver.quit()
                self.logger.debug("Chrome driver closed")

    def _wait_for_content_load(self, driver):
        """Wait for dynamic content to load on the page"""
        try:
            # Wait for "Loading data..." to disappear or content to appear
            wait = WebDriverWait(driver, 30)
            
            # Try multiple strategies to detect when content is loaded
            try:
                # Strategy 1: Wait for apartment rows to appear
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr[data-apartment], .apartment-row, tbody tr')))
                self.logger.info("Apartment elements detected")
            except TimeoutException:
                # Strategy 2: Wait for any table content
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table, .table, tbody')))
                    self.logger.info("Table content detected")
                except TimeoutException:
                    self.logger.warning("Timeout waiting for content, proceeding anyway")
            
            # Additional wait to ensure JavaScript rendering is complete
            time.sleep(3)
            
        except Exception as e:
            self.logger.warning(f"Error waiting for content load: {e}")

    def _find_apartment_elements(self, driver):
        """Find apartment listing elements using multiple CSS selectors"""
        apartment_elements = []
        
        # Multiple selector strategies
        selectors = [
            'tr[data-apartment]',  # Most specific
            '.apartment-row',      # Class-based
            'tbody tr',            # Generic table rows
            'table tr',            # All table rows
            '.apartment',          # Generic apartment class
            '[class*="apartment"]' # Any class containing "apartment"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Filter out header rows or empty elements
                    valid_elements = []
                    for element in elements:
                        text_content = element.text.strip()
                        if text_content and len(text_content) > 20:  # Ensure substantial content
                            valid_elements.append(element)
                    
                    if valid_elements:
                        apartment_elements = valid_elements
                        self.logger.info(f"Found {len(apartment_elements)} apartments using selector: {selector}")
                        break
                        
            except NoSuchElementException:
                continue
        
        if not apartment_elements:
            self.logger.warning("No apartment elements found with any selector")
        
        return apartment_elements

    def _extract_apartment_data(self, element) -> Optional[Dict]:
        """Extract apartment data from a single element"""
        try:
            text_content = element.text.strip()
            
            if not text_content:
                return None
            
            # Parse the apartment information from the text
            apartment_data = self._parse_apartment_text(text_content)
            
            # Log the raw content for analysis
            self.logger.debug(f"Extracted apartment text: {text_content[:100]}...")
            
            return apartment_data
            
        except Exception as e:
            self.logger.error(f"Error extracting apartment data: {e}")
            return None
    
    def _parse_apartment_text(self, text: str) -> Dict:
        """Parse apartment text into structured data"""
        apartment_data = {
            'id': None,
            'floor': None,
            'apartment_number': None,
            'type': None,
            'balcony': None,
            'location': None,
            'size': None,
            'price': None,
            'availability': None,
            'available_date': None,
            'barrier_free': False,
            'raw_text': text,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Split text into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return apartment_data
        
        # Parse first line: "Floor/ ApartmentNumber Type, balcony Location Size Price"
        # Example: "3/ 309 Single, balcony Inner courtyard 27.17 520.50"
        first_line = lines[0]
        
        # Extract floor and apartment number
        floor_match = re.match(r'(\d+)/\s*(\d+)', first_line)
        if floor_match:
            apartment_data['floor'] = floor_match.group(1)
            apartment_data['apartment_number'] = floor_match.group(2)
            apartment_data['id'] = f"{apartment_data['floor']}-{apartment_data['apartment_number']}"
        
        # Extract type (Single, Partner)
        if 'Single' in first_line:
            apartment_data['type'] = 'Single'
        elif 'Partner' in first_line:
            apartment_data['type'] = 'Partner'
        
        # Extract balcony information
        if 'no balcony' in first_line:
            apartment_data['balcony'] = 'no'
        elif 'balcony' in first_line:
            apartment_data['balcony'] = 'yes'
            
        # Check for barrier-free
        if 'barrier-free' in first_line:
            apartment_data['barrier_free'] = True
        
        # Extract location (Inner courtyard, Wilhelmstraße, Südstraße)
        location_patterns = [
            r'Inner courtyard',
            r'Wilhelmstraße',
            r'Südstraße'
        ]
        for pattern in location_patterns:
            if re.search(pattern, first_line):
                apartment_data['location'] = pattern.replace('ß', 'ss')  # Normalize
                break
        
        # Extract size and price (last two numbers in the first line)
        numbers = re.findall(r'\d+\.\d+', first_line)
        if len(numbers) >= 2:
            apartment_data['size'] = float(numbers[-2])  # Second to last number (size in m²)
            apartment_data['price'] = float(numbers[-1])  # Last number (price in euros)
        
        # Parse availability status
        if len(lines) > 1:
            status_line = lines[1]
            if 'Already taken' in status_line:
                apartment_data['availability'] = 'taken'
            elif 'Soon available' in status_line:
                apartment_data['availability'] = 'soon'
                # Extract available date if present
                if len(lines) > 2:
                    date_line = lines[2]
                    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date_line)
                    if date_match:
                        apartment_data['available_date'] = date_match.group(1)
            elif 'Apply now' in status_line:
                apartment_data['availability'] = 'available'
            else:
                apartment_data['availability'] = 'unknown'
        
        return apartment_data 
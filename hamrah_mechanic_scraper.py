import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

def scrape_hamrah_mechanic():
    """
    Scrapes car prices from Hamrah Mechanic website and saves them to an Excel file.
    """
    url = "https://www.hamrah-mechanic.com/carprice/"
    
    print("Initializing WebDriver...")
    try:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"Failed to initialize WebDriver with webdriver-manager: {e}")
        print("Falling back to system chromedriver.")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    print(f"Navigating to {url}...")
    driver.get(url)

    try:
        # Wait for the page to load completely
        wait = WebDriverWait(driver, 60)
        print("Waiting for page to load...")
        time.sleep(10)  # Additional wait for dynamic content
        
        # Scroll down to trigger loading of dynamic content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)
        
        # Try to find the main container
        main_container_xpath = '//*[@id="__next"]/main/div[4]/div[1]'
        print("Looking for the main container...")
        
        try:
            container = wait.until(EC.presence_of_element_located((By.XPATH, main_container_xpath)))
            print("Main container found.")
        except:
            print("Main container not found with original xpath. Trying alternative approaches...")
            # Try to find any car price elements
            container = driver.find_element(By.TAG_NAME, "body")
        
        car_data = []
        
        # Try to find car data using BeautifulSoup for better parsing
        print("Searching for car data using BeautifulSoup...")
        
        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for car price tables with specific class names
        print("Looking for car price tables...")
        
        # Find all price tables
        price_tables = soup.find_all('table', class_='carsBrandPriceList_price-table__Z04ZN')
        print(f"Found {len(price_tables)} price tables")
        
        for table in price_tables:
            try:
                # Find all rows in the table
                rows = table.find_all('tr', class_='carsBrandPriceList_price-table__row__Ev8Ts')
                
                for row in rows:
                    try:
                        # Extract car name from the left content
                        name_cell = row.find('td', class_='carsBrandPriceList_price-table__right-content__nl31g')
                        price_cell = row.find('td', class_='carsBrandPriceList_price-table__left-content__VRcOA')
                        
                        if name_cell and price_cell:
                            # Extract car name
                            car_name_div = name_cell.find('div', class_='carsBrandPriceList_model__name__fYre5')
                            car_type_div = name_cell.find('div', class_='carsBrandPriceList_model__type__1L_I7')
                            
                            # Extract price
                            price_number_div = price_cell.find('div', class_='carsBrandPriceList_price__number__APBu0')
                            price_unit_div = price_cell.find('div', class_='carsBrandPriceList_price__unit__Hjahg')
                            
                            if car_name_div and price_number_div and price_unit_div:
                                car_name = car_name_div.get_text(strip=True)
                                car_type = car_type_div.get_text(strip=True) if car_type_div else ""
                                price_number = price_number_div.get_text(strip=True)
                                price_unit = price_unit_div.get_text(strip=True)
                                
                                # Combine name and type
                                full_car_name = f"{car_name} {car_type}" if car_type else car_name
                                full_price = f"{price_number} {price_unit}"
                                
                                # Check for duplicates
                                duplicate = False
                                for existing in car_data:
                                    if existing['Car Name'] == full_car_name and existing['Price'] == full_price:
                                        duplicate = True
                                        break
                                
                                if not duplicate:
                                    car_data.append({"Car Name": full_car_name, "Price": full_price})
                                    # Log every 25th record to reduce Railway log rate limiting
                                    if len(car_data) % 25 == 0:
                                        print(f"Found {len(car_data)} records - Latest: {full_car_name} - {full_price}")
                    
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        print(f"Found {len(car_data)} car records from price tables.")
        
        # Alternative approach: Look for structured data patterns
        if len(car_data) < 10:
            print("Trying to find more structured data...")
            
            # Look for common car manufacturer names in Persian
            car_brands = ['پژو', 'سمند', 'پراید', 'تیبا', 'دنا', 'رانا', 'ساینا', 'کوئیک', 'آریو', 'شاهین', 'تارا']
            
            for brand in car_brands:
                brand_elements = soup.find_all(string=re.compile(brand, re.IGNORECASE))
                for element in brand_elements:
                    try:
                        parent = element.parent
                        for level in range(3):
                            if parent:
                                full_text = parent.get_text(separator='\n', strip=True)
                                if ('تومان' in full_text or 'ریال' in full_text) and len(full_text) > 10:
                                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                                    
                                    car_name = None
                                    car_price = None
                                    
                                    for line in lines:
                                        if brand in line and not car_name:
                                            car_name = line
                                        elif ('تومان' in line or 'ریال' in line) and re.search(r'\d', line):
                                            car_price = line
                                    
                                    if car_name and car_price:
                                        # Check if this combination is already added
                                        if not any(item['Car Name'] == car_name and item['Price'] == car_price for item in car_data):
                                            car_data.append({"Car Name": car_name, "Price": car_price})
                                    break
                                parent = parent.parent
                            else:
                                break
                    except Exception as e:
                        continue
        
        # Remove duplicates
        if car_data:
            seen = set()
            unique_data = []
            for item in car_data:
                key = (item["Car Name"], item["Price"])
                if key not in seen:
                    seen.add(key)
                    unique_data.append(item)
            car_data = unique_data
        
        print(f"Extracted {len(car_data)} unique car records.")
        
        # Create a DataFrame and save to Excel and CSV
        if car_data:
            df = pd.DataFrame(car_data)
            output_filename_xlsx = "hamrah_mechanic_prices.xlsx"
            output_filename_csv = "hamrah_mechanic_prices.csv"
            df.to_excel(output_filename_xlsx, index=False)
            df.to_csv(output_filename_csv, index=False, encoding='utf-8')
            print(f"Data saved to {output_filename_xlsx} and {output_filename_csv}")
            
            # Print first few records for verification
            print("\nFirst 10 records:")
            for i, record in enumerate(car_data[:10]):
                print(f"{i+1}. Car: '{record['Car Name']}' - Price: '{record['Price']}'")
        else:
            print("No data was extracted.")
            # Print page source for debugging
            print("\nPage title:", driver.title)
            print("\nPage URL:", driver.current_url)

    finally:
        print("Closing the WebDriver.")
        driver.quit()

if __name__ == "__main__":
    scrape_hamrah_mechanic()
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
import requests
from selenium.webdriver.chrome.options import Options
from logging_config import HAMRAH_LOG_INTERVAL, Z4CAR_LOG_INTERVAL, log_progress, VERBOSE_LOGGING

# Code from hamrah_mechanic_scraper.py
def scrape_hamrah_mechanic(force_update=False):
    """استخراج قیمت خودرو از سایت همراه مکانیک با بهینه‌سازی سرعت
    
    Args:
        force_update (bool): اگر True باشد، بدون توجه به زمان فایل، داده‌ها مجدداً استخراج می‌شوند
    """
    # بررسی وجود فایل اکسل قبلی برای جلوگیری از استخراج مجدد
    import os
    import time
    
    output_filename_xlsx = "hamrah_mechanic_prices.xlsx"
    if not force_update and os.path.exists(output_filename_xlsx):
        try:
            # بررسی تاریخ فایل - اگر کمتر از 12 ساعت از ایجاد آن گذشته باشد، از آن استفاده کن
            file_time = os.path.getmtime(output_filename_xlsx)
            current_time = time.time()
            hours_diff = (current_time - file_time) / 3600
            
            if hours_diff < 12:  # اگر کمتر از 12 ساعت گذشته باشد
                print(f"📊 استفاده از قیمت‌های همراه مکانیک ذخیره شده قبلی ({hours_diff:.1f} ساعت پیش)")
                df = pd.read_excel(output_filename_xlsx)
                # تبدیل به فرمت مورد نیاز
                car_data = []
                for _, row in df.iterrows():
                    car_name = row['Car Name']
                    price = row['Price']
                    # استخراج عدد قیمت از رشته
                    price_number = re.sub(r'[^\d]', '', price)
                    if price_number:
                        price_number = int(price_number)
                    else:
                        price_number = 0
                    
                    car_data.append({
                        'نام خودرو': car_name,
                        'قیمت (تومان)': price_number
                    })
                
                print(f"✅ {len(car_data)} قیمت خودرو از همراه مکانیک بارگذاری شد")
                return car_data
            else:
                print(f"⚠️ فایل قیمت‌های همراه مکانیک قدیمی است ({hours_diff:.1f} ساعت). در حال به‌روزرسانی...")
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری فایل قبلی همراه مکانیک: {e}")
    elif force_update:
        print("🔄 درخواست به‌روزرسانی اجباری قیمت‌های همراه مکانیک...")
    
    # تلاش برای استفاده از API به جای وب اسکرپینگ
    try:
        print("🔍 تلاش برای دریافت قیمت‌ها از API همراه مکانیک...")
        api_url = "https://www.hamrah-mechanic.com/api/v1/car-price/all"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.hamrah-mechanic.com/carprice/'
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 10:
                    print(f"✅ دریافت موفق {len(data)} قیمت خودرو از API همراه مکانیک")
                    car_data = []
                    for item in data:
                        if 'name' in item and 'price' in item:
                            car_name = item['name']
                            # تبدیل قیمت به عدد
                            price_str = str(item['price'])
                            price_number = re.sub(r'[^\d]', '', price_str)
                            if price_number:
                                price_number = int(price_number)
                            else:
                                price_number = 0
                                
                            car_data.append({
                                'نام خودرو': car_name,
                                'قیمت (تومان)': price_number
                            })
                    
                    # ذخیره در فایل اکسل برای استفاده بعدی
                    df = pd.DataFrame([
                        {"Car Name": item['نام خودرو'], "Price": f"{item['قیمت (تومان)']:,} تومان"}
                        for item in car_data
                    ])
                    df.to_excel(output_filename_xlsx, index=False)
                    df.to_csv("hamrah_mechanic_prices.csv", index=False, encoding='utf-8')
                    
                    print(f"✅ {len(car_data)} قیمت خودرو از همراه مکانیک استخراج و ذخیره شد")
                    return car_data
            except Exception as e:
                print(f"⚠️ خطا در پردازش پاسخ API: {e}")
    except Exception as e:
        print(f"⚠️ خطا در دسترسی به API: {e}")
    
    # اگر API کار نکرد، از وب اسکرپینگ استفاده کن
    url = "https://www.hamrah-mechanic.com/carprice/"
    print("🔧 راه‌اندازی WebDriver برای Hamrah Mechanic...")
    
    # تنظیمات Chrome بهینه برای سرعت بیشتر
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-animations")
    options.add_argument("--disable-web-security")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # تنظیمات اضافی برای سرعت بیشتر
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-features=UserAgentClientHint")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--no-pings")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        print("📥 تلاش برای استفاده از webdriver-manager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ WebDriver با webdriver-manager راه‌اندازی شد")
    except Exception as e:
        print(f"⚠️ خطا در webdriver-manager: {e}")
        print("🔄 تلاش برای استفاده از chromedriver سیستم...")
        try:
            driver = webdriver.Chrome(options=options)
            print("✅ WebDriver با chromedriver سیستم راه‌اندازی شد")
        except Exception as e2:
            print(f"❌ خطا در راه‌اندازی ChromeDriver: {e2}")
            raise Exception(f"Unable to locate or obtain driver for chrome: {e2}")
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(20)  # کاهش تایم‌اوت برای سرعت بیشتر

    print(f"Navigating to {url}...")
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 20)  # کاهش زمان انتظار
        print("Waiting for page to load...")
        time.sleep(5)  # کاهش زمان انتظار
        
        # اسکرول سریع‌تر
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        
        car_data = []
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # استفاده از سلکتورهای بهینه‌تر
        price_tables = soup.find_all(['table', 'div'], class_=lambda c: c and ('price-table' in c or 'price_table' in c))
        print(f"Found {len(price_tables)} price tables")
        
        # استفاده از دیکشنری برای حذف تکرارها با سرعت بیشتر
        unique_cars = {}
        
        for table in price_tables:
            try:
                rows = table.find_all(['tr', 'div'], class_=lambda c: c and ('row' in c or 'item' in c))
                for row in rows:
                    try:
                        # جستجوی انعطاف‌پذیرتر برای سلول‌های نام و قیمت
                        name_cell = row.find(['td', 'div'], class_=lambda c: c and ('right' in c or 'name' in c or 'title' in c))
                        price_cell = row.find(['td', 'div'], class_=lambda c: c and ('left' in c or 'price' in c))
                        
                        if name_cell and price_cell:
                            # استخراج نام خودرو
                            car_name = name_cell.get_text(strip=True)
                            if not car_name:
                                car_name_div = name_cell.find(['div', 'span'], class_=lambda c: c and ('name' in c or 'title' in c))
                                if car_name_div:
                                    car_name = car_name_div.get_text(strip=True)
                            
                            # استخراج قیمت
                            price_text = price_cell.get_text(strip=True)
                            if not price_text or not re.search(r'\d', price_text):
                                price_div = price_cell.find(['div', 'span'], class_=lambda c: c and ('price' in c or 'number' in c))
                                if price_div:
                                    price_text = price_div.get_text(strip=True)
                            
                            if car_name and price_text and re.search(r'\d', price_text):
                                # استخراج عدد قیمت
                                price_number = re.sub(r'[^\d]', '', price_text)
                                if price_number:
                                    price_number = int(price_number)
                                    # ذخیره در دیکشنری برای حذف تکرارها
                                    unique_cars[car_name] = price_number
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        # تبدیل دیکشنری به لیست نهایی
        car_data = [
            {'نام خودرو': name, 'قیمت (تومان)': price}
            for name, price in unique_cars.items()
        ]
        
        print(f"Extracted {len(car_data)} unique car records.")
        
        if car_data:
            # ذخیره در فایل اکسل برای استفاده بعدی
            df = pd.DataFrame([
                {"Car Name": item['نام خودرو'], "Price": f"{item['قیمت (تومان)']:,} تومان"}
                for item in car_data
            ])
            df.to_excel(output_filename_xlsx, index=False)
            df.to_csv("hamrah_mechanic_prices.csv", index=False, encoding='utf-8')
            
            print(f"✅ {len(car_data)} قیمت خودرو از همراه مکانیک استخراج و ذخیره شد")
        else:
            print("No data was extracted.")
    except Exception as e:
        print(f"❌ خطا در استخراج قیمت‌های همراه مکانیک: {e}")
        car_data = []
    finally:
        print("Closing the WebDriver.")
        driver.quit()
    
    return car_data

# Code from z4car_scraper.py
class Z4CarScraper:
    def __init__(self):
        self.base_url = "https://z4car.com"
        self.price_url = "https://z4car.com/price"
        self.driver = None
    
    def setup_driver(self):
        try:
            print("🔧 راه‌اندازی WebDriver برای Z4Car...")
            
            # تنظیمات Chrome بهینه برای سرعت بیشتر
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-animations')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # تنظیمات اضافی برای سرعت بیشتر
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-breakpad")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-features=UserAgentClientHint")
            chrome_options.add_argument("--metrics-recording-only")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-pings")
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                print("📥 تلاش برای استفاده از webdriver-manager...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ WebDriver با webdriver-manager راه‌اندازی شد")
            except Exception as e:
                print(f"⚠️ خطا در webdriver-manager: {e}")
                print("🔄 تلاش برای استفاده از chromedriver سیستم...")
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    print("✅ WebDriver با chromedriver سیستم راه‌اندازی شد")
                except Exception as e2:
                    print(f"❌ خطا در راه‌اندازی ChromeDriver: {e2}")
                    raise Exception(f"Unable to locate or obtain driver for chrome: {e2}")
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(20)  # کاهش تایم‌اوت برای سرعت بیشتر
            return True
        except Exception as e:
            print(f"❌ خطا در راه‌اندازی WebDriver: {e}")
            return False
    
    def get_page_content(self, url):
        try:
            print(f"บารยذاری صفحه: {url}")
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            # اسکرول سریع‌تر برای بهینه‌سازی سرعت
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            return self.driver.page_source
        except Exception as e:
            print(f"خطا در دریافت صفحه: {e}")
            # تلاش مجدد با تنظیمات ساده‌تر
            try:
                print("🔄 تلاش مجدد با زمان انتظار کمتر...")
                self.driver.get(url)
                time.sleep(3)
                return self.driver.page_source
            except Exception as e2:
                print(f"خطا در تلاش مجدد: {e2}")
                return None
    
    def clean_price(self, price_text):
        if not price_text:
            return None
        # استفاده از کش برای قیمت‌های تکراری
        if not hasattr(self, '_price_cache'):
            self._price_cache = {}
        
        if price_text in self._price_cache:
            return self._price_cache[price_text]
            
        price_matches = re.findall(r'\d{1,3}(?:,\d{3})+', price_text)
        if price_matches:
            for price_match in price_matches:
                clean_price_text = price_match.replace(',', '')
                try:
                    price_value = int(clean_price_text)
                    if price_value > 10000000:
                        # ذخیره در کش
                        self._price_cache[price_text] = price_value
                        return price_value
                except:
                    continue
        return None
    
    def extract_individual_prices(self, price_text):
        if not price_text:
            return []
        price_matches = re.findall(r'\d{1,3}(?:,\d{3})+', price_text)
        valid_prices = []
        for price_match in price_matches:
            clean_price_text = price_match.replace(',', '')
            try:
                price_value = int(clean_price_text)
                if price_value > 10000000:
                    valid_prices.append(price_value)
            except:
                continue
        return valid_prices
    
    def extract_car_prices(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        cars_data = []
        print("جستجوی بلوک‌های قیمت خودرو...")
        
        # ذخیره HTML فقط در صورت نیاز برای دیباگ
        debug_mode = False
        if debug_mode:
            with open('z4car_debug.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("HTML صفحه در فایل z4car_debug.html ذخیره شد")
        
        # جستجوی همزمان چندین کلاس مرتبط با قیمت - بهینه‌سازی شده
        entry_bodies = soup.find_all(['div', 'section'], class_=lambda c: c and ('entry' in c or 'price' in c or 'content' in c or 'car' in c))
        print(f"یافت شد {len(entry_bodies)} بلوک محتوا")
        
        # استفاده از دیکشنری برای حذف تکرارها با سرعت بیشتر
        unique_cars = {}
        
        # پردازش موازی برای سرعت بیشتر
        for entry in entry_bodies:
            try:
                # جستجوی همزمان لیست‌ها و جدول‌ها برای کاهش زمان پردازش
                ul_elements = entry.find_all('ul')
                tables = entry.find_all('table')
                
                # پردازش لیست‌ها
                for ul in ul_elements:
                    li_elements = ul.find_all('li')
                    if len(li_elements) >= 2:  # کاهش بیشتر حداقل تعداد آیتم‌ها برای یافتن موارد بیشتر
                        car_info = self.extract_from_columns(li_elements)
                        if car_info:
                            car_name = car_info['نام خودرو']
                            price = car_info['قیمت عددی']
                            if car_name not in unique_cars or price > unique_cars[car_name]['قیمت عددی']:
                                unique_cars[car_name] = car_info
                                if len(unique_cars) % Z4CAR_LOG_INTERVAL == 0:
                                     log_progress(f"استخراج شد: {car_name} - {car_info['قیمت (تومان)']}")
                
                # پردازش جدول‌ها با الگوریتم بهینه‌تر
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            car_name = cells[0].get_text(strip=True)
                            # بررسی همه سلول‌های باقیمانده برای یافتن قیمت
                            for cell in cells[1:]:
                                price_text = cell.get_text(strip=True)
                                if car_name and price_text and re.search(r'\d', price_text):
                                    price = self.clean_price(price_text)
                                    if price and price > 100000:
                                        car_info = {
                                            'نام خودرو': car_name.strip(),
                                            'وضعیت': 'نامشخص',
                                            'سال': 'نامشخص',
                                            'قیمت (تومان)': f"{price:,}",
                                            'قیمت عددی': price
                                        }
                                        if car_name not in unique_cars or price > unique_cars[car_name]['قیمت عددی']:
                                            unique_cars[car_name] = car_info
                                            break  # پس از یافتن اولین قیمت معتبر، به سراغ ردیف بعدی برو
            except Exception as e:
                continue
        
        # اگر هیچ داده‌ای پیدا نشد، از روش عمومی استفاده کن
        if not unique_cars:
            print("استفاده از روش عمومی...")
            general_cars = self.extract_general_method(soup)
            for car in general_cars:
                car_name = car['نام خودرو']
                price = car['قیمت عددی']
                if car_name not in unique_cars or price > unique_cars[car_name]['قیمت عددی']:
                    unique_cars[car_name] = car
        
        # تبدیل دیکشنری به لیست
        cars_data = list(unique_cars.values())
        return cars_data
    
    def extract_from_columns(self, li_elements):
        try:
            car_name = "نامشخص"
            condition = "نامشخص"
            year = "نامشخص"
            price_text = "نامشخص"
            for i, li in enumerate(li_elements):
                text = li.get_text(strip=True)
                if i == 0:
                    img = li.find('img')
                    if img and img.get('alt'):
                        alt_text = img.get('alt')
                        car_match = re.search(r'(آئودی|پژو|سمند|پراید|تیبا|دنا|رانا|سایپا|کوییک|آریو|شاهین|تارا|ساینا|مزدا|هوندا|تویوتا|نیسان|هیوندای|کیا|چری|ام وی ام|دوو|رنو|فولکس|بی ام و|بنز|آلفارومئو|آمیکو)[^\n]*', alt_text, re.I)
                        if car_match:
                            car_name = car_match.group()
                    if car_name == "نامشخص":
                        car_match = re.search(r'قیمت\s+([^\n]+)', text, re.I)
                        if car_match:
                            car_name = car_match.group(1)
                if "صفر" in text:
                    condition = "صفر کیلومتر"
                elif "کارکرده" in text:
                    condition = "کارکرده"
                year_match = re.search(r'(20\d{2}|13\d{2}|14\d{2})', text)
                if year_match:
                    year = year_match.group(1)
                price_match = re.search(r'\d{1,3}(,\d{3})+', text)
                if price_match:
                    price_text = text
            if price_text != "نامشخص":
                clean_price = self.clean_price(price_text)
                if clean_price and clean_price > 100000:
                    return {
                        'نام خودرو': car_name.strip(),
                        'وضعیت': condition,
                        'سال': year,
                        'قیمت (تومان)': f"{clean_price:,}",
                        'قیمت عددی': clean_price
                    }
            return None
        except:
            return None
    
    def extract_general_method(self, soup):
        cars_data = []
        # بهینه‌سازی: استفاده از دیکشنری برای حذف تکرارها با سرعت بیشتر
        unique_cars_dict = {}
        
        # بهینه‌سازی: جستجوی همزمان چندین نوع عنصر برای سرعت بیشتر
        price_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'price|car|vehicle', re.I))
        price_elements.extend(soup.find_all(string=re.compile(r'قیمت', re.I)))
        price_elements.extend(soup.find_all(string=re.compile(r'\d{1,3}(,\d{3})+')))
        print(f"یافت شد {len(price_elements)} عنصر برای بررسی")
        print("استخراج خودروها با روش بهینه‌سازی شده... (لاگ هر 50 رکورد)")
        
        # بهینه‌سازی: پردازش موازی برای سرعت بیشتر
        for element in price_elements:
            try:
                if isinstance(element, str):
                    text = element
                    parent = None
                else:
                    text = element.get_text(strip=True)
                    parent = element.parent
                individual_prices = self.extract_individual_prices(text)
                if individual_prices:
                    car_name = "نامشخص"
                    # بهینه‌سازی: الگوهای جستجوی بهتر برای نام خودرو
                    car_patterns = [
                        r'قیمت\s+([^\n]+)',
                        r'(آئودی|پژو|سمند|پراید|تیبا|دنا|رانا|سایپا|کوییک|آریو|شاهین|تارا|ساینا|مزدا|هوندا|تویوتا|نیسان|هیوندای|کیا|چری|ام وی ام|دوو|رنو|فولکس|بی ام و|بنز|آلفارومئو|آمیکو)[^\n]*',
                    ]
                    
                    # بهینه‌سازی: جستجوی سریع‌تر با شکست حلقه پس از یافتن اولین تطابق
                    for pattern in car_patterns:
                        match = re.search(pattern, text, re.I)
                        if match:
                            car_name = match.group(1) if match.lastindex else match.group()
                            break
                    
                    # بهینه‌سازی: بررسی فقط در صورت نیاز
                    if car_name == "نامشخص" and parent:
                        parent_text = parent.get_text(strip=True)
                        for pattern in car_patterns:
                            match = re.search(pattern, parent_text, re.I)
                            if match:
                                car_name = match.group(1) if match.lastindex else match.group()
                                break
                    
                    # بهینه‌سازی: محدود کردن جستجو در خواهر/برادرها به فقط 3 مورد اول
                    if car_name == "نامشخص" and parent:
                        siblings = parent.find_previous_siblings() + parent.find_next_siblings()
                        for sibling in siblings[:3]:  # فقط 3 مورد اول
                            if hasattr(sibling, 'get_text'):
                                sibling_text = sibling.get_text(strip=True)
                                for pattern in car_patterns:
                                    match = re.search(pattern, sibling_text, re.I)
                                    if match:
                                        car_name = match.group(1) if match.lastindex else match.group()
                                        break
                                if car_name != "نامشخص":
                                    break
                    
                    condition = "نامشخص"
                    if "صفر" in text.lower():
                        condition = "صفر کیلومتر"
                    elif "کارکرده" in text.lower():
                        condition = "کارکرده"
                    
                    year_match = re.search(r'(20\d{2}|13\d{2}|14\d{2})', text)
                    year = year_match.group(1) if year_match else "نامشخص"
                    
                    # بهینه‌سازی: ذخیره در دیکشنری برای حذف تکرارها
                    for i, price in enumerate(individual_prices):
                        display_name = car_name if len(individual_prices) == 1 else f"{car_name} (قیمت {i+1})"
                        
                        # بهینه‌سازی: فقط نگهداری قیمت‌های بالاتر برای هر خودرو
                        if display_name not in unique_cars_dict or price > unique_cars_dict[display_name]['قیمت عددی']:
                            unique_cars_dict[display_name] = {
                                'نام خودرو': display_name.strip(),
                                'وضعیت': condition,
                                'سال': year,
                                'قیمت (تومان)': f"{price:,}",
                                'قیمت عددی': price
                            }
                            # بهینه‌سازی: لاگ فقط برای موارد جدید یا به‌روزرسانی شده
                            if len(unique_cars_dict) % Z4CAR_LOG_INTERVAL == 0:
                                log_progress(f"استخراج شد: {display_name} - {price:,} تومان")
            except:
                continue
        
        # تبدیل دیکشنری به لیست نهایی
        cars_data = list(unique_cars_dict.values())
        print(f"استخراج {len(cars_data)} خودروی منحصر به فرد با روش عمومی")
        return cars_data
    
    def scrape_all_prices(self, force_update=False):
        print("شروع استخراج قیمت‌های خودرو از z4car.com...")
        # بررسی وجود فایل اکسل قبلی برای جلوگیری از استخراج مجدد
        import os
        output_filename_xlsx = "z4car_prices.xlsx"
        if not force_update and os.path.exists(output_filename_xlsx):
            try:
                # بررسی تاریخ فایل - اگر کمتر از 12 ساعت از ایجاد آن گذشته باشد، از آن استفاده کن
                file_time = os.path.getmtime(output_filename_xlsx)
                current_time = time.time()
                hours_diff = (current_time - file_time) / 3600
                
                if hours_diff < 12:  # اگر کمتر از 12 ساعت گذشته باشد
                    print(f"📊 استفاده از قیمت‌های ذخیره شده قبلی ({hours_diff:.1f} ساعت پیش)")
                    df = pd.read_excel(output_filename_xlsx)
                    cars_data = df.to_dict('records')
                    print(f"✅ {len(cars_data)} قیمت خودرو از فایل اکسل بارگذاری شد")
                    return cars_data
                else:
                    print(f"⚠️ فایل قیمت‌های Z4Car قدیمی است ({hours_diff:.1f} ساعت). در حال به‌روزرسانی...")
            except Exception as e:
                print(f"⚠️ خطا در بارگذاری فایل قبلی: {e}")
        elif force_update:
            print("🔄 درخواست به‌روزرسانی اجباری قیمت‌های Z4Car...")
        
        if not self.setup_driver():
            return []
        try:
            html_content = self.get_page_content(self.price_url)
            if not html_content:
                print("خطا در دریافت صفحه اصلی")
                return []
            print("تجزیه و تحلیل محتوای صفحه...")
            cars_data = self.extract_car_prices(html_content)
            # استفاده از دیکشنری برای حذف تکرارها با سرعت بیشتر
            unique_cars_dict = {}
            for car in cars_data:
                key = car['نام خودرو']
                price = car['قیمت عددی']
                if key not in unique_cars_dict or price > unique_cars_dict[key]['قیمت عددی']:
                    unique_cars_dict[key] = car
                    if len(unique_cars_dict) % Z4CAR_LOG_INTERVAL == 0:
                        log_progress(f"استخراج شد: {key} - {price:,} تومان")
            
            unique_cars = list(unique_cars_dict.values())
            print(f"استخراج {len(unique_cars)} خودروی منحصر به فرد")
            return unique_cars
        finally:
            if self.driver:
                self.driver.quit()
                print("WebDriver بسته شد")
    
    def save_to_excel(self, cars_data, filename):
        if not cars_data:
            print("هیچ داده‌ای برای ذخیره وجود ندارد")
            return
        try:
            print(f"💾 ذخیره {len(cars_data)} قیمت خودرو در فایل اکسل...")
            
            # تبدیل به DataFrame با بهینه‌سازی نوع داده‌ها
            df = pd.DataFrame(cars_data)
            
            # بهینه‌سازی: مرتب‌سازی بر اساس قیمت نزولی
            df = df.sort_values(by='قیمت عددی', ascending=False)
            
            # بهینه‌سازی: استفاده از موتور openpyxl برای سرعت بیشتر
            df.to_excel(filename, index=False, engine='openpyxl')
            
            # ذخیره به فرمت CSV با بهینه‌سازی
            csv_filename = filename.replace('.xlsx', '.csv')
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # پشتیبانی از کاراکترهای فارسی
            
            print(f"✅ داده‌ها در فایل {filename} و {csv_filename} ذخیره شد")
            print(f"✅ تعداد رکوردهای ذخیره شده: {len(df)}")
        except Exception as e:
            print(f"❌ خطا در ذخیره فایل: {e}")
            # تلاش مجدد با تنظیمات ساده‌تر
            try:
                print("🔄 تلاش مجدد با تنظیمات ساده‌تر...")
                pd.DataFrame(cars_data).to_excel(filename, index=False)
                print(f"✅ داده‌ها با تنظیمات ساده در {filename} ذخیره شد")
            except Exception as e2:
                print(f"❌ خطا در تلاش مجدد: {e2}")

def scrape_z4car(force_update=False):
    """استخراج قیمت خودرو از سایت زد فور کار با بهینه‌سازی سرعت
    
    Args:
        force_update (bool): اگر True باشد، بدون توجه به زمان فایل، داده‌ها مجدداً استخراج می‌شوند
    """
    # بررسی وجود فایل اکسل قبلی برای جلوگیری از استخراج مجدد
    import os
    import time
    
    output_filename_xlsx = "z4car_prices.xlsx"
    if not force_update and os.path.exists(output_filename_xlsx):
        try:
            # بررسی تاریخ فایل - اگر کمتر از 12 ساعت از ایجاد آن گذشته باشد، از آن استفاده کن
            file_time = os.path.getmtime(output_filename_xlsx)
            current_time = time.time()
            hours_diff = (current_time - file_time) / 3600
            
            if hours_diff < 12:  # اگر کمتر از 12 ساعت گذشته باشد
                print(f"🚗 استفاده از قیمت‌های زد فور کار ذخیره شده قبلی ({hours_diff:.1f} ساعت پیش)")
                df = pd.read_excel(output_filename_xlsx)
                # تبدیل به فرمت مورد نیاز
                car_data = []
                for _, row in df.iterrows():
                    car_name = row['Car Name'] if 'Car Name' in df.columns else row['نام خودرو']
                    price = row['Price'] if 'Price' in df.columns else row['قیمت (تومان)']
                    # استخراج عدد قیمت از رشته
                    price_number = re.sub(r'[^\d]', '', str(price))
                    if price_number:
                        price_number = int(price_number)
                    else:
                        price_number = 0
                    
                    car_data.append({
                        'نام خودرو': car_name,
                        'وضعیت': 'نامشخص',
                        'سال': 'نامشخص',
                        'قیمت (تومان)': f"{price_number:,}",
                        'قیمت عددی': price_number
                    })
                    
                    # استفاده از لاگ پیشرفت برای نمایش وضعیت
                    if len(car_data) % Z4CAR_LOG_INTERVAL == 0:
                        log_progress(f"بارگذاری شد: {car_name} - {price_number:,} تومان")
                
                print(f"✅ {len(car_data)} قیمت خودرو از زد فور کار بارگذاری شد")
                return car_data
            else:
                print(f"⚠️ فایل قیمت‌های زد فور کار قدیمی است ({hours_diff:.1f} ساعت). در حال به‌روزرسانی...")
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری فایل قبلی زد فور کار: {e}")
    elif force_update:
        print("🔄 درخواست به‌روزرسانی اجباری قیمت‌های زد فور کار...")
    
    print("🚗 شروع استخراج قیمت‌های جدید خودرو از Z4Car...")
    # اگر فایل قبلی وجود نداشت یا قدیمی بود، استخراج جدید انجام بده
    scraper = Z4CarScraper()
    cars_data = scraper.scrape_all_prices(force_update)
    if cars_data:
        scraper.save_to_excel(cars_data, output_filename_xlsx)
        print(f"✅ استخراج {len(cars_data)} قیمت خودرو از Z4Car با موفقیت انجام شد")
    else:
        print("❌ استخراج قیمت‌های Z4Car ناموفق بود")
    return cars_data

if __name__ == "__main__":
    scrape_hamrah_mechanic()
    scrape_z4car()
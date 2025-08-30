import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class Z4CarScraper:
    def __init__(self):
        self.base_url = "https://z4car.com"
        self.price_url = "https://z4car.com/price"
        self.driver = None
        
    def setup_driver(self):
        """راه‌اندازی WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # تلاش برای استفاده از webdriver-manager
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("WebDriver با webdriver-manager راه‌اندازی شد")
            except Exception as e:
                print(f"خطا در webdriver-manager: {e}")
                print("تلاش برای استفاده از chromedriver سیستم...")
                self.driver = webdriver.Chrome(options=chrome_options)
                print("WebDriver با chromedriver سیستم راه‌اندازی شد")
            
            # تنظیمات اضافی
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            
            return True
            
        except Exception as e:
            print(f"خطا در راه‌اندازی WebDriver: {e}")
            return False
    
    def get_page_content(self, url):
        """دریافت محتوای صفحه با Selenium"""
        try:
            print(f"بارگذاری صفحه: {url}")
            self.driver.get(url)
            
            # انتظار برای بارگذاری کامل صفحه
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # انتظار اضافی برای بارگذاری محتوای JavaScript
            time.sleep(5)
            
            # اسکرول برای بارگذاری محتوای بیشتر
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"خطا در دریافت صفحه: {e}")
            return None
    
    def clean_price(self, price_text):
        """تمیز کردن متن قیمت و تبدیل به عدد - استخراج اولین قیمت معتبر"""
        if not price_text:
            return None
        
        # استخراج تمام اعداد با کاما از متن
        price_matches = re.findall(r'\d{1,3}(?:,\d{3})+', price_text)
        
        if price_matches:
            # انتخاب اولین قیمت معتبر
            for price_match in price_matches:
                clean_price_text = price_match.replace(',', '')
                try:
                    price_value = int(clean_price_text)
                    # فقط قیمت‌های بالای 10 میلیون تومان را در نظر بگیر
                    if price_value > 10000000:
                        return price_value
                except:
                    continue
        
        return None
    
    def extract_individual_prices(self, price_text):
        """استخراج تمام قیمت‌های جداگانه از متن"""
        if not price_text:
            return []
        
        # استخراج تمام اعداد با کاما
        price_matches = re.findall(r'\d{1,3}(?:,\d{3})+', price_text)
        valid_prices = []
        
        for price_match in price_matches:
            clean_price_text = price_match.replace(',', '')
            try:
                price_value = int(clean_price_text)
                # فقط قیمت‌های بالای 10 میلیون تومان
                if price_value > 10000000:
                    valid_prices.append(price_value)
            except:
                continue
        
        return valid_prices
    
    def extract_car_prices(self, html_content):
        """استخراج قیمت‌های خودرو از HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        cars_data = []
        
        print("جستجوی بلوک‌های قیمت خودرو...")
        
        # ذخیره HTML برای دیباگ
        with open('/Users/erfantaghavi/PycharmProjects/pythonProject/z4car_debug.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML صفحه در فایل z4car_debug.html ذخیره شد")
        
        # جستجوی دقیق‌تر بر اساس ساختار سایت
        # الگوی 1: جستجوی عناصر entry-body که حاوی اطلاعات خودرو هستند
        entry_bodies = soup.find_all('div', class_='entry-body')
        print(f"یافت شد {len(entry_bodies)} entry-body")
        
        for entry in entry_bodies:
            try:
                # جستجوی لیست‌های داخل entry-body
                ul_elements = entry.find_all('ul')
                for ul in ul_elements:
                    li_elements = ul.find_all('li')
                    if len(li_elements) >= 4:  # حداقل 4 ستون اطلاعات
                        # استخراج اطلاعات از ستون‌ها
                        car_info = self.extract_from_columns(li_elements)
                        if car_info:
                            cars_data.append(car_info)
                            print(f"استخراج شد: {car_info['نام خودرو']} - {car_info['قیمت (تومان)']}")
            except Exception as e:
                continue
        
        # اگر روش اول کار نکرد، از روش عمومی استفاده کن
        if not cars_data:
            print("استفاده از روش عمومی...")
            cars_data = self.extract_general_method(soup)
        
        return cars_data
    
    def extract_from_columns(self, li_elements):
        """استخراج اطلاعات از ستون‌های لیست"""
        try:
            car_name = "نامشخص"
            condition = "نامشخص"
            year = "نامشخص"
            price_text = "نامشخص"
            
            # بررسی هر ستون
            for i, li in enumerate(li_elements):
                text = li.get_text(strip=True)
                
                # ستون اول معمولاً تصویر یا نام خودرو
                if i == 0:
                    # جستجوی نام خودرو در alt تصویر یا متن
                    img = li.find('img')
                    if img and img.get('alt'):
                        alt_text = img.get('alt')
                        car_match = re.search(r'(آئودی|پژو|سمند|پراید|تیبا|دنا|رانا|سایپا|کوییک|آریو|شاهین|تارا|ساینا|مزدا|هوندا|تویوتا|نیسان|هیوندای|کیا|چری|ام وی ام|دوو|رنو|فولکس|بی ام و|بنز|آلفارومئو|آمیکو)[^\n]*', alt_text, re.I)
                        if car_match:
                            car_name = car_match.group()
                    
                    # اگر در alt پیدا نشد، در متن جستجو کن
                    if car_name == "نامشخص":
                        car_match = re.search(r'قیمت\s+([^\n]+)', text, re.I)
                        if car_match:
                            car_name = car_match.group(1)
                
                # جستجوی وضعیت (صفر/کارکرده)
                if "صفر" in text:
                    condition = "صفر کیلومتر"
                elif "کارکرده" in text:
                    condition = "کارکرده"
                
                # جستجوی سال
                year_match = re.search(r'(20\d{2}|13\d{2}|14\d{2})', text)
                if year_match:
                    year = year_match.group(1)
                
                # جستجوی قیمت
                price_match = re.search(r'\d{1,3}(,\d{3})+', text)
                if price_match:
                    price_text = text
            
            # اگر قیمت پیدا شد، اطلاعات را برگردان
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
            
        except Exception as e:
            return None
    
    def extract_general_method(self, soup):
        """روش عمومی استخراج قیمت - تمام خودروها"""
        cars_data = []
        
        # جستجوی عناصر حاوی قیمت خودرو
        price_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'price|car|vehicle', re.I))
        price_elements.extend(soup.find_all(string=re.compile(r'قیمت', re.I)))
        price_elements.extend(soup.find_all(string=re.compile(r'\d{1,3}(,\d{3})+')))
        
        print(f"یافت شد {len(price_elements)} عنصر برای بررسی")
        print("استخراج تمام خودروها از اول تا آخر...")
        
        for element in price_elements:
            try:
                if isinstance(element, str):
                    text = element
                    parent = None
                else:
                    text = element.get_text(strip=True)
                    parent = element.parent
                
                # استخراج قیمت‌های جداگانه
                individual_prices = self.extract_individual_prices(text)
                
                if individual_prices:
                    # جستجوی نام خودرو
                    car_name = "نامشخص"
                    
                    # جستجو در متن فعلی
                    car_patterns = [
                        r'قیمت\s+([^\n]+)',
                        r'(آئودی|پژو|سمند|پراید|تیبا|دنا|رانا|سایپا|کوییک|آریو|شاهین|تارا|ساینا|مزدا|هوندا|تویوتا|نیسان|هیوندای|کیا|چری|ام وی ام|دوو|رنو|فولکس|بی ام و|بنز|آلفارومئو|آمیکو|لکسوس|اینفینیتی|اکورا|کادیلاک|لینکلن|جگوار|لندرور|پورشه|فراری|لامبورگینی|مازراتی|استون مارتین|بنتلی|رولزرویس|میتسوبیشی|سوبارو|مینی|اسمارت|تسلا|ولوو|سیتروئن|پیکاپ|ون|کامیونت|هاوال|گک|چانگان|جیلی|بی وای دی|لیفان|دانگ فنگ|فاو|گریت وال|هایما|چانا|زوتی|جک|ام جی|رنو|دیسی|سانگ یانگ|تاتا|ماهیندرا|فورس|آشوک|ایسوزو|هینو|یودیان|فوتون|شاکمن|ونوسیا|هونگچی|بسترن|کاپرا|دیگنیتی|فیدلیتی|رسپکت|لندمارک|بستیون|تانک|اکستریم|فونیکس)[^\n]*',
                    ]
                    
                    for pattern in car_patterns:
                        match = re.search(pattern, text, re.I)
                        if match:
                            car_name = match.group(1) if match.lastindex else match.group()
                            break
                    
                    # جستجو در عنصر والد
                    if car_name == "نامشخص" and parent:
                        parent_text = parent.get_text(strip=True)
                        for pattern in car_patterns:
                            match = re.search(pattern, parent_text, re.I)
                            if match:
                                car_name = match.group(1) if match.lastindex else match.group()
                                break
                    
                    # جستجو در عناصر مجاور
                    if car_name == "نامشخص" and parent:
                        siblings = parent.find_previous_siblings() + parent.find_next_siblings()
                        for sibling in siblings[:3]:  # بررسی 3 عنصر مجاور
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
                    
                    # ایجاد رکورد جداگانه برای هر قیمت
                    for i, price in enumerate(individual_prices):
                        # اگر چندین قیمت وجود دارد، شماره‌گذاری کن
                        display_name = car_name if len(individual_prices) == 1 else f"{car_name} (قیمت {i+1})"
                        
                        cars_data.append({
                            'نام خودرو': display_name.strip(),
                            'وضعیت': condition,
                            'سال': year,
                            'قیمت (تومان)': f"{price:,}",
                            'قیمت عددی': price
                        })
                        
                        print(f"استخراج شد: {display_name} - {price:,} تومان")
                
            except Exception as e:
                continue
        
        return cars_data
    
    def extract_all_data(self, soup):
        """استخراج تمام داده‌ها بدون فیلتر آئودی"""
        cars_data = []
        
        # جستجوی عناصر حاوی قیمت خودرو
        price_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'price|car|vehicle', re.I))
        price_elements.extend(soup.find_all(string=re.compile(r'قیمت', re.I)))
        price_elements.extend(soup.find_all(string=re.compile(r'\d{1,3}(,\d{3})+')))
        
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
                    # جستجوی نام خودرو
                    car_name = "نامشخص"
                    
                    car_patterns = [
                        r'قیمت\s+([^\n]+)',
                        r'(آئودی|پژو|سمند|پراید|تیبا|دنا|رانا|سایپا|کوییک|آریو|شاهین|تارا|ساینا|مزدا|هوندا|تویوتا|نیسان|هیوندای|کیا|چری|ام وی ام|دوو|رنو|فولکس|بی ام و|بنز|آلفارومئو|آمیکو)[^\n]*',
                    ]
                    
                    for pattern in car_patterns:
                        match = re.search(pattern, text, re.I)
                        if match:
                            car_name = match.group(1) if match.lastindex else match.group()
                            break
                    
                    condition = "نامشخص"
                    if "صفر" in text.lower():
                        condition = "صفر کیلومتر"
                    elif "کارکرده" in text.lower():
                        condition = "کارکرده"
                    
                    year_match = re.search(r'(20\d{2}|13\d{2}|14\d{2})', text)
                    year = year_match.group(1) if year_match else "نامشخص"
                    
                    for i, price in enumerate(individual_prices):
                        display_name = car_name if len(individual_prices) == 1 else f"{car_name} (قیمت {i+1})"
                        
                        cars_data.append({
                            'نام خودرو': display_name.strip(),
                            'وضعیت': condition,
                            'سال': year,
                            'قیمت (تومان)': f"{price:,}",
                            'قیمت عددی': price,
                            'متن اصلی': text[:100] + '...' if len(text) > 100 else text
                        })
                
            except Exception as e:
                continue
        
        return cars_data
    
    def scrape_all_prices(self):
        """استخراج تمام قیمت‌های خودرو"""
        print("شروع استخراج قیمت‌های خودرو از z4car.com...")
        
        # راه‌اندازی WebDriver
        if not self.setup_driver():
            return []
        
        try:
            # دریافت صفحه اصلی قیمت‌ها
            html_content = self.get_page_content(self.price_url)
            if not html_content:
                print("خطا در دریافت صفحه اصلی")
                return []
            
            print("تجزیه و تحلیل محتوای صفحه...")
            cars_data = self.extract_car_prices(html_content)
            
            # حذف تکراری‌ها
            unique_cars = []
            seen = set()
            
            for car in cars_data:
                key = (car['نام خودرو'], car['قیمت عددی'])
                if key not in seen:
                    seen.add(key)
                    unique_cars.append(car)
            
            print(f"استخراج {len(unique_cars)} خودروی منحصر به فرد")
            return unique_cars
            
        finally:
            # بستن WebDriver
            if self.driver:
                self.driver.quit()
                print("WebDriver بسته شد")
    
    def save_to_excel(self, cars_data, filename):
        """ذخیره داده‌ها در فایل Excel"""
        if not cars_data:
            print("هیچ داده‌ای برای ذخیره وجود ندارد")
            return
        
        try:
            df = pd.DataFrame(cars_data)
            
            # مرتب‌سازی بر اساس قیمت
            df = df.sort_values('قیمت عددی', ascending=False)
            
            # حذف ستون قیمت عددی از خروجی نهایی
            df_output = df.drop('قیمت عددی', axis=1)
            
            # ذخیره در Excel
            df_output.to_excel(filename, index=False, engine='openpyxl')
            
            # ذخیره در CSV نیز
            csv_filename = filename.replace('.xlsx', '.csv')
            df_output.to_csv(csv_filename, index=False, encoding='utf-8')
            
            print(f"\nداده‌ها ذخیره شد:")
            print(f"- فایل Excel: {filename}")
            print(f"- فایل CSV: {csv_filename}")
            print(f"- تعداد رکوردها: {len(df_output)}")
            
            # نمایش آمار
            if len(df) > 0:
                print(f"\n=== آمار قیمت‌ها ===")
                print(f"بالاترین قیمت: {df['قیمت عددی'].max():,} تومان")
                print(f"پایین‌ترین قیمت: {df['قیمت عددی'].min():,} تومان")
                print(f"میانگین قیمت: {df['قیمت عددی'].mean():,.0f} تومان")
            
            return df_output
            
        except Exception as e:
            print(f"خطا در ذخیره فایل: {e}")
            return None

# اجرای اسکریپت
if __name__ == "__main__":
    scraper = Z4CarScraper()
    
    # استخراج داده‌ها
    cars_data = scraper.scrape_all_prices()
    
    if cars_data:
        # ذخیره در فایل
        output_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/z4car_prices.xlsx"
        result_df = scraper.save_to_excel(cars_data, output_file)
        
        if result_df is not None:
            print("\n=== نمونه 10 رکورد اول ===")
            print(result_df.head(10).to_string(index=False))
    else:
        print("هیچ داده‌ای استخراج نشد.")
        print("لطفاً فایل z4car_debug.html را بررسی کنید تا ساختار صفحه را مشاهده کنید.")
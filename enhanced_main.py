#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت بهبود یافته اسکرپ دیوار با قیمت‌گذاری هوشمند
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import signal
import random
import re
from difflib import SequenceMatcher
import numpy as np

# تلاش برای import محاسبه‌گرهای قیمت
try:
    from car_price_calculator import CarPriceCalculator
    MAIN_CALC_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ خطا در import محاسبه‌گر اصلی: {e}")
    MAIN_CALC_AVAILABLE = False

try:
    from column_based_calculator import ColumnBasedCarPriceCalculator
    COLUMN_CALC_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ خطا در import محاسبه‌گر ستونی: {e}")
    COLUMN_CALC_AVAILABLE = False

class OptimizedDivarScraper:
    def __init__(self):
        self.driver = None
        self.graceful_exit = False
        self.processed_count = 0
        self.all_ads_data = []
        self.batch_size = 10
        
        # محاسبه‌گرهای قیمت
        self.main_calculator = None
        self.column_calculator = None
        self.market_prices = {}
        
        # تنظیم signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # بارگذاری محاسبه‌گرها
        self.load_calculators()
    
    def signal_handler(self, signum, frame):
        """مدیریت سیگنال‌های خروج"""
        print("\n🛑 دریافت سیگنال توقف...")
        self.graceful_exit = True
        self.finalize_and_exit()
    
    def load_calculators(self):
        """بارگذاری محاسبه‌گرهای قیمت"""
        try:
            if MAIN_CALC_AVAILABLE:
                self.main_calculator = CarPriceCalculator()
                print("✅ محاسبه‌گر اصلی فعال شد")
            
            if COLUMN_CALC_AVAILABLE:
                self.column_calculator = ColumnBasedCarPriceCalculator()
                print("✅ محاسبه‌گر ستونی فعال شد")
            
            # بارگذاری قیمت‌های بازار
            self.load_market_prices()
            
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری محاسبه‌گرها: {e}")
    
    def load_market_prices(self):
        """بارگذاری قیمت‌های بازار از فایل‌های اکسل"""
        try:
            # بارگذاری از فایل همراه مکانیک
            hamrah_file = "hamrah_mechanic_prices.xlsx"
            if os.path.exists(hamrah_file):
                df_hamrah = pd.read_excel(hamrah_file)
                for _, row in df_hamrah.iterrows():
                    car_name = str(row.get('Car Name', '')).strip()
                    price_str = str(row.get('Price', '')).strip()
                    # استخراج عدد از متن قیمت
                    price_numbers = re.findall(r'\d{1,3}(?:,\d{3})*', price_str)
                    if price_numbers:
                        try:
                            price = int(price_numbers[0].replace(',', ''))
                            # تبدیل میلیون به تومان
                            if 'میلیون' in price_str:
                                price = price * 1000000
                            elif 'هزار' in price_str:
                                price = price * 1000
                            elif price < 100000:  # احتمالاً میلیون تومان است
                                price = price * 1000000
                        except:
                            price = 0
                    else:
                        price = 0
                    if car_name and price > 100000:  # حداقل 100 هزار تومان
                        self.market_prices[car_name] = price
                print(f"📊 بارگذاری {len(df_hamrah)} قیمت از همراه مکانیک")
            
            # بارگذاری از فایل Z4Car
            z4car_file = "z4car_prices.xlsx"
            if os.path.exists(z4car_file):
                df_z4car = pd.read_excel(z4car_file)
                for _, row in df_z4car.iterrows():
                    car_name = str(row.get('نام خودرو', '')).strip()
                    price_str = str(row.get('قیمت (تومان)', '')).strip()
                    # استخراج عدد از متن قیمت
                    price_numbers = re.findall(r'\d{1,3}(?:,\d{3})*', price_str)
                    if price_numbers:
                        try:
                            price = int(price_numbers[0].replace(',', ''))
                            # تبدیل میلیون به تومان
                            if 'میلیون' in price_str:
                                price = price * 1000000
                            elif 'هزار' in price_str:
                                price = price * 1000
                            elif price < 100000:  # احتمالاً میلیون تومان است
                                price = price * 1000000
                        except:
                            price = 0
                    else:
                        price = 0
                    if car_name and price > 100000:  # حداقل 100 هزار تومان
                        # اگر قیمت از قبل وجود دارد، میانگین بگیر
                        if car_name in self.market_prices:
                            self.market_prices[car_name] = int((self.market_prices[car_name] + price) / 2)
                        else:
                            self.market_prices[car_name] = price
                print(f"📊 بارگذاری {len(df_z4car)} قیمت از Z4Car")
            
            # بارگذاری از فایل ترکیبی اگر وجود دارد
            combined_file = "combined_market_prices.xlsx"
            if os.path.exists(combined_file):
                df_combined = pd.read_excel(combined_file)
                for _, row in df_combined.iterrows():
                    car_name = str(row.get('نام خودرو', '')).strip()
                    price_str = str(row.get('قیمت', '')).strip()
                    if not price_str or price_str == 'nan':
                        price_str = str(row.get('قیمت (تومان)', '')).strip()
                    
                    # استخراج عدد از متن قیمت
                    price_numbers = re.findall(r'\d{1,3}(?:,\d{3})*', price_str)
                    if price_numbers:
                        try:
                            price = int(price_numbers[0].replace(',', ''))
                            # تبدیل میلیون به تومان
                            if 'میلیون' in price_str:
                                price = price * 1000000
                            elif 'هزار' in price_str:
                                price = price * 1000
                            elif price < 100000:  # احتمالاً میلیون تومان است
                                price = price * 1000000
                        except:
                            price = 0
                    else:
                        price = 0
                    if car_name and price > 100000:  # حداقل 100 هزار تومان
                        self.market_prices[car_name] = price
                print(f"📊 بارگذاری {len(df_combined)} قیمت از فایل ترکیبی")
            
            print(f"📊 مجموع {len(self.market_prices)} قیمت روز بارگذاری شد")
            
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری قیمت‌های بازار: {e}")
    
    def create_driver(self):
        """ایجاد Chrome driver ساده"""
        try:
            chrome_options = Options()
            # تنظیمات حداقلی
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(60)
            
            print("✅ Chrome driver راه‌اندازی شد")
            return True
            
        except Exception as e:
            print(f"❌ خطا در راه‌اندازی Chrome driver: {e}")
            return False
    
    def find_market_price(self, car_name, year=None):
        """یافتن قیمت بازار برای خودروی مشخص"""
        if not car_name or not self.market_prices:
            return None
        
        # تمیز کردن نام خودرو
        clean_car_name = car_name.strip().replace('\u200c', ' ')  # حذف نیم‌فاصله
        clean_car_name = re.sub(r'[^\u0600-\u06FF\s]', '', clean_car_name).strip()
        
        best_match = None
        best_ratio = 0
        
        # جستجوی دقیق اول
        for market_car, price in self.market_prices.items():
            clean_market_car = market_car.strip().replace('\u200c', ' ')
            
            # بررسی تطبیق دقیق
            if clean_car_name.lower() == clean_market_car.lower():
                return price
            
            # بررسی شامل بودن کلمات کلیدی
            car_words = clean_car_name.lower().split()
            market_words = clean_market_car.lower().split()
            
            # شمارش کلمات مشترک
            common_words = set(car_words) & set(market_words)
            if len(common_words) >= 2:  # حداقل 2 کلمه مشترک
                ratio = len(common_words) / max(len(car_words), len(market_words))
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = price
            
            # بررسی شباهت متنی
            ratio = SequenceMatcher(None, clean_car_name.lower(), clean_market_car.lower()).ratio()
            
            # اگر سال موجود است، امتیاز بیشتری بده
            if year and str(year) in market_car:
                ratio += 0.3
            
            if ratio > best_ratio and ratio > 0.6:  # حداقل 60% شباهت
                best_ratio = ratio
                best_match = price
        
        # اگر سال مشخص شده، سعی کن خودروی مشابه با سال پیدا کن
        if year and best_match:
            year_str = str(year)
            year_matches = []
            
            for market_car, price in self.market_prices.items():
                if year_str in market_car:
                    # بررسی اینکه برند یکسان باشد
                    car_words = clean_car_name.lower().split()
                    if car_words and car_words[0] in market_car.lower():
                        year_matches.append((market_car, price))
            
            if year_matches:
                # انتخاب بهترین تطبیق با سال
                best_year_match = None
                best_year_ratio = 0
                for year_car, price in year_matches:
                    ratio = SequenceMatcher(None, clean_car_name.lower(), year_car.lower()).ratio()
                    if ratio > best_year_ratio:
                        best_year_ratio = ratio
                        best_year_match = price
                
                if best_year_match and best_year_ratio > 0.4:
                    best_match = best_year_match
        
        if best_match and best_ratio > 0.4:  # حداقل 40% شباهت
            print(f"🔍 تطبیق یافت: '{car_name}' (شباهت: {best_ratio:.2f})")
            return best_match
        
        print(f"❌ قیمت روز برای '{car_name}' یافت نشد")
        return None
    
    def extract_ad_details(self, ad_url):
        """استخراج جزئیات کامل آگهی"""
        try:
            self.driver.get(ad_url)
            time.sleep(2)
            
            # ساختار داده آگهی مطابق با divar_ads_main.xlsx
            ad_data = {
                'عنوان آگهی': '',
                'برند و تیپ': '',
                'نام خودرو': '',
                'سال': '',
                'کیلومتر': '',
                'قیمت آگهی (تومان)': '',
                'قیمت روز (تومان)': '',
                'منبع قیمت': '',
                'وضعیت موتور': '',
                'وضعیت شاسی': '',
                'وضعیت بدنه': '',
                'مشکلات تشخیص داده شده': '',
                'افت کارکرد': '',
                'افت سن خودرو': '',
                'افت مشکلات': '',
                'درصد افت کل': '',
                'قیمت تخمینی (تومان)': '',
                'توضیحات': '',
                'رنگ': '',
                'گیربکس': '',
                'بیمه شخص ثالث': '',
                'معاوضه': '',
                'دسته بندی خودرو': 'خودرو',
                'شماره تلفن': '',
                'زمان و مکان': '',
                'لینک آگهی': ad_url
            }
            
            # استخراج عنوان
            try:
                title_selectors = [
                    'h1[data-testid="post-title"]',
                    'h1.kt-page-title__title',
                    'h1'
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if title_element.text.strip():
                            title_text = title_element.text.strip()
                            ad_data['عنوان آگهی'] = title_text
                            
                            # استخراج برند و تیپ و نام خودرو از عنوان
                            # تشخیص برند با الگوریتم بهبود یافته
                            brands = {
                                'پژو': ['پژو', '206', '207', '405', 'پارس'],
                                'سمند': ['سمند'],
                                'تیبا': ['تیبا'],
                                'پراید': ['پراید'],
                                'کوییک': ['کوییک'],
                                'دنا': ['دنا'],
                                'رانا': ['رانا'],
                                'ساینا': ['ساینا'],
                                'شاهین': ['شاهین'],
                                'تارا': ['تارا'],
                                'پیکان': ['پیکان'],
                                'نیسان': ['نیسان'],
                                'هیوندای': ['هیوندای'],
                                'کیا': ['کیا'],
                                'تویوتا': ['تویوتا'],
                                'بنز': ['بنز'],
                                'بی ام و': ['بی ام و', 'BMW'],
                                'آئودی': ['آئودی', 'audi'],
                                'رنو': ['رنو']
                            }
                            
                            detected_brand = ''
                            detected_model = ''
                            
                            # جستجوی برند
                            for brand_name, keywords in brands.items():
                                for keyword in keywords:
                                    if keyword in title_text:
                                        detected_brand = brand_name
                                        break
                                if detected_brand:
                                    break
                            
                            # استخراج مدل از عنوان
                            model_patterns = [r'(\d{3})', r'(GL)', r'(LX)', r'(تیپ\s*\d+)', r'(v\d+)', r'(پلاس)']
                            for pattern in model_patterns:
                                model_match = re.search(pattern, title_text, re.IGNORECASE)
                                if model_match:
                                    detected_model = model_match.group(1)
                                    break
                            
                            # ترکیب برند و مدل
                            if detected_brand:
                                brand_and_type = detected_brand
                                if detected_model:
                                    brand_and_type += f' {detected_model}'
                                ad_data['برند و تیپ'] = brand_and_type
                            else:
                                # اگر برند تشخیص داده نشد، سعی کن اولین کلمه را به عنوان برند در نظر بگیر
                                first_word = title_text.split()[0] if title_text.split() else ''
                                ad_data['برند و تیپ'] = first_word
                            
                            ad_data['نام خودرو'] = title_text
                            break
                    except:
                        continue
            except:
                pass
            
            # استخراج قیمت آگهی - روش ساده و مستقیم
            try:
                # جستجو در کل متن صفحه برای الگوهای قیمت
                page_source = self.driver.page_source
                
                # الگوهای مختلف قیمت (فارسی و انگلیسی)
                price_patterns = [
                    # الگوهای فارسی
                    r'([۰-۹]{1,3}(?:[،٬][۰-۹]{3})*)\s*میلیون\s*تومان',
                    r'([۰-۹]{1,3}(?:[،٬][۰-۹]{3})*)\s*میلیون',
                    r'قیمت[:\s]*([۰-۹]{1,3}(?:[،٬][۰-۹]{3})*)\s*میلیون',
                    r'([۰-۹]{1,3}(?:[،٬][۰-۹]{3})*)\s*هزار\s*تومان',
                    r'([۰-۹]{1,3}(?:[،٬][۰-۹]{3})*)\s*هزار',
                    r'قیمت[:\s]*([۰-۹]{1,3}(?:[،٬][۰-۹]{3})*)\s*هزار',
                    r'([۰-۹]{6,})\s*تومان',
                    r'قیمت[:\s]*([۰-۹]{6,})',
                    r'([۰-۹]{1,3}(?:[،٬][۰-۹]{3})*(?:[،٬][۰-۹]{3})*(?:[،٬][۰-۹]{3})*)\s*تومان',
                    
                    # الگوهای انگلیسی
                    r'(\d{1,3}(?:,\d{3})*)\s*میلیون\s*تومان',
                    r'(\d{1,3}(?:,\d{3})*)\s*میلیون',
                    r'قیمت[:\s]*(\d{1,3}(?:,\d{3})*)\s*میلیون',
                    r'(\d{1,3}(?:,\d{3})*)\s*هزار\s*تومان',
                    r'(\d{1,3}(?:,\d{3})*)\s*هزار',
                    r'قیمت[:\s]*(\d{1,3}(?:,\d{3})*)\s*هزار',
                    r'(\d{6,})\s*تومان',  # قیمت مستقیم تومان
                    r'قیمت[:\s]*(\d{6,})'
                ]
                
                price_found = False
                for pattern in price_patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        # انتخاب بزرگترین عدد (احتمالاً قیمت اصلی)
                        price_value = max(matches, key=lambda x: int(self.convert_persian_to_english(x).replace(',', '').replace('،', '').replace('٬', '')))
                        
                        # تبدیل اعداد فارسی به انگلیسی
                        price_value_clean = self.convert_persian_to_english(price_value)
                        price_num = int(price_value_clean.replace(',', '').replace('،', '').replace('٬', ''))
                        
                        if 'میلیون' in pattern:
                            final_price = price_num * 1000000
                        elif 'هزار' in pattern:
                            final_price = price_num * 1000
                        else:
                            final_price = price_num
                        
                        # فقط قیمت‌های معقول را قبول کن (بین 10 میلیون تا 10 میلیارد تومان)
                        if 100000 <= final_price <= 10000000000:
                            ad_data['قیمت آگهی (تومان)'] = str(final_price)
                            price_found = True
                            break
                
                # اگر هیچ قیمتی پیدا نشد، تلاش با CSS selector
                if not price_found:
                    try:
                        price_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > div:nth-child(9)'
                        price_element = self.driver.find_element(By.CSS_SELECTOR, price_selector)
                        price_text = price_element.text.strip()
                        
                        # جستجو برای اعداد در متن
                        numbers = re.findall(r'\d{1,3}(?:,\d{3})*', price_text)
                        if numbers:
                            # انتخاب بزرگترین عدد
                            largest_num = max(numbers, key=lambda x: int(x.replace(',', '')))
                            num_value = int(largest_num.replace(',', ''))
                            
                            # تشخیص واحد از متن
                            if 'میلیون' in price_text:
                                final_price = num_value * 10000
                            elif 'هزار' in price_text:
                                final_price = num_value * 1000
                            else:
                                final_price = num_value
                            
                            if 100000 <= final_price <= 10000000000:
                                ad_data['قیمت آگهی (تومان)'] = str(final_price)
                    except:
                        pass
                        
            except Exception as e:
                print(f"خطا در استخراج قیمت: {e}")
                pass
            
            # استخراج مشخصات با CSS selector های جدید
            try:
                # زمان و مکان
                try:
                    time_location_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.kt-page-title > div > div'
                    time_location_element = self.driver.find_element(By.CSS_SELECTOR, time_location_selector)
                    ad_data['زمان و مکان'] = time_location_element.text.strip()
                except:
                    pass
                
                # کارکرد (کیلومتر)
                try:
                    km_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > table > tbody > tr > td:nth-child(1)'
                    km_element = self.driver.find_element(By.CSS_SELECTOR, km_selector)
                    text = km_element.text.strip()
                    # استخراج عدد از متن
                    numbers = re.findall(r'[\d,]+', text)
                    if numbers:
                        # تبدیل کیلومتر به هزار
                         km_value = int(numbers[0].replace(',', ''))
                         # همیشه کیلومتر را به هزار نمایش بده
                         ad_data['کیلومتر'] = f"{km_value:,} هزار"
                    else:
                        ad_data['کیلومتر'] = text
                except:
                    pass
                
                # مدل یا سال
                try:
                    year_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > table > tbody > tr > td:nth-child(2)'
                    year_element = self.driver.find_element(By.CSS_SELECTOR, year_selector)
                    text = year_element.text.strip()
                    # جستجوی سال در متن
                    year_match = re.search(r'(13\d{2}|14\d{2}|20\d{2})', text)
                    if year_match:
                        ad_data['سال'] = year_match.group(1)
                    else:
                        ad_data['سال'] = text
                except:
                    pass
                
                # رنگ
                try:
                    color_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > table > tbody > tr > td:nth-child(3)'
                    color_element = self.driver.find_element(By.CSS_SELECTOR, color_selector)
                    ad_data['رنگ'] = color_element.text.strip()
                except:
                    pass
                
                # مشکلات موتور/گیربکس
                try:
                    motor_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > div:nth-child(12)'
                    motor_element = self.driver.find_element(By.CSS_SELECTOR, motor_selector)
                    ad_data['مشکلات تشخیص داده شده'] = motor_element.text.strip()
                except:
                    pass
                
                # بدنه
                try:
                    body_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > div:nth-child(16)'
                    body_element = self.driver.find_element(By.CSS_SELECTOR, body_selector)
                    ad_data['وضعیت بدنه'] = body_element.text.strip()
                except:
                    pass
                
                # افت موتور/گیربکس
                try:
                    chassis_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > div:nth-child(14)'
                    chassis_element = self.driver.find_element(By.CSS_SELECTOR, chassis_selector)
                    ad_data['افت مشکلات'] = chassis_element.text.strip()
                except:
                    pass
                
                # وضعیت بیمه
                try:
                    insurance_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > div:nth-child(5)'
                    insurance_element = self.driver.find_element(By.CSS_SELECTOR, insurance_selector)
                    ad_data['بیمه شخص ثالث'] = insurance_element.text.strip()
                except:
                    pass
                
                # نوع گیربکس
                try:
                    gearbox_selector = '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > div:nth-child(7)'
                    gearbox_element = self.driver.find_element(By.CSS_SELECTOR, gearbox_selector)
                    ad_data['گیربکس'] = gearbox_element.text.strip()
                except:
                    pass
                
                # معاوضه و فروش فوری
                try:
                    for i in range(1, 10):
                        try:
                            element_selector = f'#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section:nth-child(1) > div.post-page__section--padded > div:nth-child({i})'
                            element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
                            element_text = element.text.strip()
                            
                            if 'معاوضه' in element_text:
                                ad_data['معاوضه'] = element_text
                            elif 'فوری' in element_text:
                                ad_data['توضیحات'] = element_text
                            elif 'تلفن' in element_text or 'شماره' in element_text:
                                ad_data['شماره تلفن'] = element_text
                        except:
                            continue
                except:
                    pass
                
                # استخراج توضیحات از بخش مشخص شده
                try:
                    description_element = self.driver.find_element(By.CSS_SELECTOR, '#app > div.container--has-footer-d86a9.kt-container > div > main > article > div > div.kt-col-5 > section.post-page__section--padded')
                    description_text = description_element.text.strip()
                    if description_text and not ad_data['توضیحات']:
                        ad_data['توضیحات'] = description_text
                except:
                    pass
            except Exception as e:
                print(f"خطا در استخراج مشخصات: {e}")
            
            # تنظیم نام خودرو برای محاسبه قیمت (از عنوان آگهی)
            car_name = ad_data['نام خودرو'] if ad_data['نام خودرو'] else ''
            
            # محاسبه قیمت‌های هوشمند
            self.calculate_smart_pricing(ad_data)
            
            return ad_data
            
        except Exception as e:
            print(f"❌ خطا در استخراج آگهی {ad_url}: {e}")
            return None
    
    def convert_persian_to_english(self, text):
        """تبدیل اعداد فارسی به انگلیسی"""
        persian_to_english = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
            '،': ',', '٬': ','
        }
        
        result = text
        for persian, english in persian_to_english.items():
            result = result.replace(persian, english)
        
        return result
    
    def calculate_smart_pricing(self, ad_data):
        """محاسبه قیمت‌های هوشمند"""
        try:
            if not ad_data['نام خودرو']:
                return
            
            # استخراج سال
            year = None
            if ad_data['سال']:
                year_match = re.search(r'(\d{4})', ad_data['سال'])
                if year_match:
                    year = int(year_match.group(1))
            
            # یافتن قیمت بازار
            market_price = self.find_market_price(ad_data['نام خودرو'], year)
            if market_price:
                ad_data['قیمت روز (تومان)'] = f"{market_price:,}"
                ad_data['منبع قیمت'] = 'بازار'
                
                # محاسبه قیمت تخمینی و درصد افت
                if ad_data['قیمت آگهی (تومان)']:
                    try:
                        ad_price = int(ad_data['قیمت آگهی (تومان)'].replace(',', ''))
                        
                        # محاسبه درصد تفاوت
                        price_diff = ((market_price - ad_price) / market_price) * 100
                        ad_data['درصد افت کل'] = f"{price_diff:.1f}%"
                        
                        # قیمت تخمینی با محاسبه‌گر
                        if self.main_calculator:
                            try:
                                estimated = self.main_calculator.calculate_price(ad_data)
                                if estimated:
                                    ad_data['قیمت تخمینی (تومان)'] = f"{estimated:,.0f}"
                            except:
                                # قیمت تخمینی ساده
                                estimated_price = market_price * 0.85
                                ad_data['قیمت تخمینی (تومان)'] = f"{estimated_price:,.0f}"
                        else:
                            # قیمت تخمینی ساده
                            estimated_price = market_price * 0.85
                            ad_data['قیمت تخمینی (تومان)'] = f"{estimated_price:,.0f}"
                    except:
                        pass
        
        except Exception as e:
            print(f"⚠️ خطا در محاسبه قیمت: {e}")
    
    def get_ads(self):
        """دریافت لیست آگهی‌ها"""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            ad_elements = self.driver.find_elements(By.TAG_NAME, "article")
            ad_links = []
            
            for ad_element in ad_elements:
                try:
                    link_element = ad_element.find_element(By.TAG_NAME, "a")
                    href = link_element.get_attribute('href')
                    if href and '/v/' in href:
                        ad_links.append(href)
                except:
                    continue
            
            return ad_links
        
        except Exception as e:
            print(f"❌ خطا در دریافت آگهی‌ها: {e}")
            return []
    
    def save_data(self):
        """ذخیره داده‌ها در فایل اکسل"""
        if not self.all_ads_data:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimized_divar_ads_{timestamp}.xlsx"
            
            df = pd.DataFrame(self.all_ads_data)
            
            # تنظیم ترتیب ستون‌ها مطابق فایل مرجع - لینک آگهی در آخر
            column_order = [
                'عنوان آگهی', 'برند و تیپ', 'نام خودرو', 'سال', 'کیلومتر', 'قیمت آگهی (تومان)', 'قیمت روز (تومان)', 'منبع قیمت',
                'وضعیت موتور', 'وضعیت شاسی', 'وضعیت بدنه', 'مشکلات تشخیص داده شده', 'افت کارکرد', 'افت سن خودرو', 'افت مشکلات',
                'درصد افت کل', 'قیمت تخمینی (تومان)', 'توضیحات', 'رنگ', 'گیربکس', 'بیمه شخص ثالث', 'معاوضه',
                'دسته بندی خودرو', 'شماره تلفن', 'زمان و مکان', 'لینک آگهی'
            ]
            
            # مرتب کردن ستون‌ها
            df = df.reindex(columns=column_order)
            
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print(f"💾 ذخیره {len(self.all_ads_data)} آگهی در {filename}")
            print(f"📊 تعداد آگهی‌های ذخیره شده: {len(self.all_ads_data)}")
            
            # نمایش نمونه از داده‌های استخراج شده
            print("\n📋 نمونه از داده‌های استخراج شده:")
            print(df[['عنوان آگهی', 'قیمت آگهی (تومان)', 'قیمت روز (تومان)', 'درصد افت کل', 'لینک آگهی']].head(3).to_string(index=False))
            
        except Exception as e:
            print(f"❌ خطا در ذخیره: {e}")
    
    def scrape_divar_ads(self, max_ads=50):
        """اسکرپ بهینه شده آگهی‌های دیوار"""
        if not self.create_driver():
            return
        
        try:
            print("🔍 شروع اسکرپ آگهی‌های خودرو...")
            
            # رفتن به صفحه خودرو دیوار
            search_url = "https://divar.ir/s/iran/car"
            self.driver.get(search_url)
            time.sleep(3)
            
            processed_urls = set()
            consecutive_errors = 0
            max_consecutive_errors = 3
            
            while len(processed_urls) < max_ads and not self.graceful_exit:
                try:
                    # دریافت آگهی‌های فعلی
                    current_ads = self.get_ads()
                    
                    if not current_ads:
                        print("❌ آگهی‌ای یافت نشد")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            break
                        time.sleep(5)
                        continue
                    
                    print(f"📋 یافت {len(current_ads)} آگهی در صفحه")
                    consecutive_errors = 0
                    
                    # پردازش آگهی‌های جدید
                    new_ads_found = False
                    for ad_url in current_ads:
                        if self.graceful_exit or len(processed_urls) >= max_ads:
                            break
                        
                        if ad_url not in processed_urls:
                            processed_urls.add(ad_url)
                            new_ads_found = True
                            
                            print(f"🔄 پردازش آگهی {len(processed_urls)}: ...{ad_url[-15:]}")
                            
                            ad_data = self.extract_ad_details(ad_url)
                            if ad_data:
                                self.all_ads_data.append(ad_data)
                                self.processed_count += 1
                                
                                # ذخیره دسته‌ای
                                if len(self.all_ads_data) % self.batch_size == 0:
                                    self.save_data()
                                    self.all_ads_data = []  # پاک کردن برای batch بعدی
                            
                            # تاخیر کوتاه
                            time.sleep(random.uniform(1, 3))
                    
                    # اگر آگهی جدیدی پیدا نشد، اسکرول کن
                    if not new_ads_found:
                        print("📜 اسکرول برای بارگذاری آگهی‌های بیشتر...")
                        
                        # اسکرول تدریجی
                        for _ in range(3):
                            self.driver.execute_script("window.scrollBy(0, 800);")
                            time.sleep(1)
                        
                        # تلاش برای کلیک دکمه "بیشتر"
                        try:
                            load_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                                "span.kt-button__ripple, button[class*='load'], button[class*='more']")
                            
                            for button in load_more_buttons:
                                if button.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", button)
                                    print("✅ کلیک روی دکمه بارگذاری بیشتر")
                                    time.sleep(2)
                                    break
                        except:
                            pass
                        
                        time.sleep(3)
                    
                except Exception as e:
                    print(f"⚠️ خطا در حلقه اصلی: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        break
                    time.sleep(5)
            
            # ذخیره نهایی
            if self.all_ads_data:
                self.save_data()
            
            print(f"✅ اسکرپ کامل شد! تعداد کل: {self.processed_count}")
            
        except Exception as e:
            print(f"❌ خطا در اسکرپ: {e}")
        
        finally:
            self.finalize_and_exit()
    
    def finalize_and_exit(self):
        """نهایی‌سازی و خروج"""
        try:
            if self.all_ads_data:
                self.save_data()
            
            if self.driver:
                self.driver.quit()
                print("🔒 Chrome driver بسته شد")
        
        except Exception as e:
            print(f"⚠️ خطا در نهایی‌سازی: {e}")

def main():
    """تابع اصلی"""
    scraper = OptimizedDivarScraper()
    scraper.scrape_divar_ads(max_ads=100)

if __name__ == "__main__":
    main()
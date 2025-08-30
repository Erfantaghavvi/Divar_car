#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import re
from difflib import SequenceMatcher

def load_market_prices():
    """بارگذاری قیمت‌های بازار از فایل‌های اکسل"""
    market_prices = {}
    
    try:
        # بارگذاری از فایل همراه مکانیک
        hamrah_file = "hamrah_mechanic_prices.xlsx"
        if os.path.exists(hamrah_file):
            df_hamrah = pd.read_excel(hamrah_file)
            print(f"📊 فایل همراه مکانیک: {len(df_hamrah)} ردیف")
            print("نمونه داده‌ها:")
            print(df_hamrah.head(3))
            
            for _, row in df_hamrah.iterrows():
                car_name = str(row.get('Car Name', '')).strip()
                price_str = str(row.get('Price', '')).strip()
                print(f"نام: '{car_name}' - قیمت: '{price_str}'")
                
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
                        print(f"  -> قیمت نهایی: {price:,} تومان")
                    except:
                        price = 0
                        print(f"  -> خطا در تبدیل قیمت")
                else:
                    price = 0
                    print(f"  -> قیمت یافت نشد")
                
                if car_name and price > 100000:  # حداقل 100 هزار تومان
                    market_prices[car_name] = price
                    
                if len(market_prices) >= 5:  # فقط 5 نمونه اول
                    break
        
        print(f"\n📊 مجموع {len(market_prices)} قیمت بارگذاری شد")
        print("نمونه قیمت‌های بارگذاری شده:")
        for name, price in list(market_prices.items())[:5]:
            print(f"  {name}: {price:,} تومان")
            
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری قیمت‌های بازار: {e}")
    
    return market_prices

def find_market_price(market_prices, car_name, year=None):
    """یافتن قیمت بازار برای خودروی مشخص"""
    if not market_prices:
        return None
    
    # تمیز کردن نام خودرو
    clean_car_name = car_name.strip().replace('\u200c', ' ')  # حذف نیم‌فاصله
    clean_car_name = re.sub(r'[^\u0600-\u06FF\sa-zA-Z0-9]', '', clean_car_name).strip()
    
    print(f"\n🔍 جستجو برای: '{car_name}' -> '{clean_car_name}'")
    
    # استخراج برند و مدل اصلی
    brand_mapping = {
        'پژو': ['پژو', 'peugeot'],
        'تیبا': ['تیبا', 'tiba'],
        'نیسان': ['نیسان', 'nissan'],
        'فیدلیتی': ['فیدلیتی', 'fidelity'],
        'سایپا': ['سایپا', 'saipa'],
        'ایران خودرو': ['ایران خودرو', 'ikco'],
        'کیا': ['کیا', 'kia'],
        'هیوندای': ['هیوندای', 'hyundai']
    }
    
    # شناسایی برند
    detected_brand = None
    for brand, aliases in brand_mapping.items():
        for alias in aliases:
            if alias in clean_car_name.lower():
                detected_brand = brand
                break
        if detected_brand:
            break
    
    print(f"  🏷️ برند شناسایی شده: {detected_brand}")
    
    # استخراج مدل/سال از نام
    model_numbers = re.findall(r'\d{2,4}', clean_car_name)
    print(f"  🔢 اعداد یافت شده: {model_numbers}")
    
    best_match = None
    best_ratio = 0
    
    # جستجوی دقیق اول
    for market_car in market_prices:
        clean_market_car = market_car.strip().replace('\u200c', ' ')
        
        # بررسی تطبیق دقیق
        if clean_car_name.lower() == clean_market_car.lower():
            print(f"  ✅ تطبیق دقیق: '{market_car}' - قیمت: {market_prices[market_car]:,}")
            return market_prices[market_car]
        
        # اگر برند شناسایی شده، فقط در خودروهای همان برند جستجو کن
        if detected_brand:
            brand_found = False
            for alias in brand_mapping.get(detected_brand, []):
                if alias in clean_market_car.lower():
                    brand_found = True
                    break
            if not brand_found:
                continue
        
        # بررسی شامل بودن کلمات کلیدی
        car_words = clean_car_name.lower().split()
        market_words = clean_market_car.lower().split()
        
        # شمارش کلمات مشترک
        common_words = set(car_words) & set(market_words)
        if len(common_words) >= 1:  # حداقل 1 کلمه مشترک
            ratio = len(common_words) / max(len(car_words), len(market_words))
            print(f"  🔸 کلمات مشترک با '{market_car}': {common_words} - نسبت: {ratio:.2f}")
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = market_car
        
        # بررسی تطبیق اعداد (مدل/سال)
        market_numbers = re.findall(r'\d{2,4}', clean_market_car)
        number_matches = set(model_numbers) & set(market_numbers)
        if number_matches:
            ratio = len(number_matches) / max(len(model_numbers), len(market_numbers)) if model_numbers else 0
            print(f"  🔢 اعداد مشترک با '{market_car}': {number_matches} - نسبت: {ratio:.2f}")
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = market_car
        
        # بررسی شباهت متنی
        ratio = SequenceMatcher(None, clean_car_name.lower(), clean_market_car.lower()).ratio()
        if ratio > 0.3:  # نمایش شباهت‌های بالای 30%
            print(f"  🔹 شباهت متنی با '{market_car}': {ratio:.2f}")
        if ratio > best_ratio and ratio > 0.3:  # حداقل 30% شباهت
            best_ratio = ratio
            best_match = market_car
    
    if best_match and best_ratio > 0.2:  # حداقل 20% شباهت
        print(f"  ✅ بهترین تطبیق: '{best_match}' - شباهت: {best_ratio:.2f} - قیمت: {market_prices[best_match]:,}")
        return market_prices[best_match]
    
    print(f"  ❌ قیمت روز برای '{car_name}' یافت نشد")
    return None

if __name__ == "__main__":
    print("🚗 تست سیستم قیمت‌های روز")
    print("=" * 50)
    
    # بارگذاری قیمت‌های بازار
    market_prices = load_market_prices()
    
    # تست با نام‌های خودروهای نمونه
    test_cars = [
        "نیسان کمپرسی ۱۴۰۱ اپشنال کولر دار",
        "پژو ۲۰۷ tu3/دنده/فلز صفر خشک تحویل آنی", 
        "صندوق دار تیبا 1397 اقساطی با چک",
        "تیبا یک ۹۴",
        "فیدلیتی الیت مشکی ۵نفره صفر ۷نفره Elite خشک 1404"
    ]
    
    print("\n🧪 تست تطبیق نام‌ها:")
    print("=" * 50)
    
    for car_name in test_cars:
        price = find_market_price(market_prices, car_name)
        if price:
            print(f"✅ {car_name}: {price:,} تومان")
        else:
            print(f"❌ {car_name}: قیمت یافت نشد")
        print("-" * 30)
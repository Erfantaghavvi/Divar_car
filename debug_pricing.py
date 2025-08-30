#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت دیباگ محاسبه قیمت‌ها
"""

import pandas as pd
from difflib import SequenceMatcher
import re

# بارگذاری قیمت‌های بازار
market_prices = {}

# بارگذاری از فایل همراه مکانیک
try:
    df_hamrah = pd.read_excel("hamrah_mechanic_prices.xlsx")
    print(f"ستون‌های همراه مکانیک: {list(df_hamrah.columns)}")
    print(f"نمونه داده‌ها:")
    print(df_hamrah.head())
    
    for _, row in df_hamrah.iterrows():
        car_name = str(row.get('Car Name', '')).strip()
        price_str = str(row.get('Price', '')).strip()
        # حذف کلمه "تومان" و کاما از قیمت
        price_clean = price_str.replace('تومان', '').replace(',', '').strip()
        try:
            price = int(price_clean) if price_clean.isdigit() else 0
        except:
            price = 0
        print(f"  نام: '{car_name}', قیمت اصلی: '{price_str}', قیمت پاک شده: {price}")
        if car_name and price > 0:
            market_prices[car_name] = price
            print(f"    ✅ اضافه شد")
        else:
            print(f"    ❌ رد شد")
        if len(market_prices) >= 5:  # فقط 5 تا اول را نمایش بده
            break
    print(f"📊 بارگذاری {len(df_hamrah)} قیمت از همراه مکانیک")
except Exception as e:
    print(f"خطا در بارگذاری همراه مکانیک: {e}")

# بارگذاری از فایل Z4Car
try:
    df_z4car = pd.read_excel("z4car_prices.xlsx")
    print(f"ستون‌های Z4Car: {list(df_z4car.columns)}")
    
    for _, row in df_z4car.iterrows():
        car_name = str(row.get('نام خودرو', '')).strip()
        price_str = str(row.get('قیمت (تومان)', '')).strip()
        # حذف کلمه "تومان" و کاما از قیمت
        price_clean = price_str.replace('تومان', '').replace(',', '').strip()
        try:
            price = int(price_clean) if price_clean.isdigit() else 0
        except:
            price = 0
        if car_name and price > 0:
            if car_name in market_prices:
                market_prices[car_name] = (market_prices[car_name] + price) / 2
            else:
                market_prices[car_name] = price
    print(f"📊 بارگذاری {len(df_z4car)} قیمت از Z4Car")
except Exception as e:
    print(f"خطا در بارگذاری Z4Car: {e}")

print(f"\n📋 مجموع {len(market_prices)} قیمت بازار بارگذاری شد")

# نمونه‌ای از قیمت‌های بازار
print("\n🔍 نمونه قیمت‌های بازار:")
for i, (name, price) in enumerate(list(market_prices.items())[:10]):
    print(f"  {i+1}. {name}: {price:,} تومان")

def find_market_price(car_name, year=None):
    """یافتن قیمت بازار برای خودرو"""
    if not car_name or not market_prices:
        return None
    
    car_name_clean = re.sub(r'[^\u0600-\u06FF\s]', '', car_name).strip()
    best_match = None
    best_score = 0
    
    print(f"\n🔍 جستجو برای: '{car_name_clean}'")
    
    matches_found = []
    for market_name, price in market_prices.items():
        score = SequenceMatcher(None, car_name_clean, market_name).ratio()
        
        # اگر سال موجود است، امتیاز بیشتری بده
        if year and str(year) in market_name:
            score += 0.3
        
        if score > 0.3:  # نمایش همه تطبیق‌های بالای 30%
            matches_found.append((market_name, price, score))
        
        if score > best_score and score > 0.6:  # حداقل 60% شباهت
            best_score = score
            best_match = price
    
    # نمایش بهترین تطبیق‌ها
    matches_found.sort(key=lambda x: x[2], reverse=True)
    print(f"  بهترین تطبیق‌ها:")
    for name, price, score in matches_found[:5]:
        print(f"    - {name}: {price:,} تومان (امتیاز: {score:.2f})")
    
    if best_match:
        print(f"  ✅ قیمت پیدا شد: {best_match:,} تومان (امتیاز: {best_score:.2f})")
    else:
        if matches_found:
            print(f"  ❌ قیمت پیدا نشد (بهترین امتیاز: {matches_found[0][2]:.2f})")
        else:
            print(f"  ❌ قیمت پیدا نشد")
    
    return best_match

# تست با نام‌های خودروهای نمونه
test_cars = [
    "kmc eagle/حواله کی ام سی ایگل مدل1404",
    "حواله آریسان تحویل ۹۰روزه شرکتی مدل ۱۴۰۴", 
    "فروش یا معاوضه",
    "فروش برلیانس h230",
    "پژو ۲۰۶ مدل ۸۳"
]

print("\n🧪 تست یافتن قیمت برای خودروهای نمونه:")
for car in test_cars:
    find_market_price(car)
    print("-" * 50)
import pandas as pd
import numpy as np
import re
from datetime import datetime
import os
from difflib import SequenceMatcher

class ImprovedCarPriceCalculator:
    def __init__(self):
        # جدول عوامل افت قیمت
        self.depreciation_factors = {
            'high_mileage': {'rate_per_5k': 0.0125},  # 1.25% هر 5 هزار کیلومتر اضافه
            'paint_one_part': {'min': 0.02, 'max': 0.05},  # رنگ یک قطعه
            'paint_two_parts': {'min': 0.05, 'max': 0.08},  # رنگ دو قطعه
            'paint_three_parts': {'min': 0.07, 'max': 0.10},  # رنگ سه قطعه
            'paint_four_plus': {'min': 0.10, 'max': 0.15},  # رنگ چهار قطعه یا بیشتر
            'roof_paint': {'min': 0.10, 'max': 0.15},  # رنگ سقف
            'pillar_paint': {'min': 0.08, 'max': 0.12},  # رنگ ستون‌ها
            'full_paint': {'min': 0.15, 'max': 0.30},  # تمام رنگ
            'paint_chassis_damage': {'min': 0.20, 'max': 0.40},  # رنگ + آسیب شاسی
            'body_part_replacement': {'min': 0.05, 'max': 0.10},  # تعویض قطعه بدنه
            'roof_pillar_repair': {'min': 0.15, 'max': 0.25},  # تعمیر سقف/ستون
            'engine_overhaul': {'min': 0.10, 'max': 0.20},  # موتور تعمیر اساسی
            'gearbox_repair': {'min': 0.07, 'max': 0.12},  # گیربکس تعمیر شده
            'موتور خراب': {'min': 0.25, 'max': 0.40},  # موتور خراب
            'موتور تعویض شده': {'min': 0.15, 'max': 0.25},  # موتور تعویض شده
            'موتور تعمیر شده': {'min': 0.10, 'max': 0.20},  # موتور تعمیر شده
            'شاسی خراب': {'min': 0.30, 'max': 0.50},  # شاسی خراب
            'شاسی تعویض شده': {'min': 0.20, 'max': 0.35},  # شاسی تعویض شده
            'شاسی تعمیر شده': {'min': 0.15, 'max': 0.25},  # شاسی تعمیر شده
            'شاسی آسیب دیده': {'min': 0.10, 'max': 0.20},  # شاسی آسیب دیده
            'suspension_defect': {'min': 0.02, 'max': 0.05},  # سیستم تعلیق معیوب
            'option_defect': {'min': 0.005, 'max': 0.03},  # آپشن معیوب
            'old_tires': {'min': 0.01, 'max': 0.02},  # لاستیک کهنه
            'accident_history': {'min': 0.05, 'max': 0.15}  # سوابق تصادف
        }
        
        # کلمات کلیدی بهبود یافته
        self.keywords = {
            'paint': ['رنگ', 'صافکاری', 'رنگ شده', 'پوشش رنگ', 'بیرنگ', 'رنگی', 'نقاشی'],
            'accident': ['تصادف', 'ضربه', 'خسارت', 'آسیب دیده', 'تصادفی', 'ضربه خورده'],
            'engine': ['موتور', 'تعمیر موتور', 'اورهال', 'موتور تعمیری', 'تعمیر اساسی موتور'],
            'gearbox': ['گیربکس', 'دنده', 'تعمیر گیربکس', 'گیربکس تعمیری', 'جعبه دنده'],
            'high_mileage': ['کارکرد بالا', 'کیلومتر زیاد', 'کم کار', 'کارکرد کم'],
            'defects': ['معیوب', 'خراب', 'نیاز به تعمیر', 'ایراد', 'مشکل']
        }
        
        # دیکشنری نام‌های خودرو بهبود یافته
        self.car_names = {
            'پژو': ['پژو', 'peugeot', '206', '207', '405', 'پارس'],
            'پراید': ['پراید', 'pride', '131', '132', 'هاچبک'],
            'سمند': ['سمند', 'samand', 'lx', 'ef7'],
            'تیبا': ['تیبا', 'tiba'],
            'دنا': ['دنا', 'dena'],
            'رانا': ['رانا', 'rana'],
            'سایپا': ['سایپا', 'saipa'],
            'کوییک': ['کوییک', 'quick'],
            'آریو': ['آریو', 'ario'],
            'شاهین': ['شاهین', 'shahin'],
            'تارا': ['تارا', 'tara'],
            'ساینا': ['ساینا', 'saina'],
            'سهند': ['سهند', 'sahand']
        }
        
        # مقداردهی اولیه price_dict
        self.price_dict = {}
    
    def load_market_prices(self, file_path):
        """بارگذاری قیمت‌های روز از فایل همراه مکانیک"""
        try:
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
            df['Car Name'] = df['Car Name'].str.strip()
            df['Numeric Price'] = df['Price'].str.replace(',', '').str.extract(r'(\d+)').astype(float)
            
            # ایجاد دیکشنری برای جستجوی سریع‌تر
            self.price_dict = {}
            for _, row in df.iterrows():
                car_name = row['Car Name'].lower()
                price = row['Numeric Price']
                self.price_dict[car_name] = price
            
            return df
        except Exception as e:
            print(f"خطا در بارگذاری قیمت‌های روز: {e}")
            return None
    
    def load_divar_ads(self, file_path):
        """بارگذاری آگهی‌های دیوار"""
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            print(f"خطا در بارگذاری آگهی‌های دیوار: {e}")
            return None
    
    def similarity(self, a, b):
        """محاسبه شباهت بین دو رشته"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def extract_car_info(self, title, description=""):
        """استخراج بهبود یافته اطلاعات خودرو"""
        text = f"{title} {description}".lower()
        
        # استخراج سال با الگوهای مختلف
        year_patterns = [
            r'مدل\s*(13\d{2}|14\d{2})',
            r'(13\d{2}|14\d{2})\s*مدل',
            r'سال\s*(13\d{2}|14\d{2})',
            r'(13\d{2}|14\d{2})',
            r'مدل\s*(\d{2})',  # مدل 99
            r'(\d{2})\s*مدل'   # 99 مدل
        ]
        
        year = None
        for pattern in year_patterns:
            match = re.search(pattern, text)
            if match:
                year_str = match.group(1)
                if len(year_str) == 2:
                    year_num = int(year_str)
                    if year_num >= 80:
                        year = 1300 + year_num
                    else:
                        year = 1400 + year_num
                else:
                    year = int(year_str)
                break
        
        # استخراج کیلومتر با الگوهای مختلف
        km_patterns = [
            r'(\d+)\s*هزار\s*کیلومتر',
            r'(\d+)\s*هزار',
            r'(\d+)\s*k',
            r'کارکرد\s*(\d+)',
            r'(\d+)\s*کیلومتر'
        ]
        
        mileage = None
        for pattern in km_patterns:
            match = re.search(pattern, text)
            if match:
                km_num = int(match.group(1))
                if km_num < 1000:  # احتمالاً هزار کیلومتر
                    mileage = km_num * 1000
                else:
                    mileage = km_num
                break
        
        # تشخیص نام خودرو با دقت بیشتر
        car_name = None
        best_score = 0
        
        for main_name, aliases in self.car_names.items():
            for alias in aliases:
                if alias in text:
                    score = len(alias) / len(text)  # امتیاز بر اساس طول
                    if score > best_score:
                        best_score = score
                        car_name = main_name
        
        return {
            'car_name': car_name,
            'year': year,
            'mileage': mileage
        }
    
    def detect_issues(self, title, description="", body_status="", engine_status="", gearbox_status="", chassis_status=""):
        """تشخیص بهبود یافته مشکلات بر اساس متن آگهی و وضعیت‌های مختلف"""
        text = f"{title} {description}".lower()
        issues = []
        
        # تشخیص رنگ شدگی با منطق بهبود یافته
        paint_indicators = 0
        paint_keywords = ['رنگ شده', 'رنگ', 'صافکاری', 'رنگی', 'نقاشی', 'رنگ شدگی']
        
        # بررسی کلمات بی رنگ (بدون مشکل رنگ)
        no_paint_keywords = ['بی رنگ', 'بیرنگ', 'بدون رنگ', 'رنگ خالی']
        has_no_paint = any(keyword in text for keyword in no_paint_keywords)
        
        # اگر "بی رنگ" یا "بدون رنگ" ذکر شده، مشکل رنگ نیست
        if has_no_paint:
            pass  # هیچ مشکل رنگی اضافه نمی‌کنیم
        else:
            # شمارش کلمات رنگ شدگی
            for keyword in paint_keywords:
                if keyword in text:
                    paint_indicators += text.count(keyword)
            
            # اگر در متن آگهی رنگ شدگی ذکر شده، افت قیمت در نظر بگیر
            if paint_indicators > 0:
                if any(word in text for word in ['تمام رنگ', 'کامل رنگ', 'فول رنگ']):
                    issues.append('full_paint')
                elif 'سقف' in text and any(k in text for k in paint_keywords):
                    issues.append('roof_paint')
                elif 'ستون' in text and any(k in text for k in paint_keywords):
                    issues.append('pillar_paint')
                elif paint_indicators >= 4:
                    issues.append('paint_four_plus')
                elif paint_indicators == 3:
                    issues.append('paint_three_parts')
                elif paint_indicators == 2:
                    issues.append('paint_two_parts')
                else:
                    issues.append('paint_one_part')
        
        # بررسی وضعیت بدنه با منطق بهبود یافته
        body_status_lower = body_status.lower()
        if body_status_lower:
            # اگر وضعیت بدنه "سالم" یا "بی خط و خش" باشد، هیچ مشکل رنگی اضافه نمی‌کنیم
            if any(word in body_status_lower for word in ['سالم', 'بی خط', 'بی خش', 'عالی']):
                pass  # صفر درصد افت - هیچ مشکلی اضافه نمی‌کنیم
            else:
                # بررسی دور رنگ (فول پینت)
                if any(word in body_status_lower for word in ['دور رنگ', 'دوررنگ', 'فول رنگ', 'تمام رنگ', 'کامل رنگ']):
                    issues.append('full_paint')
                # بررسی رنگ در نواحی مختلف
                elif any(word in body_status_lower for word in ['3 ناحیه', 'سه ناحیه', '۳ ناحیه']):
                    issues.append('paint_three_parts')
                elif any(word in body_status_lower for word in ['2 ناحیه', 'دو ناحیه', '۲ ناحیه']):
                    issues.append('paint_two_parts')
                elif any(word in body_status_lower for word in ['1 ناحیه', 'یک ناحیه', '۱ ناحیه']):
                    issues.append('paint_one_part')
                # بررسی سایر مشکلات بدنه
                elif any(word in body_status_lower for word in ['آسیب', 'خراب', 'تعمیر', 'ضربه']):
                    issues.append('body_part_replacement')
        
        # بررسی وضعیت گیربکس
        gearbox_status_lower = gearbox_status.lower()
        if gearbox_status_lower:
            if any(word in gearbox_status_lower for word in ['تعویض', 'تعمیر', 'خراب']):
                issues.append('gearbox_repair')
            # اگر سالم باشد، مشکل در نظر نگیر
        
        # بررسی وضعیت موتور
        engine_status_lower = engine_status.lower()
        if engine_status_lower:
            if 'خراب' in engine_status_lower:
                issues.append('موتور خراب')
            elif 'تعویض' in engine_status_lower:
                issues.append('موتور تعویض شده')
            elif 'تعمیر' in engine_status_lower:
                issues.append('موتور تعمیر شده')
            # اگر سالم باشد، مشکل در نظر نگیر
        
        # بررسی وضعیت شاسی
        chassis_status_lower = chassis_status.lower()
        if chassis_status_lower:
            if 'خراب' in chassis_status_lower:
                issues.append('شاسی خراب')
            elif 'تعویض' in chassis_status_lower:
                issues.append('شاسی تعویض شده')
            elif 'تعمیر' in chassis_status_lower:
                issues.append('شاسی تعمیر شده')
            elif 'آسیب' in chassis_status_lower:
                issues.append('شاسی آسیب دیده')
            # اگر سالم باشد، مشکل در نظر نگیر
        
        # تشخیص سایر مشکلات از متن
        if any(k in text for k in self.keywords['accident']):
            issues.append('accident_history')
        
        # تشخیص کارکرد بالا
        if 'کارکرد بالا' in text or 'کیلومتر زیاد' in text:
            issues.append('high_mileage')
        
        return issues
    
    def calculate_mileage_depreciation(self, mileage, year=None):
        """محاسبه افت قیمت بر اساس کارکرد"""
        if not mileage or not year:
            return 0
        
        current_year = 1403  # سال جاری شمسی
        car_age = current_year - year
        normal_mileage = car_age * 17500  # میانگین 17.5 هزار کیلومتر در سال
        
        if mileage > normal_mileage:
            excess_km = mileage - normal_mileage
            excess_5k_units = excess_km // 5000
            return excess_5k_units * self.depreciation_factors['high_mileage']['rate_per_5k']
        
        return 0
    
    def calculate_age_depreciation(self, year):
        """محاسبه افت قیمت بر اساس سن خودرو"""
        if not year:
            return 0
        
        current_year = 1403  # سال جاری شمسی
        car_age = current_year - year
        
        # جدول افت قیمت بر اساس سن
        age_depreciation_table = {
            0: 0.00,   # صفر کیلومتر
            1: 0.12,   # 1 ساله - 12%
            2: 0.08,   # 2 ساله - 8%
            3: 0.06,   # 3 ساله - 6%
            4: 0.05,   # 4 ساله - 5%
            5: 0.04,   # 5 ساله - 4%
        }
        
        if car_age <= 5:
            return age_depreciation_table.get(car_age, 0)
        else:
            # برای خودروهای بالای 5 سال: 3% سالانه
            base_depreciation = sum(age_depreciation_table.values())
            additional_years = car_age - 5
            additional_depreciation = additional_years * 0.03
            return min(base_depreciation + additional_depreciation, 0.5)  # حداکثر 50% افت سن
    
    def calculate_total_depreciation(self, issues, mileage_depreciation, age_depreciation=0):
        """محاسبه کل افت قیمت شامل افت سن"""
        total_depreciation = mileage_depreciation + age_depreciation
        issues_depreciation = 0
        
        for issue in issues:
            if issue in self.depreciation_factors:
                factor = self.depreciation_factors[issue]
                if 'min' in factor and 'max' in factor:
                    # استفاده از میانگین
                    depreciation = (factor['min'] + factor['max']) / 2
                else:
                    depreciation = factor.get('rate', 0)
                issues_depreciation += depreciation
        
        total_depreciation += issues_depreciation
        
        return min(total_depreciation, 0.7), issues_depreciation  # حداکثر 70% افت کل و افت مشکلات جداگانه
    
    def find_market_price(self, car_info, market_df, brand_type=""):
        """یافتن دقیق‌تر قیمت روز با استفاده از برند + تیپ + سال"""
        if market_df is None:
            return None
        
        car_name = car_info.get('car_name', '').lower() if car_info.get('car_name') else ''
        year = car_info.get('year')
        brand_type_lower = brand_type.lower() if brand_type else ''
        
        # ترکیب اطلاعات برای جستجوی دقیق‌تر
        search_terms = []
        if car_name:
            search_terms.append(car_name)
        if brand_type_lower:
            search_terms.extend(brand_type_lower.split())
        if year:
            search_terms.append(str(year))
        
        if not search_terms:
            return None
        
        best_match = None
        best_score = 0
        
        for market_name, price in self.price_dict.items():
            market_name_lower = market_name.lower()
            score = 0
            
            # امتیازدهی بر اساس تطبیق کلمات کلیدی
            for term in search_terms:
                if term in market_name_lower:
                    if len(term) > 3:  # کلمات مهم‌تر امتیاز بیشتر
                        score += 0.4
                    else:
                        score += 0.2
            
            # امتیاز اضافی برای تطبیق دقیق سال
            if year and str(year) in market_name_lower:
                score += 0.5
            
            # امتیاز اضافی برای تطبیق برند اصلی
            if car_name and car_name in market_name_lower:
                score += 0.6
            
            # محاسبه شباهت کلی
            similarity_score = self.similarity(' '.join(search_terms), market_name_lower)
            score += similarity_score * 0.3
            
            if score > best_score and score > 0.4:  # حداقل 40% امتیاز
                best_score = score
                best_match = price
        
        return best_match
    
    def calculate_estimated_price(self, market_price, total_depreciation):
        """محاسبه قیمت تخمینی"""
        if not market_price:
            return None
        
        estimated_price = market_price * (1 - total_depreciation)
        return max(estimated_price, market_price * 0.25)  # حداقل 25% قیمت روز
    
    def process_ads(self, divar_file, market_file, output_file):
        """پردازش کامل آگهی‌ها"""
        print("بارگذاری داده‌ها...")
        market_df = self.load_market_prices(market_file)
        divar_df = self.load_divar_ads(divar_file)
        
        if market_df is None or divar_df is None:
            print("خطا در بارگذاری فایل‌ها")
            return
        
        results = []
        
        print(f"پردازش {len(divar_df)} آگهی...")
        
        for index, row in divar_df.iterrows():
            try:
                # استخراج عنوان و توضیحات
                title = str(row.iloc[0] if len(row) > 0 else '')
                description = str(row.iloc[1] if len(row) > 1 else '')
                
                # استخراج اطلاعات خودرو
                car_info = self.extract_car_info(title, description)
                
                # تشخیص مشکلات
                issues = self.detect_issues(title, description)
                
                # محاسبه افت کارکرد
                mileage_depreciation = self.calculate_mileage_depreciation(
                    car_info['mileage'], car_info['year']
                )
                
                # محاسبه کل افت قیمت
                total_depreciation = self.calculate_total_depreciation(issues, mileage_depreciation)
                
                # یافتن قیمت روز
                market_price = self.find_market_price(car_info, market_df)
                
                # محاسبه قیمت تخمینی
                estimated_price = self.calculate_estimated_price(market_price, total_depreciation)
                
                result = {
                    'عنوان آگهی': title,
                    'نام خودرو': car_info['car_name'] or 'نامشخص',
                    'سال': car_info['year'] or 'نامشخص',
                    'کیلومتر': f"{car_info['mileage']:,}" if car_info['mileage'] else 'نامشخص',
                    'قیمت روز (تومان)': f"{market_price:,.0f}" if market_price else 'یافت نشد',
                    'مشکلات تشخیص داده شده': ', '.join(issues) if issues else 'هیچ',
                    'افت کارکرد': f"{mileage_depreciation:.1%}",
                    'درصد افت کل': f"{total_depreciation:.1%}",
                    'قیمت تخمینی (تومان)': f"{estimated_price:,.0f}" if estimated_price else 'محاسبه نشد',
                    'توضیحات': description[:200] + '...' if len(description) > 200 else description
                }
                
                results.append(result)
                
                if (index + 1) % 50 == 0:
                    print(f"پردازش شده: {index + 1} آگهی")
                    
            except Exception as e:
                print(f"خطا در پردازش آگهی {index + 1}: {e}")
                continue
        
        # ذخیره نتایج
        results_df = pd.DataFrame(results)
        results_df.to_excel(output_file, index=False, engine='openpyxl')
        results_df.to_csv(output_file.replace('.xlsx', '.csv'), index=False, encoding='utf-8')
        
        print(f"\nپردازش کامل شد!")
        print(f"تعداد آگهی‌های پردازش شده: {len(results)}")
        print(f"نتایج در فایل {output_file} ذخیره شد")
        
        # آمار کلی
        successful_calculations = len([r for r in results if r['قیمت تخمینی (تومان)'] != 'محاسبه نشد'])
        identified_cars = len([r for r in results if r['نام خودرو'] != 'نامشخص'])
        with_issues = len([r for r in results if r['مشکلات تشخیص داده شده'] != 'هیچ'])
        
        print(f"تعداد آگهی‌های با قیمت محاسبه شده: {successful_calculations}")
        print(f"تعداد خودروهای شناسایی شده: {identified_cars}")
        print(f"تعداد خودروهای با مشکل: {with_issues}")
        
        return results_df

# اجرای اسکریپت بهبود یافته
if __name__ == "__main__":
    calculator = ImprovedCarPriceCalculator()
    
    # مسیر فایل‌ها
    divar_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/divar_ads_batch_002_20250806_124612.xlsx"
    market_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/hamrah_mechanic_prices.xlsx"
    output_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/improved_car_price_analysis.xlsx"
    
    # پردازش آگهی‌ها
    results = calculator.process_ads(divar_file, market_file, output_file)
    
    if results is not None:
        print("\n=== نمونه نتایج بهبود یافته ===")
        print(results.head(10).to_string(index=False))
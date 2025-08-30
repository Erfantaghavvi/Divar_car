import pandas as pd
import numpy as np
import re
from datetime import datetime
import os
from difflib import SequenceMatcher

class ColumnBasedCarPriceCalculator:
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
            'suspension_defect': {'min': 0.02, 'max': 0.05},  # سیستم تعلیق معیوب
            'option_defect': {'min': 0.005, 'max': 0.03},  # آپشن معیوب
            'old_tires': {'min': 0.01, 'max': 0.02},  # لاستیک کهنه
            'accident_history': {'min': 0.05, 'max': 0.15},  # سوابق تصادف
            'minor_scratches': {'min': 0.005, 'max': 0.01}  # خط و خش جزئی
        }
        
        # کلمات کلیدی برای تشخیص مشکلات
        self.keywords = {
            'paint': ['رنگ', 'صافکاری', 'رنگ شده', 'پوشش رنگ', 'بیرنگ', 'رنگی', 'نقاشی', 'دوررنگ', 'رنگ‌شدگی'],
            'accident': ['تصادف', 'ضربه', 'خسارت', 'آسیب دیده', 'تصادفی', 'ضربه خورده'],
            'engine': ['موتور', 'تعمیر موتور', 'اورهال', 'موتور تعمیری', 'تعمیر اساسی موتور'],
            'gearbox': ['گیربکس', 'تعمیر گیربکس', 'گیربکس تعمیری', 'جعبه دنده'],
            'high_mileage': ['کارکرد بالا', 'کیلومتر زیاد'],
            'defects': ['معیوب', 'خراب', 'نیاز به تعمیر', 'ایراد', 'مشکل']
        }
    
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
    
    def clean_persian_number(self, text):
        """تبدیل اعداد فارسی به انگلیسی و حذف کاما"""
        if pd.isna(text):
            return None
        
        text = str(text)
        # تبدیل اعداد فارسی به انگلیسی
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        for p, e in zip(persian_digits, english_digits):
            text = text.replace(p, e)
        
        # حذف کاما و سایر کاراکترهای غیرعددی
        text = re.sub(r'[^\d]', '', text)
        
        try:
            return int(text) if text else None
        except:
            return None
    
    def extract_car_info_from_columns(self, row):
        """استخراج اطلاعات خودرو از ستون‌های مشخص"""
        # استخراج نام خودرو از ستون برند_و_تیپ
        car_name = str(row.get('برند_و_تیپ', '')).strip() if pd.notna(row.get('برند_و_تیپ')) else None
        
        # استخراج سال از ستون مدل
        year_raw = row.get('مدل')
        year = self.clean_persian_number(year_raw)
        
        # استخراج کیلومتر از ستون کارکرد
        mileage_raw = row.get('کارکرد')
        mileage = self.clean_persian_number(mileage_raw)
        
        return {
            'car_name': car_name,
            'year': year,
            'mileage': mileage,
            'car_name_raw': car_name,
            'year_raw': year_raw,
            'mileage_raw': mileage_raw
        }
    
    def detect_issues_from_columns(self, row):
        """تشخیص مشکلات از ستون‌های مختلف"""
        issues = []
        
        # متن‌های مختلف برای بررسی
        texts_to_check = [
            str(row.get('عنوان', '')),
            str(row.get('توضیحات', '')),
            str(row.get('بدنه', '')),
            str(row.get('موتور', '')),
            str(row.get('شاسی', '')),
            str(row.get('گیربکس', ''))
        ]
        
        combined_text = ' '.join(texts_to_check).lower()
        
        # تشخیص رنگ
        paint_indicators = 0
        paint_keywords = ['رنگ', 'صافکاری', 'بیرنگ', 'رنگی', 'نقاشی', 'دوررنگ', 'رنگ‌شدگی']
        
        for keyword in paint_keywords:
            paint_indicators += combined_text.count(keyword)
        
        # بررسی خاص برای رنگ‌شدگی در ناحیه
        if 'رنگ‌شدگی در' in combined_text:
            # استخراج تعداد ناحیه
            match = re.search(r'رنگ‌شدگی در (\d+) ناحیه', combined_text)
            if match:
                num_areas = int(match.group(1))
                if num_areas >= 4:
                    issues.append('paint_four_plus')
                elif num_areas == 3:
                    issues.append('paint_three_parts')
                elif num_areas == 2:
                    issues.append('paint_two_parts')
                else:
                    issues.append('paint_one_part')
            else:
                issues.append('paint_two_parts')  # پیش‌فرض
        elif paint_indicators > 0:
            if any(word in combined_text for word in ['تمام رنگ', 'کامل رنگ', 'فول رنگ']):
                issues.append('full_paint')
            elif 'سقف' in combined_text and any(k in combined_text for k in paint_keywords):
                issues.append('roof_paint')
            elif 'ستون' in combined_text and any(k in combined_text for k in paint_keywords):
                issues.append('pillar_paint')
            elif paint_indicators >= 4:
                issues.append('paint_four_plus')
            elif paint_indicators == 3:
                issues.append('paint_three_parts')
            elif paint_indicators == 2:
                issues.append('paint_two_parts')
            else:
                issues.append('paint_one_part')
        
        # تشخیص سایر مشکلات
        if any(k in combined_text for k in self.keywords['accident']):
            issues.append('accident_history')
        
        if any(k in combined_text for k in self.keywords['engine']):
            issues.append('engine_overhaul')
        
        if any(k in combined_text for k in self.keywords['gearbox']):
            issues.append('gearbox_repair')
        
        if any(k in combined_text for k in self.keywords['defects']):
            issues.append('option_defect')
        
        # بررسی وضعیت موتور، شاسی، بدنه
        engine_status = str(row.get('موتور', '')).lower()
        chassis_status = str(row.get('شاسی', '')).lower()
        body_status = str(row.get('بدنه', '')).lower()
        
        if 'تعمیر' in engine_status or 'معیوب' in engine_status:
            issues.append('engine_overhaul')
        
        if 'آسیب' in chassis_status or 'ضربه' in chassis_status:
            issues.append('paint_chassis_damage')
        
        # بررسی خط و خش جزئی در بدنه و شاسی
        if ('خط و خش جزئی' in body_status or 'خط و خش جزیی' in body_status or 
            'خط و خش جزئی' in chassis_status or 'خط و خش جزیی' in chassis_status):
            issues.append('minor_scratches')
        
        return issues
    
    def similarity(self, a, b):
        """محاسبه شباهت بین دو رشته"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def find_market_price(self, car_info, market_df):
        """یافتن قیمت روز خودرو"""
        if market_df is None or not car_info['car_name']:
            return None
        
        car_name = car_info['car_name'].lower()
        year = car_info['year']
        
        # جستجوی مستقیم
        best_match = None
        best_score = 0
        
        for market_name, price in self.price_dict.items():
            # محاسبه شباهت
            score = self.similarity(car_name, market_name)
            
            # اگر سال موجود است، امتیاز بیشتری بده
            if year and str(year) in market_name:
                score += 0.3
            
            if score > best_score and score > 0.2:  # حداقل 20% شباهت
                best_score = score
                best_match = price
        
        return best_match
    
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
    
    def calculate_total_depreciation(self, issues, mileage_depreciation):
        """محاسبه کل افت قیمت"""
        total_depreciation = mileage_depreciation
        
        for issue in issues:
            if issue in self.depreciation_factors:
                factor = self.depreciation_factors[issue]
                if 'min' in factor and 'max' in factor:
                    # استفاده از میانگین
                    depreciation = (factor['min'] + factor['max']) / 2
                else:
                    depreciation = factor.get('rate', 0)
                total_depreciation += depreciation
        
        return min(total_depreciation, 0.6)  # حداکثر 60% افت
    
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
                # استخراج اطلاعات خودرو از ستون‌ها
                car_info = self.extract_car_info_from_columns(row)
                
                # تشخیص مشکلات
                issues = self.detect_issues_from_columns(row)
                
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
                    'عنوان آگهی': str(row.get('عنوان', '')),
                    'نام خودرو (از ستون)': car_info['car_name'] or 'نامشخص',
                    'سال (از ستون)': car_info['year'] or 'نامشخص',
                    'کیلومتر (از ستون)': f"{car_info['mileage']:,}" if car_info['mileage'] else 'نامشخص',
                    'قیمت آگهی': str(row.get('قیمت', 'نامشخص')),
                    'قیمت روز (تومان)': f"{market_price:,.0f}" if market_price else 'یافت نشد',
                    'مشکلات تشخیص داده شده': ', '.join(issues) if issues else 'هیچ',
                    'افت کارکرد': f"{mileage_depreciation:.1%}",
                    'درصد افت کل': f"{total_depreciation:.1%}",
                    'قیمت تخمینی (تومان)': f"{estimated_price:,.0f}" if estimated_price else 'محاسبه نشد',
                    'وضعیت موتور': str(row.get('موتور', 'نامشخص')),
                    'وضعیت شاسی': str(row.get('شاسی', 'نامشخص')),
                    'وضعیت بدنه': str(row.get('بدنه', 'نامشخص')),
                    'توضیحات': str(row.get('توضیحات', ''))[:200] + '...' if len(str(row.get('توضیحات', ''))) > 200 else str(row.get('توضیحات', ''))
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
        identified_cars = len([r for r in results if r['نام خودرو (از ستون)'] != 'نامشخص'])
        with_issues = len([r for r in results if r['مشکلات تشخیص داده شده'] != 'هیچ'])
        
        print(f"تعداد آگهی‌های با قیمت محاسبه شده: {successful_calculations}")
        print(f"تعداد خودروهای شناسایی شده: {identified_cars}")
        print(f"تعداد خودروهای با مشکل: {with_issues}")
        
        return results_df

# اجرای اسکریپت بهبود یافته
if __name__ == "__main__":
    calculator = ColumnBasedCarPriceCalculator()
    
    # مسیر فایل‌ها
    divar_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/divar_ads_batch_002_20250806_124612.xlsx"
    market_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/hamrah_mechanic_prices.xlsx"
    output_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/column_based_car_analysis.xlsx"
    
    # پردازش آگهی‌ها
    results = calculator.process_ads(divar_file, market_file, output_file)
    
    if results is not None:
        print("\n=== نمونه نتایج بر اساس ستون‌ها ===")
        print(results.head(10).to_string(index=False))
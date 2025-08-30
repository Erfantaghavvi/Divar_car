import pandas as pd
import numpy as np
import re
from datetime import datetime
import os
try:
    from ml_price_calculator import MachineLearningPriceCalculator
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ سیستم یادگیری ماشین در دسترس نیست")
    print("💡 برای فعال‌سازی: pip install scikit-learn joblib")

class CarPriceCalculator:
    def __init__(self, enable_ml=True):
        # راه‌اندازی سیستم یادگیری ماشین
        self.ml_calculator = None
        if enable_ml and ML_AVAILABLE:
            try:
                self.ml_calculator = MachineLearningPriceCalculator(base_calculator=self)
                print("🤖 سیستم یادگیری ماشین فعال شد")
            except Exception as e:
                print(f"⚠️ خطا در راه‌اندازی ML: {e}")
                self.ml_calculator = None
        # جدول عوامل افت قیمت بهبود یافته
        self.depreciation_factors = {
            'high_mileage': {'rate_per_5k': 0.0125},  # هر 5 هزار کیلومتر اضافه - 1.25%
            'paint_one_part': {'min': 0.03, 'max': 0.06},  # رنگ یک قطعه - 3-6%
            'paint_two_parts': {'min': 0.06, 'max': 0.10},  # رنگ دو قطعه - 6-10%
            'paint_three_parts': {'min': 0.08, 'max': 0.12},  # رنگ سه قطعه - 8-12%
            'paint_four_plus': {'min': 0.12, 'max': 0.18},  # رنگ چهار قطعه یا بیشتر - 12-18%
            'roof_paint': {'min': 0.12, 'max': 0.18},  # رنگ سقف - 12-18%
            'pillar_paint': {'min': 0.10, 'max': 0.15},  # رنگ ستون‌ها - 10-15%
            'full_paint': {'min': 0.18, 'max': 0.35},  # تمام رنگ (شامل دوررنگ) - 18-35%
            'paint_chassis_damage': {'min': 0.25, 'max': 0.45},  # رنگ + آسیب شاسی - 25-45%
            'body_part_replacement': {'min': 0.06, 'max': 0.12},  # تعویض قطعه بدنه - 6-12%
            'roof_pillar_repair': {'min': 0.18, 'max': 0.30},  # تعمیر سقف/ستون - 18-30%
            'engine_overhaul': {'min': 0.12, 'max': 0.25},  # موتور تعمیر اساسی - 12-25%
            'gearbox_repair': {'min': 0.08, 'max': 0.15},  # گیربکس تعمیر شده - 8-15%
            'suspension_defect': {'min': 0.03, 'max': 0.06},  # سیستم تعلیق معیوب - 3-6%
            'option_defect': {'min': 0.01, 'max': 0.04},  # آپشن معیوب - 1-4%
            'old_tires': {'min': 0.015, 'max': 0.03},  # لاستیک کهنه - 1.5-3%
            'accident_history': {'min': 0.08, 'max': 0.20},  # سوابق تصادف - 8-20%
            'minor_scratches': {'min': 0.005, 'max': 0.015},  # خراش‌های جزئی - 0.5-1.5%
            'electrical_issues': {'min': 0.04, 'max': 0.08},  # مشکلات برقی - 4-8%
            'interior_damage': {'min': 0.02, 'max': 0.05}  # آسیب داخلی - 2-5%
        }
        
        # جدول افت قیمت بر اساس سن خودرو (سال شمسی)
        self.age_depreciation = {
            1404: {'min': 0.00, 'max': 0.00},  # صفر کیلومتر
            1403: {'min': 0.10, 'max': 0.15},  # 1 ساله
            1402: {'min': 0.07, 'max': 0.10},  # 2 ساله
            1401: {'min': 0.05, 'max': 0.08},  # 3 ساله
            1400: {'min': 0.04, 'max': 0.06},  # 4 ساله
            1399: {'min': 0.04, 'max': 0.05},  # 5 ساله
            1398: {'min': 0.03, 'max': 0.05},  # 6 ساله
            1397: {'min': 0.03, 'max': 0.05},  # 7 ساله
            1396: {'min': 0.03, 'max': 0.05},  # 8 ساله
            1395: {'min': 0.03, 'max': 0.05},  # 9 ساله
        }
        
        # کلمات کلیدی بهبود یافته برای تشخیص مشکلات
        self.keywords = {
            'paint': ['رنگ', 'صافکاری', 'رنگ شده', 'پوشش رنگ', 'دوررنگ', 'بیرنگ', 'رنگی', 'نقاشی', 'رنگ‌شدگی'],
            'accident': ['تصادف', 'ضربه', 'خسارت', 'آسیب دیده', 'تصادفی', 'ضربه خورده', 'آسیب', 'ضربه‌خورده'],
            'engine': ['موتور', 'تعمیر موتور', 'اورهال', 'موتور تعمیری', 'تعمیر اساسی موتور', 'بازسازی موتور'],
            'gearbox': ['گیربکس', 'دنده', 'تعمیر گیربکس', 'گیربکس تعمیری', 'جعبه دنده', 'دنده‌ای'],
            'high_mileage': ['کارکرد بالا', 'کیلومتر زیاد', 'کم کار', 'کارکرد کم', 'پرکار'],
            'defects': ['معیوب', 'خراب', 'نیاز به تعمیر', 'ایراد', 'مشکل', 'مشکل‌دار'],
            'minor_scratches': ['خط و خش جزئی', 'خط و خش جزیی', 'خراش جزئی', 'خراش کم', 'خط و خش کم'],
            'body_issues': ['بدنه', 'صافکاری', 'ورق', 'تعویض قطعه', 'قطعه تعویضی']
        }
    
    def load_market_prices(self, hamrah_file, z4car_file):
        """بارگذاری قیمت‌های روز از فایل‌های همراه مکانیک و z4car"""
        combined_df = pd.DataFrame()
        
        # بارگذاری داده‌های همراه مکانیک
        try:
            if hamrah_file and os.path.exists(hamrah_file):
                hamrah_df = pd.read_excel(hamrah_file) if hamrah_file.endswith('.xlsx') else pd.read_csv(hamrah_file)
                if 'Car Name' in hamrah_df.columns and 'Price' in hamrah_df.columns:
                    hamrah_df['Car Name'] = hamrah_df['Car Name'].str.strip()
                    hamrah_df['Numeric Price'] = hamrah_df['Price'].str.replace(',', '').str.extract(r'(\d+)').astype(float)
                    hamrah_df['Source'] = 'همراه مکانیک'
                    combined_df = pd.concat([combined_df, hamrah_df], ignore_index=True)
                    print(f"بارگذاری {len(hamrah_df)} رکورد از همراه مکانیک")
        except Exception as e:
            print(f"خطا در بارگذاری همراه مکانیک: {e}")
        
        # بارگذاری داده‌های z4car
        try:
            if z4car_file and os.path.exists(z4car_file):
                z4car_df = pd.read_excel(z4car_file) if z4car_file.endswith('.xlsx') else pd.read_csv(z4car_file)
                if 'نام خودرو' in z4car_df.columns and 'قیمت (تومان)' in z4car_df.columns:
                    # تبدیل ستون‌ها به فرمت یکسان
                    z4car_df = z4car_df.rename(columns={'نام خودرو': 'Car Name', 'قیمت (تومان)': 'Price'})
                    z4car_df['Car Name'] = z4car_df['Car Name'].str.strip()
                    # تمیز کردن قیمت‌های z4car که ممکن است ترکیبی باشند
                    z4car_df['Numeric Price'] = z4car_df['Price'].astype(str).str.replace(',', '').str.extract(r'(\d+)').astype(float)
                    z4car_df['Source'] = 'z4car'
                    combined_df = pd.concat([combined_df, z4car_df], ignore_index=True)
                    print(f"بارگذاری {len(z4car_df)} رکورد از z4car")
        except Exception as e:
            print(f"خطا در بارگذاری z4car: {e}")
        
        if combined_df.empty:
            print("هیچ داده‌ای از منابع قیمت بارگذاری نشد")
            return None
        
        # حذف رکوردهای تکراری بر اساس نام خودرو و قیمت
        combined_df = combined_df.drop_duplicates(subset=['Car Name', 'Numeric Price'])
        
        # مرتب‌سازی بر اساس قیمت (بالاترین قیمت اول)
        combined_df = combined_df.sort_values('Numeric Price', ascending=False)
        
        print(f"مجموع {len(combined_df)} رکورد منحصر به فرد بارگذاری شد")
        return combined_df
    
    def load_divar_ads(self, file_path):
        """بارگذاری آگهی‌های دیوار"""
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            print(f"خطا در بارگذاری آگهی‌های دیوار: {e}")
            return None
    
    def extract_car_info(self, title, description=""):
        """استخراج اطلاعات خودرو از عنوان و توضیحات"""
        text = f"{title} {description}".lower()
        
        # استخراج سال
        year_match = re.search(r'(13\d{2}|14\d{2}|20\d{2})', text)
        year = int(year_match.group(1)) if year_match else None
        
        # استخراج کیلومتر
        km_match = re.search(r'(\d+)\s*(?:هزار|k|کیلومتر)', text)
        mileage = int(km_match.group(1)) * 1000 if km_match else None
        
        # تشخیص نوع خودرو - لیست گسترده شده
        car_brands = [
            # برندهای ایرانی
            'پژو', 'سمند', 'پراید', 'تیبا', 'دنا', 'رانا', 'سایپا', 'کوییک', 'آریو', 'شاهین', 'تارا', 'ساینا',
            # برندهای آسیایی
            'تویوتا', 'هوندا', 'نیسان', 'هیوندای', 'کیا', 'مزدا', 'میتسوبیشی', 'سوبارو',
            # برندهای اروپایی
            'بی ام و', 'بنز', 'آئودی', 'فولکس', 'رنو', 'سیتروئن', 'پورشه', 'فراری', 'لامبورگینی', 'مازراتی',
            # برندهای لوکس
            'لکسوس', 'اینفینیتی', 'اکورا', 'کادیلاک', 'لینکلن', 'جگوار', 'لندرور', 'بنتلی', 'رولزرویس',
            # برندهای چینی
            'چری', 'ام وی ام', 'هاوال', 'گک', 'چانگان', 'جیلی', 'بی وای دی', 'لیفان', 'گریت وال',
            # برندهای دیگر
            'ولوو', 'مینی', 'اسمارت', 'تسلا', 'آلفارومئو', 'فیات', 'دوو'
        ]
        
        car_name = None
        for brand in car_brands:
            if brand in text:
                car_name = brand
                break
        
        return {
            'car_name': car_name,
            'year': year,
            'mileage': mileage
        }
    
    def extract_car_info_from_columns(self, title, description, brand_type, model_year, mileage_str):
        """استخراج اطلاعات خودرو از ستون‌های مشخص"""
        # استخراج نام خودرو از ستون برند_و_تیپ
        car_name = None
        if brand_type and brand_type != 'nan':
            # تمیز کردن نام برند
            brand_clean = brand_type.strip().lower()
            
            # تشخیص برند اصلی
            car_brands = [
                # برندهای ایرانی
                'پژو', 'سمند', 'پراید', 'تیبا', 'دنا', 'رانا', 'سایپا', 'کوییک', 'آریو', 'شاهین', 'تارا', 'ساینا',
                # برندهای آسیایی
                'تویوتا', 'هوندا', 'نیسان', 'هیوندای', 'کیا', 'مزدا', 'میتسوبیشی', 'سوبارو',
                # برندهای اروپایی
                'بی ام و', 'بنز', 'آئودی', 'فولکس', 'رنو', 'سیتروئن', 'پورشه', 'فراری', 'لامبورگینی', 'مازراتی',
                # برندهای لوکس
                'لکسوس', 'اینفینیتی', 'اکورا', 'کادیلاک', 'لینکلن', 'جگوار', 'لندرور', 'بنتلی', 'رولزرویس',
                # برندهای چینی
                'چری', 'ام وی ام', 'هاوال', 'گک', 'چانگان', 'جیلی', 'بی وای دی', 'لیفان', 'گریت وال',
                # برندهای دیگر
                'ولوو', 'مینی', 'اسمارت', 'تسلا', 'آلفارومئو', 'فیات', 'دوو'
            ]
            
            for brand in car_brands:
                if brand in brand_clean:
                    car_name = brand
                    break
        
        # اگر از ستون برند_و_تیپ نتوانست، از عنوان استخراج کن
        if not car_name:
            car_info_fallback = self.extract_car_info(title, description)
            car_name = car_info_fallback['car_name']
        
        # استخراج سال از ستون مدل
        year = None
        if model_year and model_year != 'nan':
            # تبدیل اعداد فارسی به انگلیسی
            persian_to_english = {
                '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
            }
            
            year_clean = model_year.strip()
            for persian, english in persian_to_english.items():
                year_clean = year_clean.replace(persian, english)
            
            # استخراج سال
            year_match = re.search(r'(13\d{2}|14\d{2}|20\d{2})', year_clean)
            if year_match:
                year = int(year_match.group(1))
        
        # استخراج کیلومتر از ستون کارکرد
        mileage = None
        if mileage_str and mileage_str != 'nan':
            # تبدیل اعداد فارسی به انگلیسی و حذف کاما
            persian_to_english = {
                '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
                '٬': '', ',': ''
            }
            
            mileage_clean = mileage_str.strip()
            for persian, english in persian_to_english.items():
                mileage_clean = mileage_clean.replace(persian, english)
            
            # استخراج عدد
            mileage_match = re.search(r'(\d+)', mileage_clean)
            if mileage_match:
                mileage = int(mileage_match.group(1))
        
        return {
            'car_name': car_name,
            'year': year,
            'mileage': mileage
        }
    
    def detect_issues(self, title, description=""):
        """تشخیص مشکلات خودرو از متن آگهی"""
        text = f"{title} {description}".lower()
        issues = []
        
        # تشخیص رنگ
        paint_count = 0
        for keyword in self.keywords['paint']:
            if keyword in text:
                paint_count += 1
        
        if paint_count > 0:
            if 'تمام رنگ' in text or 'کامل رنگ' in text:
                issues.append('full_paint')
            elif 'سقف' in text and any(k in text for k in self.keywords['paint']):
                issues.append('roof_paint')
            elif paint_count >= 4:
                issues.append('paint_four_plus')
            elif paint_count == 3:
                issues.append('paint_three_parts')
            elif paint_count == 2:
                issues.append('paint_two_parts')
            else:
                issues.append('paint_one_part')
        
        # تشخیص سایر مشکلات
        if any(k in text for k in self.keywords['accident']):
            issues.append('accident_history')
        
        if any(k in text for k in self.keywords['engine']):
            issues.append('engine_overhaul')
        
        if any(k in text for k in self.keywords['gearbox']):
            issues.append('gearbox_repair')
        
        if any(k in text for k in self.keywords['defects']):
            issues.append('option_defect')
        
        return issues
    
    def detect_issues_from_columns(self, title, description, engine_status, chassis_status, body_status):
        """تشخیص دقیق مشکلات خودرو فقط بر اساس ستون‌های وضعیت و توضیحات"""
        issues = []
        
        # بررسی دقیق وضعیت موتور
        if engine_status and engine_status != 'nan' and engine_status.strip():
            engine_lower = engine_status.lower().strip()
            
            # موتور سالم - هیچ مشکلی نیست
            if engine_lower in ['سالم', 'بدون مشکل', 'عالی']:
                pass  # هیچ مشکلی اضافه نکن
            
            # موتور تعمیری یا اورهال شده
            elif any(keyword in engine_lower for keyword in ['تعمیر', 'اورهال', 'تعمیری', 'بازسازی', 'تعمیر شده']):
                if 'engine_overhaul' not in issues:
                    issues.append('engine_overhaul')
            
            # موتور معیوب یا نیاز به تعمیر
            elif any(keyword in engine_lower for keyword in ['معیوب', 'خراب', 'نیاز به تعمیر', 'مشکل دار']):
                if 'engine_overhaul' not in issues:
                    issues.append('engine_overhaul')
        
        # بررسی دقیق وضعیت شاسی
        if chassis_status and chassis_status != 'nan' and chassis_status.strip():
            chassis_lower = chassis_status.lower().strip()
            
            # شاسی سالم - هیچ مشکلی نیست
            if chassis_lower in ['سالم', 'سالم و پلمپ', 'پلمپ', 'بدون مشکل', 'عالی']:
                pass  # هیچ مشکلی اضافه نکن
            
            # شاسی آسیب دیده یا تصادفی
            elif any(keyword in chassis_lower for keyword in ['آسیب', 'ضربه', 'تصادف', 'خسارت', 'ضربه خورده', 'آسیب دیده']):
                if 'accident_history' not in issues:
                    issues.append('accident_history')
            
            # شاسی تعیین نشده - احتمال مشکل
            elif 'تعیین نشده' in chassis_lower or 'تعیین‌نشده' in chassis_lower:
                # در صورت عدم قطعیت، مشکل اضافه نکن
                pass
        
        # بررسی دقیق وضعیت بدنه
        if body_status and body_status != 'nan' and body_status.strip():
            body_lower = body_status.lower().strip()
            
            # بدنه سالم - هیچ مشکلی نیست
            if body_lower in ['سالم', 'سالم و بی خط و خش', 'سالم و بی‌خط و خش', 'بدون خط و خش', 'عالی', 'سالم و بی‌خط و خش']:
                pass  # هیچ مشکلی اضافه نکن - حتی اگر کلمه رنگ در توضیحات باشد
            
            # تشخیص خراش جزئی - فقط خراش، بدون رنگ
            elif any(keyword in body_lower for keyword in ['خط و خش جزئی', 'خط و خش جزیی', 'خراش جزئی', 'خراش کم']):
                if 'minor_scratches' not in issues:
                    issues.append('minor_scratches')
                # اگر فقط خراش جزئی است، رنگ اضافه نکن
            
            # تشخیص رنگ کامل
            elif any(keyword in body_lower for keyword in ['تمام رنگ', 'کامل رنگ', 'فول رنگ', 'تمام‌رنگ']):
                if 'full_paint' not in issues:
                    issues.append('full_paint')
            
            # تشخیص رنگ سقف
            elif any(keyword in body_lower for keyword in ['رنگ سقف', 'سقف رنگ']):
                if 'roof_paint' not in issues:
                    issues.append('roof_paint')
            
            # تشخیص رنگ در چند ناحیه
            elif 'رنگ‌شدگی در' in body_lower or 'رنگشدگی در' in body_lower:
                # استخراج تعداد نواحی رنگی
                if '۴' in body_lower or '4' in body_lower or 'چهار' in body_lower:
                    issues.append('paint_four_plus')
                elif '۳' in body_lower or '3' in body_lower or 'سه' in body_lower:
                    issues.append('paint_three_parts')
                elif '۲' in body_lower or '2' in body_lower or 'دو' in body_lower:
                    issues.append('paint_two_parts')
                elif '۱' in body_lower or '1' in body_lower or 'یک' in body_lower:
                    issues.append('paint_one_part')
            
            # تشخیص دوررنگ (رنگ کامل)
            elif 'دوررنگ' in body_lower or 'دور رنگ' in body_lower:
                # دوررنگ به معنای تمام رنگ است
                if 'full_paint' not in issues:
                    issues.append('full_paint')
            
            # تشخیص رنگ عمومی
            elif any(keyword in body_lower for keyword in ['رنگ', 'رنگی']):
                # اگر فقط کلمه رنگ وجود دارد، یک قطعه در نظر بگیر
                if 'paint_one_part' not in issues:
                    issues.append('paint_one_part')
        
        # تشخیص اضافی از توضیحات
        if description and description != 'nan':
            desc_lower = description.lower()
            
            # تشخیص مشکلات اضافی از توضیحات
            if any(keyword in desc_lower for keyword in ['تصادف', 'ضربه', 'خسارت', 'آسیب', 'تصادفی']):
                if 'accident_history' not in issues:
                    issues.append('accident_history')
            
            if any(keyword in desc_lower for keyword in ['اورهال', 'تعمیر موتور', 'موتور تعمیری', 'موتور تازه تعمیر']):
                if 'engine_overhaul' not in issues:
                    issues.append('engine_overhaul')
            
            if any(keyword in desc_lower for keyword in ['گیربکس', 'دنده', 'تعمیر گیربکس']):
                if 'gearbox_repair' not in issues:
                    issues.append('gearbox_repair')
            
            # بررسی رنگ فقط اگر بدنه مشکل جدی دارد (نه فقط خراش جزیی)
            body_has_serious_issue = False
            if body_status and body_status != 'nan':
                body_lower_check = body_status.lower().strip()
                # اگر بدنه سالم است یا فقط خراش جزیی دارد، رنگ اضافه نکن
                if not (body_lower_check in ['سالم', 'سالم و بی خط و خش', 'سالم و بی‌خط و خش', 'بدون خط و خش', 'عالی', 'سالم و بی‌خط و خش'] or
                       any(keyword in body_lower_check for keyword in ['خط و خش جزئی', 'خط و خش جزیی', 'خراش جزئی', 'خراش کم'])):
                    body_has_serious_issue = True
            
            # فقط اگر بدنه مشکل جدی دارد، رنگ را بررسی کن
            if body_has_serious_issue:
                if any(keyword in desc_lower for keyword in ['دوررنگ', 'دور رنگ', 'تمام رنگ', 'کامل رنگ']):
                    if 'full_paint' not in issues:
                        issues.append('full_paint')
                elif any(keyword in desc_lower for keyword in ['رنگ', 'نقاشی', 'رنگی']):
                    if not any(paint_issue in issues for paint_issue in ['full_paint', 'paint_one_part', 'paint_two_parts', 'paint_three_parts', 'paint_four_plus']):
                        issues.append('paint_one_part')
            
            # بررسی خراش فقط اگر قبلاً از بدنه اضافه نشده
            if any(keyword in desc_lower for keyword in ['خراش', 'خط و خش', 'خط وخش']):
                if 'minor_scratches' not in issues:
                    issues.append('minor_scratches')
        
        # حذف تکراری‌ها و مرتب‌سازی
        unique_issues = list(set(issues))
        
        # اولویت‌بندی مشکلات (مهم‌ترین اول)
        priority_order = [
            'accident_history', 'full_paint', 'engine_overhaul', 'roof_paint',
            'paint_four_plus', 'paint_three_parts', 'paint_two_parts', 
            'paint_one_part', 'gearbox_repair', 'minor_scratches', 'option_defect'
        ]
        
        sorted_issues = []
        for priority_issue in priority_order:
            if priority_issue in unique_issues:
                sorted_issues.append(priority_issue)
        
        # اضافه کردن مشکلات باقی‌مانده
        for issue in unique_issues:
            if issue not in sorted_issues:
                sorted_issues.append(issue)
        
        return sorted_issues
    
    def extract_price_from_text(self, price_text):
        """استخراج قیمت از متن فارسی"""
        if not price_text or price_text == 'nan':
            return None
        
        # تبدیل اعداد فارسی به انگلیسی
        persian_to_english = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
            '٬': '', ',': ''
        }
        
        price_clean = price_text.strip()
        for persian, english in persian_to_english.items():
            price_clean = price_clean.replace(persian, english)
        
        # استخراج عدد از متن
        price_match = re.search(r'(\d+)', price_clean)
        if price_match:
            return int(price_match.group(1))
        
        return None
    
    def calculate_age_depreciation(self, year):
        """محاسبه افت قیمت بر اساس سن خودرو"""
        if not year:
            return 0
        
        # برای خودروهای 1394 و قبل‌تر
        if year <= 1394:
            current_year = 1404  # سال جاری شمسی
            car_age = current_year - year
            # 2% تا 4% سالانه برای خودروهای قدیمی
            annual_depreciation = (0.02 + 0.04) / 2  # میانگین 3%
            return min(annual_depreciation * (car_age - 9), 0.5)  # حداکثر 50% افت
        
        # برای خودروهای جدیدتر از جدول
        if year in self.age_depreciation:
            factor = self.age_depreciation[year]
            return (factor['min'] + factor['max']) / 2  # میانگین
        
        return 0
    
    def calculate_mileage_depreciation(self, mileage, year=None):
        """محاسبه دقیق افت قیمت بر اساس کارکرد (کیلومتر) - اصلاح شده"""
        if not mileage or not year:
            return 0
        
        current_year = 1404  # سال جاری شمسی
        car_age = current_year - year
        
        # محاسبه کیلومتر طبیعی بر اساس سن خودرو
        if car_age <= 0:
            normal_mileage = 0  # خودروی صفر کیلومتر
        elif car_age <= 2:
            normal_mileage = car_age * 15000  # خودروهای جدید: 15 هزار کیلومتر در سال
        elif car_age <= 5:
            normal_mileage = car_age * 17500  # خودروهای متوسط: 17.5 هزار کیلومتر در سال
        elif car_age <= 10:
            normal_mileage = car_age * 18000  # خودروهای قدیمی‌تر: 18 هزار کیلومتر در سال
        else:
            normal_mileage = car_age * 15000  # خودروهای خیلی قدیمی: 15 هزار کیلومتر در سال
        
        # محاسبه افت بر اساس کیلومتر (اصلاح اساسی)
        base_depreciation = 0
        
        # افت بر اساس کیلومتر کل (نه فقط اضافی)
        if mileage >= 300000:  # بالای 300 هزار کیلومتر
            base_depreciation = 0.20  # 20% افت برای کیلومتر خیلی بالا
        elif mileage >= 250000:  # بالای 250 هزار کیلومتر
            base_depreciation = 0.15  # 15% افت
        elif mileage >= 200000:  # بالای 200 هزار کیلومتر
            base_depreciation = 0.12  # 12% افت
        elif mileage >= 150000:  # بالای 150 هزار کیلومتر
            base_depreciation = 0.08  # 8% افت
        elif mileage >= 100000:  # بالای 100 هزار کیلومتر
            base_depreciation = 0.05  # 5% افت
        elif mileage >= 50000:  # بالای 50 هزار کیلومتر
            base_depreciation = 0.03  # 3% افت
        elif mileage >= 20000:  # بالای 20 هزار کیلومتر
            base_depreciation = 0.01  # 1% افت
        
        # افت اضافی اگر کیلومتر بیش از حد طبیعی باشد
        if mileage > normal_mileage:
            excess_km = mileage - normal_mileage
            excess_depreciation = (excess_km // 10000) * 0.01  # هر 10 هزار کیلومتر اضافی = 1% افت اضافی
            base_depreciation += excess_depreciation
        
        # ارزش اضافی برای خودروهای کم‌کار (کمتر از 10 هزار کیلومتر)
        if mileage < 10000:
            base_depreciation = -0.02  # 2% ارزش اضافی
        
        return min(base_depreciation, 0.25)  # حداکثر 25% افت برای کیلومتر
    
    def calculate_total_depreciation(self, issues, mileage_depreciation, age_depreciation):
        """محاسبه کل افت قیمت شامل افت مشکلات"""
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
        """یافتن قیمت روز خودرو با دقت بالا از هر دو منبع بر اساس برند و تیپ"""
        if market_df is None:
            return None, None
        
        # اولویت با برند و تیپ کامل
        search_terms = []
        if brand_type and brand_type != 'نامشخص':
            search_terms.append(brand_type.lower().strip())
        
        if car_info['car_name']:
            search_terms.append(car_info['car_name'].lower())
        
        if not search_terms:
            return None, None
        
        year = car_info['year']
        
        # مرحله 1: جستجوی دقیق بر اساس برند و تیپ و سال
        best_match = None
        best_score = 0
        best_source = None
        
        for index, row in market_df.iterrows():
            market_name = str(row['Car Name']).lower()
            market_price = row['Numeric Price']
            source = row.get('Source', 'نامشخص')
            
            # فیلتر اولیه: جلوگیری از انتخاب پژو 508 برای پژو 207
            if any('207' in term for term in search_terms) and 'پژو ۵۰۸' in str(row['Car Name']):
                continue
            
            # فیلتر اولیه: جلوگیری از انتخاب قیمت‌های خیلی بالا برای خودروهای قدیمی
            if year and year < 1400 and market_price and market_price > 2000000000:
                continue
            
            # محاسبه امتیاز شباهت برای هر search_term
            max_score = 0
            
            for search_term in search_terms:
                score = 0
                
                # فیلتر اولیه: جلوگیری از تطبیق اشتباه مدل‌ها
                search_lower = search_term.lower()
                market_lower = market_name.lower()
                
                # اگر مدل مشخص در جستجو وجود دارد، باید در نتیجه نیز باشد
                model_numbers = ['206', '207', '405', '508', '2008', '3008', '5008']
                search_model = None
                market_model = None
                
                for model in model_numbers:
                    if model in search_lower:
                        search_model = model
                    if model in market_lower:
                        market_model = model
                
                # اگر مدل‌ها متفاوت باشند، امتیاز صفر
                if search_model and market_model and search_model != market_model:
                    score = 0
                    max_score = max(max_score, score)
                    continue
                
                # فیلتر اضافی: جلوگیری از تطبیق پژو 207 با پژو 508
                if '207' in search_lower and '508' in market_lower:
                    score = 0
                    max_score = max(max_score, score)
                    continue
                
                if '508' in search_lower and '207' in market_lower:
                    score = 0
                    max_score = max(max_score, score)
                    continue
                
                # فیلتر برای TU5: فقط با پژو 207 تطبیق دهد
                if 'tu5' in search_lower and '207' not in market_lower:
                    score = 0
                    max_score = max(max_score, score)
                    continue
                
                # فیلتر قوی: اگر جستجو پژو 207 TU5 است، نباید با پژو 508 تطبیق دهد
                if 'پژو' in search_lower and '207' in search_lower and 'tu5' in search_lower:
                    if 'پژو' in market_lower and '508' in market_lower:
                        score = 0
                        max_score = max(max_score, score)
                        continue
                
                # فیلتر عمومی: جلوگیری از تطبیق قیمت‌های خیلی بالا برای خودروهای معمولی
                if market_price and market_price > 2000000000:  # بیش از 2 میلیارد
                    if year and year < 1400:  # خودروهای قدیمی‌تر از 1400
                        score *= 0.1  # کاهش شدید امتیاز
                
                # امتیاز برای تطبیق دقیق (بهبود یافته)
                if search_term == market_name:
                    score += 1.0  # تطبیق کامل
                elif search_term in market_name:
                    # بررسی تطبیق دقیق کلمات کلیدی
                    search_words = search_term.split()
                    market_words = market_name.split()
                    exact_matches = sum(1 for word in search_words if word in market_words)
                    if exact_matches >= len(search_words) * 0.8:  # حداقل 80% کلمات تطبیق داشته باشند
                        score += 0.9
                    else:
                        score += 0.6
                elif market_name in search_term:
                    score += 0.5
                
                # امتیاز اضافی برای تطبیق دقیق برند و مدل
                # تشخیص برند در نام بازار
                brand_in_market = False
                model_in_market = False
                
                # بررسی برندهای مختلف
                brand_patterns = {
                    'پژو': ['پژو', 'peugeot'],
                    'پراید': ['پراید', 'pride'],
                    'سمند': ['سمند', 'samand'],
                    'تویوتا': ['تویوتا', 'toyota'],
                    'هوندا': ['هوندا', 'honda'],
                    'نیسان': ['نیسان', 'nissan'],
                    'هیوندای': ['هیوندای', 'hyundai'],
                    'کیا': ['کیا', 'kia'],
                    'مزدا': ['مزدا', 'mazda']
                }
                
                for brand, patterns in brand_patterns.items():
                    if any(pattern in search_lower for pattern in patterns):
                        if any(pattern in market_lower for pattern in patterns):
                            brand_in_market = True
                            score += 0.3
                            break
                
                # بررسی مدل‌های عددی
                model_patterns = ['206', '207', '405', '508', '2008', '3008', '5008', '131', '132']
                for model in model_patterns:
                    if model in search_lower and model in market_lower:
                        model_in_market = True
                        score += 0.4
                        break
                
                # امتیاز اضافی برای تطبیق کامل برند و مدل
                if brand_in_market and model_in_market:
                    score += 0.5
                
                # امتیاز برای تطبیق کلمات کلیدی
                search_words = search_term.split()
                market_words = market_name.split()
                
                common_words = set(search_words) & set(market_words)
                if common_words:
                    score += len(common_words) * 0.3
                
                # امتیاز اضافی برای تطبیق سال
                if year and str(year) in market_name:
                    score += 0.4
                
                # ترجیح به منبع z4car برای خودروهای جدیدتر
                if source == 'z4car' and year and year >= 1400:
                    score += 0.1
                
                # ترجیح به منبع همراه مکانیک برای خودروهای قدیمی‌تر
                if source == 'همراه مکانیک' and (not year or year < 1400):
                    score += 0.1
                
                # ترجیح ویژه به z4car برای پراید و پژو (دقیق‌تر است)
                if source == 'z4car':
                    for search_term in search_terms:
                        if any(brand in search_term for brand in ['پراید', 'پژو']):
                            score += 0.15  # امتیاز اضافی برای پراید و پژو از z4car
                            break
                
                max_score = max(max_score, score)
            
            if max_score > best_score and max_score > 0.4:  # حداقل 40% شباهت
                best_score = max_score
                best_match = market_price
                best_source = source
        
        # مرحله 2: اگر تطبیق دقیق پیدا نشد، جستجوی عمومی‌تر
        if not best_match:
            # جستجوی بر اساس برند اصلی - گسترده شده
            brand_keywords = {
                # برندهای ایرانی
                'پژو': ['پژو', 'peugeot', '206', '207', '405', 'پارس'],
                'پراید': ['پراید', 'pride', '131', '132'],
                'سمند': ['سمند', 'samand'],
                'دنا': ['دنا', 'dena'],
                'رانا': ['رانا', 'rana'],
                'تیبا': ['تیبا', 'tiba'],
                'ساینا': ['ساینا', 'saina'],
                'آریو': ['آریو', 'ario'],
                'شاهین': ['شاهین', 'shahin'],
                'تارا': ['تارا', 'tara'],
                'کوییک': ['کوییک', 'quick'],
                # برندهای آسیایی
                'تویوتا': ['تویوتا', 'toyota', 'کمری', 'کرولا', 'پرادو', 'لندکروزر'],
                'هوندا': ['هوندا', 'honda', 'سیویک', 'آکورد', 'crv'],
                'نیسان': ['نیسان', 'nissan', 'قشقایی', 'تینا', 'سانی', 'مورانو'],
                'هیوندای': ['هیوندای', 'hyundai', 'النترا', 'سوناتا', 'توسان', 'آزرا'],
                'کیا': ['کیا', 'kia', 'سراتو', 'اسپورتیج', 'سورنتو', 'پیکانتو'],
                'مزدا': ['مزدا', 'mazda', '323', '626'],
                'میتسوبیشی': ['میتسوبیشی', 'mitsubishi', 'لنسر', 'پاجرو', 'اوتلندر'],
                # برندهای اروپایی
                'بی ام و': ['بی ام و', 'bmw', 'سری', 'x1', 'x3', 'x5', 'x6'],
                'بنز': ['بنز', 'mercedes', 'مرسدس', 'کلاس'],
                'آئودی': ['آئودی', 'audi', 'a3', 'a4', 'a6', 'q3', 'q5', 'q7'],
                'فولکس': ['فولکس', 'volkswagen', 'پاسات', 'جتا', 'گلف'],
                'رنو': ['رنو', 'renault', 'ساندرو', 'تندر', 'فلوئنس'],
                'پورشه': ['پورشه', 'porsche', '911', 'کاین', 'ماکان'],
                # برندهای لوکس
                'لکسوس': ['لکسوس', 'lexus', 'es', 'ls', 'rx', 'lx', 'nx'],
                'اینفینیتی': ['اینفینیتی', 'infiniti', 'g35', 'fx35', 'qx56'],
                'جگوار': ['جگوار', 'jaguar', 'xf', 'xj', 'f-pace'],
                'لندرور': ['لندرور', 'land rover', 'range rover', 'discovery'],
                # برندهای چینی
                'چری': ['چری', 'chery', 'آریزو', 'تیگو'],
                'ام وی ام': ['ام وی ام', 'mvm', 'x33', 'x22', '315', '110'],
                'هاوال': ['هاوال', 'haval', 'h2', 'h6', 'h9'],
                'گک': ['گک', 'gac', 'گونو', 'امزوم', 'امکو'],
                'لیفان': ['لیفان', 'lifan', 'x60', 'x70', '520', '620'],
                'گریت وال': ['گریت وال', 'great wall', 'ولکس', 'وینگل'],
                # برندهای دیگر
                'ولوو': ['ولوو', 'volvo', 'xc60', 'xc90', 's60', 'v40'],
                'مینی': ['مینی', 'mini', 'cooper', 'countryman'],
                'فیات': ['فیات', 'fiat', 'پاندا', 'پونتو'],
                'دوو': ['دوو', 'daewoo', 'سیلو', 'نکسیا', 'ماتیز']
            }
            
            for brand, keywords in brand_keywords.items():
                if any(keyword in car_name for keyword in keywords):
                    brand_matches = market_df[market_df['Car Name'].str.contains('|'.join(keywords), case=False, na=False)]
                    if not brand_matches.empty:
                        # انتخاب نزدیک‌ترین قیمت بر اساس سال
                        if year:
                            year_matches = brand_matches[brand_matches['Car Name'].str.contains(str(year), na=False)]
                            if not year_matches.empty:
                                best_match = year_matches.iloc[0]['Numeric Price']
                                best_source = year_matches.iloc[0].get('Source', 'نامشخص')
                                break
                        
                        # اگر سال پیدا نشد، اولین مورد را انتخاب کن
                        best_match = brand_matches.iloc[0]['Numeric Price']
                        best_source = brand_matches.iloc[0].get('Source', 'نامشخص')
                        break
        
        return best_match, best_source
    
    def calculate_estimated_price(self, market_price, total_depreciation, car_data=None):
        """محاسبه قیمت تخمینی با استفاده از ML"""
        if not market_price:
            return None
        
        # محاسبه قیمت پایه
        base_estimated_price = market_price * (1 - total_depreciation)
        base_estimated_price = max(base_estimated_price, market_price * 0.3)
        
        # استفاده از ML اگر در دسترس است
        if self.ml_calculator and car_data:
            try:
                # آماده‌سازی داده‌ها برای ML
                ml_data = car_data.copy() if isinstance(car_data, dict) else {}
                ml_data.update({
                    'market_price': market_price,
                    'total_depreciation': total_depreciation,
                    'base_estimated_price': base_estimated_price
                })
                
                # پیش‌بینی ML
                ml_prediction = self.ml_calculator.predict_price(ml_data)
                
                if ml_prediction and ml_prediction > 0:
                    # ترکیب پیش‌بینی ML با روش پایه (وزن‌دار)
                    # 70% ML + 30% روش پایه
                    final_price = (0.7 * ml_prediction) + (0.3 * base_estimated_price)
                    print(f"🤖 ML پیش‌بینی: {ml_prediction:,.0f} | پایه: {base_estimated_price:,.0f} | نهایی: {final_price:,.0f}")
                    return final_price
                    
            except Exception as e:
                print(f"⚠️ خطا در ML، استفاده از روش پایه: {e}")
        
        return base_estimated_price
    
    def learn_from_feedback(self, car_data, actual_price, predicted_price):
        """یادگیری از بازخورد کاربر"""
        if self.ml_calculator:
            try:
                self.ml_calculator.learn_from_feedback(car_data, actual_price, predicted_price)
                print(f"📚 بازخورد ثبت شد: واقعی={actual_price:,.0f}, پیش‌بینی={predicted_price:,.0f}")
                return True
            except Exception as e:
                print(f"❌ خطا در ثبت بازخورد: {e}")
        return False
    
    def train_ml_model(self, training_data_file=None):
        """آموزش مدل یادگیری ماشین"""
        if self.ml_calculator:
            try:
                if not training_data_file:
                    training_data_file = "unified_car_price_analysis.xlsx"
                
                if os.path.exists(training_data_file):
                    success = self.ml_calculator.train_model(training_data_file)
                    if success:
                        print("✅ مدل ML با موفقیت آموزش داده شد")
                        return True
                    else:
                        print("❌ آموزش مدل ناموفق")
                else:
                    print(f"⚠️ فایل آموزشی {training_data_file} یافت نشد")
            except Exception as e:
                print(f"❌ خطا در آموزش مدل: {e}")
        else:
            print("⚠️ سیستم ML در دسترس نیست")
        return False
    
    def get_ml_info(self):
        """اطلاعات سیستم یادگیری ماشین"""
        if self.ml_calculator:
            return self.ml_calculator.get_model_info()
        return {'ml_available': False}
    
    def process_ads(self, divar_file, hamrah_file, z4car_file, output_file):
        """پردازش کامل آگهی‌ها با استفاده از هر دو منبع قیمت"""
        print("بارگذاری داده‌ها...")
        market_df = self.load_market_prices(hamrah_file, z4car_file)
        divar_df = self.load_divar_ads(divar_file)
        
        if market_df is None or divar_df is None:
            print("خطا در بارگذاری فایل‌ها")
            return
        
        results = []
        
        print(f"پردازش {len(divar_df)} آگهی...")
        
        for index, row in divar_df.iterrows():
            try:
                # استخراج اطلاعات از ستون‌های مشخص
                title = str(row.get('عنوان', '')) if 'عنوان' in row else ''
                description = str(row.get('توضیحات', '')) if 'توضیحات' in row else ''
                brand_type = str(row.get('برند_و_تیپ', '')) if 'برند_و_تیپ' in row else ''
                model_year = str(row.get('مدل', '')) if 'مدل' in row else ''
                mileage_str = str(row.get('کارکرد', '')) if 'کارکرد' in row else ''
                engine_status = str(row.get('موتور', '')) if 'موتور' in row else ''
                chassis_status = str(row.get('شاسی', '')) if 'شاسی' in row else ''
                body_status = str(row.get('بدنه', '')) if 'بدنه' in row else ''
                
                # استخراج اطلاعات خودرو با استفاده از ستون‌های مشخص
                car_info = self.extract_car_info_from_columns(
                    title, description, brand_type, model_year, mileage_str
                )
                
                # تشخیص مشکلات با استفاده از ستون‌های مشخص
                issues = self.detect_issues_from_columns(
                    title, description, engine_status, chassis_status, body_status
                )
                
                # محاسبه افت کارکرد
                mileage_depreciation = self.calculate_mileage_depreciation(
                    car_info['mileage'], car_info['year']
                )
                
                # محاسبه افت سن
                age_depreciation = self.calculate_age_depreciation(car_info['year'])
                
                # محاسبه کل افت شامل افت مشکلات
                total_depreciation, issues_depreciation = self.calculate_total_depreciation(issues, mileage_depreciation, age_depreciation)
                
                # یافتن قیمت روز با استفاده از برند و تیپ
                market_price, price_source = self.find_market_price(car_info, market_df, brand_type)
                
                # محاسبه قیمت تخمینی
                estimated_price = self.calculate_estimated_price(market_price, total_depreciation)
                
                # استخراج قیمت آگهی
                ad_price_str = str(row.get('قیمت', '')) if 'قیمت' in row else ''
                ad_price = self.extract_price_from_text(ad_price_str)
                
                result = {
                    'عنوان آگهی': title,
                    'برند و تیپ': brand_type or 'نامشخص',
                    'نام خودرو': car_info['car_name'] or 'نامشخص',
                    'سال': car_info['year'] or 'نامشخص',
                    'کیلومتر': f"{car_info['mileage']:,}" if car_info['mileage'] else 'نامشخص',
                    'قیمت آگهی (تومان)': f"{ad_price:,.0f}" if ad_price else 'نامشخص',
                    'قیمت روز (تومان)': f"{market_price:,.0f}" if market_price else 'یافت نشد',
                    'منبع قیمت': price_source or 'نامشخص',
                    'وضعیت موتور': engine_status or 'نامشخص',
                    'وضعیت شاسی': chassis_status or 'نامشخص',
                    'وضعیت بدنه': body_status or 'نامشخص',
                    'مشکلات تشخیص داده شده': ', '.join(issues) if issues else 'هیچ',
                    'افت کارکرد': f"{mileage_depreciation:.1%}",
                    'افت سن خودرو': f"{age_depreciation:.1%}",
                    'افت مشکلات': f"{issues_depreciation:.1%}",
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
        
        print(f"\nپردازش کامل شد!")
        print(f"تعداد آگهی‌های پردازش شده: {len(results)}")
        print(f"نتایج در فایل {output_file} ذخیره شد")
        
        # آمار کلی
        successful_calculations = len([r for r in results if r['قیمت تخمینی (تومان)'] != 'محاسبه نشد'])
        hamrah_count = len([r for r in results if r['منبع قیمت'] == 'همراه مکانیک'])
        z4car_count = len([r for r in results if r['منبع قیمت'] == 'z4car'])
        
        print(f"تعداد آگهی‌های با قیمت محاسبه شده: {successful_calculations}")
        print(f"قیمت‌های از همراه مکانیک: {hamrah_count}")
        print(f"قیمت‌های از z4car: {z4car_count}")
        
        return results_df

# اجرای اسکریپت
if __name__ == "__main__":
    calculator = CarPriceCalculator()
    
    # مسیر فایل‌ها
    divar_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/divar_ads_all_20250806_231216.xlsx"
    hamrah_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/hamrah_mechanic_prices.xlsx"
    z4car_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/z4car_prices.xlsx"
    output_file = "/Users/erfantaghavi/PycharmProjects/pythonProject/unified_car_price_analysis.xlsx"
    
    # پردازش آگهی‌ها
    results = calculator.process_ads(divar_file, hamrah_file, z4car_file, output_file)
    
    if results is not None:
        print("\n=== نمونه نتایج ===")
        print(results.head().to_string(index=False))
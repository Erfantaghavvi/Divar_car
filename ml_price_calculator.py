import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import warnings
warnings.filterwarnings('ignore')

class MachineLearningPriceCalculator:
    def __init__(self, base_calculator=None):
        self.base_calculator = base_calculator
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.label_encoders = {}
        self.feature_columns = [
            'year', 'mileage', 'market_price', 'engine_status_encoded', 
            'chassis_status_encoded', 'body_status_encoded', 'brand_encoded',
            'has_accident', 'has_paint_issue', 'has_engine_issue', 'has_gearbox_issue',
            'paint_severity', 'total_issues_count'
        ]
        self.model_file = 'ml_price_model.joblib'
        self.encoders_file = 'label_encoders.joblib'
        self.learning_data_file = 'learning_data.json'
        self.performance_log = 'model_performance.json'
        
        # بارگذاری مدل و encoders در صورت وجود
        self.load_model()
        
    def encode_categorical_features(self, df):
        """تبدیل ویژگی‌های کیفی به عددی"""
        categorical_columns = ['engine_status', 'chassis_status', 'body_status', 'brand']
        
        for col in categorical_columns:
            if col in df.columns:
                encoded_col = f"{col}_encoded"
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[encoded_col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    # برای داده‌های جدید که ممکن است مقادیر جدیدی داشته باشند
                    try:
                        df[encoded_col] = self.label_encoders[col].transform(df[col].astype(str))
                    except ValueError:
                        # اگر مقدار جدیدی وجود دارد، آن را به encoder اضافه کن
                        unique_values = list(self.label_encoders[col].classes_) + list(df[col].unique())
                        self.label_encoders[col].classes_ = np.array(list(set(unique_values)))
                        df[encoded_col] = self.label_encoders[col].transform(df[col].astype(str))
        
        return df
    
    def extract_features_from_issues(self, issues_str):
        """استخراج ویژگی از لیست مشکلات"""
        if pd.isna(issues_str) or issues_str == 'هیچ':
            return {
                'has_accident': 0,
                'has_paint_issue': 0,
                'has_engine_issue': 0,
                'has_gearbox_issue': 0,
                'paint_severity': 0,
                'total_issues_count': 0
            }
        
        issues = str(issues_str).lower()
        
        # تشخیص انواع مشکلات
        has_accident = 1 if 'accident' in issues else 0
        has_paint_issue = 1 if any(paint in issues for paint in ['paint', 'رنگ']) else 0
        has_engine_issue = 1 if 'engine' in issues else 0
        has_gearbox_issue = 1 if 'gearbox' in issues else 0
        
        # شدت مشکل رنگ
        paint_severity = 0
        if 'full_paint' in issues:
            paint_severity = 4
        elif 'paint_four_plus' in issues:
            paint_severity = 4
        elif 'paint_three_parts' in issues:
            paint_severity = 3
        elif 'paint_two_parts' in issues:
            paint_severity = 2
        elif 'paint_one_part' in issues:
            paint_severity = 1
        
        # تعداد کل مشکلات
        total_issues_count = len([x for x in issues.split(',') if x.strip() and x.strip() != 'هیچ'])
        
        return {
            'has_accident': has_accident,
            'has_paint_issue': has_paint_issue,
            'has_engine_issue': has_engine_issue,
            'has_gearbox_issue': has_gearbox_issue,
            'paint_severity': paint_severity,
            'total_issues_count': total_issues_count
        }
    
    def prepare_training_data(self, df):
        """آماده‌سازی داده‌ها برای آموزش"""
        # کپی از داده‌ها
        data = df.copy()
        
        # پاک‌سازی داده‌ها
        data = data.dropna(subset=['قیمت تخمینی (تومان)', 'قیمت روز (تومان)'])
        
        # تبدیل قیمت‌ها به عدد
        for price_col in ['قیمت تخمینی (تومان)', 'قیمت روز (تومان)', 'قیمت آگهی (تومان)']:
            if price_col in data.columns:
                data[price_col] = data[price_col].astype(str).str.replace(',', '').str.extract(r'(\d+)').astype(float)
        
        # تبدیل سال و کیلومتر
        if 'سال' in data.columns:
            data['year'] = pd.to_numeric(data['سال'], errors='coerce')
        if 'کیلومتر' in data.columns:
            data['mileage'] = data['کیلومتر'].astype(str).str.replace(',', '').str.extract(r'(\d+)').astype(float)
        
        # نام‌گذاری مجدد ستون‌ها
        column_mapping = {
            'وضعیت موتور': 'engine_status',
            'وضعیت شاسی': 'chassis_status',
            'وضعیت بدنه': 'body_status',
            'نام خودرو': 'brand',
            'قیمت روز (تومان)': 'market_price',
            'قیمت تخمینی (تومان)': 'estimated_price',
            'مشکلات تشخیص داده شده': 'issues'
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in data.columns:
                data[new_name] = data[old_name]
        
        # استخراج ویژگی از مشکلات
        if 'issues' in data.columns:
            issues_features = data['issues'].apply(self.extract_features_from_issues)
            issues_df = pd.DataFrame(list(issues_features))
            data = pd.concat([data, issues_df], axis=1)
        
        # تبدیل ویژگی‌های کیفی
        data = self.encode_categorical_features(data)
        
        return data
    
    def train_model(self, training_data_file):
        """آموزش مدل بر اساس داده‌های موجود"""
        try:
            # بارگذاری داده‌های آموزشی
            df = pd.read_excel(training_data_file)
            print(f"📊 بارگذاری {len(df)} رکورد برای آموزش")
            
            # آماده‌سازی داده‌ها
            data = self.prepare_training_data(df)
            
            # انتخاب ویژگی‌ها
            available_features = [col for col in self.feature_columns if col in data.columns]
            X = data[available_features]
            y = data['estimated_price']
            
            # حذف مقادیر NaN
            mask = ~(X.isna().any(axis=1) | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(X) < 10:
                print("⚠️ داده‌های کافی برای آموزش وجود ندارد")
                return False
            
            # تقسیم داده‌ها
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # آموزش مدل
            print("🤖 شروع آموزش مدل...")
            self.model.fit(X_train, y_train)
            
            # ارزیابی مدل
            y_pred = self.model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"📈 عملکرد مدل:")
            print(f"   MAE: {mae:,.0f} تومان")
            print(f"   R²: {r2:.3f}")
            
            # ذخیره عملکرد
            performance = {
                'timestamp': datetime.now().isoformat(),
                'mae': float(mae),
                'r2': float(r2),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features_used': available_features
            }
            
            self.save_performance(performance)
            self.save_model()
            
            return True
            
        except Exception as e:
            print(f"❌ خطا در آموزش مدل: {e}")
            return False
    
    def predict_price(self, car_data):
        """پیش‌بینی قیمت با استفاده از مدل آموزش دیده"""
        try:
            # آماده‌سازی داده‌ها
            df = pd.DataFrame([car_data])
            data = self.prepare_training_data(df)
            
            # انتخاب ویژگی‌ها
            available_features = [col for col in self.feature_columns if col in data.columns]
            X = data[available_features]
            
            # پیش‌بینی
            if hasattr(self.model, 'predict') and len(X) > 0:
                prediction = self.model.predict(X)[0]
                
                # اطمینان از اینکه پیش‌بینی منطقی است
                if prediction > 0:
                    return float(prediction)
            
            # در صورت عدم موفقیت، از روش پایه استفاده کن
            if self.base_calculator:
                return self.base_calculator.calculate_estimated_price(
                    car_data.get('market_price', 0),
                    car_data.get('total_depreciation', 0)
                )
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطا در پیش‌بینی: {e}")
            return None
    
    def learn_from_feedback(self, car_data, actual_price, predicted_price):
        """یادگیری از بازخورد کاربر"""
        feedback_data = {
            'timestamp': datetime.now().isoformat(),
            'car_data': car_data,
            'predicted_price': predicted_price,
            'actual_price': actual_price,
            'error': abs(actual_price - predicted_price) if predicted_price else None
        }
        
        # ذخیره بازخورد
        self.save_learning_data(feedback_data)
        
        # اگر تعداد کافی بازخورد جمع شد، مدل را دوباره آموزش بده
        learning_data = self.load_learning_data()
        if len(learning_data) >= 50:  # هر 50 بازخورد
            print("🔄 شروع آموزش مجدد مدل با داده‌های جدید...")
            self.retrain_with_feedback()
    
    def retrain_with_feedback(self):
        """آموزش مجدد مدل با داده‌های بازخورد"""
        try:
            learning_data = self.load_learning_data()
            
            # تبدیل بازخورد به DataFrame
            feedback_rows = []
            for item in learning_data:
                if item.get('actual_price') and item.get('car_data'):
                    row = item['car_data'].copy()
                    row['estimated_price'] = item['actual_price']
                    feedback_rows.append(row)
            
            if len(feedback_rows) < 10:
                return False
            
            df = pd.DataFrame(feedback_rows)
            data = self.prepare_training_data(df)
            
            # آموزش مدل
            available_features = [col for col in self.feature_columns if col in data.columns]
            X = data[available_features]
            y = data['estimated_price']
            
            mask = ~(X.isna().any(axis=1) | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(X) >= 10:
                self.model.fit(X, y)
                self.save_model()
                
                # پاک کردن داده‌های یادگیری
                self.clear_learning_data()
                
                print(f"✅ مدل با {len(X)} نمونه بازخورد آموزش داده شد")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ خطا در آموزش مجدد: {e}")
            return False
    
    def save_model(self):
        """ذخیره مدل و encoders"""
        try:
            joblib.dump(self.model, self.model_file)
            joblib.dump(self.label_encoders, self.encoders_file)
            print("💾 مدل ذخیره شد")
        except Exception as e:
            print(f"❌ خطا در ذخیره مدل: {e}")
    
    def load_model(self):
        """بارگذاری مدل و encoders"""
        try:
            if os.path.exists(self.model_file) and os.path.exists(self.encoders_file):
                self.model = joblib.load(self.model_file)
                self.label_encoders = joblib.load(self.encoders_file)
                print("📂 مدل بارگذاری شد")
                return True
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری مدل: {e}")
        return False
    
    def save_learning_data(self, data):
        """ذخیره داده‌های یادگیری"""
        try:
            learning_data = self.load_learning_data()
            learning_data.append(data)
            
            with open(self.learning_data_file, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ خطا در ذخیره داده‌های یادگیری: {e}")
    
    def load_learning_data(self):
        """بارگذاری داده‌های یادگیری"""
        try:
            if os.path.exists(self.learning_data_file):
                with open(self.learning_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری داده‌های یادگیری: {e}")
        return []
    
    def clear_learning_data(self):
        """پاک کردن داده‌های یادگیری"""
        try:
            if os.path.exists(self.learning_data_file):
                os.remove(self.learning_data_file)
        except Exception as e:
            print(f"❌ خطا در پاک کردن داده‌های یادگیری: {e}")
    
    def save_performance(self, performance):
        """ذخیره عملکرد مدل"""
        try:
            performances = []
            if os.path.exists(self.performance_log):
                with open(self.performance_log, 'r', encoding='utf-8') as f:
                    performances = json.load(f)
            
            performances.append(performance)
            
            with open(self.performance_log, 'w', encoding='utf-8') as f:
                json.dump(performances, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ خطا در ذخیره عملکرد: {e}")
    
    def get_model_info(self):
        """اطلاعات مدل"""
        info = {
            'model_exists': hasattr(self.model, 'predict'),
            'features_count': len(self.feature_columns),
            'encoders_count': len(self.label_encoders)
        }
        
        # آخرین عملکرد
        try:
            if os.path.exists(self.performance_log):
                with open(self.performance_log, 'r', encoding='utf-8') as f:
                    performances = json.load(f)
                    if performances:
                        info['last_performance'] = performances[-1]
        except:
            pass
        
        # تعداد داده‌های یادگیری
        learning_data = self.load_learning_data()
        info['learning_data_count'] = len(learning_data)
        
        return info

# تست سیستم
if __name__ == "__main__":
    # ایجاد نمونه
    ml_calc = MachineLearningPriceCalculator()
    
    # نمایش اطلاعات
    info = ml_calc.get_model_info()
    print("🤖 اطلاعات سیستم یادگیری ماشین:")
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # تست آموزش (اگر فایل داده وجود دارد)
    test_file = "unified_car_price_analysis.xlsx"
    if os.path.exists(test_file):
        print(f"\n📚 شروع آموزش با فایل {test_file}")
        success = ml_calc.train_model(test_file)
        if success:
            print("✅ آموزش موفقیت‌آمیز بود")
        else:
            print("❌ آموزش ناموفق")
    else:
        print(f"⚠️ فایل {test_file} یافت نشد")
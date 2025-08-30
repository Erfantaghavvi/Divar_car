# 🤖 راهنمای سیستم یادگیری ماشین برای قیمت‌گذاری خودرو

## 📋 فهرست مطالب
- [معرفی](#معرفی)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [نحوه استفاده](#نحوه-استفاده)
- [ویژگی‌ها](#ویژگی‌ها)
- [آموزش مدل](#آموزش-مدل)
- [یادگیری از بازخورد](#یادگیری-از-بازخورد)
- [مثال‌های عملی](#مثال‌های-عملی)

## 🎯 معرفی

سیستم یادگیری ماشین برای قیمت‌گذاری خودرو یک سیستم هوشمند است که:

- **از داده‌های گذشته یاد می‌گیرد** 📚
- **پیش‌بینی‌های دقیق‌تری ارائه می‌دهد** 🎯
- **خودش را بهبود می‌دهد** 🔄
- **از بازخورد کاربران استفاده می‌کند** 👥

## 🛠️ نصب و راه‌اندازی

### 1. نصب کتابخانه‌های مورد نیاز:
```bash
pip install scikit-learn joblib numpy pandas
```

### 2. بررسی نصب:
```python
from car_price_calculator import CarPriceCalculator

# ایجاد calculator با ML فعال
calculator = CarPriceCalculator(enable_ml=True)

# بررسی وضعیت ML
ml_info = calculator.get_ml_info()
print(ml_info)
```

## 🚀 نحوه استفاده

### استفاده پایه:
```python
from car_price_calculator import CarPriceCalculator

# ایجاد calculator با ML
calculator = CarPriceCalculator(enable_ml=True)

# داده‌های خودرو
car_data = {
    'year': 1395,
    'mileage': 150000,
    'brand': 'پراید',
    'engine_status': 'سالم',
    'chassis_status': 'سالم',
    'body_status': 'سالم و بی‌خط و خش',
    'issues': 'هیچ'
}

# پیش‌بینی قیمت با ML
market_price = 390000000
total_depreciation = 0.25

estimated_price = calculator.calculate_estimated_price(
    market_price, 
    total_depreciation, 
    car_data  # داده‌های اضافی برای ML
)

print(f"قیمت تخمینی: {estimated_price:,.0f} تومان")
```

## ✨ ویژگی‌ها

### 🧠 هوش مصنوعی پیشرفته:
- **Random Forest Regressor** برای پیش‌بینی دقیق
- **Feature Engineering** هوشمند
- **Ensemble Learning** (ترکیب ML + روش پایه)

### 📊 ویژگی‌های استخراج شده:
- سال تولید
- کیلومتر
- قیمت بازار
- وضعیت موتور، شاسی، بدنه
- نوع و شدت مشکلات
- تعداد کل مشکلات

### 🎯 پیش‌بینی ترکیبی:
```
قیمت نهایی = (70% × پیش‌بینی ML) + (30% × روش پایه)
```

## 📚 آموزش مدل

### آموزش خودکار:
```python
# آموزش با فایل موجود
success = calculator.train_ml_model("unified_car_price_analysis.xlsx")

if success:
    print("✅ مدل آموزش داده شد")
else:
    print("❌ آموزش ناموفق")
```

### آموزش دستی:
```python
# دسترسی مستقیم به ML calculator
ml_calc = calculator.ml_calculator

if ml_calc:
    success = ml_calc.train_model("data.xlsx")
    print(f"آموزش: {'موفق' if success else 'ناموفق'}")
```

### نمایش عملکرد:
```python
ml_info = calculator.get_ml_info()

if 'last_performance' in ml_info:
    perf = ml_info['last_performance']
    print(f"MAE: {perf['mae']:,.0f} تومان")
    print(f"R²: {perf['r2']:.3f}")
    print(f"نمونه‌های آموزشی: {perf['training_samples']}")
```

## 🔄 یادگیری از بازخورد

### ثبت بازخورد:
```python
# داده‌های خودرو
car_data = {
    'year': 1395,
    'mileage': 150000,
    'brand': 'پراید'
}

# قیمت‌ها
predicted_price = 250000000  # پیش‌بینی سیستم
actual_price = 240000000     # قیمت واقعی (از کاربر)

# ثبت بازخورد
success = calculator.learn_from_feedback(
    car_data, 
    actual_price, 
    predicted_price
)

print(f"بازخورد: {'ثبت شد' if success else 'خطا'}")
```

### آموزش مجدد خودکار:
سیستم هر 50 بازخورد، خودش را دوباره آموزش می‌دهد:

```python
# بعد از 50 بازخورد:
# 🔄 شروع آموزش مجدد مدل با داده‌های جدید...
# ✅ مدل با 50 نمونه بازخورد آموزش داده شد
```

## 💡 مثال‌های عملی

### مثال 1: پیش‌بینی ساده
```python
from car_price_calculator import CarPriceCalculator

calculator = CarPriceCalculator(enable_ml=True)

# خودروی تست
car = {
    'year': 1392,
    'mileage': 200000,
    'brand': 'سمند',
    'engine_status': 'تعمیر شده',
    'body_status': 'خط و خش جزیی',
    'issues': 'engine_overhaul, minor_scratches'
}

# پیش‌بینی
price = calculator.calculate_estimated_price(
    780000000,  # قیمت بازار
    0.45,       # درصد افت
    car         # داده‌های ML
)

print(f"قیمت تخمینی: {price:,.0f} تومان")
```

### مثال 2: آموزش و تست
```python
# آموزش مدل
training_success = calculator.train_ml_model()

if training_success:
    # تست با چند نمونه
    test_cases = [
        {'year': 1395, 'brand': 'پراید', 'mileage': 120000},
        {'year': 1390, 'brand': 'پژو', 'mileage': 180000},
        {'year': 1392, 'brand': 'سمند', 'mileage': 200000}
    ]
    
    for i, case in enumerate(test_cases, 1):
        price = calculator.calculate_estimated_price(
            500000000, 0.3, case
        )
        print(f"تست {i}: {price:,.0f} تومان")
```

### مثال 3: یادگیری تدریجی
```python
# شبیه‌سازی فرآیند یادگیری
feedbacks = [
    {'car': {'year': 1395, 'brand': 'پراید'}, 'predicted': 250000000, 'actual': 240000000},
    {'car': {'year': 1390, 'brand': 'پژو'}, 'predicted': 450000000, 'actual': 470000000},
    {'car': {'year': 1392, 'brand': 'سمند'}, 'predicted': 350000000, 'actual': 330000000}
]

for feedback in feedbacks:
    calculator.learn_from_feedback(
        feedback['car'],
        feedback['actual'],
        feedback['predicted']
    )
    print(f"بازخورد ثبت شد: خطا = {abs(feedback['actual'] - feedback['predicted']):,.0f}")
```

## 📊 نظارت و عملکرد

### بررسی وضعیت:
```python
info = calculator.get_ml_info()

print(f"مدل موجود: {info.get('model_exists', False)}")
print(f"تعداد ویژگی‌ها: {info.get('features_count', 0)}")
print(f"داده‌های یادگیری: {info.get('learning_data_count', 0)}")

if 'last_performance' in info:
    perf = info['last_performance']
    print(f"دقت مدل (R²): {perf['r2']:.3f}")
    print(f"میانگین خطا: {perf['mae']:,.0f} تومان")
```

### فایل‌های ایجاد شده:
- `ml_price_model.joblib` - مدل آموزش دیده
- `label_encoders.joblib` - رمزگذارهای متغیرهای کیفی
- `learning_data.json` - داده‌های بازخورد
- `model_performance.json` - تاریخچه عملکرد

## 🔧 تست سیستم

### اجرای تست کامل:
```bash
python test_ml_system.py
```

### خروجی مورد انتظار:
```
🧪 شروع تست سیستم یادگیری ماشین
🤖 سیستم یادگیری ماشین فعال شد
📊 اطلاعات سیستم ML:
📁 فایل آموزشی یافت شد: unified_car_price_analysis.xlsx
🤖 شروع آموزش مدل...
📈 عملکرد مدل:
   MAE: 45,230,000 تومان
   R²: 0.847
✅ مدل ML با موفقیت آموزش داده شد
🔮 تست پیش‌بینی قیمت...
🤖 ML پیش‌بینی: 245,000,000 | پایه: 250,000,000 | نهایی: 248,500,000
📚 تست یادگیری از بازخورد...
📚 بازخورد ثبت شد: واقعی=240,000,000, پیش‌بینی=248,500,000
✅ تست سیستم ML کامل شد!
```

## ⚠️ نکات مهم

### الزامات:
- **Python 3.8+**
- **scikit-learn >= 1.3.0**
- **joblib >= 1.3.0**
- **حداقل 10 نمونه** برای آموزش

### بهینه‌سازی:
- **داده‌های بیشتر = دقت بالاتر**
- **بازخورد منظم = یادگیری بهتر**
- **تنوع داده‌ها = عملکرد بهتر**

### محدودیت‌ها:
- نیاز به داده‌های کافی برای آموزش
- عملکرد بستگی به کیفیت داده‌ها دارد
- نیاز به بازخورد منظم برای بهبود

## 🎉 مزایای سیستم

### 🎯 دقت بالاتر:
- ترکیب ML + روش‌های سنتی
- یادگیری از الگوهای پیچیده
- تطبیق با شرایط بازار

### 🔄 خودبهبودی:
- یادگیری از بازخورد
- آموزش مجدد خودکار
- تطبیق با تغییرات

### 📊 شفافیت:
- نمایش دقت مدل
- مقایسه با روش پایه
- آمار عملکرد

### 🛡️ قابلیت اطمینان:
- Fallback به روش پایه
- مدیریت خطا
- ذخیره خودکار

---

**🚀 با این سیستم، قیمت‌گذاری خودرو هوشمندتر، دقیق‌تر و قابل اعتمادتر می‌شود!**
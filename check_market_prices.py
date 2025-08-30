import pandas as pd

# بررسی فایل‌های قیمت روز
print("=== بررسی فایل hamrah_mechanic_prices.xlsx ===")
try:
    hamrah_df = pd.read_excel('hamrah_mechanic_prices.xlsx')
    print(f"تعداد ردیف‌ها: {len(hamrah_df)}")
    print(f"ستون‌ها: {list(hamrah_df.columns)}")
    print("\nنمونه داده‌ها:")
    print(hamrah_df.head())
except Exception as e:
    print(f"خطا در خواندن فایل: {e}")

print("\n=== بررسی فایل z4car_prices.xlsx ===")
try:
    z4car_df = pd.read_excel('z4car_prices.xlsx')
    print(f"تعداد ردیف‌ها: {len(z4car_df)}")
    print(f"ستون‌ها: {list(z4car_df.columns)}")
    print("\nنمونه داده‌ها:")
    print(z4car_df.head())
except Exception as e:
    print(f"خطا در خواندن فایل: {e}")

# ترکیب داده‌ها
print("\n=== ترکیب داده‌های قیمت روز ===")
try:
    # خواندن هر دو فایل
    hamrah_df = pd.read_excel('hamrah_mechanic_prices.xlsx')
    z4car_df = pd.read_excel('z4car_prices.xlsx')
    
    # استانداردسازی ستون‌ها
    if 'Car Name' in hamrah_df.columns:
        hamrah_df = hamrah_df.rename(columns={'Car Name': 'نام خودرو', 'Price': 'قیمت'})
    
    # اضافه کردن منبع
    hamrah_df['منبع'] = 'همراه مکانیک'
    z4car_df['منبع'] = 'Z4Car'
    
    # ترکیب داده‌ها
    combined_df = pd.concat([hamrah_df, z4car_df], ignore_index=True)
    
    print(f"تعداد کل رکوردهای ترکیب شده: {len(combined_df)}")
    print("\nنمونه داده‌های ترکیب شده:")
    print(combined_df.head(10))
    
    # ذخیره فایل ترکیب شده
    combined_df.to_excel('combined_market_prices.xlsx', index=False)
    print("\nداده‌های ترکیب شده در فایل combined_market_prices.xlsx ذخیره شد")
    
except Exception as e:
    print(f"خطا در ترکیب داده‌ها: {e}")
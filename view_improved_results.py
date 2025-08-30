import pandas as pd

# خواندن فایل Excel و تبدیل به CSV
try:
    df = pd.read_excel('/Users/erfantaghavi/PycharmProjects/pythonProject/combined_car_price_analysis.xlsx')
    
    # ذخیره به CSV
    df.to_csv('/Users/erfantaghavi/PycharmProjects/pythonProject/combined_car_price_analysis.csv', 
              index=False, encoding='utf-8')
    
    print(f"تعداد کل آگهی‌ها: {len(df)}")
    print(f"ستون‌ها: {list(df.columns)}")
    
    # آمار کلی
    calculated_prices = df[df['قیمت تخمینی (تومان)'] != 'محاسبه نشد']
    identified_cars = df[df['نام خودرو'] != 'نامشخص']
    found_prices = df[df['قیمت روز (تومان)'] != 'یافت نشد']
    
    print(f"\n=== آمار بهبود یافته ===")
    print(f"آگهی‌های با قیمت محاسبه شده: {len(calculated_prices)}")
    print(f"خودروهای شناسایی شده: {len(identified_cars)}")
    print(f"قیمت‌های یافت شده: {len(found_prices)}")
    
    # نمایش منابع قیمت
    source_counts = df['منبع قیمت'].value_counts()
    print(f"\n=== منابع قیمت ===")
    for source, count in source_counts.items():
        print(f"{source}: {count}")
    
    # نمایش برندهای شناسایی شده
    brand_counts = df[df['نام خودرو'] != 'نامشخص']['نام خودرو'].value_counts().head(10)
    print(f"\n=== 10 برند برتر شناسایی شده ===")
    for brand, count in brand_counts.items():
        print(f"{brand}: {count}")
    
    # نمایش 10 رکورد اول
    print(f"\n=== 10 رکورد اول ===")
    print(df.head(10)[['عنوان آگهی', 'نام خودرو', 'قیمت روز (تومان)', 'منبع قیمت', 'قیمت تخمینی (تومان)']].to_string(index=False))
    
except Exception as e:
    print(f"خطا: {e}")
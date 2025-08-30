import pandas as pd
import os

# یافتن جدیدترین فایل اکسل
files = [f for f in os.listdir('.') if f.startswith('optimized_divar_ads_') and f.endswith('.xlsx')]
if files:
    latest_file = max(files, key=os.path.getctime)
    print(f"بررسی فایل: {latest_file}")
    
    # خواندن فایل اکسل
    df = pd.read_excel(latest_file)
    
    print(f"\nتعداد ردیف‌ها: {len(df)}")
    print(f"تعداد ستون‌ها: {len(df.columns)}")
    
    print("\nنام ستون‌ها:")
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. {col}")
    
    print("\nنمونه داده (5 ردیف اول):")
    print(df.head().to_string())
else:
    print("هیچ فایل اکسلی یافت نشد!")
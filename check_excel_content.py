import pandas as pd
import os

# یافتن جدیدترین فایل اکسل
excel_files = [f for f in os.listdir('.') if f.startswith('optimized_divar_ads_') and f.endswith('.xlsx')]
if excel_files:
    latest_file = max(excel_files, key=lambda x: os.path.getctime(x))
    print(f"بررسی فایل: {latest_file}")
    
    # خواندن فایل اکسل
    df = pd.read_excel(latest_file)
    
    print(f"\nتعداد ردیف‌ها: {len(df)}")
    print(f"تعداد ستون‌ها: {len(df.columns)}")
    
    # نمایش ستون‌های مهم
    important_columns = ['عنوان آگهی', 'قیمت آگهی (تومان)', 'قیمت روز (تومان)', 'قیمت تخمینی (تومان)']
    
    for col in important_columns:
        if col in df.columns:
            print(f"\n📊 ستون '{col}':")
            print(f"   مقادیر منحصر به فرد: {df[col].nunique()}")
            print(f"   نمونه مقادیر: {df[col].dropna().head(5).tolist()}")
            print(f"   مقادیر خالی: {df[col].isna().sum()}")
        else:
            print(f"\n❌ ستون '{col}' یافت نشد")
    
    # نمایش 3 ردیف اول
    print("\n📋 سه ردیف اول:")
    for i in range(min(3, len(df))):
        print(f"\nردیف {i+1}:")
        for col in ['عنوان آگهی', 'قیمت آگهی (تومان)']:
            if col in df.columns:
                print(f"  {col}: {df.iloc[i][col]}")
else:
    print("هیچ فایل اکسل یافت نشد")
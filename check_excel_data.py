import pandas as pd
import os

# بررسی فایل اکسل اصلی
MAIN_EXCEL_FILE = "divar_ads_main.xlsx"

if os.path.exists(MAIN_EXCEL_FILE):
    try:
        df = pd.read_excel(MAIN_EXCEL_FILE, engine='openpyxl')
        print(f"📊 تعداد کل رکوردها در فایل اکسل: {len(df)}")
        print(f"📋 ستون‌های موجود: {list(df.columns)}")
        
        if len(df) > 0:
            print("\n🔍 نمونه از 5 رکورد اول:")
            print(df.head().to_string())
            
            print("\n🔍 نمونه از 5 رکورد آخر:")
            print(df.tail().to_string())
            
            # بررسی آخرین تاریخ ذخیره
            if 'تاریخ ذخیره' in df.columns:
                latest_date = df['تاریخ ذخیره'].max()
                print(f"\n📅 آخرین تاریخ ذخیره: {latest_date}")
        else:
            print("⚠️ فایل اکسل خالی است")
            
    except Exception as e:
        print(f"❌ خطا در خواندن فایل اکسل: {e}")
else:
    print("❌ فایل اکسل وجود ندارد")

# بررسی فایل CSV نیز
CSV_FILE = "divar_ads_main.csv"
if os.path.exists(CSV_FILE):
    try:
        df_csv = pd.read_csv(CSV_FILE)
        print(f"\n📊 تعداد کل رکوردها در فایل CSV: {len(df_csv)}")
    except Exception as e:
        print(f"❌ خطا در خواندن فایل CSV: {e}")
else:
    print("\n⚠️ فایل CSV وجود ندارد")
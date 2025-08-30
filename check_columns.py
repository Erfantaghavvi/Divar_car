import pandas as pd

# بررسی ساختار فایل آگهی‌های دیوار
try:
    df = pd.read_excel('/Users/erfantaghavi/PycharmProjects/pythonProject/divar_ads_all_20250806_231216.xlsx')
    
    print(f"تعداد کل رکوردها: {len(df)}")
    print(f"تعداد ستون‌ها: {len(df.columns)}")
    print("\nنام ستون‌ها:")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. {col}")
    
    print("\n=== نمونه 5 رکورد اول ===")
    print(df.head().to_string())
    
    # بررسی وجود ستون‌های مورد نظر
    target_columns = ['برند_و_تیپ', 'مدل', 'کارکرد']
    print("\n=== بررسی ستون‌های مورد نظر ===")
    for col in target_columns:
        if col in df.columns:
            print(f"✅ ستون '{col}' موجود است")
            print(f"   نمونه مقادیر: {df[col].dropna().head(3).tolist()}")
        else:
            print(f"❌ ستون '{col}' موجود نیست")
            # جستجوی ستون‌های مشابه
            similar = [c for c in df.columns if col.lower() in c.lower() or c.lower() in col.lower()]
            if similar:
                print(f"   ستون‌های مشابه: {similar}")
    
except Exception as e:
    print(f"خطا: {e}")
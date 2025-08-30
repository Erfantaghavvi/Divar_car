import pandas as pd

# خواندن فایل Excel و تبدیل به CSV
try:
    df = pd.read_excel('/Users/erfantaghavi/PycharmProjects/pythonProject/unified_car_price_analysis.xlsx')
    
    # ذخیره به CSV
    df.to_csv('/Users/erfantaghavi/PycharmProjects/pythonProject/unified_car_price_analysis.csv', 
              index=False, encoding='utf-8')
    
    print(f"تعداد کل آگهی‌ها: {len(df)}")
    print(f"ستون‌ها: {list(df.columns)}")
    
    # آمار کلی
    calculated_prices = df[df['قیمت تخمینی (تومان)'] != 'محاسبه نشد']
    identified_cars = df[df['نام خودرو'] != 'نامشخص']
    found_prices = df[df['قیمت روز (تومان)'] != 'یافت نشد']
    
    print(f"\n=== آمار نهایی ===")
    print(f"آگهی‌های با قیمت محاسبه شده: {len(calculated_prices)} از {len(df)} ({len(calculated_prices)/len(df)*100:.1f}%)")
    print(f"خودروهای شناسایی شده: {len(identified_cars)} از {len(df)} ({len(identified_cars)/len(df)*100:.1f}%)")
    print(f"قیمت‌های یافت شده: {len(found_prices)} از {len(df)} ({len(found_prices)/len(df)*100:.1f}%)")
    
    # نمایش منابع قیمت
    source_counts = df['منبع قیمت'].value_counts()
    print(f"\n=== منابع قیمت ===")
    for source, count in source_counts.items():
        print(f"{source}: {count}")
    
    # نمایش برندهای شناسایی شده با جزئیات بیشتر
    brand_counts = df[df['نام خودرو'] != 'نامشخص']['نام خودرو'].value_counts()
    print(f"\n=== برندهای شناسایی شده ===")
    for brand, count in brand_counts.items():
        print(f"{brand}: {count}")
    
    # نمایش تطبیق برند و تیپ
    print(f"\n=== تطبیق برند و تیپ ===")
    brand_type_matches = df[['برند و تیپ', 'نام خودرو', 'منبع قیمت']].drop_duplicates()
    for _, row in brand_type_matches.iterrows():
        if row['نام خودرو'] != 'نامشخص':
            print(f"{row['برند و تیپ']} → {row['نام خودرو']} ({row['منبع قیمت']})")
    
    # آمار دقت تطبیق
    z4car_matches = df[df['منبع قیمت'] == 'z4car']
    hamrah_matches = df[df['منبع قیمت'] == 'همراه مکانیک']
    
    print(f"\n=== آمار دقت تطبیق ===")
    print(f"تطبیق‌های z4car: {len(z4car_matches)} ({len(z4car_matches)/len(df)*100:.1f}%)")
    print(f"تطبیق‌های همراه مکانیک: {len(hamrah_matches)} ({len(hamrah_matches)/len(df)*100:.1f}%)")
    
    # نمایش قیمت‌های مختلف برای برندهای مشابه
    print(f"\n=== تنوع قیمت‌ها ===")
    for brand in ['پراید', 'پژو', 'سمند']:
        brand_data = df[df['نام خودرو'] == brand]
        if len(brand_data) > 0:
            prices = brand_data['قیمت روز (تومان)'].apply(lambda x: int(str(x).replace(',', '')) if str(x).replace(',', '').isdigit() else 0)
            if len(prices) > 1:
                print(f"{brand}: {len(brand_data)} مورد، قیمت از {prices.min():,} تا {prices.max():,} تومان")
            else:
                print(f"{brand}: {len(brand_data)} مورد")
    
    # نمایش مشکلات تشخیص داده شده
    issues_with_problems = df[df['مشکلات تشخیص داده شده'] != 'هیچ']
    print(f"\n=== آگهی‌های با مشکل: {len(issues_with_problems)} ===")
    
    # نمایش تمام رکوردها با ستون‌های جدید
    print(f"\n=== تمام رکوردها ===")
    display_columns = ['عنوان آگهی', 'برند و تیپ', 'نام خودرو', 'سال', 'کیلومتر', 
                      'قیمت آگهی (تومان)', 'قیمت روز (تومان)', 'منبع قیمت', 
                      'وضعیت موتور', 'وضعیت شاسی', 'وضعیت بدنه',
                      'مشکلات تشخیص داده شده', 'قیمت تخمینی (تومان)']
    
    # فقط ستون‌هایی که در DataFrame موجود هستند را نمایش بده
    available_columns = [col for col in display_columns if col in df.columns]
    print(df[available_columns].to_string(index=False))
    
    # نمایش آمار قیمت‌ها
    if 'قیمت آگهی (تومان)' in df.columns:
        ad_prices = df[df['قیمت آگهی (تومان)'] != 'نامشخص']['قیمت آگهی (تومان)']
        if len(ad_prices) > 0:
            print(f"\n=== آمار قیمت آگهی‌ها ===")
            print(f"تعداد آگهی‌های با قیمت: {len(ad_prices)}")
    
    # نمایش وضعیت‌های مختلف
    if 'وضعیت موتور' in df.columns:
        engine_status = df['وضعیت موتور'].value_counts()
        print(f"\n=== وضعیت موتور ===")
        for status, count in engine_status.items():
            print(f"{status}: {count}")
    
    if 'وضعیت بدنه' in df.columns:
        body_status = df['وضعیت بدنه'].value_counts()
        print(f"\n=== وضعیت بدنه ===")
        for status, count in body_status.items():
            print(f"{status}: {count}")
    
except Exception as e:
    print(f"خطا: {e}")
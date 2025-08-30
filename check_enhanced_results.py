#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بررسی نتایج فایل بهبود یافته
"""

import pandas as pd
import os
import glob

def check_enhanced_results():
    """بررسی آخرین فایل نتایج بهبود یافته"""
    
    # یافتن آخرین فایل optimized
    pattern = "/Users/erfantaghavi/PycharmProjects/pythonProject/optimized_divar_ads_*.xlsx"
    files = glob.glob(pattern)
    
    if not files:
        print("❌ هیچ فایل optimized یافت نشد")
        return
    
    # انتخاب آخرین فایل
    latest_file = max(files, key=os.path.getctime)
    print(f"📁 بررسی فایل: {os.path.basename(latest_file)}")
    
    try:
        df = pd.read_excel(latest_file)
        
        print(f"\n📊 آمار کلی:")
        print(f"تعداد رکوردها: {len(df)}")
        print(f"تعداد ستون‌ها: {len(df.columns)}")
        
        print(f"\n📋 ستون‌های موجود:")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. {col}")
        
        if len(df) > 0:
            print(f"\n🔍 نمونه داده‌ها:")
            print(df.head().to_string(index=False))
            
            # بررسی ستون‌های مهم
            important_cols = ['عنوان آگهی', 'قیمت آگهی (تومان)', 'قیمت روز (تومان)', 'قیمت تخمینی (تومان)']
            print(f"\n📈 بررسی ستون‌های مهم:")
            
            for col in important_cols:
                if col in df.columns:
                    non_empty = df[col].notna().sum()
                    total = len(df)
                    percentage = (non_empty / total) * 100 if total > 0 else 0
                    print(f"✅ {col}: {non_empty}/{total} ({percentage:.1f}%) پر شده")
                    
                    # نمونه مقادیر
                    sample_values = df[col].dropna().head(3).tolist()
                    if sample_values:
                        print(f"   نمونه: {sample_values}")
                else:
                    print(f"❌ {col}: موجود نیست")
        
    except Exception as e:
        print(f"❌ خطا در خواندن فایل: {e}")

if __name__ == "__main__":
    check_enhanced_results()
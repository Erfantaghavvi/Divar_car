import pandas as pd

# خواندن فایل اکسل جدید
df = pd.read_excel('optimized_divar_ads_20250829_175614.xlsx')

print('✅ بررسی نهایی تغییرات:')
print('\n1. برند و تیپ:')
print(df[['عنوان آگهی', 'برند و تیپ']].to_string(index=False))

print('\n2. کیلومتر (با واحد هزار):')
print(df[['عنوان آگهی', 'کیلومتر']].to_string(index=False))

print('\n3. توضیحات (اول 150 کاراکتر):')
for i, row in df.iterrows():
    title = str(row['عنوان آگهی'])[:30]
    description = str(row['توضیحات'])[:150] if pd.notna(row['توضیحات']) else 'خالی'
    print(f'{title}... -> {description}...')

print('\n4. تمام ستون‌ها:')
print(list(df.columns))
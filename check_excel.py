import pandas as pd

file_path = '/Users/erfantaghavi/PycharmProjects/pythonProject/divar_ads_main.xlsx'
df = pd.read_excel(file_path)
print('Columns in the Excel file:')
print(df.columns.tolist())
print('\nFirst row sample:')
print(df.iloc[0].to_dict())
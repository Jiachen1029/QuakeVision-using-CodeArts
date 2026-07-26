import pandas as pd

try:
    # Try reading with default engine (usually openpyxl for xlsx, xlrd for xls)
    # The file extension is .xls but sometimes it might be .xlsx content or vice versa.
    # 'xlrd' is needed for .xls files.
    df = pd.read_excel('速报目录.xls')
    print("Columns:")
    print(df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head().to_string())
    print("\nData Types:")
    print(df.dtypes)
except Exception as e:
    print(f"Error reading excel file: {e}")

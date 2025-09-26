import pandas as pd

# خواندن فایل اکسل
df = pd.read_excel("parents.xlsx")  # یا users.xlsx اگر از اون استفاده می‌کنی

# نمایش نام ستون‌ها قبل از اصلاح
print("ستون‌ها قبل از اصلاح:")
print(df.columns.tolist())

# اصلاح فاصله‌های مخفی و اضافی
df.columns = df.columns.str.strip().str.replace('\u200c', ' ').str.replace('\xa0', ' ')

# نمایش نام ستون‌ها بعد از اصلاح
print("\nستون‌ها بعد از اصلاح:")
print(df.columns.tolist())

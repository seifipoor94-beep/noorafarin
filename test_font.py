import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import arabic_reshaper
from bidi.algorithm import get_display
import os

# مسیر فونت
font_path = os.path.join(os.getcwd(), 'fonts', 'Vazir.ttf')
font_prop = fm.FontProperties(fname=font_path)

# آماده‌سازی متن فارسی
text = 'سلام فاطمه جان!'
reshaped = arabic_reshaper.reshape(text)
bidi_text = get_display(reshaped)

title_text = get_display(arabic_reshaper.reshape('تست فونت فارسی'))

# رسم نمودار
plt.figure()
plt.text(0.5, 0.5, bidi_text, fontproperties=font_prop, fontsize=20, ha='center')
plt.title(title_text, fontproperties=font_prop)
plt.axis('off')
plt.savefig('test_font.png')
plt.close()

print("✅ تصویر تست فونت فارسی ساخته شد.")

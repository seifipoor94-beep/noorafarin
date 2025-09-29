import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import plotly.express as px
import os
import arabic_reshaper
from bidi.algorithm import get_display
import matplotlib.font_manager as fm

def reshape(text):
    return get_display(arabic_reshaper.reshape(text))

# تنظیم فونت فارسی
font_path = "fonts/vazir.ttf"
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    rcParams['font.family'] = font_prop.get_name()
else:
    rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.unicode_minus'] = False

# تنظیم صفحه
st.set_page_config(page_title="📊 درس‌بان | داشبورد تحلیلی کلاس", layout="wide")
st.title("📊 درس‌بان | گزارش نمرات و وضعیت دانش‌آموزان")

# تصویر خوش‌آمدگویی
st.image(
    "https://copilot.microsoft.com/th/id/BCO.fe2284b6-0e75-4a1d-8d3e-917ff48f283b.png",
    caption="📚 خوش آمدید به درس‌بان | همراهی هوشمند برای آموزگاران، با عشق از فاطمه سیفی‌پور 💖",
   use_container_width=True
)

# ورود کاربر
st.sidebar.title("🔐 ورود به درس‌بان")
entered_role = st.sidebar.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار", "معاون", "مدیر"])
entered_code = st.sidebar.text_input("رمز ورود:", type="password")

if not os.path.exists("data/users.xlsx"):
    st.error("❌ فایل کاربران یافت نشد.")
    st.stop()

users_df = pd.read_excel("data/users.xlsx")
users_df.columns = users_df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')
valid_user = users_df[(users_df["نقش"] == entered_role) & (users_df["رمز ورود"] == entered_code)]

if valid_user.empty:
    st.warning("❌ رمز یا نقش اشتباه است.")
    st.stop()

user_name = valid_user.iloc[0]["نام کاربر"]
st.success(f"✅ خوش آمدید {user_name} عزیز! شما به‌عنوان {entered_role} وارد درس‌بان شده‌اید.")
# آپلود فایل نمرات توسط آموزگار
if entered_role == "آموزگار":
    st.subheader("📤 لطفاً فایل نمرات کلاس خود را آپلود کنید")
    uploaded_file = st.file_uploader("فایل اکسل نمرات:", type=["xlsx"])
    if uploaded_file is None:
        st.warning("لطفاً فایل نمرات را آپلود کنید تا داشبورد فعال شود.")
        st.stop()
    xls = pd.ExcelFile(uploaded_file)
else:
    # برای نقش‌های دیگر، فایل ثابت استفاده می‌شود
    if not os.path.exists("data/nomarat_darsi.xlsx"):
        st.error("❌ فایل نمرات یافت نشد.")
        st.stop()
    xls = pd.ExcelFile("data/nomarat_darsi.xlsx")

# پردازش همه شیت‌ها
all_data = []
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    df.columns = df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')
    if 'نام دانش آموز' in df.columns:
        df.rename(columns={'نام دانش آموز':'نام دانش‌آموز'}, inplace=True)
    elif 'نام دانش‌آموز' not in df.columns:
        continue
    rename_map = {}
    for col in df.columns:
        if "هفته" in col:
            if "اول" in col: rename_map[col] = "هفته اول"
            elif "دوم" in col: rename_map[col] = "هفته دوم"
            elif "سوم" in col: rename_map[col] = "هفته سوم"
            elif "چهارم" in col: rename_map[col] = "هفته چهارم"
    df.rename(columns=rename_map, inplace=True)
    score_columns = [col for col in df.columns if col != 'نام دانش‌آموز']
    df_long = df.melt(id_vars=['نام دانش‌آموز'], value_vars=score_columns,
                      var_name='هفته', value_name='نمره')
    df_long['نمره'] = pd.to_numeric(df_long['نمره'], errors='coerce')
    df_long = df_long.dropna(subset=['نمره'])
    df_long['نمره'] = df_long['نمره'].astype(int)
    df_long['درس'] = sheet_name
    all_data.append(df_long)

scores_long = pd.concat(all_data, ignore_index=True)
# انتخاب درس و دانش‌آموز
lessons = scores_long['درس'].unique()
selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
lesson_data = scores_long[scores_long['درس'] == selected_lesson]

if entered_role == "والد":
    selected_student = user_name
else:
    students = lesson_data['نام دانش‌آموز'].unique()
    selected_student = st.selectbox("دانش‌آموز را انتخاب کنید:", students)

student_data = lesson_data[lesson_data['نام دانش‌آموز'] == selected_student]
# وضعیت کیفی
status_map = {1: "نیاز به تلاش بیشتر", 2: "قابل قبول", 3: "خوب", 4: "خیلی خوب"}
status_colors = {
    "نیاز به تلاش بیشتر": "red",
    "قابل قبول": "orange",
    "خوب": "blue",
    "خیلی خوب": "green"
}

# نمودار کیفی کلاس
st.subheader("🍩 نمودار وضعیت کیفی کلاس")
student_avg = lesson_data.groupby('نام دانش‌آموز')['نمره'].mean().reset_index()
student_avg['وضعیت'] = student_avg['نمره'].round().astype(int).map(status_map)
fig_pie = px.pie(
    student_avg,
    names='وضعیت',
    title=f"درصد وضعیت کیفی دانش‌آموزان در درس {selected_lesson}",
    color='وضعیت',
    color_discrete_map=status_colors
)
st.plotly_chart(fig_pie, use_container_width=True)

# نمودار خطی دانش‌آموز
st.subheader(f"📈 روند نمرات {selected_student}")
if not student_data.empty:
    fig_line = px.line(
        student_data,
        x='هفته',
        y='نمره',
        markers=True,
        title=f"روند نمرات {selected_student} در درس {selected_lesson}"
    )
    fig_line.update_traces(line_color='orange')
    st.plotly_chart(fig_line, use_container_width=True)

# رتبه‌بندی درس به درس
if entered_role in ["مدیر", "معاون", "آموزگار"]:
    st.subheader("🏆 رتبه‌بندی درس به درس")
    lesson_rank = lesson_data.groupby('نام دانش‌آموز')['نمره'].mean().reset_index()
    lesson_rank['رتبه'] = lesson_rank['نمره'].rank(ascending=False, method='min').astype(int)
    lesson_rank = lesson_rank.sort_values('رتبه')
    st.dataframe(lesson_rank[['رتبه', 'نام دانش‌آموز', 'نمره']])

    st.subheader("🏅 رتبه‌بندی کلی کلاس")
    overall_avg = scores_long.groupby('نام دانش‌آموز')['نمره'].mean().reset_index()
    overall_avg['رتبه'] = overall_avg['نمره'].rank(ascending=False, method='min').astype(int)
    overall_avg = overall_avg.sort_values('رتبه')
    st.dataframe(overall_avg[['رتبه', 'نام دانش‌آموز', 'نمره']])
def generate_pdf(student_name, scores_long, status_map, status_colors):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    if os.path.exists("fonts/Vazir.ttf"):
        pdfmetrics.registerFont(TTFont('Vazir', 'fonts/Vazir.ttf'))
        font_name = 'Vazir'
    else:
        font_name = "Helvetica"

    c.setFont(font_name, 18)
    c.drawCentredString(width / 2, height - 50, reshape(f"کارنامه دانش‌آموز {student_name}"))

    font_size = 12
    headers = ["درس", "میانگین دانش‌آموز", "میانگین کلاس", "وضعیت"]
    rows = []

    for lesson in scores_long['درس'].unique():
        df_student = scores_long[
            (scores_long['درس'] == lesson) &
            (scores_long['نام دانش‌آموز'] == student_name)
        ]
        df_class = scores_long[scores_long['درس'] == lesson]
        if df_student.empty:
            continue
        avg_student = df_student['نمره'].mean()
        avg_class = df_class['نمره'].mean()
        status = status_map.get(int(round(avg_student)), "نامشخص")
        row = [lesson, f"{avg_student:.2f}", f"{avg_class:.2f}", status]
        rows.append(row)

    col_widths = []
    for i in range(len(headers)):
        max_width = pdfmetrics.stringWidth(reshape(headers[i]), font_name, font_size)
        for row in rows:
            w = pdfmetrics.stringWidth(reshape(str(row[i])), font_name, font_size)
            max_width = max(max_width, w)
        col_widths.append(max_width + 20)

    total_width = sum(col_widths)
    start_x = width - 50 - total_width
    y = height - 100
    row_height = 25

    c.setFont(font_name, font_size + 2)
    for i in range(len(headers)):
        x = start_x + sum(col_widths[:i])
        c.rect(x, y, col_widths[i], row_height, stroke=1, fill=0)
        c.drawCentredString(x + col_widths[i] / 2, y + 7, reshape(headers[i]))
    y -= row_height

    c.setFont(font_name, font_size)
    for row in rows:
        for i in range(len(row)):
            x = start_x + sum(col_widths[:i])
            c.rect(x, y, col_widths[i], row_height, stroke=1, fill=0)
            c.drawCentredString(x + col_widths[i] / 2, y + 7, reshape(str(row[i])))
        y -= row_height

    # نمودار خطی نمرات
    df_student_all = scores_long[scores_long['نام دانش‌آموز'] == student_name]
    plt.figure(figsize=(6, 3))
    for lesson in df_student_all['درس'].unique():
        df_l = df_student_all[df_student_all['درس'] == lesson]
        plt.plot(df_l['هفته'], df_l['نمره'], marker='o', label=reshape(lesson))
    plt.title(reshape("روند نمرات دانش‌آموز"), fontsize=12)
    plt.xlabel(reshape("هفته"), fontsize=10)
    plt.ylabel(reshape("نمره"), fontsize=10)
    plt.legend()
    line_buf = BytesIO()
    plt.tight_layout()
    plt.savefig(line_buf, format='png')
    plt.close()
    line_buf.seek(0)
    c.drawImage(ImageReader(line_buf), 50, y - 150, width=500, height=150)

    # امضای برند
    c.setFont(font_name, 12)
    c.drawCentredString(width / 2, 40, reshape("درس‌بان | همراهی هوشمند برای آموزگاران، با عشق از فاطمه سیفی‌پور 💖"))

    c.save()
    buffer.seek(0)
    return buffer

# دکمه دانلود PDF
pdf_buf = generate_pdf(selected_student, scores_long, status_map, status_colors)
st.download_button(
    label="📥 دانلود کارنامه کامل با نمودار خطی",
    data=pdf_buf,
    file_name=f"کارنامه_{selected_student}.pdf",
    mime="application/pdf"
)


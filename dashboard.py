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

def reshape(text):
    return get_display(arabic_reshaper.reshape(text))

rcParams['font.family'] = 'Tahoma'
rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="📊 داشبورد نورآفرین", layout="wide")
st.title("📊 داشبورد نورآفرین | گزارش نمرات دانش‌آموزان")

if not os.path.exists("data/users.xlsx") or not os.path.exists("data/nomarat_darsi.xlsx"):
    st.error("❌ یکی از فایل‌های داده پیدا نشد! لطفا مسیرها را بررسی کنید.")
    st.stop()

users_df = pd.read_excel("data/users.xlsx")
users_df.columns = users_df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')

xls = pd.ExcelFile("data/nomarat_darsi.xlsx")
all_data = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    df.columns = df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')
    
    if 'نام دانش آموز' in df.columns:
        df.rename(columns={'نام دانش آموز':'نام دانش‌آموز'}, inplace=True)
    elif 'نام دانش‌آموز' not in df.columns:
        st.warning(f"ستون نام دانش‌آموز در شیت {sheet_name} یافت نشد و این شیت نادیده گرفته شد.")
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
# فرم ورود
st.sidebar.title("🔐 ورود به داشبورد")
entered_role = st.sidebar.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار","معاون", "مدیر"])
entered_code = st.sidebar.text_input("رمز ورود:", type="password")

valid_user = users_df[(users_df["نقش"] == entered_role) & (users_df["رمز ورود"] == entered_code)]
if valid_user.empty:
    st.warning("❌ رمز یا نقش اشتباه است.")
    st.stop()
user_name = valid_user.iloc[0]["نام کاربر"]
st.success(f"✅ خوش آمدید {user_name} عزیز! شما به‌عنوان {entered_role} وارد شده‌اید.")

# انتخاب درس و دانش‌آموز
if entered_role == "والد":
    student_scores = scores_long[scores_long['نام دانش‌آموز'] == user_name]
    lessons = student_scores['درس'].unique()
    selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
    selected_student = user_name
else:
    lessons = scores_long['درس'].unique()
    selected_lesson = st.selectbox("درس مورد نظر را انتخاب کنید:", lessons)
    students = scores_long[scores_long['درس'] == selected_lesson]['نام دانش‌آموز'].unique()
    selected_student = st.selectbox("دانش‌آموز را انتخاب کنید:", students)

lesson_data = scores_long[scores_long['درس'] == selected_lesson]
student_data = lesson_data[lesson_data['نام دانش‌آموز'] == selected_student]

# وضعیت کیفی
status_map = {1:"نیاز به تلاش بیشتر", 2:"قابل قبول", 3:"خوب", 4:"خیلی خوب"}
status_colors = {"نیاز به تلاش بیشتر": "red", "قابل قبول":"orange","خوب":"blue","خیلی خوب":"green"}
# نمودار دایره‌ای کلاس
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
st.subheader("🏆 رتبه‌بندی درس به درس")
lesson_rank = lesson_data.groupby('نام دانش‌آموز')['نمره'].mean().reset_index()
lesson_rank['رتبه'] = lesson_rank['نمره'].rank(ascending=False, method='min').astype(int)
lesson_rank = lesson_rank.sort_values('رتبه')
st.dataframe(lesson_rank[['رتبه','نام دانش‌آموز','نمره']])

# رتبه‌بندی کلی
st.subheader("🏅 رتبه‌بندی کلی کلاس")
overall_avg = scores_long.groupby('نام دانش‌آموز')['نمره'].mean().reset_index()
overall_avg['رتبه'] = overall_avg['نمره'].rank(ascending=False, method='min').astype(int)
overall_avg = overall_avg.sort_values('رتبه')
st.dataframe(overall_avg[['رتبه','نام دانش‌آموز','نمره']])

# نمایش کارنامه
st.subheader(f"📝 کارنامه {selected_student}")
student_overall = []
for lesson in scores_long['درس'].unique():
    df_lesson = scores_long[(scores_long['درس']==lesson) & (scores_long['نام دانش‌آموز']==selected_student)]
    if df_lesson.empty: continue
    avg_score = df_lesson['نمره'].mean()
    status = status_map.get(int(round(avg_score)),"نامشخص")
    student_overall.append({"درس":lesson,"میانگین":round(avg_score,2),"وضعیت":status})
df_card = pd.DataFrame(student_overall)
st.dataframe(df_card.style.applymap(lambda v: f"color:{status_colors[v]}" if v in status_colors else ""))

# تابع تولید PDF
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
    c.drawCentredString(width/2, height-50, reshape(f"کارنامه دانش‌آموز {student_name}"))

    # جدول کارنامه
    c.setFont(font_name, 14)
    y = height-100
    c.drawString(50,y, reshape("درس"))
    c.drawString(250,y, reshape("میانگین"))
    c.drawString(400,y, reshape("وضعیت"))
    y -= 20
    c.setFont(font_name, 12)
    for lesson in scores_long['درس'].unique():
        df_lesson = scores_long[(scores_long['درس'] == lesson) & (scores_long['نام دانش‌آموز'] == student_name)]
        if df_lesson.empty: continue
        avg_score = df_lesson['نمره'].mean()
        status = status_map.get(int(round(avg_score)), "نامشخص")
        c.drawString(50, y, reshape(lesson))
        c.drawString(250, y, str(round(avg_score, 2)))
        c.drawString(400, y, reshape(status))
        y -= 20

    # نمودار خطی
    df_student = scores_long[scores_long['نام دانش‌آموز'] == student_name]
    plt.figure(figsize=(6,3))
    for lesson in df_student['درس'].unique():
        df_l = df_student[df_student['درس'] == lesson]
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
    c.drawImage(ImageReader(line_buf), 50, y-150, width=500, height=150)
    y -= 170

    # نمودار دایره‌ای
    class_status = df_student.groupby('درس')['نمره'].mean().round().astype(int).map(status_map)
    status_counts = class_status.value_counts()
    plt.figure(figsize=(5,3))
    plt.pie(status_counts, labels=[reshape(label) for label in status_counts.index], autopct='%1.1f%%',
            colors=['red','orange','blue','green'])
    plt.title(reshape("وضعیت کیفی کلاس"), fontsize=12)
    pie_buf = BytesIO()
    plt.savefig(pie_buf, format='png')
    plt.close()
    pie_buf.seek(0)
    c.drawImage(ImageReader(pie_buf), 50, y-150, width=300, height=150)

    # امضای پایانی
    c.setFont(font_name, 12)
    c.drawCentredString(width/2, 40, reshape("طراحی‌شده با عشق توسط آموزگار: فاطمه سیفی‌پور 💖"))

    c.save()
    buffer.seek(0)
    return buffer

# دکمه دانلود PDF
pdf_buf = generate_pdf(selected_student, scores_long, status_map, status_colors)
st.download_button(
    label="📥 دانلود کارنامه کامل با نمودارها",
    data=pdf_buf,
    file_name=f"کارنامه_{selected_student}.pdf",
    mime="application/pdf"
)

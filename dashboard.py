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

# ورود کاربر با کنترل وضعیت
st.sidebar.title("🔐 ورود به درس‌بان")
entered_role = st.sidebar.selectbox("نقش خود را انتخاب کنید:", ["والد", "آموزگار", "معاون", "مدیر"])
entered_code = st.sidebar.text_input("رمز ورود:", type="password")
login_button = st.sidebar.button("✅ ورود")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if login_button:
    if not os.path.exists("data/users.xlsx"):
        st.error("❌ فایل کاربران یافت نشد.")
        st.stop()
    users_df = pd.read_excel("data/users.xlsx")
    users_df.columns = users_df.columns.str.strip().str.replace('\u200c',' ').str.replace('\xa0',' ')
    valid_user = users_df[(users_df["نقش"] == entered_role) & (users_df["رمز ورود"] == entered_code)]
    if not valid_user.empty:
        st.session_state.logged_in = True
        st.session_state.user_info = valid_user.iloc[0].to_dict()
        st.session_state.users_df = users_df  # ✅ ذخیره فایل کاربران برای استفاده بعدی
    else:
        st.warning("❌ رمز یا نقش اشتباه است.")

if not st.session_state.logged_in:
    st.image(
        "https://copilot.microsoft.com/th/id/BCO.4a841959-901a-4011-8a27-ee2d06c74fd7.png",
        caption="📈 مسیر رشد دانش‌آموزان با همراهی درس‌بان | طراحی شده توسط فاطمه سیفی‌پور 💖",
        use_container_width=True
    )
    st.stop()

# اطلاعات کاربر واردشده
user_info = st.session_state.user_info
entered_role = user_info["نقش"]
user_name = user_info["نام کاربر"]
school_name = user_info.get("مدرسه", "")
users_df = st.session_state.users_df  # ✅ بازیابی فایل کاربران برای ادامهٔ پردازش
# بازیابی فایل کاربران از session_state
users_df = st.session_state.users_df
if entered_role == "آموزگار":
    teacher_file = f"data/nomarat_{user_name}.csv"

    if os.path.exists(teacher_file):
        scores_long = pd.read_csv(teacher_file)
        st.success("✅ فایل نمرات قبلی شما بارگذاری شد.")

        with st.expander("📤 به‌روزرسانی نمرات"):
            st.info("اگر می‌خواهید فایل جدید آپلود کنید، از این بخش استفاده کنید.")
            uploaded_file = st.file_uploader("فایل اکسل جدید:", type=["xlsx"])
            if uploaded_file:
                xls = pd.ExcelFile(uploaded_file)
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

                if all_data:
                    scores_long = pd.concat(all_data, ignore_index=True)
                    os.makedirs("data", exist_ok=True)
                    scores_long.to_csv(teacher_file, index=False)
                    st.success("✅ فایل جدید با موفقیت ذخیره شد و داشبورد به‌روزرسانی شد.")
                else:
                    st.error("❌ فایل جدید معتبر نیست یا داده‌ای برای ذخیره‌سازی ندارد.")
    else:
        st.subheader("📤 لطفاً فایل نمرات کلاس خود را آپلود کنید")
        uploaded_file = st.file_uploader("فایل اکسل نمرات:", type=["xlsx"])
        if uploaded_file is None:
            st.warning("لطفاً فایل نمرات را آپلود کنید تا داشبورد فعال شود.")
            st.stop()

        xls = pd.ExcelFile(uploaded_file)
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
        os.makedirs("data", exist_ok=True)
        scores_long.to_csv(teacher_file, index=False)
        st.success("✅ فایل نمرات ذخیره شد.")

elif entered_role == "والد":
    teacher_name = user_info["آموزگار مربوطه"]
    teacher_file = f"data/nomarat_{teacher_name}.csv"
    if not os.path.exists(teacher_file):
        st.error("❌ فایل نمرات آموزگار مربوطه یافت نشد.")
        st.stop()
    scores_long = pd.read_csv(teacher_file)

elif entered_role in ["مدیر", "معاون"]:
    teacher_list = users_df[
        (users_df["نقش"] == "آموزگار") &
        (users_df["مدرسه"] == school_name)
    ]["نام کاربر"].tolist()

    selected_teacher = st.selectbox("👩‍🏫 انتخاب آموزگار مدرسه:", teacher_list)
    teacher_file = f"data/nomarat_{selected_teacher}.csv"
    if not os.path.exists(teacher_file):
        st.error("❌ فایل نمرات این آموزگار یافت نشد.")
        st.stop()
    scores_long = pd.read_csv(teacher_file)

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
def generate_pdf(selected_student, scores_long, status_map, status_colors):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from io import BytesIO

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_name = "Helvetica"  # یا فونت دلخواهت
    c.setFont(font_name, 12)
    c.drawCentredString(
        width / 2,
        40,
        reshape("درس‌بان | همراهی هوشمند برای آموزگاران")
    )

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

)



import pandas as pd
import os
import streamlit as st
from datetime import datetime

NOTES_PATH = "data/yaddasht_olya.xlsx"

def load_notes():
    if not os.path.exists(NOTES_PATH):
        df = pd.DataFrame(columns=[
            "فرستنده", "گیرنده", "نقش فرستنده", "نقش گیرنده",
            "یادداشت", "تاریخ ارسال", "رویت‌شده"
        ])
        df.to_excel(NOTES_PATH, index=False)
    return pd.read_excel(NOTES_PATH)

def save_notes(df):
    df.to_excel(NOTES_PATH, index=False)

def show_notes_for_parent(user_name):
    notes_df = load_notes()
    parent_notes = notes_df[
        (notes_df["گیرنده"] == user_name) &
        (notes_df["نقش گیرنده"] == "والد")
    ]
    st.subheader("📝 یادداشت‌های مدرسه برای شما")
    for idx, row in parent_notes.iterrows():
        st.info(f"📌 از طرف {row['نقش فرستنده']} {row['فرستنده']} در تاریخ {row['تاریخ ارسال']}:\n\n{row['یادداشت']}")
        if not row["رویت‌شده"]:
            if st.button(f"✅ اعلام رویت یادداشت شماره {idx}"):
                notes_df.at[idx, "رویت‌شده"] = True
                save_notes(notes_df)
                st.success("یادداشت رویت شد ✅")
                st.experimental_rerun()

def send_note(from_user, from_role, to_user, to_role, text):
    if not text.strip():
        st.warning("متن یادداشت نمی‌تواند خالی باشد.")
        return
    notes_df = load_notes()
    new_note = {
        "فرستنده": from_user,
        "گیرنده": to_user,
        "نقش فرستنده": from_role,
        "نقش گیرنده": to_role,
        "یادداشت": text.strip(),
        "تاریخ ارسال": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "رویت‌شده": False
    }
    notes_df = pd.concat([notes_df, pd.DataFrame([new_note])], ignore_index=True)
    save_notes(notes_df)

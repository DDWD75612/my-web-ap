import streamlit as st
import sqlite3
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from PIL import Image

# --- 1. הגדרות מייל (תשאיר את מה שעבד לך קודם) ---
SENDER_EMAIL = "D0584624770@gmail.com"  # המייל שלך
SENDER_PASSWORD = "pagb zgdr tipb onyd" # הקוד בן 16 האותיות מגוגל
TARGET_EMAIL = "D0584624770@GMAIL.COM"

# --- 2. פונקציות תשתית (בסיס נתונים ומייל) ---

def init_db():
    """יוצר את בסיס הנתונים אם הוא לא קיים"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS uploads 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER, date TEXT, image_path TEXT)''')
    conn.commit()
    conn.close()

def send_mail(name, age, date, image_data, file_name):
    """שולחת את המייל"""
    msg = EmailMessage()
    msg['Subject'] = f"העלאה חדשה: {name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = TARGET_EMAIL
    msg.set_content(f"פרטים חדשים נשמרו בארכיון:\n\nשם: {name}\nגיל: {age}\nתאריך: {date}")
    msg.add_attachment(image_data, maintype='image', subtype='png', filename=file_name)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

# --- 3. ממשק המשתמש (Streamlit) ---

st.set_page_config(page_title="ארכיון תמונות", layout="wide")
init_db()

st.title("📸 ארכיון תמונות חכם")
st.write("כל מה שתעלה כאן יישמר בטבלה למטה ל.")

# יצירת שתי עמודות: אחת להזנה ואחת להצגת נתונים
col_input, col_display = st.columns([1, 2])

with col_input:
    st.subheader("📝 הזנת נתונים")
    name = st.text_input("שם המצולם")
    age = st.number_input("גיל", min_value=1, max_value=120, value=20)
    uploaded_file = st.file_uploader("בחר תמונה", type=["jpg", "png", "jpeg"])

    if st.button("שמור"):
        if name and uploaded_file:
            try:
                with st.spinner("מעבד נתונים..."):
                    # א. שמירת התמונה בתיקייה מקומית
                    if not os.path.exists("images"):
                        os.makedirs("images")
                    
                    file_bytes = uploaded_file.read()
                    img_path = os.path.join("images", f"{name}_{datetime.now().strftime('%H%M%S')}.png")
                    with open(img_path, "wb") as f:
                        f.write(file_bytes)
                    
                    # ב. שמירה בבסיס הנתונים
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    curr_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO uploads (name, age, date, image_path) VALUES (?, ?, ?, ?)",
                              (name, age, curr_date, img_path))
                    conn.commit()
                    conn.close()
                    
                    # ג. שליחה למייל
                    send_mail(name, age, curr_date, file_bytes, uploaded_file.name)
                    
                st.success(f"הנתונים של {name} נשמרו ונשלחו!")
                st.balloons()
                st.rerun() # רענון כדי להציג בטבלה
            except Exception as e:
                st.error(f"שגיאה: {e}")
        else:
            st.warning("נא למלא את כל הפרטים")

with col_display:
    st.subheader("📋 היסטוריית העלאות")
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM uploads ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    
    if rows:
        for row in rows:
            with st.expander(f"{row[1]} (גיל: {row[2]}) - {row[3]}"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.image(row[4], width=150)
                with c2:
                    st.write(f"**שם:** {row[1]}")
                    st.write(f"**גיל:** {row[2]}")
                    st.write(f"**תאריך העלאה:** {row[3]}")
    else:
        st.info("עדיין אין תמונות בארכיון.")

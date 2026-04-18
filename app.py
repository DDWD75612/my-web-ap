import streamlit as st
import sqlite3
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from streamlit.web.server.websocket_headers import _get_websocket_headers

# --- 1. הגדרות מייל ---
# הקוד מושך את הפרטים מה-Secrets שהגדרת ב-Streamlit Cloud
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "D0584624770@GMAIL.COM")
SENDER_PASSWORD = st.secrets.get("SENDER_PASSWORD", "pagb zgdr tipb onyd")
TARGET_EMAIL = "D0584624770@GMAIL.COM"

# --- 2. פונקציות תשתית ---

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS uploads 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, age INTEGER, date TEXT, 
                  image_path TEXT, device TEXT)''')
    
    try:
        c.execute("SELECT device FROM uploads LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE uploads ADD COLUMN device TEXT")
        
    conn.commit()
    conn.close()

def get_device_info():
    """מזהה מאיזה מכשיר בוצעה ההעלאה"""
    headers = _get_websocket_headers()
    user_agent = headers.get("User-Agent", "מכשיר לא ידוע")
    if "iPhone" in user_agent: return "iPhone"
    if "Android" in user_agent: return "Android"
    if "Windows" in user_agent: return "Windows PC"
    if "Macintosh" in user_agent: return "Mac"
    return "Mobile/Tablet" if "Mobile" in user_agent else "Desktop"

def delete_entry(entry_id, image_path):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM uploads WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
        if os.path.exists(image_path): os.remove(image_path)
        return True
    except Exception as e:
        st.error(f"שגיאה במחיקה: {e}")
        return False

def send_mail(name, age, date, device, image_data, file_name):
    msg = EmailMessage()
    msg['Subject'] = f"📸 העלאה חדשה מ-{device}: {name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = TARGET_EMAIL
    msg.set_content(f"שלום,\n\nהתקבלה העלאה חדשה בארכיון:\n\n👤 שם: {name}\n🎂 גיל: {age}\n📅 תאריך: {date}\n📱 מכשיר: {device}\n\nהקובץ המצורף מצורף להודעה זו.")
    msg.add_attachment(image_data, maintype='image', subtype='png', filename=file_name)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

# --- 3. ממשק המשתמש ---

st.set_page_config(page_title="ארכיון תמונות חכם", layout="wide")
init_db()

st.title("📸 ארכיון תמונות חכם")
st.info(f"הת: {TARGET_EMAIL}")

col_input, col_display = st.columns([1, 2])

with col_input:
    st.subheader("📝 הזנת נתונים")
    name = st.text_input("שם המצולם")
    age = st.number_input("גיל", min_value=1, max_value=120, value=20)
    uploaded_file = st.file_uploader("בחר תמונה", type=["jpg", "png", "jpeg"])

    if st.button("🚀 שמור ול"):
        if name and uploaded_file:
            with st.spinner("מעבד נתונים ול..."):
                device = get_device_info()
                file_bytes = uploaded_file.read()
                
                if not os.path.exists("images"): os.makedirs("images")
                img_path = os.path.join("images", f"{name}_{datetime.now().strftime('%H%M%S')}.png")
                with open(img_path, "wb") as f: f.write(file_bytes)
                
                curr_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("INSERT INTO uploads (name, age, date, image_path, device) VALUES (?, ?, ?, ?, ?)",
                          (name, age, curr_date, img_path, device))
                conn.commit()
                conn.close()
                
                try:
                    send_mail(name, age, curr_date, device, file_bytes, uploaded_file.name)
                    st.success(f"הנתונים נשמרו!  מ-{device}.")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"הנתונים נשמרו בארכיון,ל: {e}")

with col_display:
    st.subheader("📋 היסטוריית העלאות")
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM uploads ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    
    if rows:
        for row in rows:
            device_label = row[5] if row[5] else "לא ידוע"
            with st.expander(f"👤 {row[1]} | 📅 {row[3]} | 📱 {device_label}"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.image(row[4], use_container_width=True)
                with c2:
                    st.write(f"**שם:** {row[1]}")
                    st.write(f"**גיל:** {row[2]}")
                    st.write(f"**הועלה ממכשיר:** {device_label}")
                    if st.button(f"🗑️ מחק רשומה", key=f"del_{row[0]}"):
                        if delete_entry(row[0], row[4]):
                            st.rerun()
    else:
        st.write("הארכיון ריק כרגע.")

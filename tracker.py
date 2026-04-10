import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# Optional AI
USE_AI = False
try:
    from openai import OpenAI
    client = OpenAI(api_key="YOUR_API_KEY")
    USE_AI = True
except:
    USE_AI = False

st.set_page_config(page_title="Productivity Dashboard", layout="wide")

# -------------------------
# SUBJECT CONFIG
# -------------------------
priority_subjects = ["Bioinformatics", "Bioprocess Engineering", "IPR", "Mathematics", "PSM"]
regular_subjects = ["Statistics", "DS & AI", "DSP", "Food Technology"]

# -------------------------
# FILE SETUP
# -------------------------
FILE = "sessions.csv"

def initialize_data():
    data = []

    # Priority → 3 sessions
    for sub in priority_subjects:
        for i in range(1, 4):
            data.append([sub, i, "High", False, "", ""])

    # Regular → 2 sessions
    for sub in regular_subjects:
        for i in range(1, 3):
            data.append([sub, i, "Normal", False, "", ""])

    df = pd.DataFrame(data, columns=[
        "Subject", "Session No", "Priority", "Completed", "Date", "Last Worked"
    ])
    df.to_csv(FILE, index=False)

if not os.path.exists(FILE):
    initialize_data()

df = pd.read_csv(FILE)

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def save():
    df.to_csv(FILE, index=False)

def days_ignored(last_worked):
    if last_worked == "" or pd.isna(last_worked):
        return 999
    return (datetime.today() - pd.to_datetime(last_worked)).days

df["Days Ignored"] = df["Last Worked"].apply(days_ignored)

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Monthly Tracker", "AI Insights"])

# -------------------------
# DASHBOARD
# -------------------------
if page == "Dashboard":
    st.title("📅 TODAY'S PRODUCTIVITY DASHBOARD")

    today = date.today()

    st.subheader("➕ Assign Tasks for Today")
    pending = df[df["Completed"] == False]

    selected = st.multiselect(
        "Select sessions for today",
        pending.index,
        format_func=lambda x: f"{df.loc[x, 'Subject']} (Session {df.loc[x, 'Session No']})"
    )

    if st.button("Assign to Today"):
        for idx in selected:
            df.at[idx, "Date"] = str(today)
        save()
        st.success("Assigned!")

    # Show today's tasks
    st.subheader("🔥 Today's Tasks")
    today_tasks = df[(df["Date"] == str(today)) & (df["Completed"] == False)]

    for idx, row in today_tasks.iterrows():
        col1, col2 = st.columns([4,1])
        col1.write(f"{row['Subject']} - Session {row['Session No']}")
        if col2.button("Done", key=idx):
            df.at[idx, "Completed"] = True
            df.at[idx, "Last Worked"] = str(today)
            save()
            st.rerun()

    # Neglect alerts
    st.subheader("🚨 Neglect Alerts")
    neglect = df[(df["Days Ignored"] >= 3) & (df["Completed"] == False)]

    if not neglect.empty:
        st.warning("You are ignoring these subjects:")
        for _, row in neglect.iterrows():
            st.write(f"{row['Subject']} (Ignored {row['Days Ignored']} days)")
    else:
        st.success("All subjects on track!")

# -------------------------
# MONTHLY TRACKER
# -------------------------
elif page == "Monthly Tracker":
    st.title("📊 Monthly Study Tracker")

    edited_df = st.data_editor(df, num_rows="dynamic")
    df = edited_df
    save()

    completed = df["Completed"].sum()
    total = len(df)

    st.metric("Completion %", f"{(completed/total)*100:.1f}%")
    st.progress(completed / total)

# -------------------------
# AI INSIGHTS
# -------------------------
elif page == "AI Insights":
    st.title("🤖 AI Productivity Insights")

    if not USE_AI:
        st.warning("Add your OpenAI API key in code to enable AI.")
    else:
        if st.button("Generate Insights"):
            summary = df.to_string()

            prompt = f"""
            Analyze this study data:
            {summary}

            Tell:
            1. Which subjects are neglected
            2. What to study next
            3. Any imbalance
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            st.write(response.choices[0].message.content)
# this one had 5 scrollable panels in 5 columns with white outline
import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from streamlit_autorefresh import st_autorefresh

# 🔄 Auto-refresh every 20 seconds
st_autorefresh(interval=20 * 1000, key="refresh")

# 🗂 Load data from Google Sheets
@st.cache_data(ttl=20)
def load_data():
    gc = gspread.service_account(filename='creds.json')
    sheet = gc.open("UT 402 Final").sheet1
    df = get_as_dataframe(sheet)
    df.dropna(how='all', inplace=True)
    df.columns = df.columns.str.strip().str.lower()  # normalize column names
    for col in ['place', 'keywords', 'urgency', 'department']:
        if col not in df.columns:
            df[col] = pd.NA
    return df

df = load_data()

# 🎛 Filter to known departments
known_departments = ["Police", "Fire Department", "Public Works", "Sanitation", "Social Services"]
df = df[df['department'].isin(known_departments)]

# Convert urgency to numeric for sorting
df['urgency'] = pd.to_numeric(df['urgency'], errors='coerce')

st.title("City Incident Dashboard by Department")

# st.markdown("""
# <style>
# [data-testid="column"] > div {
#     max-height: 450px;
#     overflow-y: auto;
#     padding-right: 10px;
# }
# </style>
# """, unsafe_allow_html=True)
st.markdown("""
<style>
[data-testid="column"] > div {
    max-height: 450px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 10px;
    box-shadow: 0 0 5px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)


# Split departments into two rows
row1_departments = known_departments[:3]
row2_departments = known_departments[3:]

# First row (3 columns)
row1_cols = st.columns(len(row1_departments))
for i, department in enumerate(row1_departments):
    dept_df = df[df['department'] == department].sort_values(by='urgency', ascending=False)
    with row1_cols[i].container():
        st.markdown(f"<h3><strong>{department} ({len(dept_df)} incident{'s' if len(dept_df)!=1 else ''})</strong></h3>", unsafe_allow_html=True)
        st.markdown("<div style='max-height: 300px; overflow-y: auto; padding-right: 10px;'>", unsafe_allow_html=True)
        for idx, row in dept_df.iterrows():
            urgency = row['urgency'] if pd.notnull(row['urgency']) else 1
            urgency = max(1, min(10, int(urgency)))
            red = 255
            green = int(255 * (10 - urgency) / 9)
            color = f"#{red:02x}{green:02x}00"
            st.markdown(f"""
                <div style='background-color:{color}; color: #000; font-weight: 500; padding:10px; border-radius:10px; margin-bottom:10px;'>
                    <p><strong>Place:</strong> {row.get('place', 'N/A')}</p>
                    <p><strong>Keywords:</strong> {row.get('keywords', 'N/A')}</p>
                    <p><strong>Message:</strong> {row.get('message', 'N/A')}</p>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Second row (2 columns)
row2_cols = st.columns(len(row2_departments))
for i, department in enumerate(row2_departments):
    dept_df = df[df['department'] == department].sort_values(by='urgency', ascending=False)
    with row2_cols[i].container():
        st.markdown(f"<h3><strong>{department} ({len(dept_df)} incident{'s' if len(dept_df)!=1 else ''})</strong></h3>", unsafe_allow_html=True)
        st.markdown("<div style='max-height: 300px; overflow-y: auto; padding-right: 10px;'>", unsafe_allow_html=True)
        for idx, row in dept_df.iterrows():
            urgency = row['urgency'] if pd.notnull(row['urgency']) else 1
            urgency = max(1, min(10, int(urgency)))
            red = 255
            green = int(255 * (10 - urgency) / 9)
            color = f"#{red:02x}{green:02x}00"
            st.markdown(f"""
                <div style='background-color:{color}; color: #000; font-weight: 500; padding:10px; border-radius:10px; margin-bottom:10px;'>
                    <p><strong>Place:</strong> {row.get('place', 'N/A')}</p>
                    <p><strong>Keywords:</strong> {row.get('keywords', 'N/A')}</p>
                    <p><strong>Message:</strong> {row.get('message', 'N/A')}</p>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


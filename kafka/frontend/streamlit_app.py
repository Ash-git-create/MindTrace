import os
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz
import requests

# --- AUTO REFRESH EVERY 30 SECONDS ---
st_autorefresh(interval=30000, key="datarefresh")

# --- PAGE CONFIG ---
st.set_page_config(page_title="🧠 MindMap - Real-Time Mental Health Dashboard", layout="wide")

# --- SIDEBAR: TIME, WEATHER, FILTERS ---
st.sidebar.title("🧠 MindMap")

# Time Display
now = datetime.now(pytz.timezone("Europe/Berlin"))
st.sidebar.markdown(f"**🕒 {now.strftime('%A, %d %B %Y %H:%M:%S')}**")

# Weather API (Open-Meteo)
def get_weather(city="Berlin"):
    try:
        resp = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true")
        data = resp.json()["current_weather"]
        return f"🌤 {city}: {data['temperature']}°C, {data['weathercode']}"
    except:
        return "🌤 Weather unavailable"

st.sidebar.markdown(get_weather())

# --- FILTERS ---
source_filter = st.sidebar.multiselect("Filter by Source", ["reddit", "news"], default=["reddit", "news"])
sentiment_filter = st.sidebar.multiselect("Sentiment", ["Positive", "Neutral", "Negative"], default=["Positive", "Neutral", "Negative"])

# --- LOAD DATA ---
mongo_uri = os.getenv("MONGO_URI") or st.secrets["MONGO_URI"]
client = MongoClient(mongo_uri)
db = client["mindmap"]
collection = db["sentiment_messages"]

cursor = collection.find({"source": {"$in": source_filter}, "sentiment": {"$in": sentiment_filter}}).sort("timestamp", -1)
data = list(cursor)

df = pd.DataFrame(data)

if df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# --- PREPROCESS ---
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date

# --- TOP: SENTIMENT TREND ---
st.subheader("📈 Sentiment Trend")
trend_df = df.groupby(['date', 'sentiment']).size().unstack().fillna(0)
st.line_chart(trend_df)

# --- MID: SENTIMENT BREAKDOWN ---
st.subheader("📊 Sentiment by Source")
bar_df = df.groupby(['source', 'sentiment']).size().unstack().fillna(0)
st.bar_chart(bar_df)

# --- BOTTOM: LIVE FEED ---
st.subheader("🧾 Live Feed")
for _, row in df.head(20).iterrows():
    with st.expander(f"{row.get('title', '[No Title]')} [{row['sentiment']}] - {row['source'].capitalize()} ({row['timestamp'].strftime('%Y-%m-%d %H:%M')})"):
        st.write(row.get("body") or row.get("text") or "[No Content]")
        if row.get("url"):
            st.markdown(f"[🔗 View Source]({row['url']})")
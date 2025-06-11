import os
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz
import requests
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import altair as alt
from collections import Counter
import re
import openai
from dotenv import load_dotenv
import numpy as np
from PIL import Image

# Set Streamlit page configuration
st.set_page_config(
    page_title="MindTrace - Mental Health Sentiment Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="datarefresh")

# Custom CSS with professional styling
st.markdown("""
    <style>
    :root {
        --primary: #4a6fa5;
        --secondary: #166088;
        --accent: #4fc3f7;
        --positive: #4caf50;
        --negative: #f44336;
        --neutral: #2196f3;
        --background: #f5f7fa;
        --card-bg: #ffffff;
        --text: #333333;
        --text-light: #6c757d;
    }
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    body {
        font-family: 'Inter', sans-serif;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        justify-content: left;
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        padding: 8px 16px;
        font-weight: 500;
        border-radius: 8px 8px 0 0;
        transition: all 0.2s;
        background-color: #f0f2f6;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary);
        color: white;
    }
    
    .card {
        border: none;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: var(--card-bg);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        border: none;
        border-radius: 16px;
        padding: 15px;
        text-align: center;
        background: linear-gradient(135deg, #f5f5f5, #ffffff);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.3s ease, background 0.3s ease, box-shadow 0.3s ease;
        cursor: default;
    }

    .metric-card.total:hover,
    .metric-card.ratio:hover,
    .metric-card.common:hover {
        background: linear-gradient(135deg, #bbdefb, #ffffff);
        transform: translateY(-4px);
    }

    .metric-card.positive:hover {
        background: linear-gradient(135deg, #a5d6a7, #ffffff);
        transform: translateY(-4px);
    }
    
    body {
        background: linear-gradient(160deg, #f5f7fa 0%, #eef2f7 100%) !important;
    }
    
    .chart-container {
        border-left: 4px solid #4fc3f7;
        border-radius: 12px;
    }
    
    .metric-card.negative:hover {
        background: linear-gradient(135deg, #ef9a9a, #ffffff);
        transform: translateY(-4px);
    }

    .metric-title {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 8px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #4a6fa5;
        margin-bottom: 5px;
    }
    
    .metric-change {
        font-size: 12px;
        font-weight: 500;
    }
    
    .positive-change {
        color: var(--positive);
    }
    
    .negative-change {
        color: var(--negative);
    }
    
    .connection-status {
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        font-size: 14px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .connection-status:before {
        content: "•";
        font-size: 24px;
    }
    
    .connected {
        background-color: rgba(46, 125, 50, 0.1);
        color: var(--positive);
    }
    
    .disconnected {
        background-color: rgba(198, 40, 40, 0.1);
        color: var(--negative);
    }
    
    .debug-info {
        font-size: 12px;
        color: var(--text-light);
        margin-top: 5px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .filter-section {
        margin-bottom: 20px;
    }
    
    .filter-label {
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 8px;
        color: var(--text);
    }
    
    .footer {
        font-size: 14px;
        color: var(--text-light);
        text-align: center;
        margin-top: 30px;
        padding-top: 15px;
        border-top: 1px solid #e0e0e0;
    }
    
    .chart-container {
        border: none;
        border-radius: 12px;
        padding: 15px;
        background-color: var(--card-bg);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .feed-item {
        border: none;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        background-color: var(--card-bg);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .feed-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .feed-title {
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 8px;
        color: var(--primary);
    }
    
    .feed-sentiment {
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 8px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .positive {
        background-color: rgba(76, 175, 80, 0.1);
        color: var(--positive);
    }
    
    .neutral {
        background-color: rgba(33, 150, 243, 0.1);
        color: var(--neutral);
    }
    
    .negative {
        background-color: rgba(244, 67, 54, 0.1);
        color: var(--negative);
    }
    
    h1 {
        font-size: 32px !important;
        color: var(--primary) !important;
        margin-bottom: 24px !important;
        font-weight: 700 !important;
    }
    
    h2 {
        font-size: 24px !important;
        color: var(--secondary) !important;
        margin-bottom: 16px !important;
        font-weight: 600 !important;
    }
    
    h3 {
        font-size: 20px !important;
        color: var(--secondary) !important;
        margin-bottom: 12px !important;
        font-weight: 600 !important;
    }
    
    .stMarkdown {
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    
    .center-chart {
        display: flex;
        justify-content: center;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Custom select boxes */
    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        padding: 8px 12px !important;
    }
    
    /* Custom buttons */
    .stButton button {
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .main-header {
        text-align: center;
        margin: 16px 0 40px 0;
    }
    
    .header-container {
        position: relative;
        width: 100%;
        height: 350px;
        overflow: hidden;
        border-radius: 12px;
        margin: 0 0 20px 0;
    }
    
    .header-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
    }
    
    .header-title {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 20px;
        background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 70%, transparent 100%);
        color: white;
        font-size: 36px !important;
        font-weight: 700 !important;
        margin-bottom: 0 !important;
    }
    
    @keyframes bounceIcon {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }

    .bounce {
        animation: bounceIcon 2s infinite ease-in-out;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(74, 111, 165, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(74, 111, 165, 0); }
        100% { box-shadow: 0 0 0 0 rgba(74, 111, 165, 0); }
    }
    
    .pulse {
        animation: pulse 1.5s infinite;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR LAYOUT ---
st.sidebar.markdown("""
    <div style='text-align: center; margin: 0 0 24px 0;'>
        <h1 style='color: var(--primary); font-size: 36px; font-weight: 700;'>MindTrace</h1>
        <p style='color: var(--text-light); font-size: 16px; margin-top: 4px;'>Tracking emotional signals from Reddit and news sources in real-time.</p>
    </div>
""", unsafe_allow_html=True)

# Date, Time, Weather
now = datetime.now(pytz.timezone("Europe/Berlin"))
st.sidebar.markdown(f"""
    <div style='display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px;'>
        <div style='font-size: 16px; color: var(--text-light); display: flex; align-items: center; gap: 8px;'>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 4H5C3.89543 4 3 4.89543 3 6V20C3 21.1046 3.89543 22 5 22H19C20.1046 22 21 21.1046 21 20V6C21 4.89543 20.1046 4 19 4Z" stroke="#6c757d" stroke-width="2"/>
                <path d="M16 2V6" stroke="#6c757d" stroke-width="2" stroke-linecap="round"/>
                <path d="M8 2V6" stroke="#6c757d" stroke-width="2" stroke-linecap="round"/>
                <path d="M3 10H21" stroke="#6c757d" stroke-width="2" stroke-linecap="round"/>
            </svg>
            {now.strftime('%A, %d %B %Y')}
        </div>
        <div style='font-size: 16px; color: var(--text-light); display: flex; align-items: center; gap: 8px;'>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#6c757d" stroke-width="2"/>
                <path d="M12 6V12L16 14" stroke="#6c757d" stroke-width="2" stroke-linecap="round"/>
            </svg>
            {now.strftime('%H:%M:%S')}
        </div>
    </div>
""", unsafe_allow_html=True)

try:
    resp = requests.get("https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true", timeout=5)
    weather = resp.json()["current_weather"]
    weather_icon = "☀️" if weather['weathercode'] in [0, 1] else "⛅" if weather['weathercode'] in [2, 3] else "🌧️" if weather['weathercode'] in [51, 53, 55, 61, 63, 65] else "❄️"
    st.sidebar.markdown(f"""
        <div style='font-size: 16px; color: var(--text-light); display: flex; align-items: center; gap: 8px; margin-bottom: 24px;'>
            {weather_icon}
            {weather['temperature']}°C | Berlin
        </div>
    """, unsafe_allow_html=True)
except Exception as e:
    st.sidebar.markdown("""
        <div style='font-size: 16px; color: var(--text-light); display: flex; align-items: center; gap: 8px; margin-bottom: 24px;'>
            🌐 Weather data unavailable
        </div>
    """, unsafe_allow_html=True)

# Mental health quote
def get_mh_quote():
    quotes = [
        "You are not alone. Support is always closer than you think.",
        "Mental health is not a destination, but a process. It's about how you drive, not where you're going.",
        "Healing takes time, and asking for help is a courageous step.",
        "Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.",
        "It's okay to not be okay. What matters is that you don't give up."
    ]
    return np.random.choice(quotes)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
    <div style='font-size: 16px; font-style: italic; color: var(--text-light); padding: 8px 0;'>
        "{get_mh_quote()}"
    </div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Crisis Support Links
st.sidebar.markdown("<h3 style='font-size: 18px; margin-bottom: 12px;'>Crisis Resources</h3>", unsafe_allow_html=True)

crisis_links = [
    {"name": "Crisis Text Line", "url": "https://www.crisistextline.org/", "icon": "💬"},
    {"name": "WHO Mental Health", "url": "https://www.who.int/health-topics/mental-health", "icon": "🌍"},
    {"name": "NAMI Support", "url": "https://www.nami.org/Home", "icon": "🤝"},
    {"name": "Suicide Prevention", "url": "https://suicidepreventionlifeline.org/", "icon": "🆘"}
]

for link in crisis_links:
    st.sidebar.markdown(f"""
        <div style='margin-bottom: 8px;'>
            <a href="{link['url']}" target="_blank" style='display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--primary);'>
                {link['icon']} {link['name']}
            </a>
        </div>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=30)
def load_data():
    try:
        mongo_uri = st.secrets["MONGO_URI"]
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        
        db = client.get_database("mindmap")
        collection = db["sentiment_messages"]
        
        data = list(collection.find({}))
        df = pd.DataFrame(data)
        
        for col in ['timestamp', 'source', 'sentiment', 'text', 'title', 'url']:
            if col not in df.columns:
                df[col] = None
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            na_mask = df['timestamp'].isna()
            if na_mask.any():
                df.loc[na_mask, 'timestamp'] = pd.to_datetime(
                    df.loc[na_mask, 'timestamp'], 
                    errors='coerce'
                )
            
        st.session_state.connection_status = "connected"
        return df
        
    except Exception as e:
        st.session_state.connection_status = "disconnected"
        st.error(f"Database connection error: {str(e)}")
        return pd.DataFrame()

df = load_data()

# Combine news and gnews sources into a single "news" category
if 'source' in df.columns:
    df['source'] = df['source'].replace({'gnews': 'news'})

# Data preprocessing
try:
    if 'timestamp' in df.columns:
        valid_timestamps = df['timestamp'].notna()
        df.loc[valid_timestamps, 'date'] = df.loc[valid_timestamps, 'timestamp'].dt.date
        df.loc[valid_timestamps, 'hour'] = df.loc[valid_timestamps, 'timestamp'].dt.hour
        df.loc[valid_timestamps, 'day_of_week'] = df.loc[valid_timestamps, 'timestamp'].dt.day_name()
except Exception as e:
    st.error(f"Error processing dates: {str(e)}")
    st.stop()

# Connection status indicator
if st.session_state.get('connection_status', 'disconnected') == 'connected':
    st.sidebar.markdown("""
        <div class='connection-status connected'>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 12.55L12 19.55L19 12.55M12 4.55V18.55" stroke="#2e7d32" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Connected to Database
        </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
        <div class='connection-status disconnected'>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 8V12M12 16H12.01M7.05005 4.92999L4.93005 7.04999M16.96 4.92999L19.08 7.04999M4 12C4 14.1217 4.84288 16.1566 6.34317 17.6569C7.84345 19.1571 9.87824 20 12 20C14.1218 20 16.1566 19.1571 17.6569 17.6569C19.1571 16.1566 20 14.1217 20 12C20 9.87824 19.1571 7.84345 17.6569 6.34317C16.1566 4.84288 14.1218 4 12 4C9.87824 4 7.84345 4.84288 6.34317 6.34317C4.84288 7.84345 4 9.87824 4 12Z" stroke="#c62828" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Database Connection Error
        </div>
    """, unsafe_allow_html=True)

# Data freshness indicator
if not df.empty and 'timestamp' in df.columns:
    last_update = df['timestamp'].max()
    if pd.notna(last_update):
        st.sidebar.markdown(f"""
            <div class='debug-info'>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 8V12L16 14M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="#6c757d" stroke-width="2" stroke-linecap="round"/>
                </svg>
                Last update: {last_update.strftime('%Y-%m-%d %H:%M')}
            </div>
        """, unsafe_allow_html=True)

# --- MAIN PAGE CONTENT ---
# Header image
st.markdown("""
    <div class="header-container">
        <img src="app/static/dashboard.png" class="header-image" />
        <div class="header-title">Mental Health Sentiment Dashboard</div>
    </div>
""", unsafe_allow_html=True)

# Calculate insights
def safe_mode(series, default="N/A"):
    try:
        if not series.empty:
            return series.mode()[0]
        return default
    except:
        return default

top_sentiment = safe_mode(df['sentiment']) if 'sentiment' in df.columns else "N/A"
top_source = safe_mode(df['source']) if 'source' in df.columns else "N/A"
neg_sub = safe_mode(df[(df['sentiment'] == 'Negative') & (df['source'] == 'reddit')]['subreddit']) if all(col in df.columns for col in ['sentiment', 'source', 'subreddit']) else "N/A"

# Sentiment counts
positive_count = df[df['sentiment'] == 'Positive'].shape[0] if 'sentiment' in df.columns else 0
neutral_count = df[df['sentiment'] == 'Neutral'].shape[0] if 'sentiment' in df.columns else 0
negative_count = df[df['sentiment'] == 'Negative'].shape[0] if 'sentiment' in df.columns else 0
total_count = df.shape[0]

# Sentiment percentages
positive_pct = (positive_count / total_count * 100) if total_count > 0 else 0
neutral_pct = (neutral_count / total_count * 100) if total_count > 0 else 0
negative_pct = (negative_count / total_count * 100) if total_count > 0 else 0

# Word frequency analysis
common_word = "N/A"
word_freq = {}
try:
    text_blob = " ".join(df.get('body', pd.Series(dtype=str)).dropna().tolist() + 
                df.get('text', pd.Series(dtype=str)).dropna().tolist())
    words = re.findall(r'\b[a-z]{4,}\b', text_blob.lower())
    stopwords = STOPWORDS.union({"https", "com", "www", "reddit", "also", "get", "one", "like", "just", "know", "people", "think", "really"})
    filtered_words = [w for w in words if w not in stopwords]
    if filtered_words:
        word_freq = Counter(filtered_words)
        common_word = word_freq.most_common(1)[0][0]
except:
    pass

# Positive/Negative ratio
positive = df[df['sentiment'] == 'Positive'].shape[0] if 'sentiment' in df.columns else 0
negative = df[df['sentiment'] == 'Negative'].shape[0] if 'sentiment' in df.columns else 0
pos_neg_ratio = round(positive / negative, 2) if negative > 0 else "∞"

# --- INSIGHT METRICS ---
st.markdown("<h2 style='margin-bottom: 16px;'>Key Metrics</h2>", unsafe_allow_html=True)
metric_cols = st.columns(5)

metrics = [
    {"title": "Total Posts", "value": total_count, "change": None},
    {"title": "Positive Sentiment", "value": f"{positive_count} ({positive_pct:.1f}%)", "change": None},
    {"title": "Negative Sentiment", "value": f"{negative_count} ({negative_pct:.1f}%)", "change": None},
    {"title": "Pos:Neg Ratio", "value": f"{pos_neg_ratio}:1", "change": None},
    {"title": "Common Word", "value": common_word, "change": None}
]

card_classes = ['metric-card total', 'metric-card positive', 'metric-card negative', 'metric-card ratio', 'metric-card common']

for i, metric in enumerate(metrics):
    with metric_cols[i]:
        st.markdown(f"""
            <div class='{card_classes[i]}'>
                <div class='metric-title'>{metric['title']}</div>
                <div class='metric-value'>{metric['value']}</div>
            </div>
        """, unsafe_allow_html=True)

# --- CHARTS ROW 1 ---
st.markdown("<h2 style='margin-bottom: 16px;'>Trends and Sentiment Overview</h2>", unsafe_allow_html=True)
chart_cols = st.columns([2, 1])

# Line Chart - Sentiment Over Time
try:
    if not df.empty and all(col in df for col in ['date', 'sentiment']):
        trend_df = df.groupby(['date', 'sentiment']).size().reset_index(name='count')
        
        with chart_cols[0]:
            st.markdown("<h3 style='font-size: 16px; margin-bottom: 8px;'>Sentiment Over Time</h3>", unsafe_allow_html=True)
            line_chart = alt.Chart(trend_df).mark_line(point=True).encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('count:Q', title='Number of Posts'),
                color=alt.Color('sentiment:N', scale=alt.Scale(
                    domain=['Positive', 'Neutral', 'Negative'],
                    range=['#4caf50', '#2196f3', '#f44336']
                ), title='Sentiment')
            ).properties(height=300)
            st.altair_chart(line_chart, use_container_width=True)
except Exception as e:
    with chart_cols[0]:
        st.error(f"Error generating trend chart: {str(e)}")

# Hourly Activity Heatmap
try:
    if not df.empty and all(col in df for col in ['hour', 'sentiment']):
        hourly_df = df.groupby(['hour', 'sentiment']).size().reset_index(name='count')
        
        with chart_cols[1]:
            st.markdown("<h3 style='font-size: 16px; margin-bottom: 8px;'>Activity by Hour</h3>", unsafe_allow_html=True)
            heatmap = alt.Chart(hourly_df).mark_rect().encode(
                x=alt.X('hour:O', title='Hour of Day'),
                y=alt.Y('sentiment:N', title='Sentiment'),
                color=alt.Color('count:Q', title='Posts', scale=alt.Scale(scheme='blues')),
                tooltip=['hour', 'sentiment', 'count']
            ).properties(height=300)
            st.altair_chart(heatmap, use_container_width=True)
except Exception as e:
    with chart_cols[1]:
        st.error(f"Error generating hourly activity chart: {str(e)}")

# --- CHARTS ROW 2 ---
chart_cols2 = st.columns([2, 2])

# Word Cloud
with chart_cols2[0]:
    st.markdown("<h3 style='font-size: 16px; margin-bottom: 8px;'>Frequent Terms</h3>", unsafe_allow_html=True)
    try:
        if word_freq:
            wordcloud = WordCloud(width=800, 
                                height=400, 
                                background_color='white',
                                colormap='Blues',
                                max_words=50).generate_from_frequencies(word_freq)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        else:
            st.info("No word frequency data available")
    except Exception as e:
        st.error(f"Error generating word cloud: {str(e)}")

# Sentiment by Source
with chart_cols2[1]:
    st.markdown("<h3 style='font-size: 16px; margin-bottom: 8px;'>Sentiment by Source</h3>", unsafe_allow_html=True)
    try:
        if not df.empty and all(col in df for col in ['source', 'sentiment']):
            source_df = df.groupby(['source', 'sentiment']).size().reset_index(name='count')
            
            bar_chart = alt.Chart(source_df).mark_bar().encode(
                x=alt.X('source:N', title='Source'),
                y=alt.Y('count:Q', title='Number of Posts'),
                color=alt.Color('sentiment:N', scale=alt.Scale(
                    domain=['Positive', 'Neutral', 'Negative'],
                    range=['#4caf50', '#2196f3', '#f44336']
                )),
                column=alt.Column('sentiment:N', header=alt.Header(titleOrient='bottom'))
            ).properties(height=250, width=100)
            st.altair_chart(bar_chart)
    except Exception as e:
        st.error(f"Error generating source sentiment chart: {str(e)}")

# --- LIVE FEED SECTION ---
st.markdown("<h2 style='margin-bottom: 16px;'>Recent Items</h2>", unsafe_allow_html=True)

# Get counts for each source type
reddit_count = df[df['source'] == 'reddit'].shape[0] if 'source' in df.columns else 0
news_count = df[df['source'] == 'news'].shape[0] if 'source' in df.columns else 0

# Add sentiment filter dropdown above the feed
sentiment_filter = st.multiselect(
    "Filter by sentiment:",
    options=["Positive", "Neutral", "Negative"],
    default=[],
    key="sentiment_filter"
)

feed_tabs = st.tabs([
    f"Reddit ({reddit_count})", 
    f"News ({news_count})",
    "Sentiment Analysis"
])

# Apply sentiment filter if any selected
if sentiment_filter:
    filtered_df = df[df['sentiment'].isin(sentiment_filter)] if 'sentiment' in df.columns else pd.DataFrame()
else:
    filtered_df = df

# Reddit Feed
with feed_tabs[0]:
    try:
        if 'source' in filtered_df.columns:
            reddit_df = filtered_df[filtered_df['source'] == 'reddit'].sort_values('timestamp', ascending=False).head(10)
        else:
            reddit_df = pd.DataFrame()
            
        if not reddit_df.empty:
            for idx, row in reddit_df.iterrows():
                sentiment_class = row.get('sentiment', '').lower()
                is_new = (datetime.now(pytz.utc) - row['timestamp']).total_seconds() < 3600 if pd.notna(row.get('timestamp')) else False
                
                with st.container():
                    st.markdown(f"<div class='feed-item {'pulse' if is_new else ''}'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='feed-title'>{row.get('title', 'No title')}</div>", unsafe_allow_html=True)
                    
                    if 'sentiment' in row:
                        st.markdown(f"<div class='feed-sentiment {sentiment_class}'>{row['sentiment']}</div>", unsafe_allow_html=True)
                    
                    if 'subreddit' in row:
                        st.markdown(f"<div style='font-size: 12px; color: var(--text-light); margin-bottom: 8px;'>r/{row['subreddit']}</div>", unsafe_allow_html=True)
                    
                    if 'text' in row and pd.notna(row['text']):
                        preview = (row['text'][:200] + '...') if len(row['text']) > 200 else row['text']
                        st.markdown(f"<div style='font-size: 14px; margin-bottom: 8px;'>{preview}</div>", unsafe_allow_html=True)
                    
                    if 'url' in row and pd.notna(row['url']):
                        st.markdown(f"<a href='{row['url']}' target='_blank' style='font-size: 12px; color: var(--primary);'>View on Reddit →</a>", unsafe_allow_html=True)
                    
                    if 'timestamp' in row and pd.notna(row['timestamp']):
                        time_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
                        st.markdown(f"<div style='font-size: 11px; color: var(--text-light); margin-top: 8px;'>{time_str}</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No news articles found with current filters")
    except Exception as e:
        st.error(f"Error displaying news feed: {str(e)}")

# Sentiment Analysis Tab
with feed_tabs[2]:
    st.markdown("<h3 style='font-size: 16px; margin-bottom: 8px;'>Sentiment Insights</h3>", unsafe_allow_html=True)
    
    try:
        if not df.empty and 'sentiment' in df.columns:
            # Sentiment trends by day of week
            if all(col in df.columns for col in ['day_of_week', 'sentiment']):
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_df = df.groupby(['day_of_week', 'sentiment']).size().reset_index(name='count')
                day_df['day_of_week'] = pd.Categorical(day_df['day_of_week'], categories=day_order, ordered=True)
                day_df = day_df.sort_values('day_of_week')
                
                day_chart = alt.Chart(day_df).mark_bar().encode(
                    x=alt.X('day_of_week:N', title='Day of Week'),
                    y=alt.Y('count:Q', title='Number of Posts'),
                    color=alt.Color('sentiment:N', scale=alt.Scale(
                        domain=['Positive', 'Neutral', 'Negative'],
                        range=['#4caf50', '#2196f3', '#f44336']
                    )),
                    column=alt.Column('sentiment:N', header=alt.Header(titleOrient='bottom'))
                ).properties(height=250, width=100)
                st.altair_chart(day_chart)
            
            # Sentiment analysis summary
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<h4 style='font-size: 14px;'>Most Common Positive Phrases</h4>", unsafe_allow_html=True)
                if 'text' in df.columns and 'sentiment' in df.columns:
                    positive_text = " ".join(df[df['sentiment'] == 'Positive']['text'].dropna().tolist())
                    if positive_text:
                        words = re.findall(r'\b[a-z]{4,}\b', positive_text.lower())
                        filtered_words = [w for w in words if w not in STOPWORDS]
                        if filtered_words:
                            word_counts = Counter(filtered_words).most_common(5)
                            for word, count in word_counts:
                                st.markdown(f"- {word.capitalize()} ({count})")
                        else:
                            st.info("No positive text data available")
                    else:
                        st.info("No positive text data available")
            
            with col2:
                st.markdown("<h4 style='font-size: 14px;'>Most Common Negative Phrases</h4>", unsafe_allow_html=True)
                if 'text' in df.columns and 'sentiment' in df.columns:
                    negative_text = " ".join(df[df['sentiment'] == 'Negative']['text'].dropna().tolist())
                    if negative_text:
                        words = re.findall(r'\b[a-z]{4,}\b', negative_text.lower())
                        filtered_words = [w for w in words if w not in STOPWORDS]
                        if filtered_words:
                            word_counts = Counter(filtered_words).most_common(5)
                            for word, count in word_counts:
                                st.markdown(f"- {word.capitalize()} ({count})")
                        else:
                            st.info("No negative text data available")
                    else:
                        st.info("No negative text data available")
            
            # GPT-4 Analysis (if API key is available)
            if openai.api_key and st.button("Generate AI Insights Summary"):
                with st.spinner("Generating insights with AI..."):
                    try:
                        # Prepare data for GPT
                        summary_data = {
                            "total_posts": total_count,
                            "positive_posts": positive_count,
                            "negative_posts": negative_count,
                            "neutral_posts": neutral_count,
                            "common_words": word_freq.most_common(10) if word_freq else [],
                            "top_sources": df['source'].value_counts().head(3).to_dict() if 'source' in df.columns else {}
                        }
                        
                        prompt = f"""
                        Analyze this mental health sentiment data and provide 3-5 key insights in bullet points:
                        {summary_data}
                        
                        Focus on:
                        - Overall sentiment trends
                        - Notable patterns in positive/negative content
                        - Any concerning findings
                        - Recommendations for mental health professionals
                        
                        Write in clear, concise professional language.
                        """
                        
                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are a mental health data analyst. Provide clear insights from sentiment data."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        st.markdown("#### AI-Generated Insights")
                        st.write(response.choices[0].message['content'])
                    except Exception as e:
                        st.error(f"Error generating AI insights: {str(e)}")
        else:
            st.info("No sentiment data available for analysis")
    except Exception as e:
        st.error(f"Error in sentiment analysis: {str(e)}")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
    <div class='footer'>
        <div style='display: flex; justify-content: center; gap: 16px; margin-bottom: 8px;'>
            <a href='https://github.com/Ash-git-create/MindTrace/' target='_blank' style='color: var(--text-light); text-decoration: none;'>GitHub</a>
        </div>
        <div>MindTrace Dashboard</div>
    </div>
""", unsafe_allow_html=True)
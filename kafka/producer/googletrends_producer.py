import time
import json
from datetime import datetime
from pytrends.request import TrendReq
from dotenv import load_dotenv
import os
import sys

# Kafka config path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')))
from kafka_config import get_kafka_producer

# Load environment variables
load_dotenv()

# Initialize Kafka producer
producer = get_kafka_producer()
TOPIC = "mindmap.trends"

# Keywords to track
KEYWORDS = ["mental health", "anxiety", "depression", "therapy"]

# Initialize pytrends
pytrends = TrendReq(hl='en-US', tz=360)

def produce_trends():
    try:
        pytrends.build_payload(KEYWORDS, cat=0, timeframe='now 1-H', geo='', gprop='')
        data = pytrends.interest_over_time()
    except Exception as e:
        print("❌ Error fetching Google Trends:", e)
        return

    if data.empty:
        print("⚠️ No trend data available.")
        return

    for timestamp, row in data.iterrows():
        if row.get("isPartial", False):
            continue  # skip incomplete data

        record = {
            "source": "google_trends",
            "timestamp": timestamp.isoformat(),
            "data": {kw: int(row[kw]) for kw in KEYWORDS}
        }

        producer.send(TOPIC, record)
        print("✅ Produced:", record)
        time.sleep(0.2)

if __name__ == "__main__":
    while True:
        produce_trends()
        time.sleep(300)  # wait 5 minutes before polling again

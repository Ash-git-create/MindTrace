import os
import sys
import requests
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from newspaper import Article

# Add kafka/config to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')))
from kafka_config import get_kafka_producer

# Load environment variables
load_dotenv()

# Constants
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
TOPIC = "mindmap.raw"
KEYWORDS = [
    "mental health", "anxiety", "depression", "stress", "PTSD",
    "panic attack", "bipolar disorder", "trauma", "emotional support",
    "mental illness", "self harm", "burnout", "therapy", "counseling",
    "psychologist", "suicide prevention", "crisis helpline", "loneliness",
    "grief", "wellbeing"
]
# Initialize Kafka producer
producer = get_kafka_producer()

def hash_url(url: str) -> str:
    """Generate a unique hash for the URL to use as article_id."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def produce_news_articles():
    url = f"https://newsapi.org/v2/everything?q={'%20OR%20'.join(KEYWORDS)}&language=en&pageSize=20&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json()

    for article in data.get("articles", []):
        article_url = article.get("url")
        full_text = ""
        title = ""

        try:
            a = Article(article_url)
            a.download()
            a.parse()
            full_text = a.text
            title = a.title
        except Exception as e:
            full_text = article.get("description", "") or article.get("content", "")
            title = article.get("title", "")

        if not full_text:
            print(f"⚠️ Skipping empty article: {article_url}")
            continue

        message = {
            "source": "news",
            "article_id": hash_url(article_url),  # UNIQUE ID
            "title": title,
            "text": full_text.strip(),
            "timestamp": article.get("publishedAt"),
            "url": article_url
        }

        producer.send(TOPIC, message)
        print("✅ Produced:", message)
        time.sleep(0.5)

if __name__ == "__main__":
    produce_news_articles()
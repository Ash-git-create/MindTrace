import os
import sys
import requests
import time
import hashlib
from dotenv import load_dotenv
from newspaper import Article

# Add kafka/config to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')))
from kafka_config import get_kafka_producer

# Load environment variables
load_dotenv()

# Constants
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
TOPIC = "mindmap.raw"
KEYWORDS = ["mental health", "anxiety", "depression", "stress"]

# Initialize Kafka producer
producer = get_kafka_producer()

def hash_url(url: str) -> str:
    """Generate a unique hash for the URL to use as article_id."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def produce_gnews_articles():
    if not GNEWS_API_KEY:
        print("❌ GNEWS_API_KEY not found in environment.")
        return

    query = " OR ".join(KEYWORDS)
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=10&token={GNEWS_API_KEY}"

    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        data = response.json()
    except Exception as e:
        print("❌ Request failed:", e)
        return

    if "articles" not in data:
        print("❌ No articles found in GNews response:", data)
        return

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
            print(f"⚠️ Newspaper3k failed for {article_url}:", e)
            full_text = article.get("description", "") or article.get("content", "")
            title = article.get("title", "")

        if not full_text:
            print(f"⚠️ Skipping empty article: {article_url}")
            continue

        message = {
            "source": "gnews",
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
    produce_gnews_articles()
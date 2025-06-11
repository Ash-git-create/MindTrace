import os
import json
import time
import openai
import hashlib
from kafka import KafkaConsumer
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI")

# MongoDB connection
client = MongoClient(mongo_uri)
db = client["mindmap"]
collection = db["sentiment_messages"]

# Create unique index on article_id if not exists
collection.create_index("article_id", unique=True)

# Kafka setup
consumer = KafkaConsumer(
    "mindmap.raw",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="sentiment-consumer-group",
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

def get_article_id(item):
    key = item.get("url") or (item.get("title", "") + item.get("timestamp", ""))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def classify_sentiment(text):
    try:
        prompt = f"Classify the sentiment of this mental health post as Positive, Neutral, or Negative:\n\n{text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("OpenAI error:", e)
        return "Unknown"

print("🧠 GPT Sentiment Consumer started...")

for message in consumer:
    item = message.value

    try:
        item["article_id"] = get_article_id(item)

        if collection.count_documents({"article_id": item["article_id"]}, limit=1):
            print("🔁 Skipping duplicate:", item["article_id"])
            continue

        sentiment = classify_sentiment(item["text"])
        item["sentiment"] = sentiment

        collection.insert_one(item)
        print("✅ Inserted:", item["article_id"])
    except Exception as e:
        print("❌ Error:", e)

    time.sleep(1)
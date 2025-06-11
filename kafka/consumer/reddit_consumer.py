from kafka import KafkaConsumer
import json

TOPIC = "mindmap.raw"
BOOTSTRAP_SERVERS = ["localhost:9092"]

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="reddit-consumer-group",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

print("🔍 Reddit Consumer started...")

for message in consumer:
    item = message.value
    if item.get("source") == "reddit":
        print("\n--- Reddit Post ---")
        print(f"Subreddit: {item.get('subreddit', '[N/A]')}")
        print(f"Title: {item.get('text', '[No title]')}")
        print(f"Timestamp: {item.get('timestamp', '[No timestamp]')}")
        print(f"URL: {item.get('url', '[No URL]')}")
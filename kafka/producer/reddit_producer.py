import praw
import os
import sys
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Load config directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')))
from kafka_config import get_kafka_producer

# Load .env variables
load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

# Full user-authenticated Reddit client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD
)

# Confirm authentication
print("Logged in as:", reddit.user.me())
print("Auth success:", not reddit.read_only)

# Kafka config
TOPIC = "mindmap.raw"
producer = get_kafka_producer()

# Target mental health subreddits
SUBREDDITS = [
    "mentalhealth", "depression", "Anxiety", "SuicideWatch",
    "BPD", "ADHD", "CPTSD", "DecidingToBeBetter",
    "socialanxiety", "MentalHealthUK", "offmychest", "selfharm", "KindVoice"
]
def hash_post(title, created_utc) -> str:
    """Generate a hash from post title and timestamp."""
    raw = f"{title}_{created_utc}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def produce_reddit_posts():
    posts = []

    # Collect top posts from each subreddit
    for sub in SUBREDDITS:
        subreddit = reddit.subreddit(sub)
        for post in subreddit.top(limit=5, time_filter="day"):
            posts.append({
                "subreddit": sub,
                "title": post.title,
                "score": post.score,
                "url": post.url,
                "created_utc": post.created_utc,
                "text": post.selftext.strip()
            })

    # Select global top 10 by score
    top_today = sorted(posts, key=lambda x: x["score"], reverse=True)[:10]

    for post in top_today:
        article_id = hash_post(post["title"], post["created_utc"])

        message = {
            "source": "reddit",
            "article_id": article_id,
            "title": post["title"].strip(),
            "text": post.get("text", "").strip(),
            "timestamp": datetime.utcfromtimestamp(post["created_utc"]).isoformat(),
            "subreddit": post["subreddit"],
            "url": post["url"]
        }

        producer.send(TOPIC, message)
        print("✅ Produced:", message)
        time.sleep(0.5)

if __name__ == "__main__":
    produce_reddit_posts()
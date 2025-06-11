import os
import json
from kafka import KafkaProducer

def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers='localhost:9092',
        api_version=(3, 5),  # Match Kafka version 7.5.0 = Kafka 3.5.0
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

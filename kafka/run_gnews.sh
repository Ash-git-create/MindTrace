#!/bin/bash
cd /home/mindmap/kafka/producer
/usr/bin/python3 gnewsapi_producer.py >> /home/mindmap/logs/gnews.log 2>&1

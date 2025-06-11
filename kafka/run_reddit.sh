#!/bin/bash
cd /home/mindmap/kafka/producer
/usr/bin/python3 reddit_producer.py >> /home/mindmap/logs/reddit.log 2>&1


#!/bin/bash
cd /home/mindmap/kafka/producer
/usr/bin/python3 newsapi_producer.py >> /home/mindmap/logs/newsapi.log 2>&1


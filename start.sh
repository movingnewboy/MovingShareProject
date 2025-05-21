#!/bin/sh
gunicorn app:app --bind 0.0.0.0:8080 &
python3 /app/bot.py

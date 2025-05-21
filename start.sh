#!/bin/sh
gunicorn app:app &
python3 /app/bot.py

#!/bin/sh
gunicorn app:app &
python3 bot.py

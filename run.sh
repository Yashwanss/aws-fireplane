#!/bin/bash
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt
echo "Starting AWS Fireplane..."
python3 run.py

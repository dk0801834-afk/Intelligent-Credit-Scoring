#!/usr/bin/env bash
# Convenience launcher for the Intelligent Credit Scoring app.
set -e
cd "$(dirname "$0")"
pip install -r requirements.txt
streamlit run app.py

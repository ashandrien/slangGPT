#!/usr/bin/env bash
# Simple helper to install spaCy model used by the backend
python3 -m pip install -r requirements.txt
python3 -m spacy download en_core_web_sm

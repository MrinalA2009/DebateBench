#!/bin/bash
# Script to run the DebateBench backend

source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8001


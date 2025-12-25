#!/bin/bash
# Script to run the DebateBench backend

cd backend
uvicorn app.main:app --reload --port 8001


#!/bin/bash
# Build script for Railway — builds frontend and copies to backend/static/
set -e

echo "=== Building frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Copying frontend build to backend/static/ ==="
rm -rf backend/static
cp -r frontend/dist backend/static

echo "=== Installing backend dependencies ==="
cd backend
pip install -r requirements.txt

echo "=== Build complete ==="

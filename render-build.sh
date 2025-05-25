#!/bin/bash

set -e  # Stop on error

# =============
# Install Chrome
# =============
CHROME_VERSION="124.0.6367.91"
CHROME_ZIP="chrome-linux64.zip"
CHROME_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/ ${CHROME_VERSION}.0/linux64/${CHROME_ZIP}"

echo "📥 Downloading Chrome..."
wget -q $CHROME_URL
unzip $CHROME_ZIP

# Rename chrome folder for easier access
mv chrome-linux64 chrome

# ================
# Install ChromeDriver
# ================

CHROMEDRIVER_ZIP="chromedriver-linux64.zip"
CHROMEDRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/ ${CHROME_VERSION}.0/linux64/${CHROMEDRIVER_ZIP}"

echo "📥 Downloading ChromeDriver..."
wget -q $CHROMEDRIVER_URL
unzip $CHROMEDRIVER_ZIP

# Rename chromedriver binary folder
mv chromedriver-linux64 chromedriver

# Make chromedriver executable
chmod +x chromedriver/chromedriver

# ================
# Set Environment Variables
# ================

export CHROME_BINARY=$(pwd)/chrome/chrome
export CHROMEDRIVER_PATH=$(pwd)/chromedriver/chromedriver
export PATH=$PATH:$CHROMEDRIVER_PATH

# ================
# Install Python Dependencies
# ================

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete!"

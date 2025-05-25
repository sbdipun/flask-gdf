#!/bin/bash

# =============
# Install Chrome
# =============
CHROME_VERSION="124.0.6367.91"
CHROME_DEB="google-chrome-stable_$CHROME_VERSION-1_amd64.deb"

echo "📥 Downloading Chrome..."
wget -q https://dl.google.com/linux/direct/ $CHROME_DEB
echo "📦 Installing Chrome..."
sudo apt-get update && sudo apt-get install -y ./$CHROME_DEB --no-install-recommends

# ================
# Install ChromeDriver
# ================
CHROMEDRIVER_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1)
CHROMEDRIVER_ZIP="chromedriver-linux64.zip"

echo "📥 Downloading ChromeDriver $CHROMEDRIVER_VERSION..."
wget -q https://storage.googleapis.com/chrome-for-testing-public/ $CHROMEDRIVER_VERSION/linux64/$CHROMEDRIVER_ZIP
unzip $CHROMEDRIVER_ZIP
chmod +x chromedriver

# Move to bin so it's accessible
sudo mv chromedriver /usr/local/bin/

echo "✅ Setup complete!"

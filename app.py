import time
import tempfile
import os
import json
import re
from flask import Flask, request, jsonify
from seleniumbase import Driver
import asyncio
import aiohttp

app = Flask(__name__)

# ===== GLOBAL CACHE FOR PHPSESSID =====
SESSION_CACHE = {
    "session_id": None,
    "expires_at": 0
}

# ===== UTILITY FUNCTIONS =====

def extract_google_drive_file_id(gdrive_link):
    patterns = [
        r'/d/([a-zA-Z0-9_-]+)',       # https://drive.google.com/file/d/ <id>
        r'id=([a-zA-Z0-9_-]+)',        # https://drive.google.com/uc?id= <id> or /open?id=<id>
    ]
    for pattern in patterns:
        match = re.search(pattern, gdrive_link)
        if match:
            return match.group(1)
    return None

def get_size(size):
    if size is None:
        return "Unknown"

    if isinstance(size, str):
        try:
            size = float(size)
        except ValueError:
            raise ValueError("Error 403")

    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    while size > 1024 and index < len(suffixes) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f} {suffixes[index]}"

# ===== LOGIN TO GET PHPSESSID =====

def get_phpsessionid(email, password):
    print("🔐 Starting login process...")

    # Only one session at a time
    if SESSION_CACHE["session_id"] and SESSION_CACHE["expires_at"] > time.time():
        print("✅ Reusing cached PHPSESSID")
        return SESSION_CACHE["session_id"]

    print("🔄 Logging in to refresh PHPSESSID...")

    driver = Driver(
        browser="chrome",
        headless=True,
        chromium_arg=[
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--incognito",
            "--disable-automation"
        ]
    )

    try:
        # Open login page
        driver.get("https://new7.gdflix.dad/login")
        time.sleep(2)

        # Fill credentials
        driver.type("[name='email']", email)
        driver.type("[name='password']", password)
        time.sleep(1)

        # Wait for reCAPTCHA iframe
        print("⏳ Waiting for reCAPTCHA...")
        time.sleep(3)

        recaptcha_iframe = driver.find_element("xpath", '//iframe[contains(@src, "recaptcha")]')
        driver.switch_to.frame(recaptcha_iframe)
        driver.click('//div[@class="recaptcha-checkbox-border"]')
        driver.switch_to.default_content()
        time.sleep(2)

        # Submit form
        driver.click("button[type='submit']")
        time.sleep(5)

        # Get cookies and extract PHPSESSID
        cookies = driver.get_cookies()
        phpsessionid = next((cookie['value'] for cookie in cookies if cookie['name'] == 'PHPSESSID'), None)

        if not phpsessionid:
            raise Exception("PHPSESSID not found in cookies")

        print("✅ PHPSESSID:", phpsessionid)

        # Cache session for 24 hours
        SESSION_CACHE.update({
            "session_id": phpsessionid,
            "expires_at": time.time() + 86400  # 24 hours
        })

        return phpsessionid

    finally:
        print("🛑 Closing browser...")
        try:
            driver.quit()
        except Exception as e:
            print("⚠️ Error closing driver:", str(e))

# ===== SHARE FILE USING aiohttp =====

async def share_file(session_id, file_id):
    url = "https://new7.gdflix.dad/share"
    payload = {
        "action": "share",
        "id": file_id
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36",
        "Cookie": f"PHPSESSID={session_id}; MD=Ym9sTzdPYzlhS0xmaExxR0c2c2hoaVQycENzeGdxczR6N09GL2toSDZyOWwvNTduZnVjaXNmUXNCcnROVFE4MWJBWXRPeW16aDBZaHUrVFcwbHpKd1E9PQ%3D%3D; _token=UGRsRzdkNm00MGhFTC9xWUZzSGpaQ3pVcFhyYXlBb0xLVWZrdXgvcFlWWVNUeWdsYVZZMWRicnBuenppSk1iYUFxYXY1VnRVc0w0eHVtSjJNbHFnQlE9PQ%3D%3D"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers) as response:
            print("Status Code:", response.status)

            raw_text = await response.text()
            try:
                response_data = json.loads(raw_text)

                name = response_data.get("name")
                size = response_data.get("size")
                key = response_data.get("key")

                formatted_size = get_size(size)
                final_url = f"https://gdlink.dev/file/{key}"

                result = {
                    "name": name,
                    "size": formatted_size,
                    "url": final_url
                }

                return result

            except json.JSONDecodeError:
                print("❌ Failed to parse JSON:", raw_text)
                return None

# ===== FLASK ENDPOINT =====

@app.route('/gdrive', methods=['GET'])
def generate_link():
    gdrive_link = request.args.get('url')

    if not gdrive_link:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    # Extract file ID
    file_id = extract_google_drive_file_id(gdrive_link)
    if not file_id:
        return jsonify({"error": "Invalid Google Drive link"}), 400

    # Hardcoded credentials
    EMAIL = "cinehub4u@gmail.com"
    PASSWORD = "Daddy@9090"

    # Get session ID from cache or refresh
    session_id = get_phpsessionid(EMAIL, PASSWORD)

    # Run async function inside Flask
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(share_file(session_id, file_id))

    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Failed to generate link"}), 500

# ===== RUNNER =====

if __name__ == '__main__':
    app.run(debug=False)

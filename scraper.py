import os
import requests
import time
import csv
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- PROFESSIONAL CONFIGURATION ---
# We use the ASIN-based approach for maximum stability
ASIN_LIST = {
    "Logitech_G305": "B07CMS5Q6P",
    "Redragon_K552": "B016MAK38U"  # Your new active keyboard link
}

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
CSV_FILE = "price_history.csv"

# Identity Rotation (Stealth)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def save_to_csv(name, price):
    """Logs data into a persistent history file."""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Product", "Price"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, price])

def check_product(page, name, asin):
    url = f"https://www.amazon.com/dp/{asin}"
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"🔍 [{name}] Attempt {attempt + 1}...")
        try:
            # Random delay + Referer to look like a human visitor
            page.goto(url, wait_until="domcontentloaded", timeout=60000, referer="https://www.google.com/")
            time.sleep(random.randint(4, 7))

            # Block Detection (Looking for the 'Dog' or Captcha)
            if "captcha" in page.content().lower() or not page.query_selector(".a-price"):
                print(f"⚠️ Blocked/Dog page on attempt {attempt + 1}. Retrying...")
                time.sleep(random.randint(10, 20))
                continue

            # Try the standard offscreen price first
            price_el = page.query_selector(".a-price .a-offscreen")
            price_str = ""
            
            if price_el:
                price_str = price_el.inner_text().strip()
            
            # FALLBACK: If the first one is empty, try the 'whole' and 'fraction' parts
            if not price_str or "$" not in price_str:
                whole = page.query_selector(".a-price-whole")
                fraction = page.query_selector(".a-price-fraction")
                if whole and fraction:
                    price_str = f"{whole.inner_text()}{fraction.inner_text()}"
            
            # Clean the string (remove $, commas, and newlines)
            clean_price = price_str.replace('$', '').replace(',', '').replace('\n', '').strip()
            
            if not clean_price:
                raise ValueError("Price string is empty after extraction")

            new_price = float(clean_price)

        except Exception as e:
            print(f"❌ Error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                page.screenshot(path=f"error_{name}.png")

def run():
    print("🚀 Initializing Professional Scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Creating a 'Human' context
        context = browser.new_context(user_agent=random.choice(USER_AGENTS), viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # Human entry-point
        page.goto("https://www.amazon.com", wait_until="domcontentloaded")
        time.sleep(random.randint(2, 4))
        
        for name, asin in ASIN_LIST.items():
            check_product(page, name, asin)
            time.sleep(random.randint(5, 10)) # Wait between products
            
        browser.close()
    print("✅ All products checked.")

if __name__ == "__main__":
    run()
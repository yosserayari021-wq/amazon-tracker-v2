import os
import requests
from playwright.sync_api import sync_playwright

# The Logitech Mouse
PRODUCT_URL = "https://www.amazon.com/dp/B07CMS5Q6P"
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

def run():
    with sync_playwright() as p:
        # Launching a standard browser
        browser = p.chromium.launch(headless=True)
        
        # We still use a User-Agent so we don't identify as 'HeadlessChrome'
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Opening: {PRODUCT_URL}")
        page.goto(PRODUCT_URL, wait_until="load")
        
        try:
            # Wait for the price whole number
            page.wait_for_selector(".a-price-whole", timeout=10000)
            
            price_whole = page.query_selector(".a-price-whole").inner_text().strip().replace('\n', '')
            price_fraction = page.query_selector(".a-price-fraction").inner_text().strip()
            
            full_price = f"${price_whole}.{price_fraction}"
            print(f"Found Price: {full_price}")

            if WEBHOOK_URL:
                requests.post(WEBHOOK_URL, json={"content": f"Amazon Alert: {full_price}"})
                
        except Exception as e:
            print("Could not find price. Amazon might be blocking this IP.")
            page.screenshot(path="amazon_result.png")
            
        browser.close()

if __name__ == "__main__":
    run()
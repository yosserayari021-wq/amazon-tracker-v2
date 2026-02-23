import os
import requests
from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://www.amazon.com/dp/B07CMS5Q6P"
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PRICE_FILE = "last_price.txt"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Checking Amazon for: {PRODUCT_URL}")
        
        try:
            page.goto(PRODUCT_URL, wait_until="domcontentloaded", timeout=60000)
            
            page.wait_for_selector(".a-price-whole", timeout=15000)
            
            raw_whole = page.query_selector(".a-price-whole").inner_text()
            price_whole = raw_whole.strip().replace('.', '').replace(',', '').replace('\n', '')
            
            raw_fraction = page.query_selector(".a-price-fraction").inner_text()
            price_fraction = raw_fraction.strip().replace('.', '')
            
            new_price = float(f"{price_whole}.{price_fraction}")
            print(f"Current Price Found: ${new_price}")

            old_price = None
            if os.path.exists(PRICE_FILE):
                with open(PRICE_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        old_price = float(content)

            print(f"Previous Price: ${old_price}")

            if old_price is None or new_price < old_price:
                status = "📉 PRICE DROP!" if old_price else "🚀 First Run - Tracking Started"
                message = f"{status}\nPrice: ${new_price}\nLink: {PRODUCT_URL}"
                
                print(f"Sending alert: {status}")
                if WEBHOOK_URL:
                    requests.post(WEBHOOK_URL, json={"content": message})
                
                with open(PRICE_FILE, "w") as f:
                    f.write(str(new_price))
            else:
                print("No price drop detected. Keeping quiet.")

        except Exception as e:
            print(f"Error during scraping: {e}")
            page.screenshot(path="amazon_result.png")
            raise
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()
from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to https://voterlist.election.gov.np/ ...")
        page.goto("https://voterlist.election.gov.np/")
        
        # Select Bagmati Province (Value 3)
        print("Selecting Bagmati Province...")
        page.select_option("select#state", value="3")
        
        # Wait for network idle or a specific timeout to allow district to load
        # Since we don't know the exact API call, we'll wait a bit or wait for the district dropdown to have options > 1
        page.wait_for_timeout(2000) 
        
        # Get district options
        district_select = page.query_selector("select#district")
        options = district_select.query_selector_all("option")
        
        print("District Options for Bagmati:")
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.inner_text()
            print(f"  Value: {val}, Text: {text}")
            if "ललितपुर" in text or "Lalitpur" in text:
                print(f"FOUND LALITPUR! Value: {val}")

        browser.close()

if __name__ == "__main__":
    run()

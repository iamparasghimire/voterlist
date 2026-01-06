from playwright.sync_api import sync_playwright
import pandas as pd
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Headless False to see what happens
        page = browser.new_page()
        
        print("Navigating to https://voterlist.election.gov.np/ ...")
        page.goto("https://voterlist.election.gov.np/")
        
        # 1. Select State: Bagmati (3)
        print("Selecting State 3...")
        page.select_option("select#state", value="3")
        page.wait_for_timeout(1000) # Wait for district to load
        
        # 2. Select District: Lalitpur (28)
        print("Selecting District 28 (Lalitpur)...")
        page.select_option("select#district", value="28")
        page.wait_for_timeout(1000) # Wait for VDC/Mun to load
        
        # 3. Select first Municipality
        mun_select = page.query_selector("select#vdc_mun")
        mun_options = mun_select.query_selector_all("option")
        # Skip the first option (placeholder)
        if len(mun_options) > 1:
            first_mun_val = mun_options[1].get_attribute("value")
            first_mun_text = mun_options[1].inner_text()
            print(f"Selecting Municipality: {first_mun_text} ({first_mun_val})")
            page.select_option("select#vdc_mun", value=first_mun_val)
            page.wait_for_timeout(1000)
        else:
            print("No municipalities found!")
            return

        # 4. Select first Ward
        ward_select = page.query_selector("select#ward")
        ward_options = ward_select.query_selector_all("option")
        if len(ward_options) > 1:
            first_ward_val = ward_options[1].get_attribute("value")
            first_ward_text = ward_options[1].inner_text()
            print(f"Selecting Ward: {first_ward_text} ({first_ward_val})")
            page.select_option("select#ward", value=first_ward_val)
            page.wait_for_timeout(1000)
        else:
            print("No wards found!")
            return

        # 5. Select first Polling Centre
        center_select = page.query_selector("select#reg_centre")
        center_options = center_select.query_selector_all("option")
        if len(center_options) > 1:
            first_center_val = center_options[1].get_attribute("value")
            first_center_text = center_options[1].inner_text()
            print(f"Selecting Polling Centre: {first_center_text} ({first_center_val})")
            page.select_option("select#reg_centre", value=first_center_val)
        else:
            print("No polling centres found!")
            return
            
        # 6. Click Submit
        print("Clicking Submit...")
        # Look for the submit button. Based on previous fetch, it might be a button or input type=submit
        # Let's try to find it by text or type
        submit_btn = page.query_selector("button.btn-success") # Common class for submit buttons
        if not submit_btn:
             submit_btn = page.query_selector("input[type='submit']")
        
        if submit_btn:
            submit_btn.click()
            print("Submit clicked. Waiting for data...")
            
            # Wait for table to appear
            try:
                page.wait_for_selector("table", timeout=10000)
                print("Table found!")
                
                # Extract headers
                headers = [th.inner_text() for th in page.query_selector_all("thead th")]
                print(f"Headers: {headers}")
                
                # Extract rows
                rows = page.query_selector_all("tbody tr")
                print(f"Found {len(rows)} rows of data.")
                
                data = []
                for row in rows:
                    cells = [td.inner_text() for td in row.query_selector_all("td")]
                    data.append(cells)
                
                if data:
                    print("Sample data (first row):", data[0])
                    df = pd.DataFrame(data, columns=headers)
                    print(df.head())
                
            except Exception as e:
                print(f"Error waiting for table: {e}")
                # Take screenshot to debug
                page.screenshot(path="error_screenshot.png")
        else:
            print("Submit button not found!")
            page.screenshot(path="no_submit_btn.png")

        browser.close()

if __name__ == "__main__":
    run()

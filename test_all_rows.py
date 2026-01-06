from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Navigating to https://voterlist.election.gov.np/ ...")
        page.goto("https://voterlist.election.gov.np/")
        
        # Select State 3, District 28 (Lalitpur)
        page.select_option("select#state", value="3")
        page.wait_for_timeout(1000)
        page.select_option("select#district", value="28")
        page.wait_for_timeout(1000)
        
        # Select first available Mun, Ward, Center
        page.select_option("select#vdc_mun", index=1)
        page.wait_for_timeout(1000)
        page.select_option("select#ward", index=1)
        page.wait_for_timeout(1000)
        page.select_option("select#reg_centre", index=1)
        
        # Submit
        submit_btn = page.query_selector("button.btn-success")
        if not submit_btn:
            submit_btn = page.query_selector("input[type='submit']")
        submit_btn.click()
        
        page.wait_for_selector("table#tbl_data", timeout=10000)
        print("Table loaded.")
        
        # Try to set the length to -1 (All) via JavaScript
        print("Attempting to set table length to -1 (All)...")
        
        # Check if the select exists
        select_exists = page.evaluate("() => !!document.querySelector('select[name=\"tbl_data_length\"]')")
        if select_exists:
            # Add an option for -1 if it doesn't exist and select it
            page.evaluate("""() => {
                const sel = document.querySelector('select[name="tbl_data_length"]');
                const opt = document.createElement('option');
                opt.value = "-1";
                opt.text = "All";
                sel.add(opt);
                sel.value = "-1";
                // Trigger change event
                sel.dispatchEvent(new Event('change'));
            }""")
            
            print("Set value to -1. Waiting for update...")
            page.wait_for_timeout(5000) # Wait for potential reload
            
            # Count rows
            row_count = page.evaluate("() => document.querySelectorAll('tbody tr').length")
            print(f"Row count after hack: {row_count}")
            
        else:
            print("Length select not found.")

        browser.close()

if __name__ == "__main__":
    run()

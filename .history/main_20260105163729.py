from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        # Launch browser in non-headless mode to see what's happening
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Navigating to https://voterlist.election.gov.np/ ...")
        page.goto("https://voterlist.election.gov.np/")
        
        print(f"Page title: {page.title()}")

        # TODO: Inspect the page to find the correct selectors for the dropdowns.
        # The form likely has dependent dropdowns for State -> District -> Municipality -> Ward -> Polling Centre.
        
        # Example interaction (commented out until selectors are verified):
        # page.select_option('select#state_id', value='1') 
        # page.wait_for_load_state('networkidle')
        
        print("Script finished successfully. Browser will close in 5 seconds.")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    run()

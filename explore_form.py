from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to https://voterlist.election.gov.np/ ...")
        page.goto("https://voterlist.election.gov.np/")
        
        # Wait for the form to be visible
        page.wait_for_selector("form")
        
        # Find all select elements
        selects = page.query_selector_all("select")
        
        print(f"Found {len(selects)} select elements.")
        
        for i, select in enumerate(selects):
            name = select.get_attribute("name")
            id_attr = select.get_attribute("id")
            print(f"Select #{i}: name='{name}', id='{id_attr}'")
            
            # Print options for the first select (State)
            if i == 0:
                options = select.query_selector_all("option")
                print(f"Options for {name}:")
                for opt in options:
                    val = opt.get_attribute("value")
                    text = opt.inner_text()
                    print(f"  Value: {val}, Text: {text}")

        # Find submit button
        buttons = page.query_selector_all("button")
        for btn in buttons:
            print(f"Button text: '{btn.inner_text()}', type: '{btn.get_attribute('type')}'")
            
        inputs = page.query_selector_all("input[type='submit']")
        for inp in inputs:
             print(f"Input Submit value: '{inp.get_attribute('value')}'")

        browser.close()

if __name__ == "__main__":
    run()

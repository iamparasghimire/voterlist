from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://voterlist.election.gov.np/")
        page.select_option("select#state", value="3")
        page.wait_for_timeout(1000)
        
        # Get all options from district select
        options = page.eval_on_selector_all("select#district option", """
            opts => opts.map(o => ({text: o.innerText, value: o.value}))
        """)
        
        for opt in options:
            if "Bhaktapur" in opt['text'] or "भक्तपुर" in opt['text']:
                print(f"Bhaktapur ID: {opt['value']}")
        
        browser.close()

if __name__ == "__main__":
    run()

from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os

# Configuration
STATE_ID = "3" # Bagmati
DISTRICTS = [
    {"id": "27", "name": "Bhaktapur"},
    {"id": "28", "name": "Lalitpur"}
]
OUTPUT_DIR = "data"

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_options(page, selector):
    return page.eval_on_selector_all(f"{selector} option", """
        opts => opts.map(o => ({
            text: o.innerText.trim(), 
            value: o.value
        })).filter(o => o.value !== "")
    """)

def scrape_data(page, district_name, mun_name, ward_name, center_name):
    print(f"Processing: {district_name} -> {mun_name} -> Ward {ward_name} -> {center_name}")
    
    # 1. Click Submit
    submit_btn = page.query_selector("button.btn-success")
    if not submit_btn:
        submit_btn = page.query_selector("input[type='submit']")
    
    if not submit_btn:
        print("!! Submit button not found")
        return []

    submit_btn.click()
    
    # 2. Wait for table loading
    try:
        # Wait a bit for the table to appear or update
        page.wait_for_selector("table#tbl_data", state="attached", timeout=10000)
    except:
        print("!! Table not found or timed out")
        return []

    # 3. Apply 'All' rows hack
    try:
        # Check if select exists
        has_select = page.evaluate("() => !!document.querySelector('select[name=\"tbl_data_length\"]')")
        
        if has_select:
            page.evaluate("""() => {
                const sel = document.querySelector('select[name="tbl_data_length"]');
                if (sel) {
                    let opt = sel.querySelector('option[value="-1"]');
                    if (!opt) {
                        opt = document.createElement('option');
                        opt.value = "-1";
                        opt.text = "All";
                        sel.add(opt);
                    }
                    sel.value = "-1";
                    sel.dispatchEvent(new Event('change'));
                }
            }""")
            # Wait for reload/update. 
            # We can check if the rows count changes or just wait.
            # A fixed wait is safer for now.
            page.wait_for_timeout(3000)
    except Exception as e:
        print(f"!! Error setting 'All' rows: {e}")

    # 4. Extract Data
    rows_data = page.evaluate("""() => {
        const rows = Array.from(document.querySelectorAll('table#tbl_data tbody tr'));
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            return cells.map(cell => cell.innerText.trim());
        });
    }""")
    
    print(f"   Fetched {len(rows_data)} rows.")

    structured_data = []
    for cells in rows_data:
        # Basic validation: Table usually has 8 columns
        # Serial, Voter ID, Name, Age, Gender, Spouse, Parent, Mother
        if len(cells) >= 8:
            record = {
                "District": district_name,
                "Municipality": mun_name,
                "Ward No": ward_name,
                "Polling Centre": center_name,
                "Voter ID": cells[2] if len(cells) > 2 else "",
                "Name": cells[3] if len(cells) > 3 else "",
                "Age": cells[4] if len(cells) > 4 else "",
                "Gender": cells[5] if len(cells) > 5 else "",
                "Spouse Name": cells[6] if len(cells) > 6 else "",
                "Parent Name": cells[7] if len(cells) > 7 else "",
                "Mother Name": cells[8] if len(cells) > 8 else "" 
            }
            structured_data.append(record)
            
    return structured_data

def run():
    ensure_dir(OUTPUT_DIR)
    
    with sync_playwright() as p:
        # headless=False so you can see it working. Set to True for background run.
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigate to site...")
        page.goto("https://voterlist.election.gov.np/", timeout=60000)
        
        # Select State
        print(f"Selecting State: {STATE_ID}")
        page.select_option("select#state", value=STATE_ID)
        page.wait_for_timeout(1000)

        for district in DISTRICTS:
            dist_id = district["id"]
            dist_name = district["name"]
            
            print(f"\n=== Starting District: {dist_name} ({dist_id}) ===")
            page.select_option("select#state", value=STATE_ID) # Ensure state is selected
            page.wait_for_timeout(500)
            page.select_option("select#district", value=dist_id)
            page.wait_for_timeout(1000)
            
            # Get Municipalities
            # Note: We need to re-query options every time the parent reference changes, 
            # but getting the list of values upfront is safer, then re-selecting by value.
            mun_options = get_options(page, "select#vdc_mun")
            
            for mun_opt in mun_options:
                mun_val = mun_opt["value"]
                mun_text = mun_opt["text"]
                
                # Create folder for Municipality
                mun_dir = os.path.join(OUTPUT_DIR, dist_name, mun_text)
                ensure_dir(mun_dir)
                
                print(f" -> Municipality: {mun_text}")
                
                # Re-select context to be safe (state -> district -> mun)
                page.select_option("select#district", value=dist_id)
                page.wait_for_timeout(500)
                page.select_option("select#vdc_mun", value=mun_val)
                page.wait_for_timeout(1000)
                
                # Get Wards
                ward_options = get_options(page, "select#ward")
                
                for ward_opt in ward_options:
                    ward_val = ward_opt["value"]
                    ward_text = ward_opt["text"]
                    
                    print(f"   -> Ward: {ward_text}")
                    
                    # Re-select context
                    page.select_option("select#vdc_mun", value=mun_val)
                    page.wait_for_timeout(500)
                    page.select_option("select#ward", value=ward_val)
                    page.wait_for_timeout(1000)
                    
                    # Get Polling Centres
                    center_options = get_options(page, "select#reg_centre")
                    
                    for center_opt in center_options:
                        center_val = center_opt["value"]
                        center_text = center_opt["text"]
                        
                        # Check if file exists to skip
                        safe_center_name = center_text.replace("/", "-").replace("\\", "-")
                        csv_path = os.path.join(mun_dir, f"Ward_{ward_text}_{safe_center_name}.csv")
                        
                        if os.path.exists(csv_path):
                            print(f"      [Skipping] Already exists: {csv_path}")
                            continue

                        # Select Center
                        page.select_option("select#ward", value=ward_val)
                        page.wait_for_timeout(500)
                        page.select_option("select#reg_centre", value=center_val)
                        
                        # Scrape
                        data = scrape_data(page, dist_name, mun_text, ward_text, center_text)
                        
                        # Save
                        if data:
                            df = pd.DataFrame(data)
                            df.to_csv(csv_path, index=False, encoding='utf-8')
                            print(f"      Saved to {csv_path}")
                        
                        # Navigate back / reset for next iteration?
                        # The page might have reloaded. It's safer to ensure we are at the root or just re-select content.
                        # Since scrape_data clicks submit, the page content changes.
                        # We don't always reload the page, but the dropdowns might need refreshing or the selection might trigger ajax.
                        # The safest usage for this specific site (which uses ajax) is probably to 
                        # just re-select the dropdowns in the next loop iteration, which we do.
                        
                        # Small pause to be nice to server
                        time.sleep(1)

        browser.close()

if __name__ == "__main__":
    run()

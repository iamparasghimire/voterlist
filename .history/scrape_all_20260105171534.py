from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os

OUTPUT_DIR = "voter_data"

def scrape_polling_centre(page, state_name, district_name, mun_name, ward_name, center_name):
    print(f"Scraping: {state_name} -> {district_name} -> {mun_name} -> Ward {ward_name} -> {center_name}")
    
    # Click Submit
    submit_btn = page.query_selector("button.btn-success")
    if not submit_btn:
        submit_btn = page.query_selector("input[type='submit']")
    
    if not submit_btn:
        print("  Submit button not found!")
        return []

    submit_btn.click()
    
    # Wait for table
    try:
        page.wait_for_selector("table#tbl_data", timeout=10000)
    except:
        print("  Table not found (timeout). Maybe no data?")
        return []

    # Force "All" rows (-1)
    try:
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
        page.wait_for_timeout(3000) 
    except Exception as e:
        print(f"  Could not set 'All' rows: {e}")

    # Scrape all rows
    page_data = page.evaluate("""() => {
        const rows = Array.from(document.querySelectorAll('tbody tr'));
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            return cells.map(cell => cell.innerText);
        });
    }""")
    
    print(f"  Found {len(page_data)} rows.")
    
    all_data = []
    for cells in page_data:
        if len(cells) >= 8:
            record = {
                "State": state_name,
                "District": district_name,
                "Municipality": mun_name,
                "Ward": ward_name,
                "Polling Centre": center_name,
                "Voter ID": cells[2],
                "Name": cells[3],
                "Age": cells[4],
                "Gender": cells[5],
                "Spouse Name": cells[6],
                "Parent Name": cells[7]
            }
            all_data.append(record)
            
    return all_data

def navigate_to_context(page, state_val, district_val, mun_val, ward_val):
    print("  Re-navigating to context...")
    try:
        page.goto("https://voterlist.election.gov.np/", timeout=60000)
        
        if state_val:
            page.select_option("select#state", value=state_val)
            page.wait_for_timeout(1000)
        
        if district_val:
            page.select_option("select#district", value=district_val)
            page.wait_for_timeout(1000)
            
        if mun_val:
            page.select_option("select#vdc_mun", value=mun_val)
            page.wait_for_timeout(1000)
            
        if ward_val:
            page.select_option("select#ward", value=ward_val)
            page.wait_for_timeout(1000)
    except Exception as e:
        print(f"  Error during re-navigation: {e}")

def get_options(page, selector):
    select = page.query_selector(selector)
    if not select:
        return []
    options = select.query_selector_all("option")
    results = []
    for opt in options:
        val = opt.get_attribute("value")
        text = opt.inner_text()
        if val: # Skip empty values
            results.append((val, text))
    return results

def run():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to https://voterlist.election.gov.np/ ...")
        page.goto("https://voterlist.election.gov.np/", timeout=60000)
        
        # 1. States
        states = get_options(page, "select#state")
        print(f"Found {len(states)} states.")
        
        for state_val, state_text in states:
            print(f"\n=== State: {state_text} ===")
            page.select_option("select#state", value=state_val)
            page.wait_for_timeout(1500)
            
            # 2. Districts
            districts = get_options(page, "select#district")
            print(f"Found {len(districts)} districts in {state_text}.")
            
            for dist_val, dist_text in districts:
                print(f"\n  --- District: {dist_text} ---")
                page.select_option("select#district", value=dist_val)
                page.wait_for_timeout(1500)
                
                # 3. Municipalities
                muns = get_options(page, "select#vdc_mun")
                print(f"  Found {len(muns)} municipalities in {dist_text}.")
                
                for mun_val, mun_text in muns:
                    print(f"\n    Processing Municipality: {mun_text}")
                    
                    # Select Mun
                    try:
                        page.select_option("select#vdc_mun", value=mun_val)
                        page.wait_for_timeout(1500)
                    except:
                        navigate_to_context(page, state_val, dist_val, mun_val, "")
                    
                    # 4. Wards
                    wards = get_options(page, "select#ward")
                    print(f"    Found {len(wards)} wards.")
                    
                    for ward_val, ward_text in wards:
                        # Select Ward
                        try:
                            page.select_option("select#ward", value=ward_val)
                            page.wait_for_timeout(1500)
                        except:
                            navigate_to_context(page, state_val, dist_val, mun_val, ward_val)

                        # 5. Polling Centres
                        centers = get_options(page, "select#reg_centre")
                        print(f"      Ward {ward_text}: Found {len(centers)} polling centres.")
                        
                        for center_val, center_text in centers:
                            # Select Polling Centre
                            try:
                                page.select_option("select#reg_centre", value=center_val)
                            except:
                                print("      Dropdown issue, reloading...")
                                navigate_to_context(page, state_val, dist_val, mun_val, ward_val)
                                page.select_option("select#reg_centre", value=center_val)
                            
                            # Scrape
                            data = scrape_polling_centre(page, state_text, dist_text, mun_text, ward_text, center_text)
                            
                            # Save Data
                            if data:
                                try:
                                    df = pd.DataFrame(data)
                                    
                                    # Create directory structure: data/State/District/Municipality
                                    safe_state = state_text.replace('/', '_').strip()
                                    safe_dist = dist_text.replace('/', '_').strip()
                                    safe_mun = mun_text.replace('/', '_').strip()
                                    safe_ward = ward_text.replace('/', '_').strip()
                                    safe_center = center_text.replace('/', '_').strip()
                                    
                                    save_dir = os.path.join(OUTPUT_DIR, safe_state, safe_dist, safe_mun)
                                    if not os.path.exists(save_dir):
                                        os.makedirs(save_dir)
                                        
                                    filename = os.path.join(save_dir, f"Ward_{safe_ward}_{safe_center}.xlsx")
                                    df.to_excel(filename, index=False)
                                    print(f"      Saved to {filename}")
                                except Exception as e:
                                    print(f"      Error saving file: {e}")
                            
                            # Reload to clean up
                            page.reload()
                            navigate_to_context(page, state_val, dist_val, mun_val, ward_val)

        browser.close()

if __name__ == "__main__":
    run()

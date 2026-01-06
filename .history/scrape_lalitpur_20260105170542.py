from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os

# Configuration
STATE_ID = "3" # Bagmati
DISTRICT_ID = "28" # Lalitpur
OUTPUT_DIR = "data"

def scrape_polling_centre(page, mun_name, ward_name, center_name):
    print(f"Scraping: {mun_name} - Ward {ward_name} - {center_name}")
    
    # Click Submit
    submit_btn = page.query_selector("button.btn-success")
    if not submit_btn:
        submit_btn = page.query_selector("input[type='submit']")
    
    if not submit_btn:
        print("Submit button not found!")
        return []

    submit_btn.click()
    
    # Wait for table
    try:
        page.wait_for_selector("table#tbl_data", timeout=10000)
    except:
        print("Table not found (timeout). Maybe no data?")
        return []

    # Force "All" rows (-1)
    try:
        page.evaluate("""() => {
            const sel = document.querySelector('select[name="tbl_data_length"]');
            if (sel) {
                // Check if -1 option exists
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
        # Wait for table to update. 
        # If there are many rows, this might take a moment.
        # We can wait for the number of rows to be > 100 if possible, or just a fixed wait.
        # Or wait for the processing overlay to disappear.
        page.wait_for_timeout(3000) 
    except Exception as e:
        print(f"Could not set 'All' rows: {e}")

    # Scrape all rows at once
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
        # Add metadata
        if len(cells) >= 8: # Ensure valid row
            # Columns: Serial, ID, Name, Age, Gender, Spouse, Parent, Link
            record = {
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

def navigate_to_context(page, mun_val, ward_val):
    print("  Re-navigating to context...")
    page.goto("https://voterlist.election.gov.np/", timeout=60000)
    page.select_option("select#state", value=STATE_ID)
    page.wait_for_timeout(1000)
    page.select_option("select#district", value=DISTRICT_ID)
    page.wait_for_timeout(1000)
    page.select_option("select#vdc_mun", value=mun_val)
    page.wait_for_timeout(1000)
    page.select_option("select#ward", value=ward_val)
    page.wait_for_timeout(1000)

def run():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to https://voterlist.election.gov.np/ ...")
        page.goto("https://voterlist.election.gov.np/", timeout=60000)
        
        # Select State
        print("Selecting State 3...")
        page.select_option("select#state", value=STATE_ID)
        page.wait_for_timeout(2000)
        
        # Select District
        print("Selecting District 28 (Lalitpur)...")
        page.select_option("select#district", value=DISTRICT_ID)
        page.wait_for_timeout(2000)
        
        # Get Municipalities
        mun_select = page.query_selector("select#vdc_mun")
        mun_options = mun_select.query_selector_all("option")
        # Skip first (placeholder)
        muns = []
        for opt in mun_options:
            val = opt.get_attribute("value")
            text = opt.inner_text()
            if val:
                muns.append((val, text))
        
        print(f"Found {len(muns)} municipalities.")
        
        all_records = []
        tables_scraped = 0

        for mun_val, mun_text in muns:
            print(f"\nProcessing Municipality: {mun_text}")
            mun_data = []
            
            # Select Municipality
            # We might need to re-select if we reloaded
            try:
                page.select_option("select#vdc_mun", value=mun_val)
                page.wait_for_timeout(2000)
            except:
                navigate_to_context(page, mun_val, "") # Ward not known yet
            
            # Get Wards
            ward_select = page.query_selector("select#ward")
            ward_options = ward_select.query_selector_all("option")
            wards = []
            for opt in ward_options:
                val = opt.get_attribute("value")
                text = opt.inner_text()
                if val:
                    wards.append((val, text))
            
            print(f"  Found {len(wards)} wards.")
            
            for ward_val, ward_text in wards:
                # Select Ward
                try:
                    page.select_option("select#ward", value=ward_val)
                    page.wait_for_timeout(2000)
                except:
                    navigate_to_context(page, mun_val, ward_val)

                # Get Polling Centres
                center_select = page.query_selector("select#reg_centre")
                center_options = center_select.query_selector_all("option")
                centers = []
                for opt in center_options:
                    val = opt.get_attribute("value")
                    text = opt.inner_text()
                    if val:
                        centers.append((val, text))
                
                print(f"  Ward {ward_text}: Found {len(centers)} polling centres.")
                
                for center_val, center_text in centers:
                    # Select Polling Centre
                    try:
                        page.select_option("select#reg_centre", value=center_val)
                    except:
                        print("  Dropdown issue, reloading...")
                        navigate_to_context(page, mun_val, ward_val)
                        page.select_option("select#reg_centre", value=center_val)
                    
                    # Scrape
                    data = scrape_polling_centre(page, mun_text, ward_text, center_text)
                    mun_data.extend(data)

                    # Save Polling Centre Data (One by one)
                    if data:
                        try:
                            df_center = pd.DataFrame(data)
                            safe_mun = mun_text.replace('/', '_').strip()
                            safe_ward = ward_text.replace('/', '_').strip()
                            safe_center = center_text.replace('/', '_').strip()
                            
                            # Create Mun directory
                            mun_dir = os.path.join(OUTPUT_DIR, safe_mun)
                            if not os.path.exists(mun_dir):
                                os.makedirs(mun_dir)
                                
                            filename = os.path.join(mun_dir, f"Ward_{safe_ward}_{safe_center}.xlsx")
                            df_center.to_excel(filename, index=False)
                            print(f"  Saved {len(data)} records to {filename}")
                        except Exception as e:
                            print(f"  Error saving file: {e}")
                    
                    # Reload page to clean up DOM hack
                    # This ensures the next iteration starts clean
                    page.reload()
                    # We need to get back to the current state (Mun -> Ward)
                    # But we are inside the loop.
                    # The easiest way is to just re-select everything at the start of the loop or catch exceptions.
                    # But since we reload, we MUST re-navigate.
                    navigate_to_context(page, mun_val, ward_val)
                    
                    tables_scraped += 1
                    if tables_scraped >= 100:
                        print("Reached 100 tables limit. Stopping.")
                        break
                
                if tables_scraped >= 100:
                    break
            
            if tables_scraped >= 100:
                break
                    
            # Save Municipality Data
            if mun_data:
                df = pd.DataFrame(mun_data)
                filename = f"{OUTPUT_DIR}/{mun_text.replace('/', '_')}.xlsx"
                df.to_excel(filename, index=False)
                print(f"Saved {len(mun_data)} records to {filename}")
                
                # Add to main list
                all_records.extend(mun_data)
            else:
                print(f"No data found for {mun_text}")

        # Save ALL data to one file
        if all_records:
            print(f"Saving total {len(all_records)} records to all_voter_list.xlsx...")
            df_all = pd.DataFrame(all_records)
            df_all.to_excel("all_voter_list.xlsx", index=False)
            print("Done.")

        browser.close()

if __name__ == "__main__":
    run()

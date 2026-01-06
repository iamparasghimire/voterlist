# Voter List Scraper (Bhaktapur & Lalitpur)

This tool automates the extraction of voter list data from the Election Commission of Nepal website for **Bhaktapur** and **Lalitpur** districts.

## Features
- **Districts Covered**: Bhaktapur and Lalitpur (Province 3 - Bagmati).
- **Automated Traversal**: Iterates through all Municipalities, Wards, and Polling Centres.
- **Full Data Extraction**: Automatically handles the "All" rows option to download complete tables.
- **Datafields**: Municipality, Ward No, Polling Centre, Voter ID, Name, Age, Gender, Spouse Name, Parent Name, Mother Name.
- **Output**: Saves data as CSV files organized by District and Municipality.

## Prerequisites

- Python 3.8+
- Playwright

## Installation

1. **Clone or Download the code**

2. **Set up a Virtual Environment** (Recommended)
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Browsers**
   ```bash
   playwright install chromium
   ```

## How to Run

To start the scraping process for both districts:

```bash
python scrape_districts.py
```

*Note: The script runs in `headless=False` mode by default, so you will see the browser open and perform actions. Do not close the browser window.*

## Output Data

The downloaded data will be saved in the `data/` folder with the following structure:

```
data/
├── Bhaktapur/
│   ├── Municipality Name/
│   │   ├── Ward_1_PollingCentreName.csv
│   │   ├── Ward_2_PollingCentreName.csv
│   │   └── ...
├── Lalitpur/
│   ├── Municipality Name/
│   │   └── ...
```

Each CSV file contains the voter list for a specific polling centre.

## Troubleshooting

- **Timeout Errors**: If the internet connection is slow, the script might time out. It is designed to skip already downloaded files, so you can restart the script to resume.
- **Table Loading**: Sometimes the website is slow to load the data table. The script attempts to wait, but if it fails, that specific center might differ.

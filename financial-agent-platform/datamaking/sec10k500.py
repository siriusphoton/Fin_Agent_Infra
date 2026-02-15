import pandas as pd
from sec_edgar_downloader import Downloader
import os
import shutil
import glob
import requests
from io import StringIO


def download_sp500_csv():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # Define a User-Agent header to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Fetch the page content first using requests
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors

        # Use StringIO to make the HTML string look like a file object for pandas
        tables = pd.read_html(StringIO(response.text))
        
        # The first table is usually the S&P 500 list
        sp500_table = tables[0]
        
        print("First 5 rows fetched:")
        print(sp500_table.head())
        
        csv_filename = 'sp500_companies.csv'
        sp500_table.to_csv(csv_filename, index=False)
        print(f"\nSuccessfully saved to '{csv_filename}'")
        
    except Exception as e:
        print(f"Error: {e}")

def download_latest_10k():
    # --- CONFIGURATION ---
    # SEC requires a User-Agent formatted as "Name email@domain.com"
    # Please replace these with your actual details to avoid being blocked.
    USER_NAME = "YourName"
    USER_EMAIL = "your.email@example.com" 
    
    CSV_FILE = 'sp500_companies.csv'
    DOWNLOAD_FOLDER = "sec-edgar-filings" # Temp folder created by the library
    TARGET_FOLDER = "html10k"
    # ---------------------
    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
        print(f"Created directory: {TARGET_FOLDER}")
    # Initialize the downloader
    dl = Downloader(USER_NAME, USER_EMAIL)

    # Read the tickers from your CSV
    try:
        df = pd.read_csv(CSV_FILE)
        tickers = df['Symbol'].tolist()
    except FileNotFoundError:
        print(f"Error: Could not find {CSV_FILE}. Please run the previous script first.")
        return

    print(f"Found {len(tickers)} companies. Starting download...")

    for ticker in tickers:
        # SEC tickers often use hyphen instead of dot (e.g., BRK.B -> BRK-B)
        formatted_ticker = ticker.replace('.', '-')
        
        print(f"\nProcessing: {ticker}...")
        
        try:
            # Download the latest 10-K (limit=1)
            # download_details=True ensures we get the readable HTML file
            count = dl.get("10-K", formatted_ticker, limit=1, download_details=True)
            
            if count == 0:
                print(f"No 10-K found for {ticker}")
                continue

            # The library saves to: sec-edgar-filings/TICKER/10-K/ACCESSION_NUMBER/primary-document.html
            # We need to find that HTML file and move it.
            
            # Construct the path pattern to find the .htm files
            # Note: We look for the folder matching the formatted ticker
            search_path = os.path.join(DOWNLOAD_FOLDER, formatted_ticker, "10-K", "*", "*.htm*")
            files = glob.glob(search_path)
            
            if files:
                # Heuristic: The main 10-K is usually the largest HTML file in the folder
                # (Exhibits are usually smaller)
                main_file = max(files, key=os.path.getsize)
                
                # Define the new filename (e.g., AAPL.html)
                new_filename = f"{ticker}.html"
                
                destination_path = os.path.join(TARGET_FOLDER, new_filename) 
                # Move and rename
                shutil.move(main_file, destination_path)
                print(f"-> Saved as {new_filename}")
                
            else:
                print(f"-> Downloaded, but could not locate HTML file for {ticker}")

        except Exception as e:
            print(f"-> Failed: {e}")

    # Optional: Cleanup the 'sec-edgar-filings' temp folder after finishing
    shutil.rmtree(DOWNLOAD_FOLDER) 
    print("\nCleanup complete.")

if __name__ == "__main__":
    download_sp500_csv()
    download_latest_10k()
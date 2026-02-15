import os

KEEP_TICKERS = {
    "NVDA","AAPL","GOOG","MSFT","AMZN","META","TSLA","AVGO","BRK-B",
    "WMT","LLY","JPM","XOM","V","JNJ","MU","MA","ORCL","COST",
    "ABBV","HD","BAC","PG","CVX","CAT","KO","AMD","GE","NFLX",
    "PLTR","CSCO","MRK","LRCX","PM","AMAT","GS","WFC","MS",
    "RTX","UNH","TMUS","IBM","MCD","INTC","AXP","PEP","GEV",
    "VZ","TXN","T"
}

MDS_FOLDER = "mds"

deleted_files = []

for filename in os.listdir(MDS_FOLDER):
    if not filename.endswith(".md"):
        continue

    ticker = filename.replace(".md", "")

    if ticker not in KEEP_TICKERS:
        file_path = os.path.join(MDS_FOLDER, filename)
        deleted_files.append(file_path)

        os.remove(file_path)

print("\nFiles deleted:")
for f in deleted_files:
    print(f)


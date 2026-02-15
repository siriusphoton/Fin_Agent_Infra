import os
import glob
import time
from tqdm import tqdm  # The progress bar library
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document
from sqlalchemy import create_engine, text

# Configuration
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5432/financial_agent"
COLLECTION_NAME = "sec_filings_mpnet"
DATA_FOLDER = "mds"  # Ensure your markdown files are here

# Initialize Embeddings
print("🔌 Initializing Embeddings Model (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")

# Initialize Vector Store
vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

def get_processed_tickers():
    """
    Checks the database to see which tickers have already been ingested.
    Returns a set of ticker strings (e.g., {'AAPL', 'MSFT'}).
    """
    engine = create_engine(CONNECTION_STRING)
    try:
        with engine.connect() as connection:
            # We query the distinct metadata->>'ticker' from the table
            # Note: The table name is usually "langchain_pg_embedding"
            # This query is robust enough for standard PGVector setups
            result = connection.execute(text(
                "SELECT DISTINCT cmetadata->>'ticker' FROM langchain_pg_embedding"
            ))
            existing_tickers = {row[0] for row in result if row[0]}
            return existing_tickers
    except Exception as e:
        print(f"⚠️ Could not fetch existing tickers (Table might be empty): {e}")
        return set()

def split_markdown(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split by Header (Structure)
    headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(text)

    # Split by Characters (Size)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return text_splitter.split_documents(md_header_splits)

def main():
    # 1. Get List of Files
    md_files = glob.glob(os.path.join(DATA_FOLDER, "*.md"))
    if not md_files:
        print(f"❌ No markdown files found in '{DATA_FOLDER}/'.")
        return

    # 2. Check Resume Status
    print("🔍 Checking database for existing data...")
    existing_tickers = get_processed_tickers()
    print(f"✅ Found {len(existing_tickers)} tickers already in DB. Skipping them.")

    # Filter out files that are already done
    files_to_process = []
    for f in md_files:
        ticker = os.path.basename(f).replace(".md", "").upper()
        if ticker not in existing_tickers:
            files_to_process.append(f)
        else:
            # Optional: Print skipped files if you want debug info
            # print(f"⏩ Skipping {ticker} (Already processed)")
            pass

    if not files_to_process:
        print("🎉 All files are already processed! Nothing to do.")
        return

    print(f"🚀 Starting ingestion for {len(files_to_process)} new files...")
    
    # 3. Process with Progress Bar
    # tqdm wraps the loop and creates the bar
    for file_path in tqdm(files_to_process, desc="Ingesting Files", unit="file"):
        ticker = os.path.basename(file_path).replace(".md", "").upper()
        
        try:
            # A. Split
            chunks = split_markdown(file_path)
            
            # B. Tag
            for chunk in chunks:
                chunk.metadata["ticker"] = ticker
                chunk.metadata["source"] = file_path

            # C. Embed & Upload (Batch per file)
            # We upload immediately so if script crashes, this file is saved.
            vector_store.add_documents(chunks)
            
        except Exception as e:
            print(f"\n❌ Error processing {ticker}: {e}")
            # Continue to next file despite error
            continue

    print("\n✅ Ingestion Complete!")

if __name__ == "__main__":
    main()
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

# 1. Setup (Must match ingest.py)
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5432/financial_agent"
COLLECTION_NAME = "sec_filings"

print("🔌 Connecting to Vector Database...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

def test_query(query, ticker=None):
    print(f"\n🔎 Query: '{query}' (Filter: {ticker if ticker else 'None'})")
    print("-" * 50)
    
    # 2. Run the Search
    # k=3 means "Get the top 3 most similar chunks"
    try:
        if ticker:
            # Filter specifically for this company
            # Note: PGVector syntax for metadata filtering can vary slightly by version, 
            # but usually looks like this dict structure.
            results = vector_store.similarity_search_with_score(
                query, 
                k=3,
                filter={"ticker": ticker} 
            )
        else:
            results = vector_store.similarity_search_with_score(query, k=3)
            
        if not results:
            print("❌ No results found. Is the database empty?")
            return

        # 3. Print Results
        for i, (doc, score) in enumerate(results):
            # score is usually 'distance' (lower is better) or 'similarity' (higher is better)
            # PGVector usually returns L2 distance by default (Lower = Better match)
            print(f"📄 Result {i+1} (Score: {score:.4f})")
            print(f"   Source: {doc.metadata.get('ticker')} | {doc.metadata.get('source')}")
            print(f"   Content snippet: {doc.page_content}...") # Show first 200 chars
            print("")
            
    except Exception as e:
        print(f"❌ Error during search: {e}")

if __name__ == "__main__":
    # Test 1: General Concept Search
    test_query("What are the primary risk factors regarding supply chain?")
    
    # Test 2: Specific Company Search (Replace AAPL with a ticker you actually ingested)
    # If you ingested MSFT, change this to MSFT
    test_query("What is the revenue growth?", ticker="AAPL") 
    
    # Test 3: Specific Topic for a Company
    test_query("What does the report say about AI or Artificial Intelligence?", ticker="GOOG")
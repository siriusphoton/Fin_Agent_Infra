# tools.py
import random
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

# --- 1. SETUP VECTOR STORE CONNECTION (Global) ---
# This runs once when the agent starts
print("Connecting tools to Knowledge Base...")
CONNECTION_STRING = "postgresql+psycopg://admin:password@localhost:5432/financial_agent"
COLLECTION_NAME = "sec_filings"

# Initialize the same embeddings model used in ingestion
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=CONNECTION_STRING,
    use_jsonb=True,
)
# -------------------------------------------------

@tool
def get_stock_price(ticker: str):
    """
    Retrieves the current stock price for a given ticker symbol.
    Use this for questions like 'What is the price of Apple?' or 'Current price of NVDA'.
    """
    print(f"\n--- 🛠️ TOOL CALL: Fetching price for {ticker} ---")
    
    mock_prices = {
        "AAPL": 220.50,
        "GOOGL": 175.30,
        "MSFT": 410.10,
        "NVDA": 135.20
    }
    price = mock_prices.get(ticker.upper(), round(random.uniform(100, 500), 2))
    return f"The current price of {ticker.upper()} is ${price}"

@tool
def search_10k(query: str, ticker: str):
    """
    Searches the company's latest 10-K (Annual Report) for specific information.
    ALWAYS use this tool when the user asks about risks, revenue, business description, or legal proceedings.
    
    Args:
        query: The specific question or topic to search for (e.g., "supply chain risks", "AI strategy").
        ticker: The stock ticker symbol (e.g., "AAPL", "MSFT").
    """
    print(f"\n--- 🛠️ TOOL CALL: RAG Search for {ticker}: '{query}' ---")
    
    try:
        # 1. Search the Vector DB
        # We perform a similarity search looking for the top 5 most relevant chunks
        results = vector_store.similarity_search(
            query, 
            k=15, 
            filter={"ticker": ticker.upper()} # Strict filtering ensures we don't mix up companies
        )
        
        if not results:
            return f"I searched the 10-K report for {ticker} but found no information regarding '{query}'."
        
        # 2. Format the results for the LLM
        # We combine the chunks into a single string context
        context = ""
        for doc in results:
            context += f"---\nExcerpt:\n{doc.page_content}\n"
        
        return f"Found the following relevant excerpts from the {ticker} 10-K report:\n{context}"

    except Exception as e:
        return f"Error searching documents: {str(e)}"

@tool
def calculate_financial_metric(metric: str, value_a: float, value_b: float):
    """
    Performs deterministic financial calculations. ALWAYS use this for ratios, margins, or growth rates.
    NEVER do math in your head.

    Args:
        metric: The name of the metric (e.g., "net_margin", "current_ratio", "pe_ratio").
        value_a: The numerator or primary value (e.g., Net Income, Current Assets, Price).
        value_b: The denominator or secondary value (e.g., Revenue, Current Liabilities, EPS).
    """
    print(f"\n--- 🧮 TOOL CALL: Calculating {metric} ({value_a} / {value_b}) ---")
    
    try:
        if value_b == 0:
            return "Error: Division by zero is not allowed."
            
        result = 0.0
        
        if metric.lower() in ["net_margin", "profit_margin"]:
            # Net Income / Revenue
            result = (value_a / value_b) * 100
            return f"The {metric} is {result:.2f}%"
            
        elif metric.lower() == "current_ratio":
            # Current Assets / Current Liabilities
            result = value_a / value_b
            return f"The Current Ratio is {result:.2f}"
            
        elif metric.lower() == "pe_ratio":
            # Price / EPS
            result = value_a / value_b
            return f"The P/E Ratio is {result:.2f}"
            
        else:
            # Generic Division fallback
            result = value_a / value_b
            return f"The calculated value for {metric} is {result:.2f}"

    except Exception as e:
        return f"Calculation Error: {str(e)}"

# Update your tools list
tools = [get_stock_price, search_10k, calculate_financial_metric]
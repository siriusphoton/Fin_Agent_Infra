# tools.py
import random
from langchain_core.tools import tool

# @tool decorator makes this function visible to the LLM
@tool
def get_stock_price(ticker: str):
    """
    Retrieves the current stock price for a given ticker symbol.
    Use this for questions like 'What is the price of Apple?' or 'Current price of NVDA'.
    """
    print(f"--- 🛠️ TOOL CALL: Fetching price for {ticker} ---")
    
    # Mocking real data for Phase 1 (to avoid Yahoo Finance API limits while testing)
    mock_prices = {
        "AAPL": 220.50,
        "GOOGL": 175.30,
        "MSFT": 410.10,
        "NVDA": 135.20
    }
    
    # Simulate a database lookup
    price = mock_prices.get(ticker.upper(), round(random.uniform(100, 500), 2))
    return f"The current price of {ticker.upper()} is ${price}"

# List of tools we will give to the Agent
tools = [get_stock_price]
from langchain_ollama import ChatOllama
import os
from dotenv import load_dotenv

load_dotenv()  # you had a bug here

llm = ChatOllama(
    model="gpt-oss:20b-cloud",
    base_url=os.getenv("OLLAMA_BASE_URL"),
    headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"},
)

messages = [
    ("human", "Explain how does a transformer work?")
]

output = llm.invoke(messages)
print(output.content)

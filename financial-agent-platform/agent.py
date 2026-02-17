import os
from dotenv import load_dotenv

from state import AgentState
from tools import tools

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
load_dotenv()

llm = ChatOllama(
    model="gpt-oss:20b-cloud",
    base_url=os.getenv("OLLAMA_BASE_URL"),
    headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"},
)

llm_with_tools = llm.bind_tools(tools)

def reasoner(state: AgentState):
    """
    The Main Node: It looks at the conversation history and decides what to do.
    """
    # Get the message history
    instruction = SystemMessage(content="When you use search_10k tool make sure you give a long and detailed query for effective retrieval. only answer after analyzing tool output never answer on your own knowledge")
    messages = state["messages"]
    # Ask the LLM
    response = llm_with_tools.invoke([instruction] + messages)
    # Return the new message to update the state
    return {"messages": [response]}

# 5. Build the Graph (The Architecture)
builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("reasoner", reasoner)
builder.add_node("tools", ToolNode(tools)) # Prebuilt node that runs our Python functions

# Add Edges (The Logic)
builder.add_edge(START, "reasoner")

# Conditional Edge:
# After 'reasoner' runs, check: Did the LLM ask to use a tool?
# If YES -> Go to "tools" node
# If NO  -> Go to END (Finish)
builder.add_conditional_edges(
    "reasoner",
    tools_condition,
)

# Loop back: After the tool runs, give the result back to the reasoner
builder.add_edge("tools", "reasoner")

# Compile the Graph
graph = builder.compile()

# --- RUN IT ---
if __name__ == "__main__":
    print("--- 🤖 Financial Agent MVP (Type 'quit' to exit) ---")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        
        # FIX: Use HumanMessage object instead of a tuple ("user", input)
        # This ensures 'last_msg' always has a .type attribute
        events = graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            stream_mode="values"
        )
        
        for event in events:
            if "messages" in event:
                # Get the last message in the list
                last_msg = event["messages"][-1]
                
                # Check if it is actually a Message object (has a 'type')
                # This protects against any initial state weirdness
                if hasattr(last_msg, "type") and last_msg.type == "ai":
                    print(f"Agent: {last_msg.content}")

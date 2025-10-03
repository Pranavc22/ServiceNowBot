from langgraph.graph import StateGraph, END
from agents.summary_agent import SummarizerAgent

# Initialize your agents
summarizer_agent = SummarizerAgent()

# Build the state graph
graph = StateGraph(dict)

# --- Nodes ---
def summarize_node(state: dict):
    transcript = state["transcript"]
    summary_json = summarizer_agent.run(transcript)
    state["summary_json"] = summary_json
    return state

graph.add_node("summarizer", summarize_node)

# --- Graph flow ---
graph.set_entry_point("summarizer")   # first node
graph.add_edge("summarizer", END)     # ends after summarizer for now

# Compile pipeline
sn_pipeline = graph.compile()
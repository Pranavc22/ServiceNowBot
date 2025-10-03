from langgraph.graph import StateGraph, END

from agents.summary_agent import SummarizerAgent
from agents.servicenow_agent import ServiceNowAgent

# Initialize agents
summarizer_agent = SummarizerAgent()
servicenow_agent = ServiceNowAgent()

# Build state graph
graph = StateGraph(dict)

# Nodes
def summarize_node(state: dict):
    transcript = state["transcript"]
    summary_json = summarizer_agent.run(transcript)
    state["summary_json"] = summary_json
    return state

def servicenow_lookup_node(state: dict):
    """Fetch ServiceNow sys_id for the requestor only, update in place."""
    summary = state.get("summary_json", {})
    requestor = summary.get("requestor")

    if not requestor or not requestor.get("id"):
        return state

    email = requestor["id"]
    try:
        user_data = servicenow_agent.get_user_sys_id(email)
        if user_data:
            requestor["sys_id"] = user_data["sys_id"]
            requestor["sn_name"] = user_data.get("name")
    except Exception as e:
        requestor["error"] = str(e)

    return state

# Graph flow
graph.add_node("summarizer", summarize_node)
graph.add_node("servicenow_lookup", servicenow_lookup_node)

graph.set_entry_point("summarizer")        
graph.add_edge("summarizer", "servicenow_lookup")
graph.add_edge("servicenow_lookup", END)   

# Compile
sn_pipeline = graph.compile()
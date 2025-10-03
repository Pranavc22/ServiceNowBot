from langgraph import Pipeline
from summarizer_agent import SummarizerAgent

# Initialize agent
summarizer_agent = SummarizerAgent()

# Define the pipeline
pipeline = Pipeline(
    nodes=[
        {
            "name": "summarizer",
            "type": "custom",
            "func": summarizer_agent.run,
            "inputs": ["transcript"],
            "outputs": ["summary_json"]
        }
    ]
)
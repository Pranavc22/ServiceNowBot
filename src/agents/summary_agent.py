import json
import re

from typing import Dict, Any

from helpers.llm_api import get_llm_client

class SummarizerAgent:
    """Agent that summarizes transcript text and extracts user/email pairs."""

    def __init__(self):
        self.llm = get_llm_client()

    def run(self, transcript: str) -> Dict[str, Any]:
        """Send transcript to LLM and return JSON output with summary and attendees."""
        
        system_prompt = """
        You are a meeting transcript assistant that is detecting action items for Service Now User Stories. Produce a JSON object that contains the following:
        - 'summary': contains a short summary of the transcript.
        - 'requestor': contains 'user' (name) and 'id' (email id) of the requestor. Found at the beginning of the transcript.  
        - 'new_stories': an array of new recommended user stories. Each array element should have: 'short_desc' (A name for the new task), 'acceptance_criteria' (A paragraph of the objectives for the new story)
        - 'existing_stories': an array of existing user stories identified in the conversation. Each array element should have 'short_desc' (Name of the existing story that has been explicitly mentioned), 'number' (the ID for the user story), 'acceptance_criteria'(a paragraph of the existing and new objectives)

        Leave any field null, if not detected/perceivable.
        Do not output anything but the JSON object within <json></json> tags.
        """

        user_prompt = f"Transcript:\n{transcript}\nReturn the JSON as specified.\nJSON:"

        response = self.llm.chat(system=system_prompt, user=user_prompt, temperature=0.2, max_tokens=1024)
        match = re.search(r"<json>(.*)</json>", response, flags=re.DOTALL)
        if not match:
            raise ValueError(f"No <json> block found in response: {response}")

        cleaned = match.group(1).strip()
        
        try:
            data = json.loads(cleaned)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")

        return data
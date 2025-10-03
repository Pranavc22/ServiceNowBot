import json

from typing import Dict, Any

from helpers.llm_api import get_llm_client

class SummarizerAgent:
    """Agent that summarizes transcript text and extracts user/email pairs."""

    def __init__(self):
        self.llm = get_llm_client()

    def run(self, transcript: str) -> Dict[str, Any]:
        """Send transcript to LLM and return JSON output with summary and attendees."""
        
        system_prompt = """
        You are a meeting transcript assistant. Produce a JSON object that contains the following:
        1. 'summary': contains a short summary of the transcript.
        2. 'requestor': contains 'user' (name) and 'id' (email id) of the requestor. Found at the beginning of the transcript.  
        3. 'recommended_stories': an array of new recommended action items in the form of Service Now User Stories. Should have: 'short_desc' (A name for the task), 'acceptance_criteria' (The criteria which defines the task's completion)(Leave empty if not perceivable) 
        4. 'identified_stories': an array of existing user stories identified in the conversation. Should have 'short_desc' (A short description of the task or name of the task that has been explicitly mentioned) (Leave empty if not detected), 'number' (the ID for the user story) (Leave empty if not detected)

        No need for code block markdown. Respond with just the JSON object. 
        """

        user_prompt = f"Transcript:\n{transcript}\nReturn the JSON as specified.\nJSON:"

        response = self.llm.chat(system=system_prompt, user=user_prompt, temperature=0.2, max_tokens=200)

        try:
            data = json.loads(response)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")

        return data
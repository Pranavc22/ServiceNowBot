from helpers.llm_api import get_llm_client
from typing import Dict, Any

class SummarizerAgent:
    """
    Agent that summarizes transcript text and extracts user/email pairs.
    """

    def __init__(self):
        self.llm = get_llm_client()

    def run(self, transcript: str) -> Dict[str, Any]:
        """
        Send transcript to LLM and return JSON output with summary and attendees.
        """
        system_prompt = (
            "You are an assistant that reads meeting transcripts and produces a JSON "
            "object with a 'summary' key containing a short summary of the meeting, "
            "and an 'attendees' key which is a list of objects with 'user' and 'id' "
            "(email) for each participant mentioned in the transcript. Respond only in JSON format."
        )

        user_prompt = f"Transcript:\n{transcript}\n\nReturn the JSON as specified."

        response = self.llm.chat(system=system_prompt, user=user_prompt, temperature=0.0, max_tokens=800)

        # LLM returns JSON string, convert to Python dict
        import json
        try:
            data = json.loads(response)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")

        return data
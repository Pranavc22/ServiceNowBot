import json
import os
import requests
import urllib.parse

from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()  

class ServiceNowAgent:
    """Agent to interact with ServiceNow APIs (via Table API)."""

    def __init__(self):
        self.base_url = os.getenv("SN_INSTANCE")
        self.username = os.getenv("SN_USER")
        self.password = os.getenv("SN_PWD")

        if not self.base_url:
            raise RuntimeError("Missing SN_INSTANCE in environment")

        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def get_user_sys_id(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetch ServiceNow sys_id, name, and email for a user by email prefix."""
        
        encoded_id = urllib.parse.quote(email)
        url = (
            f"{self.base_url}/api/now/table/sys_user"
            f"?sysparm_query=emailSTARTSWITH{encoded_id}"
            f"&sysparm_fields=sys_id,name,email"
            f"&sysparm_limit=1"
        )

        resp = self.session.get(url)
        if resp.status_code != 200:
            raise RuntimeError(
                f"ServiceNow API error {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        result = data.get("result", [])
        if not result:
            return None

        return result[0]
    
    def create_story(
        self,
        requested_for_sys_id: str,
        short_description: str,
        acceptance_criteria: str,
        assigned_to_sys_id: Optional[str] = None,
        implementation_type: str = "oob",
    ) -> Dict[str, Any]:
        """
        Create a new ServiceNow story (rm_story table).

        Parameters:
            requested_for_sys_id: sys_id of the requestor
            short_description: story short description
            acceptance_criteria: story acceptance criteria
            assigned_to_sys_id: optional sys_id to assign the story
            implementation_type: e.g., "oob"
        Returns:
            dict: JSON response from ServiceNow API
        """
        url = f"{self.base_url}/api/now/table/rm_story?sysparm_fields=sys_id,number,short_description"

        payload = {
            "u_requested_for": requested_for_sys_id,
            "short_description": short_description,
            "u_implementation_type": implementation_type,
            "acceptance_criteria": acceptance_criteria
        }

        if assigned_to_sys_id:
            payload["assigned_to"] = assigned_to_sys_id

        resp = self.session.post(url, data=json.dumps(payload))
        if resp.status_code != 201 and resp.status_code != 200:
            raise RuntimeError(
                f"ServiceNow API error {resp.status_code}: {resp.text}"
            )

        return resp.json()
    
    def find_story_by_short_desc(
        self, short_desc: str, limit: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Find ServiceNow stories by short description (LIKE search).

        Parameters:
            short_desc: Partial or full short description to search
            limit: Max number of results to return

        Returns:
            dict or None: JSON response containing matching stories, or None if not found
        """
        encoded_desc = urllib.parse.quote(short_desc)
        url = (
            f"{self.base_url}/api/now/table/rm_story"
            f"?sysparm_query=short_descriptionLIKE{encoded_desc}"
            f"&sysparm_fields=sys_id,number,short_description"
            f"&sysparm_limit={limit}"
        )

        resp = self.session.get(url)
        if resp.status_code != 200:
            raise RuntimeError(
                f"ServiceNow API error {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        result = data.get("result", [])
        return result if result else None

    def update_story(
        self,
        short_desc: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing ServiceNow story found by short description.

        Parameters:
            short_desc: The short description of the story to update
            updates: A dict containing the fields to update

        Returns:
            dict or None: JSON response of the updated story, or None if not found
        """
        stories = self.find_story_by_short_desc(short_desc=short_desc, limit=1)
        if not stories:
            print(f"No story found with short description LIKE '{short_desc}'")
            return None

        sys_id = stories[0]["sys_id"]

        url = (
            f"{self.base_url}/api/now/table/rm_story/{sys_id}"
            f"?sysparm_fields=sys_id,number,short_description"
        )

        resp = self.session.patch(url, data=json.dumps(updates))
        if resp.status_code != 200:
            raise RuntimeError(
                f"ServiceNow API error {resp.status_code}: {resp.text}"
            )

        return resp.json()
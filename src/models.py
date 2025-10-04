from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class StoryItem(BaseModel):
    short_desc: str
    acceptance_criteria: Optional[str] = ""
    action_type: str


class PushStoriesRequest(BaseModel):
    requestor_sys_id: str
    confirmed_stories: List[StoryItem]


class PushStoriesResponse(BaseModel):
    created_stories: List[Dict[str, Any]]
from typing import Any, Dict, List
from pydantic import BaseModel


class RedTeamRequest(BaseModel):
    role: str
    max_tests: int = 12
    intensity: str = "standard"


class RedTeamStep(BaseModel):
    step_no: int

    # ReAct style trace
    agent_thought: str
    agent_action: str
    attack_prompt: str

    # Attack metadata
    target_collection: str
    attack_type: str
    attack_goal: str

    # Observation
    medibot_retrieval_type: str
    medibot_answer: str
    medibot_sources: List[Dict[str, Any]]

    # Agent judgement
    source_collections_returned: List[str]
    leaked_collections: List[str]
    passed: bool
    agent_observation: str
    agent_reflection: str
    next_action: str


class RedTeamResponse(BaseModel):
    role: str
    allowed_collections: List[str]
    forbidden_collections: List[str]

    total_tests: int
    passed_tests: int
    failed_tests: int

    risk_level: str
    verdict: str

    executive_summary: str
    attack_strategy: str
    final_conclusion: str

    frontend_timeline: List[str]
    steps: List[RedTeamStep]
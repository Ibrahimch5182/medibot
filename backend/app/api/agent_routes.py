from fastapi import APIRouter, HTTPException

from app.agent.red_team_agent import red_team_agent
from app.schemas.agent import RedTeamRequest, RedTeamResponse

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/red-team-audit", response_model=RedTeamResponse)
def run_red_team_audit(request: RedTeamRequest):
    try:
        return red_team_agent.run_audit(
            role=request.role,
            max_tests=request.max_tests,
            intensity=request.intensity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
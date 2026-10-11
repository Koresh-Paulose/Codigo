from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HintRequest(BaseModel):
    session_id: str
    concept_id: str

class HintResponse(BaseModel):
    hint: str
    level: int

from .ladder import get_next_hint

@router.post("/session/hint", response_model=HintResponse)
async def get_hint(request: HintRequest):
    # Call the actual ladder logic
    res = get_next_hint(request.session_id, request.concept_id)
    if "error" in res:
        return HintResponse(hint=res["error"], level=res["level"])
    return HintResponse(hint=res["hint"], level=res["level"])

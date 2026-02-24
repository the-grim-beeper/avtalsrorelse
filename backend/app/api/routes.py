import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.definitions import AGENTS
from app.engine.runner import SimulationRunner
from app.models.scenario import MacroParameters
from app.scenarios.presets import PRESETS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


class SimulationRequest(BaseModel):
    preset_id: str | None = None
    parameters: MacroParameters | None = None


@router.get("/presets")
async def get_presets():
    return list(PRESETS.values())


@router.get("/agents")
async def get_agents():
    return list(AGENTS.values())


@router.post("/simulate")
async def simulate(request: SimulationRequest):
    flavor_text = ""
    if request.preset_id:
        preset = PRESETS.get(request.preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{request.preset_id}' not found")
        parameters = request.parameters or preset.parameters
        flavor_text = preset.flavor_text
    elif request.parameters:
        parameters = request.parameters
    else:
        raise HTTPException(status_code=400, detail="Must provide preset_id or parameters")

    runner = SimulationRunner(parameters, request.preset_id, flavor_text)

    async def event_generator():
        async for event in runner.run():
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())

from enum import Enum
from pydantic import BaseModel, Field


class ExportPressure(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MacroParameters(BaseModel):
    inflation: float = Field(2.0, ge=0, le=15, description="KPI inflation %")
    unemployment: float = Field(7.0, ge=2, le=15, description="Unemployment %")
    gdp_growth: float = Field(2.0, ge=-5, le=8, description="GDP growth %")
    policy_rate: float = Field(2.5, ge=-0.5, le=10, description="Riksbank policy rate %")
    political_climate: int = Field(3, ge=1, le=5, description="1=Left, 5=Right")
    export_pressure: ExportPressure = ExportPressure.MEDIUM
    previous_agreement: float = Field(2.5, ge=0, le=8, description="Previous märket %")


class ScenarioPreset(BaseModel):
    id: str
    name: str
    description: str
    flavor_text: str
    parameters: MacroParameters

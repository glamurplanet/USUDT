from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class MeasurementIn(BaseModel):
    source_code: str
    external_id: str
    signal_code: str
    observed_at: datetime
    vehicle_count: int = Field(ge=0)
    period_seconds: int = Field(default=60, gt=0)
    occupancy: float = Field(default=0, ge=0, le=100)
    speed_kmh: float | None = Field(default=None, ge=0)
    @field_validator('observed_at')
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Нужно указать часовой пояс')
        return value

class ProgramIn(BaseModel):
    signal_code: str
    code: str
    name: str
    approved: bool = True
    current: bool = False

class EstimateIn(BaseModel):
    program_id: int
    scenario: str = 'base'
    cars_delay: float = Field(ge=0)
    buses_delay: float = Field(ge=0)
    trolley_delay: float = Field(ge=0)
    tram_delay: float = Field(ge=0)
    buses_count: int = Field(ge=0)
    trolley_count: int = Field(ge=0)
    tram_count: int = Field(ge=0)

class DecisionIn(BaseModel):
    signal_code: str
    program_id: int
    engineer: str = Field(min_length=2)
    reason: str = Field(min_length=3)

class IncidentIn(BaseModel):
    signal_code: str
    category: str
    description: str

class AppealIn(BaseModel):
    signal_code: str
    registry_code: str
    summary: str
    period_start: datetime
    period_end: datetime

class ConfirmIn(BaseModel):
    engineer: str

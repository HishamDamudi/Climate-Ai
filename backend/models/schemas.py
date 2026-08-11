from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date as Date


class District(BaseModel):
    district: str
    state: str
    region: str
    lat: float
    lon: float
    population: int


class WeatherRecord(BaseModel):
    date: str
    district: str
    state: str
    region: str
    lat: float
    lon: float
    max_temp: float
    humidity: float
    wind_kmph: float
    rainfall_mm: float
    heat_index: Optional[float] = None
    aqi: Optional[int] = None
    uv_index: Optional[float] = None


class PredictionRequest(BaseModel):
    district: str
    max_temp: float
    humidity: float
    wind_kmph: float
    rainfall_mm: float = 0.0


class PredictionResponse(BaseModel):
    district: str
    risk_level: str
    heatwave_probability: float
    expected_temp: float
    severity: str
    confidence_score: float
    explanation: str


class Alert(BaseModel):
    id: int
    level: str
    title: str
    description: str
    timestamp: str
    affected_areas: List[str]
    recommended_actions: List[str]


class UploadResult(BaseModel):
    filename: str
    rows_received: int
    rows_imported: int
    rows_rejected: int
    errors: List[str] = Field(default_factory=list)

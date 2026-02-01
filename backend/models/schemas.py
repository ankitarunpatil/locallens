from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Request Models
class SearchRequest(BaseModel):
    """Search for places"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    location: tuple[float, float] = Field(..., description="(latitude, longitude)")
    radius_km: float = Field(default=2.0, ge=0.1, le=50, description="Search radius in kilometers")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")

class NeighborhoodAnalysisRequest(BaseModel):
    """Analyze a neighborhood"""
    name: str = Field(..., min_length=1, max_length=100, description="Neighborhood name")
    city: str = Field(..., min_length=1, max_length=100, description="City name")

class RecommendationsRequest(BaseModel):
    """Get personalized recommendations"""
    preferences: List[str] = Field(..., min_items=1, max_items=10, description="User preferences")
    location: tuple[float, float] = Field(..., description="(latitude, longitude)")
    radius_km: float = Field(default=5.0, ge=0.1, le=50)
    limit: int = Field(default=10, ge=1, le=50)

class TourRequest(BaseModel):
    """Generate walking tour"""
    location: tuple[float, float] = Field(..., description="Starting point (latitude, longitude)")
    duration_hours: int = Field(default=2, ge=1, le=8, description="Tour duration in hours")
    interests: List[str] = Field(default=["food", "culture"], description="Tour themes")

class CompareRequest(BaseModel):
    """Compare neighborhoods"""
    neighborhoods: List[str] = Field(..., min_items=2, max_items=5)
    city: str = Field(..., min_length=1, max_length=100)

# Response Models
class PlaceResponse(BaseModel):
    """Place information"""
    id: Optional[int] = None
    osm_id: int
    name: str
    category: Optional[str] = None
    lat: float
    lon: float
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    similarity: Optional[float] = None

class NeighborhoodAnalysisResponse(BaseModel):
    """Neighborhood analysis result"""
    neighborhood: str
    city: str
    summary: str
    dining_score: int
    walkability_score: int
    highlights: List[str]
    best_for: str
    total_places: int
    categories: Dict[str, int]
    weather: Optional[Dict[str, Any]] = None

class RecommendationItem(BaseModel):
    """Single recommendation"""
    name: str
    category: Optional[str] = None
    reason: str
    lat: Optional[float] = None
    lon: Optional[float] = None

class RecommendationsResponse(BaseModel):
    """Recommendations result"""
    recommendations: List[RecommendationItem]
    total_found: int

class TourStop(BaseModel):
    """Stop on a walking tour"""
    order: int
    name: str
    category: str
    lat: float
    lon: float
    duration_mins: int
    why_visit: str

class TourResponse(BaseModel):
    """Walking tour result"""
    title: str
    total_distance_km: float
    total_duration: str
    stops: List[TourStop]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
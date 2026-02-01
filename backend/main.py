from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from models.schemas import (
    SearchRequest, NeighborhoodAnalysisRequest, RecommendationsRequest,
    TourRequest, CompareRequest, PlaceResponse, NeighborhoodAnalysisResponse,
    RecommendationsResponse, HealthResponse, RecommendationItem, TourResponse, TourStop
)
from services.embeddings_service import EmbeddingsService
from services.database_service import DatabaseService
from services.places_service import PlacesService
from services.weather_service import WeatherService
from services.llm_service import LLMService
from core.cache import cache

load_dotenv()

# Production configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Global service instances (initialized on startup)
embeddings: EmbeddingsService = None
db: DatabaseService = None
places_service: PlacesService = None
weather_service: WeatherService = None
llm_service: LLMService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global embeddings, db, places_service, weather_service, llm_service
    
    print("🚀 Starting LocalLens API...")
    print("=" * 60)
    
    try:
        embeddings = EmbeddingsService()
        db = DatabaseService()
        places_service = PlacesService()
        weather_service = WeatherService()
        llm_service = LLMService()
        
        print("=" * 60)
        print("✅ All services initialized successfully!")
        print(f"🌍 Environment: {ENVIRONMENT}")
        print("💰 Total cost: $0.00/month")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    yield
    
    # Shutdown
    print("👋 Shutting down LocalLens API...")
    cache.clear()

# Create FastAPI app
app = FastAPI(
    title="LocalLens API",
    description="🔍 AI-Powered Neighborhood Discovery - 100% FREE",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - single configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        os.getenv("FRONTEND_URL", ""),
        "*"  # Allow all in development
    ] if not IS_PRODUCTION else ["*"],  # Production: allow all (update with your domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all uncaught exceptions"""
    print(f"❌ Unhandled error: {exc}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else "An error occurred"
        }
    )

# Routes
@app.get("/", tags=["Root"])
async def root():
    """API information"""
    return {
        "app": "LocalLens API",
        "version": "1.0.0",
        "description": "AI-Powered Neighborhood Discovery",
        "environment": ENVIRONMENT,
        "cost": "$0.00/month",
        "stack": "100% FREE open source",
        "features": [
            "Semantic place search",
            "AI neighborhood analysis",
            "Walking tour generation",
            "Personalized recommendations",
            "Real-time weather"
        ],
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    
    services_status = {
        "embeddings": "ok" if embeddings else "error",
        "database": "ok" if db else "error",
        "places": "ok" if places_service else "error",
        "weather": "ok" if weather_service else "error",
        "llm": "ok" if llm_service else "error",
        "cache": "ok"
    }
    
    all_ok = all(s == "ok" for s in services_status.values())
    
    return {
        "status": "healthy" if all_ok else "degraded",
        "timestamp": datetime.now(),
        "services": services_status
    }

@app.post("/api/search", response_model=list[PlaceResponse], tags=["Search"])
async def search_places(request: SearchRequest):
    """
    Search for places (production uses keyword search, dev uses embeddings)
    """
    cache_key = f"search:{request.query}:{request.location}:{request.radius_km}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        print(f"📦 Cache hit for: {request.query}")
        return cached
    
    try:
        lat, lon = request.location
        
        # Fetch places from OpenStreetMap
        print(f"🔍 Searching OpenStreetMap for: {request.query}")
        osm_places = await places_service.search_nearby(
            lat=lat,
            lon=lon,
            radius=int(request.radius_km * 1000)
        )
        
        if not osm_places:
            return []
        
        # Simple keyword filtering (works in production without embeddings)
        query_lower = request.query.lower()
        query_keywords = query_lower.split()
        
        scored_places = []
        for place in osm_places:
            score = 0
            name_lower = place['name'].lower()
            category_lower = place.get('category', '').lower()
            cuisine = place.get('tags', {}).get('cuisine', '').lower()
            
            # Score based on keyword matches
            for keyword in query_keywords:
                if keyword in name_lower:
                    score += 3
                if keyword in category_lower:
                    score += 5
                if keyword in cuisine:
                    score += 4
            
            if score > 0:
                scored_places.append((score, place))
        
        # If no keyword matches, return all places
        if not scored_places:
            scored_places = [(1, p) for p in osm_places]
        
        # Sort by score and take top results
        scored_places.sort(reverse=True, key=lambda x: x[0])
        results = [p for _, p in scored_places[:request.limit]]
        
        # Convert to response format
        response = [
            PlaceResponse(
                id=None,
                osm_id=r['osm_id'],
                name=r['name'],
                category=r.get('category'),
                lat=float(r['lat']),
                lon=float(r['lon']),
                address=r.get('address'),
                phone=r.get('phone'),
                website=r.get('website'),
                tags=r.get('tags'),
                similarity=None
            )
            for r in results
        ]
        
        # Cache for 1 hour
        cache.set(cache_key, response, expire_seconds=3600)
        
        return response
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@app.post("/api/neighborhood/analyze", response_model=NeighborhoodAnalysisResponse, tags=["Analysis"])
async def analyze_neighborhood(request: NeighborhoodAnalysisRequest):
    """AI-powered neighborhood analysis"""
    cache_key = f"analysis:{request.name}:{request.city}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        print(f"📦 Cache hit for analysis: {request.name}")
        return cached
    
    try:
        # Geocode neighborhood
        location = await places_service.geocode(f"{request.name}, {request.city}")
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Neighborhood '{request.name}, {request.city}' not found"
            )
        
        lat, lon = location['lat'], location['lon']
        
        # Get places
        places = await places_service.search_nearby(
            lat=lat,
            lon=lon,
            radius=2000  # 2km radius
        )
        
        if not places:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No places found in this neighborhood"
            )
        
        # Get weather
        weather = await weather_service.get_current_weather(lat, lon)
        
        # AI analysis
        analysis = await llm_service.analyze_neighborhood(
            neighborhood=request.name,
            city=request.city,
            places_data=places,
            weather_data=weather
        )
        
        # Add metadata
        categories = {}
        for place in places:
            cat = place.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
        
        response = NeighborhoodAnalysisResponse(
            neighborhood=request.name,
            city=request.city,
            summary=analysis['summary'],
            dining_score=analysis['dining_score'],
            walkability_score=analysis['walkability_score'],
            highlights=analysis['highlights'],
            best_for=analysis['best_for'],
            total_places=len(places),
            categories=categories,
            weather=weather
        )
        
        # Cache for 24 hours
        cache.set(cache_key, response, expire_seconds=86400)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/recommendations", response_model=RecommendationsResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendationsRequest):
    """Get personalized place recommendations"""
    try:
        lat, lon = request.location
        
        # Get nearby places
        places = await places_service.search_nearby(
            lat=lat,
            lon=lon,
            radius=int(request.radius_km * 1000)
        )
        
        if not places:
            return RecommendationsResponse(recommendations=[], total_found=0)
        
        # Simple keyword filtering by preferences
        query_lower = " ".join(request.preferences).lower()
        scored_places = []
        
        for place in places:
            score = 0
            for pref in request.preferences:
                pref_lower = pref.lower()
                if pref_lower in place['name'].lower():
                    score += 2
                if pref_lower in place.get('category', '').lower():
                    score += 3
            if score > 0:
                scored_places.append((score, place))
        
        # Sort and take top matches
        scored_places.sort(reverse=True, key=lambda x: x[0])
        top_places = [p for _, p in scored_places[:request.limit * 2]]
        
        if not top_places:
            top_places = places[:request.limit * 2]
        
        # Get AI explanations
        ai_recs = await llm_service.generate_recommendations(
            preferences=request.preferences,
            places=top_places,
            limit=request.limit
        )
        
        # Build response
        recommendations = []
        for rec in ai_recs.get('recommendations', [])[:request.limit]:
            matching_place = next(
                (p for p in top_places if p['name'].lower() == rec['name'].lower()),
                top_places[0] if top_places else None
            )
            
            if matching_place:
                recommendations.append(
                    RecommendationItem(
                        name=rec['name'],
                        category=matching_place.get('category'),
                        reason=rec['reason'],
                        lat=float(matching_place['lat']),
                        lon=float(matching_place['lon'])
                    )
                )
        
        return RecommendationsResponse(
            recommendations=recommendations,
            total_found=len(top_places)
        )
        
    except Exception as e:
        print(f"❌ Recommendations error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendations failed: {str(e)}"
        )

@app.post("/api/tours/generate", response_model=TourResponse, tags=["Tours"])
async def generate_walking_tour(request: TourRequest):
    """Generate AI-powered walking tour"""
    try:
        lat, lon = request.location
        
        # Get places within walking distance
        places = await places_service.search_nearby(
            lat=lat,
            lon=lon,
            radius=1500,
            amenity_types=None
        )
        
        if not places:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No places found for tour"
            )
        
        # Filter by interests
        interest_keywords = {
            'food': ['restaurant', 'cafe', 'bakery', 'pub', 'bar', 'fast_food'],
            'culture': ['museum', 'theatre', 'gallery', 'library', 'cinema'],
            'history': ['monument', 'memorial'],
            'nature': ['park', 'garden', 'playground'],
            'shopping': ['shop', 'mall', 'market', 'boutique'],
            'nightlife': ['bar', 'pub', 'club', 'nightclub']
        }
        
        relevant_places = []
        for place in places:
            category = place.get('category', '').lower()
            for interest in request.interests:
                keywords = interest_keywords.get(interest.lower(), [interest.lower()])
                if any(kw in category for kw in keywords):
                    relevant_places.append(place)
                    break
        
        if not relevant_places:
            relevant_places = places[:20]
        
        # Use LLM to create tour
        places_text = "\n".join([
            f"- {p['name']} ({p.get('category', 'N/A')}) at ({p['lat']}, {p['lon']})"
            for p in relevant_places[:30]
        ])
        
        prompt = f"""Create a {request.duration_hours}-hour walking tour starting from ({lat}, {lon}).

User interests: {', '.join(request.interests)}

Available places nearby:
{places_text}

Create an optimal walking route with 4-6 stops. Return ONLY valid JSON (no markdown):
{{
    "title": "Descriptive tour name",
    "total_distance_km": 0.0,
    "total_duration": "2h 30m",
    "stops": [
        {{
            "order": 1,
            "name": "exact place name from list",
            "category": "category",
            "lat": 0.0,
            "lon": 0.0,
            "duration_mins": 30,
            "why_visit": "brief reason"
        }}
    ]
}}
"""
        
        response_text = await llm_service.generate(prompt, temperature=0.7)
        
        # Parse JSON
        import json
        import re
        
        json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        response_text = response_text.strip().strip('`').strip()
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
        
        try:
            tour_data = json.loads(response_text)
            
            stops = [
                TourStop(
                    order=stop.get('order', idx + 1),
                    name=stop['name'],
                    category=stop.get('category', 'unknown'),
                    lat=float(stop['lat']),
                    lon=float(stop['lon']),
                    duration_mins=stop.get('duration_mins', 30),
                    why_visit=stop.get('why_visit', 'Interesting place')
                )
                for idx, stop in enumerate(tour_data.get('stops', []))
            ]
            
            return TourResponse(
                title=tour_data.get('title', f"{request.duration_hours}-Hour Tour"),
                total_distance_km=float(tour_data.get('total_distance_km', 2.0)),
                total_duration=tour_data.get('total_duration', f"{request.duration_hours}h"),
                stops=stops
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠️ JSON parsing failed: {e}")
            
            # Fallback: create simple tour
            stops = [
                TourStop(
                    order=idx + 1,
                    name=place['name'],
                    category=place.get('category', 'unknown'),
                    lat=place['lat'],
                    lon=place['lon'],
                    duration_mins=30,
                    why_visit=f"Popular {place.get('category', 'place')}"
                )
                for idx, place in enumerate(relevant_places[:5])
            ]
            
            return TourResponse(
                title=f"{request.duration_hours}-Hour Tour",
                total_distance_km=2.0,
                total_duration=f"{request.duration_hours}h",
                stops=stops
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Tour generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tour generation failed: {str(e)}"
        )

@app.post("/api/neighborhoods/compare", tags=["Analysis"])
async def compare_neighborhoods(request: CompareRequest):
    """Compare multiple neighborhoods"""
    try:
        analyses = []
        
        for neighborhood in request.neighborhoods:
            try:
                analysis = await analyze_neighborhood(
                    NeighborhoodAnalysisRequest(
                        name=neighborhood,
                        city=request.city
                    )
                )
                analyses.append({
                    'neighborhood': neighborhood,
                    'analysis': analysis
                })
            except Exception as e:
                print(f"⚠️ Could not analyze {neighborhood}: {e}")
                continue
        
        if not analyses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not analyze any neighborhoods"
            )
        
        # Use LLM to create comparison
        comparison_text = "\n\n".join([
            f"{a['neighborhood']}:\n"
            f"- Summary: {a['analysis'].summary}\n"
            f"- Dining: {a['analysis'].dining_score}/10\n"
            f"- Walkability: {a['analysis'].walkability_score}/10"
            for a in analyses
        ])
        
        prompt = f"""Compare these neighborhoods in {request.city}:

{comparison_text}

Return ONLY valid JSON:
{{
    "summary": "Overall comparison",
    "best_for_dining": "neighborhood name",
    "best_for_walkability": "neighborhood name"
}}
"""
        
        response_text = await llm_service.generate(prompt, temperature=0.7)
        
        import json
        import re
        
        json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        try:
            comparison = json.loads(response_text.strip().strip('`').strip())
            comparison['neighborhoods'] = analyses
            return comparison
        except:
            return {
                'summary': f"Comparison of {len(analyses)} neighborhoods",
                'best_for_dining': analyses[0]['neighborhood'],
                'best_for_walkability': analyses[0]['neighborhood'],
                'neighborhoods': analyses
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Comparison error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )

@app.get("/api/cache/stats", tags=["Admin"])
async def cache_stats():
    """Get cache statistics"""
    return cache.get_stats()

@app.post("/api/cache/clear", tags=["Admin"])
async def clear_cache():
    """Clear all cache"""
    cache.clear()
    return {"message": "Cache cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
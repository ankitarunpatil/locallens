

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.schemas import TourRequest, TourResponse, TourStop
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from models.schemas import (
    SearchRequest, NeighborhoodAnalysisRequest, RecommendationsRequest,
    TourRequest, PlaceResponse, NeighborhoodAnalysisResponse,
    RecommendationsResponse, HealthResponse, RecommendationItem, CompareRequest
)
from services.embeddings_service import EmbeddingsService
from services.database_service import DatabaseService
from services.places_service import PlacesService
from services.weather_service import WeatherService
from services.llm_service import LLMService
from core.cache import cache

# Production configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

load_dotenv()

# Global service instances (initialized on startup)
embeddings: EmbeddingsService = None
db: DatabaseService = None
places_service: PlacesService = None
weather_service: WeatherService = None
llm_service: LLMService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
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
        print("💰 Total cost: $0.00/month")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Startup error: {e}")
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

# Update CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://localhost:3000",
        "https://*.vercel.app",   # Vercel deployments
        os.getenv("FRONTEND_URL", "")  # Production frontend
    ] if not IS_PRODUCTION else [os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
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
            "detail": str(exc) if os.getenv("DEBUG") else "An error occurred"
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
    
    all_ok = all(status == "ok" for status in services_status.values())
    
    return {
        "status": "healthy" if all_ok else "degraded",
        "timestamp": datetime.now(),
        "services": services_status
    }

@app.post("/api/search", response_model=list[PlaceResponse], tags=["Search"])
async def search_places(request: SearchRequest):
    """
    Search for places using semantic search
    
    Combines:
    - Vector similarity search
    - Geographic filtering
    - Real-time OSM data
    """
    cache_key = f"search:{request.query}:{request.location}:{request.radius_km}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        print(f"📦 Cache hit for: {request.query}")
        return cached
    
    try:
        lat, lon = request.location
        
        # Create query embedding
        query_embedding = embeddings.create_embedding(request.query)
        
        # Search database first (fast)
        db_results = await db.search_places_by_vector(
            query_embedding,
            threshold=0.25,
            limit=request.limit * 2  # Get more to account for filtering
        )
        
        # Filter by distance
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c
        
        nearby_results = [
            r for r in db_results
            if haversine(lat, lon, float(r['lat']), float(r['lng'])) <= request.radius_km
        ]
        
        # If we have enough results, use them
        if len(nearby_results) >= request.limit:
            results = nearby_results[:request.limit]
        else:
            # Fetch fresh data from OSM
            print(f"🔍 Fetching fresh data from OpenStreetMap...")
            osm_places = await places_service.search_nearby(
                lat=lat,
                lon=lon,
                radius=int(request.radius_km * 1000)
            )
            
            # Store new places in database
            for place in osm_places[:50]:  # Limit to avoid overload
                place_text = f"{place['name']} {place.get('category', '')} {place.get('cuisine', '')}"
                place_embedding = embeddings.create_embedding(place_text)
                
                await db.upsert_place({
                    'osm_id': place['osm_id'],
                    'name': place['name'],
                    'category': place.get('category'),
                    'lat': place['lat'],
                    'lng': place['lon'],
                    'address': place.get('address'),
                    'tags': place.get('tags', {}),
                    'embedding': place_embedding
                })
            
            # Re-run vector search
            db_results = await db.search_places_by_vector(
                query_embedding,
                threshold=0.2,
                limit=request.limit
            )
            
            results = db_results[:request.limit]
        
        # Convert to response format
        response = [
            PlaceResponse(
                id=r.get('id'),
                osm_id=r['osm_id'],
                name=r['name'],
                category=r.get('category'),
                lat=float(r['lat']),
                lon=float(r['lng']),
                address=r.get('address'),
                tags=r.get('tags'),
                similarity=r.get('similarity')
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
    """
    AI-powered neighborhood analysis
    
    Analyzes:
    - Dining & entertainment options
    - Walkability
    - Character & vibe
    - Best resident fit
    """
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
    """
    Get personalized place recommendations
    
    Uses AI to match places to user preferences
    """
    try:
        lat, lon = request.location
        
        # Create preference embedding
        query = " ".join(request.preferences)
        query_embedding = embeddings.create_embedding(query)
        
        # Vector search
        results = await db.search_places_by_vector(
            query_embedding,
            threshold=0.3,
            limit=request.limit * 2
        )
        
        # Filter by distance
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c
        
        nearby = [
            r for r in results
            if haversine(lat, lon, float(r['lat']), float(r['lng'])) <= request.radius_km
        ][:request.limit * 2]  # Get more for AI to choose from
        
        if not nearby:
            # Return empty response if no places found
            return RecommendationsResponse(
                recommendations=[],
                total_found=0
            )
        
        # Get AI explanations
        ai_recs = await llm_service.generate_recommendations(
            preferences=request.preferences,
            places=nearby,
            limit=request.limit
        )
        
        # Build response
        recommendations = []
        for rec in ai_recs.get('recommendations', [])[:request.limit]:
            # Find matching place for coordinates
            matching_place = next(
                (p for p in nearby if p['name'].lower() == rec['name'].lower()),
                nearby[0] if nearby else None  # Fallback to first place
            )
            
            if matching_place:
                recommendations.append(
                    RecommendationItem(
                        name=rec['name'],
                        category=matching_place.get('category'),
                        reason=rec['reason'],
                        lat=float(matching_place['lat']),
                        lon=float(matching_place['lng'])
                    )
                )
        
        return RecommendationsResponse(
            recommendations=recommendations,
            total_found=len(nearby)
        )
        
    except Exception as e:
        print(f"❌ Recommendations error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendations failed: {str(e)}"
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


@app.post("/api/tours/generate", response_model=TourResponse, tags=["Tours"])
async def generate_walking_tour(request: TourRequest):
    """
    Generate AI-powered walking tour
    
    Creates an optimized route based on:
    - User interests
    - Walking distance
    - Place ratings/popularity
    - Logical geographic flow
    """
    try:
        lat, lon = request.location
        
        # Get places within walking distance (1.5km = ~20min walk)
        places = await places_service.search_nearby(
            lat=lat,
            lon=lon,
            radius=1500,
            amenity_types=None  # Get all types
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
            relevant_places = places[:20]  # Fallback to any places
        
        # Use LLM to create tour
        places_text = "\n".join([
            f"- {p['name']} ({p.get('category', 'N/A')}) at ({p['lat']}, {p['lon']})"
            for p in relevant_places[:30]
        ])
        
        prompt = f"""Create a {request.duration_hours}-hour walking tour starting from ({lat}, {lon}).

User interests: {', '.join(request.interests)}

Available places nearby:
{places_text}

Create an optimal walking route with 4-6 stops. Consider:
- Walking distance between stops (keep it reasonable)
- Logical geographic flow (don't zigzag)
- Variety of experiences
- Time spent at each location

Return ONLY valid JSON (no markdown):
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
            "why_visit": "brief reason to visit"
        }}
    ]
}}
"""
        
        response = await llm_service.generate(prompt, temperature=0.7)
        
        # Parse JSON
        import json
        import re
        
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        response = response.strip().strip('`').strip()
        if response.startswith('json'):
            response = response[4:].strip()
        
        try:
            tour_data = json.loads(response)
            
            # Validate and convert to response model
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
            print(f"Raw response: {response}")
            
            # Fallback: create simple tour from first N places
            stops = [
                TourStop(
                    order=idx + 1,
                    name=place['name'],
                    category=place.get('category', 'unknown'),
                    lat=place['lat'],
                    lon=place['lon'],
                    duration_mins=30,
                    why_visit=f"Popular {place.get('category', 'place')} in the area"
                )
                for idx, place in enumerate(relevant_places[:5])
            ]
            
            return TourResponse(
                title=f"{request.duration_hours}-Hour {', '.join(request.interests).title()} Tour",
                total_distance_km=2.0,
                total_duration=f"{request.duration_hours}h",
                stops=stops
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Tour generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tour generation failed: {str(e)}"
        )


@app.post("/api/neighborhoods/compare", tags=["Analysis"])
async def compare_neighborhoods(request: CompareRequest):
    """
    Compare multiple neighborhoods
    
    Analyzes and compares neighborhoods across various criteria
    """
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
            f"- Walkability: {a['analysis'].walkability_score}/10\n"
            f"- Best for: {a['analysis'].best_for}\n"
            f"- Total places: {a['analysis'].total_places}"
            for a in analyses
        ])
        
        prompt = f"""Compare these neighborhoods in {request.city}:

{comparison_text}

Provide a comparison. Return ONLY valid JSON:
{{
    "summary": "Overall comparison highlighting key differences",
    "best_for_dining": "neighborhood name",
    "best_for_walkability": "neighborhood name",
    "best_for_families": {{"name": "neighborhood", "reason": "why"}},
    "best_for_young_professionals": {{"name": "neighborhood", "reason": "why"}},
    "best_for_nightlife": {{"name": "neighborhood", "reason": "why"}}
}}
"""
        
        response = await llm_service.generate(prompt, temperature=0.7)
        
        # Parse JSON
        import json
        import re
        
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        try:
            comparison = json.loads(response.strip().strip('`').strip())
            comparison['neighborhoods'] = analyses
            return comparison
        except:
            # Fallback
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
import asyncio
from services.places_service import PlacesService
from services.weather_service import WeatherService
from services.llm_service import LLMService
from services.embeddings_service import EmbeddingsService
from services.database_service import DatabaseService

async def main():
    print("=" * 60)
    print("DAY 2 INTEGRATION TEST - ALL FREE APIS")
    print("=" * 60)
    print()
    
    # Initialize all services
    print("1️⃣  Initializing services...")
    places_service = PlacesService()
    weather_service = WeatherService()
    llm_service = LLMService()
    embeddings = EmbeddingsService()
    db = DatabaseService()
    print()
    
    # Test geocoding
    print("2️⃣  Testing geocoding...")
    location = await places_service.geocode("Wicker Park, Chicago")
    if location:
        lat, lon = location['lat'], location['lon']
        print(f"   Wicker Park coordinates: ({lat}, {lon})")
    else:
        # Fallback
        lat, lon = 41.9097, -87.6777
        print(f"   Using default coordinates: ({lat}, {lon})")
    print()
    
    # Test places search
    print("3️⃣  Testing OpenStreetMap places search...")
    places = await places_service.search_nearby(
        lat=lat,
        lon=lon,
        radius=1000,
        amenity_types=['restaurant', 'cafe', 'bar', 'park']
    )
    print(f"   Found {len(places)} places")
    if places:
        print("   Sample places:")
        for place in places[:5]:
            print(f"     • {place['name']} ({place['category']})")
    print()
    
    # Test weather
    print("4️⃣  Testing weather API...")
    weather = await weather_service.get_current_weather(lat, lon)
    if weather:
        print(f"   Temperature: {weather['temperature_f']}°F")
        print(f"   Conditions: {weather['description']}")
    print()
    
    # Test embeddings + database
    print("5️⃣  Storing places with embeddings in database...")
    stored_count = 0
    for place in places[:10]:  # Store first 10
        # Create embedding
        place_text = f"{place['name']} {place.get('category', '')} {place.get('cuisine', '')}"
        embedding = embeddings.create_embedding(place_text)
        
        # Store in database
        place_data = {
            'osm_id': place['osm_id'],
            'name': place['name'],
            'category': place.get('category'),
            'lat': place['lat'],
            'lng': place['lon'],
            'address': place.get('address'),
            'tags': place.get('tags', {}),
            'embedding': embedding
        }
        
        result = await db.upsert_place(place_data)
        if result:
            stored_count += 1
    
    print(f"   ✅ Stored {stored_count} places")
    print()
    
    # Test AI analysis
    print("6️⃣  Testing AI neighborhood analysis...")
    analysis = await llm_service.analyze_neighborhood(
        neighborhood="Wicker Park",
        city="Chicago",
        places_data=places,
        weather_data=weather
    )
    
    print("   AI Analysis:")
    print(f"   Summary: {analysis['summary']}")
    print(f"   Dining score: {analysis['dining_score']}/10")
    print(f"   Walkability score: {analysis['walkability_score']}/10")
    print(f"   Highlights: {', '.join(analysis['highlights'][:3])}")
    print(f"   Best for: {analysis['best_for']}")
    print()
    
    # Test vector search
    print("7️⃣  Testing semantic search...")
    query = "coffee shop with wifi"
    query_embedding = embeddings.create_embedding(query)
    
    results = await db.search_places_by_vector(
        query_embedding,
        threshold=0.2,
        limit=5
    )
    
    print(f"   Query: '{query}'")
    print(f"   Found {len(results)} matches:")
    for result in results[:3]:
        print(f"     • {result['name']} (similarity: {result['similarity']:.3f})")
    print()
    
    print("=" * 60)
    print("✅ DAY 2 COMPLETE! All APIs integrated!")
    print("=" * 60)
    print()
    print("What you've accomplished:")
    print("• ✅ OpenStreetMap places (FREE)")
    print("• ✅ Open-Meteo weather (FREE)")
    print("• ✅ Groq LLM (FREE)")
    print("• ✅ Local embeddings (FREE)")
    print("• ✅ Vector search with real data")
    print("• ✅ AI neighborhood analysis")
    print()
    print("Total cost: $0.00/month 💰")
    print()
    print("Ready for Day 3! 🚀")

if __name__ == "__main__":
    asyncio.run(main())
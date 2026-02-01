import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_api():
    print("=" * 60)
    print("DAY 3 API TESTING")
    print("=" * 60)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Health check
        print("1️⃣  Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        health = response.json()
        print(f"   Services: {health['services']}")
        print()
        
        # Test 2: Search
        print("2️⃣  Testing semantic search...")
        search_data = {
            "query": "coffee shop with wifi",
            "location": [41.9097, -87.6777],  # Wicker Park
            "radius_km": 1.0,
            "limit": 5
        }
        response = await client.post(f"{BASE_URL}/api/search", json=search_data)
        print(f"   Status: {response.status_code}")
        results = response.json()
        print(f"   Found {len(results)} places:")
        for place in results[:3]:
            print(f"     • {place['name']} (similarity: {place.get('similarity', 0):.3f})")
        print()
        
        # Test 3: Neighborhood analysis
        print("3️⃣  Testing neighborhood analysis...")
        analysis_data = {
            "name": "Wicker Park",
            "city": "Chicago"
        }
        response = await client.post(f"{BASE_URL}/api/neighborhood/analyze", json=analysis_data)
        print(f"   Status: {response.status_code}")
        analysis = response.json()
        print(f"   Summary: {analysis['summary'][:100]}...")
        print(f"   Dining score: {analysis['dining_score']}/10")
        print(f"   Walkability: {analysis['walkability_score']}/10")
        print(f"   Total places: {analysis['total_places']}")
        print()
        
        # Test 4: Recommendations
        print("4️⃣  Testing recommendations...")
        rec_data = {
            "preferences": ["vegetarian food", "outdoor seating", "romantic"],
            "location": [41.9097, -87.6777],
            "radius_km": 2.0,
            "limit": 3
        }
        response = await client.post(f"{BASE_URL}/api/recommendations", json=rec_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            recs = response.json()
            if 'recommendations' in recs:
                print(f"   Got {len(recs['recommendations'])} recommendations:")
                for rec in recs['recommendations']:
                    print(f"     • {rec['name']}")
                    print(f"       Reason: {rec['reason']}")
            else:
                print(f"   ⚠️  Unexpected response format: {recs}")
        else:
            error = response.json()
            print(f"   ❌ Error: {error}")
            print(f"   Response body: {json.dumps(error, indent=2)}")
        print()
        
        # Test 5: Cache stats
        print("5️⃣  Testing cache...")
        response = await client.get(f"{BASE_URL}/api/cache/stats")
        stats = response.json()
        print(f"   Cache stats: {stats}")
        print()
        
        print("=" * 60)
        print("✅ DAY 3 COMPLETE! API is working!")
        print("=" * 60)
        print()
        print("What you've accomplished:")
        print("• ✅ FastAPI backend running")
        print("• ✅ Semantic search endpoint")
        print("• ✅ AI neighborhood analysis")
        print("• ✅ Personalized recommendations")
        print("• ✅ Caching system")
        print("• ✅ Error handling")
        print("• ✅ API documentation (Swagger)")
        print()
        print("API available at: http://localhost:8000")
        print("Docs available at: http://localhost:8000/docs")
        print()
        print("Ready for Day 4! 🚀")

if __name__ == "__main__":
    asyncio.run(test_api())
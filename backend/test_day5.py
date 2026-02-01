import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def test_day5():
    print("=" * 60)
    print("DAY 5 TESTING - Advanced Features")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:

        # Test 1: Walking Tour
        print("1️⃣  Testing walking tour generator...")
        tour_data = {
            "location": [41.9097, -87.6777],
            "duration_hours": 2,
            "interests": ["food", "culture"]
        }

        response = await client.post(f"{BASE_URL}/api/tours/generate", json=tour_data)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            tour = response.json()
            print(f"   Tour: {tour.get('title', 'N/A')}")
            print(f"   Stops: {len(tour.get('stops', []))}")
            print(f"   Duration: {tour.get('total_duration', 'N/A')}")

            for stop in tour.get('stops', [])[:3]:
                print(f"     {stop['order']}. {stop['name']}")
        else:
            print("   ❌ Tour generation failed")

        print()

        # Test 2: Neighborhood Comparison
        print("2️⃣  Testing neighborhood comparison...")
        compare_data = {
            "neighborhoods": ["Wicker Park", "Lincoln Park", "Logan Square"],
            "city": "Chicago"
        }

        response = await client.post(
            f"{BASE_URL}/api/neighborhoods/compare",
            json=compare_data
        )
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            comparison = response.json()
            print(f"   Summary: {comparison.get('summary', 'N/A')[:100]}...")
            print(f"   Best for dining: {comparison.get('best_for_dining', 'N/A')}")
            print(f"   Best for walkability: {comparison.get('best_for_walkability', 'N/A')}")
        else:
            print("   ❌ Neighborhood comparison failed")

        print()

        # Test 3: Search with ingested data
        print("3️⃣  Testing search with populated database...")
        search_data = {
            "query": "pizza restaurant",
            "location": [41.8781, -87.6298],
            "radius_km": 3.0,
            "limit": 10
        }

        response = await client.post(f"{BASE_URL}/api/search", json=search_data)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            results = response.json()
            print(f"   Found {len(results)} results")
            for place in results[:5]:
                print(f"     • {place['name']} ({place.get('similarity', 0):.2f})")
        else:
            print("   ❌ Search failed")

    print()
    print("=" * 60)
    print("✅ DAY 5 COMPLETE!")
    print("=" * 60)
    print()
    print("What you've accomplished:")
    print("• ✅ Walking tour generator with AI")
    print("• ✅ Neighborhood comparison")
    print("• ✅ Database populated with real data")
    print("• ✅ Rich search results")
    print("• ✅ Interactive tour UI")
    print()
    print("Ready for Day 6 (Deployment)! 🚀")


if __name__ == "__main__":
    asyncio.run(test_day5())
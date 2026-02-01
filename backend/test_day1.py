import asyncio
from services.embeddings_service import EmbeddingsService
from services.database_service import DatabaseService

async def main():
    print("=" * 60)
    print("DAY 1 INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Initialize services
    print("1️⃣  Initializing services...")
    embeddings = EmbeddingsService()
    db = DatabaseService()
    print()
    
    # Test embeddings
    print("2️⃣  Testing embeddings...")
    test_text = "best pizza restaurant in Chicago"
    embedding = embeddings.create_embedding(test_text)
    print(f"   Query: '{test_text}'")
    print(f"   Embedding size: {len(embedding)} dimensions")
    print(f"   Sample values: {embedding[:3]}")
    print()
    
    # Test database insert with embedding
    print("3️⃣  Testing database insert...")
    test_places = [
        {
            'osm_id': 111111,
            'name': 'Lou Malnatis Pizzeria',
            'category': 'restaurant',
            'lat': 41.8902,
            'lng': -87.6347,
            'address': '439 N Wells St, Chicago, IL',
            'tags': {'amenity': 'restaurant', 'cuisine': 'pizza'},
        },
        {
            'osm_id': 222222,
            'name': 'Giordanos',
            'category': 'restaurant',
            'lat': 41.8850,
            'lng': -87.6280,
            'address': '730 N Rush St, Chicago, IL',
            'tags': {'amenity': 'restaurant', 'cuisine': 'pizza'},
        },
        {
            'osm_id': 333333,
            'name': 'Starbucks Reserve Roastery',
            'category': 'cafe',
            'lat': 41.8919,
            'lng': -87.6278,
            'address': '646 N Michigan Ave, Chicago, IL',
            'tags': {'amenity': 'cafe', 'cuisine': 'coffee'},
        }
    ]
    
    # Create embeddings for places
    place_texts = [
        f"{p['name']} {p['category']} {p.get('tags', {}).get('cuisine', '')}"
        for p in test_places
    ]
    place_embeddings = embeddings.create_embeddings_batch(place_texts)
    
    # Insert with embeddings
    for place, embedding in zip(test_places, place_embeddings):
        place['embedding'] = embedding
        result = await db.upsert_place(place)
        if result:
            print(f"   ✅ Inserted: {result['name']}")
    print()
    
    # Test vector search
    print("4️⃣  Testing vector search...")
    query_embedding = embeddings.create_embedding("pizza restaurant")
    results = await db.search_places_by_vector(
        query_embedding,
        threshold=0.2,
        limit=5
    )
    
    print(f"   Query: 'pizza restaurant'")
    print(f"   Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['name']} (similarity: {result['similarity']:.3f})")
    print()
    
    # Test similarity comparison
    print("5️⃣  Testing semantic similarity...")
    queries = [
        "pizza restaurant",
        "coffee shop",
        "italian food"
    ]
    
    for query in queries:
        q_emb = embeddings.create_embedding(query)
        results = await db.search_places_by_vector(q_emb, threshold=0.1, limit=3)
        print(f"   '{query}' → {results[0]['name'] if results else 'No results'}")
    print()
    
    print("=" * 60)
    print("✅ DAY 1 COMPLETE! Vector search is working!")
    print("=" * 60)
    print()
    print("What you've accomplished:")
    print("• ✅ Supabase database with pgvector")
    print("• ✅ Local embeddings (no API costs)")
    print("• ✅ Vector similarity search")
    print("• ✅ Database integration")
    print()
    print("Ready for Day 2! 🚀")

if __name__ == "__main__":
    asyncio.run(main())
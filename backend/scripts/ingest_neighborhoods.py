import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import services
sys.path.append(str(Path(__file__).parent.parent))

from services.places_service import PlacesService
from services.embeddings_service import EmbeddingsService
from services.database_service import DatabaseService
from dotenv import load_dotenv

load_dotenv()

async def ingest_neighborhood(
    name: str,
    city: str,
    lat: float,
    lon: float,
    db: DatabaseService,
    places_service: PlacesService,
    embeddings: EmbeddingsService
):
    """
    Ingest all data for a neighborhood
    
    1. Fetch places from OpenStreetMap
    2. Generate embeddings for each place
    3. Store in Supabase database
    """
    
    print(f"\n{'='*60}")
    print(f"🔍 Ingesting: {name}, {city}")
    print(f"   Coordinates: ({lat}, {lon})")
    print(f"{'='*60}")
    
    try:
        # Fetch places from OpenStreetMap
        print(f"📍 Fetching places from OpenStreetMap...")
        places = await places_service.search_nearby(
            lat=lat,
            lon=lon,
            radius=2000  # 2km radius
        )
        
        print(f"   ✅ Found {len(places)} places")
        
        if not places:
            print(f"   ⚠️  No places found, skipping")
            return
        
        # Generate embeddings in batch (faster)
        print(f"🧠 Generating embeddings...")
        place_texts = [
            f"{p['name']} {p.get('category', '')} {p.get('cuisine', '')} {p.get('address', '')}"
            for p in places
        ]
        
        embeddings_list = embeddings.create_embeddings_batch(place_texts)
        print(f"   ✅ Generated {len(embeddings_list)} embeddings")
        
        # Store in database
        print(f"💾 Storing in database...")
        stored_count = 0
        failed_count = 0
        
        for place, embedding in zip(places, embeddings_list):
            try:
                place_data = {
                    'osm_id': place['osm_id'],
                    'name': place['name'],
                    'category': place.get('category'),
                    'lat': place['lat'],
                    'lng': place['lon'],
                    'address': place.get('address'),
                    'phone': place.get('phone'),
                    'website': place.get('website'),
                    'tags': place.get('tags', {}),
                    'embedding': embedding
                }
                
                result = await db.upsert_place(place_data)
                if result:
                    stored_count += 1
                    if stored_count % 10 == 0:
                        print(f"   ... {stored_count} places stored")
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"   ⚠️  Error storing {place['name']}: {e}")
                failed_count += 1
                continue
        
        print(f"   ✅ Successfully stored: {stored_count}")
        if failed_count > 0:
            print(f"   ⚠️  Failed: {failed_count}")
        
        # Store neighborhood record
        print(f"📝 Creating neighborhood record...")
        neighborhood_text = f"{name} {city} neighborhood"
        neighborhood_embedding = embeddings.create_embedding(neighborhood_text)
        
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            
            supabase.table('neighborhoods').upsert({
                'name': name,
                'city': city,
                'center_lat': lat,
                'center_lng': lon,
                'embedding': neighborhood_embedding
            }, on_conflict='name,city').execute()
            
            print(f"   ✅ Neighborhood record created")
            
        except Exception as e:
            print(f"   ⚠️  Error creating neighborhood record: {e}")
        
        print(f"\n✅ {name} ingestion complete!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Error ingesting {name}: {e}")
        print(f"{'='*60}\n")


async def main():
    """
    Ingest data for multiple neighborhoods
    
    Customize this list with your city's neighborhoods!
    """
    
    print("\n" + "="*60)
    print("🚀 LOCALLENS DATA INGESTION")
    print("="*60)
    
    # Initialize services
    print("\n📦 Initializing services...")
    db = DatabaseService()
    places_service = PlacesService()
    embeddings = EmbeddingsService()
    print("✅ Services ready\n")
    
    # Define neighborhoods to ingest
    # Format: (name, city, lat, lon)
    neighborhoods = [
        # Chicago neighborhoods
        ("Wicker Park", "Chicago", 41.9097, -87.6777),
        ("Lincoln Park", "Chicago", 41.9217, -87.6571),
        ("Logan Square", "Chicago", 41.9289, -87.7073),
        ("The Loop", "Chicago", 41.8781, -87.6298),
        ("River North", "Chicago", 41.8919, -87.6278),
        ("Old Town", "Chicago", 41.9122, -87.6354),
        ("Bucktown", "Chicago", 41.9203, -87.6838),
        ("Lakeview", "Chicago", 41.9403, -87.6548),
        
        # Add your city's neighborhoods here!
        # ("Greenwich Village", "New York", 40.7336, -74.0027),
        # ("SoHo", "New York", 40.7233, -74.0030),
        # ("Mission District", "San Francisco", 37.7599, -122.4148),
        # ("Capitol Hill", "Seattle", 47.6205, -122.3212),
        # ("Downtown", "Austin", 30.2672, -97.7431),
    ]
    
    print(f"📋 Will ingest {len(neighborhoods)} neighborhoods\n")
    
    # Ingest each neighborhood
    for idx, (name, city, lat, lon) in enumerate(neighborhoods, 1):
        print(f"\n[{idx}/{len(neighborhoods)}] Processing {name}...")
        
        await ingest_neighborhood(
            name=name,
            city=city,
            lat=lat,
            lon=lon,
            db=db,
            places_service=places_service,
            embeddings=embeddings
        )
        
        # Rate limiting - be nice to OpenStreetMap
        if idx < len(neighborhoods):
            print(f"⏳ Waiting 3 seconds before next neighborhood...")
            await asyncio.sleep(3)
    
    print("\n" + "="*60)
    print("🎉 DATA INGESTION COMPLETE!")
    print("="*60)
    print(f"\nIngested {len(neighborhoods)} neighborhoods")
    print("Your LocalLens database is now populated with real data!")
    print("\nNext steps:")
    print("1. Restart your backend: uvicorn main:app --reload")
    print("2. Try searching and analyzing neighborhoods")
    print("3. Enjoy your fully functional LocalLens! 🚀")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
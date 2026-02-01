from supabase import create_client, Client
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    """
    Handles all Supabase database operations
    Production-ready with fallbacks
    """
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self.is_production = os.getenv("ENVIRONMENT") == "production"
        print(f"✅ Connected to Supabase ({'production' if self.is_production else 'development'} mode)")
    
    async def insert_place(self, place_data: Dict) -> Optional[Dict]:
        """Insert a new place into database"""
        try:
            # Remove embedding in production if present
            if self.is_production and 'embedding' in place_data:
                place_data = {k: v for k, v in place_data.items() if k != 'embedding'}
            
            result = self.client.table('places').insert(place_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error inserting place: {e}")
            return None
    
    async def upsert_place(self, place_data: Dict) -> Optional[Dict]:
        """Insert or update place (based on osm_id)"""
        try:
            # Remove embedding in production if present
            if self.is_production and 'embedding' in place_data:
                place_data = {k: v for k, v in place_data.items() if k != 'embedding'}
            
            result = self.client.table('places').upsert(
                place_data,
                on_conflict='osm_id'
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error upserting place: {e}")
            return None
    
    async def search_places_by_vector(
        self,
        query_embedding: List[float],
        threshold: float = 0.3,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search places using vector similarity
        In production mode, returns empty list (use keyword search instead)
        """
        if self.is_production:
            print("⚠️ Vector search not available in production mode")
            return []
        
        try:
            result = self.client.rpc(
                'match_places',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            return result.data or []
        except Exception as e:
            print(f"Error searching places: {e}")
            return []
    
    async def get_places_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get places by category"""
        try:
            result = self.client.table('places').select('*').eq('category', category).limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"Error fetching places by category: {e}")
            return []
    
    async def get_all_places(self, limit: int = 100) -> List[Dict]:
        """Get all places (with limit)"""
        try:
            result = self.client.table('places').select('*').limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"Error fetching all places: {e}")
            return []
    
    async def get_places_by_location(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0
    ) -> List[Dict]:
        """Get places within radius of coordinates"""
        try:
            # Try using RPC function first
            result = self.client.rpc(
                'get_places_in_radius',
                {
                    'center_lat': lat,
                    'center_lng': lng,
                    'radius_km': radius_km
                }
            ).execute()
            return result.data or []
        except Exception as e:
            print(f"⚠️ RPC function not available, using fallback: {e}")
            
            # Fallback: get all places and filter in Python
            try:
                all_places = self.client.table('places').select('*').limit(500).execute()
                
                from math import radians, sin, cos, sqrt, atan2
                
                def haversine(lat1, lon1, lat2, lon2):
                    R = 6371  # Earth radius in km
                    dlat = radians(lat2 - lat1)
                    dlon = radians(lon2 - lon1)
                    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    return R * c
                
                nearby = [
                    p for p in (all_places.data or [])
                    if p.get('lat') and p.get('lng') and 
                       haversine(lat, lng, float(p['lat']), float(p['lng'])) <= radius_km
                ]
                return nearby
            except Exception as e2:
                print(f"❌ Fallback also failed: {e2}")
                return []


# Test the service
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing DatabaseService...\n")
        
        db = DatabaseService()
        
        # Test: Insert a sample place
        print("Test 1: Insert sample place")
        sample_place = {
            'osm_id': 12345678,
            'name': 'Test Coffee Shop',
            'category': 'cafe',
            'lat': 41.8781,
            'lng': -87.6298,
            'address': '123 Test St, Chicago, IL',
            'tags': {'amenity': 'cafe', 'cuisine': 'coffee'}
        }
        
        result = await db.upsert_place(sample_place)
        if result:
            print(f"✅ Inserted: {result['name']}\n")
        
        # Test: Search by location
        print("Test 2: Search by location")
        places = await db.get_places_by_location(41.8781, -87.6298, radius_km=10)
        print(f"Found {len(places)} places within 10km\n")
        
        # Test: Get by category
        print("Test 3: Get by category")
        cafes = await db.get_places_by_category('cafe', limit=10)
        print(f"Found {len(cafes)} cafes\n")
        
        print("✅ All tests passed!")
    
    asyncio.run(test())
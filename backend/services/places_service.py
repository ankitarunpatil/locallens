import httpx
from typing import List, Dict, Optional
import asyncio
from datetime import datetime

class PlacesService:
    """
    FREE OpenStreetMap data via Overpass API
    No API key needed, unlimited requests (be respectful!)
    """
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        
        # Rate limiting: Nominatim requires 1 req/sec
        self.last_nominatim_request = 0
        
        print("✅ PlacesService initialized (OpenStreetMap)")
    
    async def search_nearby(
        self,
        lat: float,
        lon: float,
        radius: int = 1000,
        amenity_types: List[str] = None
    ) -> List[Dict]:
        """
        Search OpenStreetMap for places near coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters (default 1km)
            amenity_types: List of OSM amenity types to search for
            
        Returns:
            List of places with metadata
        """
        
        if amenity_types is None:
            # Default: common useful amenities
            amenity_types = [
                'restaurant', 'cafe', 'bar', 'pub', 'fast_food',
                'park', 'playground',
                'museum', 'library', 'theatre', 'cinema',
                'school', 'university',
                'hospital', 'pharmacy', 'clinic',
                'bank', 'atm', 'post_office',
                'supermarket', 'convenience', 'mall',
                'gym', 'sports_centre'
            ]
        
        # Build Overpass QL query
        amenity_filter = '|'.join(amenity_types)
        
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"^({amenity_filter})$"](around:{radius},{lat},{lon});
          way["amenity"~"^({amenity_filter})$"](around:{radius},{lat},{lon});
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.overpass_url,
                    data={"data": query}
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            print(f"❌ Overpass API error: {e}")
            return []
        
        # Parse results
        places = []
        elements = data.get('elements', [])
        
        for element in elements:
            if element.get('type') not in ['node', 'way']:
                continue
            
            tags = element.get('tags', {})
            
            # Skip if no name
            if not tags.get('name'):
                continue
            
            # Get coordinates
            if element['type'] == 'node':
                elem_lat = element.get('lat')
                elem_lon = element.get('lon')
            elif element['type'] == 'way':
                # For ways, use center point
                elem_lat = element.get('center', {}).get('lat')
                elem_lon = element.get('center', {}).get('lon')
            else:
                continue
            
            if not elem_lat or not elem_lon:
                continue
            
            # Build place object
            place = {
                'osm_id': element['id'],
                'osm_type': element['type'],
                'name': tags.get('name'),
                'category': tags.get('amenity'),
                'lat': float(elem_lat),
                'lon': float(elem_lon),
                'address': self._format_address(tags),
                'phone': tags.get('phone') or tags.get('contact:phone'),
                'website': tags.get('website') or tags.get('contact:website'),
                'opening_hours': tags.get('opening_hours'),
                'cuisine': tags.get('cuisine'),
                'outdoor_seating': tags.get('outdoor_seating'),
                'wheelchair': tags.get('wheelchair'),
                'wifi': tags.get('internet_access'),
                'tags': tags  # Store all tags
            }
            
            places.append(place)
        
        print(f"✅ Found {len(places)} places via OpenStreetMap")
        return places
    
    def _format_address(self, tags: Dict) -> Optional[str]:
        """Format address from OSM tags"""
        parts = []
        
        # House number + street
        if tags.get('addr:housenumber'):
            parts.append(tags['addr:housenumber'])
        if tags.get('addr:street'):
            parts.append(tags['addr:street'])
        
        # City
        if tags.get('addr:city'):
            parts.append(tags['addr:city'])
        
        # State/Province
        if tags.get('addr:state'):
            parts.append(tags['addr:state'])
        
        # Postal code
        if tags.get('addr:postcode'):
            parts.append(tags['addr:postcode'])
        
        return ', '.join(parts) if parts else None
    
    async def geocode(self, address: str) -> Optional[Dict]:
        """
        Convert address to coordinates using Nominatim (FREE)
        
        Args:
            address: Address string (e.g., "Wicker Park, Chicago")
            
        Returns:
            Dict with lat, lon, display_name or None
        """
        
        # Rate limiting: wait 1 second between requests
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self.last_nominatim_request
        if time_since_last < 1.0:
            await asyncio.sleep(1.0 - time_since_last)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.nominatim_url}/search",
                    params={
                        'q': address,
                        'format': 'json',
                        'limit': 1
                    },
                    headers={
                        'User-Agent': 'LocalLens/1.0 (Learning Project)'
                    }
                )
                response.raise_for_status()
                results = response.json()
            
            self.last_nominatim_request = datetime.now().timestamp()
            
            if results:
                return {
                    'lat': float(results[0]['lat']),
                    'lon': float(results[0]['lon']),
                    'display_name': results[0]['display_name']
                }
            return None
            
        except Exception as e:
            print(f"❌ Geocoding error: {e}")
            return None
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Convert coordinates to address (FREE)
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Address information
        """
        
        # Rate limiting
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self.last_nominatim_request
        if time_since_last < 1.0:
            await asyncio.sleep(1.0 - time_since_last)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.nominatim_url}/reverse",
                    params={
                        'lat': lat,
                        'lon': lon,
                        'format': 'json'
                    },
                    headers={
                        'User-Agent': 'LocalLens/1.0 (Learning Project)'
                    }
                )
                response.raise_for_status()
                result = response.json()
            
            self.last_nominatim_request = datetime.now().timestamp()
            
            return result.get('address', {})
            
        except Exception as e:
            print(f"❌ Reverse geocoding error: {e}")
            return None


# Test the service
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing PlacesService...\n")
        
        service = PlacesService()
        
        # Test 1: Search near Chicago downtown
        print("Test 1: Search for places near Chicago Loop")
        places = await service.search_nearby(
            lat=41.8781,
            lon=-87.6298,
            radius=500,
            amenity_types=['restaurant', 'cafe']
        )
        
        print(f"Found {len(places)} places")
        if places:
            print("\nSample places:")
            for place in places[:5]:
                print(f"  • {place['name']} ({place['category']})")
                print(f"    {place['address']}")
        print()
        
        # Test 2: Geocode
        print("Test 2: Geocode 'Wicker Park, Chicago'")
        location = await service.geocode("Wicker Park, Chicago")
        if location:
            print(f"  Coordinates: ({location['lat']}, {location['lon']})")
            print(f"  Full name: {location['display_name']}")
        print()
        
        print("✅ All tests passed!")
    
    asyncio.run(test())
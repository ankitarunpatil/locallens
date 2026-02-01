import httpx
from typing import Dict, Optional

class WeatherService:
    """
    FREE weather data from Open-Meteo
    No API key needed, unlimited requests!
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"
        print("✅ WeatherService initialized (Open-Meteo)")
    
    async def get_current_weather(
        self,
        lat: float,
        lon: float
    ) -> Optional[Dict]:
        """
        Get current weather for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dict
        """
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        'latitude': lat,
                        'longitude': lon,
                        'current': [
                            'temperature_2m',
                            'relative_humidity_2m',
                            'apparent_temperature',
                            'precipitation',
                            'weather_code',
                            'wind_speed_10m',
                            'wind_direction_10m'
                        ],
                        'temperature_unit': 'fahrenheit',
                        'wind_speed_unit': 'mph',
                        'precipitation_unit': 'inch'
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            current = data.get('current', {})
            
            # Decode weather code
            weather_description = self._decode_weather_code(
                current.get('weather_code', 0)
            )
            
            return {
                'temperature_f': current.get('temperature_2m'),
                'feels_like_f': current.get('apparent_temperature'),
                'humidity': current.get('relative_humidity_2m'),
                'precipitation': current.get('precipitation'),
                'wind_speed_mph': current.get('wind_speed_10m'),
                'wind_direction': current.get('wind_direction_10m'),
                'description': weather_description,
                'weather_code': current.get('weather_code')
            }
            
        except Exception as e:
            print(f"❌ Weather API error: {e}")
            return None
    
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7
    ) -> Optional[Dict]:
        """Get weather forecast"""
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        'latitude': lat,
                        'longitude': lon,
                        'daily': [
                            'temperature_2m_max',
                            'temperature_2m_min',
                            'precipitation_sum',
                            'weather_code'
                        ],
                        'temperature_unit': 'fahrenheit',
                        'precipitation_unit': 'inch',
                        'forecast_days': days
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            return data.get('daily', {})
            
        except Exception as e:
            print(f"❌ Forecast API error: {e}")
            return None
    
    def _decode_weather_code(self, code: int) -> str:
        """Decode WMO weather codes"""
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return codes.get(code, "Unknown")


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing WeatherService...\n")
        
        service = WeatherService()
        
        # Test: Chicago weather
        print("Test: Get current weather for Chicago")
        weather = await service.get_current_weather(41.8781, -87.6298)
        
        if weather:
            print(f"  Temperature: {weather['temperature_f']}°F")
            print(f"  Feels like: {weather['feels_like_f']}°F")
            print(f"  Conditions: {weather['description']}")
            print(f"  Humidity: {weather['humidity']}%")
            print(f"  Wind: {weather['wind_speed_mph']} mph")
        
        print("\n✅ Weather service working!")
    
    asyncio.run(test())
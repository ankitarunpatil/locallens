from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  Groq not installed. Run: pip install groq")

class LLMService:
    """
    FREE LLM using Groq API (Llama 3.3)
    30 requests/minute on free tier
    """
    
    def __init__(self):
        if not GROQ_AVAILABLE:
            raise Exception("Groq not available. Install with: pip install groq")
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        
        self.client = Groq(api_key=api_key)
        # Updated to currently supported model (as of Jan 2025)
        self.model = "llama-3.3-70b-versatile"  # Fast, high quality, latest
        
        print(f"✅ LLM Service initialized (Groq - {self.model})")
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate text completion
        
        Args:
            prompt: User prompt
            system: System message (optional)
            temperature: 0-1, higher = more creative
            max_tokens: Max response length
            
        Returns:
            Generated text
        """
        
        messages = []
        
        if system:
            messages.append({
                "role": "system",
                "content": system
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return f"Error generating response: {e}"
    
    async def analyze_neighborhood(
        self,
        neighborhood: str,
        city: str,
        places_data: List[Dict],
        weather_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generate AI-powered neighborhood analysis
        
        Args:
            neighborhood: Neighborhood name
            city: City name
            places_data: List of places in the neighborhood
            weather_data: Current weather (optional)
            
        Returns:
            Analysis as dict
        """
        
        # Prepare data summary
        total_places = len(places_data)
        
        categories = {}
        for place in places_data:
            cat = place.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
        
        top_categories = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Sample place names
        sample_places = [p['name'] for p in places_data[:15]]
        
        # Build prompt
        system_msg = """You are a local neighborhood expert. 
Analyze neighborhoods based on available data and provide helpful, accurate insights.
Always respond with valid JSON only, no markdown formatting."""
        
        prompt = f"""Analyze the {neighborhood} neighborhood in {city}.

Available data:
- Total places: {total_places}
- Top categories: {', '.join([f"{cat} ({count})" for cat, count in top_categories])}
- Sample places: {', '.join(sample_places[:10])}
"""
        
        if weather_data:
            prompt += f"\n- Current weather: {weather_data.get('description')}, {weather_data.get('temperature_f')}°F"
        
        prompt += """

Provide a brief analysis. Return ONLY valid JSON (no markdown code blocks):
{
    "summary": "2-3 sentence overview of the neighborhood character",
    "dining_score": <1-10 based on restaurant/cafe density>,
    "walkability_score": <1-10 estimate based on amenity density>,
    "highlights": ["highlight 1", "highlight 2", "highlight 3"],
    "best_for": "brief description of ideal resident type"
}
"""
        
        response = await self.generate(prompt, system=system_msg)
        
        # Parse JSON from response
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            # Remove any markdown
            response = response.strip().strip('`').strip()
            if response.startswith('json'):
                response = response[4:].strip()
            
            analysis = json.loads(response)
            
            # Validate structure
            required_keys = ['summary', 'dining_score', 'walkability_score', 'highlights', 'best_for']
            if not all(key in analysis for key in required_keys):
                raise ValueError("Missing required keys")
            
            return analysis
            
        except Exception as e:
            print(f"⚠️  JSON parsing error: {e}")
            print(f"Raw response: {response}")
            
            # Return fallback
            return {
                "summary": f"Analysis of {neighborhood} based on {total_places} local places.",
                "dining_score": min(10, len([p for p in places_data if p.get('category') in ['restaurant', 'cafe', 'bar']]) // 5),
                "walkability_score": min(10, total_places // 20),
                "highlights": [f"{count} {cat}s" for cat, count in top_categories[:3]],
                "best_for": "Various residents"
            }
    
    async def generate_recommendations(
        self,
        preferences: List[str],
        places: List[Dict],
        limit: int = 5
    ) -> Dict:
        """Generate personalized place recommendations"""
        
        system_msg = """You are a helpful local guide. 
Recommend places based on user preferences.
Always respond with valid JSON only."""
        
        places_summary = "\n".join([
            f"- {p['name']} ({p.get('category', 'N/A')})"
            for p in places[:20]
        ])
        
        prompt = f"""User preferences: {', '.join(preferences)}

Available places:
{places_summary}

Recommend the top {limit} best matches. Return ONLY valid JSON:
{{
    "recommendations": [
        {{
            "name": "place name",
            "reason": "why it matches their preferences"
        }}
    ]
}}
"""
        
        response = await self.generate(prompt, system=system_msg)
        
        try:
            # Clean JSON
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            return json.loads(response.strip().strip('`').strip())
        except:
            # Fallback: return first N places
            return {
                "recommendations": [
                    {"name": p['name'], "reason": "Matches your interests"}
                    for p in places[:limit]
                ]
            }


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing LLMService...\n")
        
        service = LLMService()
        
        # Test 1: Simple generation
        print("Test 1: Simple generation")
        response = await service.generate(
            "Describe Chicago in one sentence.",
            temperature=0.7
        )
        print(f"Response: {response}\n")
        
        # Test 2: Neighborhood analysis
        print("Test 2: Neighborhood analysis")
        sample_places = [
            {'name': 'Lou Malnatis', 'category': 'restaurant'},
            {'name': 'Starbucks', 'category': 'cafe'},
            {'name': 'Wicker Park', 'category': 'park'},
        ]
        
        analysis = await service.analyze_neighborhood(
            "Wicker Park",
            "Chicago",
            sample_places
        )
        
        print("Analysis:")
        print(f"  Summary: {analysis['summary']}")
        print(f"  Dining score: {analysis['dining_score']}/10")
        print(f"  Walkability: {analysis['walkability_score']}/10")
        
        print("\n✅ LLM service working!")
    
    asyncio.run(test())
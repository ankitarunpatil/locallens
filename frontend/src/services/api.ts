import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD 
    ? 'https://locallens-api.onrender.com'  // Your Render URL
    : 'http://localhost:8000'
  );

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Place {
  id?: number;
  osm_id: number;
  name: string;
  category?: string;
  lat: number;
  lon: number;
  address?: string;
  phone?: string;
  website?: string;
  tags?: Record<string, any>;
  similarity?: number;
}

export interface NeighborhoodAnalysis {
  neighborhood: string;
  city: string;
  summary: string;
  dining_score: number;
  walkability_score: number;
  highlights: string[];
  best_for: string;
  total_places: number;
  categories: Record<string, number>;
  weather?: {
    temperature_f: number;
    description: string;
    humidity: number;
  };
}

export interface Recommendation {
  name: string;
  category?: string;
  reason: string;
  lat?: number;
  lon?: number;
}

export interface SearchRequest {
  query: string;
  location: [number, number];
  radius_km?: number;
  limit?: number;
}

export interface NeighborhoodRequest {
  name: string;
  city: string;
}

export interface RecommendationsRequest {
  preferences: string[];
  location: [number, number];
  radius_km?: number;
  limit?: number;
}

// API functions
export const searchPlaces = async (request: SearchRequest): Promise<Place[]> => {
  const response = await api.post('/api/search', request);
  return response.data;
};

export const analyzeNeighborhood = async (
  request: NeighborhoodRequest
): Promise<NeighborhoodAnalysis> => {
  const response = await api.post('/api/neighborhood/analyze', request);
  return response.data;
};

export const getRecommendations = async (
  request: RecommendationsRequest
): Promise<{ recommendations: Recommendation[]; total_found: number }> => {
  const response = await api.post('/api/recommendations', request);
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
import React, { useState } from 'react';
import { Search, TrendingUp, Sparkles, Navigation } from 'lucide-react';

import { MapView } from './components/Map/MapView';
import { SearchBar } from './components/Search/SearchBar';
import { SearchResults } from './components/Search/SearchResults';
import { AnalysisCard } from './components/Neighborhood/AnalysisCard';
import { TourGenerator } from './components/Tour/TourGenerator';

import { 
  searchPlaces, 
  analyzeNeighborhood, 
  type Place, 
  type NeighborhoodAnalysis 
} from './services/api';

type ViewMode = 'search' | 'analysis' | 'tour';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('search');
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState<[number, number]>([41.8781, -87.6298]);
  const [places, setPlaces] = useState<Place[]>([]);
  const [analysis, setAnalysis] = useState<NeighborhoodAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string, searchLocation: [number, number]) => {
    setLoading(true);
    setError(null);
    setViewMode('search');

    try {
      const results = await searchPlaces({
        query,
        location: searchLocation,
        radius_km: 2.0,
        limit: 20
      });

      setPlaces(results);
      setLocation(searchLocation);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (neighborhood: string, city: string) => {
    setLoading(true);
    setError(null);
    setViewMode('analysis');

    try {
      const result = await analyzeNeighborhood({ name: neighborhood, city });
      setAnalysis(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const quickNeighborhoods = [
    { name: 'Wicker Park', city: 'Chicago' },
    { name: 'Lincoln Park', city: 'Chicago' },
    { name: 'Logan Square', city: 'Chicago' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      
      {/* HEADER */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-8 h-8 text-blue-600" />
              LocalLens
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              🎯 AI-Powered Neighborhood Discovery • 100% Free
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('search')}
              className={`px-4 py-2 rounded-lg transition ${
                viewMode === 'search'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Search className="w-5 h-5" />
            </button>

            <button
              onClick={() => setViewMode('analysis')}
              className={`px-4 py-2 rounded-lg transition ${
                viewMode === 'analysis'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <TrendingUp className="w-5 h-5" />
            </button>

            <button
              onClick={() => setViewMode('tour')}
              className={`px-4 py-2 rounded-lg transition flex items-center gap-2 ${
                viewMode === 'tour'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Navigation className="w-5 h-5" />
              <span className="hidden md:inline">Tour</span>
            </button>
          </div>
        </div>
      </header>

      {/* MAIN */}
      <main className="max-w-7xl mx-auto px-4 py-8">

        {/* SEARCH BAR */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>

        {/* ERROR */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* QUICK ANALYSIS */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Quick Neighborhood Analysis
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {quickNeighborhoods.map((hood) => (
              <button
                key={`${hood.name}-${hood.city}`}
                onClick={() => handleAnalyze(hood.name, hood.city)}
                disabled={loading}
                className="bg-white p-4 rounded-lg shadow hover:shadow-md transition text-left disabled:opacity-50"
              >
                <h3 className="font-bold text-gray-900">{hood.name}</h3>
                <p className="text-sm text-gray-600">{hood.city}</p>
                <p className="text-xs text-blue-600 mt-2">
                  Click for AI analysis →
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* CONTENT GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* MAP */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Map View</h2>
            <div className="h-[600px]">
              <MapView
                center={location}
                places={places.map(p => ({
                  ...p,
                  lat: p.lat,
                  lon: p.lon
                }))}
              />
            </div>
          </div>

          {/* RIGHT PANEL */}
          <div>

            {viewMode === 'search' && places.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <SearchResults places={places} />
              </div>
            )}

            {viewMode === 'search' && places.length === 0 && !loading && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Start Searching
                </h3>
                <p className="text-gray-500">
                  Use the search bar above to find places near you
                </p>
              </div>
            )}

            {viewMode === 'analysis' && analysis && (
              <AnalysisCard analysis={analysis} />
            )}

            {viewMode === 'analysis' && !analysis && !loading && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Analyze a Neighborhood
                </h3>
                <p className="text-gray-500">
                  Click a quick action above or search for a neighborhood
                </p>
              </div>
            )}

            {viewMode === 'tour' && (
              <TourGenerator
                location={location}
                onTourGenerated={(stops) => {
                  const tourPlaces = stops.map(stop => ({
                    name: stop.name,
                    category: stop.category,
                    lat: stop.lat,
                    lon: stop.lon,
                    osm_id: 0,
                    similarity: 1.0
                  }));

                  setPlaces(tourPlaces);
                }}
              />
            )}

            {loading && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading...</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* FOOTER */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-600">
          <p className="text-sm">
            💯 100% Free & Open Source • OpenStreetMap + Groq + Supabase
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Built with React, FastAPI, and AI • $0.00/month
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
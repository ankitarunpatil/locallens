import React, { useState } from 'react';
import { Search, MapPin, Loader2 } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string, location: [number, number]) => void;
  loading?: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, loading }) => {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState<[number, number]>([41.8781, -87.6298]); // Chicago default

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, location);
    }
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation([position.coords.latitude, position.coords.longitude]);
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Could not get your location. Using default (Chicago).');
        }
      );
    } else {
      alert('Geolocation is not supported by your browser');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for coffee shops, parks, restaurants..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            disabled={loading}
          />
        </div>
        <button
          type="button"
          onClick={getCurrentLocation}
          className="px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
          title="Use my location"
        >
          <MapPin className="w-5 h-5 text-gray-600" />
        </button>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            'Search'
          )}
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Current location: {location[0].toFixed(4)}, {location[1].toFixed(4)}
      </p>
    </form>
  );
};
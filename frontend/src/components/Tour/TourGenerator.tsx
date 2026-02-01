import React, { useState } from 'react';
import { MapPin, Clock, Navigation, Loader2 } from 'lucide-react';
import axios from 'axios';

interface TourStop {
  order: number;
  name: string;
  category: string;
  lat: number;
  lon: number;
  duration_mins: number;
  why_visit: string;
}

interface Tour {
  title: string;
  total_distance_km: number;
  total_duration: string;
  stops: TourStop[];
}

interface TourGeneratorProps {
  location: [number, number];
  onTourGenerated?: (stops: TourStop[]) => void;
}

export const TourGenerator: React.FC<TourGeneratorProps> = ({ 
  location, 
  onTourGenerated 
}) => {
  const [tour, setTour] = useState<Tour | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedInterests, setSelectedInterests] = useState<string[]>(['food']);
  const [duration, setDuration] = useState(2);

  const interests = [
    { id: 'food', label: '🍕 Food', emoji: '🍕' },
    { id: 'culture', label: '🎭 Culture', emoji: '🎭' },
    { id: 'history', label: '🏛️ History', emoji: '🏛️' },
    { id: 'nature', label: '🌳 Nature', emoji: '🌳' },
    { id: 'shopping', label: '🛍️ Shopping', emoji: '🛍️' },
    { id: 'nightlife', label: '🌃 Nightlife', emoji: '🌃' },
  ];

  const toggleInterest = (interest: string) => {
    if (selectedInterests.includes(interest)) {
      setSelectedInterests(selectedInterests.filter(i => i !== interest));
    } else {
      setSelectedInterests([...selectedInterests, interest]);
    }
  };

  const generateTour = async () => {
    if (selectedInterests.length === 0) {
      alert('Please select at least one interest');
      return;
    }

    setLoading(true);
    
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${API_URL}/api/tours/generate`, {
        location,
        duration_hours: duration,
        interests: selectedInterests
      });
      
      setTour(response.data);
      onTourGenerated?.(response.data.stops);
    } catch (error: any) {
      console.error('Tour generation error:', error);
      alert(error.response?.data?.detail || 'Failed to generate tour');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        🚶 Walking Tour Generator
      </h2>

      {/* Duration Selector */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Tour Duration
        </label>
        <div className="flex gap-2">
          {[1, 2, 3, 4].map(hours => (
            <button
              key={hours}
              onClick={() => setDuration(hours)}
              className={`px-4 py-2 rounded-lg transition ${
                duration === hours
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {hours}h
            </button>
          ))}
        </div>
      </div>

      {/* Interests Selector */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Your Interests
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {interests.map(interest => (
            <button
              key={interest.id}
              onClick={() => toggleInterest(interest.id)}
              className={`px-4 py-2 rounded-lg transition text-sm ${
                selectedInterests.includes(interest.id)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {interest.label}
            </button>
          ))}
        </div>
      </div>

      {/* Generate Button */}
      <button
        onClick={generateTour}
        disabled={loading || selectedInterests.length === 0}
        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating your tour...
          </>
        ) : (
          <>
            <Navigation className="w-5 h-5" />
            Generate Walking Tour
          </>
        )}
      </button>

      {/* Tour Results */}
      {tour && (
        <div className="mt-6">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-4">
            <h3 className="font-bold text-lg text-gray-900">{tour.title}</h3>
            <div className="flex gap-4 mt-2 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <Navigation className="w-4 h-4" />
                {tour.total_distance_km.toFixed(1)} km
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {tour.total_duration}
              </span>
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {tour.stops.length} stops
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {tour.stops.map((stop, idx) => (
              <div
                key={idx}
                className="border-l-4 border-blue-500 pl-4 py-2 hover:bg-gray-50 transition rounded-r"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="bg-blue-600 text-white rounded-full w-7 h-7 flex items-center justify-center text-sm font-bold">
                        {stop.order}
                      </span>
                      <h4 className="font-bold text-gray-900">{stop.name}</h4>
                    </div>
                    <p className="text-sm text-gray-600 capitalize ml-9">
                      {stop.category}
                    </p>
                    <p className="text-sm text-gray-700 mt-2 ml-9">
                      {stop.why_visit}
                    </p>
                  </div>
                  <span className="text-sm text-gray-500 whitespace-nowrap ml-4">
                    {stop.duration_mins} min
                  </span>
                </div>
                
                {idx < tour.stops.length - 1 && (
                  <div className="ml-9 mt-2 text-xs text-gray-400">
                    ↓ Walk to next stop
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-green-800">
              ✅ Your tour is ready! The stops are now highlighted on the map.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
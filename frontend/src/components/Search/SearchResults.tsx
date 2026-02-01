import React from 'react';
import { MapPin, Phone, Globe, ExternalLink } from 'lucide-react';

interface Place {
  name: string;
  category?: string;
  lat: number;
  lon: number;
  address?: string;
  phone?: string;
  website?: string;
  similarity?: number;
}

interface SearchResultsProps {
  places: Place[];
  onPlaceClick?: (place: Place) => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ 
  places, 
  onPlaceClick 
}) => {
  if (places.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No results found. Try a different search.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">
        Found {places.length} places
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {places.map((place, idx) => (
          <div
            key={idx}
            onClick={() => onPlaceClick?.(place)}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition cursor-pointer bg-white"
          >
            <div className="flex items-start justify-between">
              <h3 className="font-bold text-gray-900">{place.name}</h3>
              {place.similarity && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  {(place.similarity * 100).toFixed(0)}% match
                </span>
              )}
            </div>
            
            {place.category && (
              <p className="text-sm text-gray-600 capitalize mt-1">
                {place.category}
              </p>
            )}
            
            {place.address && (
              <div className="flex items-start gap-2 mt-2 text-xs text-gray-500">
                <MapPin className="w-3 h-3 mt-0.5 flex-shrink-0" />
                <p>{place.address}</p>
              </div>
            )}
            
            <div className="flex gap-3 mt-3">
              {place.phone && (
                <a
                  href={`tel:${place.phone}`}
                  className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Phone className="w-3 h-3" />
                  Call
                </a>
              )}
              {place.website && (
                <a
                  href={place.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Globe className="w-3 h-3" />
                  Website
                </a>
              )}
              <a
                href={`https://www.openstreetmap.org/?mlat=${place.lat}&mlon=${place.lon}&zoom=18`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="w-3 h-3" />
                View on Map
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
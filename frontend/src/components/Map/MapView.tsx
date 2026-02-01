import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default marker icon
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  iconRetinaUrl: iconRetina,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface Place {
  name: string;
  lat: number;
  lon: number;
  category?: string;
  address?: string;
  similarity?: number;
}

interface MapViewProps {
  center: [number, number];
  places: Place[];
  zoom?: number;
}

// Component to update map center when it changes
function ChangeView({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

export const MapView: React.FC<MapViewProps> = ({ 
  center, 
  places, 
  zoom = 13 
}) => {
  // Create custom icons based on category
  const getCategoryIcon = (category?: string) => {
    const colors: Record<string, string> = {
      restaurant: '#ef4444',
      cafe: '#8b5cf6',
      bar: '#f59e0b',
      park: '#10b981',
      museum: '#3b82f6',
      default: '#6b7280'
    };

    const color = category ? (colors[category] || colors.default) : colors.default;

    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="background-color: ${color}; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12]
    });
  };

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      className="h-full w-full rounded-lg"
      style={{ minHeight: '500px' }}
    >
      <ChangeView center={center} zoom={zoom} />
      
      {/* FREE OpenStreetMap tiles */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {/* Place markers */}
      {places.map((place, idx) => (
        <Marker 
          key={idx} 
          position={[place.lat, place.lon]}
          icon={getCategoryIcon(place.category)}
        >
          <Popup>
            <div className="p-2">
              <h3 className="font-bold text-lg">{place.name}</h3>
              {place.category && (
                <p className="text-sm text-gray-600 capitalize">{place.category}</p>
              )}
              {place.address && (
                <p className="text-xs text-gray-500 mt-1">{place.address}</p>
              )}
              {place.similarity && (
                <p className="text-xs text-blue-600 mt-1">
                  Match: {(place.similarity * 100).toFixed(0)}%
                </p>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
      
      {/* User location marker */}
      <Marker position={center}>
        <Popup>
          <div className="p-2">
            <p className="font-bold">Your Location</p>
          </div>
        </Popup>
      </Marker>
    </MapContainer>
  );
};
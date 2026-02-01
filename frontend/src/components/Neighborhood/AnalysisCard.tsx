import React from 'react';
import { Star, TrendingUp, MapPin, Cloud } from 'lucide-react';

interface NeighborhoodAnalysis {
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

interface AnalysisCardProps {
  analysis: NeighborhoodAnalysis;
}

export const AnalysisCard: React.FC<AnalysisCardProps> = ({ analysis }) => {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600 bg-green-100';
    if (score >= 6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const topCategories = Object.entries(analysis.categories)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {analysis.neighborhood}
          </h2>
          <p className="text-gray-600 flex items-center gap-1 mt-1">
            <MapPin className="w-4 h-4" />
            {analysis.city}
          </p>
        </div>
        
        {analysis.weather && (
          <div className="text-right">
            <div className="flex items-center gap-2 text-gray-700">
              <Cloud className="w-5 h-5" />
              <span className="text-2xl font-bold">
                {analysis.weather.temperature_f}°F
              </span>
            </div>
            <p className="text-sm text-gray-600 capitalize">
              {analysis.weather.description}
            </p>
          </div>
        )}
      </div>

      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <p className="text-gray-800">{analysis.summary}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">Dining & Entertainment</h3>
            <Star className="w-5 h-5 text-yellow-500" />
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-3xl font-bold px-3 py-1 rounded ${getScoreColor(analysis.dining_score)}`}>
              {analysis.dining_score}
            </span>
            <span className="text-sm text-gray-600">out of 10</span>
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">Walkability</h3>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-3xl font-bold px-3 py-1 rounded ${getScoreColor(analysis.walkability_score)}`}>
              {analysis.walkability_score}
            </span>
            <span className="text-sm text-gray-600">out of 10</span>
          </div>
        </div>
      </div>

      <div className="border rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Key Highlights</h3>
        <ul className="space-y-2">
          {analysis.highlights.map((highlight, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span className="text-gray-700">{highlight}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="border rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Best For</h3>
        <p className="text-gray-700">{analysis.best_for}</p>
      </div>

      <div className="border rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-3">
          Place Categories ({analysis.total_places} total)
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {topCategories.map(([category, count]) => (
            <div key={category} className="flex justify-between items-center bg-gray-50 px-3 py-2 rounded">
              <span className="text-sm capitalize text-gray-700">{category}</span>
              <span className="text-sm font-bold text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
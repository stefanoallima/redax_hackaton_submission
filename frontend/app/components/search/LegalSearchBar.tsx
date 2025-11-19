'use client';

import { useState } from 'react';
import { Search, Filter, X } from 'lucide-react';

export interface SearchFilters {
  articleType?: string;
  book?: string;
  dateRange?: { start: string; end: string };
  sortBy?: 'relevance' | 'date' | 'article_number';
}

interface LegalSearchBarProps {
  onSearch: (query: string, filters: SearchFilters) => void;
  onClear?: () => void;
  placeholder?: string;
  initialQuery?: string;
}

export default function LegalSearchBar({
  onSearch,
  onClear,
  placeholder = 'Cerca articoli del Codice Civile...',
  initialQuery = ''
}: LegalSearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    sortBy: 'relevance'
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, filters);
    }
  };

  const handleClear = () => {
    setQuery('');
    setFilters({ sortBy: 'relevance' });
    setShowFilters(false);
    onClear?.();
  };

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="w-full space-y-4">
      {/* Main Search Bar */}
      <form onSubmit={handleSearch} className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholder}
              className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-3 border rounded-lg flex items-center gap-2 ${
              showFilters
                ? 'bg-blue-50 border-blue-500 text-blue-600'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Filter className="h-5 w-5" />
            Filtri
          </button>

          <button
            type="submit"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Cerca
          </button>
        </div>
      </form>

      {/* Advanced Filters Panel */}
      {showFilters && (
        <div className="p-4 border border-gray-200 rounded-lg bg-gray-50 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Article Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo Articolo
              </label>
              <select
                value={filters.articleType || ''}
                onChange={(e) => updateFilter('articleType', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Tutti</option>
                <option value="contract">Contratti</option>
                <option value="property">Proprieta</option>
                <option value="family">Famiglia</option>
                <option value="succession">Successioni</option>
                <option value="obligations">Obbligazioni</option>
              </select>
            </div>

            {/* Book Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Libro
              </label>
              <select
                value={filters.book || ''}
                onChange={(e) => updateFilter('book', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Tutti</option>
                <option value="1">Libro I - Persone e Famiglia</option>
                <option value="2">Libro II - Successioni</option>
                <option value="3">Libro III - Proprieta</option>
                <option value="4">Libro IV - Obbligazioni</option>
                <option value="5">Libro V - Lavoro</option>
                <option value="6">Libro VI - Tutela dei Diritti</option>
              </select>
            </div>

            {/* Sort By Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ordina Per
              </label>
              <select
                value={filters.sortBy}
                onChange={(e) => updateFilter('sortBy', e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="relevance">Rilevanza</option>
                <option value="article_number">Numero Articolo</option>
                <option value="date">Data Modifica</option>
              </select>
            </div>
          </div>

          {/* Active Filters Summary */}
          {(filters.articleType || filters.book) && (
            <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
              <span className="text-sm text-gray-600">Filtri attivi:</span>
              {filters.articleType && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-sm">
                  {filters.articleType}
                </span>
              )}
              {filters.book && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-sm">
                  Libro {filters.book}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

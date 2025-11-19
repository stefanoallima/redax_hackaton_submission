'use client';

import { useState } from 'react';
import { BookOpen, Calendar, Scale, ChevronRight } from 'lucide-react';
import ArticleCard from './ArticleCard';

export interface LegalArticle {
  id: string;
  article_number: string;
  book: number;
  title: string;
  content: string;
  keywords: string[];
  last_modified?: string;
  relevance_score?: number;
  matched_snippet?: string;
}

interface SearchResultsProps {
  results: LegalArticle[];
  query: string;
  totalResults: number;
  isLoading?: boolean;
  onArticleClick: (article: LegalArticle) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export default function SearchResults({
  results,
  query,
  totalResults,
  isLoading = false,
  onArticleClick,
  onLoadMore,
  hasMore = false
}: SearchResultsProps) {
  const [expandedArticleId, setExpandedArticleId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-32 bg-gray-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  if (results.length === 0 && query) {
    return (
      <div className="text-center py-12">
        <Scale className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          Nessun risultato trovato
        </h3>
        <p className="text-gray-500">
          Prova a modificare la tua ricerca o rimuovere alcuni filtri
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results Header */}
      {query && (
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Risultati per "{query}"
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {totalResults} articoli trovati
            </p>
          </div>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {results.map((article) => (
          <ArticleCard
            key={article.id}
            article={article}
            isExpanded={expandedArticleId === article.id}
            onExpand={() => setExpandedArticleId(
              expandedArticleId === article.id ? null : article.id
            )}
            onClick={() => onArticleClick(article)}
            highlightQuery={query}
          />
        ))}
      </div>

      {/* Load More Button */}
      {hasMore && onLoadMore && (
        <div className="text-center pt-6">
          <button
            onClick={onLoadMore}
            className="px-6 py-3 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 inline-flex items-center gap-2"
          >
            Carica altri risultati
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* No More Results */}
      {!hasMore && results.length > 0 && (
        <div className="text-center pt-6 text-gray-500 text-sm">
          Nessun altro risultato disponibile
        </div>
      )}
    </div>
  );
}

'use client';

import { useState } from 'react';
import { BookOpen, Calendar, Tag, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import type { LegalArticle } from './SearchResults';

interface ArticleCardProps {
  article: LegalArticle;
  isExpanded?: boolean;
  onExpand?: () => void;
  onClick?: () => void;
  highlightQuery?: string;
}

export default function ArticleCard({
  article,
  isExpanded = false,
  onExpand,
  onClick,
  highlightQuery = ''
}: ArticleCardProps) {
  const highlightText = (text: string, query: string) => {
    if (!query) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={index} className="bg-yellow-200 text-gray-900 font-medium">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const getBookName = (bookNumber: number): string => {
    const books = {
      1: 'Persone e Famiglia',
      2: 'Successioni',
      3: 'Proprieta',
      4: 'Obbligazioni',
      5: 'Lavoro',
      6: 'Tutela dei Diritti'
    };
    return books[bookNumber as keyof typeof books] || `Libro ${bookNumber}`;
  };

  const truncateContent = (content: string, maxLength: number = 200) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <div className="border border-gray-200 rounded-lg hover:shadow-md transition-shadow bg-white">
      {/* Article Header */}
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium">
                Art. {article.article_number}
              </span>
              <span className="text-sm text-gray-500">
                <BookOpen className="inline h-4 w-4 mr-1" />
                Libro {article.book} - {getBookName(article.book)}
              </span>
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {highlightText(article.title, highlightQuery)}
            </h3>

            {/* Matched Snippet or Content Preview */}
            <p className="text-gray-700 text-sm leading-relaxed">
              {isExpanded
                ? highlightText(article.content, highlightQuery)
                : article.matched_snippet
                ? highlightText(article.matched_snippet, highlightQuery)
                : highlightText(truncateContent(article.content), highlightQuery)
              }
            </p>
          </div>

          {/* Relevance Score */}
          {article.relevance_score !== undefined && (
            <div className="ml-4 text-right">
              <div className="text-xs text-gray-500 mb-1">Rilevanza</div>
              <div className="text-lg font-bold text-blue-600">
                {Math.round(article.relevance_score * 100)}%
              </div>
            </div>
          )}
        </div>

        {/* Keywords */}
        {article.keywords && article.keywords.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {article.keywords.slice(0, 5).map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-600 rounded-md text-xs inline-flex items-center gap-1"
              >
                <Tag className="h-3 w-3" />
                {keyword}
              </span>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center gap-4 text-xs text-gray-500">
            {article.last_modified && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                Modificato: {new Date(article.last_modified).toLocaleDateString('it-IT')}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Expand/Collapse Button */}
            {onExpand && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onExpand();
                }}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md flex items-center gap-1"
              >
                {isExpanded ? (
                  <>
                    Riduci <ChevronUp className="h-4 w-4" />
                  </>
                ) : (
                  <>
                    Espandi <ChevronDown className="h-4 w-4" />
                  </>
                )}
              </button>
            )}

            {/* View Full Article Button */}
            {onClick && (
              <button
                onClick={onClick}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1"
              >
                Visualizza
                <ExternalLink className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

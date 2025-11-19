'use client';

import { useState } from 'react';
import { BookOpen, Calendar, Tag, Share2, Bookmark, MessageSquare, ChevronLeft } from 'lucide-react';
import type { LegalArticle } from '../search/SearchResults';

interface ArticleViewerProps {
  article: LegalArticle;
  relatedArticles?: LegalArticle[];
  onBack?: () => void;
  onAskQuestion?: (article: LegalArticle) => void;
  onBookmark?: (article: LegalArticle) => void;
  isBookmarked?: boolean;
}

export default function ArticleViewer({
  article,
  relatedArticles = [],
  onBack,
  onAskQuestion,
  onBookmark,
  isBookmarked = false
}: ArticleViewerProps) {
  const [copied, setCopied] = useState(false);

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

  const handleShare = async () => {
    const url = `${window.location.origin}/article/${article.id}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const formatArticleContent = (content: string) => {
    // Split content into paragraphs
    return content.split('\n').filter(p => p.trim()).map((paragraph, index) => (
      <p key={index} className="mb-4 leading-relaxed">
        {paragraph}
      </p>
    ));
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="p-6">
          {/* Back Button */}
          {onBack && (
            <button
              onClick={onBack}
              className="mb-4 text-sm text-gray-600 hover:text-gray-900 inline-flex items-center gap-1"
            >
              <ChevronLeft className="h-4 w-4" />
              Torna ai risultati
            </button>
          )}

          {/* Article Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-3">
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md text-sm font-medium">
                  Articolo {article.article_number}
                </span>
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <BookOpen className="h-4 w-4" />
                  Libro {article.book} - {getBookName(article.book)}
                </span>
              </div>

              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                {article.title}
              </h1>

              {/* Last Modified */}
              {article.last_modified && (
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  Ultimo aggiornamento: {new Date(article.last_modified).toLocaleDateString('it-IT', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={handleShare}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
                title="Condividi"
              >
                <Share2 className="h-5 w-5" />
              </button>

              {onBookmark && (
                <button
                  onClick={() => onBookmark(article)}
                  className={`p-2 rounded-md ${
                    isBookmarked
                      ? 'text-blue-600 bg-blue-50'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  title={isBookmarked ? 'Rimuovi segnalibro' : 'Aggiungi segnalibro'}
                >
                  <Bookmark className={`h-5 w-5 ${isBookmarked ? 'fill-current' : ''}`} />
                </button>
              )}

              {onAskQuestion && (
                <button
                  onClick={() => onAskQuestion(article)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
                >
                  <MessageSquare className="h-4 w-4" />
                  Chiedi a Claude
                </button>
              )}
            </div>
          </div>

          {/* Copy Confirmation */}
          {copied && (
            <div className="text-sm text-green-600 bg-green-50 px-3 py-2 rounded-md">
              Link copiato negli appunti!
            </div>
          )}
        </div>
      </div>

      {/* Article Content */}
      <div className="bg-white p-6 space-y-6">
        {/* Keywords */}
        {article.keywords && article.keywords.length > 0 && (
          <div className="flex flex-wrap gap-2 pb-4 border-b border-gray-200">
            <span className="text-sm text-gray-600 flex items-center gap-1">
              <Tag className="h-4 w-4" />
              Parole chiave:
            </span>
            {article.keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md text-sm"
              >
                {keyword}
              </span>
            ))}
          </div>
        )}

        {/* Content */}
        <div className="prose prose-lg max-w-none">
          <div className="text-gray-800 text-justify">
            {formatArticleContent(article.content)}
          </div>
        </div>
      </div>

      {/* Related Articles */}
      {relatedArticles.length > 0 && (
        <div className="bg-gray-50 border-t border-gray-200 p-6 mt-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Articoli correlati
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {relatedArticles.slice(0, 4).map((relArticle) => (
              <div
                key={relArticle.id}
                className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    Art. {relArticle.article_number}
                  </span>
                  <span className="text-xs text-gray-500">
                    Libro {relArticle.book}
                  </span>
                </div>
                <h3 className="font-medium text-gray-900 mb-2">
                  {relArticle.title}
                </h3>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {relArticle.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

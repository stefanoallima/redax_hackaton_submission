'use client';

import { useState } from 'react';
import { BookOpen, ChevronRight, ChevronDown } from 'lucide-react';

export interface BookSection {
  book: number;
  title: string;
  chapters: Chapter[];
}

export interface Chapter {
  id: string;
  title: string;
  articleRange: string;
  articles: ArticleLink[];
}

export interface ArticleLink {
  id: string;
  article_number: string;
  title: string;
}

interface TableOfContentsProps {
  sections: BookSection[];
  currentArticleId?: string;
  onArticleClick: (articleId: string) => void;
}

export default function TableOfContents({
  sections,
  currentArticleId,
  onArticleClick
}: TableOfContentsProps) {
  const [expandedBooks, setExpandedBooks] = useState<Set<number>>(new Set([1]));
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set());

  const toggleBook = (bookNumber: number) => {
    setExpandedBooks(prev => {
      const next = new Set(prev);
      if (next.has(bookNumber)) {
        next.delete(bookNumber);
      } else {
        next.add(bookNumber);
      }
      return next;
    });
  };

  const toggleChapter = (chapterId: string) => {
    setExpandedChapters(prev => {
      const next = new Set(prev);
      if (next.has(chapterId)) {
        next.delete(chapterId);
      } else {
        next.add(chapterId);
      }
      return next;
    });
  };

  return (
    <nav className="h-full overflow-y-auto bg-white border-r border-gray-200">
      <div className="p-4 border-b border-gray-200 sticky top-0 bg-white z-10">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          Codice Civile
        </h2>
        <p className="text-sm text-gray-500 mt-1">Indice degli articoli</p>
      </div>

      <div className="p-2">
        {sections.map((section) => (
          <div key={section.book} className="mb-2">
            {/* Book Header */}
            <button
              onClick={() => toggleBook(section.book)}
              className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors ${
                expandedBooks.has(section.book)
                  ? 'bg-blue-50 text-blue-900'
                  : 'hover:bg-gray-50 text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">
                  Libro {section.book}
                </span>
                <span className="text-xs text-gray-600">
                  {section.title}
                </span>
              </div>
              {expandedBooks.has(section.book) ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>

            {/* Chapters */}
            {expandedBooks.has(section.book) && (
              <div className="ml-4 mt-1 space-y-1">
                {section.chapters.map((chapter) => (
                  <div key={chapter.id}>
                    {/* Chapter Header */}
                    <button
                      onClick={() => toggleChapter(chapter.id)}
                      className={`w-full flex items-center justify-between p-2 rounded-md text-left transition-colors ${
                        expandedChapters.has(chapter.id)
                          ? 'bg-gray-100 text-gray-900'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <div className="flex-1">
                        <div className="text-sm font-medium">
                          {chapter.title}
                        </div>
                        <div className="text-xs text-gray-500">
                          Art. {chapter.articleRange}
                        </div>
                      </div>
                      {expandedChapters.has(chapter.id) ? (
                        <ChevronDown className="h-3 w-3" />
                      ) : (
                        <ChevronRight className="h-3 w-3" />
                      )}
                    </button>

                    {/* Articles */}
                    {expandedChapters.has(chapter.id) && (
                      <div className="ml-4 mt-1 space-y-0.5">
                        {chapter.articles.map((article) => (
                          <button
                            key={article.id}
                            onClick={() => onArticleClick(article.id)}
                            className={`w-full text-left p-2 rounded-md text-sm transition-colors ${
                              currentArticleId === article.id
                                ? 'bg-blue-100 text-blue-900 font-medium'
                                : 'hover:bg-gray-100 text-gray-700'
                            }`}
                          >
                            <div className="flex items-start gap-2">
                              <span className="text-xs px-1.5 py-0.5 bg-gray-200 text-gray-700 rounded font-mono">
                                {article.article_number}
                              </span>
                              <span className="flex-1 line-clamp-2">
                                {article.title}
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </nav>
  );
}

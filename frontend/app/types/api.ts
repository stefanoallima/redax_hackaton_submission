/**
 * API Type Definitions for CodiceCivile.ai
 * Generated from OpenAPI specification
 * @see docs/openapi.yaml
 */

// ARTICLE TYPES

export interface Article {
  id: string;
  article_number: string;
  book: number; // 1-6
  title: string;
  content: string;
  keywords: string[];
  last_modified?: string; // ISO date string
  embedding?: number[]; // 768-dimensional vector
}

export type ArticleType =
  | 'contract'
  | 'property'
  | 'family'
  | 'succession'
  | 'obligations';

export interface ArticleFilter {
  book?: number;
  article_type?: ArticleType;
}

// SEARCH TYPES

export interface SearchRequest {
  query: string;
  filters?: {
    book?: number;
    article_type?: ArticleType;
    date_range?: {
      start: string;
      end: string;
    };
  };
  limit?: number; // 1-50, default 10
  sort_by?: 'relevance' | 'date' | 'article_number';
}

export interface SearchResult {
  article: Article;
  relevance_score: number; // 0-1
  matched_snippet?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

// CHAT TYPES

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  context?: {
    article_id?: string;
    article_title?: string;
    article_content?: string;
  };
  stream?: boolean;
}

export interface ChatResponse {
  id: string;
  role: 'assistant';
  content: string;
  related_articles?: string[]; // Article IDs
  timestamp: string; // ISO datetime
}

// EMBEDDINGS TYPES

export interface EmbeddingRequest {
  text: string; // Max 8000 chars
}

export interface EmbeddingResponse {
  embedding: number[]; // 768-dimensional vector
  model: string; // e.g., "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
}

// USER TYPES

export interface Bookmark {
  article: Article;
  bookmarked_at: string; // ISO datetime
}

export interface BookmarksResponse {
  bookmarks: Bookmark[];
}

export interface AddBookmarkRequest {
  article_id: string;
}

export interface AddBookmarkResponse {
  success: boolean;
  bookmark_id: string;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  results_count: number;
  created_at: string; // ISO datetime
}

export interface SearchHistoryResponse {
  history: SearchHistoryItem[];
}

// RELATED ARTICLES TYPES

export interface RelatedArticleResult {
  article: Article;
  similarity_score: number; // 0-1
}

export interface RelatedArticlesResponse {
  article_id: string;
  related_articles: RelatedArticleResult[];
}

// PAGINATION TYPES

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

// ERROR TYPES

export interface APIError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

// API RESPONSE WRAPPER

export type APIResponse<T> =
  | { success: true; data: T }
  | { success: false; error: APIError['error'] };

// HELPER TYPES

export type BookNumber = 1 | 2 | 3 | 4 | 5 | 6;

export const BOOK_NAMES: Record<BookNumber, string> = {
  1: 'Persone e Famiglia',
  2: 'Successioni',
  3: 'Proprieta',
  4: 'Obbligazioni',
  5: 'Lavoro',
  6: 'Tutela dei Diritti'
};

export const ARTICLE_TYPES: Record<ArticleType, string> = {
  contract: 'Contratti',
  property: 'Proprieta',
  family: 'Famiglia',
  succession: 'Successioni',
  obligations: 'Obbligazioni'
};

// TYPE GUARDS

export function isAPIError(response: any): response is APIError {
  return response && response.error && typeof response.error.code === 'string';
}

export function isArticle(data: any): data is Article {
  return (
    data &&
    typeof data.id === 'string' &&
    typeof data.article_number === 'string' &&
    typeof data.book === 'number' &&
    typeof data.title === 'string' &&
    typeof data.content === 'string' &&
    Array.isArray(data.keywords)
  );
}

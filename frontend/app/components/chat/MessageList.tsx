'use client';

import { User, Sparkles, FileText } from 'lucide-react';
import type { ChatMessage } from './ChatInterface';

interface MessageListProps {
  messages: ChatMessage[];
  streamingMessage?: string;
  onArticleClick?: (articleId: string) => void;
}

export default function MessageList({
  messages,
  streamingMessage,
  onArticleClick
}: MessageListProps) {
  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === 'user';

    return (
      <div
        key={message.id}
        className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
      >
        {/* Avatar */}
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
        )}

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-3xl`}>
          <div
            className={`px-4 py-3 rounded-2xl ${
              isUser
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
          </div>

          {/* Related Articles */}
          {!isUser && message.relatedArticles && message.relatedArticles.length > 0 && (
            <div className="mt-2 space-y-1">
              <div className="text-xs text-gray-500 px-2">Articoli citati:</div>
              <div className="flex flex-wrap gap-2">
                {message.relatedArticles.map((articleId) => (
                  <button
                    key={articleId}
                    onClick={() => onArticleClick?.(articleId)}
                    className="px-2 py-1 bg-blue-50 text-blue-700 rounded-md text-xs hover:bg-blue-100 flex items-center gap-1"
                  >
                    <FileText className="h-3 w-3" />
                    Art. {articleId}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className="text-xs text-gray-500 mt-1 px-2">
            {message.timestamp.toLocaleTimeString('it-IT', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        </div>

        {/* User Avatar */}
        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
            <User className="h-4 w-4 text-gray-600" />
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {messages.map(renderMessage)}

      {/* Streaming Message */}
      {streamingMessage && (
        <div className="flex gap-3 justify-start">
          <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>

          <div className="flex flex-col items-start max-w-3xl">
            <div className="px-4 py-3 rounded-2xl bg-gray-100 text-gray-900">
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {streamingMessage}
                <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

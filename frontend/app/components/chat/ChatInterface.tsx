'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Sparkles, X } from 'lucide-react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  relatedArticles?: string[]; // Article IDs cited in the response
  isStreaming?: boolean;
}

interface ChatInterfaceProps {
  initialContext?: {
    articleId?: string;
    articleTitle?: string;
    articleContent?: string;
  };
  onClose?: () => void;
  onArticleClick?: (articleId: string) => void;
}

export default function ChatInterface({
  initialContext,
  onClose,
  onArticleClick
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Add initial context message if provided
  useEffect(() => {
    if (initialContext?.articleTitle && messages.length === 0) {
      setMessages([
        {
          id: 'context',
          role: 'assistant',
          content: `Ciao! Vedo che stai leggendo l'articolo "${initialContext.articleTitle}". Come posso aiutarti a comprendere meglio questo articolo?`,
          timestamp: new Date()
        }
      ]);
    }
  }, [initialContext, messages.length]);

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // TODO: Replace with actual API call to Claude
      // This is a scaffolded implementation
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          context: initialContext
        })
      });

      if (!response.ok) throw new Error('Failed to get response');

      // Simulate streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        assistantMessage += chunk;
        setStreamingMessage(assistantMessage);
      }

      // Add complete assistant message
      const assistantResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: assistantMessage,
        timestamp: new Date(),
        relatedArticles: [] // TODO: Extract from response
      };

      setMessages(prev => [...prev, assistantResponse]);
      setStreamingMessage('');
    } catch (error) {
      console.error('Chat error:', error);

      // Add error message (scaffolded fallback)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Mi dispiace, al momento non sono disponibile. L'integrazione con Claude e in fase di sviluppo. Per ora, puoi usare la ricerca semantica per trovare articoli rilevanti.`,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestedQuestions = initialContext?.articleId ? [
    'Qual e il significato di questo articolo?',
    'Quali sono i casi pratici di applicazione?',
    'Ci sono articoli correlati?',
    'Quali sono le sentenze rilevanti?'
  ] : [
    'Come funziona la proprieta in Italia?',
    'Quali sono i diritti del consumatore?',
    'Come si regolano le successioni?',
    'Cosa dice il codice sui contratti?'
  ];

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Sparkles className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              Assistente Legale AI
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                Powered by Claude
              </span>
            </h2>
            <p className="text-sm text-gray-600">
              {initialContext?.articleTitle
                ? `Discutendo: ${initialContext.articleTitle}`
                : 'Chiedi informazioni sul Codice Civile'
              }
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !streamingMessage && (
          <div className="text-center py-12">
            <div className="inline-flex p-4 bg-blue-50 rounded-full mb-4">
              <MessageSquare className="h-12 w-12 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Inizia una conversazione
            </h3>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Fai domande sugli articoli del Codice Civile e ricevi risposte dettagliate
              basate sulla giurisprudenza e sulla dottrina.
            </p>
          </div>
        )}

        <MessageList
          messages={messages}
          streamingMessage={streamingMessage}
          onArticleClick={onArticleClick}
        />

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-gray-50">
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          suggestedQuestions={messages.length === 0 ? suggestedQuestions : undefined}
          placeholder="Scrivi una domanda sul Codice Civile..."
        />
      </div>
    </div>
  );
}

import { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Bot, User, Loader2, Terminal } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolsUsed?: string[];
  executionTime?: number;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [userId] = useState(() => `user-${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          user_id: userId,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();
      setConversationId(data.conversation_id);

      const assistantMessage: Message = {
        id: data.id,
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        toolsUsed: data.tools_used,
        executionTime: data.execution_time_ms,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleRecording = () => {
    // Voice recording would be implemented here
    setIsRecording(!isRecording);
  };

  const exampleQueries = [
    'Show me all running EC2 instances in production',
    'Deploy auth-service to staging',
    'Why is my API slow?',
    'Check for any security alerts',
    'Scale analytics agent to 5 replicas',
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-600 rounded-lg">
              <Terminal className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">NL Automation Hub</h1>
              <p className="text-sm text-gray-400">AI-powered DevOps control plane</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            Connected to 6 projects
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <Bot className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                <h2 className="text-xl font-medium mb-2">Welcome to NL Automation Hub</h2>
                <p className="text-gray-400 mb-8">
                  Control your infrastructure with natural language commands
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {exampleQueries.map((query, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(query)}
                      className="text-left px-4 py-3 bg-gray-800/50 hover:bg-gray-800 rounded-lg border border-gray-700 hover:border-indigo-500 transition-colors text-sm"
                    >
                      "{query}"
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={clsx('flex gap-4', message.role === 'user' && 'flex-row-reverse')}
                >
                  <div
                    className={clsx(
                      'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center',
                      message.role === 'user' ? 'bg-indigo-600' : 'bg-gray-700'
                    )}
                  >
                    {message.role === 'user' ? (
                      <User className="w-5 h-5" />
                    ) : (
                      <Bot className="w-5 h-5" />
                    )}
                  </div>
                  <div
                    className={clsx(
                      'flex-1 max-w-[80%]',
                      message.role === 'user' && 'text-right'
                    )}
                  >
                    <div
                      className={clsx(
                        'inline-block px-4 py-3 rounded-2xl',
                        message.role === 'user'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-800 text-gray-100'
                      )}
                    >
                      {message.role === 'assistant' ? (
                        <div className="prose prose-invert prose-sm max-w-none">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p>{message.content}</p>
                      )}
                    </div>
                    {message.role === 'assistant' && message.toolsUsed && message.toolsUsed.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {message.toolsUsed.map((tool, i) => (
                          <span
                            key={i}
                            className="text-xs px-2 py-1 bg-gray-800 rounded-full text-gray-400"
                          >
                            {tool}
                          </span>
                        ))}
                        {message.executionTime && (
                          <span className="text-xs text-gray-500">
                            {message.executionTime}ms
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="flex items-center gap-2 text-gray-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-800 bg-gray-900/50 backdrop-blur-sm px-4 py-4">
            <div className="flex gap-3 items-center">
              <button
                onClick={toggleRecording}
                className={clsx(
                  'p-3 rounded-lg transition-colors',
                  isRecording
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
                )}
                title={isRecording ? 'Stop recording' : 'Start voice input'}
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me to deploy, monitor, troubleshoot..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-gray-500"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="p-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Connected to Projects 1-6 • LangGraph Agent • LangSmith Tracing
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

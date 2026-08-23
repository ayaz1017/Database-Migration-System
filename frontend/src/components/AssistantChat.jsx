import { useState, useEffect, useRef } from 'react';
import apiClient from '../apiClient'
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, X, Send, Minimize2, Maximize2, Bot, Loader2, ArrowRight, AlertTriangle } from 'lucide-react';
import { useLocation, Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API_BASE_URL } from '../config';

const STARTER_QUESTIONS = [
  "Summarize my recent migrations",
  "Which migration took the longest?",
  "What's my overall success rate?",
  "How do I migrate Oracle sequences?"
];

export default function AssistantChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [chatError, setChatError] = useState(null);
  const [isLongLoading, setIsLongLoading] = useState(false);
  
  const location = useLocation();
  const { id: jobIdParam } = useParams();
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto scroll
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [messages, isOpen, isMinimized, isStreaming]);

  // Proactive suggestions based on route
  useEffect(() => {
    if (messages.length > 0) return; // Only on empty state
    
    let proactive = [];
    const path = location.pathname;
    
    if (path === '/app') {
      proactive = ["Summarize my migration activity this week"];
    } else if (path.includes('/app/report/')) {
      proactive = ["What went wrong in this migration?"];
    } else if (path.includes('/app/new')) {
      proactive = ["What chunk size should I use for a 2M row table?"];
    } else if (path.includes('/app/progress/')) {
      proactive = ["Is this migration running at normal speed?"];
    }

    if (proactive.length > 0) {
      setSuggestedQuestions(proactive);
      if (!isOpen) {
        setUnreadCount(1);
      }
    }
  }, [location.pathname]);

  const handleSubmit = async (e, overrideText = null) => {
    if (e) e.preventDefault();
    const textToSend = overrideText || input.trim();
    if (!textToSend || isStreaming) return;

    setInput('');
    const userMsg = { role: 'user', content: textToSend, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setSuggestedQuestions([]);
    setChatError(null);
    
    if (!isOpen) {
      setIsOpen(true);
      setIsMinimized(false);
    }
    setUnreadCount(0);

    // Initial empty assistant message to append to
    const asstMsgId = Date.now() + 1;
    setMessages(prev => [...prev, { role: 'assistant', content: '', id: asstMsgId }]);
    
    setIsLongLoading(false);
    const longLoadTimer = setTimeout(() => setIsLongLoading(true), 3000);

    try {
      const response = await apiClient.fetchWithAuth(`${API_BASE_URL}/api/assistant/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          session_id: sessionId,
          current_page: location.pathname,
          context_job_id: jobIdParam || null
        })
      });

      if (!response.ok) {
        let errMsg = 'Assistant unavailable — the AI service is currently unreachable. Check your API key configuration.';
        try {
          const errData = await response.json();
          if (errData.message) errMsg = errData.message;
        } catch(e) {}
        throw new Error(errMsg);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let done = false;
      let buffer = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';
          
          for (const part of parts) {
            const trimmedPart = part.trim();
            if (!trimmedPart) continue;
            
            // Standard SSE format handling
            if (trimmedPart.startsWith('data: ')) {
              const dataStr = trimmedPart.slice(6).trim();
              if (dataStr === '[DONE]') continue;
              
              try {
                const data = JSON.parse(dataStr);
                if (data.type === 'session_id') {
                  setSessionId(data.session_id);
                } else if (data.type === 'chunk') {
                  setMessages(prev => prev.map(m => 
                    m.id === asstMsgId ? { ...m, content: m.content + data.content } : m
                  ));
                } else if (data.type === 'done') {
                  setSuggestedQuestions(data.suggested_questions || []);
                } else if (data.type === 'error') {
                  setMessages(prev => prev.map(m => 
                    m.id === asstMsgId ? { ...m, content: m.content + data.content } : m
                  ));
                }
              } catch (err) {
                console.error('Error parsing SSE part', err, dataStr);
              }
            }
          }
        }
      }

      // Flush any remaining data left in the buffer after the stream closes.
      // This handles the case where the final SSE message (often the 'done' event)
      // arrives in the same TCP frame as the stream EOF signal.
      if (buffer.trim()) {
        const finalParts = buffer.split('\n\n');
        for (const part of finalParts) {
          const trimmedPart = part.trim();
          if (!trimmedPart || !trimmedPart.startsWith('data: ')) continue;
          const dataStr = trimmedPart.slice(6).trim();
          if (dataStr === '[DONE]') continue;
          try {
            const data = JSON.parse(dataStr);
            if (data.type === 'session_id') {
              setSessionId(data.session_id);
            } else if (data.type === 'chunk') {
              setMessages(prev => prev.map(m =>
                m.id === asstMsgId ? { ...m, content: m.content + data.content } : m
              ));
            } else if (data.type === 'done') {
              setSuggestedQuestions(data.suggested_questions || []);
            } else if (data.type === 'error') {
              setMessages(prev => prev.map(m =>
                m.id === asstMsgId ? { ...m, content: m.content + data.content } : m
              ));
            }
          } catch (err) {
            console.error('Error parsing final SSE buffer', err, dataStr);
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => prev.filter(m => m.id !== asstMsgId && m.id !== userMsg.id));
      
      let finalMessage = err.message || 'Assistant unavailable — the AI service is currently unreachable.';
      if (finalMessage.includes('Failed to fetch') || finalMessage.includes('NetworkError') || finalMessage.includes('fetch failed')) {
        finalMessage = 'Assistant unavailable — the AI service is currently unreachable. Please verify the backend is running.';
      }

      setChatError({
        message: finalMessage,
        lastInput: textToSend
      });
    } finally {
      clearTimeout(longLoadTimer);
      setIsLongLoading(false);
      setIsStreaming(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Replace job IDs with markdown links
  const preprocessMarkdown = (content) => {
    return content.replace(/(mig_\d+)/g, '[$1](/app/report/$1)');
  };

  const MarkdownComponents = {
    a: ({node, ...props}) => {
      const isJobId = props.href?.includes('/app/report/mig_');
      if (isJobId) {
        return (
          <Link 
            to={props.href} 
            className="inline-flex items-center px-1.5 py-0.5 mx-1 rounded bg-accent/10 border border-accent/20 text-accent font-mono text-[10px] uppercase font-bold hover:bg-accent hover:text-white transition-colors"
          >
            {props.children}
          </Link>
        );
      }
      return <a {...props} className="text-accent hover:underline" target="_blank" rel="noreferrer" />;
    },
    p: ({node, ...props}) => <p className="mb-2 last:mb-0 leading-relaxed" {...props} />,
    ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
    ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
    li: ({node, ...props}) => <li className="" {...props} />,
    code: ({node, inline, ...props}) => 
      inline 
        ? <code className="bg-bg-sunken text-accent px-1.5 py-0.5 rounded text-xs font-mono border border-border-default" {...props} />
        : <pre className="bg-bg-sunken p-2 rounded-md overflow-x-auto text-xs font-mono border border-border-default my-2"><code {...props} /></pre>
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <motion.button
        className={`fixed z-50 flex items-center justify-center rounded-full shadow-xl transition-colors ${
          isOpen ? 'bg-bg-raised border border-border-default text-text-primary' : 'bg-accent text-white'
        }`}
        style={{ bottom: 24, right: 24, width: 56, height: 56 }}
        animate={isOpen ? {} : {
          boxShadow: [
            '0 0 0px rgba(124,58,237,0)',
            '0 0 20px rgba(124,58,237,0.45)',
            '0 0 0px rgba(124,58,237,0)'
          ]
        }}
        transition={isOpen ? {} : { duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => {
          if (isOpen && !isMinimized) {
            setIsOpen(false);
          } else {
            setIsOpen(true);
            setIsMinimized(false);
            setUnreadCount(0);
            setTimeout(() => inputRef.current?.focus(), 100);
          }
        }}
      >
        {isOpen && !isMinimized ? (
          <X className="w-6 h-6" />
        ) : (
          <div className="relative">
            <Sparkles className="w-6 h-6" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-success rounded-full border-2 border-white dark:border-[#0a0a0a]"></span>
            )}
          </div>
        )}
      </motion.button>

      {/* Chat Panel Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95, transformOrigin: 'bottom right' }}
            animate={{ 
              opacity: 1, 
              y: isMinimized ? 0 : 0, 
              scale: 1,
              height: isMinimized ? 60 : 560
            }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed z-40 flex flex-col bg-bg-panel border border-border-default rounded-2xl shadow-2xl overflow-hidden"
            style={{ 
              bottom: 96, 
              right: 24, 
              width: 380,
              maxHeight: 'calc(100vh - 120px)'
            }}
          >
            {/* Header */}
            <div 
              className="flex items-center justify-between px-4 py-3 bg-bg-raised border-b border-border-default cursor-pointer shrink-0"
              onClick={() => setIsMinimized(!isMinimized)}
            >
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center border border-accent/20">
                  <Bot className="w-4.5 h-4.5 text-accent" />
                </div>
                <div>
                  <h3 className="text-sm font-display font-black text-text-primary tracking-wide">Flux</h3>
                  <p className="text-[10px] font-mono text-text-secondary uppercase tracking-wider">AI Migration Assistant</p>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <button 
                  className="p-1.5 text-text-tertiary hover:text-text-primary hover:bg-bg-overlay rounded-md transition-colors"
                  onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}
                >
                  {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
                </button>
                <button 
                  className="p-1.5 text-text-tertiary hover:text-error hover:bg-error-muted rounded-md transition-colors"
                  onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Scrollable Message Area */}
            <div className={`flex-1 overflow-y-auto p-4 space-y-4 bg-bg-canvas ${isMinimized ? 'hidden' : 'block'}`}>
              
              {/* Empty State */}
              {messages.length === 0 && (
                <div className="flex flex-col h-full items-center justify-center text-center px-4 space-y-6 pt-8 pb-4">
                  <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center border border-accent/20 mb-2">
                    <Sparkles className="w-6 h-6 text-accent" />
                  </div>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    Hi! I'm <strong className="text-text-primary">Flux</strong>, your migration assistant. I can help you understand your migration history, configure new migrations, or answer questions about database migration best practices. What would you like to know?
                  </p>
                  
                  <div className="flex flex-wrap gap-2 justify-center w-full mt-4">
                    {(suggestedQuestions.length > 0 ? suggestedQuestions : STARTER_QUESTIONS).map((q, i) => (
                      <button
                        key={i}
                        onClick={() => handleSubmit(null, q)}
                        className="text-xs text-text-secondary bg-bg-raised border border-border-default px-3 py-1.5 rounded-full hover:border-accent hover:text-accent transition-colors text-left"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Messages */}
              {messages.map((m) => (
                <div key={m.id} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className="flex items-end space-x-2 max-w-[85%]">
                    {m.role === 'assistant' && (
                      <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center border border-accent/20 shrink-0 mb-1">
                        <Bot className="w-3.5 h-3.5 text-accent" />
                      </div>
                    )}
                    <div 
                      className={`px-3 py-2.5 rounded-2xl text-[13px] shadow-sm ${
                        m.role === 'user' 
                          ? 'bg-accent text-white rounded-br-none' 
                          : 'bg-bg-raised border border-border-default text-text-primary rounded-bl-none'
                      }`}
                    >
                      {m.role === 'user' ? (
                        <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
                      ) : (
                        <div className="markdown-body">
                          {m.content.trim() === '' && isStreaming ? (
                            <div className="flex flex-col space-y-2 py-1">
                              <div className="flex space-x-1">
                                <motion.div className="w-1.5 h-1.5 bg-text-tertiary rounded-full" animate={{ y: [0, -3, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0 }} />
                                <motion.div className="w-1.5 h-1.5 bg-text-tertiary rounded-full" animate={{ y: [0, -3, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }} />
                                <motion.div className="w-1.5 h-1.5 bg-text-tertiary rounded-full" animate={{ y: [0, -3, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }} />
                              </div>
                              {isLongLoading && (
                                <div className="text-[10px] text-text-tertiary animate-pulse font-mono">
                                  Waking up local model (this may take a moment)...
                                </div>
                              )}
                            </div>
                          ) : m.content.trim() === '' && !isStreaming ? (
                            <span className="text-text-secondary italic text-xs">I couldn't generate a response. Please try again.</span>
                          ) : (
                            <ReactMarkdown 
                              remarkPlugins={[remarkGfm]}
                              components={MarkdownComponents}
                            >
                              {preprocessMarkdown(m.content)}
                            </ReactMarkdown>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Suggested Questions below last message */}
              {messages.length > 0 && !isStreaming && suggestedQuestions.length > 0 && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex flex-wrap gap-2 pt-2 pl-8"
                >
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleSubmit(null, q)}
                      className="text-[11px] text-text-secondary bg-bg-raised border border-border-default px-2.5 py-1.5 rounded-full hover:border-accent hover:text-accent transition-colors flex items-center"
                    >
                      <span>{q}</span>
                    </button>
                  ))}
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className={`p-3 bg-bg-raised border-t border-border-default shrink-0 ${isMinimized ? 'hidden' : 'block'}`}>
              <form onSubmit={handleSubmit} className="relative flex items-end">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isStreaming ? "Flux is thinking..." : 
                    "Ask about your migrations..."
                  }
                  disabled={isStreaming}
                  className="w-full bg-bg-sunken border border-border-default text-text-primary text-[13px] rounded-xl pl-3 pr-10 py-2.5 min-h-[40px] max-h-[120px] resize-none focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all placeholder:text-text-tertiary disabled:opacity-60 scrollbar-hide"
                  style={{ fieldSizing: 'content' }} 
                  rows={1}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isStreaming}
                  className="absolute right-2 bottom-2 p-1.5 rounded-lg bg-accent text-white hover:bg-accent-hover disabled:opacity-50 disabled:bg-bg-overlay disabled:text-text-tertiary transition-colors"
                >
                  {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </form>
              
              {chatError && (
                <div className="mt-3 p-3 bg-error/10 border border-error/20 rounded-xl flex flex-col space-y-3">
                  <div className="flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 text-error shrink-0 mt-0.5" />
                    <p className="text-xs text-text-primary leading-relaxed">{chatError.message}</p>
                  </div>
                  <div className="flex justify-end">
                    <button 
                      onClick={() => handleSubmit(null, chatError.lastInput)}
                      className="text-[11px] font-medium bg-bg-panel hover:bg-bg-overlay border border-border-default px-3 py-1.5 rounded-lg text-text-secondary transition-colors"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              )}
              <div className="text-[9px] text-text-tertiary text-center mt-2 font-mono uppercase tracking-wider">
                Flux AI • Press Enter to send, Shift+Enter for newline
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

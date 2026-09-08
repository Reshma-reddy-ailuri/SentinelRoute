import React, { useState, useEffect, useRef } from 'react';
import { sendChatPrompt } from '../services/api';
import SecurityBadge from '../components/SecurityBadge';
import CategoryChip from '../components/CategoryChip';
import {
  Send, ShieldAlert, Clock, User, Sparkles, Trash2,
  Lock, CheckCircle2, ChevronDown, ChevronUp, AlertTriangle
} from 'lucide-react';

// Suggestion chips — clicking them just fills the composer; same API path as any typed prompt
const SUGGESTIONS = [
  'Explain recursion to a beginner',
  'Write a Java program to sort an array',
  'How does OAuth 2.0 work?',
  'Explain microservices architecture',
];

const getReadableError = (error) => {
  if (typeof error?.detail === 'string') return error.detail;
  if (typeof error?.message === 'string') return error.message;
  return 'Unable to reach the Security Gateway. Please try again.';
};

export default function ChatPage() {
  const [prompt, setPrompt] = useState('');
  const [userId, setUserId] = useState('emp_john_doe');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [error, setError] = useState(null);
  const [expandedDetails, setExpandedDetails] = useState({});

  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const toggleDetails = (id) =>
    setExpandedDetails(prev => ({ ...prev, [id]: !prev[id] }));

  const handleSend = async (e) => {
    e?.preventDefault();
    const userPrompt = prompt.trim();
    if (!userPrompt || loading) return;

    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsgId = 'u_' + Date.now();
    const asstMsgId = 'a_' + Date.now();

    setMessages(prev => [...prev, { id: userMsgId, sender: 'user', text: userPrompt, ts }]);
    setPrompt('');
    setError(null);
    setLoading(true);
    setLoadingStep('Scanning prompt…');

    try {
      await new Promise(r => setTimeout(r, 220));
      setLoadingStep('Checking security policy…');
      await new Promise(r => setTimeout(r, 180));
      setLoadingStep('Processing via gateway…');

      const data = await sendChatPrompt(userPrompt, userId);

      const asstTs = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      // Only show "Generating response…" step if ALLOW and we're still waiting
      if (data.decision === 'ALLOW') {
        // Already have the response from the await above; step label is cosmetic
      }

      setMessages(prev => [...prev, {
        id: asstMsgId,
        sender: 'assistant',
        text: data.response,
        ts: asstTs,
        security: {
          request_id:       data.request_id,
          decision:         data.decision,
          risk_level:       data.risk_level,
          is_sensitive:     data.is_sensitive,
          categories:       data.categories    || [],
          detected_entities: data.detected_entities || [],
          reason:           data.reason,
          llm_called:       data.llm_called,
          latency_ms:       data.latency_ms,
        },
      }]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(getReadableError(err));
    } finally {
      setLoading(false);
      setLoadingStep('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const fillPrompt = (text) => {
    setPrompt(text);
    textareaRef.current?.focus();
  };

  const clearChat = () => { setMessages([]); setError(null); };

  return (
    <div className="chat-shell">
      {/* ── Topbar inside chat ────────────────────────────────── */}
      <div className="chat-topbar">
        <div className="chat-topbar-left">
          <span className="chat-topbar-title">Enterprise AI Assistant</span>
          <span className="chat-topbar-sub">Secured · Scanned before external AI</span>
        </div>
        <div className="chat-topbar-right">
          <div className="userid-field">
            <User size={13} className="userid-icon" />
            <input
              type="text"
              className="userid-input"
              value={userId}
              onChange={e => setUserId(e.target.value)}
              placeholder="Employee ID"
              title="Used for audit logging"
            />
          </div>
          {messages.length > 0 && (
            <button className="btn-clear" onClick={clearChat} title="Clear conversation">
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* ── Message stream ────────────────────────────────────── */}
      <div className="chat-stream">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Sparkles size={28} />
            </div>
            <h2 className="empty-heading">How can I help you today?</h2>
            <p className="empty-sub">
              Your prompt is scanned for sensitive data before it reaches any external AI.
            </p>
            <div className="suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => fillPrompt(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map(msg => (
              msg.sender === 'user' ? (
                // ── User bubble ──
                <div key={msg.id} className="msg-row msg-row-user">
                  <div className="msg-user-wrap">
                    <div className="msg-meta msg-meta-right">
                      <span className="msg-sender">{userId}</span>
                      <span className="msg-ts">{msg.ts}</span>
                    </div>
                    <div className="bubble-user">{msg.text}</div>
                  </div>
                </div>
              ) : (
                // ── Assistant response ──
                <div key={msg.id} className="msg-row msg-row-asst">
                  <div className="msg-asst-wrap">
                    <div className="msg-meta">
                      <Sparkles size={12} className="asst-icon" />
                      <span className="msg-sender">Assistant</span>
                      <span className="msg-ts">{msg.ts}</span>
                    </div>

                    {msg.security && (
                      <div className="response-card">
                        {/* Security status strip */}
                        <div className={`sec-strip ${msg.security.decision === 'ALLOW' ? 'sec-strip-ok' : 'sec-strip-block'}`}>
                          <div className="sec-strip-left">
                            {msg.security.decision === 'ALLOW' ? (
                              <>
                                <CheckCircle2 size={13} />
                                <span className="sec-label sec-label-ok">Security check passed</span>
                                <span className="sec-divider">·</span>
                                <span className="sec-sub">Forwarded to external AI</span>
                              </>
                            ) : (
                              <>
                                <AlertTriangle size={13} />
                                <span className="sec-label sec-label-block">Request blocked</span>
                                <span className="sec-divider">·</span>
                                <span className="sec-sub">Sensitive data detected</span>
                              </>
                            )}
                          </div>
                          <div className="sec-strip-right">
                            <span className="sec-latency">
                              <Clock size={11} /> {msg.security.latency_ms} ms
                            </span>
                            <button
                              className="sec-toggle"
                              onClick={() => toggleDetails(msg.id)}
                            >
                              {expandedDetails[msg.id] ? (
                                <>Hide <ChevronUp size={12} /></>
                              ) : (
                                <>Details <ChevronDown size={12} /></>
                              )}
                            </button>
                          </div>
                        </div>

                        {/* Expandable details */}
                        {expandedDetails[msg.id] && (
                          <div className="sec-details">
                            <div className="sec-details-grid">
                              <div className="sec-detail-item">
                                <span className="sec-detail-label">Decision</span>
                                <SecurityBadge type="decision" value={msg.security.decision} />
                              </div>
                              <div className="sec-detail-item">
                                <span className="sec-detail-label">Risk Level</span>
                                <SecurityBadge type="risk" value={msg.security.risk_level} />
                              </div>
                              <div className="sec-detail-item">
                                <span className="sec-detail-label">External LLM</span>
                                <span className={msg.security.llm_called ? 'detail-yes' : 'detail-no'}>
                                  {msg.security.llm_called ? 'Called (Groq)' : 'Not called'}
                                </span>
                              </div>
                              <div className="sec-detail-item">
                                <span className="sec-detail-label">Request ID</span>
                                <code className="sec-req-id">{msg.security.request_id?.slice(0, 8)}…</code>
                              </div>
                            </div>
                            {msg.security.categories?.length > 0 && (
                              <div className="sec-categories">
                                <span className="sec-detail-label">Detected Categories</span>
                                <div className="chips-row">
                                  {msg.security.categories.map((c, i) => (
                                    <CategoryChip key={i} category={c} />
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Main body */}
                        <div className="response-body">
                          {msg.security.decision === 'ALLOW' ? (
                            <div className="response-text">{msg.text}</div>
                          ) : (
                            <div className="block-notice">
                              <ShieldAlert size={18} className="block-notice-icon" />
                              <div>
                                <p className="block-notice-reason">{msg.security.reason}</p>
                                {msg.security.categories?.length > 0 && (
                                  <div className="block-cats">
                                    {msg.security.categories.map((c, i) => (
                                      <CategoryChip key={i} category={c} />
                                    ))}
                                  </div>
                                )}
                                <p className="block-guarantee">
                                  <Lock size={11} /> The external AI was not contacted.
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="msg-row msg-row-asst">
                <div className="msg-asst-wrap">
                  <div className="loading-bubble">
                    <div className="pulse-spinner" />
                    <span className="loading-text">{loadingStep}</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* ── Error banner ──────────────────────────────────────── */}
      {error && (
        <div className="error-banner">
          <ShieldAlert size={16} />
          <span>{error}</span>
          <button className="error-dismiss" onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* ── Composer ──────────────────────────────────────────── */}
      <div className="composer">
        <form className="composer-form" onSubmit={handleSend}>
          <textarea
            ref={textareaRef}
            className="composer-input"
            rows={2}
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything…"
            disabled={loading}
          />
          <button
            type="submit"
            className="composer-send"
            disabled={!prompt.trim() || loading}
            title="Send"
          >
            {loading ? <span className="spinner" /> : <Send size={16} />}
          </button>
        </form>
        <p className="composer-hint">
          Prompts are scanned before being sent to external AI · Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

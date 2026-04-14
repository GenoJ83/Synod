import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '../../config';

/**
 * Grounded tutor chat: POST /chat/notes with source_text from the current analysis.
 */
function NotesChatPanel({ sourceText, summary }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState('');
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    const send = async () => {
        const q = input.trim();
        if (!q || loading) return;
        if (!sourceText || sourceText.length < 50) {
            setErr('Run a full analysis so your notes are stored for chat (at least 50 characters).');
            return;
        }

        setErr('');
        const prior = messages;
        setInput('');
        setMessages([...prior, { role: 'user', content: q }]);
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/chat/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_text: sourceText,
                    message: q,
                    history: prior.map(({ role, content }) => ({ role, content })),
                    summary_hint: summary || '',
                }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                const d = data.detail;
                const msg = typeof d === 'string' ? d : Array.isArray(d)
                    ? d.map((x) => x.msg || String(x)).join(' ')
                    : 'Could not get a reply.';
                throw new Error(msg);
            }
            setMessages((m) => [...m, { role: 'assistant', content: data.reply || '' }]);
        } catch (e) {
            setMessages(prior);
            setInput(q);
            setErr(e.message || 'Chat failed.');
        } finally {
            setLoading(false);
        }
    };

    const canChat = sourceText && sourceText.length >= 50;

    return (
        <div className="pro-card p-6 border border-app-border/80">
            <div className="flex items-center gap-3 mb-3 text-emerald-500">
                <MessageCircle className="w-5 h-5" />
                <h3 className="text-xs font-bold uppercase tracking-widest">Study assistant</h3>
            </div>
            <p className="text-[11px] text-app-muted mb-4 leading-relaxed">
                Ask questions about this upload. Answers are grounded in your notes and the summary.
            </p>

            {!canChat && (
                <p className="text-xs text-amber-600/90 dark:text-amber-400/90 mb-3">
                    Chat needs the saved source text from this analysis. Re-run analysis from the dashboard if you opened an old history item.
                </p>
            )}

            <div className="max-h-72 overflow-y-auto space-y-3 mb-3 pr-1 border border-app-border/40 rounded-lg p-3 bg-app-bg/40">
                {messages.length === 0 && (
                    <p className="text-xs text-app-muted italic">Try: “What is the main idea of this lecture?” or “Explain XOR vs OR in one paragraph.”</p>
                )}
                {messages.map((m, i) => (
                    <div
                        key={i}
                        className={`text-sm leading-relaxed rounded-lg px-3 py-2 ${
                            m.role === 'user'
                                ? 'bg-emerald-500/15 text-app-fg ml-6'
                                : 'bg-app-card text-app-fg mr-4 border border-app-border/50'
                        }`}
                    >
                        <span className="text-[9px] font-bold uppercase text-app-muted block mb-1">
                            {m.role === 'user' ? 'You' : 'Assistant'}
                        </span>
                        <div className="whitespace-pre-wrap">{m.content}</div>
                    </div>
                ))}
                {loading && (
                    <div className="flex items-center gap-2 text-xs text-app-muted py-2">
                        <Loader2 className="w-4 h-4 animate-spin text-emerald-500" />
                        Thinking…
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {err && <p className="text-xs text-red-500/90 mb-2">{err}</p>}

            <div className="flex gap-2">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            send();
                        }
                    }}
                    disabled={!canChat || loading}
                    placeholder={canChat ? 'Ask about your notes…' : 'Notes unavailable'}
                    rows={2}
                    className="flex-1 resize-none rounded-lg border border-app-border bg-app-bg px-3 py-2 text-sm text-app-fg placeholder:text-app-muted focus:outline-none focus:ring-1 focus:ring-emerald-500/40 disabled:opacity-50"
                />
                <button
                    type="button"
                    onClick={send}
                    disabled={!canChat || loading || !input.trim()}
                    className="self-end shrink-0 p-3 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    aria-label="Send"
                >
                    <Send className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}

export default NotesChatPanel;

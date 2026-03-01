import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Zap, Lock } from 'lucide-react';

const QUICK_REPLIES = [
    "What's the best hotel option?",
    "Tell me more about this destination",
    "What's the total cost breakdown?",
    "Best time activities here?",
    "I want to change destination",
    "I'm ready to book",
];

function TypingIndicator() {
    return (
        <div className="flex gap-1 items-center px-4 py-3">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
        </div>
    );
}

function ActionCard({ action, onApply }) {
    const labels = {
        reorder_stops: '🔄 Route Reorder Suggested',
        change_transport: '✈️ Transport Change Suggested',
        adjust_days: '📅 Day Allocation Suggested',
    };
    if (!labels[action]) return null;
    return (
        <div className="chat-action-card mt-2">
            <p className="text-xs font-semibold text-blue-700 mb-2">{labels[action]}</p>
            <button onClick={onApply} className="btn-primary text-xs px-4 py-2">
                Apply <Zap size={11} />
            </button>
        </div>
    );
}

export default function ChatWindow({ messages, isTyping, onSend, onConfirm, isPopup = false, actionApplied, onApplyAction }) {
    const [inputText, setInputText] = useState('');
    const [pendingSend, setPendingSend] = useState(false);  // queued send while AI is typing
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    // When AI finishes typing, if we had a pending send fire it
    useEffect(() => {
        if (!isTyping && pendingSend && inputText.trim()) {
            setPendingSend(false);
            const text = inputText.trim();
            setInputText('');
            onSend(text);
        }
    }, [isTyping, pendingSend, inputText, onSend]);

    const handleSend = useCallback(() => {
        if (!inputText.trim()) return;
        if (isTyping) {
            // Queue: mark as pending, will fire when AI is done
            setPendingSend(true);
            return;
        }
        const text = inputText.trim();
        setInputText('');
        onSend(text);
    }, [inputText, isTyping, onSend]);

    const handleKeyDown = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }, [handleSend]);

    const isLocked = isTyping; // input is visually locked while AI responds

    return (
        <div className={`flex flex-col h-full ${isPopup ? 'bg-white' : 'bg-white border-r border-gray-100'}`}>
            {/* Chat header */}
            <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                    <span className="text-white text-sm">✨</span>
                </div>
                <div className="flex-1">
                    <p className="text-sm font-bold text-gray-900">AI Travel Planner</p>
                    <p className="text-[11px] flex items-center gap-1">
                        {isTyping ? (
                            <><span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block animate-pulse" />
                                <span className="text-amber-600 font-medium">Thinking…</span></>
                        ) : (
                            <><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
                                <span className="text-emerald-600">Ready</span></>
                        )}
                    </p>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scrollbar-hide">
                {messages.map((msg, i) => (
                    <div key={msg.id || i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}>
                        {msg.role === 'assistant' && (
                            <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center mr-2 flex-none self-end mb-1">
                                <span className="text-xs">✨</span>
                            </div>
                        )}
                        <div>
                            <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                                {msg.content}
                            </div>
                            {msg.role === 'assistant' && actionApplied && i === messages.length - 1 && (
                                <ActionCard action={actionApplied.type} onApply={onApplyAction} />
                            )}
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="flex items-end gap-2">
                        <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center flex-none">
                            <span className="text-xs">✨</span>
                        </div>
                        <div className="chat-bubble-ai px-3">
                            <TypingIndicator />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Quick replies — only show contextually, not while typing */}
            {!isPopup && !isTyping && (
                <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                    {QUICK_REPLIES.slice(0, 4).map(qr => (
                        <button
                            key={qr}
                            onClick={() => {
                                setInputText(qr);
                                setTimeout(() => inputRef.current?.focus(), 50);
                            }}
                            className="text-[11px] bg-gray-100 hover:bg-blue-50 hover:text-blue-700 text-gray-600 px-3 py-1.5 rounded-full transition-colors"
                        >
                            {qr}
                        </button>
                    ))}
                </div>
            )}

            {/* Input */}
            <div className="px-4 pb-4 pt-2 border-t border-gray-100">
                <div className={`flex gap-2 transition-opacity ${isLocked && !pendingSend ? 'opacity-60' : ''}`}>
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputText}
                        onChange={e => setInputText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={isTyping
                            ? pendingSend
                                ? "Message queued — will send when AI finishes…"
                                : "AI is thinking… type your next message"
                            : "Ask me about this trip…"}
                        className="input-clean flex-1 text-sm py-2.5"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!inputText.trim()}
                        title={isTyping ? "Will send after AI finishes responding" : "Send"}
                        className={`px-4 py-2.5 flex-none rounded-xl transition-all disabled:opacity-40 ${pendingSend
                                ? 'bg-amber-500 hover:bg-amber-600 text-white'
                                : 'btn-primary'
                            }`}
                    >
                        {pendingSend ? <Lock size={16} /> : <Send size={16} />}
                    </button>
                </div>
                {pendingSend && (
                    <p className="text-[10px] text-amber-600 font-medium mt-1.5 flex items-center gap-1">
                        ⏳ Message queued — will send when the AI finishes responding
                    </p>
                )}
                {onConfirm && (
                    <button
                        onClick={onConfirm}
                        className="w-full mt-2 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-xl py-2 transition-colors"
                    >
                        ✓ Confirm & Book This Itinerary
                    </button>
                )}
            </div>
        </div>
    );
}

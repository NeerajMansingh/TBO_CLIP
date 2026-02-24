import { useEffect, useRef, useState } from 'react'

export default function ChatWindow({ messages, isTyping, onSend }) {
    const [input, setInput] = useState('')
    const bottomRef = useRef(null)
    const inputRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, isTyping])

    const handleSubmit = (e) => {
        e?.preventDefault()
        const text = input.trim()
        if (!text || isTyping) return
        setInput('')
        onSend(text)
        inputRef.current?.focus()
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit()
        }
    }

    return (
        <div className="flex flex-col h-full min-h-[60vh] lg:min-h-0">
            {/* Header */}
            <div className="px-5 py-4 border-b border-white/8 flex items-center gap-3 shrink-0">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse-soft" />
                <div>
                    <p className="text-sm font-semibold text-white">VibeTravel AI</p>
                    <p className="text-xs text-white/40">Powered by Gemini · Ask anything</p>
                </div>
                <div className="ml-auto">
                    <span className="text-xs text-white/30 bg-white/5 px-2 py-1 rounded-lg border border-white/10">
                        💬 {messages.length} messages
                    </span>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
                {messages.map((msg) => (
                    <MessageBubble key={msg.id} msg={msg} />
                ))}

                {isTyping && <TypingIndicator />}
                <div ref={bottomRef} />
            </div>

            {/* Quick reply chips */}
            <QuickReplies onSelect={(text) => { setInput(text); inputRef.current?.focus() }} />

            {/* Input bar */}
            <form
                onSubmit={handleSubmit}
                className="px-4 py-4 border-t border-white/8 flex gap-3 items-end shrink-0"
            >
                <textarea
                    ref={inputRef}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    placeholder="Type a message… (Enter to send)"
                    className="flex-1 resize-none bg-white/8 border border-white/15 rounded-xl px-4 py-3
                     text-white text-sm placeholder-white/35
                     focus:outline-none focus:border-brand-400/60 focus:ring-1 focus:ring-brand-400/20
                     transition-all duration-200 max-h-32"
                    style={{ fieldSizing: 'content' }}
                />
                <button
                    type="submit"
                    disabled={!input.trim() || isTyping}
                    id="send-message-btn"
                    className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-all duration-200
            ${input.trim() && !isTyping
                            ? 'bg-gradient-to-br from-brand-500 to-brand-600 text-white shadow-lg shadow-brand-500/30 hover:shadow-brand-500/50 hover:scale-105 active:scale-95'
                            : 'bg-white/8 text-white/25 cursor-not-allowed'
                        }`}
                >
                    <svg className="w-5 h-5 rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                </button>
            </form>
        </div>
    )
}

function MessageBubble({ msg }) {
    const isUser = msg.role === 'user'
    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-orange-500 flex items-center justify-center shrink-0 mr-2.5 mt-0.5 text-xs font-bold shadow-md shadow-brand-500/30">
                    ✈
                </div>
            )}
            <div className={isUser ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                {msg.content}
            </div>
        </div>
    )
}

function TypingIndicator() {
    return (
        <div className="flex items-start gap-2.5 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-orange-500 flex items-center justify-center shrink-0 text-xs font-bold shadow-md shadow-brand-500/30">
                ✈
            </div>
            <div className="chat-bubble-ai flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
        </div>
    )
}

const QUICK_REPLIES = [
    "I want something more mountainous",
    "I prefer beach destinations",
    "Not too touristy please",
    "This looks perfect!",
    "Can we go somewhere romantic?",
]

function QuickReplies({ onSelect }) {
    return (
        <div className="px-4 pb-2 flex gap-2 overflow-x-auto scrollbar-hide">
            {QUICK_REPLIES.map(q => (
                <button
                    key={q}
                    onClick={() => onSelect(q)}
                    className="shrink-0 px-3 py-1.5 rounded-full text-xs border border-white/15 bg-white/5 text-white/60 hover:bg-white/10 hover:text-white hover:border-white/25 transition-all duration-150 whitespace-nowrap"
                >
                    {q}
                </button>
            ))}
        </div>
    )
}

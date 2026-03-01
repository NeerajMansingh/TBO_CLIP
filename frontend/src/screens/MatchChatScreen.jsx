import { useState, useRef, useEffect, useCallback } from 'react'
import DestinationPanel from '../components/DestinationPanel'
import ChatWindow from '../components/ChatWindow'
const API_BASE = ''
export default function MatchChatScreen({ matchData, uploadedPhoto, onSendMessage, onConfirm, apiBase }) {
    const [currentMatch, setCurrentMatch] = useState({
        destination: matchData.matched_destination,
        photo: matchData.destination_photo,
        price: matchData.price_per_person,
        reasons: matchData.match_reasons,
        hotels: matchData.hotels,
        tagline: matchData.tagline || '',
        stops: matchData.stops || []
    })
    const [messages, setMessages] = useState([
        { role: 'assistant', content: matchData.conversation_opener, id: 'opener' }
    ])
    const [isTyping, setIsTyping] = useState(false)
    const [isUpdatingMatch, setIsUpdatingMatch] = useState(false)

    const handleSend = useCallback(async (text) => {
        const userMsg = { role: 'user', content: text, id: Date.now() }
        setMessages(prev => [...prev, userMsg])
        setIsTyping(true)

        try {
            const result = await onSendMessage(text)

            setIsTyping(false)

            const aiMsg = { role: 'assistant', content: result.message, id: Date.now() + 1 }
            setMessages(prev => [...prev, aiMsg])

            if (result.action === 'search_again' && result.updated_match) {
                setIsUpdatingMatch(true)
                setTimeout(() => {
                    const m = result.updated_match
                    setCurrentMatch({
                        destination: m.matched_destination,
                        photo: m.destination_photo,
                        price: m.price_per_person,
                        reasons: m.match_reasons,
                        hotels: m.hotels,
                        tagline: m.tagline || '',
                        stops: m.stops || []
                    })
                    setIsUpdatingMatch(false)
                }, 400)
            }

            if (result.action === 'confirm_booking') {
                setTimeout(() => onConfirm(), 1200)
            }
        } catch (err) {
            setIsTyping(false)
            setMessages(prev => [
                ...prev,
                { role: 'assistant', content: "I'm having a little trouble right now. Could you repeat that?", id: Date.now() + 2 }
            ])
        }
    }, [onSendMessage, onConfirm])

    const [isChatOpen, setIsChatOpen] = useState(false)

    return (
        <div className="min-h-screen relative flex justify-center bg-[#0a0a0a]">
            {/* Full width destination info */}
            <div className="w-full max-w-5xl h-screen overflow-y-auto px-4 pb-24">
                <DestinationPanel
                    uploadedPhoto={uploadedPhoto}
                    currentMatch={currentMatch}
                    isUpdating={isUpdatingMatch}
                    apiBase={apiBase}
                />
            </div>

            {/* Floating Chat Bubble Toggle */}
            <button
                onClick={() => setIsChatOpen(!isChatOpen)}
                className="fixed bottom-6 right-6 lg:bottom-10 lg:right-10 w-16 h-16 bg-gradient-to-br from-brand-500 to-orange-500 rounded-full shadow-2xl shadow-brand-500/30 flex items-center justify-center hover:scale-105 active:scale-95 transition-all z-[60] group border border-white/20"
            >
                {isChatOpen ? (
                    <span className="text-2xl text-white font-bold">✕</span>
                ) : (
                    <span className="text-3xl filter drop-shadow-md">✨</span>
                )}
                {!isChatOpen && messages.length > 1 && (
                    <span className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full text-xs text-white flex items-center justify-center font-bold border-2 border-[#1a1a1a] shadow-lg animate-bounce">
                        {messages.length - 1}
                    </span>
                )}
            </button>

            {/* Floating Chat Window Overlay */}
            <div className={`fixed bottom-28 right-6 lg:right-10 w-[min(90vw,400px)] h-[min(70vh,600px)] bg-[#1a1a1a]/95 backdrop-blur-3xl border border-white/10 rounded-2xl shadow-2xl flex flex-col z-[50] overflow-hidden transition-all duration-300 origin-bottom-right ${isChatOpen ? 'scale-100 opacity-100 translate-y-0' : 'scale-75 opacity-0 translate-y-10 pointer-events-none'}`}>
                <ChatWindow
                    messages={messages}
                    isTyping={isTyping}
                    onSend={handleSend}
                    onConfirm={onConfirm}
                    isPopup={true}
                />
            </div>
        </div>
    )
}

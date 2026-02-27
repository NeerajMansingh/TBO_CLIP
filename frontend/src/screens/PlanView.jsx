import React, { useState, useCallback } from 'react';
import ChatWindow from '../components/ChatWindow';
import { MapPin, Star, ArrowLeft, GripVertical, Plane, Train, Bus, ChevronDown, ChevronUp, Info } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const TRANSPORT_OPTIONS = [
    { value: 'flight', label: 'Flight', icon: '✈️' },
    { value: 'train', label: 'Train', icon: '🚂' },
    { value: 'bus', label: 'Bus', icon: '🚌' },
    { value: 'drive', label: 'Drive', icon: '🚗' },
];

// ── Individual stop card (draggable) ─────────────────────────────────────────
function StopCard({ stop, index, total, transport, days, onTransportChange, onDaysChange, isDragging, onDragStart, onDragEnd, onDragOver, onDrop }) {
    const [expanded, setExpanded] = useState(index === 0);

    const photoUrl = stop.photo
        ? (stop.photo.startsWith('http') ? stop.photo : `${API_BASE}/${stop.photo}`)
        : null;

    const isMock = stop.hotels?.some(h => h.name?.includes('(Fallback)')) || false;
    const flightCost = stop.flight_min_fare || Math.round((stop.price_per_person || 0) * 0.35);
    const hotelCost = Math.max(0, (stop.price_per_person || 0) - flightCost);

    return (
        <div
            draggable
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
            onDragOver={onDragOver}
            onDrop={onDrop}
            className={`card-light overflow-hidden transition-all duration-200 cursor-default ${isDragging ? 'opacity-40 scale-95' : ''}`}
        >
            {/* Card header (always visible) */}
            <div className="flex items-center gap-3 p-4 border-b border-gray-50">
                {/* Drag handle */}
                <div className="drag-handle flex-none" title="Drag to reorder">
                    <GripVertical size={18} />
                </div>

                {/* Stop number */}
                <div className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center flex-none">
                    {index + 1}
                </div>

                {/* Photo thumb */}
                {photoUrl && (
                    <img src={photoUrl} alt={stop.destination} className="w-12 h-12 rounded-lg object-cover flex-none" />
                )}

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <h4 className="font-bold text-gray-900 text-sm truncate">{stop.destination}</h4>
                        {isMock && <span className="mock-badge">Mock</span>}
                    </div>
                    <p className="text-xs text-gray-500 truncate">{stop.tagline || 'India'}</p>
                </div>

                <div className="flex items-center gap-2 flex-none">
                    <span className="text-sm font-bold text-gray-900">₹{(stop.price_per_person || 0).toLocaleString('en-IN')}</span>
                    <button onClick={() => setExpanded(e => !e)} className="text-gray-400 hover:text-gray-700 transition-colors">
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                </div>
            </div>

            {/* Expanded details */}
            {expanded && (
                <div className="p-4 space-y-4 bg-gray-50/50 animate-slide-up">
                    {/* Cost breakdown */}
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-white rounded-xl p-2 border border-gray-100">
                            <p className="text-[10px] text-gray-400 mb-0.5">Flight</p>
                            <p className="text-sm font-bold text-gray-800">₹{flightCost.toLocaleString('en-IN')}</p>
                        </div>
                        <div className="bg-white rounded-xl p-2 border border-gray-100">
                            <p className="text-[10px] text-gray-400 mb-0.5">Hotel</p>
                            <p className="text-sm font-bold text-gray-800">₹{hotelCost.toLocaleString('en-IN')}</p>
                        </div>
                        <div className="bg-blue-50 rounded-xl p-2 border border-blue-100">
                            <p className="text-[10px] text-blue-600 mb-0.5">Total</p>
                            <p className="text-sm font-bold text-blue-700">₹{(stop.price_per_person || 0).toLocaleString('en-IN')}</p>
                        </div>
                    </div>

                    {/* Transport selector */}
                    <div>
                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">Travel Mode to Next Stop</p>
                        <div className="flex gap-2">
                            {TRANSPORT_OPTIONS.map(opt => (
                                <button
                                    key={opt.value}
                                    onClick={() => onTransportChange(index, opt.value)}
                                    className={`flex-1 py-2 rounded-lg border text-xs font-semibold transition-all ${transport === opt.value
                                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                                            : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                                        }`}
                                    disabled={index === total - 1}
                                >
                                    {opt.icon} {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Days stepper */}
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Days at this stop</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => onDaysChange(index, Math.max(1, days - 1))}
                                className="w-8 h-8 rounded-lg border border-gray-200 hover:bg-gray-100 text-gray-600 font-bold transition-colors"
                            >−</button>
                            <span className="w-12 text-center font-bold text-gray-900">{days}</span>
                            <button
                                onClick={() => onDaysChange(index, Math.min(14, days + 1))}
                                className="w-8 h-8 rounded-lg border border-gray-200 hover:bg-gray-100 text-gray-600 font-bold transition-colors"
                            >+</button>
                        </div>
                    </div>

                    {/* Day itinerary */}
                    {stop.itinerary && stop.itinerary.length > 0 && (
                        <div>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">Sample Itinerary</p>
                            <div className="space-y-2">
                                {stop.itinerary.map((day, i) => (
                                    <div key={i} className="flex gap-3 text-xs">
                                        <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold flex-none mt-0.5">
                                            {day.day}
                                        </div>
                                        <div>
                                            <p className="font-semibold text-gray-800">{day.title}</p>
                                            <p className="text-gray-500">{day.description}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Hotels */}
                    {stop.hotels && stop.hotels.length > 0 && (
                        <div>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">Hotel Options</p>
                            <div className="space-y-2">
                                {stop.hotels.slice(0, 2).map((hotel, i) => (
                                    <div key={i} className="bg-white rounded-xl p-3 border border-gray-100 flex items-center gap-3">
                                        {hotel.photo && (
                                            <img src={hotel.photo} alt={hotel.name} className="w-12 h-10 rounded-lg object-cover flex-none" onError={e => e.target.style.display = 'none'} />
                                        )}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-bold text-gray-800 truncate">{hotel.name}</p>
                                            <div className="flex items-center gap-1 mt-0.5">
                                                <Star size={10} className="text-amber-400 fill-amber-400" />
                                                <span className="text-[10px] text-gray-500">{hotel.rating}</span>
                                                <span className="text-[10px] text-gray-400">• ₹{(hotel.price_per_night || 0).toLocaleString('en-IN')}/night</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}


// ── Main PlanView ─────────────────────────────────────────────────────────────
export default function PlanView({ itinerary, sessionId, apiBase = API_BASE, onBack, onConfirm, uploadedPhoto }) {
    const [stops, setStops] = useState(itinerary.stops || []);
    const [totalPrice, setTotalPrice] = useState(itinerary.total_price || 0);
    const [messages, setMessages] = useState([]);
    const [isTyping, setIsTyping] = useState(false);
    const [transportModes, setTransportModes] = useState(() =>
        Object.fromEntries((itinerary.stops || []).map((_, i) => [i, 'flight']))
    );
    const [daysPerStop, setDaysPerStop] = useState(() =>
        Object.fromEntries((itinerary.stops || []).map((_, i) => [i, 2]))
    );
    const [routeJustification, setRouteJustification] = useState(itinerary.route_justification || '');
    const [lastActionApplied, setLastActionApplied] = useState(null);
    const [dragIndex, setDragIndex] = useState(null);
    const [dragOverIndex, setDragOverIndex] = useState(null);

    const totalDays = Object.values(daysPerStop).reduce((a, b) => a + b, 0);

    // ── Drag and Drop (HTML5 DnD) ──────────────────────────────────────────────
    const handleDragStart = useCallback((index) => () => setDragIndex(index), []);
    const handleDragEnd = useCallback(() => { setDragIndex(null); setDragOverIndex(null); }, []);

    const handleDragOver = useCallback((index) => (e) => {
        e.preventDefault();
        setDragOverIndex(index);
    }, []);

    const handleDrop = useCallback((index) => async (e) => {
        e.preventDefault();
        if (dragIndex === null || dragIndex === index) { setDragIndex(null); setDragOverIndex(null); return; }

        const newStops = [...stops];
        const [moved] = newStops.splice(dragIndex, 1);
        newStops.splice(index, 0, moved);

        setStops(newStops);
        setDragIndex(null);
        setDragOverIndex(null);

        // Call backend reorder endpoint
        try {
            const res = await fetch(`${apiBase}/itinerary/reorder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    new_stop_order: newStops.map(s => s.destination),
                }),
            });
            if (res.ok) {
                const data = await res.json();
                setStops(data.stops || newStops);
                setTotalPrice(data.total_price || totalPrice);
                setRouteJustification(data.route_justification || routeJustification);
            }
        } catch (err) {
            console.warn('Reorder API failed (local reorder applied):', err);
        }
    }, [dragIndex, stops, sessionId, apiBase, totalPrice, routeJustification]);

    // ── Transport / Days update ────────────────────────────────────────────────
    const handleTransportChange = useCallback(async (legIndex, mode) => {
        setTransportModes(prev => ({ ...prev, [legIndex]: mode }));
        try {
            await fetch(`${apiBase}/itinerary/update-leg`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, leg_index: legIndex, transport_mode: mode }),
            });
        } catch (err) { console.warn('Update-leg failed:', err); }
    }, [sessionId, apiBase]);

    const handleDaysChange = useCallback(async (stopIndex, days) => {
        setDaysPerStop(prev => ({ ...prev, [stopIndex]: days }));
        try {
            await fetch(`${apiBase}/itinerary/update-leg`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, leg_index: stopIndex, days_at_stop: days }),
            });
        } catch (err) { console.warn('Update-leg days failed:', err); }
    }, [sessionId, apiBase]);

    // ── Chat ───────────────────────────────────────────────────────────────────
    const opener = itinerary.conversation_opener || `We've built your ${itinerary.label} itinerary through ${stops.map(s => s.destination).join(' → ')}! Ask me anything or modify it using the controls on the right.`;

    const [initialized, setInitialized] = useState(false);
    if (!initialized) {
        setMessages([{ role: 'assistant', content: opener, id: 'opener' }]);
        setInitialized(true);
    }

    const handleSend = useCallback(async (text) => {
        setMessages(prev => [...prev, { role: 'user', content: text, id: Date.now() }]);
        setIsTyping(true);
        setLastActionApplied(null);

        try {
            const res = await fetch(`${apiBase}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, message: text }),
            });
            const data = await res.json();
            setIsTyping(false);
            setMessages(prev => [...prev, { role: 'assistant', content: data.message, id: Date.now() + 1 }]);

            if (data.action_applied) setLastActionApplied(data.action_applied);

            if (data.action === 'search_again' && data.updated_match) {
                // Shallow stop replacement for single-destination change
            }
            if (data.action === 'confirm_booking') {
                setTimeout(onConfirm, 1200);
            }
        } catch (err) {
            setIsTyping(false);
            setMessages(prev => [...prev, { role: 'assistant', content: "I had a small hiccup! Please try again.", id: Date.now() + 2 }]);
        }
    }, [sessionId, apiBase, onConfirm]);

    // ── Render ─────────────────────────────────────────────────────────────────
    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Top bar */}
            <div className="navbar-light px-6 py-3 flex items-center justify-between gap-4 sticky top-0 z-30">
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="btn-ghost text-sm">
                        <ArrowLeft size={16} /> Back to Options
                    </button>
                    <div className="h-5 w-px bg-gray-200" />
                    <div>
                        <h1 className="font-bold text-gray-900 text-sm">{itinerary.label}</h1>
                        <p className="text-xs text-gray-500">{stops.map(s => s.destination).join(' → ')}</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    {/* Summary stats */}
                    <div className="hidden md:flex items-center gap-4 text-sm">
                        <div className="text-center">
                            <p className="text-[10px] text-gray-400 uppercase tracking-wide">Total Cost</p>
                            <p className="font-bold text-gray-900">₹{totalPrice.toLocaleString('en-IN')}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-[10px] text-gray-400 uppercase tracking-wide">Total Days</p>
                            <p className="font-bold text-gray-900">{totalDays}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-[10px] text-gray-400 uppercase tracking-wide">Stops</p>
                            <p className="font-bold text-gray-900">{stops.length}</p>
                        </div>
                    </div>
                    <button
                        onClick={onConfirm}
                        className="btn-primary text-sm px-5 py-2"
                    >
                        ✓ Confirm & Book
                    </button>
                </div>
            </div>

            {/* 2-column layout */}
            <div className="flex flex-1 overflow-hidden">

                {/* LEFT: Chat panel (40%) */}
                <div className="w-full md:w-[42%] flex-none overflow-hidden border-r border-gray-200">
                    <ChatWindow
                        messages={messages}
                        isTyping={isTyping}
                        onSend={handleSend}
                        onConfirm={onConfirm}
                        isPopup={false}
                        actionApplied={lastActionApplied}
                        onApplyAction={() => setLastActionApplied(null)}
                    />
                </div>

                {/* RIGHT: Itinerary editor (60%) */}
                <div className="flex-1 overflow-y-auto px-6 py-5 scrollbar-hide">
                    {/* Route justification */}
                    {routeJustification && (
                        <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 mb-5 flex items-start gap-3">
                            <Info size={16} className="text-blue-500 flex-none mt-0.5" />
                            <div>
                                <p className="text-xs font-bold text-blue-700 mb-1 uppercase tracking-wide">Route Intelligence</p>
                                <p className="text-sm text-gray-700 leading-relaxed">{routeJustification}</p>
                            </div>
                        </div>
                    )}

                    {/* Drag hint */}
                    {stops.length > 1 && (
                        <p className="text-xs text-gray-400 mb-4 flex items-center gap-1.5">
                            <GripVertical size={12} />
                            Drag cards to reorder your cities
                        </p>
                    )}

                    {/* Stop cards */}
                    <div className="space-y-3">
                        {stops.map((stop, i) => (
                            <StopCard
                                key={`${stop.destination}-${i}`}
                                stop={stop}
                                index={i}
                                total={stops.length}
                                transport={transportModes[i] || 'flight'}
                                days={daysPerStop[i] || 2}
                                onTransportChange={handleTransportChange}
                                onDaysChange={handleDaysChange}
                                isDragging={dragIndex === i}
                                onDragStart={handleDragStart(i)}
                                onDragEnd={handleDragEnd}
                                onDragOver={handleDragOver(i)}
                                onDrop={handleDrop(i)}
                            />
                        ))}
                    </div>

                    {/* Bottom total */}
                    <div className="card-light mt-5 p-4 flex items-center justify-between">
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Total Estimated Cost (per person)</p>
                            <p className="text-2xl font-black text-gray-900 mt-0.5">₹{totalPrice.toLocaleString('en-IN')}</p>
                            <p className="text-xs text-gray-400">Flights + Hotels • {totalDays} day trip</p>
                        </div>
                        <button onClick={onConfirm} className="btn-primary px-6 py-3">
                            Book This Trip →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

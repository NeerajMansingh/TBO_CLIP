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
function StopCard({ stop, index, total, transport, days, onTransportChange, onDaysChange, isDragging, onDragStart, onDragEnd, onDragOver, onDrop, onCostUpdate }) {
    const [expanded, setExpanded] = useState(index === 0);
    const isNearby = !!stop.is_nearby;

    // Resolve photo: prefer local destinations file, then backend path, then null
    const localSlug = stop.destination
        ? stop.destination.toLowerCase().replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, '_')
        : null;
    const localPhoto = localSlug ? `${API_BASE}/destinations/${localSlug}/1.jpg` : null;
    const remotePhoto = stop.photo
        ? (stop.photo.startsWith('http') ? stop.photo : `${API_BASE}/${stop.photo}`)
        : null;
    const [photoErr, setPhotoErr] = useState(false);
    const photoUrl = !photoErr && localPhoto ? localPhoto : remotePhoto;

    const isMock = false; // Mock data has been removed — no more mock badges

    const [liveDetails, setLiveDetails] = useState({ hotels: stop.hotels || [], flights: stop.flights || [], initialized: false });
    const [loadingDetails, setLoadingDetails] = useState(false);
    const [selectedHotelIndex, setSelectedHotelIndex] = useState(0);
    const [selectedFlightIndex, setSelectedFlightIndex] = useState(0);

    React.useEffect(() => {
        if (!isNearby && !liveDetails.initialized) {
            setLoadingDetails(true);
            fetch(`${API_BASE}/tbo_details?tbo_id=${stop.tbo_id}&budget=${stop.price_per_person || 100000}`)
                .then(res => res.json())
                .then(data => {
                    setLiveDetails({ hotels: data.hotels || [], flights: data.flights || [], initialized: true });
                    setLoadingDetails(false);
                })
                .catch(() => {
                    setLiveDetails({ hotels: [], flights: [], initialized: true });
                    setLoadingDetails(false);
                });
        }
    }, [stop.tbo_id, isNearby, stop.price_per_person, liveDetails.initialized]);

    // Clamp selection indices to valid range after data loads
    const safeFlightIdx = Math.min(selectedFlightIndex, Math.max(0, liveDetails.flights.length - 1));
    const safeHotelIdx = Math.min(selectedHotelIndex, Math.max(0, liveDetails.hotels.length - 1));

    const selectedFlight = liveDetails.flights.length > 0 ? liveDetails.flights[safeFlightIdx] : null;
    const selectedHotel = liveDetails.hotels.length > 0 ? liveDetails.hotels[safeHotelIdx] : null;

    // Only compute real costs when TBO data is available.
    // If not loaded yet (loadingDetails) -> undefined (show spinner). If loaded but empty -> null (show N/A).
    const hasData = liveDetails.initialized;
    const flightCost = hasData && selectedFlight ? Number(selectedFlight.fare) : null;
    const hotelCost = hasData && selectedHotel ? Math.round(Number(selectedHotel.price_per_night) * (days || 2)) : null;
    const stopTotal = (flightCost !== null && hotelCost !== null) ? flightCost + hotelCost : null;

    React.useEffect(() => {
        // Only propagate real cost — propagate 0 when no data so global total isn't inflated
        if (onCostUpdate) onCostUpdate(index, stopTotal ?? 0);
    }, [index, stopTotal, onCostUpdate]);

    // Estimate travel TIME for ground transport (rough: 50km/h avg for bus/drive, 80km/h for train)
    // distance_km is available on nearby stops; for primary stops we don't have it, so skip the estimate
    const distKm = stop.distance_km || null;
    function travelTimeLabel(mode) {
        if (!distKm) return '';
        const hours = mode === 'train' ? distKm / 80 : distKm / 50;
        if (hours < 1) return ` (~${Math.round(hours * 60)}min)`;
        return ` (~${hours.toFixed(1)}h)`;
    }

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
                        {isNearby && (
                            <span className="text-[9px] font-bold bg-emerald-100 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full whitespace-nowrap">
                                📍 Nearby
                            </span>
                        )}
                        {isMock && <span className="mock-badge">Mock</span>}
                    </div>
                    <p className="text-xs text-gray-500 truncate">{stop.tagline || (isNearby ? stop.category : 'India')}</p>
                </div>

                <div className="flex items-center gap-2 flex-none">
                    {!isNearby && (
                        <span className="text-sm font-bold text-gray-900">
                            {loadingDetails
                                ? <span className="text-xs text-gray-400 animate-pulse">Fetching…</span>
                                : stopTotal !== null
                                    ? `₹${stopTotal.toLocaleString('en-IN')}`
                                    : <span className="text-xs text-gray-400">Price TBD</span>
                            }
                        </span>
                    )}
                    {isNearby && stop.distance_km && (
                        <span className="text-xs text-gray-500">{stop.distance_km}km away</span>
                    )}
                    <button onClick={() => setExpanded(e => !e)} className="text-gray-400 hover:text-gray-700 transition-colors">
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                </div>
            </div>

            {/* Expanded details */}
            {expanded && (
                <div className="p-4 space-y-4 bg-gray-50/50 animate-slide-up">
                    {/* Nearby place: show visit info instead of cost breakdown */}
                    {isNearby ? (
                        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3 flex items-center gap-3">
                            <span className="text-2xl">📍</span>
                            <div>
                                <p className="text-xs font-bold text-emerald-700">Nearby Day Trip</p>
                                <p className="text-xs text-gray-600 mt-0.5">{stop.tagline}</p>
                                {stop.visit_duration && (
                                    <p className="text-[11px] text-emerald-600 mt-1 font-semibold">⏱ Suggested: {stop.visit_duration}</p>
                                )}
                            </div>
                        </div>
                    ) : (
                        /* Cost breakdown — only show when real data available */
                        <div className="grid grid-cols-3 gap-2 text-center">
                            <div className="bg-white rounded-xl p-2 border border-gray-100">
                                <p className="text-[10px] text-gray-400 mb-0.5">Flight</p>
                                <p className="text-sm font-bold text-gray-800">
                                    {loadingDetails ? '…' : flightCost !== null ? `₹${flightCost.toLocaleString('en-IN')}` : 'N/A'}
                                </p>
                            </div>
                            <div className="bg-white rounded-xl p-2 border border-gray-100">
                                <p className="text-[10px] text-gray-400 mb-0.5">Hotel ({days || 2}n)</p>
                                <p className="text-sm font-bold text-gray-800">
                                    {loadingDetails ? '…' : hotelCost !== null ? `₹${hotelCost.toLocaleString('en-IN')}` : 'N/A'}
                                </p>
                            </div>
                            <div className="bg-blue-50 rounded-xl p-2 border border-blue-100">
                                <p className="text-[10px] text-blue-600 mb-0.5">Total</p>
                                <p className="text-sm font-bold text-blue-700">
                                    {loadingDetails ? '…' : stopTotal !== null ? `₹${stopTotal.toLocaleString('en-IN')}` : 'TBD'}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Transport selector — with travel time hints for ground modes */}
                    {!isNearby && index < total - 1 && (
                        <div>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">Travel Mode to Next Stop</p>
                            <div className="grid grid-cols-4 gap-1.5">
                                {TRANSPORT_OPTIONS.map(opt => {
                                    const timeHint = (opt.value !== 'flight') ? travelTimeLabel(opt.value) : '';
                                    const isSelected = transport === opt.value;
                                    return (
                                        <button
                                            key={opt.value}
                                            onClick={() => onTransportChange(index, opt.value)}
                                            className={`py-2 px-1 rounded-lg border text-xs font-semibold transition-all text-center ${isSelected
                                                ? 'border-blue-500 bg-blue-50 text-blue-700'
                                                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                                                }`}
                                        >
                                            <div>{opt.icon} {opt.label}</div>
                                            {timeHint && (
                                                <div className={`text-[9px] mt-0.5 font-normal ${isSelected ? 'text-blue-500' : 'text-gray-400'}`}>
                                                    {timeHint}
                                                </div>
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    )}

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

                    {/* Flight & Hotels — live TBO data */}
                    {!isNearby && (
                        <div className="space-y-4">
                            {loadingDetails ? (
                                <div className="text-center py-4 text-xs text-gray-500 animate-pulse">
                                    Fetching live flights and hotels...
                                </div>
                            ) : (
                                <>
                                    {/* Flights */}
                                    <div>
                                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">Flight Options (From Origin)</p>
                                        {liveDetails.flights.length > 0 ? (
                                            <div className="space-y-2 max-h-40 overflow-y-auto pr-1 stylish-scrollbar">
                                                {liveDetails.flights.map((flight, i) => (
                                                    <div
                                                        key={i}
                                                        onClick={() => setSelectedFlightIndex(i)}
                                                        className={`bg-white rounded-xl p-3 border cursor-pointer transition-all flex items-center justify-between ${safeFlightIdx === i ? 'border-blue-500 ring-1 ring-blue-500 bg-blue-50/30' : 'border-gray-200 hover:border-blue-300'}`}
                                                    >
                                                        <div className="flex items-center gap-2">
                                                            <Plane size={14} className={safeFlightIdx === i ? "text-blue-500" : "text-gray-400"} />
                                                            <p className="text-xs font-bold text-gray-800">{flight.airline}</p>
                                                        </div>
                                                        <p className="text-xs font-bold text-gray-900">₹{Number(flight.fare).toLocaleString('en-IN')}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 border border-gray-100 flex items-center gap-2">
                                                <Plane size={13} className="text-gray-400" /> No flights available from this origin.
                                            </div>
                                        )}
                                    </div>

                                    {/* Hotels */}
                                    <div>
                                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">Hotel Options</p>
                                        {liveDetails.hotels.length > 0 ? (
                                            <div className="space-y-2 max-h-60 overflow-y-auto pr-1 stylish-scrollbar">
                                                {liveDetails.hotels.map((hotel, i) => (
                                                    <div
                                                        key={i}
                                                        onClick={() => setSelectedHotelIndex(i)}
                                                        className={`bg-white rounded-xl p-3 border cursor-pointer transition-all flex items-center gap-3 ${safeHotelIdx === i ? 'border-blue-500 ring-1 ring-blue-500 bg-blue-50/30' : 'border-gray-200 hover:border-blue-300'}`}
                                                    >
                                                        {hotel.photo && (
                                                            <img src={hotel.photo} alt={hotel.name} className="w-12 h-12 rounded-lg object-cover flex-none" onError={e => e.target.style.display = 'none'} />
                                                        )}
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-xs font-bold text-gray-800 truncate">{hotel.name}</p>
                                                            <div className="flex items-center gap-1 mt-0.5">
                                                                <Star size={10} className="text-amber-400 fill-amber-400" />
                                                                <span className="text-[10px] font-semibold text-gray-700">{hotel.rating} Stars</span>
                                                                <span className="text-[10px] text-gray-400 ml-1">• ₹{(Number(hotel.price_per_night) || 0).toLocaleString('en-IN')}/night</span>
                                                                <span className="text-[10px] text-gray-500 ml-1">× {days || 2}d = ₹{Math.round((Number(hotel.price_per_night) || 0) * (days || 2)).toLocaleString('en-IN')}</span>
                                                            </div>
                                                        </div>
                                                        {safeHotelIdx === i && (
                                                            <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center flex-none">
                                                                <svg width="12" height="10" viewBox="0 0 14 10" fill="none"><path d="M1 5L5 9L13 1" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500 border border-gray-100 flex items-center gap-2">
                                                🏨 Hotels not available for this destination at the moment.
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
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
    const [stopTotals, setStopTotals] = useState({});
    const baseTotalPrice = itinerary.total_price || 0;

    // Compute derived total price based on selected hotels/flights.
    // stopTotals[i] = 0 means no real TBO data yet (StopCard propagates 0 when null).
    // Only show a real total when at least one stop has real data.
    const totalPrice = React.useMemo(() => {
        const realTotals = Object.values(stopTotals).filter(v => v > 0);
        if (realTotals.length === 0) return null; // nothing loaded yet
        return realTotals.reduce((a, b) => a + b, 0);
    }, [stopTotals]);

    const handleCostUpdate = useCallback((index, stopTotal) => {
        setStopTotals(prev => {
            if (prev[index] === stopTotal) return prev;
            return { ...prev, [index]: stopTotal };
        });
    }, []);

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
                // Also reset stopTotals to resync, or let them recalculate
                setStopTotals({});
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
                            <p className="font-bold text-gray-900">
                                {totalPrice !== null ? `₹${totalPrice.toLocaleString('en-IN')}` : 'Fetching…'}
                            </p>
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
                        {stops.map((stop, index) => (
                            <StopCard
                                key={`${stop.destination}-${index}`}
                                stop={stop}
                                index={index}
                                total={stops.length}
                                transport={transportModes[index] || 'flight'}
                                days={daysPerStop[index] || 2}
                                onTransportChange={handleTransportChange}
                                onDaysChange={handleDaysChange}
                                onCostUpdate={handleCostUpdate}
                                isDragging={dragIndex === index}
                                onDragStart={handleDragStart(index)}
                                onDragEnd={handleDragEnd}
                                onDragOver={handleDragOver(index)}
                                onDrop={handleDrop(index)}
                            />
                        ))}
                    </div>

                    {/* Bottom total */}
                    <div className="card-light mt-5 p-4 flex items-center justify-between">
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">Total Estimated Cost (per person)</p>
                            <p className="text-2xl font-black text-gray-900 mt-0.5">
                                {totalPrice !== null
                                    ? `₹${totalPrice.toLocaleString('en-IN')}`
                                    : <span className="text-lg text-gray-400">Fetching prices…</span>
                                }
                            </p>
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

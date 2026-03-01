import React, { useState, useEffect, useCallback } from 'react';
import {
    ArrowLeft, ArrowRight, MapPin, Star, Clock, Tag,
    ChevronDown, ChevronUp, CheckSquare, Square,
    Compass, Mountain, Waves, Landmark, Trees, RefreshCcw,
    Info, Calendar, Users
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// ── Utility: get local destination image URL ────────────────────────────────
function getLocalImageUrl(destinationName, fallbackUrl) {
    if (!destinationName) return fallbackUrl;
    // Map destination name to folder slug (lowercase, spaces→underscores, etc.)
    const slug = destinationName
        .toLowerCase()
        .replace(/[^a-z0-9\s_-]/g, '')
        .replace(/\s+/g, '_')
        .replace(/-/g, '_')
        // Special overrides for known folder names
        .replace('andaman_islands', 'andaman')
        .replace('leh_ladakh', 'leh')
        .replace('kerala_hill_stations', 'kerala_hills')
        .replace('udaipur', 'udaipur')
        .replace('spiti_valley', 'spiti')
        .replace('ziro_valley', 'ziro');
    return `${API_BASE}/destinations/${slug}/1.jpg`;
}

// ── Utility: category metadata ────────────────────────────────────────────────
const CATEGORY_META = {
    historical: { icon: Landmark, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', label: 'Historical' },
    nature: { icon: Trees, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'Nature' },
    adventure: { icon: Mountain, color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200', label: 'Adventure' },
    cultural: { icon: Compass, color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-200', label: 'Cultural' },
    beach: { icon: Waves, color: 'text-blue-500', bg: 'bg-blue-50', border: 'border-blue-200', label: 'Beach' },
};

function getCategoryMeta(cat) {
    return CATEGORY_META[cat?.toLowerCase()] || CATEGORY_META.cultural;
}

// ── Star Rating Display ───────────────────────────────────────────────────────
function StarRating({ rating }) {
    const full = Math.floor(rating);
    const half = rating - full >= 0.5;
    return (
        <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map(i => (
                <Star
                    key={i}
                    size={12}
                    className={i <= full ? 'text-amber-400 fill-amber-400' : i === full + 1 && half ? 'text-amber-400 fill-amber-200' : 'text-gray-200 fill-gray-200'}
                />
            ))}
            <span className="text-xs text-gray-500 ml-1 font-semibold">{rating.toFixed(1)}</span>
        </div>
    );
}

// ── Image Lightbox (fullscreen overlay) ─────────────────────────────────────
function ImageLightbox({ src, alt, onClose }) {
    if (!src) return null;
    return (
        <div
            className="fixed inset-0 z-[999] flex items-center justify-center bg-black/85 backdrop-blur-sm animate-fade-in"
            onClick={onClose}
        >
            <div className="relative max-w-4xl max-h-[90vh] w-full mx-4" onClick={e => e.stopPropagation()}>
                <img
                    src={src}
                    alt={alt}
                    className="w-full h-full object-contain rounded-2xl shadow-2xl max-h-[85vh]"
                />
                <button
                    onClick={onClose}
                    className="absolute top-3 right-3 bg-white/20 hover:bg-white/40 text-white backdrop-blur-md rounded-full p-2 transition-all duration-150"
                >
                    ×
                </button>
                <p className="text-white/80 text-center text-sm mt-3 font-semibold">{alt}</p>
            </div>
        </div>
    );
}

// ── Individual Nearby Place Card (accordion) ───────────────────────────────
function NearbyPlaceCard({ place, isSelected, onToggle, onEnlargeImage }) {
    const [expanded, setExpanded] = useState(false);
    const catMeta = getCategoryMeta(place.category);
    const CatIcon = catMeta.icon;
    const imgUrl = place.image_path ? `${API_BASE}${place.image_path}` : null;

    return (
        <div
            className={`rounded-2xl border transition-all duration-200 overflow-hidden
                ${isSelected
                    ? 'border-blue-400 bg-blue-50/60 shadow-md'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }`}
        >
            {/* Banner image — full width, taller, clickable */}
            {imgUrl && (
                <div className="relative h-36 overflow-hidden bg-gray-100 group">
                    <img
                        src={imgUrl}
                        alt={place.name}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    {/* Dark gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                    {/* Enlarge button */}
                    <button
                        onClick={() => onEnlargeImage(imgUrl, place.name)}
                        className="absolute top-2 right-2 bg-black/40 hover:bg-black/70 text-white rounded-lg p-1.5 backdrop-blur-sm transition-all duration-150 opacity-0 group-hover:opacity-100"
                        title="Enlarge image"
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="15 3 21 3 21 9" />
                            <polyline points="9 21 3 21 3 15" />
                            <line x1="21" y1="3" x2="14" y2="10" />
                            <line x1="3" y1="21" x2="10" y2="14" />
                        </svg>
                    </button>
                    {/* Category badge on image */}
                    <div className="absolute bottom-2 left-2">
                        <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full border ${catMeta.bg} ${catMeta.color} ${catMeta.border}`}>
                            <CatIcon size={9} />
                            {catMeta.label}
                        </span>
                    </div>
                </div>
            )}

            {/* Header row */}
            <div className="flex items-start gap-3 p-3.5">
                {/* Checkbox */}
                <button
                    onClick={onToggle}
                    className="flex-none mt-0.5 transition-transform hover:scale-110"
                    aria-label={isSelected ? 'Deselect place' : 'Select place'}
                >
                    {isSelected
                        ? <CheckSquare size={20} className="text-blue-600" />
                        : <Square size={20} className="text-gray-300 hover:text-gray-500" />
                    }
                </button>

                {/* Info (no image thumbnail here — it's the banner above) */}
                <div className="flex-1 min-w-0" onClick={() => setExpanded(e => !e)} style={{ cursor: 'pointer' }}>
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                        <h4 className="font-bold text-gray-900 text-sm leading-tight">{place.name}</h4>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-[11px] text-gray-500 flex items-center gap-1">
                            <MapPin size={9} className="text-gray-400" />
                            {place.distance_km} km away
                        </span>
                        <span className="text-[11px] text-gray-500 flex items-center gap-1">
                            <Clock size={9} className="text-gray-400" />
                            {Math.floor(place.travel_time_min / 60) > 0
                                ? `${Math.floor(place.travel_time_min / 60)}h ${place.travel_time_min % 60}m`
                                : `${place.travel_time_min}m`} drive
                        </span>
                    </div>
                </div>

                {/* Expand toggle */}
                <button
                    onClick={() => setExpanded(e => !e)}
                    className="flex-none text-gray-400 hover:text-gray-700 transition-colors p-0.5"
                >
                    {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
            </div>

            {/* Accordion body */}
            <div
                style={{
                    maxHeight: expanded ? '400px' : '0px',
                    transition: 'max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
                    overflow: 'hidden',
                }}
            >
                <div className="px-4 pb-4 space-y-3 border-t border-gray-100 pt-3">
                    {/* Description */}
                    <p className="text-xs text-gray-600 leading-relaxed">{place.description}</p>

                    {/* Highlights */}
                    {place.highlights?.length > 0 && (
                        <div>
                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5">Key Highlights</p>
                            <div className="flex flex-wrap gap-1.5">
                                {place.highlights.map((h, i) => (
                                    <span key={i} className="text-[10px] font-medium bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full border border-gray-200">
                                        {h}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Stats row */}
                    <div className="grid grid-cols-3 gap-2">
                        <div className="bg-gray-50 rounded-xl p-2 text-center border border-gray-100">
                            <p className="text-[9px] text-gray-400 font-bold uppercase tracking-wide mb-0.5">Duration</p>
                            <p className="text-[11px] font-bold text-gray-700">{place.visit_duration}</p>
                        </div>
                        <div className={`rounded-xl p-2 text-center border ${catMeta.bg} ${catMeta.border}`}>
                            <p className="text-[9px] text-gray-400 font-bold uppercase tracking-wide mb-0.5">Category</p>
                            <p className={`text-[11px] font-bold ${catMeta.color}`}>{catMeta.label}</p>
                        </div>
                        <div className="bg-gray-50 rounded-xl p-2 text-center border border-gray-100">
                            <p className="text-[9px] text-gray-400 font-bold uppercase tracking-wide mb-0.5">Rating</p>
                            <div className="flex justify-center">
                                <StarRating rating={place.rating} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── Itinerary Preview (live updates) ─────────────────────────────────────────
function ItineraryPreview({ primaryStop, selectedPlaces, onBuildItinerary, isLoading }) {
    const totalStops = 1 + selectedPlaces.length;
    const estimatedDays = Math.max(2, totalStops * 2);

    return (
        <div className="card-light p-5 sticky bottom-0 bg-white/95 backdrop-blur-md border-t border-gray-200 shadow-xl mt-4">
            <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-2">Your Itinerary Preview</p>

                    {/* Stops chain */}
                    <div className="flex items-center gap-1.5 flex-wrap">
                        {/* Primary */}
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full bg-blue-600 flex-none" />
                            <span className="text-xs font-bold text-gray-900">{primaryStop?.destination || 'Primary Destination'}</span>
                        </div>

                        {selectedPlaces.map((place, i) => (
                            <React.Fragment key={place.name}>
                                <svg width="16" height="8" viewBox="0 0 16 8" className="flex-none">
                                    <path d="M0 4 L12 4 M10 1 L15 4 L10 7" stroke="#CBD5E1" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                                <div className="flex items-center gap-1">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500 flex-none" />
                                    <span className="text-xs font-semibold text-gray-700">{place.name}</span>
                                </div>
                            </React.Fragment>
                        ))}

                        {selectedPlaces.length === 0 && (
                            <span className="text-xs text-gray-400 italic ml-1">Pick nearby places →</span>
                        )}
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-4 mt-2">
                        <span className="text-[11px] text-gray-500 flex items-center gap-1">
                            <MapPin size={10} className="text-blue-400" />
                            {totalStops} {totalStops === 1 ? 'stop' : 'stops'}
                        </span>
                        <span className="text-[11px] text-gray-500 flex items-center gap-1">
                            <Calendar size={10} className="text-blue-400" />
                            ~{estimatedDays} days
                        </span>
                    </div>
                </div>

                <button
                    onClick={onBuildItinerary}
                    disabled={isLoading}
                    className="btn-primary text-sm px-5 py-2.5 flex-none whitespace-nowrap"
                >
                    {isLoading ? (
                        <span className="flex items-center gap-2">
                            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                                <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="3" strokeDasharray="60" strokeDashoffset="20" />
                            </svg>
                            Building…
                        </span>
                    ) : (
                        <>Build My Itinerary <ArrowRight size={14} /></>
                    )}
                </button>
            </div>
        </div>
    );
}

// Ranked Search Result Picker Card
// Each card = one independently-ranked result (Card 1 = best match, Card 2 = 2nd, Card 3 = 3rd).
function RankedCard({ itinerary, rank, isActive, onSelect }) {
    const stop = itinerary?.stops?.[0] || {};
    const [imgErr, setImgErr] = React.useState(false);
    const slug = (stop.destination || '')
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, '_');
    const localImg = slug ? `${API_BASE}/destinations/${slug}/1.jpg` : null;
    const imgSrc = !imgErr && localImg
        ? localImg
        : stop.photo?.startsWith('http') ? stop.photo : null;

    const rankColors = [
        { badge: 'bg-violet-600 text-white', ring: 'ring-violet-400', border: 'border-violet-300', label: 'text-violet-700' },
        { badge: 'bg-blue-600 text-white', ring: 'ring-blue-400', border: 'border-blue-200', label: 'text-blue-700' },
        { badge: 'bg-emerald-600 text-white', ring: 'ring-emerald-400', border: 'border-emerald-200', label: 'text-emerald-700' },
    ];
    const colors = rankColors[(rank - 1) % 3];
    const rankLabel = ['Best Match', '2nd Match', '3rd Match'][rank - 1] || `Match ${rank}`;

    return (
        <button
            onClick={onSelect}
            className={`relative flex items-center gap-3 rounded-2xl border-2 p-3 text-left transition-all duration-200 w-full ${isActive
                ? `${colors.border} ${colors.ring} ring-2 bg-white shadow-md`
                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }`}
        >
            <div className={`absolute -top-2 -left-1 text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full ${colors.badge}`}>
                #{rank}
            </div>
            <div className="w-14 h-14 rounded-xl overflow-hidden bg-gray-100 flex-none">
                {imgSrc ? (
                    <img
                        src={imgSrc}
                        alt={stop.destination}
                        className="w-full h-full object-cover"
                        onError={() => setImgErr(true)}
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-blue-100 to-indigo-200 flex items-center justify-center">
                        <MapPin size={20} className="text-blue-400" />
                    </div>
                )}
            </div>
            <div className="flex-1 min-w-0">
                <p className={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${colors.label}`}>{rankLabel}</p>
                <h4 className="font-bold text-gray-900 text-sm leading-tight truncate">{stop.destination || 'Loading…'}</h4>
                {stop.category && (
                    <p className="text-[10px] text-gray-500 capitalize mt-0.5">{stop.category}</p>
                )}
            </div>
            {isActive && (
                <div className="flex-none w-5 h-5 rounded-full bg-violet-500 flex items-center justify-center">
                    <svg width="10" height="8" viewBox="0 0 14 10" fill="none">
                        <path d="M1 5L5 9L13 1" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </div>
            )}
        </button>
    );
}


// Main DestinationSelectionScreen
export default function DestinationSelectionScreen({
    primaryItinerary,         // The top-ranked itinerary (rank 1)
    allItineraries = [],      // All 3 ranked results
    originCity,
    travelMonth,
    routeJustification,
    onBack,
    onBuildItinerary,         // (primaryItinerary, selectedNearbyPlaces) => void
}) {
    // Which of the 3 ranked cards is the user currently viewing
    const [activeIndex, setActiveIndex] = React.useState(0);
    const activePrimary = allItineraries.length > 0 ? allItineraries[activeIndex] : primaryItinerary;
    const primaryStop = activePrimary?.stops?.[0] || {};

    const [nearbyPlaces, setNearbyPlaces] = useState([]);
    const [selectedPlaceNames, setSelectedPlaceNames] = useState(new Set());
    const [loadingNearby, setLoadingNearby] = useState(false);
    const [nearbyError, setNearbyError] = useState(null);
    const [building, setBuilding] = useState(false);
    const [imgError, setImgError] = useState(false);
    const [lightbox, setLightbox] = useState(null);

    // Reset image error when destination changes
    React.useEffect(() => { setImgError(false); }, [primaryStop.destination]);

    // Resolve hero image: prefer local file, fall back to backend photo
    const localImgUrl = getLocalImageUrl(primaryStop.destination, null);
    const heroUrl = !imgError && localImgUrl
        ? localImgUrl
        : (primaryStop.photo?.startsWith('http')
            ? primaryStop.photo
            : primaryStop.photo ? `${API_BASE}/${primaryStop.photo}` : null);

    // Fetch nearby places when active destination changes
    useEffect(() => {
        if (!primaryStop.destination) return;
        setLoadingNearby(true);
        setNearbyError(null);
        setSelectedPlaceNames(new Set());

        fetch(`${API_BASE}/nearby?destination=${encodeURIComponent(primaryStop.destination)}`)
            .then(r => r.json())
            .then(data => {
                setNearbyPlaces(data.nearby_places || []);
                setLoadingNearby(false);
            })
            .catch(err => {
                console.warn('Failed to fetch nearby places:', err);
                setNearbyError('Could not load nearby places.');
                setLoadingNearby(false);
            });
    }, [primaryStop.destination]);

    const togglePlace = useCallback((placeName) => {
        setSelectedPlaceNames(prev => {
            const next = new Set(prev);
            if (next.has(placeName)) next.delete(placeName);
            else next.add(placeName);
            return next;
        });
    }, []);

    const selectedPlaces = nearbyPlaces.filter(p => selectedPlaceNames.has(p.name));

    const handleBuild = useCallback(async () => {
        setBuilding(true);
        await new Promise(r => setTimeout(r, 400));
        onBuildItinerary(activePrimary, selectedPlaces);
        setBuilding(false);
    }, [activePrimary, selectedPlaces, onBuildItinerary]);

    const catCounts = nearbyPlaces.reduce((acc, p) => {
        acc[p.category] = (acc[p.category] || 0) + 1;
        return acc;
    }, {});

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col animate-fade-in">
            {/* Image lightbox */}
            <ImageLightbox
                src={lightbox?.src}
                alt={lightbox?.alt}
                onClose={() => setLightbox(null)}
            />
            {/* ── Top bar ──────────────────────────────────────────────── */}
            <div className="navbar-light px-6 py-3 flex items-center justify-between sticky top-0 z-30">
                <div className="flex items-center gap-3">
                    <button onClick={onBack} className="btn-ghost text-sm">
                        <ArrowLeft size={16} /> New Search
                    </button>
                    <div className="h-5 w-px bg-gray-200 hidden sm:block" />
                    <div className="hidden sm:block">
                        <p className="text-xs text-gray-400 font-medium">Customise your trip</p>
                        <h1 className="font-bold text-gray-900 text-sm leading-tight">
                            {primaryStop.destination || 'Destination'} & Nearby Places
                        </h1>
                    </div>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-500">
                    {travelMonth && (
                        <span className="hidden md:flex items-center gap-1 text-xs bg-blue-50 text-blue-600 border border-blue-200 px-3 py-1 rounded-full font-semibold">
                            📅 {travelMonth}
                        </span>
                    )}
                    {originCity && (
                        <span className="hidden md:flex items-center gap-1 text-xs text-gray-500">
                            ✈️ From {originCity}
                        </span>
                    )}
                </div>
            </div>

            {/* ── Ranked Result Picker (3 cards) ───────────────────────── */}
            {allItineraries.length > 1 && (
                <div className="bg-white border-b border-gray-100 px-4 py-3">
                    <p className="text-[11px] text-gray-400 font-semibold uppercase tracking-widest mb-2.5">
                        🎯 Top 3 Ranked Matches — pick your destination
                    </p>
                    <div className="grid grid-cols-3 gap-3">
                        {allItineraries.slice(0, 3).map((itin, idx) => (
                            <RankedCard
                                key={idx}
                                itinerary={itin}
                                rank={idx + 1}
                                isActive={activeIndex === idx}
                                onSelect={() => {
                                    setActiveIndex(idx);
                                    setSelectedPlaceNames(new Set());
                                }}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* ── Main 2-column layout ─────────────────────────────────── */}
            <div className="flex flex-1 overflow-hidden">

                {/* ── LEFT: Primary Destination Hero (60%) ─────────────── */}
                <div className="w-full lg:w-[58%] flex-none overflow-y-auto scrollbar-hide">

                    {/* Hero image */}
                    <div className="relative h-72 md:h-96 overflow-hidden bg-gray-200">
                        {heroUrl ? (
                            <img
                                src={heroUrl}
                                alt={primaryStop.destination}
                                className="w-full h-full object-cover"
                                onError={() => setImgError(true)}
                            />
                        ) : (
                            <div className="w-full h-full bg-gradient-to-br from-blue-100 to-indigo-200 flex items-center justify-center">
                                <MapPin size={48} className="text-blue-300" />
                            </div>
                        )}

                        {/* Gradient overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent" />

                        {/* Destination title overlay */}
                        <div className="absolute bottom-0 left-0 right-0 p-6">
                            <div className="flex items-end justify-between">
                                <div>
                                    <p className="text-white/70 text-xs font-semibold uppercase tracking-widest mb-1 flex items-center gap-1.5">
                                        <MapPin size={10} /> {activePrimary?.region || 'India'}
                                    </p>
                                    <h2 className="text-white font-black text-3xl md:text-4xl leading-tight drop-shadow-lg">
                                        {primaryStop.destination}
                                    </h2>
                                    {primaryStop.tagline && (
                                        <p className="text-white/80 text-sm mt-1 font-medium italic">
                                            "{primaryStop.tagline}"
                                        </p>
                                    )}
                                </div>
                                <div className="text-right hidden sm:block">
                                    <p className="text-white/60 text-[10px] uppercase tracking-wider">From</p>
                                    <p className="text-white font-black text-2xl">
                                        ₹{(primaryStop.price_per_person || 0).toLocaleString('en-IN')}
                                    </p>
                                    <p className="text-white/60 text-[10px]">per person</p>
                                </div>
                            </div>
                        </div>

                        {/* Primary badge */}
                        <div className="absolute top-4 left-4">
                            <span className="bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-full shadow-lg">
                                ⭐ Primary Destination
                            </span>
                        </div>
                    </div>

                    {/* Destination details card */}
                    <div className="px-5 py-5 space-y-4">

                        {/* Route justification */}
                        {routeJustification && (
                            <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 flex items-start gap-3">
                                <Info size={16} className="text-blue-500 flex-none mt-0.5" />
                                <div>
                                    <p className="text-[10px] font-bold text-blue-700 uppercase tracking-wider mb-1">Why This Destination?</p>
                                    <p className="text-sm text-gray-700 leading-relaxed">{routeJustification}</p>
                                </div>
                            </div>
                        )}

                        {/* Key info chips */}
                        <div className="flex flex-wrap gap-2">
                            {primaryItinerary?.label && (
                                <span className="section-badge">{primaryItinerary.label}</span>
                            )}
                            {primaryItinerary?.stop_count > 1 && (
                                <span className="section-badge">{primaryItinerary.stop_count} cities</span>
                            )}
                            {primaryStop.best_season && (
                                <span className="section-badge">🌤 {primaryStop.best_season}</span>
                            )}
                        </div>




                        {/* Nearby category summary */}
                        {Object.keys(catCounts).length > 0 && (
                            <div className="card-light p-4">
                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">Nearby Experiences</p>
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(catCounts).map(([cat, count]) => {
                                        const meta = getCategoryMeta(cat);
                                        const Icon = meta.icon;
                                        return (
                                            <div key={cat} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold ${meta.bg} ${meta.color} ${meta.border}`}>
                                                <Icon size={11} />
                                                {count} {meta.label}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Live preview (desktop sticky, shown here on mobile) */}
                        <div className="lg:hidden">
                            <ItineraryPreview
                                primaryStop={primaryStop}
                                selectedPlaces={selectedPlaces}
                                onBuildItinerary={handleBuild}
                                isLoading={building}
                            />
                        </div>
                    </div>
                </div>

                {/* ── RIGHT: Nearby Places Panel (40%) ─────────────────── */}
                <div className="hidden lg:flex flex-col flex-1 border-l border-gray-200 bg-white overflow-hidden">
                    {/* Panel header */}
                    <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10">
                        <div>
                            <h3 className="font-bold text-gray-900 text-sm">Nearby Places</h3>
                            <p className="text-xs text-gray-400 mt-0.5">
                                Within 70 km of {primaryStop.destination} •
                                {selectedPlaceNames.size > 0
                                    ? <span className="text-blue-600 font-bold"> {selectedPlaceNames.size} selected</span>
                                    : ' None selected yet'}
                            </p>
                        </div>
                        {selectedPlaceNames.size > 0 && (
                            <button
                                onClick={() => setSelectedPlaceNames(new Set())}
                                className="text-xs text-gray-400 hover:text-gray-700 flex items-center gap-1 transition-colors"
                            >
                                <RefreshCcw size={11} /> Clear
                            </button>
                        )}
                    </div>

                    {/* Scrollable place list */}
                    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scrollbar-hide">
                        {loadingNearby && (
                            <div className="space-y-3">
                                {[1, 2, 3, 4].map(i => (
                                    <div key={i} className="h-20 skeleton rounded-2xl" />
                                ))}
                            </div>
                        )}

                        {nearbyError && (
                            <div className="text-center py-10 text-gray-400">
                                <MapPin size={32} className="mx-auto mb-2 opacity-30" />
                                <p className="text-sm">{nearbyError}</p>
                            </div>
                        )}

                        {!loadingNearby && !nearbyError && nearbyPlaces.length === 0 && (
                            <div className="text-center py-10 text-gray-400">
                                <Compass size={32} className="mx-auto mb-2 opacity-30" />
                                <p className="text-sm">No nearby places found.</p>
                            </div>
                        )}

                        {!loadingNearby && nearbyPlaces.map((place, i) => (
                            <NearbyPlaceCard
                                key={place.name + i}
                                place={place}
                                isSelected={selectedPlaceNames.has(place.name)}
                                onToggle={() => togglePlace(place.name)}
                                onEnlargeImage={(src, alt) => setLightbox({ src, alt })}
                            />
                        ))}
                    </div>

                    {/* Sticky itinerary preview at the bottom of right panel */}
                    <div className="border-t border-gray-100">
                        <div className="px-4 py-4">
                            <ItineraryPreview
                                primaryStop={primaryStop}
                                selectedPlaces={selectedPlaces}
                                onBuildItinerary={handleBuild}
                                isLoading={building}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Mobile: Nearby places below (shown beneath hero on mobile) ── */}
            <div className="lg:hidden px-4 py-4 space-y-3 bg-gray-50 border-t border-gray-100">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="font-bold text-gray-900 text-sm">Nearby Places</h3>
                        <p className="text-xs text-gray-400 mt-0.5">
                            Within 70km •
                            {selectedPlaceNames.size > 0
                                ? <span className="text-blue-600 font-bold"> {selectedPlaceNames.size} selected</span>
                                : ' None selected'}
                        </p>
                    </div>
                    {selectedPlaceNames.size > 0 && (
                        <button onClick={() => setSelectedPlaceNames(new Set())} className="text-xs text-gray-400 hover:text-gray-700 flex items-center gap-1">
                            <RefreshCcw size={11} /> Clear
                        </button>
                    )}
                </div>

                {loadingNearby && <div className="h-16 skeleton rounded-2xl" />}
                {!loadingNearby && nearbyPlaces.map((place, i) => (
                    <NearbyPlaceCard
                        key={place.name + i}
                        place={place}
                        isSelected={selectedPlaceNames.has(place.name)}
                        onToggle={() => togglePlace(place.name)}
                        onEnlargeImage={(src, alt) => setLightbox({ src, alt })}
                    />
                ))}
            </div>
        </div>
    );
}

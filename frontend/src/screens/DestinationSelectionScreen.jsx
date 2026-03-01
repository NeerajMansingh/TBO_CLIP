import React, { useState, useEffect, useCallback } from 'react';
import {
    ArrowLeft, ArrowRight, MapPin, Star, Clock,
    Check, Plus, Compass, Mountain, Waves, Landmark, Trees,
    Info, Calendar, Sparkles, Loader2, Award, ChevronDown, ChevronUp,
    RefreshCcw, Users
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// ── Utility: get local destination image URL ────────────────────────────────
function getLocalImageUrl(destinationName) {
    if (!destinationName) return null;
    const slug = destinationName
        .toLowerCase()
        .replace(/[^a-z0-9\s_-]/g, '')
        .replace(/\s+/g, '_')
        .replace(/-/g, '_')
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
    historical: { icon: Landmark, color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-100', label: 'History' },
    nature: { icon: Trees, color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-100', label: 'Nature' },
    adventure: { icon: Mountain, color: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-100', label: 'Adventure' },
    cultural: { icon: Compass, color: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-100', label: 'Culture' },
    beach: { icon: Waves, color: 'text-cyan-700', bg: 'bg-cyan-50', border: 'border-cyan-100', label: 'Beach' },
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
                    size={11}
                    className={
                        i <= full
                            ? 'text-amber-400 fill-amber-400'
                            : i === full + 1 && half
                                ? 'text-amber-400 fill-amber-200'
                                : 'text-gray-200 fill-gray-200'
                    }
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
            className="fixed inset-0 z-[999] flex items-center justify-center bg-black/85 backdrop-blur-sm"
            onClick={onClose}
        >
            <div className="relative max-w-4xl max-h-[90vh] w-full mx-4" onClick={e => e.stopPropagation()}>
                <img src={src} alt={alt} className="w-full h-full object-contain rounded-2xl shadow-2xl max-h-[85vh]" />
                <button
                    onClick={onClose}
                    className="absolute top-3 right-3 bg-white/20 hover:bg-white/40 text-white backdrop-blur-md rounded-full p-2 transition-all"
                >×</button>
                <p className="text-white/80 text-center text-sm mt-3 font-semibold">{alt}</p>
            </div>
        </div>
    );
}

// ── Destination Selector Card (expandable carousel item) ──────────────────────
function DestinationSelector({ itinerary, rank, isActive, onSelect }) {
    const stop = itinerary?.stops?.[0] || {};
    const [imgErr, setImgErr] = useState(false);
    const localImg = getLocalImageUrl(stop.destination);
    const imgSrc = !imgErr && localImg ? localImg : (stop.photo?.startsWith('http') ? stop.photo : null);

    const rankColors = ['bg-emerald-600', 'bg-violet-600', 'bg-blue-600'];
    const badgeColor = rankColors[(rank - 1) % 3];

    return (
        <button
            onClick={onSelect}
            className={`relative group flex flex-col items-start text-left transition-all duration-500 ease-out outline-none flex-shrink-0 ${isActive ? 'flex-1' : 'w-20 md:w-28 opacity-60 hover:opacity-100'
                }`}
        >
            <div className={`relative w-full overflow-hidden rounded-[2rem] transition-all duration-500 shadow-xl ${isActive
                ? 'h-64 md:h-80 ring-4 ring-white shadow-indigo-500/10'
                : 'h-24 md:h-32 grayscale-[0.4] hover:grayscale-0'
                }`}>
                {imgSrc ? (
                    <img
                        src={imgSrc}
                        alt={stop.destination}
                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                        onError={() => setImgErr(true)}
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-indigo-100 to-purple-200 flex items-center justify-center">
                        <MapPin size={32} className="text-indigo-400" />
                    </div>
                )}

                {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent p-6 flex flex-col justify-end">
                        <div className="flex items-center gap-3 mb-3 flex-wrap">
                            <span className={`${badgeColor} text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full shadow-lg`}>
                                #{rank} Top Match
                            </span>
                            {stop.best_season && (
                                <span className="bg-white/20 backdrop-blur-md text-white text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border border-white/20">
                                    {stop.best_season}
                                </span>
                            )}
                        </div>
                        <h1 className="text-3xl md:text-5xl font-black text-white leading-none tracking-tight mb-2 drop-shadow-lg">
                            {stop.destination}
                        </h1>
                        {stop.tagline && (
                            <p className="text-white/80 text-sm font-medium max-w-lg line-clamp-2">
                                "{stop.tagline}"
                            </p>
                        )}
                    </div>
                )}

                {!isActive && (
                    <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors flex items-center justify-center">
                        <span className="w-8 h-8 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white font-bold text-xs border border-white/30">
                            #{rank}
                        </span>
                    </div>
                )}
            </div>

            {!isActive && (
                <p className="mt-2 text-xs font-bold text-gray-500 text-center w-full truncate px-1">
                    {stop.destination}
                </p>
            )}
        </button>
    );
}

// ── Experience Card (Nearby Place) with accordion ────────────────────────────
function ExperienceCard({ place, isSelected, onToggle, onEnlargeImage }) {
    const [expanded, setExpanded] = useState(false);
    const catMeta = getCategoryMeta(place.category);
    const imgUrl = place.image_path ? `${API_BASE}${place.image_path}` : null;

    return (
        <div
            className={`group relative flex flex-col bg-white rounded-3xl transition-all duration-300 overflow-hidden ${isSelected
                ? 'ring-2 ring-indigo-600 shadow-2xl shadow-indigo-900/10 -translate-y-1 z-10'
                : 'border border-gray-100 shadow-sm hover:shadow-xl hover:shadow-gray-200/50 hover:-translate-y-1'
                }`}
        >
            {/* Image Header */}
            <div className="relative h-52 overflow-hidden cursor-pointer" onClick={onToggle}>
                {imgUrl ? (
                    <img
                        src={imgUrl}
                        alt={place.name}
                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                    />
                ) : (
                    <div className="w-full h-full bg-gray-50 flex items-center justify-center">
                        <Compass className="text-gray-300" size={32} />
                    </div>
                )}

                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60 group-hover:opacity-40 transition-opacity" />

                {/* Category Badge */}
                <div className="absolute top-4 left-4">
                    <span className={`inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider px-3 py-1.5 rounded-full backdrop-blur-md bg-white/95 shadow-sm ${catMeta.color}`}>
                        {catMeta.label}
                    </span>
                </div>

                {/* Enlarge Button */}
                {imgUrl && (
                    <button
                        onClick={e => { e.stopPropagation(); onEnlargeImage(imgUrl, place.name); }}
                        className="absolute top-4 right-14 bg-black/40 hover:bg-black/70 text-white rounded-xl p-2 backdrop-blur-sm transition-all opacity-0 group-hover:opacity-100"
                    >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="15 3 21 3 21 9" /><polyline points="9 21 3 21 3 15" />
                            <line x1="21" y1="3" x2="14" y2="10" /><line x1="3" y1="21" x2="10" y2="14" />
                        </svg>
                    </button>
                )}

                {/* Select Toggle */}
                <div
                    className={`absolute top-4 right-4 w-10 h-10 rounded-full flex items-center justify-center backdrop-blur-md transition-all duration-300 shadow-lg cursor-pointer ${isSelected
                        ? 'bg-indigo-600 text-white scale-110'
                        : 'bg-white/30 text-white hover:bg-white hover:text-indigo-600'
                        }`}
                    onClick={e => { e.stopPropagation(); onToggle(); }}
                >
                    {isSelected ? <Check size={18} strokeWidth={3} /> : <Plus size={20} />}
                </div>

                {/* Distance / Time / Rating chips */}
                <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between text-white/90">
                    <div className="flex items-center gap-2 text-xs font-bold">
                        <span className="flex items-center gap-1 bg-black/25 px-2 py-1 rounded-lg backdrop-blur-sm">
                            <MapPin size={11} /> {place.distance_km}km
                        </span>
                        <span className="flex items-center gap-1 bg-black/25 px-2 py-1 rounded-lg backdrop-blur-sm">
                            <Clock size={11} /> {place.visit_duration}
                        </span>
                        <span className="flex items-center gap-1 bg-black/25 px-2 py-1 rounded-lg backdrop-blur-sm">
                            <Star size={11} className="text-yellow-400 fill-yellow-400" /> {place.rating}
                        </span>
                    </div>
                </div>
            </div>

            {/* Content Body */}
            <div className="p-5 flex flex-col flex-1">
                <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => setExpanded(e => !e)}
                >
                    <h3 className={`text-base font-black leading-tight transition-colors ${isSelected ? 'text-indigo-600' : 'text-gray-900 group-hover:text-indigo-600'
                        }`}>
                        {place.name}
                    </h3>
                    <button className="flex-none text-gray-400 hover:text-gray-700 transition-colors ml-2 mt-0.5">
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                </div>

                <p className="text-sm text-gray-500 leading-relaxed mt-2 line-clamp-2">
                    {place.description}
                </p>

                {/* Accordion expansion */}
                <div style={{
                    maxHeight: expanded ? '300px' : '0px',
                    transition: 'max-height 0.35s cubic-bezier(0.4,0,0.2,1)',
                    overflow: 'hidden',
                }}>
                    <div className="pt-4 space-y-3">
                        {place.highlights?.length > 0 && (
                            <div>
                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1.5">Key Highlights</p>
                                <div className="flex flex-wrap gap-1.5">
                                    {place.highlights.map((h, i) => (
                                        <span key={i} className="text-[10px] font-bold text-gray-500 bg-gray-50 px-2.5 py-1 rounded-md border border-gray-100">
                                            {h}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                        <div className="grid grid-cols-3 gap-2">
                            <div className="bg-gray-50 rounded-xl p-2 text-center border border-gray-100">
                                <p className="text-[9px] text-gray-400 font-bold uppercase tracking-wide mb-0.5">Duration</p>
                                <p className="text-[11px] font-bold text-gray-700">{place.visit_duration}</p>
                            </div>
                            <div className={`rounded-xl p-2 text-center border ${catMeta.bg} ${catMeta.border}`}>
                                <p className="text-[9px] text-gray-400 font-bold uppercase tracking-wide mb-0.5">Type</p>
                                <p className={`text-[11px] font-bold ${catMeta.color}`}>{catMeta.label}</p>
                            </div>
                            <div className="bg-gray-50 rounded-xl p-2 text-center border border-gray-100">
                                <p className="text-[9px] text-gray-400 font-bold uppercase tracking-wide mb-0.5">Rating</p>
                                <div className="flex justify-center"><StarRating rating={place.rating} /></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Tags */}
                {!expanded && place.highlights?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-1.5">
                        {place.highlights.slice(0, 2).map((h, i) => (
                            <span key={i} className="text-[10px] font-bold text-gray-500 bg-gray-50 px-2.5 py-1 rounded-md">
                                {h}
                            </span>
                        ))}
                        {place.highlights.length > 2 && (
                            <span className="text-[10px] font-bold text-gray-400 px-1 py-1">+{place.highlights.length - 2} more</span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function DestinationSelectionScreen({
    primaryItinerary,
    allItineraries = [],
    originCity,
    travelMonth,
    durationDays,
    routeJustification,
    onBack,
    onBuildItinerary,
}) {
    const [activeIndex, setActiveIndex] = useState(0);
    const activePrimary = allItineraries.length > 0 ? allItineraries[activeIndex] : primaryItinerary;
    const primaryStop = activePrimary?.stops?.[0] || {};

    const [nearbyPlaces, setNearbyPlaces] = useState([]);
    const [selectedPlaceNames, setSelectedPlaceNames] = useState(new Set());
    const [loadingNearby, setLoadingNearby] = useState(false);
    const [nearbyError, setNearbyError] = useState(null);
    const [nearbyRadius, setNearbyRadius] = useState(70);
    const [building, setBuilding] = useState(false);
    const [lightbox, setLightbox] = useState(null);

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
                setNearbyRadius(data.radius_km || 70);
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

    return (
        <div className="min-h-screen bg-[#FAFAFA] text-gray-900 font-sans pb-36">
            <ImageLightbox src={lightbox?.src} alt={lightbox?.alt} onClose={() => setLightbox(null)} />

            {/* ── Top Navigation ──────────────────────────────────────────── */}
            <nav className="fixed top-0 inset-x-0 z-40 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 h-16 flex items-center justify-between px-6 md:px-12">
                <button
                    onClick={onBack}
                    className="group flex items-center gap-2 text-xs font-bold text-gray-500 hover:text-gray-900 transition-colors uppercase tracking-wider"
                >
                    <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                        <ArrowLeft size={14} />
                    </span>
                    New Search
                </button>
                <div className="flex items-center gap-4">
                    {originCity && (
                        <span className="hidden md:flex items-center gap-1 text-xs text-gray-500 font-medium">
                            ✈️ From {originCity}
                        </span>
                    )}
                    {travelMonth && (
                        <div className="hidden md:flex flex-col items-end">
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Travel Date</span>
                            <span className="text-sm font-bold text-gray-900">{travelMonth}</span>
                        </div>
                    )}
                </div>
            </nav>

            <div className="max-w-7xl mx-auto px-6 md:px-12 pt-28">

                {/* ── 1. Destination Carousel ──────────────────────────────── */}
                <div className="mb-12">
                    {allItineraries.length > 1 && (
                        <div className="flex items-center gap-3 mb-6">
                            <Sparkles size={16} className="text-indigo-600" />
                            <span className="text-xs font-bold text-indigo-900 uppercase tracking-widest">
                                We found {allItineraries.length} perfect matches for you
                            </span>
                        </div>
                    )}

                    <div className="flex gap-4 md:gap-6 overflow-x-auto pb-8 scrollbar-hide snap-x">
                        {allItineraries.length > 0 ? (
                            allItineraries.map((itin, idx) => (
                                <DestinationSelector
                                    key={idx}
                                    itinerary={itin}
                                    rank={idx + 1}
                                    isActive={activeIndex === idx}
                                    onSelect={() => {
                                        setActiveIndex(idx);
                                        setSelectedPlaceNames(new Set());
                                    }}
                                />
                            ))
                        ) : (
                            <DestinationSelector
                                itinerary={primaryItinerary}
                                rank={1}
                                isActive={true}
                                onSelect={() => { }}
                            />
                        )}
                    </div>
                </div>

                {/* ── 2. Destination Context ───────────────────────────────── */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 mb-16">
                    <div className="lg:col-span-8">
                        <div className="flex flex-col gap-5">
                            {/* Route Justification */}
                            {routeJustification && (
                                <div className="bg-white rounded-3xl p-7 border border-gray-100 shadow-xl shadow-gray-200/40 relative overflow-hidden">
                                    <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-indigo-50 rounded-full blur-3xl opacity-50 pointer-events-none" />
                                    <div className="relative z-10">
                                        <h3 className="text-xs font-black text-gray-900 uppercase tracking-widest mb-3 flex items-center gap-2">
                                            <Award size={16} className="text-indigo-600" />
                                            Why this fits your vibe
                                        </h3>
                                        <p className="text-base text-gray-600 leading-relaxed font-medium">
                                            {routeJustification}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Quick Stats */}
                            <div className="flex flex-wrap gap-4">
                                {primaryStop.price_per_person > 0 && (
                                    <div className="bg-white px-5 py-4 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-green-50 flex items-center justify-center text-green-600">
                                            <span className="text-lg font-bold">₹</span>
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Est. Cost</p>
                                            <p className="text-base font-black text-gray-900">
                                                ₹{(primaryStop.price_per_person || 0).toLocaleString('en-IN')}
                                            </p>
                                        </div>
                                    </div>
                                )}
                                {primaryStop.best_season && (
                                    <div className="bg-white px-5 py-4 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                                            <Calendar size={18} />
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Best Time</p>
                                            <p className="text-base font-bold text-gray-900">{primaryStop.best_season}</p>
                                        </div>
                                    </div>
                                )}
                                {primaryItinerary?.stops?.[0]?.category && (
                                    <div className="bg-white px-5 py-4 rounded-2xl border border-gray-100 shadow-sm flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-purple-50 flex items-center justify-center text-purple-600">
                                            <Sparkles size={16} />
                                        </div>
                                        <div>
                                            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Category</p>
                                            <p className="text-base font-bold text-gray-900 capitalize">{primaryItinerary.stops[0].category}</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* CTA text */}
                    <div className="lg:col-span-4 flex flex-col justify-center">
                        <h2 className="text-2xl md:text-3xl font-black text-gray-900 mb-3">
                            Curate your<br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                                perfect timeline.
                            </span>
                        </h2>
                        <p className="text-sm text-gray-500 font-medium leading-relaxed mb-5">
                            Hand-picked experiences within {nearbyRadius}km of{' '}
                            <span className="font-bold text-gray-700">{primaryStop.destination}</span>.
                            Select the ones that excite you.
                        </p>
                        <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full">
                                {nearbyPlaces.length} experiences found
                            </span>
                            {selectedPlaceNames.size > 0 && (
                                <>
                                    <span className="text-xs font-bold bg-indigo-100 text-indigo-700 px-3 py-1.5 rounded-full">
                                        {selectedPlaceNames.size} selected
                                    </span>
                                    <button
                                        onClick={() => setSelectedPlaceNames(new Set())}
                                        className="text-xs text-gray-400 hover:text-gray-700 flex items-center gap-1 transition-colors ml-1"
                                    >
                                        <RefreshCcw size={11} /> Clear
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* ── 3. Experiences Grid ──────────────────────────────────── */}
                <div className="relative min-h-[400px]">
                    {loadingNearby ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-7">
                            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                                <div key={i} className="h-80 bg-gray-200 rounded-3xl animate-pulse" />
                            ))}
                        </div>
                    ) : nearbyError ? (
                        <div className="text-center py-16 text-gray-400">
                            <MapPin size={36} className="mx-auto mb-3 opacity-30" />
                            <p className="text-sm font-medium">{nearbyError}</p>
                        </div>
                    ) : nearbyPlaces.length === 0 ? (
                        <div className="col-span-full py-20 text-center">
                            <Compass size={36} className="mx-auto mb-3 text-gray-300" />
                            <p className="text-gray-400 font-medium">No specific nearby places found for this destination.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-7">
                            {nearbyPlaces.map((place, i) => (
                                <ExperienceCard
                                    key={place.name + i}
                                    place={place}
                                    isSelected={selectedPlaceNames.has(place.name)}
                                    onToggle={() => togglePlace(place.name)}
                                    onEnlargeImage={(src, alt) => setLightbox({ src, alt })}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* ── Floating Glass HUD ───────────────────────────────────────── */}
            <div className="fixed bottom-8 inset-x-0 z-50 flex justify-center pointer-events-none px-6">
                <div className="w-full max-w-3xl pointer-events-auto">
                    <div className="bg-gray-900/90 backdrop-blur-xl text-white p-2 pl-6 rounded-2xl shadow-2xl shadow-indigo-900/30 flex items-center justify-between ring-1 ring-white/10 transition-all hover:scale-[1.01]">

                        <div className="flex items-center gap-6 flex-wrap">
                            <div className="flex flex-col">
                                <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-0.5">Destination</span>
                                <span className="text-sm font-bold text-white">{primaryStop.destination || '—'}</span>
                            </div>

                            {selectedPlaces.length > 0 && (
                                <>
                                    <div className="h-8 w-px bg-white/10 hidden sm:block" />
                                    <div className="flex flex-col">
                                        <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider mb-0.5">Add-ons</span>
                                        <span className="text-sm font-bold text-white">+{selectedPlaces.length} experiences</span>
                                    </div>
                                    <div className="h-8 w-px bg-white/10 hidden sm:block" />
                                    <div className="flex flex-col">
                                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-0.5">Est. Duration</span>
                                        <span className="text-sm font-bold text-white">{durationDays || '~5'} days</span>
                                    </div>
                                </>
                            )}

                            {selectedPlaces.length === 0 && (
                                <span className="text-xs text-gray-500 italic ml-1 hidden sm:block">
                                    Select experiences above →
                                </span>
                            )}
                        </div>

                        <button
                            onClick={handleBuild}
                            disabled={building}
                            className="bg-white text-gray-900 hover:bg-gray-100 px-7 py-3.5 rounded-xl font-black text-sm transition-all active:scale-95 flex items-center gap-2 shadow-lg flex-shrink-0 ml-4"
                        >
                            {building ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    <span>Generating…</span>
                                </>
                            ) : (
                                <>
                                    <span>Build Itinerary</span>
                                    <ArrowRight size={16} />
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
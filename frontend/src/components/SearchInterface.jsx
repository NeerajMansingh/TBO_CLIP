import React, { useState, useRef, useCallback } from 'react';
import {
    Search, Upload, MapPin, Calendar, Sparkles, X, Sliders,
    ChevronDown, Clock, TrendingUp
} from 'lucide-react';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const ORIGIN_CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Ahmedabad', 'Pune', 'Dubai', 'London', 'Singapore'];

const VIBES = [
    { label: 'Adventure', emoji: '🧗' },
    { label: 'Beach', emoji: '🏖️' },
    { label: 'Mountains', emoji: '⛰️' },
    { label: 'Heritage', emoji: '🏯' },
    { label: 'Luxury', emoji: '✨' },
    { label: 'Budget', emoji: '💰' },
    { label: 'Nature', emoji: '🌿' },
    { label: 'Spiritual', emoji: '🙏' },
    { label: 'Romantic', emoji: '💑' },
    { label: 'Family', emoji: '👨‍👩‍👧' },
    { label: 'Solo', emoji: '🎒' },
    { label: 'City', emoji: '🏙️' },
];

const QUICK_SEARCHES = [
    '5 days in Rajasthan under ₹40,000',
    'Beach holiday in Goa in December',
    'Himalayas trek under ₹60,000',
    'Heritage tour of South India',
    'Couple trip to Kerala backwaters',
];

export default function SearchInterface({
    imagePreview, setImagePreview,
    chatInput, setChatInput,
    originCity, setOriginCity,
    travelMonth, setTravelMonth,
    selectedVibes, setSelectedVibes,
    recentSearches,
    budget, setBudget,
    durationDays, setDurationDays,
    onSearch, onSurpriseMe,
}) {
    const [isDragging, setIsDragging] = useState(false);
    const [showAdvanced, setShowAdvanced] = useState(false);
    const fileInputRef = useRef(null);

    const toggleVibe = (vibe) =>
        setSelectedVibes(prev =>
            prev.includes(vibe) ? prev.filter(v => v !== vibe) : [...prev, vibe]
        );

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) setImagePreview(URL.createObjectURL(file));
    }, [setImagePreview]);

    const handleFileSelect = (e) => {
        const file = e.target.files?.[0];
        if (file) setImagePreview(URL.createObjectURL(file));
    };

    const formatBudget = (val) => {
        if (val >= 100000) return `₹${(val / 100000).toFixed(val % 100000 === 0 ? 0 : 1)}L`;
        if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
        return `₹${val}`;
    };

    return (
        <div className="w-full max-w-6xl mx-auto px-4 py-10 animate-fade-in">

            {/* Hero Header */}
            <div className="text-center mb-10">
                <div className="section-badge mb-4">
                    <Sparkles size={10} />
                    AI-Powered Travel Planner
                </div>
                <h1 className="text-5xl md:text-6xl font-black tracking-tight text-gray-900 mb-4 leading-[1.1]">
                    Where do you want<br />
                    <span className="text-gradient-blue">to go next?</span>
                </h1>
                <p className="text-gray-500 text-lg max-w-xl mx-auto">
                    Describe your dream trip in plain English, or upload an inspiration photo. We'll build a personalised, priced itinerary instantly.
                </p>
            </div>

            {/* Main Search Card */}
            <div className="card-light p-2 mb-6 relative">
                {/* Natural Language Input */}
                <div className="flex items-center gap-2 p-2">
                    <div className="flex-1 relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                        <input
                            type="text"
                            value={chatInput}
                            onChange={e => setChatInput(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter' && chatInput.trim()) onSearch(); }}
                            placeholder='e.g. "5 days in Rajasthan under ₹40,000 for a couple"'
                            className="w-full pl-12 pr-4 py-4 text-base bg-transparent border-none outline-none text-gray-900 placeholder-gray-400"
                        />
                    </div>
                    {/* Photo upload trigger */}
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className={`flex-none flex items-center gap-2 px-4 py-3 rounded-xl border-2 border-dashed transition-all
              ${imagePreview
                                ? 'border-blue-400 bg-blue-50 text-blue-700'
                                : 'border-gray-200 text-gray-400 hover:border-gray-300 hover:text-gray-600'
                            }`}
                        title="Upload inspiration photo"
                    >
                        {imagePreview
                            ? <><img src={imagePreview} alt="" className="w-7 h-7 rounded object-cover" /><span className="text-xs font-medium">Photo added</span></>
                            : <><Upload size={18} /><span className="text-xs font-medium hidden sm:block">Add photo</span></>
                        }
                    </button>
                    <button
                        id="main-search-btn"
                        onClick={onSearch}
                        className="btn-primary px-6 py-3 flex-none"
                    >
                        Search
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handleFileSelect}
                    />
                </div>

                {/* Quick searches */}
                <div className="px-4 pb-3 flex flex-wrap gap-2">
                    {QUICK_SEARCHES.map(q => (
                        <button
                            key={q}
                            onClick={() => { setChatInput(q); }}
                            className="text-xs text-gray-500 bg-gray-100 hover:bg-blue-50 hover:text-blue-700 px-3 py-1.5 rounded-full transition-colors cursor-pointer"
                        >
                            {q}
                        </button>
                    ))}
                </div>
            </div>

            {/* Photo Drop Overlay (when dragging) */}
            {isDragging && (
                <div
                    onDragOver={e => e.preventDefault()}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleDrop}
                    className="fixed inset-0 bg-blue-600/20 backdrop-blur-sm z-50 flex items-center justify-center"
                >
                    <div className="bg-white border-2 border-blue-500 border-dashed rounded-2xl p-16 text-center">
                        <Upload size={40} className="text-blue-500 mx-auto mb-3" />
                        <p className="text-xl font-bold text-gray-900">Drop your photo here</p>
                    </div>
                </div>
            )}

            {/* Image preview strip (if uploaded) */}
            {imagePreview && (
                <div className="card-light p-4 mb-6 flex items-center gap-4 animate-slide-up">
                    <img src={imagePreview} alt="Vibe preview" className="w-20 h-14 object-cover rounded-lg border border-gray-200" />
                    <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-800">Inspiration photo added</p>
                        <p className="text-xs text-gray-500">We'll match your trip vibe from this image</p>
                    </div>
                    <button
                        onClick={() => setImagePreview(null)}
                        className="text-gray-400 hover:text-gray-700 transition-colors p-1"
                    >
                        <X size={18} />
                    </button>
                </div>
            )}

            {/* Trip Configuration Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                {/* Origin City */}
                <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">From</label>
                    <div className="relative">
                        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                        <select
                            value={originCity}
                            onChange={e => setOriginCity(e.target.value)}
                            className="input-clean pl-9 pr-8 h-11 appearance-none text-sm"
                        >
                            {ORIGIN_CITIES.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
                    </div>
                </div>

                {/* Travel Month */}
                <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">When</label>
                    <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                        <select
                            value={travelMonth}
                            onChange={e => setTravelMonth(e.target.value)}
                            className="input-clean pl-9 pr-8 h-11 appearance-none text-sm"
                        >
                            {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
                    </div>
                </div>

                {/* Duration */}
                <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Duration</label>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setDurationDays?.(d => Math.max(1, (d || 5) - 1))}
                            className="w-11 h-11 flex-none rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 transition-colors font-bold text-lg"
                        >−</button>
                        <div className="flex-1 h-11 flex items-center justify-center bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-800">
                            {durationDays || 5} days
                        </div>
                        <button
                            onClick={() => setDurationDays?.(d => Math.min(30, (d || 5) + 1))}
                            className="w-11 h-11 flex-none rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 transition-colors font-bold text-lg"
                        >+</button>
                    </div>
                </div>

                {/* Budget */}
                <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                        Budget — <span className="text-blue-600 font-bold">{formatBudget(budget || 100000)}</span>
                    </label>
                    <input
                        type="range"
                        min={5000}
                        max={500000}
                        step={5000}
                        value={budget || 100000}
                        onChange={e => setBudget?.(Number(e.target.value))}
                        className="w-full h-11 accent-blue-600"
                    />
                </div>
            </div>

            {/* Vibe Tags */}
            <div className="card-light p-5 mb-4">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Travel Vibes (optional)</p>
                <div className="flex flex-wrap gap-2">
                    {VIBES.map(({ label, emoji }) => (
                        <button
                            key={label}
                            onClick={() => toggleVibe(label)}
                            className={`tag-pill ${selectedVibes.includes(label) ? 'active' : ''}`}
                        >
                            {emoji} {label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Recent Searches */}
            {recentSearches?.length > 0 && (
                <div className="mb-6">
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <Clock size={12} /> Recent Searches
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {recentSearches.slice(0, 6).map((s, i) => (
                            <button
                                key={i}
                                onClick={() => setChatInput(s)}
                                className="text-xs text-gray-600 bg-white border border-gray-200 hover:border-blue-300 hover:text-blue-700 px-3 py-2 rounded-full transition-colors"
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* CTA row */}
            <div className="flex flex-col sm:flex-row items-center gap-3">
                <button
                    id="find-journey-btn"
                    onClick={onSearch}
                    className="btn-primary w-full sm:w-auto px-8 py-4 text-base"
                >
                    <Search size={18} />
                    Find My Journey
                </button>
                <button
                    onClick={onSurpriseMe}
                    className="btn-secondary w-full sm:w-auto px-6 py-4 text-base"
                >
                    <Sparkles size={16} />
                    Surprise Me
                </button>
            </div>
        </div>
    );
}

// import React, { useState, useRef, useCallback } from 'react';
// import {
//     Search, Upload, MapPin, Calendar, Sparkles, X, Sliders,
//     ChevronDown, Clock, TrendingUp
// } from 'lucide-react';

// const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
// const ORIGIN_CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Ahmedabad', 'Pune', 'Dubai', 'London', 'Singapore'];

// const VIBES = [
//     { label: 'Adventure', emoji: '🧗' },
//     { label: 'Beach', emoji: '🏖️' },
//     { label: 'Mountains', emoji: '⛰️' },
//     { label: 'Heritage', emoji: '🏯' },
//     { label: 'Luxury', emoji: '✨' },
//     { label: 'Budget', emoji: '💰' },
//     { label: 'Nature', emoji: '🌿' },
//     { label: 'Spiritual', emoji: '🙏' },
//     { label: 'Romantic', emoji: '💑' },
//     { label: 'Family', emoji: '👨‍👩‍👧' },
//     { label: 'Solo', emoji: '🎒' },
//     { label: 'City', emoji: '🏙️' },
// ];

// const QUICK_SEARCHES = [
//     '5 days in Rajasthan under ₹40,000',
//     'Beach holiday in Goa in December',
//     'Himalayas trek under ₹60,000',
//     'Heritage tour of South India',
//     'Couple trip to Kerala backwaters',
// ];

// export default function SearchInterface({
//     imagePreview, setImagePreview,
//     chatInput, setChatInput,
//     originCity, setOriginCity,
//     travelMonth, setTravelMonth,
//     selectedVibes, setSelectedVibes,
//     recentSearches,
//     budget, setBudget,
//     durationDays, setDurationDays,
//     onSearch, onSurpriseMe,
// }) {
//     const [isDragging, setIsDragging] = useState(false);
//     const [showAdvanced, setShowAdvanced] = useState(false);
//     const fileInputRef = useRef(null);

//     const toggleVibe = (vibe) =>
//         setSelectedVibes(prev =>
//             prev.includes(vibe) ? prev.filter(v => v !== vibe) : [...prev, vibe]
//         );

//     const handleDrop = useCallback((e) => {
//         e.preventDefault();
//         setIsDragging(false);
//         const file = e.dataTransfer.files?.[0];
//         if (file) setImagePreview(URL.createObjectURL(file));
//     }, [setImagePreview]);

//     const handleFileSelect = (e) => {
//         const file = e.target.files?.[0];
//         if (file) setImagePreview(URL.createObjectURL(file));
//     };

//     const formatBudget = (val) => {
//         if (val >= 100000) return `₹${(val / 100000).toFixed(val % 100000 === 0 ? 0 : 1)}L`;
//         if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
//         return `₹${val}`;
//     };

//     return (
//         <div className="w-full max-w-6xl mx-auto px-4 py-10 animate-fade-in">

//             {/* Hero Header */}
//             <div className="text-center mb-10">
//                 <div className="section-badge mb-4">
//                     <Sparkles size={10} />
//                     AI-Powered Travel Planner
//                 </div>
//                 <h1 className="text-5xl md:text-6xl font-black tracking-tight text-gray-900 mb-4 leading-[1.1]">
//                     Where do you want<br />
//                     <span className="text-gradient-blue">to go next?</span>
//                 </h1>
//                 <p className="text-gray-500 text-lg max-w-xl mx-auto">
//                     Describe your dream trip in plain English, or upload an inspiration photo. We'll build a personalised, priced itinerary instantly.
//                 </p>
//             </div>

//             {/* Main Search Card */}
//             <div className="card-light p-2 mb-6 relative">
//                 {/* Natural Language Input */}
//                 <div className="flex items-center gap-2 p-2">
//                     <div className="flex-1 relative">
//                         <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
//                         <input
//                             type="text"
//                             value={chatInput}
//                             onChange={e => setChatInput(e.target.value)}
//                             onKeyDown={e => { if (e.key === 'Enter' && chatInput.trim()) onSearch(); }}
//                             placeholder='e.g. "5 days in Rajasthan under ₹40,000 for a couple"'
//                             className="w-full pl-12 pr-4 py-4 text-base bg-transparent border-none outline-none text-gray-900 placeholder-gray-400"
//                         />
//                     </div>
//                     {/* Photo upload trigger */}
//                     <button
//                         onClick={() => fileInputRef.current?.click()}
//                         className={`flex-none flex items-center gap-2 px-4 py-3 rounded-xl border-2 border-dashed transition-all
//               ${imagePreview
//                                 ? 'border-blue-400 bg-blue-50 text-blue-700'
//                                 : 'border-gray-200 text-gray-400 hover:border-gray-300 hover:text-gray-600'
//                             }`}
//                         title="Upload inspiration photo"
//                     >
//                         {imagePreview
//                             ? <><img src={imagePreview} alt="" className="w-7 h-7 rounded object-cover" /><span className="text-xs font-medium">Photo added</span></>
//                             : <><Upload size={18} /><span className="text-xs font-medium hidden sm:block">Add photo</span></>
//                         }
//                     </button>
//                     <button
//                         id="main-search-btn"
//                         onClick={onSearch}
//                         className="btn-primary px-6 py-3 flex-none"
//                     >
//                         Search
//                     </button>
//                     <input
//                         ref={fileInputRef}
//                         type="file"
//                         accept="image/*"
//                         className="hidden"
//                         onChange={handleFileSelect}
//                     />
//                 </div>

//                 {/* Quick searches */}
//                 <div className="px-4 pb-3 flex flex-wrap gap-2">
//                     {QUICK_SEARCHES.map(q => (
//                         <button
//                             key={q}
//                             onClick={() => { setChatInput(q); }}
//                             className="text-xs text-gray-500 bg-gray-100 hover:bg-blue-50 hover:text-blue-700 px-3 py-1.5 rounded-full transition-colors cursor-pointer"
//                         >
//                             {q}
//                         </button>
//                     ))}
//                 </div>
//             </div>

//             {/* Photo Drop Overlay (when dragging) */}
//             {isDragging && (
//                 <div
//                     onDragOver={e => e.preventDefault()}
//                     onDragLeave={() => setIsDragging(false)}
//                     onDrop={handleDrop}
//                     className="fixed inset-0 bg-blue-600/20 backdrop-blur-sm z-50 flex items-center justify-center"
//                 >
//                     <div className="bg-white border-2 border-blue-500 border-dashed rounded-2xl p-16 text-center">
//                         <Upload size={40} className="text-blue-500 mx-auto mb-3" />
//                         <p className="text-xl font-bold text-gray-900">Drop your photo here</p>
//                     </div>
//                 </div>
//             )}

//             {/* Image preview strip (if uploaded) */}
//             {imagePreview && (
//                 <div className="card-light p-4 mb-6 flex items-center gap-4 animate-slide-up">
//                     <img src={imagePreview} alt="Vibe preview" className="w-20 h-14 object-cover rounded-lg border border-gray-200" />
//                     <div className="flex-1">
//                         <p className="text-sm font-semibold text-gray-800">Inspiration photo added</p>
//                         <p className="text-xs text-gray-500">We'll match your trip vibe from this image</p>
//                     </div>
//                     <button
//                         onClick={() => setImagePreview(null)}
//                         className="text-gray-400 hover:text-gray-700 transition-colors p-1"
//                     >
//                         <X size={18} />
//                     </button>
//                 </div>
//             )}

//             {/* Trip Configuration Grid */}
//             <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
//                 {/* Origin City */}
//                 <div>
//                     <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">From</label>
//                     <div className="relative">
//                         <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
//                         <select
//                             value={originCity}
//                             onChange={e => setOriginCity(e.target.value)}
//                             className="input-clean pl-9 pr-8 h-11 appearance-none text-sm"
//                         >
//                             {ORIGIN_CITIES.map(c => <option key={c} value={c}>{c}</option>)}
//                         </select>
//                         <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
//                     </div>
//                 </div>

//                 {/* Travel Month */}
//                 <div>
//                     <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">When</label>
//                     <div className="relative">
//                         <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
//                         <select
//                             value={travelMonth}
//                             onChange={e => setTravelMonth(e.target.value)}
//                             className="input-clean pl-9 pr-8 h-11 appearance-none text-sm"
//                         >
//                             {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
//                         </select>
//                         <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
//                     </div>
//                 </div>

//                 {/* Duration */}
//                 <div>
//                     <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Duration</label>
//                     <div className="flex items-center gap-2">
//                         <button
//                             onClick={() => setDurationDays?.(d => Math.max(1, (d || 5) - 1))}
//                             className="w-11 h-11 flex-none rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 transition-colors font-bold text-lg"
//                         >−</button>
//                         <div className="flex-1 h-11 flex items-center justify-center bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-800">
//                             {durationDays || 5} days
//                         </div>
//                         <button
//                             onClick={() => setDurationDays?.(d => Math.min(30, (d || 5) + 1))}
//                             className="w-11 h-11 flex-none rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 transition-colors font-bold text-lg"
//                         >+</button>
//                     </div>
//                 </div>

//                 {/* Budget */}
//                 <div>
//                     <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
//                         Budget — <span className="text-blue-600 font-bold">{formatBudget(budget || 100000)}</span>
//                     </label>
//                     <input
//                         type="range"
//                         min={5000}
//                         max={500000}
//                         step={5000}
//                         value={budget || 100000}
//                         onChange={e => setBudget?.(Number(e.target.value))}
//                         className="w-full h-11 accent-blue-600"
//                     />
//                 </div>
//             </div>

//             {/* Vibe Tags */}
//             <div className="card-light p-5 mb-4">
//                 <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Travel Vibes (optional)</p>
//                 <div className="flex flex-wrap gap-2">
//                     {VIBES.map(({ label, emoji }) => (
//                         <button
//                             key={label}
//                             onClick={() => toggleVibe(label)}
//                             className={`tag-pill ${selectedVibes.includes(label) ? 'active' : ''}`}
//                         >
//                             {emoji} {label}
//                         </button>
//                     ))}
//                 </div>
//             </div>

//             {/* Recent Searches */}
//             {recentSearches?.length > 0 && (
//                 <div className="mb-6">
//                     <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
//                         <Clock size={12} /> Recent Searches
//                     </p>
//                     <div className="flex flex-wrap gap-2">
//                         {recentSearches.slice(0, 6).map((s, i) => (
//                             <button
//                                 key={i}
//                                 onClick={() => setChatInput(s)}
//                                 className="text-xs text-gray-600 bg-white border border-gray-200 hover:border-blue-300 hover:text-blue-700 px-3 py-2 rounded-full transition-colors"
//                             >
//                                 {s}
//                             </button>
//                         ))}
//                     </div>
//                 </div>
//             )}

//             {/* CTA row */}
//             <div className="flex flex-col sm:flex-row items-center gap-3">
//                 <button
//                     id="find-journey-btn"
//                     onClick={onSearch}
//                     className="btn-primary w-full sm:w-auto px-8 py-4 text-base"
//                 >
//                     <Search size={18} />
//                     Find My Journey
//                 </button>
//                 <button
//                     onClick={onSurpriseMe}
//                     className="btn-secondary w-full sm:w-auto px-6 py-4 text-base"
//                 >
//                     <Sparkles size={16} />
//                     Surprise Me
//                 </button>
//             </div>
//         </div>
//     );
// }


import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
    Search, Upload, MapPin, Calendar, Sparkles, X, SlidersHorizontal,
    ChevronDown, Clock, TrendingUp, Compass, Mountain, Waves,
    Palmtree, Building2, Heart, Users, RefreshCw, ArrowRight
} from 'lucide-react';

// ── Constants ───────────────────────────────────────────────────────────────
const MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

const ORIGIN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata',
    'Hyderabad', 'Ahmedabad', 'Pune', 'Dubai', 'London', 'Singapore'
];

const VIBES = [
    { id: 'adventure', label: 'Adventure', icon: Mountain, color: 'bg-orange-100 text-orange-600' },
    { id: 'beach', label: 'Beach', icon: Waves, color: 'bg-blue-100 text-blue-600' },
    { id: 'nature', label: 'Nature', icon: Palmtree, color: 'bg-green-100 text-green-600' },
    { id: 'city', label: 'City', icon: Building2, color: 'bg-gray-100 text-gray-600' },
    { id: 'romantic', label: 'Romantic', icon: Heart, color: 'bg-rose-100 text-rose-600' },
    { id: 'family', label: 'Family', icon: Users, color: 'bg-purple-100 text-purple-600' },
];

const SUGGESTIONS = [
    '5 days in Kerala for a couple',
    'Budget solo trip to Himachal',
    'Luxury beach vacation in Goa',
    'Heritage tour of Rajasthan',
];

// ── Components ──────────────────────────────────────────────────────────────

// 1. Vibe Card Component
function VibeCard({ vibe, isSelected, onClick }) {
    const Icon = vibe.icon;
    return (
        <button
            onClick={onClick}
            className={`group relative flex flex-col items-center justify-center p-4 rounded-2xl transition-all duration-300 border ${isSelected
                ? 'bg-white border-indigo-600 shadow-lg shadow-indigo-100 scale-105'
                : 'bg-white/60 border-gray-200 hover:border-gray-300 hover:bg-white hover:scale-105'
                }`}
        >
            <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors ${isSelected ? 'bg-indigo-600 text-white' : vibe.color
                }`}>
                <Icon size={20} />
            </div>
            <span className={`text-xs font-bold ${isSelected ? 'text-indigo-900' : 'text-gray-500'}`}>
                {vibe.label}
            </span>
            {isSelected && (
                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
            )}
        </button>
    );
}

// ── Main Search Screen ──────────────────────────────────────────────────────
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
    const [showFilters, setShowFilters] = useState(true);
    const [scrolled, setScrolled] = useState(false);
    const fileInputRef = useRef(null);

    // Scroll listener for glass navbar effect
    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 20);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const toggleVibe = (vibeLabel) => {
        setSelectedVibes(prev =>
            prev.includes(vibeLabel) ? prev.filter(v => v !== vibeLabel) : [...prev, vibeLabel]
        );
    };

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
        if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
        if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
        return `₹${val}`;
    };

    return (
        <div
            className="min-h-screen w-full bg-[#FAFAFA] font-sans text-gray-900 selection:bg-indigo-500/30 overflow-x-hidden"
            onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
        >

            {/* ── Background Ambient Glows ── */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-indigo-500/5 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-rose-500/5 rounded-full blur-[100px]" />
            </div>

            {/* ── Navbar ── */}
            <nav className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/80 backdrop-blur-xl shadow-sm border-b border-gray-100 py-3' : 'bg-transparent py-6'
                }`}>
                <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
                            <Compass size={18} strokeWidth={2.5} />
                        </div>
                        <span className="font-bold text-lg tracking-tight text-gray-900">Visionvoyage</span>
                    </div>

                    <div className="flex items-center gap-4">
                    </div>
                </div>
            </nav>

            <div className="relative z-10 max-w-4xl mx-auto px-6 pt-24 pb-10">

                {/* ── Hero Section ── */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 text-[10px] font-black uppercase tracking-widest mb-4 shadow-sm">
                        <Sparkles size={12} />
                        AI-Powered Trip Planner
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black tracking-tight text-gray-900 mb-3 leading-[1.1]">
                        Show Us Your{' '}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 animate-gradient bg-300%">Dream Destination.</span>
                    </h1>
                    <p className="text-base text-gray-500 max-w-lg mx-auto font-medium">
                        Upload an inspiration photo and we'll find the perfect match.
                    </p>
                </div>

                {/* ── Search Area ── */}
                <div className="relative z-20 mb-6">
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-3xl blur-2xl" />

                    <div className="relative bg-white/80 backdrop-blur-sm rounded-3xl shadow-lg shadow-gray-200/40 border border-gray-100/80 p-5 md:p-6">

                        {/* Top row: Upload + Text */}
                        <div className="flex flex-col sm:flex-row gap-3 mb-4">
                            {/* Upload Zone */}
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className={`group relative sm:w-48 flex items-center gap-3 px-4 py-3.5 rounded-2xl border-2 border-dashed transition-all duration-300 ${imagePreview
                                    ? 'border-indigo-300 bg-indigo-50/60'
                                    : 'border-gray-200 bg-gray-50/50 hover:border-indigo-300 hover:bg-indigo-50/40'
                                    }`}
                            >
                                {imagePreview ? (
                                    <>
                                        <img src={imagePreview} alt="" className="w-10 h-10 rounded-xl object-cover shadow-sm ring-2 ring-white" />
                                        <div className="text-left flex-1 min-w-0">
                                            <span className="text-[10px] text-green-600 font-black uppercase tracking-wider block">Ready</span>
                                            <span className="text-xs text-indigo-600 font-semibold">Change</span>
                                        </div>
                                        <div
                                            onClick={(e) => { e.stopPropagation(); setImagePreview(null); }}
                                            className="p-1 hover:bg-red-100 rounded-full text-gray-300 hover:text-red-500 transition-colors"
                                        >
                                            <X size={14} />
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-500 flex items-center justify-center group-hover:bg-indigo-500 group-hover:text-white transition-colors duration-300">
                                            <Upload size={18} />
                                        </div>
                                        <div className="text-left">
                                            <span className="text-sm font-bold text-gray-700 block leading-tight">Upload</span>
                                            <span className="text-[10px] text-gray-400 font-medium">Photo or drag</span>
                                        </div>
                                    </>
                                )}
                            </button>
                            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileSelect} />

                            {/* Text Input */}
                            <div className="flex-1 relative">
                                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300">
                                    <Search size={16} />
                                </div>
                                <input
                                    type="text"
                                    value={chatInput}
                                    onChange={e => setChatInput(e.target.value)}
                                    onKeyDown={e => { if (e.key === 'Enter') onSearch(); }}
                                    placeholder="Describe your trip (optional)..."
                                    className="w-full h-full pl-11 pr-4 py-3.5 rounded-2xl bg-gray-50/80 border border-gray-100 text-sm font-medium text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-200 focus:bg-white transition-all"
                                />
                            </div>
                        </div>

                        {/* CTA Button */}
                        <button
                            onClick={onSearch}
                            className="w-full bg-gray-900 hover:bg-black text-white py-3.5 rounded-2xl font-bold text-sm transition-all shadow-lg shadow-gray-300/50 hover:shadow-xl active:scale-[0.98] flex items-center justify-center gap-2"
                        >
                            <Sparkles size={16} />
                            <span>Find Matches</span>
                            <ArrowRight size={16} />
                        </button>

                    </div>
                </div>

                {/* ── Suggested / Recent ── */}
                <div className="text-center mb-10">
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4">
                        {recentSearches?.length > 0 ? 'Recent Searches' : 'Try asking'}
                    </p>
                    <div className="flex flex-wrap justify-center gap-3">
                        {(recentSearches?.length > 0 ? recentSearches : SUGGESTIONS).slice(0, 4).map((s, i) => (
                            <button
                                key={i}
                                onClick={() => setChatInput(s)}
                                className="bg-white border border-gray-200 hover:border-indigo-300 hover:shadow-md text-gray-600 hover:text-indigo-700 px-5 py-2.5 rounded-xl text-sm font-medium transition-all"
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                </div>

                {/* ── Filters Toggle & Content ── */}
                <div className="mb-12">
                    <div className="flex justify-center mb-6">
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className={`flex items-center gap-2 px-5 py-2 rounded-full text-xs font-bold uppercase tracking-wider transition-all ${showFilters ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200' : 'bg-white text-gray-500 shadow-sm border border-gray-100 hover:bg-gray-50'
                                }`}
                        >
                            <SlidersHorizontal size={14} />
                            Trip Preferences
                            <ChevronDown size={14} className={`transition-transform duration-300 ${showFilters ? 'rotate-180' : ''}`} />
                        </button>
                    </div>

                    <div className={`overflow-hidden transition-all duration-500 ease-in-out ${showFilters ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0'}`}>
                        <div className="bg-white/60 backdrop-blur-md border border-white/50 rounded-3xl p-6 md:p-8 shadow-xl shadow-gray-200/50">

                            {/* Grid Settings */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                                {/* Origin */}
                                <div className="space-y-3">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                                        <MapPin size={12} /> Starting Point
                                    </label>
                                    <div className="relative group">
                                        <select
                                            value={originCity}
                                            onChange={e => setOriginCity(e.target.value)}
                                            className="w-full bg-white border border-gray-200 text-gray-900 text-sm font-bold rounded-xl px-4 py-3 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow"
                                        >
                                            {ORIGIN_CITIES.map(c => <option key={c} value={c}>{c}</option>)}
                                        </select>
                                        <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none group-hover:text-gray-600" size={16} />
                                    </div>
                                </div>

                                {/* Date */}
                                <div className="space-y-3">
                                    <label className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                                        <Calendar size={12} /> Travel Month
                                    </label>
                                    <div className="relative group">
                                        <select
                                            value={travelMonth}
                                            onChange={e => setTravelMonth(e.target.value)}
                                            className="w-full bg-white border border-gray-200 text-gray-900 text-sm font-bold rounded-xl px-4 py-3 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow"
                                        >
                                            {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                                        </select>
                                        <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none group-hover:text-gray-600" size={16} />
                                    </div>
                                </div>

                                {/* Budget Slider */}
                                <div className="space-y-3">
                                    <div className="flex justify-between">
                                        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                                            <TrendingUp size={12} /> Budget
                                        </label>
                                        <span className="text-xs font-black text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
                                            {formatBudget(budget || 100000)}
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min={5000}
                                        max={500000}
                                        step={5000}
                                        value={budget || 100000}
                                        onChange={e => setBudget?.(Number(e.target.value))}
                                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                    />
                                    <div className="flex justify-between text-[10px] text-gray-400 font-bold uppercase">
                                        <span>₹5k</span>
                                        <span>₹5L+</span>
                                    </div>
                                </div>
                            </div>

                            {/* Vibe Selection */}
                            <div>
                                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 block">
                                    What's your vibe?
                                </label>
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                                    {VIBES.map((v) => (
                                        <VibeCard
                                            key={v.id}
                                            vibe={v}
                                            isSelected={selectedVibes.includes(v.label)}
                                            onClick={() => toggleVibe(v.label)}
                                        />
                                    ))}
                                </div>
                            </div>

                        </div>
                    </div>
                </div>

                {/* ── Drag Overlay ── */}
                {isDragging && (
                    <div className="fixed inset-0 bg-indigo-900/50 backdrop-blur-sm z-[100] flex items-center justify-center animate-fade-in">
                        <div className="bg-white rounded-3xl p-12 text-center shadow-2xl scale-110">
                            <div className="w-20 h-20 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce">
                                <Upload size={32} />
                            </div>
                            <h3 className="text-2xl font-black text-gray-900">Drop it like it's hot</h3>
                            <p className="text-gray-500 mt-2">Upload your inspiration photo</p>
                        </div>
                    </div>
                )}



                {/* ── Surprise Me ── */}
                <div className="mt-12 flex justify-center">
                    <button
                        onClick={onSurpriseMe}
                        className="group flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-indigo-600 transition-colors"
                    >
                        <Sparkles size={14} className="group-hover:animate-spin" />
                        I'm feeling lucky, surprise me
                    </button>
                </div>

            </div>
        </div>
    );
}
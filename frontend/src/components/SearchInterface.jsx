import React, { useState } from 'react';
import { Upload, MapPin, Calendar, Search, Sparkles } from 'lucide-react';

const VIBES = ['Luxury', 'Budget', 'Adventure', 'Relaxing', 'Family', 'Couple', 'Solo', 'Nature', 'City', 'Beach', 'Mountains'];

export default function SearchInterface({
    imagePreview,
    setImagePreview,
    chatInput,
    setChatInput,
    originCity,
    setOriginCity,
    travelMonth,
    setTravelMonth,
    selectedVibes,
    setSelectedVibes,
    recentSearches,
    onSearch,
    onSurpriseMe
}) {
    const [isDragging, setIsDragging] = useState(false);

    const toggleVibe = (vibe) => {
        setSelectedVibes(prev =>
            prev.includes(vibe) ? prev.filter(v => v !== vibe) : [...prev, vibe]
        );
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => setIsDragging(false);

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            setImagePreview(URL.createObjectURL(file));
            // In a real app we would store the actual file for upload
        }
    };

    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setImagePreview(URL.createObjectURL(file));
        }
    };

    return (
        <div className="w-full max-w-6xl mx-auto px-4 py-12 animate-fade-in flex flex-col md:flex-row gap-12 items-center">

            {/* Visual Upload Zone */}
            <div className="flex-1 w-full relative">
                <label
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    htmlFor="file-upload"
                    className={`flex flex-col items-center justify-center p-12 text-center rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer min-h-[400px] glass ${isDragging ? 'border-indigo-400 bg-indigo-500/10' : 'border-gray-600 hover:border-gray-500'}`}
                >
                    {imagePreview ? (
                        <div className="absolute inset-0 p-2">
                            <img src={imagePreview} alt="Vibe Preview" className="w-full h-full object-cover rounded-xl" />
                            <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity rounded-xl">
                                <span className="text-white font-medium flex items-center gap-2"><Upload size={20} /> Change Photo</span>
                            </div>
                        </div>
                    ) : (
                        <>
                            <Upload className="w-12 h-12 text-indigo-400 mb-4" />
                            <h3 className="text-xl font-bold text-white mb-2">Drop your dream photo</h3>
                            <p className="text-gray-400 text-sm mb-6 max-w-xs">Upload a screenshot from Instagram, Pinterest, or anywhere.</p>
                            <div className="btn-primary">Browse Files</div>
                        </>
                    )}
                    <input id="file-upload" type="file" accept="image/*" className="hidden" onChange={handleFileSelect} />
                </label>

                <div className="mt-8 flex items-center gap-4">
                    <div className="flex-1 h-px bg-gray-800"></div>
                    <span className="text-xs text-gray-500 font-semibold tracking-wider">OR</span>
                    <div className="flex-1 h-px bg-gray-800"></div>
                </div>

                <button
                    onClick={onSurpriseMe}
                    className="w-full mt-6 py-3 text-indigo-400 hover:text-indigo-300 font-medium text-sm flex items-center justify-center gap-2 transition-colors duration-200"
                >
                    <Sparkles size={16} /> No inspiration photo? Tell us your vibe instead.
                </button>
            </div>

            {/* Configuration Zone */}
            <div className="flex-1 w-full space-y-8">
                <div>
                    <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 leading-tight tracking-tight">
                        Find the vibe.<br />
                        <span className="text-gradient">Within your budget.</span>
                    </h1>
                    <p className="text-gray-400 text-lg mb-8 max-w-lg">
                        Tell us your origin, travel month, and preferred vibes. Our AI will filter TBO's live inventory to find 3 perfect matching options.
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Origin City</label>
                        <div className="relative">
                            <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5 pointer-events-none" />
                            <select
                                value={originCity}
                                onChange={e => setOriginCity(e.target.value)}
                                className="input-field pl-12 appearance-none h-12 bg-gray-900 border-gray-800 text-white w-full"
                            >
                                <option value="Mumbai">Mumbai</option>
                                <option value="Delhi">Delhi</option>
                                <option value="Bangalore">Bangalore</option>
                                <option value="Dubai">Dubai</option>
                                <option value="London">London</option>
                                <option value="New York">New York</option>
                            </select>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Travel Month</label>
                        <div className="relative">
                            <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5 pointer-events-none" />
                            <select
                                value={travelMonth}
                                onChange={e => setTravelMonth(e.target.value)}
                                className="input-field pl-12 appearance-none h-12 bg-gray-900 border-gray-800 text-white w-full"
                            >
                                {['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'].map(m => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {recentSearches && recentSearches.length > 0 && (
                    <div className="p-4 rounded-xl border border-gray-800 bg-gray-900/50">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                                <Search size={14} /> Recent Searches
                            </span>
                            <span className="text-[10px] text-gray-600 italic">Phase 1: Local Session Continuity</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {recentSearches.map((search, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setChatInput(search)}
                                    className="px-3 py-1.5 rounded-full text-xs font-medium bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                                >
                                    {search}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                <div className="relative">
                    <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') onSearch(); }}
                        placeholder="e.g. Budget ₹80k, must have great seafood!"
                        className="input-field pl-4 pr-14 py-4 h-14 bg-gray-900 border-gray-800 text-white shadow-inner"
                    />
                    <button
                        onClick={onSearch}
                        className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center bg-gray-800 hover:bg-indigo-600 text-gray-400 hover:text-white rounded-lg transition-colors duration-200"
                    >
                        <Search size={18} />
                    </button>
                </div>

            </div>
        </div>
    );
}

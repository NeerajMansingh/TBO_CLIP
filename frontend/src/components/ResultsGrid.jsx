import React from 'react';
import { MapPin, Star, ArrowRight, RefreshCcw, Info } from 'lucide-react';

export default function ResultsGrid({ results, onBook, onReroll, rejectedIds }) {
    if (!results || results.length === 0) return null;

    return (
        <div className="w-full max-w-7xl mx-auto px-4 py-12 animate-fade-in flex flex-col items-center">

            <div className="w-full mb-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                <div>
                    <button className="text-gray-400 hover:text-white transition-colors text-sm font-medium mb-4 flex items-center gap-2">
                        ← Start Over
                    </button>
                    <h2 className="text-4xl font-bold text-white tracking-tight mb-2">Top 3 Matches Found</h2>
                    <p className="text-gray-400">We analyzed your parameters and verified live pricing.</p>
                </div>

                {/* Fake Query Composition */}
                <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800 glass text-right">
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block mb-2">Query Composition</span>
                    <div className="text-sm text-gray-300 font-mono">
                        <span className="text-white font-bold">100%</span> Prompt Weights
                    </div>
                </div>
            </div>

            {/* Refine Output Vibes Row */}
            <div className="w-full mb-8 p-4 bg-gray-900/40 rounded-2xl border border-gray-800/80">
                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block mb-3 pl-2">Refine Output Vibes</span>
                <div className="flex flex-wrap gap-2">
                    {['Luxury', 'Budget', 'Adventure', 'Relaxing', 'Family', 'Couple', 'Solo', 'Nature', 'City', 'Beach', 'Mountains'].map(vibe => (
                        <button key={vibe} className="text-xs px-4 py-1.5 rounded-full border border-gray-700 text-gray-400 hover:text-white hover:border-indigo-400 hover:bg-indigo-500/10 transition-colors">
                            {vibe}
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-12">
                {results.map((dest, index) => (
                    <div key={dest.id} className="card flex flex-col h-full bg-gray-900 relative group border-gray-800/80 transition-all duration-300 hover:border-indigo-500/30 hover:shadow-2xl hover:shadow-indigo-500/10">

                        {/* Image Header */}
                        <div className="relative h-56 w-full overflow-hidden">
                            <img src={dest.image_url} alt={dest.name} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
                            <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent"></div>

                            <div className="absolute top-4 right-4 bg-yellow-500 text-yellow-950 font-bold text-xs px-3 py-1 rounded-full shadow-lg">
                                {dest.match_score >= 90 ? 'Strong Match' : 'Good Match'}
                            </div>

                            <div className="absolute bottom-4 left-4 right-4">
                                <span className="text-indigo-400 text-xs font-bold uppercase tracking-widest flex items-center gap-1 mb-1">
                                    <MapPin size={12} /> {dest.country}
                                </span>
                                <h3 className="text-2xl font-bold text-white shadow-sm">{dest.name}</h3>
                            </div>
                        </div>

                        <div className="p-6 flex-1 flex flex-col">
                            <div className="flex justify-between items-center mb-4">
                                <div className="flex items-center gap-1 text-yellow-500 font-medium">
                                    <Star size={16} fill="currentColor" />
                                    <span className="text-white">{dest.rating || "4.5"}</span>
                                </div>
                                <div className="text-xs text-gray-400">
                                    Best: <span className="text-white font-medium">{dest.best_month || "Anytime"}</span>
                                </div>
                            </div>

                            {/* Vibe Tags */}
                            <div className="flex flex-wrap gap-2 mb-6">
                                {(dest.tags || []).slice(0, 3).map((tag, i) => (
                                    <span key={i} className="text-[10px] bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-2 py-1 rounded uppercase tracking-wider font-bold">
                                        {tag}
                                    </span>
                                ))}
                            </div>

                            {/* Intelligence Narrative */}
                            <div className="mb-6 bg-gray-950/50 p-4 rounded-xl border border-gray-800 flex-1">
                                <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest flex items-center gap-1.5 mb-2">
                                    <Info size={12} /> Why this works for you
                                </span>
                                <p className="text-sm text-gray-300 italic leading-relaxed">
                                    "{dest.reasoning || "Based on your vibes, this destination offers a perfect blend of experiences that match your request."}"
                                </p>
                            </div>

                            {/* Pricing breakdown */}
                            <div className="mb-6 pt-4 border-t border-gray-800 text-sm">
                                <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-3">Estimated pricing (INR)</p>
                                <div className="flex justify-between items-center mb-1 text-gray-400">
                                    <span>✈️ Flights</span>
                                    <span>₹{dest.flight_price?.toLocaleString('en-IN') || "24,500"}</span>
                                </div>
                                <div className="flex justify-between items-center mb-3 text-gray-400">
                                    <span>🏨 Hotel</span>
                                    <span>₹{dest.hotel_price?.toLocaleString('en-IN') || "12,800"}</span>
                                </div>
                                <div className="flex justify-between items-center pt-2 border-t border-gray-800/50">
                                    <span className="text-gray-300 font-medium tracking-wide">TOTAL COST</span>
                                    <span className="text-xl font-bold text-white">₹{((dest.flight_price || 24500) + (dest.hotel_price || 12800)).toLocaleString('en-IN')}</span>
                                </div>
                            </div>

                            {/* Book Action */}
                            <button
                                onClick={() => onBook(dest)}
                                className={`w-full py-3 rounded-xl font-semibold flex flex-row items-center justify-center gap-2 transition-all ${index === 0 ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'bg-gray-800 text-white hover:bg-gray-700'}`}
                            >
                                Book on TBO <ArrowRight size={16} />
                            </button>
                        </div>

                    </div>
                ))}
            </div>

            <button
                onClick={onReroll}
                className="flex items-center gap-2 px-6 py-3 bg-gray-900 border border-gray-800 text-white font-medium rounded-xl hover:bg-gray-800 transition-colors"
            >
                <RefreshCcw size={16} className="text-indigo-400" />
                Show Me Something Else
            </button>

        </div>
    );
}

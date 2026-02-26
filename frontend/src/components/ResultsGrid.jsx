import React from 'react';
import { MapPin, Star, ArrowRight, RefreshCcw, Info, SlidersHorizontal } from 'lucide-react';
import ItineraryCard from './ItineraryCard';

export default function ResultsGrid({ results, onBook, onReroll, onRefine, rejectedIds, originCity, travelMonth, activeVibes, setActiveVibes }) {
    if (!results || results.length === 0) return null;

    const toggleVibe = (vibe) => {
        setActiveVibes(prev =>
            prev.includes(vibe) ? prev.filter(v => v !== vibe) : [...prev, vibe]
        );
    };

    const applyFilters = () => {
        if (activeVibes.length === 0) return;
        onRefine && onRefine(activeVibes.join(', '));
        // Keep selections visible after refinement
    };

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

                {/* Transparent Query Composition Panel */}
                <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800 glass text-right">
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block mb-2">Query Composition</span>
                    <div className="flex flex-col items-end gap-1 text-xs text-gray-300 font-mono">
                        <div><span className="text-white font-bold">60%</span> Image Vibe Vectors</div>
                        <div><span className="text-white font-bold">30%</span> User Semantic Prompt</div>
                        <div><span className="text-white font-bold">10%</span> Active Filters</div>
                    </div>
                </div>
            </div>

            {/* Refine Output Vibes Row */}
            <div className="w-full mb-8 p-4 bg-gray-900/40 rounded-2xl border border-gray-800/80">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-1.5 pl-2">
                        <SlidersHorizontal size={10} /> Refine Output Vibes
                    </span>
                    {activeVibes.length > 0 && (
                        <button
                            onClick={applyFilters}
                            className="text-[10px] font-bold bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1 rounded-full uppercase tracking-widest transition-colors"
                        >
                            Apply {activeVibes.length} Filter{activeVibes.length > 1 ? 's' : ''}
                        </button>
                    )}
                </div>
                <div className="flex flex-wrap gap-2">
                    {['Solo Stops', '2 Destinations', '3 Destinations', 'South India', 'North India', 'More Adventure', 'Stricter Budget', 'More Luxury', 'Family Friendly', 'More Nature', 'City Vibes', 'Beachfront', 'Mountain Views', 'More Couple Focus'].map(vibe => (
                        <button
                            key={vibe}
                            onClick={() => toggleVibe(vibe)}
                            className={`text-xs px-4 py-1.5 rounded-full border transition-colors ${activeVibes.includes(vibe)
                                ? 'border-indigo-400 bg-indigo-500/20 text-indigo-200 font-semibold'
                                : 'border-gray-700 text-gray-400 hover:text-white hover:border-indigo-400 hover:bg-indigo-500/10'
                                }`}
                        >
                            {activeVibes.includes(vibe) ? '✓ ' : ''}{vibe}
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-12">
                {results.map((itinerary, index) => (
                    <ItineraryCard
                        key={index}
                        itinerary={itinerary}
                        onSelect={onBook}
                        travelMonth={travelMonth}
                        originCity={originCity}
                        index={index}
                    />
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

import React, { useState } from 'react';
import { RefreshCcw, SlidersHorizontal, ArrowLeft } from 'lucide-react';
import ItineraryCard from './ItineraryCard';

const FILTER_VIBES = [
    'Solo Stops', '2 Destinations', '3 Destinations',
    'South India', 'North India', 'Rajasthan',
    'More Adventure', 'Stricter Budget', 'More Luxury',
    'Family Friendly', 'Nature', 'Beachfront', 'Mountains', 'Romantic',
];

export default function ResultsGrid({
    results, onBook, onReroll, onRefine, onReset,
    rejectedIds, originCity, travelMonth,
    activeVibes, setActiveVibes,
    vibeTagsFromSearch = [],
    routeJustification = '',
}) {
    const [showFilters, setShowFilters] = useState(false);

    if (!results || results.length === 0) return null;

    const toggleVibe = (vibe) =>
        setActiveVibes(prev =>
            prev.includes(vibe) ? prev.filter(v => v !== vibe) : [...prev, vibe]
        );

    const applyFilters = () => {
        if (activeVibes.length === 0) return;
        onRefine?.(activeVibes.join(', '));
    };

    return (
        <div className="w-full max-w-6xl mx-auto px-4 py-10 animate-fade-in">

            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                    <button
                        onClick={onReset}
                        className="text-sm text-gray-400 hover:text-gray-700 flex items-center gap-1.5 mb-3 transition-colors"
                    >
                        <ArrowLeft size={14} /> New Search
                    </button>
                    <h2 className="text-3xl font-black text-gray-900 tracking-tight">
                        {results.length} Itinerary {results.length === 1 ? 'Match' : 'Options'} Found
                    </h2>
                    <p className="text-gray-500 mt-1">Based on live TBO pricing • Sorted by best value</p>
                </div>

                {/* AI Vibe Tags from search */}
                {vibeTagsFromSearch.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {vibeTagsFromSearch.slice(0, 4).map(tag => (
                            <span key={tag} className="section-badge">{tag}</span>
                        ))}
                    </div>
                )}
            </div>

            {/* Route justification */}
            {routeJustification && (
                <div className="card-light p-4 mb-6 flex items-start gap-3 border-blue-100 bg-blue-50/40">
                    <span className="text-lg flex-none mt-0.5">🗺️</span>
                    <div>
                        <p className="text-xs font-bold text-blue-700 uppercase tracking-wider mb-1">Route Intelligence</p>
                        <p className="text-sm text-gray-700 leading-relaxed">{routeJustification}</p>
                    </div>
                </div>
            )}

            {/* Filter row */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                    <button
                        onClick={() => setShowFilters(f => !f)}
                        className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
                    >
                        <SlidersHorizontal size={15} />
                        Refine Results
                        {activeVibes.length > 0 && (
                            <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded-full">
                                {activeVibes.length}
                            </span>
                        )}
                    </button>
                    {activeVibes.length > 0 && (
                        <div className="flex gap-2">
                            <button
                                onClick={() => setActiveVibes([])}
                                className="text-xs text-gray-400 hover:text-gray-700 transition-colors"
                            >
                                Clear filters
                            </button>
                            <button
                                onClick={applyFilters}
                                className="btn-primary text-xs px-4 py-2"
                            >
                                Apply {activeVibes.length} Filter{activeVibes.length > 1 ? 's' : ''}
                            </button>
                        </div>
                    )}
                </div>

                {showFilters && (
                    <div className="flex flex-wrap gap-2 animate-slide-up">
                        {FILTER_VIBES.map(vibe => (
                            <button
                                key={vibe}
                                onClick={() => toggleVibe(vibe)}
                                className={`tag-pill ${activeVibes.includes(vibe) ? 'active' : ''}`}
                            >
                                {activeVibes.includes(vibe) ? '✓ ' : ''}{vibe}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
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

            {/* Reroll */}
            <div className="flex justify-center">
                <button
                    onClick={onReroll}
                    className="btn-secondary flex items-center gap-2 px-6 py-3"
                >
                    <RefreshCcw size={15} className="text-blue-500" />
                    Show Different Options
                </button>
            </div>
        </div>
    );
}

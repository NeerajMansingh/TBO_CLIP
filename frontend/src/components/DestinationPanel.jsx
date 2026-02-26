const API_BASE = ''

export default function DestinationPanel({ uploadedPhoto, currentMatch, isUpdating, apiBase = API_BASE }) {
    const photoUrl = currentMatch.photo
        ? `${apiBase}/${currentMatch.photo}`
        : null

    const isFallback = currentMatch.hotels?.some(h => h.name.includes('(Fallback)')) || false

    return (
        <div className="h-full flex flex-col bg-gray-950/60 p-4 gap-4">
            {/* Journey Header */}
            <div className="mb-2 mt-4 flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-1">
                        Your {currentMatch.stops?.length > 1 ? `${currentMatch.stops.length} Stop` : ''} Journey
                    </h2>
                    <p className="text-white/50 text-sm">
                        Detailed price breakdown and intelligence for each stop on your itinerary.
                    </p>
                </div>
                {isFallback ? (
                    <span className="flex items-center gap-1.5 text-xs text-orange-300 bg-orange-500/10 px-2 py-1 rounded-lg border border-orange-500/30">
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        Mock Demo Mode
                    </span>
                ) : (
                    <span className="text-xs text-brand-300 bg-brand-500/10 px-2 py-1 rounded-lg border border-brand-500/30">
                        Live TBO Match
                    </span>
                )}
            </div>

            {/* Stops Grid */}
            <div className={`grid grid-cols-1 ${currentMatch.stops?.length === 3 ? 'md:grid-cols-3' : currentMatch.stops?.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-1'} gap-6 w-full transition-all duration-500 pb-4 ${isUpdating ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'}`}>
                {(() => {
                    const stopsToRender = currentMatch.stops && currentMatch.stops.length > 0
                        ? currentMatch.stops
                        : [{
                            destination: currentMatch.destination,
                            photo: currentMatch.photo,
                            tagline: currentMatch.tagline,
                            price_per_person: currentMatch.price,
                            flight_min_fare: currentMatch.flight_min_fare,
                            rating: 4.5,
                            best_season: "Year-round"
                        }];

                    return stopsToRender.map((stop, index) => {
                        const stopPhotoUrl = stop.photo
                            ? (stop.photo.startsWith('http') ? stop.photo : `${apiBase}/${stop.photo}`)
                            : null;
                        const defaultFlight = Math.floor(stop.price_per_person * 0.35);
                        const flightCost = stop.flight_min_fare || defaultFlight;
                        const hotelCost = stop.price_per_person ? stop.price_per_person - flightCost : 0;
                        const totalCost = flightCost + hotelCost;

                        return (
                            <div key={index} className="card flex flex-col h-full bg-gray-900 relative group border-gray-800/80 transition-all duration-300 hover:border-indigo-500/30 hover:shadow-2xl hover:shadow-indigo-500/10">

                                {/* Image Header */}
                                <div className="relative h-56 w-full overflow-hidden rounded-t-2xl">
                                    <img
                                        src={stopPhotoUrl || "https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"}
                                        alt={stop.destination}
                                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent"></div>

                                    {stopsToRender.length > 1 && (
                                        <div className="absolute top-4 right-4 bg-indigo-500 text-white font-bold text-[10px] px-3 py-1 rounded-full shadow-lg uppercase tracking-wider flex items-center gap-1.5">
                                            <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
                                            Stop {index + 1}
                                        </div>
                                    )}

                                    <div className="absolute bottom-4 left-4 right-4">
                                        <span className="text-indigo-400 text-xs font-bold uppercase tracking-widest flex items-center gap-1 mb-1">
                                            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> India
                                        </span>
                                        <h3 className="text-2xl font-bold text-white shadow-sm">{stop.destination}</h3>
                                    </div>
                                </div>

                                <div className="p-6 flex-1 flex flex-col rounded-b-2xl">
                                    <div className="flex justify-between items-center mb-4">
                                        <div className="flex items-center gap-1 text-yellow-500 font-medium">
                                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                                            <span className="text-white">{stop.rating || "4.5"}</span>
                                        </div>
                                        <div className="text-xs text-gray-400">
                                            Best: <span className="text-white font-medium">{stop.best_season || "Year-round"}</span>
                                        </div>
                                    </div>

                                    {/* Vibe Tags - using global match reasons for the overall vibe */}
                                    <div className="flex flex-wrap gap-2 mb-6">
                                        {(currentMatch.reasons || []).slice(0, 3).map((tag, i) => (
                                            <span key={i} className="text-[10px] bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-2 py-1 rounded uppercase tracking-wider font-bold">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>

                                    {/* Intelligence Narrative */}
                                    <div className="mb-6 bg-gray-950/50 p-4 rounded-xl border border-gray-800 flex-1">
                                        <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest flex items-center gap-1.5 mb-2">
                                            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg> Why this works for you
                                        </span>
                                        <p className="text-sm text-gray-300 italic leading-relaxed">
                                            "{stop.tagline || `Based on your vibes, ${stop.destination} offers a perfect blend of experiences that match your request.`}"
                                        </p>
                                    </div>

                                    {/* Pricing breakdown */}
                                    {stop.price_per_person && (
                                        <div className="mt-auto pt-4 border-t border-gray-800 text-sm">
                                            <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-3">Estimated price per person</p>
                                            <div className="flex justify-between items-center mb-1 text-gray-400">
                                                <span>✈️ Flights</span>
                                                <span>₹{flightCost.toLocaleString('en-IN')}</span>
                                            </div>
                                            <div className="flex justify-between items-center mb-3 text-gray-400">
                                                <span>🏨 Hotel</span>
                                                <span>₹{hotelCost.toLocaleString('en-IN')}</span>
                                            </div>
                                            <div className="flex justify-between items-center pt-2 border-t border-gray-800/50">
                                                <span className="text-gray-300 font-medium tracking-wide">Total Allocation</span>
                                                <span className="text-xl font-bold text-white">₹{totalCost.toLocaleString('en-IN')}</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    });
                })()}
            </div>
        </div>
    )
}

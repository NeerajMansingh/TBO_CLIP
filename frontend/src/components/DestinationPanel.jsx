const API_BASE = ''

export default function DestinationPanel({ uploadedPhoto, currentMatch, isUpdating, apiBase = API_BASE }) {
    const photoUrl = currentMatch.photo
        ? `${apiBase}/${currentMatch.photo}`
        : null

    const isFallback = currentMatch.hotels?.some(h => h.name.includes('(Fallback)')) || false

    return (
        <div className="h-full flex flex-col bg-gray-950/60 p-4 gap-4">
            {/* Header */}
            <div className="flex items-center gap-2 pt-2 px-1">
                <span className="text-lg">✈️</span>
                <span className="font-display font-bold text-white text-lg">VibeTravel</span>

                {isFallback ? (
                    <span className="ml-auto flex items-center gap-1.5 text-xs text-orange-300 bg-orange-500/10 px-2 py-1 rounded-lg border border-orange-500/30">
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        Mock Demo Mode
                    </span>
                ) : (
                    <span className="ml-auto text-xs text-brand-300 bg-brand-500/10 px-2 py-1 rounded-lg border border-brand-500/30">
                        Live TBO Match
                    </span>
                )}
            </div>

            {/* User's uploaded photo */}
            <div className="relative rounded-2xl overflow-hidden ring-1 ring-white/10 shadow-xl shrink-0">
                <img
                    src={uploadedPhoto}
                    alt="Your inspiration"
                    className="w-full h-44 object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                <div className="absolute bottom-3 left-3">
                    <span className="text-xs font-medium text-white/80 bg-black/40 backdrop-blur-sm px-2 py-1 rounded-lg border border-white/10">
                        📸 Your inspiration
                    </span>
                </div>
            </div>

            {/* Arrow connector */}
            <div className="flex items-center justify-center gap-3">
                <div className="flex-1 h-px bg-gradient-to-r from-transparent to-white/10" />
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-brand-500/15 border border-brand-400/25 text-brand-300 text-xs font-medium">
                    <span>CLIP matched</span>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
                <div className="flex-1 h-px bg-gradient-to-l from-transparent to-white/10" />
            </div>

            {/* Matched destination photo(s) */}
            <div className={`transition-all duration-500 ${isUpdating ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`}>
                {currentMatch.stops && currentMatch.stops.length > 1 ? (
                    <div className="flex gap-3 overflow-x-auto pb-4 snap-x">
                        {currentMatch.stops.map((stop, i) => (
                            <div key={i} className="relative rounded-2xl overflow-hidden ring-1 ring-white/10 shadow-xl shrink-0 w-48 h-32 snap-start">
                                <img
                                    src={`${apiBase}/${stop.photo}`}
                                    alt={stop.destination}
                                    className="w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                                <div className="absolute bottom-2 left-2 right-2">
                                    <span className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Stop {i + 1}</span>
                                    <h3 className="text-sm font-bold text-white leading-tight">{stop.destination}</h3>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="relative rounded-2xl overflow-hidden ring-1 ring-white/10 shadow-xl shrink-0">
                        {photoUrl ? (
                            <img
                                src={photoUrl}
                                alt={currentMatch.destination}
                                className="w-full h-44 object-cover"
                            />
                        ) : (
                            <div className="w-full h-44 bg-gradient-to-br from-brand-600/30 to-ocean-600/20 flex items-center justify-center">
                                <span className="text-4xl">🏝️</span>
                            </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                        <div className="absolute bottom-3 left-3 right-3">
                            <span className="text-xs font-medium text-white/80 bg-black/40 backdrop-blur-sm px-2 py-1 rounded-lg border border-white/10">
                                🎯 Best match
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* Destination info card */}
            <div
                className={`card p-4 space-y-3 transition-all duration-500 ${isUpdating ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'
                    }`}
            >
                <div className="flex items-start justify-between gap-2">
                    <div>
                        <h2 className="font-display text-2xl font-bold text-white leading-tight">
                            {currentMatch.destination}
                        </h2>
                        {currentMatch.tagline && (
                            <p className="text-white/50 text-xs mt-0.5 italic">{currentMatch.tagline}</p>
                        )}
                    </div>
                    <div className="text-right shrink-0">
                        <p className="text-2xl font-bold text-brand-400">
                            ₹{currentMatch.price?.toLocaleString('en-IN')}
                        </p>
                        <p className="text-white/40 text-xs">per person</p>
                    </div>
                </div>

                {/* Match reason tags */}
                {currentMatch.reasons?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                        {currentMatch.reasons.map((r, i) => (
                            <span
                                key={i}
                                className={`vibe-tag animate-fade-in`}
                                style={{ animationDelay: `${i * 80}ms` }}
                            >
                                {r}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

import HotelCard from '../components/HotelCard'

const TBO_URL = 'https://www.tbo.com'

export default function BookingScreen({ bookingData, apiBase }) {
    const {
        matched_destination,
        destination_photo,
        price_per_person,
        hotels = [],
        match_reasons = [],
        travel_dates,
        budget,
    } = bookingData

    const photoUrl = destination_photo
        ? `${apiBase}/${destination_photo}`
        : null

    return (
        <div className="min-h-screen bg-mesh">
            {/* Hero section */}
            <div className="relative h-72 md:h-96 overflow-hidden">
                {photoUrl ? (
                    <img
                        src={photoUrl}
                        alt={matched_destination}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-brand-600/30 to-ocean-600/30" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-gray-950 via-gray-950/50 to-transparent" />

                {/* Top bar */}
                <div className="absolute top-4 left-4">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-green-500/20 border border-green-500/30 text-green-300">
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                        Match confirmed
                    </span>
                </div>

                {/* Destination name overlay */}
                <div className="absolute bottom-6 left-6 right-6">
                    <p className="text-white/50 text-sm uppercase tracking-widest mb-1">Your perfect match</p>
                    <h1 className="font-display text-4xl md:text-5xl font-bold text-white mb-2">
                        {matched_destination}
                    </h1>
                    <div className="flex flex-wrap gap-2">
                        {match_reasons.map((r, i) => (
                            <span key={i} className="vibe-tag">{r}</span>
                        ))}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
                {/* Summary bar */}
                <div className="card p-5 flex flex-wrap gap-6 items-center justify-between">
                    <div>
                        <p className="text-white/40 text-xs uppercase tracking-wide mb-1">Price per person</p>
                        <p className="text-3xl font-bold text-white">
                            ₹{price_per_person?.toLocaleString('en-IN')}
                        </p>
                        <p className="text-white/40 text-xs mt-0.5">
                            {budget ? `Budget: ₹${Number(budget).toLocaleString('en-IN')}` : ''}{' '}
                            {price_per_person && budget ? `· saves ₹${(Number(budget) - price_per_person).toLocaleString('en-IN')}` : ''}
                        </p>
                    </div>

                    {travel_dates && (
                        <div>
                            <p className="text-white/40 text-xs uppercase tracking-wide mb-1">Travel dates</p>
                            <p className="text-white font-medium">{travel_dates}</p>
                        </div>
                    )}

                    <div>
                        <p className="text-white/40 text-xs uppercase tracking-wide mb-1">Hotels available</p>
                        <p className="text-white font-semibold">{hotels.length} options</p>
                    </div>
                </div>

                {/* Hotel cards */}
                <div>
                    <h2 className="text-xl font-display font-bold text-white mb-4">Where to stay</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {hotels.slice(0, 3).map((hotel, i) => (
                            <HotelCard key={i} hotel={hotel} index={i} />
                        ))}
                    </div>
                </div>

                {/* CTA */}
                <div className="text-center py-6">
                    <p className="text-white/50 text-sm mb-4">
                        Ready to make this trip happen?
                    </p>
                    <a
                        href={TBO_URL}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-3 px-10 py-4 rounded-2xl text-white font-bold text-lg
              bg-gradient-to-r from-brand-500 via-brand-600 to-orange-600
              shadow-xl shadow-brand-500/30 hover:shadow-brand-500/50
              hover:scale-[1.02] active:scale-[0.98]
              transition-all duration-200"
                    >
                        <span>Book on TBO</span>
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                    </a>
                    <p className="text-white/25 text-xs mt-3">Opens TBO's booking portal in a new tab</p>
                </div>
            </div>
        </div>
    )
}

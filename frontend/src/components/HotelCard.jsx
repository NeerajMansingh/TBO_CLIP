const API_BASE = ''

const STAR_COLORS = ['from-yellow-400 to-orange-400', 'from-orange-400 to-brand-500', 'from-brand-400 to-ocean-500']

export default function HotelCard({ hotel, index = 0, apiBase = API_BASE }) {
    const { name, price_per_night, rating, photo } = hotel
    const photoUrl = photo ? `${apiBase}/${photo}` : null

    const stars = Math.floor(rating)
    const hasHalf = rating - stars >= 0.5

    return (
        <div
            className="card overflow-hidden hover:scale-[1.02] hover:ring-1 hover:ring-white/20 transition-all duration-300 animate-fade-in"
            style={{ animationDelay: `${index * 120}ms` }}
        >
            {/* Hotel image */}
            <div className="relative h-36 overflow-hidden bg-white/5">
                {photoUrl ? (
                    <img
                        src={photoUrl}
                        alt={name}
                        className="w-full h-full object-cover"
                        onError={e => { e.target.style.display = 'none' }}
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-brand-600/20 to-ocean-600/15 flex items-center justify-center">
                        <span className="text-3xl opacity-50">🏨</span>
                    </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-gray-950/60 to-transparent" />

                {/* Price badge */}
                <div className="absolute top-2 right-2">
                    <span className="text-xs font-bold text-white bg-black/50 backdrop-blur-sm px-2 py-1 rounded-lg border border-white/10">
                        ₹{price_per_night?.toLocaleString('en-IN')}/night
                    </span>
                </div>

                {/* Index badge */}
                <div className="absolute top-2 left-2">
                    <span className={`text-xs font-bold text-white px-2 py-1 rounded-lg bg-gradient-to-r ${STAR_COLORS[index % 3]}`}>
                        #{index + 1} pick
                    </span>
                </div>
            </div>

            {/* Info */}
            <div className="p-4">
                <h3 className="font-semibold text-white text-sm leading-tight mb-2 line-clamp-2">
                    {name}
                </h3>

                {/* Stars rating */}
                <div className="flex items-center gap-1.5">
                    <div className="flex gap-0.5">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <svg
                                key={i}
                                className={`w-3.5 h-3.5 ${i < stars ? 'text-yellow-400' : 'text-white/15'}`}
                                fill="currentColor"
                                viewBox="0 0 20 20"
                            >
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                        ))}
                    </div>
                    <span className="text-xs text-white/60">{rating?.toFixed(1)}</span>
                </div>
            </div>
        </div>
    )
}

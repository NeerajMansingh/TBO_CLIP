import React from 'react';
import { MapPin, ArrowRight, Plane, Train, Bus } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const TRANSPORT_ICONS = {
    flight: <Plane size={12} />,
    train: <Train size={12} />,
    bus: <Bus size={12} />,
};

// Derive local image URL from destination name (matches backend /destinations/<slug>/1.jpg)
function getLocalImageUrl(destinationName) {
    if (!destinationName) return null;
    const slug = destinationName
        .toLowerCase()
        .replace(/[^a-z0-9\s_-]/g, '')
        .replace(/\s+/g, '_')
        .replace(/-/g, '_')
        .replace('andaman_islands', 'andaman')
        .replace('leh_ladakh', 'leh')
        .replace('kerala_hill_stations', 'kerala_hills')
        .replace('spiti_valley', 'spiti')
        .replace('ziro_valley', 'ziro');
    return `${API_BASE}/destinations/${slug}/1.jpg`;
}

function RouteConnector({ transport = 'flight' }) {
    return (
        <div className="flex items-center gap-1 flex-none">
            <div className="h-px w-6 bg-blue-200" />
            <span className="transport-badge">{TRANSPORT_ICONS[transport] || <Plane size={12} />}</span>
            <div className="h-px w-6 bg-blue-200" />
        </div>
    );
}

export default function ItineraryCard({ itinerary, onSelect, travelMonth, originCity, index }) {
    const { type, label, stops, total_price, region, stop_count } = itinerary;
    const [imgError, setImgError] = React.useState(false);

    const typeColors = {
        '1-stop': 'bg-emerald-50 text-emerald-700 border-emerald-200',
        '2-stop': 'bg-blue-50 text-blue-700 border-blue-200',
        '3-stop': 'bg-violet-50 text-violet-700 border-violet-200',
    };

    // Prefer local image file first; fall back to backend-returned photo URL
    const primaryPhotoLocal = getLocalImageUrl(stops[0]?.destination);
    const primaryPhotoRemote = stops[0]?.photo?.startsWith('http')
        ? stops[0].photo
        : stops[0]?.photo ? `${API_BASE}/${stops[0].photo}` : null;
    const heroUrl = !imgError && primaryPhotoLocal ? primaryPhotoLocal : primaryPhotoRemote;

    return (
        <div className="card-light overflow-hidden flex flex-col animate-slide-up" style={{ animationDelay: `${index * 80}ms` }}>
            {/* Hero image with stop photos */}
            <div className="relative h-48 overflow-hidden">
                {heroUrl
                    ? <img
                        src={heroUrl}
                        alt={stops[0]?.destination}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        onError={() => setImgError(true)}
                    />
                    : <div className="w-full h-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center">
                        <MapPin size={40} className="text-blue-300" />
                    </div>
                }
                {/* Gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

                {/* Journey type badge */}
                <div className="absolute top-3 left-3">
                    <span className={`text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full border ${typeColors[type] || typeColors['1-stop']}`}>
                        {label}
                    </span>
                </div>

                {/* Stop count */}
                <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm text-gray-700 text-[10px] font-bold px-2.5 py-1 rounded-full">
                    {stop_count} {stop_count === 1 ? 'city' : 'cities'}
                </div>

                {/* Destination name */}
                <div className="absolute bottom-3 left-3 right-3">
                    <p className="text-[10px] text-white/70 font-semibold uppercase tracking-wider mb-0.5 flex items-center gap-1">
                        <MapPin size={9} /> {region}
                    </p>
                    <h3 className="text-white font-bold text-lg leading-tight">
                        {stops.map(s => s.destination).join(' → ')}
                    </h3>
                </div>
            </div>

            {/* Route diagram */}
            {stops.length > 1 && (
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
                    <div className="flex items-center flex-wrap gap-1">
                        {originCity && (
                            <>
                                <span className="text-[11px] font-medium text-gray-400">{originCity}</span>
                                <RouteConnector transport="flight" />
                            </>
                        )}
                        {stops.map((stop, i) => (
                            <React.Fragment key={stop.destination}>
                                <div className="flex items-center gap-1">
                                    <div className="w-2 h-2 rounded-full bg-blue-500 flex-none" />
                                    <span className="text-[11px] font-bold text-gray-700">{stop.destination}</span>
                                </div>
                                {i < stops.length - 1 && <RouteConnector transport="flight" />}
                            </React.Fragment>
                        ))}
                    </div>
                </div>
            )}

            {/* Details */}
            <div className="p-4 flex-1 flex flex-col gap-3">
                {/* Stop thumbnails for multi-stop */}
                {stops.length > 1 && (
                    <div className="flex gap-2">
                        {stops.slice(1).map((stop, i) => {
                            const localUrl = getLocalImageUrl(stop.destination);
                            const remoteUrl = stop.photo?.startsWith('http') ? stop.photo : stop.photo ? `${API_BASE}/${stop.photo}` : null;
                            return (
                                <div key={i} className="flex-1 rounded-lg overflow-hidden h-14 bg-gray-100 relative">
                                    <img
                                        src={localUrl || remoteUrl}
                                        alt={stop.destination}
                                        className="w-full h-full object-cover"
                                        onError={e => {
                                            if (e.target.src !== remoteUrl && remoteUrl) e.target.src = remoteUrl;
                                            else e.target.style.display = 'none';
                                        }}
                                    />
                                    <div className="absolute inset-0 bg-black/30 flex items-end p-1">
                                        <span className="text-white text-[9px] font-bold">{stop.destination}</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Tagline */}
                {stops[0]?.tagline && (
                    <p className="text-xs text-gray-500 italic leading-relaxed line-clamp-2">
                        "{stops[0].tagline}"
                    </p>
                )}

                {/* Travel month */}
                {travelMonth && (
                    <div className="flex items-center gap-1.5 text-xs text-gray-500">
                        <span>📅</span>
                        <span>Best for {travelMonth} travel</span>
                    </div>
                )}

                {/* Price */}
                <div className="mt-auto pt-3 border-t border-gray-100 flex items-center justify-between">
                    <div>
                        <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wide mb-0.5">Total per person</p>
                        <div className="flex items-baseline gap-1">
                            <span className="price-large">₹{total_price.toLocaleString('en-IN')}</span>
                        </div>
                        <p className="text-[10px] text-gray-400 mt-0.5">incl. flights + hotels</p>
                    </div>
                    <button
                        onClick={() => onSelect(itinerary)}
                        className="btn-primary px-5 py-2.5 text-sm"
                    >
                        Explore <ArrowRight size={14} />
                    </button>
                </div>
            </div>
        </div>
    );
}

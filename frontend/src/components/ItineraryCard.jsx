import React from 'react';
import { MapPin, ArrowRight, Navigation, Plane, Building2 } from 'lucide-react';

export default function ItineraryCard({ itinerary, onSelect, travelMonth, originCity, index }) {
    if (!itinerary) return null;

    return (
        <div className="card flex flex-col h-full bg-gray-900 relative group border-gray-800/80 transition-all duration-300 hover:border-indigo-500/30 hover:shadow-2xl hover:shadow-indigo-500/10">

            {/* Header Area with Type Badge */}
            <div className="p-5 border-b border-gray-800/80 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent"></div>

                <div className="flex justify-between items-start relative z-10 mb-2">
                    <span className="text-indigo-400 text-xs font-bold uppercase tracking-widest flex items-center gap-1">
                        <Navigation size={12} /> {itinerary.region}
                    </span>
                    <span className="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2.5 py-1 rounded text-xs font-bold tracking-wider uppercase">
                        {itinerary.label} ({itinerary.type})
                    </span>
                </div>

                <h3 className="text-xl font-bold text-white relative z-10">{itinerary.stops.length} Stop Journey</h3>
            </div>

            {/* Stops Strip */}
            <div className="p-5 flex-1 flex flex-col gap-4">
                <div className="space-y-4 relative">
                    {/* Connecting line */}
                    {itinerary.stops.length > 1 && (
                        <div className="absolute left-6 pl-[1px] top-6 bottom-6 w-px bg-gray-800 z-0"></div>
                    )}

                    {itinerary.stops.map((stop, i) => (
                        <div key={stop.tbo_id} className="relative z-10">
                            {/* Destination row */}
                            <div className="flex gap-3 items-center mb-2">
                                <img
                                    src={stop.photo?.startsWith('http') ? stop.photo : `http://localhost:8000/${stop.photo}`}
                                    alt={stop.destination}
                                    className="w-12 h-12 rounded-lg object-cover ring-2 ring-gray-900 shadow-lg"
                                />
                                <div className="flex-1 min-w-0">
                                    <h4 className="text-sm font-bold text-white truncate">{stop.destination}</h4>
                                    <p className="text-xs text-gray-400 truncate mt-0.5">{stop.tagline || 'Scenic destination'}</p>
                                </div>
                            </div>

                            {/* Price chips for this stop */}
                            <div className="ml-15 pl-[60px] flex flex-wrap gap-2 text-[11px]">
                                {/* Hotel price */}
                                {stop.price_per_person != null && (
                                    <div className="flex flex-col">
                                        <span className="flex items-center gap-1 bg-gray-800/70 text-gray-200 px-2 py-0.5 rounded-full">
                                            <Building2 size={10} className="text-emerald-400" />
                                            Hotel: ₹{Math.round(stop.price_per_person / 5).toLocaleString('en-IN')}/night
                                        </span>
                                        {stop.hotel_price_date_label && (
                                            <span className="text-[9px] text-gray-500 mt-0.5 pl-1">
                                                (avail. for {stop.hotel_price_date_label})
                                            </span>
                                        )}
                                    </div>
                                )}
                                {/* Flight price */}
                                {stop.flight_min_fare != null ? (
                                    <span className="flex items-center gap-1 bg-gray-800/70 text-gray-200 px-2 py-0.5 rounded-full">
                                        <Plane size={10} className="text-sky-400" />
                                        Flight: ₹{stop.flight_min_fare.toLocaleString('en-IN')}
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1 bg-gray-800/50 text-gray-500 px-2 py-0.5 rounded-full">
                                        <Plane size={10} />
                                        Flight: checking...
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Total Pricing */}
            <div className="p-5 pt-0 mt-auto">
                <div className="mt-4 pt-4 border-t border-gray-800 text-sm">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-3">
                        Hotel total for {travelMonth} from {originCity}
                    </p>
                    <div className="flex justify-between items-end">
                        <span className="text-gray-300 font-medium tracking-wide">Total Hotel Cost</span>
                        <span className="text-2xl font-bold text-white tracking-tight">
                            ₹{itinerary.total_price?.toLocaleString('en-IN') || "N/A"}
                        </span>
                    </div>
                    {itinerary.stops.some(s => s.hotel_price_date_label) && (
                        <p className="text-[9px] text-amber-500/70 mt-1 text-right">
                            * Some prices shown for alternate availability dates
                        </p>
                    )}
                </div>

                {/* Select Action */}
                <button
                    onClick={() => onSelect(itinerary)}
                    className={`w-full mt-5 py-3 rounded-xl font-semibold flex flex-row items-center justify-center gap-2 transition-all ${index === 0 ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'bg-gray-800 text-white hover:bg-gray-700'}`}
                >
                    Plan This Trip <ArrowRight size={16} />
                </button>
            </div>
        </div>
    );
}


import React from 'react';
import { X, MapPin, Star, Check, Download } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function BookingModal({ itinerary, sessionId, onClose, onConfirmed }) {
    const [confirming, setConfirming] = React.useState(false);
    const [confirmed, setConfirmed] = React.useState(false);

    if (!itinerary) return null;

    const { stops, total_price, label, region, type } = itinerary;

    const handleConfirm = async () => {
        setConfirming(true);
        try {
            await fetch(`${API_BASE}/confirm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId }),
            });
            setConfirmed(true);
            setTimeout(() => { onConfirmed?.(); }, 2200);
        } catch (err) {
            console.warn('Confirm failed:', err);
        } finally {
            setConfirming(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm animate-fade-in">
            <div className="bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl w-full sm:max-w-lg max-h-[90vh] overflow-y-auto animate-slide-up">

                {confirmed ? (
                    <div className="p-12 text-center">
                        <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                            <Check size={32} className="text-emerald-600" />
                        </div>
                        <h2 className="text-2xl font-black text-gray-900 mb-2">Trip Confirmed! 🎉</h2>
                        <p className="text-gray-500">Your itinerary has been saved. Have a wonderful trip!</p>
                    </div>
                ) : (
                    <>
                        {/* Header */}
                        <div className="flex items-center justify-between p-5 border-b border-gray-100">
                            <div>
                                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">{label}</p>
                                <h2 className="text-xl font-black text-gray-900">{stops.map(s => s.destination).join(' → ')}</h2>
                            </div>
                            <button onClick={onClose} className="text-gray-400 hover:text-gray-700 transition-colors p-1">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Stops summary */}
                        <div className="p-5 space-y-3">
                            {stops.map((stop, i) => {
                                const photoUrl = stop.photo?.startsWith('http') ? stop.photo : stop.photo ? `${API_BASE}/${stop.photo}` : null;
                                const flight = stop.flight_min_fare || Math.round((stop.price_per_person || 0) * 0.35);
                                const hotel = Math.max(0, (stop.price_per_person || 0) - flight);
                                return (
                                    <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                                        {photoUrl && <img src={photoUrl} alt={stop.destination} className="w-14 h-12 rounded-lg object-cover flex-none" />}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <div className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center flex-none">{i + 1}</div>
                                                <p className="font-bold text-gray-900 text-sm">{stop.destination}</p>
                                            </div>
                                            <div className="flex gap-3 text-[11px] text-gray-500">
                                                <span>✈️ ₹{flight.toLocaleString('en-IN')}</span>
                                                <span>🏨 ₹{hotel.toLocaleString('en-IN')}</span>
                                            </div>
                                        </div>
                                        <p className="text-sm font-bold text-gray-800 flex-none">₹{(stop.price_per_person || 0).toLocaleString('en-IN')}</p>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Total */}
                        <div className="px-5 py-4 bg-blue-50 border-t border-blue-100 flex items-center justify-between">
                            <div>
                                <p className="text-xs text-blue-600 font-semibold uppercase tracking-wide">Total (per person)</p>
                                <p className="text-3xl font-black text-gray-900">₹{total_price.toLocaleString('en-IN')}</p>
                            </div>
                            <div className="section-badge">{region}</div>
                        </div>

                        {/* Note */}
                        <div className="px-5 pb-2 pt-3">
                            <p className="text-xs text-gray-400">
                                ℹ️ Prices are estimates based on live TBO availability. Final prices confirmed at booking.
                            </p>
                        </div>

                        {/* Actions */}
                        <div className="p-5 flex gap-3">
                            <button onClick={onClose} className="btn-secondary flex-1 py-3">
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirm}
                                disabled={confirming}
                                className="btn-primary flex-1 py-3"
                            >
                                {confirming ? 'Confirming…' : '✓ Confirm Booking'}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

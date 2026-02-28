import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { TRAVEL_STYLES, getRecommendedStyle } from '../data/travelStyles'
import { getFallbackHotel } from '../data/fallbackHotels'

/**
 * TravelStylePicker — Step 2: Choose how you travel.
 *
 * Props:
 *   budget       — int, user budget
 *   destination  — string
 *   hotels       — existing hotel data from session (if any)
 *   onComplete   — (styleObj) => void
 *   onBack       — () => void
 */
export default function TravelStylePicker({ budget, destination, hotels = [], onComplete, onBack }) {
    const recommendedId = useMemo(() => getRecommendedStyle(budget), [budget])
    const [selectedId, setSelectedId] = useState(recommendedId)

    const selectedStyle = TRAVEL_STYLES.find(s => s.id === selectedId)
    const estimatedCost = Math.round(budget * (selectedStyle?.budget_multiplier || 1))

    // Get hotel preview for selected style
    const getHotelPreview = (style) => {
        // Try to find a hotel from real data matching style stars
        const maxStar = Math.max(...style.hotel_stars)
        const realHotel = hotels.find(h => h.rating >= maxStar - 0.5 && h.rating <= maxStar + 0.5)
        if (realHotel) return realHotel
        return getFallbackHotel(destination, style.hotel_stars)
    }

    const previewHotel = selectedStyle ? getHotelPreview(selectedStyle) : null

    return (
        <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 pb-32">
            {/* Header */}
            <div className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-100">
                <div className="max-w-3xl mx-auto px-4 py-4">
                    <div className="flex items-center gap-3">
                        <button onClick={onBack} className="w-9 h-9 flex items-center justify-center rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors text-gray-600 text-sm">
                            ←
                        </button>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">How do you like to travel?</h1>
                            <p className="text-xs text-gray-500 mt-0.5">
                                Your budget: ₹{budget.toLocaleString('en-IN')}
                            </p>
                        </div>
                        <div className="ml-auto text-right">
                            <div className="text-[10px] text-gray-400 uppercase tracking-wide">Step 2 of 4</div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-3xl mx-auto px-4 py-8">
                {/* Style cards grid */}
                <div className="grid grid-cols-2 gap-4 mb-8">
                    {TRAVEL_STYLES.map((style, idx) => {
                        const isSelected = selectedId === style.id
                        const isRecommended = style.id === recommendedId
                        const estimated = Math.round(budget * style.budget_multiplier)
                        const isOverBudget = estimated > budget * 1.2

                        return (
                            <motion.button
                                key={style.id}
                                initial={{ opacity: 0, y: 16 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.08 }}
                                onClick={() => setSelectedId(style.id)}
                                className={`relative p-5 rounded-2xl text-left transition-all duration-200 border-2 ${isSelected
                                    ? 'border-emerald-400 bg-emerald-50/50 shadow-lg shadow-emerald-100'
                                    : isOverBudget
                                        ? 'border-gray-100 bg-gray-50 opacity-60'
                                        : 'border-gray-100 bg-white hover:border-gray-200 hover:shadow-md'
                                    }`}
                            >
                                {/* Recommended badge */}
                                {isRecommended && (
                                    <div className="absolute -top-2.5 left-4 px-2.5 py-0.5 bg-emerald-500 text-white text-[10px] font-bold rounded-full uppercase tracking-wide shadow-sm">
                                        Recommended
                                    </div>
                                )}

                                {/* Over budget badge */}
                                {isOverBudget && (
                                    <div className="absolute -top-2.5 right-4 px-2.5 py-0.5 bg-red-100 text-red-600 text-[10px] font-semibold rounded-full">
                                        Over budget
                                    </div>
                                )}

                                <span className="text-3xl mb-2 block">{style.emoji}</span>
                                <h3 className="font-bold text-gray-800 text-base mb-1">{style.label}</h3>
                                <p className="text-xs text-gray-500 mb-2">{style.tagline}</p>
                                <p className="text-sm font-semibold" style={{ color: style.color }}>
                                    ₹{estimated.toLocaleString('en-IN')}
                                </p>
                                <p className="text-[10px] text-gray-400 mt-1">{style.description}</p>

                                {/* Selection indicator */}
                                {isSelected && (
                                    <motion.div
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="absolute top-3 right-3 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center"
                                    >
                                        <span className="text-white text-xs">✓</span>
                                    </motion.div>
                                )}
                            </motion.button>
                        )
                    })}
                </div>

                {/* Preview panel */}
                {selectedStyle && (
                    <motion.div
                        key={selectedId}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white rounded-2xl border border-gray-200 p-5 mb-6"
                    >
                        <h3 className="text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide">
                            What you'll get
                        </h3>

                        <div className="space-y-3">
                            {previewHotel && (
                                <div className="flex items-center gap-3">
                                    <span className="text-lg">🏨</span>
                                    <div>
                                        <p className="text-sm font-medium text-gray-800">{previewHotel.name}</p>
                                        <p className="text-xs text-gray-500">
                                            {'★'.repeat(previewHotel.stars || previewHotel.rating || 3)} · ₹{(previewHotel.price_night || previewHotel.price_per_night || 3000).toLocaleString('en-IN')}/night
                                        </p>
                                    </div>
                                </div>
                            )}

                            <div className="flex items-center gap-3">
                                <span className="text-lg">🚗</span>
                                <div>
                                    <p className="text-sm font-medium text-gray-800">
                                        {selectedStyle.transport === 'shared' && 'Shared transport (bus, auto, shared cabs)'}
                                        {selectedStyle.transport === 'shared+private mix' && 'Mix of shared & private transfers'}
                                        {selectedStyle.transport === 'private' && 'Private cab included for all transfers'}
                                        {selectedStyle.transport === 'private+premium' && 'Premium sedan / SUV with driver'}
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center gap-3">
                                <span className="text-lg">📋</span>
                                <div>
                                    <p className="text-sm font-medium text-gray-800">
                                        Up to {selectedStyle.activities_per_day} activities per day
                                    </p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>

            {/* Sticky bottom */}
            <motion.div
                initial={{ y: 100 }}
                animate={{ y: 0 }}
                className="fixed bottom-0 left-0 right-0 z-40 bg-white/90 backdrop-blur-xl border-t border-gray-200 p-4"
            >
                <div className="max-w-3xl mx-auto flex items-center justify-between gap-4">
                    <div>
                        <p className="text-sm font-semibold text-gray-800">
                            {selectedStyle?.label || 'Choose a style'}
                        </p>
                        <p className="text-xs text-gray-500">
                            Est. ₹{estimatedCost.toLocaleString('en-IN')} total
                        </p>
                    </div>
                    <button
                        onClick={() => onComplete(selectedStyle)}
                        disabled={!selectedStyle}
                        className="px-6 py-3 rounded-xl text-sm font-semibold bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-200 transition-all"
                    >
                        Build My Itinerary →
                    </button>
                </div>
            </motion.div>
        </div>
    )
}

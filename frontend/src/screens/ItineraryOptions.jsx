import { useState } from 'react'
import { motion } from 'framer-motion'

/**
 * ItineraryOptions — Step 3: Pick from 3 AI-generated itinerary packages.
 *
 * Props:
 *   options     — array of 3 package objects
 *   destination — string
 *   onSelect    — (option) => void
 *   onBack      — () => void
 *   budget      — int
 */

const TIERS = {
    option_a: {
        icon: '⚡',
        accent: 'from-emerald-500 to-teal-400',
        accentLight: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        badge: 'Best Value',
        ring: 'ring-emerald-200',
        btnBg: 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-200/60',
        progressColor: '#10b981',
    },
    option_b: {
        icon: '✨',
        accent: 'from-blue-500 to-indigo-500',
        accentLight: 'bg-blue-50 text-blue-700 border-blue-200',
        badge: '⭐ Recommended',
        ring: 'ring-blue-200',
        btnBg: 'bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 shadow-blue-300/60',
        progressColor: '#3b82f6',
    },
    option_c: {
        icon: '👑',
        accent: 'from-amber-500 to-orange-400',
        accentLight: 'bg-amber-50 text-amber-700 border-amber-200',
        badge: 'Premium',
        ring: 'ring-amber-200',
        btnBg: 'bg-amber-500 hover:bg-amber-600 shadow-amber-200/60',
        progressColor: '#f59e0b',
    },
}

// Circular progress ring component
function BudgetRing({ percent, color, size = 56 }) {
    const stroke = 4
    const radius = (size - stroke) / 2
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (Math.min(percent, 100) / 100) * circumference
    const isOver = percent > 100

    return (
        <svg width={size} height={size} className="transform -rotate-90">
            <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke="currentColor"
                strokeWidth={stroke}
                className="text-gray-100"
            />
            <motion.circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={isOver ? '#ef4444' : color}
                strokeWidth={stroke}
                strokeLinecap="round"
                strokeDasharray={circumference}
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset: offset }}
                transition={{ duration: 0.8, ease: 'easeOut', delay: 0.3 }}
            />
            <text
                x={size / 2}
                y={size / 2}
                textAnchor="middle"
                dominantBaseline="central"
                className="transform rotate-90 origin-center"
                style={{ fontSize: '11px', fontWeight: 700, fill: isOver ? '#ef4444' : '#374151' }}
            >
                {percent}%
            </text>
        </svg>
    )
}

// Mini timeline dot for day preview
function DayDot({ dayNum, label, slotsCount, isFirst, isLast }) {
    return (
        <div className="flex items-center gap-1.5 text-[10px]">
            <div className="relative flex flex-col items-center">
                <div className={`w-2 h-2 rounded-full ${slotsCount > 0 ? 'bg-gray-800' : 'bg-gray-300'}`} />
                {!isLast && <div className="w-px h-3 bg-gray-200 mt-0.5" />}
            </div>
            <span className="text-gray-500 whitespace-nowrap leading-none">
                {label || `Day ${dayNum}`}
            </span>
        </div>
    )
}

export default function ItineraryOptions({ options = [], destination, onSelect, onBack, budget }) {
    const [hoveredId, setHoveredId] = useState(null)

    // Safely get the numeric day count
    const getDayCount = (option) => {
        if (typeof option.days_count === 'number') return option.days_count
        if (typeof option.days === 'number') return option.days
        if (Array.isArray(option.days)) return option.days.length
        return 0
    }

    // Steps for progress indicator
    const steps = [
        { label: 'Activities', done: true },
        { label: 'Style', done: true },
        { label: 'Package', active: true },
        { label: 'Customize', done: false },
    ]

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
            {/* ── Header ──────────────────────────────────────── */}
            <div className="sticky top-0 z-30 bg-white/70 backdrop-blur-2xl border-b border-gray-100/80">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={onBack}
                            className="w-10 h-10 flex items-center justify-center rounded-2xl bg-gray-100/80 hover:bg-gray-200/80 transition-all text-gray-500 hover:text-gray-700 hover:scale-105 active:scale-95"
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M19 12H5M12 19l-7-7 7-7" />
                            </svg>
                        </button>
                        <div className="flex-1">
                            <h1 className="text-lg sm:text-xl font-extrabold text-gray-900 tracking-tight">
                                Choose your {destination} package
                            </h1>
                            <p className="text-xs text-gray-400 mt-0.5 font-medium">
                                3 curated options based on your preferences
                            </p>
                        </div>
                    </div>

                    {/* Step progress bar */}
                    <div className="flex items-center gap-1 mt-4">
                        {steps.map((step, i) => (
                            <div key={i} className="flex items-center flex-1">
                                <div className="flex items-center gap-1.5 flex-1">
                                    <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${step.done
                                            ? 'bg-emerald-500 text-white'
                                            : step.active
                                                ? 'bg-blue-500 text-white ring-4 ring-blue-100'
                                                : 'bg-gray-200 text-gray-400'
                                        }`}>
                                        {step.done ? '✓' : i + 1}
                                    </div>
                                    <span className={`text-[10px] font-semibold hidden sm:inline ${step.active ? 'text-blue-600' : step.done ? 'text-gray-500' : 'text-gray-300'
                                        }`}>
                                        {step.label}
                                    </span>
                                </div>
                                {i < steps.length - 1 && (
                                    <div className={`flex-1 h-px mx-1 ${step.done ? 'bg-emerald-300' : 'bg-gray-200'}`} />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Cards ──────────────────────────────────────── */}
            <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
                {options.length > 0 && (
                    <div className="grid md:grid-cols-3 gap-5">
                        {options.map((option, idx) => {
                            const tier = TIERS[option.id] || TIERS.option_a
                            const isRecommended = option.recommended
                            const isHovered = hoveredId === option.id
                            const dayCount = getDayCount(option)
                            const budgetPercent = budget > 0
                                ? Math.round(((option.total_cost || 0) / budget) * 100)
                                : 0
                            const activityCount = Array.isArray(option.activities)
                                ? option.activities.length
                                : 0

                            // Get day schedule for mini preview (from days array if available)
                            const daySchedule = Array.isArray(option.days) ? option.days : []

                            return (
                                <motion.div
                                    key={option.id}
                                    initial={{ opacity: 0, y: 30, scale: 0.97 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    transition={{
                                        delay: idx * 0.12,
                                        type: 'spring',
                                        stiffness: 260,
                                        damping: 22,
                                    }}
                                    onMouseEnter={() => setHoveredId(option.id)}
                                    onMouseLeave={() => setHoveredId(null)}
                                    className={`group relative rounded-3xl bg-white overflow-hidden transition-all duration-300 cursor-pointer ${isRecommended
                                            ? 'ring-2 ring-blue-300 shadow-xl shadow-blue-100/50'
                                            : 'ring-1 ring-gray-200/80 shadow-md hover:shadow-xl'
                                        } ${isHovered ? 'scale-[1.02] -translate-y-1' : ''}`}
                                    onClick={() => onSelect(option)}
                                >
                                    {/* Gradient accent bar at top */}
                                    <div className={`h-1.5 bg-gradient-to-r ${tier.accent}`} />

                                    {/* Recommended glow effect */}
                                    {isRecommended && (
                                        <div className="absolute inset-0 bg-gradient-to-b from-blue-50/40 to-transparent pointer-events-none" />
                                    )}

                                    <div className="relative p-5 sm:p-6">
                                        {/* Badge + Icon row */}
                                        <div className="flex items-start justify-between mb-4">
                                            <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${tier.accent} flex items-center justify-center text-xl shadow-lg`}>
                                                {tier.icon}
                                            </div>
                                            <span className={`px-2.5 py-1 text-[10px] font-bold rounded-full border ${tier.accentLight}`}>
                                                {tier.badge}
                                            </span>
                                        </div>

                                        {/* Title & tagline */}
                                        <h3 className="text-lg font-extrabold text-gray-900 mb-1 tracking-tight">
                                            {option.label}
                                        </h3>
                                        <p className="text-sm text-gray-500 mb-4 leading-relaxed">
                                            {option.tagline}
                                        </p>

                                        {/* Stats chips */}
                                        <div className="flex flex-wrap gap-2 mb-5">
                                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-gray-50 text-xs font-medium text-gray-600">
                                                📅 {dayCount} days
                                            </span>
                                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-gray-50 text-xs font-medium text-gray-600">
                                                🎯 {activityCount} activities
                                            </span>
                                        </div>

                                        {/* Hotel */}
                                        {option.hotel && (
                                            <div className="flex items-center gap-3 mb-3 p-3 rounded-2xl bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-100/80">
                                                <div className="w-9 h-9 rounded-xl bg-white shadow-sm flex items-center justify-center text-base">
                                                    🏨
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs font-bold text-gray-800 truncate">{option.hotel.name}</p>
                                                    <p className="text-[10px] text-gray-400">
                                                        {'★'.repeat(option.hotel.stars)} · ₹{(option.hotel.price_night || option.hotel.price_per_night || 0).toLocaleString('en-IN')}/night
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {/* Flight */}
                                        {option.flight && (
                                            <div className="flex items-center gap-3 mb-3 p-3 rounded-2xl bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-100/80">
                                                <div className="w-9 h-9 rounded-xl bg-white shadow-sm flex items-center justify-center text-base">
                                                    ✈️
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs font-bold text-gray-800 truncate">
                                                        {option.flight.from} → {option.flight.to}
                                                    </p>
                                                    <p className="text-[10px] text-gray-400">
                                                        {option.flight.airline} · ₹{(option.flight.price || 0).toLocaleString('en-IN')}
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {/* Highlights */}
                                        {option.highlights && option.highlights.length > 0 && (
                                            <div className="mb-5">
                                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
                                                    Highlights
                                                </p>
                                                <div className="space-y-1.5">
                                                    {option.highlights.slice(0, 4).map((h, i) => (
                                                        <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                                                            <div className={`w-1.5 h-1.5 rounded-full bg-gradient-to-r ${tier.accent} flex-shrink-0`} />
                                                            {h}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Mini day preview */}
                                        {daySchedule.length > 0 && (
                                            <div className="mb-5 p-3 rounded-2xl bg-slate-50/80 border border-gray-100/50">
                                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
                                                    Day Overview
                                                </p>
                                                <div className="space-y-0.5">
                                                    {daySchedule.slice(0, 4).map((day, i) => (
                                                        <DayDot
                                                            key={i}
                                                            dayNum={day.day}
                                                            label={day.label}
                                                            slotsCount={day.slots?.filter(s => s.activity).length || 0}
                                                            isFirst={i === 0}
                                                            isLast={i === Math.min(daySchedule.length, 4) - 1}
                                                        />
                                                    ))}
                                                    {daySchedule.length > 4 && (
                                                        <p className="text-[10px] text-gray-400 ml-4">
                                                            +{daySchedule.length - 4} more days
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* Divider */}
                                        <div className="h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent mb-4" />

                                        {/* Price + Budget ring + CTA */}
                                        <div className="flex items-end justify-between">
                                            <div className="flex items-center gap-3">
                                                <BudgetRing
                                                    percent={budgetPercent}
                                                    color={tier.progressColor}
                                                />
                                                <div>
                                                    <p className="text-2xl font-black text-gray-900 tracking-tight leading-none">
                                                        ₹{(option.total_cost || 0).toLocaleString('en-IN')}
                                                    </p>
                                                    <p className="text-[10px] text-gray-400 mt-0.5 font-medium">
                                                        per person · {budgetPercent}% of budget
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* CTA button */}
                                        <motion.button
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.97 }}
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                onSelect(option)
                                            }}
                                            className={`w-full mt-4 py-3 rounded-2xl text-sm font-bold text-white transition-all shadow-lg ${tier.btnBg}`}
                                        >
                                            {isRecommended ? '🚀 Customize This Plan' : 'View Full Plan →'}
                                        </motion.button>
                                    </div>
                                </motion.div>
                            )
                        })}
                    </div>
                )}

                {/* Empty / loading state */}
                {options.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-24">
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                            className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-2xl text-white shadow-xl mb-6"
                        >
                            ✨
                        </motion.div>
                        <h2 className="text-xl font-extrabold text-gray-800 mb-2">
                            Crafting your perfect itinerary...
                        </h2>
                        <p className="text-sm text-gray-400 max-w-sm text-center">
                            We're building 3 curated packages based on your activity selections and travel style
                        </p>
                        <div className="flex gap-1.5 mt-6">
                            {[0, 1, 2].map(i => (
                                <motion.div
                                    key={i}
                                    animate={{ scale: [1, 1.3, 1] }}
                                    transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                                    className="w-2 h-2 rounded-full bg-blue-400"
                                />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

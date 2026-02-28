import { motion } from 'framer-motion'

/**
 * ActivityCard — Reusable card for both ActivityDiscovery and ItineraryEditor.
 *
 * Props:
 *   activity      — activity object from activities.js
 *   selected      — boolean, whether this card is currently selected
 *   onToggle      — callback when tapped (for selection mode)
 *   compact       — boolean, smaller layout for editor pool
 *   draggable     — boolean, shows drag handle
 *   locked        — boolean, shows lock icon (non-interactive)
 *   onRemove      — callback for remove button in editor
 */
export default function ActivityCard({
    activity,
    selected = false,
    onToggle,
    compact = false,
    draggable = false,
    locked = false,
    onRemove,
    className = '',
}) {
    const handleClick = () => {
        if (locked) return
        if (onToggle) onToggle(activity)
    }

    const timeColors = {
        morning: 'bg-amber-50 text-amber-700 border-amber-200',
        afternoon: 'bg-orange-50 text-orange-700 border-orange-200',
        evening: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    }

    if (compact) {
        return (
            <motion.div
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className={`
          flex items-center gap-3 p-3 rounded-xl bg-white border cursor-pointer
          transition-all duration-200 hover:shadow-md
          ${selected ? 'border-emerald-400 bg-emerald-50/50 shadow-sm' : 'border-gray-200'}
          ${locked ? 'opacity-60 cursor-not-allowed' : ''}
          ${className}
        `}
                onClick={handleClick}
                whileHover={!locked ? { scale: 1.02 } : {}}
                whileTap={!locked ? { scale: 0.98 } : {}}
            >
                {draggable && !locked && (
                    <span className="text-gray-300 text-sm cursor-grab active:cursor-grabbing select-none">⠿</span>
                )}
                {locked && <span className="text-gray-400 text-sm">🔒</span>}
                <span className="text-xl flex-shrink-0">{activity.emoji}</span>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{activity.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-500">{activity.duration_hrs}hrs</span>
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs font-medium text-gray-600">₹{activity.cost.toLocaleString('en-IN')}</span>
                    </div>
                </div>
                {onRemove && !locked && (
                    <button
                        onClick={e => { e.stopPropagation(); onRemove(activity) }}
                        className="w-6 h-6 flex items-center justify-center rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors text-sm"
                    >
                        ✕
                    </button>
                )}
                {selected && !compact && (
                    <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-xs">✓</span>
                    </div>
                )}
            </motion.div>
        )
    }

    // Full-size card (ActivityDiscovery)
    return (
        <motion.div
            layout
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onClick={handleClick}
            className={`
        relative rounded-2xl p-4 cursor-pointer transition-all duration-200
        ${selected
                    ? 'bg-emerald-50 border-2 border-emerald-400 shadow-md shadow-emerald-100'
                    : 'bg-white border-2 border-gray-100 hover:border-gray-200 hover:shadow-md'
                }
        ${className}
      `}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.97 }}
        >
            {/* Selection checkmark */}
            {selected && (
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg z-10"
                >
                    <span className="text-white text-xs font-bold">✓</span>
                </motion.div>
            )}

            {/* Emoji + Name */}
            <div className="flex items-start gap-3 mb-2">
                <span className="text-3xl">{activity.emoji}</span>
                <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 text-sm leading-tight">{activity.name}</h3>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{activity.description}</p>
                </div>
            </div>

            {/* Meta row */}
            <div className="flex items-center gap-2 mt-3 flex-wrap">
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${timeColors[activity.time_of_day] || 'bg-gray-50 text-gray-600 border-gray-200'}`}>
                    {activity.time_of_day}
                </span>
                <span className="text-xs text-gray-500">{activity.duration_hrs}hrs</span>
                <span className="text-xs text-gray-400">•</span>
                <span className="text-xs font-semibold text-gray-700">₹{activity.cost.toLocaleString('en-IN')}</span>
            </div>
        </motion.div>
    )
}

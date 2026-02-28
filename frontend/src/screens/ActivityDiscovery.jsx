import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ActivityCard from '../components/ActivityCard'
import { getActivitiesForDestination, CATEGORIES } from '../data/activities'
import { getRelevantTags, vibeMatchScore } from '../data/vibeTagMap'

/**
 * ActivityDiscovery — Step 1: Browse & select activities for the matched destination.
 *
 * Props:
 *   destination — string, matched destination name
 *   duration    — int, trip duration days
 *   budget      — int, user budget
 *   vibes       — string[], CLIP vibe tags
 *   onComplete  — (selectedActivities[]) => void
 *   onBack      — () => void
 */
export default function ActivityDiscovery({ destination, duration, budget, vibes = [], onComplete, onBack }) {
    const allActivities = useMemo(() => getActivitiesForDestination(destination), [destination])
    const relevantTags = useMemo(() => getRelevantTags(vibes), [vibes])

    // Sort activities by vibe relevance
    const sortedActivities = useMemo(() => {
        return [...allActivities].sort((a, b) => {
            const scoreA = vibeMatchScore(a, relevantTags) * 100 + a.popularity
            const scoreB = vibeMatchScore(b, relevantTags) * 100 + b.popularity
            return scoreB - scoreA
        })
    }, [allActivities, relevantTags])

    // Top picks = activities with at least 1 matching vibe tag
    const topPicks = useMemo(() => {
        return sortedActivities.filter(a => vibeMatchScore(a, relevantTags) > 0).slice(0, 4)
    }, [sortedActivities, relevantTags])

    const [selectedIds, setSelectedIds] = useState(() => {
        // Auto-pre-select top picks
        return new Set(topPicks.map(a => a.id))
    })
    const [activeCategory, setActiveCategory] = useState('all')

    const toggleActivity = (activity) => {
        setSelectedIds(prev => {
            const next = new Set(prev)
            if (next.has(activity.id)) {
                next.delete(activity.id)
            } else {
                next.add(activity.id)
            }
            return next
        })
    }

    const selectedActivities = allActivities.filter(a => selectedIds.has(a.id))
    const estimatedCost = selectedActivities.reduce((sum, a) => sum + a.cost, 0)

    // Get available categories for this destination
    const availableCategories = useMemo(() => {
        const catSet = new Set(allActivities.map(a => a.category))
        return CATEGORIES.filter(c => catSet.has(c.id))
    }, [allActivities])

    // Filter by active category
    const filteredActivities = activeCategory === 'all'
        ? sortedActivities
        : sortedActivities.filter(a => a.category === activeCategory)

    // Separate top picks from the rest for display
    const topPickIds = new Set(topPicks.map(a => a.id))
    const otherActivities = filteredActivities.filter(a => !topPickIds.has(a.id))

    // Group "other" activities by category for nice display
    const groupedOthers = useMemo(() => {
        if (activeCategory !== 'all') return [{ category: activeCategory, items: otherActivities }]
        const groups = {}
        for (const act of otherActivities) {
            if (!groups[act.category]) groups[act.category] = []
            groups[act.category].push(act)
        }
        return CATEGORIES
            .filter(c => groups[c.id])
            .map(c => ({ category: c.id, label: c.label, emoji: c.emoji, items: groups[c.id] }))
    }, [otherActivities, activeCategory])

    const canContinue = selectedIds.size >= 2

    if (allActivities.length === 0) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6">
                <div className="text-center max-w-md">
                    <p className="text-6xl mb-4">🗺️</p>
                    <h2 className="text-xl font-bold text-gray-800 mb-2">No Activities Found</h2>
                    <p className="text-gray-500 mb-6">We don't have curated activities for {destination} yet.</p>
                    <button onClick={onBack} className="px-6 py-3 bg-gray-100 rounded-xl text-gray-700 font-medium hover:bg-gray-200 transition-colors">
                        ← Go Back
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 pb-32">
            {/* Header */}
            <div className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-100">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <div className="flex items-center gap-3 mb-3">
                        <button onClick={onBack} className="w-9 h-9 flex items-center justify-center rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors text-gray-600 text-sm">
                            ←
                        </button>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">
                                Activities in {destination}
                            </h1>
                            {vibes.length > 0 && (
                                <p className="text-xs text-gray-500 mt-0.5">
                                    Based on your vibe: {vibes.slice(0, 3).join(', ')}
                                </p>
                            )}
                        </div>
                        <div className="ml-auto text-right">
                            <div className="text-[10px] text-gray-400 uppercase tracking-wide">Step 1 of 4</div>
                        </div>
                    </div>

                    {/* Category tabs */}
                    <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide -mx-1 px-1">
                        <button
                            onClick={() => setActiveCategory('all')}
                            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all flex-shrink-0 ${activeCategory === 'all'
                                ? 'bg-gray-900 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            All ({allActivities.length})
                        </button>
                        {availableCategories.map(cat => (
                            <button
                                key={cat.id}
                                onClick={() => setActiveCategory(cat.id)}
                                className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all flex-shrink-0 ${activeCategory === cat.id
                                    ? 'text-white'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                                style={activeCategory === cat.id ? { backgroundColor: cat.color } : {}}
                            >
                                {cat.emoji} {cat.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="max-w-4xl mx-auto px-4 py-6">
                {/* Top Picks Section */}
                {activeCategory === 'all' && topPicks.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-lg">⭐</span>
                            <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wide">Top Picks For You</h2>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <AnimatePresence>
                                {topPicks.map(activity => (
                                    <ActivityCard
                                        key={activity.id}
                                        activity={activity}
                                        selected={selectedIds.has(activity.id)}
                                        onToggle={toggleActivity}
                                    />
                                ))}
                            </AnimatePresence>
                        </div>
                    </motion.section>
                )}

                {/* Category sections */}
                {groupedOthers.map(group => {
                    const catInfo = CATEGORIES.find(c => c.id === group.category) || {}
                    return (
                        <motion.section
                            key={group.category}
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-8"
                        >
                            {activeCategory === 'all' && (
                                <div className="flex items-center gap-2 mb-3">
                                    <span className="text-lg">{catInfo.emoji || '📌'}</span>
                                    <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wide">
                                        {catInfo.label || group.category}
                                    </h2>
                                </div>
                            )}
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                <AnimatePresence>
                                    {group.items.map(activity => (
                                        <ActivityCard
                                            key={activity.id}
                                            activity={activity}
                                            selected={selectedIds.has(activity.id)}
                                            onToggle={toggleActivity}
                                        />
                                    ))}
                                </AnimatePresence>
                            </div>
                        </motion.section>
                    )
                })}
            </div>

            {/* Sticky bottom bar */}
            <motion.div
                initial={{ y: 100 }}
                animate={{ y: 0 }}
                className="fixed bottom-0 left-0 right-0 z-40 bg-white/90 backdrop-blur-xl border-t border-gray-200 p-4"
            >
                <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
                    <div>
                        <p className="text-sm font-semibold text-gray-800">
                            {selectedIds.size} activit{selectedIds.size === 1 ? 'y' : 'ies'} selected
                        </p>
                        <p className="text-xs text-gray-500">
                            Est. ₹{estimatedCost.toLocaleString('en-IN')} for activities
                        </p>
                    </div>
                    <button
                        onClick={() => onComplete(selectedActivities)}
                        disabled={!canContinue}
                        className={`px-6 py-3 rounded-xl text-sm font-semibold transition-all ${canContinue
                            ? 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-200'
                            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            }`}
                    >
                        Continue → Choose Travel Style
                    </button>
                </div>
                {!canContinue && (
                    <p className="text-center text-xs text-gray-400 mt-2">Select at least 2 activities to continue</p>
                )}
            </motion.div>
        </div>
    )
}

import { useState, useCallback, useMemo, useEffect } from 'react'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import { motion } from 'framer-motion'
import BudgetBar from '../components/BudgetBar'
import { CATEGORIES } from '../data/activities'

/**
 * ItineraryEditor — Step 4: Drag-and-drop day-by-day itinerary editor.
 *
 * Props:
 *   itinerary     — { days: [...], pool: [...], hotel, flight }
 *   allActivities — full list of activities for this destination
 *   budget        — int, user budget
 *   destination   — string
 *   hotel         — { name, stars, price_night }
 *   flight        — { from, to, price, airline, duration }
 *   onConfirm     — () => void
 *   onBack        — () => void
 *   duration      — int, trip days
 */
export default function ItineraryEditor({
    itinerary: initialItinerary,
    allActivities = [],
    budget,
    destination,
    hotel,
    flight,
    onConfirm,
    onBack,
    duration = 4,
}) {
    const [days, setDays] = useState(initialItinerary?.days || [])
    const [pool, setPool] = useState(initialItinerary?.pool || [])
    const [poolFilter, setPoolFilter] = useState('all')

    // Calculate totals reactively
    const totals = useMemo(() => {
        const nights = Math.max(duration - 1, 1)
        const hotelCost = (hotel?.price_night || hotel?.price_per_night || 3000) * nights
        const flightCost = (flight?.price || 0) * 2 // Round trip
        const activityCost = days
            .flatMap(d => d.slots)
            .filter(s => s.activity && !s.locked)
            .reduce((sum, s) => sum + (s.activity?.cost || 0), 0)
        const subtotal = hotelCost + flightCost + activityCost
        const buffer = Math.round(subtotal * 0.1)
        return {
            hotel: hotelCost,
            flights: flightCost,
            activities: activityCost,
            buffer,
            grand_total: subtotal + buffer,
        }
    }, [days, hotel, flight, duration])

    // --- Drag and Drop logic ---
    const onDragEnd = useCallback((result) => {
        const { source, destination: dest, draggableId } = result
        if (!dest) return

        const sourceId = source.droppableId
        const destId = dest.droppableId

        // Moving within the same list
        if (sourceId === destId) {
            if (sourceId === 'pool') {
                // Reorder pool
                const newPool = [...pool]
                const [moved] = newPool.splice(source.index, 1)
                newPool.splice(dest.index, 0, moved)
                setPool(newPool)
            } else {
                // Reorder within a day
                const dayIdx = parseInt(sourceId.replace('day_', ''))
                setDays(prev => {
                    const newDays = [...prev]
                    const day = { ...newDays[dayIdx] }
                    const newSlots = [...day.slots]
                    const [moved] = newSlots.splice(source.index, 1)
                    newSlots.splice(dest.index, 0, moved)
                    day.slots = newSlots
                    newDays[dayIdx] = day
                    return newDays
                })
            }
            return
        }

        // Moving from pool to a day
        if (sourceId === 'pool') {
            const dayIdx = parseInt(destId.replace('day_', ''))
            const activity = pool[source.index]
            if (!activity) return

            setPool(prev => prev.filter((_, i) => i !== source.index))
            setDays(prev => {
                const newDays = [...prev]
                const day = { ...newDays[dayIdx] }
                const newSlots = [...day.slots]

                // Find the first empty slot or insert at destination index
                const emptyIdx = newSlots.findIndex(s => !s.activity && !s.locked)
                if (emptyIdx >= 0) {
                    newSlots[emptyIdx] = { ...newSlots[emptyIdx], activity }
                } else {
                    // Add a new slot
                    newSlots.splice(dest.index, 0, {
                        id: `slot_${dayIdx}_extra_${Date.now()}`,
                        time: 'afternoon',
                        activity,
                        locked: false,
                    })
                }
                day.slots = newSlots
                newDays[dayIdx] = day
                return newDays
            })
            return
        }

        // Moving from a day to pool
        if (destId === 'pool') {
            const dayIdx = parseInt(sourceId.replace('day_', ''))
            setDays(prev => {
                const newDays = [...prev]
                const day = { ...newDays[dayIdx] }
                const slot = day.slots[source.index]
                if (!slot || slot.locked) return prev

                const activity = slot.activity
                const newSlots = [...day.slots]
                newSlots[source.index] = { ...slot, activity: null }
                day.slots = newSlots
                newDays[dayIdx] = day

                if (activity) {
                    setPool(prev => [...prev, activity])
                }
                return newDays
            })
            return
        }

        // Moving between days
        const srcDayIdx = parseInt(sourceId.replace('day_', ''))
        const destDayIdx = parseInt(destId.replace('day_', ''))
        setDays(prev => {
            const newDays = [...prev]
            const srcDay = { ...newDays[srcDayIdx] }
            const dstDay = { ...newDays[destDayIdx] }
            const srcSlots = [...srcDay.slots]
            const dstSlots = [...dstDay.slots]

            const [srcSlot] = srcSlots.splice(source.index, 1)
            if (!srcSlot || srcSlot.locked) return prev

            // Put empty placeholder where it came from
            srcSlots.splice(source.index, 0, { ...srcSlot, activity: null })

            // Insert into destination
            const emptyIdx = dstSlots.findIndex(s => !s.activity && !s.locked)
            if (emptyIdx >= 0) {
                dstSlots[emptyIdx] = { ...dstSlots[emptyIdx], activity: srcSlot.activity }
            } else {
                dstSlots.splice(dest.index, 0, {
                    id: `slot_${destDayIdx}_moved_${Date.now()}`,
                    time: 'afternoon',
                    activity: srcSlot.activity,
                    locked: false,
                })
            }

            srcDay.slots = srcSlots
            dstDay.slots = dstSlots
            newDays[srcDayIdx] = srcDay
            newDays[destDayIdx] = dstDay
            return newDays
        })
    }, [pool])

    // Remove activity from timeline to pool
    const handleRemoveActivity = useCallback((activity, slotId) => {
        setDays(prev => {
            const newDays = prev.map(day => ({
                ...day,
                slots: day.slots.map(slot =>
                    slot.id === slotId ? { ...slot, activity: null } : slot
                ),
            }))
            return newDays
        })
        setPool(prev => [...prev, activity])
    }, [])

    // Filter pool
    const filteredPool = poolFilter === 'all'
        ? pool
        : pool.filter(a => a.category === poolFilter)

    const availablePoolCats = [...new Set(pool.map(a => a.category))]

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Top bar */}
            <div className="sticky top-0 z-30 bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button onClick={onBack} className="w-9 h-9 flex items-center justify-center rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors text-gray-600 text-sm">
                            ←
                        </button>
                        <div>
                            <h1 className="text-lg font-bold text-gray-900">Your {destination} Itinerary</h1>
                            <p className="text-[10px] text-gray-400 uppercase tracking-wide">Step 4 of 4 — Drag to customize</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm font-bold text-gray-800">
                            Total: ₹{totals.grand_total.toLocaleString('en-IN')}
                        </span>
                        <button
                            onClick={onConfirm}
                            className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-200 transition-all"
                        >
                            Book This Trip 🎉
                        </button>
                    </div>
                </div>
            </div>

            <DragDropContext onDragEnd={onDragEnd}>
                <div className="max-w-7xl mx-auto px-4 py-6">
                    <div className="flex gap-6">
                        {/* LEFT: Day-by-day timeline */}
                        <div className="flex-1 min-w-0">
                            <h2 className="text-sm font-bold text-gray-700 mb-4 uppercase tracking-wide">📋 The Plan</h2>

                            {days.map((day, dayIdx) => (
                                <Droppable key={`day_${dayIdx}`} droppableId={`day_${dayIdx}`}>
                                    {(provided, snapshot) => (
                                        <div className={`mb-6 p-4 rounded-2xl transition-colors ${snapshot.isDraggingOver ? 'bg-emerald-50 border-2 border-emerald-200' : 'bg-white border border-gray-200'
                                            }`}>
                                            {/* Day header */}
                                            <div className="flex items-center gap-2 mb-3">
                                                <div className="w-8 h-8 rounded-lg bg-gray-900 text-white flex items-center justify-center text-sm font-bold">
                                                    {day.day}
                                                </div>
                                                <div>
                                                    <h3 className="text-sm font-bold text-gray-800">{day.label}</h3>
                                                    <p className="text-[10px] text-gray-400">
                                                        {day.slots.filter(s => s.activity).length} activities · {
                                                            day.slots
                                                                .filter(s => s.activity)
                                                                .reduce((sum, s) => sum + (s.activity?.duration_hrs || 0), 0)
                                                        }hrs planned
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Droppable slots */}
                                            <div
                                                ref={provided.innerRef}
                                                {...provided.droppableProps}
                                                className="space-y-2 min-h-[60px]"
                                            >
                                                {day.slots.map((slot, slotIdx) => (
                                                    <Draggable
                                                        key={slot.id}
                                                        draggableId={slot.id}
                                                        index={slotIdx}
                                                        isDragDisabled={slot.locked || !slot.activity}
                                                    >
                                                        {(dragProvided, dragSnapshot) => (
                                                            <div
                                                                ref={dragProvided.innerRef}
                                                                {...dragProvided.draggableProps}
                                                                {...dragProvided.dragHandleProps}
                                                                className={`transition-transform ${dragSnapshot.isDragging ? 'rotate-1 shadow-xl scale-105 z-50' : ''
                                                                    }`}
                                                            >
                                                                {slot.activity ? (
                                                                    <div className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${slot.locked
                                                                        ? 'bg-gray-50 border-gray-200 opacity-70'
                                                                        : 'bg-white border-gray-200 hover:shadow-md cursor-grab active:cursor-grabbing'
                                                                        }`}>
                                                                        {!slot.locked && <span className="text-gray-300 text-sm select-none">⠿</span>}
                                                                        {slot.locked && <span className="text-gray-400 text-sm">🔒</span>}
                                                                        <span className="text-xl flex-shrink-0">{slot.activity.emoji}</span>
                                                                        <div className="flex-1 min-w-0">
                                                                            <p className="text-sm font-semibold text-gray-800 truncate">{slot.activity.name}</p>
                                                                            <div className="flex items-center gap-2 mt-0.5">
                                                                                <span className="text-xs text-gray-500">{slot.activity.duration_hrs}hrs</span>
                                                                                <span className="text-xs text-gray-400">•</span>
                                                                                <span className="text-xs font-medium text-gray-600">₹{slot.activity.cost.toLocaleString('en-IN')}</span>
                                                                            </div>
                                                                        </div>
                                                                        {!slot.locked && (
                                                                            <button
                                                                                onClick={(e) => { e.stopPropagation(); handleRemoveActivity(slot.activity, slot.id) }}
                                                                                className="w-6 h-6 flex items-center justify-center rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors text-sm"
                                                                            >
                                                                                ✕
                                                                            </button>
                                                                        )}
                                                                    </div>
                                                                ) : (
                                                                    <div className="flex items-center justify-center h-14 rounded-xl border-2 border-dashed border-gray-200 text-xs text-gray-400">
                                                                        Drop activity here · {slot.time}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}
                                                    </Draggable>
                                                ))}
                                                {provided.placeholder}
                                            </div>
                                        </div>
                                    )}
                                </Droppable>
                            ))}
                        </div>

                        {/* RIGHT: Activity Pool */}
                        <div className="w-80 flex-shrink-0">
                            <div className="sticky top-20">
                                <h2 className="text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide">
                                    ➕ Add Activities ({pool.length})
                                </h2>

                                {/* Pool category filters */}
                                <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1 scrollbar-hide">
                                    <button
                                        onClick={() => setPoolFilter('all')}
                                        className={`px-2.5 py-1 rounded-full text-[10px] font-medium whitespace-nowrap transition-all ${poolFilter === 'all' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                            }`}
                                    >
                                        All
                                    </button>
                                    {CATEGORIES.filter(c => availablePoolCats.includes(c.id)).map(cat => (
                                        <button
                                            key={cat.id}
                                            onClick={() => setPoolFilter(cat.id)}
                                            className={`px-2.5 py-1 rounded-full text-[10px] font-medium whitespace-nowrap transition-all ${poolFilter === cat.id ? 'text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                                }`}
                                            style={poolFilter === cat.id ? { backgroundColor: cat.color } : {}}
                                        >
                                            {cat.emoji} {cat.label}
                                        </button>
                                    ))}
                                </div>

                                <Droppable droppableId="pool">
                                    {(provided, snapshot) => (
                                        <div
                                            ref={provided.innerRef}
                                            {...provided.droppableProps}
                                            className={`space-y-2 min-h-[200px] p-3 rounded-2xl transition-colors ${snapshot.isDraggingOver ? 'bg-amber-50 border-2 border-amber-200' : 'bg-white border border-gray-200'
                                                }`}
                                        >
                                            {filteredPool.map((activity, index) => (
                                                <Draggable key={`pool_${activity.id}`} draggableId={`pool_${activity.id}`} index={index}>
                                                    {(dragProvided, dragSnapshot) => (
                                                        <div
                                                            ref={dragProvided.innerRef}
                                                            {...dragProvided.draggableProps}
                                                            {...dragProvided.dragHandleProps}
                                                            className={`flex items-center gap-3 p-3 rounded-xl bg-white border border-gray-200 cursor-grab active:cursor-grabbing hover:shadow-md transition-all ${dragSnapshot.isDragging ? 'rotate-2 shadow-xl scale-105' : ''
                                                                }`}
                                                        >
                                                            <span className="text-gray-300 text-sm select-none">⠿</span>
                                                            <span className="text-xl flex-shrink-0">{activity.emoji}</span>
                                                            <div className="flex-1 min-w-0">
                                                                <p className="text-sm font-semibold text-gray-800 truncate">{activity.name}</p>
                                                                <div className="flex items-center gap-2 mt-0.5">
                                                                    <span className="text-xs text-gray-500">{activity.duration_hrs}hrs</span>
                                                                    <span className="text-xs text-gray-400">•</span>
                                                                    <span className="text-xs font-medium text-gray-600">₹{activity.cost.toLocaleString('en-IN')}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </Draggable>
                                            ))}
                                            {provided.placeholder}

                                            {filteredPool.length === 0 && (
                                                <div className="flex items-center justify-center h-24 text-xs text-gray-400">
                                                    {pool.length === 0 ? 'All activities are in your plan!' : 'No activities in this category'}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </Droppable>
                            </div>
                        </div>
                    </div>
                </div>
            </DragDropContext>

            {/* Sticky budget bar */}
            <div className="fixed bottom-0 left-0 right-0 z-40 bg-white/90 backdrop-blur-xl border-t border-gray-200 p-4">
                <div className="max-w-7xl mx-auto">
                    <BudgetBar totals={totals} budget={budget} />
                </div>
            </div>
        </div>
    )
}

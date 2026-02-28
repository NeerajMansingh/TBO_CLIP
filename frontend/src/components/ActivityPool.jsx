import { useState } from 'react'
import { Draggable } from '@hello-pangea/dnd'
import { CATEGORIES } from '../data/activities'

/**
 * ActivityPool — Right panel in ItineraryEditor showing unassigned activities.
 *
 * Props:
 *   activities — array of unassigned activity objects
 *   provided   — droppable provided (from parent Droppable)
 */
export default function ActivityPool({ activities, provided }) {
    const [filter, setFilter] = useState('all')

    const filtered = filter === 'all'
        ? activities
        : activities.filter(a => a.category === filter)

    const availableCats = [...new Set(activities.map(a => a.category))]

    return (
        <div>
            <h3 className="text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide">
                Add More Activities ({activities.length})
            </h3>

            {/* Category filters */}
            <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1 scrollbar-hide">
                <button
                    onClick={() => setFilter('all')}
                    className={`px-2.5 py-1 rounded-full text-[10px] font-medium whitespace-nowrap transition-all ${filter === 'all' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                >
                    All
                </button>
                {CATEGORIES.filter(c => availableCats.includes(c.id)).map(cat => (
                    <button
                        key={cat.id}
                        onClick={() => setFilter(cat.id)}
                        className={`px-2.5 py-1 rounded-full text-[10px] font-medium whitespace-nowrap transition-all ${filter === cat.id ? 'text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                        style={filter === cat.id ? { backgroundColor: cat.color } : {}}
                    >
                        {cat.emoji} {cat.label}
                    </button>
                ))}
            </div>

            {/* Draggable activity list */}
            <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="space-y-2 min-h-[200px]"
            >
                {filtered.map((activity, index) => (
                    <Draggable key={activity.id} draggableId={`pool_${activity.id}`} index={index}>
                        {(dragProvided, dragSnapshot) => (
                            <div
                                ref={dragProvided.innerRef}
                                {...dragProvided.draggableProps}
                                {...dragProvided.dragHandleProps}
                                className={`transition-transform ${dragSnapshot.isDragging ? 'rotate-2 shadow-xl z-50' : ''}`}
                            >
                                <div className="flex items-center gap-3 p-3 rounded-xl bg-white border border-gray-200 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow">
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
                            </div>
                        )}
                    </Draggable>
                ))}
                {provided.placeholder}

                {filtered.length === 0 && (
                    <div className="flex items-center justify-center h-24 text-xs text-gray-400">
                        No activities available
                    </div>
                )}
            </div>
        </div>
    )
}

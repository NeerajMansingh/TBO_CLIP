import { Draggable } from '@hello-pangea/dnd'
import ActivityCard from './ActivityCard'

/**
 * DayTimeline — A single day column in the ItineraryEditor.
 * 
 * Props:
 *   day          — { day: int, label: string, slots: [...] }
 *   provided     — droppable provided (from parent Droppable)
 *   onRemoveActivity — (activity, slotId) => void
 */
export default function DayTimeline({ day, provided, onRemoveActivity }) {
    return (
        <div className="mb-6">
            {/* Day header */}
            <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 rounded-lg bg-gray-900 text-white flex items-center justify-center text-sm font-bold">
                    {day.day}
                </div>
                <div>
                    <h3 className="text-sm font-bold text-gray-800">{day.label}</h3>
                    <p className="text-[10px] text-gray-400">
                        {day.slots.filter(s => s.activity).length} activities · {day.slots.filter(s => s.activity).reduce((sum, s) => sum + (s.activity?.duration_hrs || 0), 0)}hrs planned
                    </p>
                </div>
            </div>

            {/* Slots */}
            <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="space-y-2 min-h-[100px] p-2 rounded-xl bg-gray-50/50 border border-dashed border-gray-200"
            >
                {day.slots.map((slot, index) => (
                    <div key={slot.id}>
                        {slot.activity ? (
                            <Draggable
                                draggableId={slot.id}
                                index={index}
                                isDragDisabled={slot.locked}
                            >
                                {(dragProvided, dragSnapshot) => (
                                    <div
                                        ref={dragProvided.innerRef}
                                        {...dragProvided.draggableProps}
                                        {...dragProvided.dragHandleProps}
                                        className={`transition-transform ${dragSnapshot.isDragging ? 'rotate-2 shadow-xl' : ''}`}
                                    >
                                        <ActivityCard
                                            activity={slot.activity}
                                            compact
                                            draggable={!slot.locked}
                                            locked={slot.locked}
                                            onRemove={slot.locked ? undefined : (act) => onRemoveActivity(act, slot.id)}
                                        />
                                    </div>
                                )}
                            </Draggable>
                        ) : (
                            <Draggable draggableId={slot.id} index={index} isDragDisabled>
                                {(dragProvided) => (
                                    <div
                                        ref={dragProvided.innerRef}
                                        {...dragProvided.draggableProps}
                                        {...dragProvided.dragHandleProps}
                                        className="flex items-center justify-center h-14 rounded-xl border-2 border-dashed border-gray-200 text-xs text-gray-400"
                                    >
                                        Drop activity here · {slot.time}
                                    </div>
                                )}
                            </Draggable>
                        )}
                    </div>
                ))}
                {provided.placeholder}
            </div>
        </div>
    )
}

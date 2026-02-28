import { motion } from 'framer-motion'

/**
 * BudgetBar — Sticky bottom bar showing cost breakdown with progress bar.
 *
 * Props:
 *   totals  — { hotel, activities, flights, buffer, grand_total }
 *   budget  — user's total budget
 *   compact — if true, show single-line version
 */
export default function BudgetBar({ totals, budget, compact = false }) {
    const { hotel = 0, activities = 0, flights = 0, buffer = 0, grand_total = 0 } = totals
    const percent = budget > 0 ? Math.round((grand_total / budget) * 100) : 0
    const overBudget = grand_total > budget

    const barColor = overBudget
        ? 'bg-red-500'
        : percent >= 85
            ? 'bg-amber-500'
            : 'bg-emerald-500'

    const bgColor = overBudget
        ? 'bg-red-50 border-red-200'
        : percent >= 85
            ? 'bg-amber-50 border-amber-200'
            : 'bg-white border-gray-200'

    if (compact) {
        return (
            <div className={`flex items-center gap-3 p-3 rounded-xl border ${bgColor}`}>
                <div className="flex-1">
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <motion.div
                            className={`h-full rounded-full ${barColor}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(percent, 100)}%` }}
                            transition={{ duration: 0.4, ease: 'easeOut' }}
                        />
                    </div>
                </div>
                <span className="text-sm font-semibold text-gray-700 whitespace-nowrap">
                    ₹{grand_total.toLocaleString('en-IN')}
                    <span className="text-gray-400 font-normal"> / ₹{budget.toLocaleString('en-IN')}</span>
                </span>
            </div>
        )
    }

    return (
        <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className={`p-4 rounded-2xl border ${bgColor}`}
        >
            {/* Progress bar */}
            <div className="mb-3">
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                        className={`h-full rounded-full ${barColor}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(percent, 100)}%` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                </div>
                <div className="flex justify-between items-center mt-1.5">
                    <span className={`text-xs font-medium ${overBudget ? 'text-red-600' : 'text-gray-500'}`}>
                        {percent}% of ₹{budget.toLocaleString('en-IN')} budget
                    </span>
                    {overBudget && (
                        <span className="text-xs font-semibold text-red-600 flex items-center gap-1">
                            ⚠️ Over budget by ₹{(grand_total - budget).toLocaleString('en-IN')}
                        </span>
                    )}
                </div>
            </div>

            {/* Breakdown */}
            <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
                {hotel > 0 && (
                    <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-blue-400" />
                        Hotel ₹{hotel.toLocaleString('en-IN')}
                    </span>
                )}
                {flights > 0 && (
                    <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-violet-400" />
                        Flights ₹{flights.toLocaleString('en-IN')}
                    </span>
                )}
                {activities > 0 && (
                    <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                        Activities ₹{activities.toLocaleString('en-IN')}
                    </span>
                )}
                {buffer > 0 && (
                    <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-gray-300" />
                        Buffer ₹{buffer.toLocaleString('en-IN')}
                    </span>
                )}
                <span className="ml-auto font-bold text-sm text-gray-800">
                    Total: ₹{grand_total.toLocaleString('en-IN')}
                </span>
            </div>
        </motion.div>
    )
}

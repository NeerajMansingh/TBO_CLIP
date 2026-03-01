import React from 'react';
import { motion } from 'framer-motion';

export default function PackagePresentation({ packages, itinerary, onBack, onSelect }) {
    // Framer Motion Animation Variants
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.12 }
        }
    };

    const cardVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { type: "spring", stiffness: 80, damping: 14 }
        }
    };

    return (
        // 1. CHANGED: Swapped bg-gray-100 for bg-slate-100 (a cooler, richer backdrop that contrasts better with pure white)
        <div className="relative min-h-screen bg-slate-100 pb-32 text-slate-900 font-sans selection:bg-indigo-500/30 overflow-hidden">

            {/* Decorative Background Ambient Glows - Slightly increased opacity for better background texture */}
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
            <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

            {/* Sleek Minimal Header */}
            <nav className="fixed top-0 inset-x-0 z-40 bg-white/70 backdrop-blur-2xl border-b border-slate-200 shadow-sm transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <button onClick={onBack} className="group flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                        <span className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </span>
                        Back to Activities
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-indigo-500 animate-[pulse_2s_ease-in-out_infinite]"></div>
                        <span className="text-xs font-bold uppercase tracking-widest text-indigo-600">Step 3: Trajectory</span>
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto pt-32 px-6 relative z-10">

                {/* Header Section */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7, ease: "easeOut" }}
                    className="max-w-2xl mb-20"
                >
                    <h1 className="text-5xl md:text-[3.5rem] font-black text-slate-900 mb-6 tracking-tight leading-[1.1]">
                        Your generated <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 bg-300% animate-gradient">trajectories.</span>
                    </h1>
                    <p className="text-lg text-slate-600 leading-relaxed font-normal">
                        We've synthesized your activity selections with three distinct accommodation philosophies. Select the footprint that fits your journey.
                    </p>
                </motion.div>

                {/* Grid Container */}
                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 items-center"
                >
                    {packages.map((pkg) => {
                        const isRec = pkg.id === "balanced";

                        return (
                            <motion.div
                                variants={cardVariants}
                                key={pkg.id}
                                className="relative z-10 hover:z-50 h-full"
                            >
                                {/* 2. CHANGED: Massively upgraded the baseline shadows (shadow-xl shadow-slate-300/70) so cards heavily detach from the background even before hover */}
                                <div className={`relative w-full h-full rounded-[28px] transition-all duration-300 ease-out flex flex-col group transform-gpu ${isRec
                                        ? 'lg:-translate-y-4 scale-[1.04] hover:scale-[1.10] hover:-translate-y-8 shadow-[0_20px_50px_-12px_rgba(99,102,241,0.4)] hover:shadow-[0_40px_80px_-10px_rgba(99,102,241,0.6)] bg-white ring-2 ring-indigo-500/50'
                                        : 'scale-100 hover:scale-[1.06] hover:-translate-y-4 border border-slate-200 shadow-xl shadow-slate-300/70 hover:shadow-2xl hover:shadow-slate-400/80 hover:border-slate-300 bg-white'
                                    }`}>

                                    {/* Floating Premium Badge */}
                                    {isRec && (
                                        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full shadow-lg shadow-indigo-500/40">
                                            <svg className="w-3.5 h-3.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                            </svg>
                                            <span className="text-[10px] font-black uppercase tracking-widest text-white">Algorithm Pick</span>
                                        </div>
                                    )}

                                    <div className="h-full w-full rounded-[27px] flex flex-col overflow-hidden relative bg-white">

                                        <div className="px-8 pt-10 pb-8 flex-1 flex flex-col relative z-10">

                                            <h3 className="text-2xl font-black text-slate-900 tracking-tight leading-none mb-3">{pkg.tier}</h3>
                                            <p className="text-slate-600 text-sm leading-relaxed mb-6 h-10 line-clamp-2 pr-4">{pkg.description}</p>

                                            {/* Stylized Price */}
                                            <div className="mb-8 flex items-baseline gap-1.5 border-b border-slate-200 pb-6">
                                                <span className={`text-[2.75rem] font-black tracking-tighter transition-colors duration-300 ${isRec ? 'text-transparent bg-clip-text bg-gradient-to-br from-slate-900 to-indigo-900 group-hover:from-indigo-600 group-hover:to-purple-600' : 'text-slate-900 group-hover:text-indigo-600'}`}>
                                                    ₹{Math.round(pkg.total_price || 0).toLocaleString()}
                                                </span>
                                                <span className="text-slate-500 font-bold text-sm">/pp</span>
                                            </div>

                                            <div className="space-y-4 flex-grow mb-10">
                                                {/* Feature 1 */}
                                                <div className="flex items-center gap-3.5 group/item cursor-default">
                                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-transform group-hover/item:scale-110 ${isRec ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1v1H9V7zm5 0h1v1h-1V7zm-5 4h1v1H9v-1zm5 0h1v1h-1v-1zm-3 4H2v3h10v-3z" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className={`font-bold text-sm ${isRec ? 'text-slate-900' : 'text-slate-800'}`}>{pkg.hotel_rating}</span>
                                                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Accommodation</span>
                                                    </div>
                                                </div>

                                                {/* Feature 2 */}
                                                <div className="flex items-center gap-3.5 group/item cursor-default">
                                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-transform group-hover/item:scale-110 ${isRec ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className={`font-bold text-sm ${isRec ? 'text-slate-900' : 'text-slate-800'}`}>Included</span>
                                                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">TBO Flight Feeds</span>
                                                    </div>
                                                </div>

                                                {/* Feature 3 */}
                                                <div className="flex items-center gap-3.5 group/item cursor-default">
                                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-transform group-hover/item:scale-110 ${isRec ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className={`font-bold text-sm ${isRec ? 'text-slate-900' : 'text-slate-800'}`}>Included</span>
                                                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Selected Activities</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Refined CTA Buttons */}
                                            <button
                                                onClick={() => onSelect(pkg)}
                                                className={`w-full py-4 rounded-[14px] font-bold transition-all duration-300 flex items-center justify-center gap-2 group/btn text-sm ${isRec
                                                    ? 'bg-slate-900 text-white hover:bg-black shadow-lg shadow-slate-900/30 hover:shadow-xl hover:shadow-slate-900/40 hover:-translate-y-0.5'
                                                    : 'bg-transparent text-slate-700 border-2 border-slate-200 group-hover:border-indigo-600 group-hover:text-indigo-600 hover:bg-indigo-50'
                                                    }`}
                                            >
                                                Inspect Breakdown
                                                <svg className={`w-4 h-4 transition-transform duration-300 ${isRec ? 'group-hover/btn:translate-x-1.5' : 'opacity-0 -translate-x-2 group-hover/btn:opacity-100 group-hover/btn:translate-x-0'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                                </svg>
                                            </button>

                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </motion.div>
            </div>
        </div>
    );
}
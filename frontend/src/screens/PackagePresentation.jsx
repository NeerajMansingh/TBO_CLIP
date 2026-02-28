export default function PackagePresentation({ packages, itinerary, onBack, onSelect }) {
    return (
        <div className="min-h-screen bg-[#0F1115] pb-32 text-gray-100 font-sans selection:bg-indigo-500/30">

            {/* Sleek Minimal Header - Dark Mode */}
            <nav className="fixed top-0 inset-x-0 z-40 bg-[#0F1115]/80 backdrop-blur-xl border-b border-white/5 shadow-sm transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <button onClick={onBack} className="group flex items-center gap-2 text-sm font-medium text-gray-400 hover:text-white transition-colors">
                        <span className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </span>
                        Back to Activities
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
                        <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Step 3: Trajectory</span>
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto pt-32 px-6">

                {/* Dynamic Header Section */}
                <div className="text-center mb-24 relative">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-600/20 blur-[120px] rounded-full pointer-events-none"></div>
                    <h1 className="text-5xl md:text-7xl font-black text-white mb-6 tracking-tight leading-tight relative z-10">
                        Your generated <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-fuchsia-500">trajectories.</span>
                    </h1>
                    <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed relative z-10">
                        We've synthesized your activity selections with three distinct accommodation philosophies. Select the footprint that fits your journey.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-end">
                    {packages.map((pkg) => {
                        const isRec = pkg.id === "balanced";

                        return (
                            <div
                                key={pkg.id}
                                className={`relative rounded-3xl p-[1px] transform transition-all duration-500 outline-none flex flex-col group ${isRec
                                        ? 'bg-gradient-to-b from-indigo-500 to-indigo-900 shadow-[0_0_80px_-15px_rgba(99,102,241,0.4)] md:-translate-y-8 z-10'
                                        : 'bg-white/10 hover:bg-white/20 hover:-translate-y-2'
                                    }`}
                            >
                                <div className={`h-full w-full rounded-[23px] flex flex-col overflow-hidden relative ${isRec ? 'bg-[#151822]' : 'bg-[#12141A]'
                                    }`}>

                                    {/* Recommended Glow & Tab */}
                                    {isRec && (
                                        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400"></div>
                                    )}

                                    <div className="px-8 pt-10 pb-8 flex-1 flex flex-col relative z-10">

                                        {isRec && (
                                            <div className="text-indigo-400 text-xs font-extrabold uppercase tracking-widest mb-4 flex items-center gap-2">
                                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                                </svg>
                                                Algorithm Pick
                                            </div>
                                        )}

                                        <h3 className="text-3xl font-black text-white tracking-tight leading-none mb-3">{pkg.tier}</h3>
                                        <p className="text-gray-400 text-sm leading-relaxed mb-8 h-12 line-clamp-2">{pkg.description}</p>

                                        <div className="mb-10 flex items-baseline gap-1 border-b border-white/10 pb-8">
                                            <span className="text-5xl font-black text-white tracking-tighter">₹{Math.round(pkg.total_price).toLocaleString()}</span>
                                            <span className="text-gray-500 font-medium">/pp</span>
                                        </div>

                                        <div className="space-y-6 flex-grow mb-10">

                                            <div className="group/item flex items-start gap-4 transition-colors">
                                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border transition-colors ${isRec ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' : 'bg-white/5 border-white/5 text-gray-400 group-hover/item:text-white'}`}>
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1v1H9V7zm5 0h1v1h-1V7zm-5 4h1v1H9v-1zm5 0h1v1h-1v-1zm-3 4H2v3h10v-3z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className={`font-bold transition-colors ${isRec ? 'text-indigo-100' : 'text-gray-300'}`}>{pkg.hotel_rating}</p>
                                                    <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider font-semibold">Accommodation Baseline</p>
                                                </div>
                                            </div>

                                            <div className="group/item flex items-start gap-4 transition-colors">
                                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border transition-colors ${isRec ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' : 'bg-white/5 border-white/5 text-gray-400 group-hover/item:text-white'}`}>
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className={`font-bold transition-colors ${isRec ? 'text-indigo-100' : 'text-gray-300'}`}>Included</p>
                                                    <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider font-semibold">TBO Flight Feeds</p>
                                                </div>
                                            </div>

                                            <div className="group/item flex items-start gap-4 transition-colors">
                                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border transition-colors ${isRec ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' : 'bg-white/5 border-white/5 text-gray-400 group-hover/item:text-white'}`}>
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className={`font-bold transition-colors ${isRec ? 'text-indigo-100' : 'text-gray-300'}`}>Included</p>
                                                    <p className="text-xs text-gray-500 mt-1 uppercase tracking-wider font-semibold">Your Selected Activities</p>
                                                </div>
                                            </div>

                                        </div>

                                        <button
                                            onClick={() => onSelect(pkg)}
                                            className={`w-full py-4 rounded-xl font-bold transition-all flex items-center justify-center gap-2 group/btn ${isRec
                                                    ? 'bg-indigo-500 text-white hover:bg-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:shadow-[0_0_30px_rgba(99,102,241,0.6)]'
                                                    : 'bg-white/5 text-white border border-white/10 hover:bg-white/10 hover:border-white/20'
                                                }`}
                                        >
                                            Inspect Breakdown
                                            <svg className={`w-4 h-4 transition-transform ${isRec ? 'group-hover/btn:translate-x-1' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                            </svg>
                                        </button>

                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

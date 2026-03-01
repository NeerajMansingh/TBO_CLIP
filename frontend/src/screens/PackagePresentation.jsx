export default function PackagePresentation({ packages, itinerary, onBack, onSelect }) {
    return (
        <div className="min-h-screen bg-[#F9FAFB] pb-32 text-gray-900 font-sans selection:bg-indigo-500/30">

            {/* Sleek Minimal Header - Light Mode to match ActivitySelector */}
            <nav className="fixed top-0 inset-x-0 z-40 bg-white/70 backdrop-blur-xl border-b border-gray-200/50 shadow-sm transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <button onClick={onBack} className="group flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
                        <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </span>
                        Back to Activities
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
                        <span className="text-xs font-bold uppercase tracking-widest text-indigo-500">Step 3: Trajectory</span>
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto pt-32 px-6">

                {/* Header Section */}
                <div className="max-w-2xl mb-16">
                    <h1 className="text-5xl md:text-6xl font-black text-gray-900 mb-6 tracking-tight leading-[1.1]">
                        Your generated <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600">trajectories.</span>
                    </h1>
                    <p className="text-xl text-gray-500 leading-relaxed font-light">
                        We've synthesized your activity selections with three distinct accommodation philosophies. Select the footprint that fits your journey.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                    {packages.map((pkg) => {
                        const isRec = pkg.id === "balanced";

                        return (
                            <div
                                key={pkg.id}
                                className={`relative rounded-2xl transition-all duration-500 outline-none flex flex-col group ${isRec
                                    ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-[#F9FAFB] shadow-[0_8px_30px_-10px_rgba(99,102,241,0.25)] md:-translate-y-4 z-10'
                                    : 'border border-gray-200 hover:border-gray-300 hover:shadow-[0_8px_30px_-10px_rgba(0,0,0,0.08)] hover:-translate-y-1'
                                    }`}
                            >
                                <div className={`h-full w-full rounded-[14px] flex flex-col overflow-hidden relative bg-white`}>

                                    {/* Recommended accent bar */}
                                    {isRec && (
                                        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400 rounded-t-[14px]"></div>
                                    )}

                                    <div className="px-7 pt-8 pb-7 flex-1 flex flex-col relative z-10">

                                        {isRec && (
                                            <div className="text-indigo-500 text-xs font-extrabold uppercase tracking-widest mb-4 flex items-center gap-2">
                                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                                </svg>
                                                Algorithm Pick
                                            </div>
                                        )}

                                        <h3 className="text-2xl font-black text-gray-900 tracking-tight leading-none mb-2">{pkg.tier}</h3>
                                        <p className="text-gray-500 text-sm leading-relaxed mb-6 h-10 line-clamp-2">{pkg.description}</p>

                                        <div className="mb-8 flex items-baseline gap-1 border-b border-gray-200 pb-6">
                                            <span className="text-4xl font-black text-gray-900 tracking-tighter">₹{Math.round(pkg.total_price).toLocaleString()}</span>
                                            <span className="text-gray-400 font-medium text-sm">/pp</span>
                                        </div>

                                        <div className="space-y-5 flex-grow mb-8">

                                            <div className="flex items-start gap-3">
                                                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors ${isRec ? 'bg-indigo-50 text-indigo-500' : 'bg-gray-100 text-gray-500'}`}>
                                                    <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1v1H9V7zm5 0h1v1h-1V7zm-5 4h1v1H9v-1zm5 0h1v1h-1v-1zm-3 4H2v3h10v-3z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className="font-bold text-gray-900 text-sm">{pkg.hotel_rating}</p>
                                                    <p className="text-xs text-gray-400 mt-0.5 uppercase tracking-wider font-semibold">Accommodation Baseline</p>
                                                </div>
                                            </div>

                                            <div className="flex items-start gap-3">
                                                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors ${isRec ? 'bg-indigo-50 text-indigo-500' : 'bg-gray-100 text-gray-500'}`}>
                                                    <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className="font-bold text-gray-900 text-sm">Included</p>
                                                    <p className="text-xs text-gray-400 mt-0.5 uppercase tracking-wider font-semibold">TBO Flight Feeds</p>
                                                </div>
                                            </div>

                                            <div className="flex items-start gap-3">
                                                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors ${isRec ? 'bg-indigo-50 text-indigo-500' : 'bg-gray-100 text-gray-500'}`}>
                                                    <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className="font-bold text-gray-900 text-sm">Included</p>
                                                    <p className="text-xs text-gray-400 mt-0.5 uppercase tracking-wider font-semibold">Your Selected Activities</p>
                                                </div>
                                            </div>

                                        </div>

                                        <button
                                            onClick={() => onSelect(pkg)}
                                            className={`w-full py-3.5 rounded-xl font-bold transition-all flex items-center justify-center gap-2 group/btn text-sm ${isRec
                                                ? 'bg-gray-900 text-white hover:bg-black shadow-lg shadow-gray-900/20'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200'
                                                }`}
                                        >
                                            Inspect Breakdown
                                            <svg className={`w-4 h-4 transition-transform group-hover/btn:translate-x-1`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
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

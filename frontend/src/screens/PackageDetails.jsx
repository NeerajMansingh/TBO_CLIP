import { useState, useEffect, useRef } from "react";

export default function PackageDetails({ pkg, itinerary, initialSelectedActivities, sessionId, apiBase, onBack, onConfirm }) {
    const [selectedActivities, setSelectedActivities] = useState(initialSelectedActivities || {});
    const [activitiesByStop, setActivitiesByStop] = useState({});
    const [loading, setLoading] = useState(true);

    const [currentPkg, setCurrentPkg] = useState(pkg);

    // Track which act's swap menu is open: { stopId, actId }
    const [activeSwapMenu, setActiveSwapMenu] = useState(null);

    useEffect(() => {
        const fetchActivities = async () => {
            setLoading(true);
            const acts = {};
            for (const stop of itinerary.stops) {
                try {
                    const res = await fetch(`${apiBase}/activities/${stop.tbo_id}`);
                    if (res.ok) {
                        const data = await res.json();
                        acts[stop.tbo_id] = data.activities || [];
                    }
                } catch (e) {
                    console.error("Failed fetching activities", e);
                }
            }
            setActivitiesByStop(acts);
            setLoading(false);
        };
        fetchActivities();
    }, [itinerary, apiBase]);

    // Handle swapping out 'oldActId' for 'newActId' at 'stopId'
    const handleSwapActivity = (stopId, oldActId, newAct) => {
        // 1. Update selection state
        setSelectedActivities(prev => {
            const stopActs = prev[stopId] || [];
            const newStopActs = stopActs.filter(id => id !== oldActId);
            newStopActs.push(newAct.id);
            return { ...prev, [stopId]: newStopActs };
        });

        // 2. Find old activity price to deduct
        const oldAct = (activitiesByStop[stopId] || []).find(a => a.id === oldActId);
        const oldPrice = oldAct ? oldAct.price : 0;
        const newPrice = newAct.price;
        const priceDiff = newPrice - oldPrice;

        // 3. Update local package costs
        setCurrentPkg(prev => ({
            ...prev,
            activities_cost: prev.activities_cost + priceDiff,
            total_price: prev.total_price + priceDiff
        }));

        // 4. Close menu
        setActiveSwapMenu(null);
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#0A0C10]">
                <div className="flex flex-col items-center gap-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-[3px] border-indigo-200 border-t-indigo-500"></div>
                    <p className="text-sm font-medium text-indigo-400 tracking-wide uppercase">Assembling Timeline...</p>
                </div>
            </div>
        );
    }

    const allSelectedCount = Object.values(selectedActivities).flat().length;

    return (
        <div className="min-h-screen bg-[#0A0C10] pb-32 font-sans text-gray-100 selection:bg-indigo-500/30">

            {/* Sleek Minimal Header */}
            <nav className="fixed top-0 inset-x-0 z-50 bg-[#0A0C10]/80 backdrop-blur-xl border-b border-white/5 shadow-sm transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <button onClick={onBack} className="group flex items-center gap-2 text-sm font-medium text-gray-400 hover:text-white transition-colors">
                        <span className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </span>
                        Back to Options
                    </button>

                    <button
                        onClick={onConfirm}
                        className="bg-indigo-500 text-white px-6 py-2 rounded-full font-bold hover:bg-indigo-400 transition-all text-sm shadow-[0_0_15px_rgba(99,102,241,0.3)] hover:shadow-[0_0_25px_rgba(99,102,241,0.5)] flex items-center gap-2"
                    >
                        Confirm & Book
                        <span className="bg-white/20 px-2 py-0.5 rounded text-xs">₹{currentPkg.total_price.toLocaleString()}</span>
                    </button>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto pt-32 px-6 grid grid-cols-1 lg:grid-cols-12 gap-16 relative">

                {/* Left Column: The Immersive Interactive Timeline */}
                <div className="lg:col-span-7">
                    <div className="mb-12">
                        <span className="text-indigo-400 text-xs font-bold uppercase tracking-widest mb-2 block">
                            Interactive Itinerary
                        </span>
                        <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight leading-tight">
                            Your Complete <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-fuchsia-500">Journey Map.</span>
                        </h1>
                    </div>

                    <div className="relative pl-8 md:pl-12 pb-12">
                        {/* The vertical connective line */}
                        <div className="absolute top-8 bottom-0 left-[23px] md:left-[39px] w-[3px] bg-gradient-to-b from-indigo-500/50 via-purple-500/30 to-transparent rounded-full shadow-[0_0_15px_rgba(99,102,241,0.5)]"></div>

                        {/* Render each stop */}
                        {(() => {
                            let globalDayCounter = 1;

                            return itinerary.stops.map((stop, index) => {
                                const stopActsAll = activitiesByStop[stop.tbo_id] || [];
                                const stopSelectedIds = selectedActivities[stop.tbo_id] || [];
                                const stopSelectedActs = stopSelectedIds.map(id => stopActsAll.find(a => a.id === id)).filter(Boolean);

                                const stopPhotoUrl = stop.photo ? (stop.photo.startsWith('http') ? stop.photo : `${apiBase}/${stop.photo}`) : "https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80";

                                return (
                                    <div key={stop.tbo_id} className="relative mb-20 last:mb-0">

                                        {/* Timeline Node Ring */}
                                        <div className="absolute -left-[37px] md:-left-[53px] top-6 w-8 h-8 rounded-full bg-[#0A0C10] border-[4px] border-indigo-500 flex items-center justify-center z-10 shadow-[0_0_20px_rgba(99,102,241,0.6)]">
                                            <div className="w-2.5 h-2.5 bg-indigo-400 rounded-full animate-pulse"></div>
                                        </div>

                                        {/* Stop Header Node */}
                                        <div className="bg-[#12141A] rounded-2xl overflow-hidden border border-white/5 shadow-xl relative group mb-8">
                                            <div className="absolute inset-0 bg-gradient-to-t from-[#12141A] via-[#12141A]/60 to-transparent z-10"></div>
                                            <img src={stopPhotoUrl} className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-700" alt={stop.destination} />

                                            <div className="absolute bottom-4 left-6 right-6 z-20 flex items-end justify-between">
                                                <div>
                                                    <p className="text-indigo-400 text-[10px] font-bold uppercase tracking-widest mb-1">Destination {index + 1}</p>
                                                    <h3 className="text-3xl font-black text-white">{stop.destination}</h3>
                                                </div>
                                                <div className="bg-white/10 backdrop-blur-md rounded-lg px-3 py-1.5 border border-white/10 text-xs font-bold">
                                                    {stopSelectedActs.length} Activities
                                                </div>
                                            </div>
                                        </div>

                                        {/* Day-by-Day Itinerary Flow */}
                                        <div className="relative pl-6 md:pl-8 border-l-2 border-dashed border-white/10 ml-6 md:ml-8 mt-2 pb-8">

                                            {(() => {
                                                const actsList = [...stopSelectedActs];
                                                const totalDays = Math.max(2, Math.ceil(actsList.length / 2) + 1); // at least 2 days + 1 for departure
                                                const days = [];

                                                const isFirstStop = index === 0;
                                                const isLastStop = index === itinerary.stops.length - 1;

                                                for (let d = 1; d <= totalDays; d++) {
                                                    const dayActs = [];

                                                    if (d === 1 && isFirstStop) {
                                                        dayActs.push({ type: 'transit', label: 'Arrival & Hotel Check-in', time: 'Morning/Afternoon', icon: '🛬' });
                                                        if (actsList.length > 0) dayActs.push({ ...actsList.shift(), type: 'activity', time: 'Evening' });
                                                    } else if (d === totalDays && isLastStop) {
                                                        if (actsList.length > 0) dayActs.push({ ...actsList.shift(), type: 'activity', time: 'Morning' });
                                                        dayActs.push({ type: 'transit', label: 'Hotel Check-out & Departure', time: 'Afternoon', icon: '🛫' });
                                                    } else {
                                                        if (actsList.length > 0) dayActs.push({ ...actsList.shift(), type: 'activity', time: 'Morning/Afternoon' });
                                                        if (actsList.length > 0) dayActs.push({ ...actsList.shift(), type: 'activity', time: 'Evening' });
                                                    }

                                                    // If we have no specific activities mapped, add some leisure time
                                                    const hasActivity = dayActs.some(a => a.type === 'activity');
                                                    const hasDeparture = dayActs.some(a => a.label?.includes('Departure'));

                                                    if (!hasActivity && !hasDeparture) {
                                                        dayActs.push({ type: 'leisure', label: 'Explore & Lean into the Local Vibe', time: 'Leisure', icon: '🚶' });
                                                    }

                                                    days.push({ day: globalDayCounter++, events: dayActs });
                                                }

                                                return days.map(dayInfo => (
                                                    <div key={`day-${dayInfo.day}`} className="relative mb-12 last:mb-0">

                                                        {/* Floating Day Marker */}
                                                        <div className="absolute -left-[45px] top-0 bg-[#0A0C10] border-2 border-indigo-500/50 text-indigo-300 text-[10px] font-black tracking-widest px-3 py-1 rounded-full shadow-lg shadow-indigo-500/20 z-10">
                                                            DAY {dayInfo.day}
                                                        </div>

                                                        <div className="space-y-4 pt-1">
                                                            {dayInfo.events.map((evt, eIdx) => {

                                                                if (evt.type === 'transit' || evt.type === 'leisure') {
                                                                    return (
                                                                        <div key={`evt-${eIdx}`} className="bg-white/[0.03] border border-white/5 rounded-xl p-4 flex items-center gap-4 group hover:bg-white/[0.05] transition-colors">
                                                                            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-lg">{evt.icon}</div>
                                                                            <div>
                                                                                <p className="text-sm font-bold text-gray-300">{evt.label}</p>
                                                                                <p className="text-xs text-gray-500 font-semibold uppercase tracking-widest mt-0.5">{evt.time}</p>
                                                                            </div>
                                                                        </div>
                                                                    );
                                                                }

                                                                // This is a curated activity (evt.type === 'activity')
                                                                const act = evt;
                                                                const alternatives = stopActsAll.filter(a => !stopSelectedIds.includes(a.id));
                                                                const isMenuOpen = activeSwapMenu?.stopId === stop.tbo_id && activeSwapMenu?.actId === act.id;

                                                                return (
                                                                    <div key={act.id} className="bg-white/[0.08] border border-white/10 rounded-2xl p-5 hover:bg-white/[0.12] transition-all relative group shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                                                                        <div className="flex-1">
                                                                            <div className="flex items-center gap-2 mb-1">
                                                                                <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]"></span>
                                                                                <span className="text-[10px] text-emerald-400 font-black uppercase tracking-widest">{evt.time}</span>
                                                                            </div>
                                                                            <h4 className="text-lg font-bold text-gray-100">{act.name}</h4>
                                                                            <p className="text-gray-400 text-sm mt-1">{act.duration} • <span className="text-indigo-400 font-semibold">Allocated Value: ₹{act.price}</span></p>
                                                                        </div>

                                                                        {/* Swap Mechanism */}
                                                                        {alternatives.length > 0 && (
                                                                            <div className="relative z-20">
                                                                                <button
                                                                                    onClick={() => setActiveSwapMenu(isMenuOpen ? null : { stopId: stop.tbo_id, actId: act.id })}
                                                                                    className="text-xs font-bold uppercase tracking-wider bg-[#0A0C10] hover:bg-[#12141A] border border-white/10 px-4 py-2 rounded-lg text-gray-300 transition-colors flex items-center gap-2 shadow-inner"
                                                                                >
                                                                                    Swap Activity
                                                                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                                                                    </svg>
                                                                                </button>

                                                                                {/* Dropdown Menu for Swaps */}
                                                                                {isMenuOpen && (
                                                                                    <div className="absolute right-0 top-full mt-2 w-72 bg-[#1A1D24] border border-white/10 rounded-xl shadow-[0_20px_40px_-15px_rgba(0,0,0,0.5)] p-2 z-50 animate-fade-in-up">
                                                                                        <p className="text-[10px] text-gray-500 font-bold uppercase px-3 pt-2 pb-1 tracking-widest">Available Alternatives</p>
                                                                                        <div className="max-h-64 overflow-y-auto no-scrollbar space-y-1">
                                                                                            {alternatives.map(alt => {
                                                                                                const diff = alt.price - act.price;
                                                                                                return (
                                                                                                    <button
                                                                                                        key={alt.id}
                                                                                                        onClick={() => handleSwapActivity(stop.tbo_id, act.id, alt)}
                                                                                                        className="w-full text-left p-3 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1 group/alt border border-transparent hover:border-white/5"
                                                                                                    >
                                                                                                        <div className="flex justify-between items-start">
                                                                                                            <span className="font-bold text-sm text-gray-200 group-hover/alt:text-white leading-tight">{alt.name}</span>
                                                                                                            <span className={`text-xs ml-2 font-bold whitespace-nowrap px-2 py-0.5 rounded-md ${diff > 0 ? 'bg-orange-500/10 text-orange-400' : diff < 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/5 text-gray-400'}`}>
                                                                                                                {diff > 0 ? `+₹${diff}` : diff < 0 ? `-₹${Math.abs(diff)}` : 'Same'}
                                                                                                            </span>
                                                                                                        </div>
                                                                                                        <span className="text-xs text-gray-500">{alt.duration}</span>
                                                                                                    </button>
                                                                                                )
                                                                                            })}
                                                                                        </div>
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    </div>
                                                ));
                                            })()}
                                        </div>

                                    </div>
                                );
                            })
                        })()}
                    </div>
                </div>


                {/* Right Column: Sticky Infographic Summary */}
                <div className="lg:col-span-5">
                    <div className="sticky top-28 bg-[#12141A]/90 backdrop-blur-2xl rounded-3xl p-8 border border-white/5 shadow-2xl">

                        <div className="mb-8">
                            <span className="bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full shadow-lg shadow-indigo-500/30">
                                Calculated Trajectory
                            </span>
                            <h2 className="text-3xl font-black text-white mt-4">{currentPkg.tier}</h2>
                            <p className="text-gray-400 text-sm mt-2">{currentPkg.description}</p>
                        </div>

                        {/* Advanced Infographic Blueprint */}
                        <div className="space-y-1 relative">
                            {/* Visual connecting line for blueprint */}
                            <div className="absolute left-[20px] top-6 bottom-6 w-[2px] bg-white/5 z-0"></div>

                            <div className="relative z-10 flex items-center gap-4 bg-[#1A1D24] p-4 rounded-2xl border border-white/5 transition-transform hover:-translate-y-0.5 hover:shadow-lg hover:border-white/10 group">
                                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 shrink-0">
                                    <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <div className="flex-1">
                                    <p className="text-gray-100 font-bold text-sm">Transit & Flights</p>
                                    <p className="text-xs text-blue-400 mt-0.5">TBO Live PNRs Included</p>
                                </div>
                                <div className="text-right">
                                    <p className="font-bold text-white tracking-tight">₹{currentPkg.flight_cost.toLocaleString()}</p>
                                </div>
                            </div>

                            <div className="relative z-10 flex items-center gap-4 bg-[#1A1D24] p-4 rounded-2xl border border-white/5 transition-transform hover:-translate-y-0.5 hover:shadow-lg hover:border-white/10 group">
                                <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 shrink-0">
                                    <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1v1H9V7zm5 0h1v1h-1V7zm-5 4h1v1H9v-1zm5 0h1v1h-1v-1zm-3 4H2v3h10v-3z" />
                                    </svg>
                                </div>
                                <div className="flex-1">
                                    <p className="text-gray-100 font-bold text-sm">Accommodations</p>
                                    <p className="text-[10px] text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20 uppercase tracking-wider font-bold inline-block mt-1">
                                        {currentPkg.hotel_rating} Guaranteed
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="font-bold text-white tracking-tight">₹{currentPkg.hotel_cost.toLocaleString()}</p>
                                </div>
                            </div>

                            <div className="relative z-10 flex items-center gap-4 bg-[#1A1D24] p-4 rounded-2xl border border-white/5 transition-transform hover:-translate-y-0.5 hover:shadow-lg hover:border-white/10 group">
                                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 shrink-0">
                                    <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <div className="flex-1">
                                    <p className="text-gray-100 font-bold text-sm">Curated Experiences</p>
                                    <p className="text-xs text-emerald-400 mt-0.5">{allSelectedCount} items sequenced</p>
                                </div>
                                <div className="text-right flex flex-col items-end">
                                    <p className="font-bold text-emerald-400 tracking-tight transition-colors">
                                        ₹{currentPkg.activities_cost.toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-white/10 flex justify-between items-end">
                            <div>
                                <p className="text-gray-500 text-xs font-bold uppercase tracking-widest mb-1">Final Authorization</p>
                                <p className="text-sm text-gray-400 leading-tight">Net cost per passenger.<br />Locks in current rates.</p>
                            </div>
                            <div className="text-right">
                                <span className="font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 text-5xl tracking-tighter">
                                    ₹{currentPkg.total_price.toLocaleString()}
                                </span>
                            </div>
                        </div>

                        <div className="mt-10">
                            <button
                                onClick={onConfirm}
                                className="w-full bg-indigo-500 text-white rounded-2xl py-4 font-black tracking-wide shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:shadow-[0_0_40px_rgba(99,102,241,0.6)] hover:scale-[1.02] hover:-translate-y-1 transition-all overflow-hidden relative group/btn"
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover/btn:translate-x-full duration-1000 ease-in-out"></div>
                                Authorize & Generate Dossier
                            </button>
                            <p className="text-center text-xs text-gray-500 mt-4 flex items-center justify-center gap-1.5">
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                                Secure SSL 256-bit encryption connection.
                            </p>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
}

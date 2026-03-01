import { useState, useEffect } from "react";

const TIME_SLOTS = ["Morning", "Afternoon", "Evening"];

const getImageForActivity = (act) => {
    const name = act.name.toLowerCase();
    let keyword = "india"; // default

    if (name.includes('food') || name.includes('tasting') || name.includes('cuisine') || name.includes('eat') || name.includes('dinner') || name.includes('market')) {
        keyword = "food,plating";
    } else if (name.includes('boat') || name.includes('cruise') || name.includes('lake') || name.includes('river') || name.includes('beach') || name.includes('mangrove') || name.includes('backwater')) {
        keyword = "boat,lake";
    } else if (name.includes('nature') || name.includes('hike') || name.includes('trek') || name.includes('jungle') || name.includes('safari') || name.includes('mountain') || name.includes('valley')) {
        keyword = "forest,safari";
    } else if (name.includes('temple') || name.includes('heritage') || name.includes('culture') || name.includes('museum') || name.includes('fort') || name.includes('palace') || name.includes('monument')) {
        keyword = "temple,india";
    }

    // Use a hash of the activity ID to consistently pick the same image from the category
    const idHash = (act.id || "1").split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const lockId = (idHash % 1000) + 1; // LoremFlickr lock needs a positive integer

    return `https://loremflickr.com/800/600/${keyword}?lock=${lockId}`;
};

export default function PackageDetails({ pkg, itinerary, initialSelectedActivities, sessionId, apiBase, onBack, onConfirm }) {
    const [selectedActivities, setSelectedActivities] = useState(initialSelectedActivities || {});
    const [activitiesByStop, setActivitiesByStop] = useState({});
    const [loading, setLoading] = useState(true);
    const [currentPkg, setCurrentPkg] = useState(pkg);
    const [swapMenuOpen, setSwapMenuOpen] = useState(null); // { stopId, actId }

    // Preferences state
    const [tripDays, setTripDays] = useState(
        itinerary.stops ? Math.max(3, itinerary.stops.length * 2 + 1) : 5
    );
    const [tripBudget, setTripBudget] = useState(pkg.total_price || 100000);
    const [travelWith, setTravelWith] = useState("couple");

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

    // Build the day plan from selected activities
    const buildDayPlan = () => {
        const days = [];
        let globalDay = 1;

        itinerary.stops.forEach((stop, stopIdx) => {
            const stopActsAll = activitiesByStop[stop.tbo_id] || [];
            const stopSelectedIds = selectedActivities[stop.tbo_id] || [];
            const stopSelectedActs = stopSelectedIds
                .map(id => stopActsAll.find(a => a.id === id))
                .filter(Boolean);

            const isFirst = stopIdx === 0;
            const isLast = stopIdx === itinerary.stops.length - 1;
            const totalDays = Math.max(2, Math.ceil(stopSelectedActs.length / 2) + 1);
            const actsList = [...stopSelectedActs];

            for (let d = 1; d <= totalDays; d++) {
                const events = [];

                if (d === 1 && isFirst) {
                    events.push({ type: "transit", label: "Arrival & Hotel Check-in", time: "Morning", icon: "🛬" });
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Evening", stopId: stop.tbo_id });
                } else if (d === totalDays && isLast) {
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Morning", stopId: stop.tbo_id });
                    events.push({ type: "transit", label: "Hotel Check-out & Departure", time: "Afternoon", icon: "🛫" });
                } else if (d === totalDays && !isLast) {
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Morning", stopId: stop.tbo_id });
                    events.push({ type: "transit", label: `Travel to ${itinerary.stops[stopIdx + 1]?.destination || 'next city'}`, time: "Afternoon", icon: "🚆" });
                } else {
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Morning", stopId: stop.tbo_id });
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Evening", stopId: stop.tbo_id });
                }

                if (!events.some(e => e.type === "activity") && !events.some(e => e.label?.includes("Departure") || e.label?.includes("Travel"))) {
                    events.push({ type: "leisure", label: "Free time — explore at your own pace", time: "Afternoon", icon: "🚶" });
                }

                days.push({ day: globalDay++, city: stop.destination, stopId: stop.tbo_id, events });
            }
        });

        return days;
    };

    // Remove an activity from a stop
    const removeActivity = (stopId, actId) => {
        const act = (activitiesByStop[stopId] || []).find(a => a.id === actId);
        const price = act ? act.price : 0;

        setSelectedActivities(prev => ({
            ...prev,
            [stopId]: (prev[stopId] || []).filter(id => id !== actId)
        }));

        setCurrentPkg(prev => ({
            ...prev,
            activities_cost: prev.activities_cost - price,
            total_price: prev.total_price - price
        }));

        setSwapMenuOpen(null);
    };

    // Swap an activity for another
    const swapActivity = (stopId, oldActId, newAct) => {
        const oldAct = (activitiesByStop[stopId] || []).find(a => a.id === oldActId);
        const priceDiff = newAct.price - (oldAct?.price || 0);

        setSelectedActivities(prev => {
            const stopActs = (prev[stopId] || []).filter(id => id !== oldActId);
            stopActs.push(newAct.id);
            return { ...prev, [stopId]: stopActs };
        });

        setCurrentPkg(prev => ({
            ...prev,
            activities_cost: prev.activities_cost + priceDiff,
            total_price: prev.total_price + priceDiff
        }));

        setSwapMenuOpen(null);
    };

    // Add an activity to a stop
    const addActivity = (stopId, act) => {
        setSelectedActivities(prev => {
            const current = prev[stopId] || [];
            if (current.includes(act.id)) return prev;
            return { ...prev, [stopId]: [...current, act.id] };
        });

        setCurrentPkg(prev => ({
            ...prev,
            activities_cost: prev.activities_cost + act.price,
            total_price: prev.total_price + act.price
        }));
    };

    // Get available (unselected) activities for all stops
    const getAvailableActivities = () => {
        const available = [];
        itinerary.stops.forEach(stop => {
            const allActs = activitiesByStop[stop.tbo_id] || [];
            const selectedIds = selectedActivities[stop.tbo_id] || [];
            allActs.forEach((act, idx) => {
                if (!selectedIds.includes(act.id)) {
                    available.push({ ...act, stopId: stop.tbo_id, city: stop.destination, imgIdx: idx });
                }
            });
        });
        return available;
    };

    const allSelectedCount = Object.values(selectedActivities).flat().length;
    const dayPlan = buildDayPlan();
    const availableActivities = getAvailableActivities();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#F9FAFB]">
                <div className="flex flex-col items-center gap-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-[3px] border-indigo-200 border-t-indigo-600"></div>
                    <p className="text-sm font-medium text-indigo-900 tracking-wide uppercase">Assembling your journey...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#F9FAFB] pb-32 font-sans text-gray-900 selection:bg-indigo-500/30">

            {/* Header */}
            <nav className="fixed top-0 inset-x-0 z-50 bg-white/70 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <button onClick={onBack} className="group flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
                        <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </span>
                        Back to Options
                    </button>
                    <button
                        onClick={onConfirm}
                        className="bg-gray-900 text-white px-6 py-2.5 rounded-full font-bold hover:bg-black transition-all text-sm shadow-lg shadow-gray-900/20 flex items-center gap-2"
                    >
                        Confirm & Book
                        <span className="bg-white/20 px-2 py-0.5 rounded text-xs">₹{currentPkg.total_price.toLocaleString()}</span>
                    </button>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto pt-28 px-6">

                {/* Title */}
                <div className="max-w-2xl mb-12">
                    <span className="text-indigo-500 text-xs font-bold uppercase tracking-widest mb-2 block">Interactive Itinerary</span>
                    <h1 className="text-4xl md:text-5xl font-black text-gray-900 tracking-tight leading-[1.1]">
                        Your Complete <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600">Journey Map.</span>
                    </h1>
                </div>

                {/* Main 2-column layout */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* LEFT: Day-by-Day Plan */}
                    <div className="lg:col-span-7">
                        <div className="space-y-6">
                            {dayPlan.map((dayInfo, dayIdx) => {
                                const showCityHeader = dayIdx === 0 || dayPlan[dayIdx - 1]?.city !== dayInfo.city;

                                return (
                                    <div key={`day-${dayInfo.day}`}>
                                        {/* City divider */}
                                        {showCityHeader && (
                                            <div className="flex items-center gap-3 mb-4 mt-2">
                                                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                                                    <span className="text-indigo-600 text-xs font-black">📍</span>
                                                </div>
                                                <h2 className="text-xl font-bold text-gray-900">{dayInfo.city}</h2>
                                                <div className="flex-1 h-px bg-gray-200"></div>
                                            </div>
                                        )}

                                        {/* Day card */}
                                        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                                            {/* Day header */}
                                            <div className="bg-gray-50 border-b border-gray-200 px-5 py-3 flex items-center justify-between">
                                                <span className="text-xs font-black uppercase tracking-widest text-indigo-500">Day {dayInfo.day}</span>
                                                <span className="text-xs text-gray-400 font-medium">{dayInfo.city}</span>
                                            </div>

                                            {/* Events */}
                                            <div className="divide-y divide-gray-100">
                                                {dayInfo.events.map((evt, eIdx) => {
                                                    if (evt.type === "transit" || evt.type === "leisure") {
                                                        return (
                                                            <div key={`evt-${eIdx}`} className="px-5 py-4 flex items-center gap-4">
                                                                <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center text-lg shrink-0">
                                                                    {evt.icon}
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="text-sm font-semibold text-gray-700">{evt.label}</p>
                                                                    <p className="text-xs text-gray-400 uppercase tracking-wider font-medium mt-0.5">{evt.time}</p>
                                                                </div>
                                                            </div>
                                                        );
                                                    }

                                                    // Activity event
                                                    const bgImg = getImageForActivity(evt);
                                                    const isSwapOpen = swapMenuOpen?.stopId === evt.stopId && swapMenuOpen?.actId === evt.id;
                                                    const alternatives = (activitiesByStop[evt.stopId] || []).filter(
                                                        a => !(selectedActivities[evt.stopId] || []).includes(a.id)
                                                    );

                                                    return (
                                                        <div key={evt.id}>
                                                            <div className="px-5 py-4 flex items-start gap-4 group hover:bg-gray-50/50 transition-colors">
                                                                {/* Time slot */}
                                                                <div className="w-16 shrink-0 pt-1">
                                                                    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-emerald-600">
                                                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                                                        {evt.time}
                                                                    </span>
                                                                </div>

                                                                {/* Image */}
                                                                <div className="w-16 h-16 rounded-xl overflow-hidden shrink-0">
                                                                    <img src={bgImg} alt={evt.name} className="w-full h-full object-cover" />
                                                                </div>

                                                                {/* Info */}
                                                                <div className="flex-1 min-w-0">
                                                                    <h4 className="text-sm font-bold text-gray-900 leading-snug">{evt.name}</h4>
                                                                    <p className="text-xs text-gray-500 mt-1">
                                                                        {evt.duration} • <span className="text-indigo-500 font-semibold">₹{evt.price?.toLocaleString()}</span>
                                                                    </p>
                                                                    {evt.description && (
                                                                        <p className="text-xs text-gray-400 mt-1 line-clamp-1">{evt.description}</p>
                                                                    )}
                                                                </div>

                                                                {/* Action buttons — always visible */}
                                                                <div className="flex items-center gap-1.5 shrink-0 mt-1">
                                                                    {/* Replace button */}
                                                                    {alternatives.length > 0 && (
                                                                        <button
                                                                            onClick={() => setSwapMenuOpen(isSwapOpen ? null : { stopId: evt.stopId, actId: evt.id })}
                                                                            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${isSwapOpen
                                                                                ? 'bg-indigo-100 text-indigo-600'
                                                                                : 'bg-gray-100 text-gray-500 hover:bg-indigo-50 hover:text-indigo-500'
                                                                                }`}
                                                                            title="Replace activity"
                                                                        >
                                                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                                                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                                                            </svg>
                                                                        </button>
                                                                    )}
                                                                    {/* Remove button */}
                                                                    <button
                                                                        onClick={() => removeActivity(evt.stopId, evt.id)}
                                                                        className="w-8 h-8 rounded-lg bg-gray-100 text-gray-500 hover:bg-red-50 hover:text-red-500 flex items-center justify-center transition-all"
                                                                        title="Remove activity"
                                                                    >
                                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                                                        </svg>
                                                                    </button>
                                                                </div>
                                                            </div>

                                                            {/* Inline Replacement Panel */}
                                                            {isSwapOpen && alternatives.length > 0 && (
                                                                <div className="mx-5 mb-4 bg-gray-50 border border-gray-200 rounded-xl overflow-hidden animate-[expand_0.3s_ease-out]">
                                                                    <div className="px-4 py-2.5 border-b border-gray-200 flex items-center justify-between">
                                                                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Replace with</span>
                                                                        <button onClick={() => setSwapMenuOpen(null)} className="text-gray-400 hover:text-gray-600 transition-colors">
                                                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                                                            </svg>
                                                                        </button>
                                                                    </div>
                                                                    <div className="max-h-64 overflow-y-auto">
                                                                        {alternatives.map((alt, altIdx) => {
                                                                            const diff = alt.price - evt.price;
                                                                            const altImg = getImageForActivity(alt);
                                                                            return (
                                                                                <button
                                                                                    key={alt.id}
                                                                                    onClick={() => swapActivity(evt.stopId, evt.id, alt)}
                                                                                    className="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-white transition-colors border-b border-gray-100 last:border-b-0 group/alt"
                                                                                >
                                                                                    <div className="w-12 h-12 rounded-lg overflow-hidden shrink-0">
                                                                                        <img src={altImg} alt={alt.name} className="w-full h-full object-cover" />
                                                                                    </div>
                                                                                    <div className="flex-1 min-w-0">
                                                                                        <p className="text-sm font-semibold text-gray-800 group-hover/alt:text-gray-900 leading-snug">{alt.name}</p>
                                                                                        <p className="text-xs text-gray-400 mt-0.5">{alt.duration}</p>
                                                                                        {alt.description && (
                                                                                            <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{alt.description}</p>
                                                                                        )}
                                                                                    </div>
                                                                                    <div className="text-right shrink-0">
                                                                                        <span className="text-xs font-bold text-gray-700">₹{alt.price.toLocaleString()}</span>
                                                                                        <span className={`block text-[10px] font-bold mt-0.5 ${diff > 0 ? 'text-orange-500' : diff < 0 ? 'text-emerald-500' : 'text-gray-400'
                                                                                            }`}>
                                                                                            {diff > 0 ? `+₹${diff.toLocaleString()}` : diff < 0 ? `-₹${Math.abs(diff).toLocaleString()}` : 'Same price'}
                                                                                        </span>
                                                                                    </div>
                                                                                </button>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* RIGHT: Sticky sidebar */}
                    <div className="lg:col-span-5">
                        <div className="sticky top-24 space-y-6">

                            {/* Cost Breakdown Card */}
                            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
                                <div className="mb-5">
                                    <span className="bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full">
                                        Calculated Trajectory
                                    </span>
                                    <h2 className="text-2xl font-black text-gray-900 mt-3">{currentPkg.tier}</h2>
                                    <p className="text-gray-500 text-sm mt-1">{currentPkg.description}</p>
                                </div>

                                <div className="space-y-3 mb-6">
                                    <div className="flex items-center gap-3 bg-gray-50 p-3.5 rounded-xl">
                                        <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                                            <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-sm font-bold text-gray-900">Transit & Flights</p>
                                            <p className="text-xs text-blue-500">TBO Live PNRs</p>
                                        </div>
                                        <span className="font-bold text-gray-900 text-sm">₹{currentPkg.flight_cost.toLocaleString()}</span>
                                    </div>

                                    <div className="flex items-center gap-3 bg-gray-50 p-3.5 rounded-xl">
                                        <div className="w-9 h-9 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
                                            <svg className="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1v1H9V7zm5 0h1v1h-1V7zm-5 4h1v1H9v-1zm5 0h1v1h-1v-1z" />
                                            </svg>
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-sm font-bold text-gray-900">Accommodations</p>
                                            <p className="text-xs text-purple-500">{currentPkg.hotel_rating}</p>
                                        </div>
                                        <span className="font-bold text-gray-900 text-sm">₹{currentPkg.hotel_cost.toLocaleString()}</span>
                                    </div>

                                    <div className="flex items-center gap-3 bg-gray-50 p-3.5 rounded-xl">
                                        <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
                                            <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-sm font-bold text-gray-900">Experiences</p>
                                            <p className="text-xs text-emerald-500">{allSelectedCount} activities</p>
                                        </div>
                                        <span className="font-bold text-emerald-600 text-sm">₹{currentPkg.activities_cost.toLocaleString()}</span>
                                    </div>
                                </div>

                                {/* Total */}
                                <div className="border-t border-gray-200 pt-4 flex justify-between items-end">
                                    <div>
                                        <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Total per person</p>
                                    </div>
                                    <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600 tracking-tight">
                                        ₹{currentPkg.total_price.toLocaleString()}
                                    </span>
                                </div>

                                <button
                                    onClick={onConfirm}
                                    className="w-full mt-5 bg-gray-900 text-white rounded-xl py-3.5 font-bold hover:bg-black transition-all shadow-lg shadow-gray-900/20 text-sm"
                                >
                                    Authorize & Generate Dossier
                                </button>
                            </div>

                            {/* Preferences Card */}
                            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
                                <h3 className="text-sm font-black uppercase tracking-wider text-gray-400 mb-4">Trip Preferences</h3>

                                <div className="space-y-4">
                                    {/* Days */}
                                    <div>
                                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Number of Days</label>
                                        <div className="flex items-center gap-3">
                                            <button
                                                onClick={() => setTripDays(d => Math.max(2, d - 1))}
                                                className="w-9 h-9 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 font-bold transition-colors"
                                            >−</button>
                                            <span className="text-xl font-black text-gray-900 w-8 text-center">{tripDays}</span>
                                            <button
                                                onClick={() => setTripDays(d => Math.min(14, d + 1))}
                                                className="w-9 h-9 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 font-bold transition-colors"
                                            >+</button>
                                            <span className="text-xs text-gray-400 ml-1">days</span>
                                        </div>
                                    </div>

                                    {/* Budget */}
                                    <div>
                                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Budget</label>
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-bold text-gray-400">₹</span>
                                            <input
                                                type="number"
                                                value={tripBudget}
                                                onChange={(e) => setTripBudget(Number(e.target.value))}
                                                className="w-full bg-gray-100 border border-gray-200 rounded-lg px-3 py-2 text-sm font-bold text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                            />
                                        </div>
                                    </div>

                                    {/* Traveling With */}
                                    <div>
                                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">Traveling With</label>
                                        <div className="grid grid-cols-2 gap-2">
                                            {[
                                                { value: "solo", label: "Solo", icon: "🧍" },
                                                { value: "couple", label: "Couple", icon: "👫" },
                                                { value: "friends", label: "Friends", icon: "👥" },
                                                { value: "family", label: "Family", icon: "👨‍👩‍👧‍👦" },
                                            ].map(opt => (
                                                <button
                                                    key={opt.value}
                                                    onClick={() => setTravelWith(opt.value)}
                                                    className={`py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${travelWith === opt.value
                                                        ? 'bg-indigo-50 text-indigo-700 border-2 border-indigo-300'
                                                        : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100'
                                                        }`}
                                                >
                                                    <span>{opt.icon}</span>
                                                    {opt.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* BOTTOM: Available Activities Pool */}
                {availableActivities.length > 0 && (
                    <div className="mt-12">
                        <div className="flex items-center gap-3 mb-6">
                            <h2 className="text-xl font-black text-gray-900">Available Experiences</h2>
                            <span className="bg-gray-200 text-gray-600 text-xs font-bold px-2.5 py-1 rounded-full">{availableActivities.length}</span>
                            <div className="flex-1 h-px bg-gray-200"></div>
                        </div>
                        <p className="text-sm text-gray-500 mb-6 -mt-3">Click any activity to add it to your plan. Cost and itinerary update automatically.</p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {availableActivities.map((act) => {
                                const bgImg = getImageForActivity(act);

                                return (
                                    <div
                                        key={act.id}
                                        onClick={() => addActivity(act.stopId, act)}
                                        className="group flex rounded-xl overflow-hidden cursor-pointer transition-all duration-300 bg-white border border-gray-200 hover:border-indigo-300 hover:shadow-md"
                                    >
                                        {/* Image */}
                                        <div className="relative w-28 shrink-0 overflow-hidden">
                                            <img src={bgImg} alt={act.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 p-4 flex flex-col justify-between min-w-0">
                                            <div>
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500">{act.city} • {act.duration}</span>
                                                    <span className="text-xs font-bold text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">₹{act.price.toLocaleString()}</span>
                                                </div>
                                                <h4 className="text-sm font-bold text-gray-900 leading-snug">{act.name}</h4>
                                                {act.description && (
                                                    <p className="text-xs text-gray-400 mt-1 line-clamp-1">{act.description}</p>
                                                )}
                                            </div>
                                            <div className="mt-2 flex items-center gap-1 text-xs font-medium text-indigo-500 group-hover:text-indigo-600">
                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                                                </svg>
                                                Add to plan
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

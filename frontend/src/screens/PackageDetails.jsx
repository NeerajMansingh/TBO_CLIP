import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

// From kiran3rd: context-aware image selection based on activity name keywords
const getImageForActivity = (act) => {
    const name = act.name.toLowerCase();
    let keyword = "india";

    if (name.includes('food') || name.includes('tasting') || name.includes('cuisine') || name.includes('eat') || name.includes('dinner') || name.includes('market')) {
        keyword = "food,plating";
    } else if (name.includes('boat') || name.includes('cruise') || name.includes('lake') || name.includes('river') || name.includes('beach') || name.includes('mangrove') || name.includes('backwater')) {
        keyword = "boat,lake";
    } else if (name.includes('nature') || name.includes('hike') || name.includes('trek') || name.includes('jungle') || name.includes('safari') || name.includes('mountain') || name.includes('valley')) {
        keyword = "forest,safari";
    } else if (name.includes('temple') || name.includes('heritage') || name.includes('culture') || name.includes('museum') || name.includes('fort') || name.includes('palace') || name.includes('monument')) {
        keyword = "temple,india";
    }

    const idHash = (act.id || "1").split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const lockId = (idHash % 1000) + 1;
    return `https://loremflickr.com/800/600/${keyword}?lock=${lockId}`;
};

export default function PackageDetails({ pkg, itinerary, initialSelectedActivities, sessionId, apiBase, durationDays, onBack, onConfirm }) {
    const [selectedActivities, setSelectedActivities] = useState(initialSelectedActivities || {});
    const [activitiesByStop, setActivitiesByStop] = useState({});
    const [loading, setLoading] = useState(true);
    const [currentPkg, setCurrentPkg] = useState(pkg);
    const [swapMenuOpen, setSwapMenuOpen] = useState(null); // { stopId, actId }

    const [tripDays, setTripDays] = useState(
        durationDays || (itinerary.stops ? Math.max(3, itinerary.stops.length * 2 + 1) : 5)
    );
    const [tripBudget, setTripBudget] = useState(pkg.total_price || 100000);
    const [travelWith, setTravelWith] = useState("couple");

    useEffect(() => {
        const fetchActivities = async () => {
            setLoading(true);
            const acts = {};
            await new Promise(r => setTimeout(r, 400));

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

    const buildDayPlan = () => {
        const days = [];
        const numStops = itinerary.stops.length;

        // Distribute tripDays across stops
        const baseDaysPerStop = Math.max(1, Math.floor(tripDays / Math.max(1, numStops)));
        let remainingDays = tripDays;

        itinerary.stops.forEach((stop, stopIdx) => {
            const stopActsAll = activitiesByStop[stop.tbo_id] || [];
            const stopSelectedIds = selectedActivities[stop.tbo_id] || [];
            const stopSelectedActs = stopSelectedIds
                .map(id => stopActsAll.find(a => a.id === id))
                .filter(Boolean);

            const isFirst = stopIdx === 0;
            const isLast = stopIdx === numStops - 1;

            // Days for this stop: distribute evenly, give remainder to last stop
            const daysForStop = isLast ? remainingDays : Math.min(baseDaysPerStop, remainingDays);
            remainingDays -= daysForStop;

            const actsList = [...stopSelectedActs];

            for (let d = 1; d <= daysForStop; d++) {
                const events = [];
                const globalDay = days.length + 1;

                if (d === 1 && isFirst) {
                    events.push({ type: "transit", label: "Arrival & Check-in", time: "Morning", icon: "🛬", description: "Private transfer to hotel included." });
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Evening", stopId: stop.tbo_id });
                } else if (d === daysForStop && isLast) {
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Morning", stopId: stop.tbo_id });
                    events.push({ type: "transit", label: "Departure", time: "Afternoon", icon: "🛫", description: "Transfer to airport." });
                } else if (d === daysForStop && !isLast) {
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Morning", stopId: stop.tbo_id });
                    events.push({ type: "transit", label: `Transit to ${itinerary.stops[stopIdx + 1]?.destination || 'Next City'}`, time: "Afternoon", icon: "🚄", description: "Inter-city transfer." });
                } else {
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Morning", stopId: stop.tbo_id });
                    if (actsList.length > 0) events.push({ ...actsList.shift(), type: "activity", time: "Evening", stopId: stop.tbo_id });
                }

                if (!events.some(e => e.type === "activity") && !events.some(e => e.type === "transit")) {
                    events.push({ type: "leisure", label: "Leisure & Exploration", time: "Flexible", icon: "✨", description: "Free time to explore local markets, cafes & hidden gems." });
                }

                days.push({ day: globalDay, city: stop.destination, stopId: stop.tbo_id, events });
            }
        });

        return days;
    };

    const removeActivity = (stopId, actId) => {
        const act = (activitiesByStop[stopId] || []).find(a => a.id === actId);
        const price = act ? act.price : 0;
        setSelectedActivities(prev => ({ ...prev, [stopId]: (prev[stopId] || []).filter(id => id !== actId) }));
        setCurrentPkg(prev => ({ ...prev, activities_cost: prev.activities_cost - price, total_price: prev.total_price - price }));
        setSwapMenuOpen(null);
    };

    const swapActivity = (stopId, oldActId, newAct) => {
        const oldAct = (activitiesByStop[stopId] || []).find(a => a.id === oldActId);
        const priceDiff = newAct.price - (oldAct?.price || 0);
        setSelectedActivities(prev => {
            const stopActs = (prev[stopId] || []).filter(id => id !== oldActId);
            stopActs.push(newAct.id);
            return { ...prev, [stopId]: stopActs };
        });
        setCurrentPkg(prev => ({ ...prev, activities_cost: prev.activities_cost + priceDiff, total_price: prev.total_price + priceDiff }));
        setSwapMenuOpen(null);
    };

    const addActivity = (stopId, act) => {
        // Calculate max capacity for this stop based on how buildDayPlan works
        const numStops = itinerary.stops.length;
        const baseDaysPerStop = Math.max(1, Math.floor(tripDays / Math.max(1, numStops)));

        let remainingDays = tripDays;
        let daysForStop = baseDaysPerStop;

        itinerary.stops.forEach((stop, idx) => {
            const isLast = idx === numStops - 1;
            const stopDays = isLast ? remainingDays : Math.min(baseDaysPerStop, remainingDays);
            if (stop.tbo_id === stopId) daysForStop = stopDays;
            remainingDays -= stopDays;
        });

        const stopSelectedIds = selectedActivities[stopId] || [];

        const isFirstStop = itinerary.stops[0].tbo_id === stopId;
        const isLastStop = itinerary.stops[numStops - 1].tbo_id === stopId;

        // Exact capacity check mimicking buildDayPlan
        let exactCapacity = 0;
        for (let d = 1; d <= daysForStop; d++) {
            if (numStops === 1) {
                if (d === 1) exactCapacity += 1;
                else if (d === daysForStop) exactCapacity += 1;
                else exactCapacity += 2;
            } else {
                if (d === 1 && isFirstStop) exactCapacity += 1;
                else if (d === daysForStop && isLastStop) exactCapacity += 1;
                else if (d === daysForStop && !isLastStop) exactCapacity += 1;
                else exactCapacity += 2;
            }
        }

        if (stopSelectedIds.length >= exactCapacity) {
            alert(`Your itinerary for this city is full! Please increase the 'Duration' in Trip Settings to add more experiences.`);
            return;
        }

        setSelectedActivities(prev => {
            const current = prev[stopId] || [];
            if (current.includes(act.id)) return prev; // Already selected, do not charge!

            // Only increase the price if we are actually adding the activity
            setCurrentPkg(currPkg => ({ ...currPkg, activities_cost: currPkg.activities_cost + act.price, total_price: currPkg.total_price + act.price }));

            return { ...prev, [stopId]: [...current, act.id] };
        });
    };

    const handleDecreaseDuration = () => {
        setTripDays((currentDays) => {
            const newTripDays = Math.max(2, currentDays - 1);
            if (newTripDays === currentDays) return currentDays; // Already at min

            // Dry run the new stop capacities based on the new reduced duration
            const numStops = itinerary.stops.length;
            const baseDaysPerStop = Math.max(1, Math.floor(newTripDays / Math.max(1, numStops)));

            let remainingDays = newTripDays;
            const newCapacities = {}; // StopId -> NewExactCapacity

            itinerary.stops.forEach((stop, idx) => {
                const isFirstStop = idx === 0;
                const isLastStop = idx === numStops - 1;

                const stopDays = isLastStop ? remainingDays : Math.min(baseDaysPerStop, remainingDays);
                remainingDays -= stopDays;

                let exactCapacity = 0;
                for (let d = 1; d <= stopDays; d++) {
                    if (numStops === 1) {
                        if (d === 1 || d === stopDays) exactCapacity += 1;
                        else exactCapacity += 2;
                    } else {
                        if (d === 1 && isFirstStop) exactCapacity += 1;
                        else if (d === stopDays && isLastStop) exactCapacity += 1;
                        else if (d === stopDays && !isLastStop) exactCapacity += 1;
                        else exactCapacity += 2;
                    }
                }
                newCapacities[stop.tbo_id] = exactCapacity;
            });

            // Prune excess activities from selected state & adjust costs
            setSelectedActivities((prevActivities) => {
                let costToDeduct = 0;
                const newActivities = { ...prevActivities };

                for (const stopId of Object.keys(newActivities)) {
                    const capacity = newCapacities[stopId] || 0;
                    const stopSelectedIds = newActivities[stopId];
                    if (stopSelectedIds.length > capacity) {
                        // We must prune! We keep only the first N items up to capacity.
                        const prunedIds = stopSelectedIds.slice(capacity);
                        newActivities[stopId] = stopSelectedIds.slice(0, capacity);

                        // Calculate refund for pruned items
                        const stopActs = activitiesByStop[stopId] || [];
                        prunedIds.forEach((prunedId) => {
                            const actIdObj = stopActs.find((a) => a.id === prunedId);
                            if (actIdObj) costToDeduct += actIdObj.price;
                        });
                    }
                }

                // If anything was pruned, update the global package price right now
                if (costToDeduct > 0) {
                    setCurrentPkg((currPkg) => ({
                        ...currPkg,
                        activities_cost: currPkg.activities_cost - costToDeduct,
                        total_price: currPkg.total_price - costToDeduct,
                    }));
                }

                return newActivities;
            });

            return newTripDays;
        });
    };

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
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="flex flex-col items-center gap-6">
                    <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
                    <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-sm font-bold text-slate-500 uppercase tracking-widest">
                        Designing your experience...
                    </motion.p>
                </div>
            </div>
        );
    }

    return (
        <div className="relative min-h-screen bg-slate-100 text-slate-900 font-sans selection:bg-indigo-500/30 overflow-x-hidden">

            <div className="fixed inset-0 bg-gradient-to-br from-slate-50 via-slate-100 to-slate-200 z-0 pointer-events-none" />
            <div className="fixed top-[-20%] right-[-10%] w-[800px] h-[800px] bg-indigo-500/5 rounded-full blur-[120px] pointer-events-none z-0" />
            <div className="fixed bottom-[-20%] left-[-10%] w-[600px] h-[600px] bg-rose-500/5 rounded-full blur-[100px] pointer-events-none z-0" />

            {/* Navigation */}
            <nav className="fixed top-0 inset-x-0 z-50 bg-white/80 backdrop-blur-xl border-b border-white/50 shadow-sm transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <button onClick={onBack} className="group flex items-center gap-3 text-sm font-bold text-slate-600 hover:text-slate-900 transition-colors">
                        <span className="w-10 h-10 rounded-full bg-slate-50 group-hover:bg-slate-200 flex items-center justify-center transition-colors border border-slate-200">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </span>
                        <span>Adjust Preferences</span>
                    </button>

                    <div className="flex items-center gap-6">
                        <div className="hidden md:flex flex-col items-end mr-2">
                            <span className="text-[10px] uppercase tracking-widest font-extrabold text-slate-400">Estimated Total</span>
                            <span className="text-lg font-black text-slate-900">₹{currentPkg.total_price.toLocaleString()}</span>
                        </div>
                        <button
                            onClick={onConfirm}
                            className="bg-slate-900 hover:bg-black text-white px-8 py-3 rounded-xl font-bold transition-all shadow-xl shadow-slate-900/20 hover:-translate-y-0.5 flex items-center gap-2"
                        >
                            Confirm Itinerary
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                        </button>
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto pt-32 px-6 relative z-10">

                {/* Hero Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="max-w-3xl mb-16"
                >
                    <div className="flex items-center gap-3 mb-4">
                        <span className="bg-indigo-600 text-white px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider shadow-sm shadow-indigo-200">
                            {tripDays} Days
                        </span>
                        <span className="bg-white border border-slate-200 text-slate-700 px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider shadow-sm">
                            {itinerary.stops.length} Cities
                        </span>
                    </div>
                    <h1 className="text-5xl md:text-6xl font-black text-slate-900 tracking-tight leading-[1.1] mb-6 drop-shadow-sm">
                        Your Curated <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">Journey Map.</span>
                    </h1>
                    <p className="text-lg text-slate-600 font-medium max-w-2xl leading-relaxed">
                        We've organized your selected activities into a cohesive timeline. Review your daily flow, swap experiences, or add new discoveries below.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">

                    {/* LEFT COLUMN: Timeline */}
                    <div className="lg:col-span-8">
                        <div className="space-y-0 relative">
                            <div className="absolute left-[27px] top-4 bottom-10 w-0.5 bg-slate-300 z-0"></div>

                            {dayPlan.map((dayInfo, dayIdx) => {
                                const showCityHeader = dayIdx === 0 || dayPlan[dayIdx - 1]?.city !== dayInfo.city;
                                const cityIndex = itinerary.stops.findIndex(s => s.tbo_id === dayInfo.stopId) + 1;

                                return (
                                    <motion.div
                                        key={`day-${dayInfo.day}`}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: dayIdx * 0.1 }}
                                        className="relative z-10 pb-12"
                                    >
                                        {showCityHeader && (
                                            <div className="flex items-center gap-5 mb-8 -ml-1">
                                                <div className="w-14 h-14 rounded-2xl bg-slate-900 text-white shadow-xl shadow-slate-900/20 flex items-center justify-center shrink-0 z-20 font-black text-xl border-4 border-slate-100 ring-1 ring-slate-900/5">
                                                    {cityIndex.toString().padStart(2, '0')}
                                                </div>
                                                <div>
                                                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">{dayInfo.city}</h2>
                                                    <p className="text-sm font-bold text-slate-500">Arrival & Exploration</p>
                                                </div>
                                            </div>
                                        )}

                                        <div className="pl-[70px] relative">
                                            <div className="absolute -left-[42px] top-0 flex flex-col items-center">
                                                <div className="w-3.5 h-3.5 bg-indigo-600 rounded-full ring-4 ring-slate-100 shadow-sm"></div>
                                                <span className="mt-3 text-[10px] font-black uppercase tracking-widest text-slate-400 -rotate-90 origin-center whitespace-nowrap w-20">Day {dayInfo.day}</span>
                                            </div>

                                            <div className="space-y-4">
                                                {dayInfo.events.map((evt, eIdx) => {
                                                    if (evt.type === "transit" || evt.type === "leisure") {
                                                        return (
                                                            <div key={`evt-${eIdx}`} className="bg-white/50 border border-slate-200/80 rounded-xl p-4 flex items-center gap-4 hover:bg-white hover:shadow-md transition-all duration-200">
                                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg shrink-0 border ${evt.type === 'transit' ? 'bg-blue-50 border-blue-100 text-blue-600' : 'bg-amber-50 border-amber-100 text-amber-600'}`}>
                                                                    {evt.icon}
                                                                </div>
                                                                <div>
                                                                    <p className="text-sm font-bold text-slate-800">{evt.label}</p>
                                                                    <p className="text-xs font-medium text-slate-500">{evt.description}</p>
                                                                </div>
                                                            </div>
                                                        );
                                                    }

                                                    // ACTIVITY CARD — uses getImageForActivity (kiran3rd) for context-aware images
                                                    const bgImg = getImageForActivity(evt);
                                                    const isSwapOpen = swapMenuOpen?.stopId === evt.stopId && swapMenuOpen?.actId === evt.id;
                                                    const alternatives = (activitiesByStop[evt.stopId] || []).filter(
                                                        a => !(selectedActivities[evt.stopId] || []).includes(a.id)
                                                    );

                                                    return (
                                                        <motion.div
                                                            layout
                                                            key={evt.id}
                                                            className={`bg-white rounded-2xl border transition-all duration-300 overflow-hidden group shadow-sm hover:shadow-xl hover:shadow-slate-300/40 hover:border-indigo-300 ${isSwapOpen ? 'border-indigo-500 ring-4 ring-indigo-500/10 z-20' : 'border-slate-200'}`}
                                                        >
                                                            <div className="p-1.5 flex gap-5">
                                                                {/* Image */}
                                                                <div className="w-32 md:w-44 relative rounded-xl overflow-hidden shrink-0">
                                                                    <img src={bgImg} alt={evt.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                                                                    <div className="absolute top-2 left-2 bg-slate-900/90 text-white px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wide shadow-md border border-white/10 backdrop-blur-md">
                                                                        {evt.time}
                                                                    </div>
                                                                </div>

                                                                {/* Content */}
                                                                <div className="py-2.5 pr-4 flex-1 flex flex-col justify-between min-h-[130px]">
                                                                    <div>
                                                                        <div className="flex justify-between items-start mb-1 gap-4">
                                                                            <h4 className="text-base font-extrabold text-slate-900 leading-snug line-clamp-2">{evt.name}</h4>
                                                                            <span className="text-sm font-black text-indigo-600 shrink-0 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">₹{evt.price?.toLocaleString()}</span>
                                                                        </div>
                                                                        <p className="text-xs font-bold text-slate-500 mb-2">{evt.duration} • Included</p>
                                                                        {evt.description && <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed font-medium">{evt.description}</p>}
                                                                    </div>

                                                                    {/* Actions */}
                                                                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-100">
                                                                        {alternatives.length > 0 && (
                                                                            <button
                                                                                onClick={() => setSwapMenuOpen(isSwapOpen ? null : { stopId: evt.stopId, actId: evt.id })}
                                                                                className={`text-xs font-bold flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors border ${isSwapOpen ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50'}`}
                                                                            >
                                                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                                                                                Swap Activity
                                                                            </button>
                                                                        )}
                                                                        {/* Remove button — from kiran4th (labeled, cleaner) */}
                                                                        <button
                                                                            onClick={() => removeActivity(evt.stopId, evt.id)}
                                                                            className="text-xs font-bold flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-slate-500 border border-slate-200 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition-colors ml-auto"
                                                                        >
                                                                            Remove
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Swap Drawer — animated, from kiran4th */}
                                                            <AnimatePresence>
                                                                {isSwapOpen && (
                                                                    <motion.div
                                                                        initial={{ height: 0, opacity: 0 }}
                                                                        animate={{ height: "auto", opacity: 1 }}
                                                                        exit={{ height: 0, opacity: 0 }}
                                                                        className="bg-slate-50 border-t border-slate-200"
                                                                    >
                                                                        <div className="p-4">
                                                                            <h5 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Available Alternatives</h5>
                                                                            <div className="grid grid-cols-1 gap-2">
                                                                                {alternatives.map((alt, altIdx) => {
                                                                                    const diff = alt.price - evt.price;
                                                                                    // Use getImageForActivity for contextual images in swap drawer too
                                                                                    const altImg = getImageForActivity(alt);
                                                                                    return (
                                                                                        <button
                                                                                            key={alt.id}
                                                                                            onClick={() => swapActivity(evt.stopId, evt.id, alt)}
                                                                                            className="flex items-center gap-3 p-2 rounded-xl bg-white border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all text-left group/alt"
                                                                                        >
                                                                                            <img src={altImg} className="w-12 h-12 rounded-lg object-cover" alt="" />
                                                                                            <div className="flex-1">
                                                                                                <div className="flex justify-between">
                                                                                                    <span className="text-sm font-bold text-slate-800 group-hover/alt:text-indigo-600">{alt.name}</span>
                                                                                                    <span className={`text-xs font-bold ${diff > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                                                                                        {diff > 0 ? `+₹${diff.toLocaleString()}` : diff < 0 ? `-₹${Math.abs(diff).toLocaleString()}` : 'Same Price'}
                                                                                                    </span>
                                                                                                </div>
                                                                                                <span className="text-xs text-slate-500 line-clamp-1">{alt.description}</span>
                                                                                            </div>
                                                                                        </button>
                                                                                    );
                                                                                })}
                                                                            </div>
                                                                        </div>
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </motion.div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>
                    </div>

                    {/* RIGHT COLUMN: Sticky Sidebar */}
                    <div className="lg:col-span-4">
                        <div className="sticky top-28 space-y-6">

                            {/* Stats Card */}
                            <div className="bg-white/80 backdrop-blur-xl rounded-3xl border border-white shadow-xl shadow-slate-200/50 p-6 relative overflow-hidden ring-1 ring-slate-200/50">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full blur-3xl -mr-10 -mt-10"></div>

                                <div className="relative z-10">
                                    <h3 className="text-lg font-black text-slate-900 mb-6">Investment Breakdown</h3>

                                    <div className="space-y-4 mb-8">
                                        <div className="flex justify-between items-center pb-3 border-b border-slate-200/60">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-sm border border-blue-100">✈️</div>
                                                <span className="text-sm font-bold text-slate-700">Transit</span>
                                            </div>
                                            <span className="font-bold text-slate-900">₹{currentPkg.flight_cost.toLocaleString()}</span>
                                        </div>
                                        <div className="flex justify-between items-center pb-3 border-b border-slate-200/60">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center text-sm border border-purple-100">🏨</div>
                                                <span className="text-sm font-bold text-slate-700">Hotels</span>
                                            </div>
                                            <span className="font-bold text-slate-900">₹{currentPkg.hotel_cost.toLocaleString()}</span>
                                        </div>
                                        <div className="flex justify-between items-center pb-3 border-b border-slate-200/60">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-sm border border-emerald-100">🎟️</div>
                                                <span className="text-sm font-bold text-slate-700">Activities ({allSelectedCount})</span>
                                            </div>
                                            <span className="font-bold text-emerald-700">₹{currentPkg.activities_cost.toLocaleString()}</span>
                                        </div>
                                    </div>

                                    <div className="flex justify-between items-end mb-6">
                                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total per person</span>
                                        <span className="text-3xl font-black text-slate-900">₹{currentPkg.total_price.toLocaleString()}</span>
                                    </div>

                                    <button onClick={onConfirm} className="w-full py-4 bg-slate-900 hover:bg-black text-white rounded-xl font-bold transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-slate-900/10">
                                        Proceed to Booking
                                    </button>
                                </div>
                            </div>

                            {/* Preferences Compact */}
                            <div className="bg-white/80 backdrop-blur-sm rounded-3xl border border-slate-200 p-6 shadow-sm">
                                <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-4">Trip Settings</h4>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-bold text-slate-800">Duration</span>
                                        <div className="flex items-center gap-3 bg-slate-50 rounded-lg p-1 border border-slate-200">
                                            <button onClick={handleDecreaseDuration} className="w-6 h-6 flex items-center justify-center rounded bg-white shadow-sm border border-slate-200 text-xs font-bold hover:text-indigo-600">-</button>
                                            <span className="text-sm font-bold w-4 text-center text-slate-700">{tripDays}</span>
                                            <button onClick={() => setTripDays(d => Math.min(14, d + 1))} className="w-6 h-6 flex items-center justify-center rounded bg-white shadow-sm border border-slate-200 text-xs font-bold hover:text-indigo-600">+</button>
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-bold text-slate-800">Group Type</span>
                                        <div className="flex gap-1">
                                            {['couple', 'family'].map(t => (
                                                <button
                                                    key={t}
                                                    onClick={() => setTravelWith(t)}
                                                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${travelWith === t ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}
                                                >
                                                    {t === 'couple' ? 'Couple' : 'Family'}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>

                {/* BOTTOM: Discovery Deck — kiran4th layout (4-column grid with hover overlay) */}
                <div className="mt-20 border-t border-slate-200/60 pt-12 mb-20 relative z-10">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                        <div>
                            <h2 className="text-3xl font-black text-slate-900">Curate More Memories</h2>
                            <p className="text-slate-600 font-medium mt-2">Tap any experience below to instantly add it to your itinerary.</p>
                        </div>
                        <span className="bg-white border border-slate-200 text-slate-700 font-bold px-4 py-2 rounded-full text-sm self-start shadow-sm">
                            {availableActivities.length} Available Experiences
                        </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {availableActivities.map((act) => {
                            // Use getImageForActivity for contextual images in discovery deck too
                            const bgImg = getImageForActivity(act);
                            return (
                                <motion.div
                                    key={act.id}
                                    whileHover={{ y: -8 }}
                                    onClick={() => addActivity(act.stopId, act)}
                                    className="group cursor-pointer bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300"
                                >
                                    <div className="h-40 relative overflow-hidden">
                                        <img src={bgImg} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt="" />
                                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/70 to-transparent opacity-70 group-hover:opacity-50 transition-opacity"></div>
                                        <div className="absolute bottom-3 left-3 text-white">
                                            <span className="text-[10px] font-bold uppercase tracking-wider bg-white/20 backdrop-blur-md px-2 py-0.5 rounded mb-1 inline-block border border-white/10">{act.city}</span>
                                            <p className="text-lg font-bold">₹{act.price.toLocaleString()}</p>
                                        </div>
                                        <div className="absolute inset-0 bg-indigo-900/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-[2px]">
                                            <span className="bg-white text-indigo-900 font-bold px-4 py-2 rounded-full transform scale-90 group-hover:scale-100 transition-transform shadow-lg">
                                                + Add to Trip
                                            </span>
                                        </div>
                                    </div>
                                    <div className="p-4">
                                        <h4 className="font-bold text-slate-900 line-clamp-1 group-hover:text-indigo-600 transition-colors">{act.name}</h4>
                                        <p className="text-xs text-slate-500 mt-1 line-clamp-2">{act.description || "An amazing experience awaiting you."}</p>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>
                </div>

            </div>
        </div>
    );
}
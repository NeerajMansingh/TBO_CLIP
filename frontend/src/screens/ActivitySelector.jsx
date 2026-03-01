import { useState, useEffect } from "react";

const ACTIVITY_IMAGES = [
    "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1533750349088-cd871a92f312?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1499696010180-025ef6e1a8f9?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1530789253388-582c481c54b0?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=80&w=800&auto=format&fit=crop"
];

export default function ActivitySelector({ itinerary, sessionId, apiBase, budget, onBack, onGenerate }) {
    const [activitiesByStop, setActivitiesByStop] = useState({});
    const [selectedActivities, setSelectedActivities] = useState({});
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [activeTab, setActiveTab] = useState(0);

    // Filter to only stops that have activities loaded
    const stopsWithActivities = itinerary.stops.filter(
        (stop) => (activitiesByStop[stop.tbo_id] || []).length > 0
    );

    useEffect(() => {
        const fetchActivities = async () => {
            setLoading(true);
            const acts = {};
            const initialSels = {};
            for (const stop of itinerary.stops) {
                if (!stop.tbo_id) continue;
                try {
                    const res = await fetch(`${apiBase}/activities/${stop.tbo_id}`);
                    if (res.ok) {
                        const data = await res.json();
                        acts[stop.tbo_id] = data.activities || [];
                        initialSels[stop.tbo_id] = [];
                    }
                } catch (e) {
                    console.error("Failed fetching activities", e);
                }
            }
            setActivitiesByStop(acts);
            setSelectedActivities(initialSels);
            setLoading(false);
        };
        fetchActivities();
    }, [itinerary, apiBase]);

    const toggleActivity = (stopId, actId) => {
        setSelectedActivities((prev) => {
            const stopSels = prev[stopId] || [];
            if (stopSels.includes(actId)) {
                return { ...prev, [stopId]: stopSels.filter((id) => id !== actId) };
            } else {
                return { ...prev, [stopId]: [...stopSels, actId] };
            }
        });
    };

    const allSelectedActs = Object.entries(selectedActivities).flatMap(([stopId, actIds]) => {
        const stopActs = activitiesByStop[stopId] || [];
        return actIds.map(id => stopActs.find(a => a.id === id)).filter(Boolean);
    });

    const currentTotal = allSelectedActs.reduce((sum, act) => sum + act.price, 0);
    const totalSelected = allSelectedActs.length;

    const handleGenerate = async () => {
        setGenerating(true);
        try {
            const res = await fetch(`${apiBase}/generate-packages`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    budget: budget || 100000,
                    travel_month: itinerary.travel_month || "December",
                    selections: selectedActivities
                })
            });
            if (res.ok) {
                const data = await res.json();
                onGenerate(data.packages, selectedActivities);
            } else {
                console.error("Failed generating packages", res.status);
            }
        } catch (e) {
            console.error(e);
        }
        setGenerating(false);
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#F9FAFB]">
                <div className="flex flex-col items-center gap-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-[3px] border-indigo-200 border-t-indigo-600"></div>
                    <p className="text-sm font-medium text-indigo-900 tracking-wide uppercase">Curating vibes...</p>
                </div>
            </div>
        );
    }

    const currentStop = stopsWithActivities[activeTab];
    const currentActs = currentStop ? (activitiesByStop[currentStop.tbo_id] || []) : [];
    const currentSelected = currentStop ? (selectedActivities[currentStop.tbo_id] || []) : [];

    return (
        <div className="min-h-screen bg-[#F9FAFB] pb-40 font-sans selection:bg-indigo-500/30 text-gray-900">

            {/* Sleek Minimal Header */}
            <nav className="fixed top-0 inset-x-0 z-40 bg-white/70 backdrop-blur-xl border-b border-gray-200/50 shadow-sm transition-all duration-300">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <button onClick={onBack} className="group flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
                        <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </span>
                        Return to Route
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
                        <span className="text-xs font-bold uppercase tracking-widest text-indigo-500">Step 2: Experiences</span>
                    </div>
                </div>
            </nav>

            {/* Main Content Area */}
            <div className="max-w-4xl mx-auto pt-32 px-6">
                <div className="max-w-2xl mb-12">
                    <h1 className="text-5xl md:text-6xl font-black text-gray-900 mb-6 tracking-tight leading-[1.1]">
                        Build your <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600">narrative.</span>
                    </h1>
                    <p className="text-xl text-gray-500 leading-relaxed font-light">
                        Go beyond the standard itinerary. Hand-pick the experiences that resonate with you, and we'll craft the perfect package layers around them.
                    </p>
                </div>

                {/* City Tabs */}
                {stopsWithActivities.length > 1 && (
                    <div className="flex items-center gap-2 mb-10">
                        {stopsWithActivities.map((stop, i) => {
                            const stopSelected = (selectedActivities[stop.tbo_id] || []).length;
                            const isActive = activeTab === i;
                            return (
                                <button
                                    key={stop.tbo_id}
                                    onClick={() => setActiveTab(i)}
                                    className={`relative px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 cursor-pointer ${isActive
                                        ? 'bg-gray-900 text-white shadow-lg shadow-gray-900/20'
                                        : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200 hover:border-gray-300'
                                        }`}
                                >
                                    {stop.destination}
                                    {stopSelected > 0 && (
                                        <span className={`ml-2 inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold ${isActive ? 'bg-indigo-500 text-white' : 'bg-indigo-100 text-indigo-600'
                                            }`}>
                                            {stopSelected}
                                        </span>
                                    )}
                                </button>
                            );
                        })}
                    </div>
                )}

                {/* Single-city header when only one stop */}
                {stopsWithActivities.length === 1 && currentStop && (
                    <div className="flex items-baseline gap-4 mb-10 border-b border-gray-200 pb-4">
                        <span className="text-4xl font-black text-gray-200 tracking-tighter">01</span>
                        <h2 className="text-3xl font-bold text-gray-900 tracking-tight">{currentStop.destination}</h2>
                    </div>
                )}

                {/* Horizontal Activity Cards */}
                <div className="space-y-4">
                    {currentActs.map((act, idx) => {
                        const isSelected = currentSelected.includes(act.id);
                        const bgImg = ACTIVITY_IMAGES[idx % ACTIVITY_IMAGES.length];

                        return (
                            <div
                                key={act.id}
                                onClick={() => toggleActivity(currentStop.tbo_id, act.id)}
                                className={`group relative flex rounded-2xl overflow-hidden cursor-pointer transition-all duration-400 ease-out bg-white border ${isSelected
                                    ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-[#F9FAFB] border-indigo-200 shadow-[0_8px_30px_-10px_rgba(99,102,241,0.25)]'
                                    : 'border-gray-200 hover:border-gray-300 hover:shadow-[0_8px_30px_-10px_rgba(0,0,0,0.08)]'
                                    }`}
                            >
                                {/* Left: Image */}
                                <div className="relative w-48 min-h-[180px] flex-shrink-0 overflow-hidden">
                                    <img
                                        src={bgImg}
                                        alt={act.name}
                                        className={`absolute inset-0 w-full h-full object-cover transition-transform duration-700 ease-out ${isSelected ? 'scale-105' : 'group-hover:scale-110'
                                            }`}
                                    />
                                    {/* Subtle overlay */}
                                    <div className={`absolute inset-0 transition-opacity duration-500 ${isSelected
                                        ? 'bg-indigo-900/20'
                                        : 'bg-gray-900/5 group-hover:bg-gray-900/10'
                                        }`}></div>

                                    {/* Check indicator overlay */}
                                    {isSelected && (
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <div className="bg-indigo-500 text-white w-10 h-10 rounded-full flex items-center justify-center shadow-lg animate-[bounce-in_0.4s_cubic-bezier(0.175,0.885,0.32,1.275)]">
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                                </svg>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Right: Content */}
                                <div className="flex-1 p-5 flex flex-col justify-between min-w-0">
                                    <div>
                                        {/* Top row: Duration + Price */}
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-indigo-500">
                                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                {act.duration}
                                            </span>
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold transition-colors duration-300 ${isSelected
                                                ? 'bg-indigo-500 text-white'
                                                : 'bg-gray-100 text-gray-700 group-hover:bg-gray-200'
                                                }`}>
                                                ₹{act.price.toLocaleString()}
                                            </span>
                                        </div>

                                        {/* Activity Name */}
                                        <h3 className="text-lg font-bold text-gray-900 mb-2 leading-snug">
                                            {act.name}
                                        </h3>

                                        {/* Description */}
                                        <p className="text-sm text-gray-500 leading-relaxed line-clamp-2">
                                            {act.description || `Experience ${act.name} — a curated activity designed to immerse you in the local culture and create lasting memories.`}
                                        </p>
                                    </div>

                                    {/* Bottom action hint */}
                                    <div className="mt-3 flex items-center justify-between">
                                        <span className={`text-xs font-medium transition-colors duration-300 ${isSelected ? 'text-indigo-500' : 'text-gray-400 group-hover:text-gray-500'
                                            }`}>
                                            {isSelected ? '✓ Added to your trip' : 'Click to add'}
                                        </span>
                                        <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${isSelected
                                            ? 'bg-indigo-500 border-indigo-500'
                                            : 'border-gray-300 group-hover:border-gray-400'
                                            }`}>
                                            {isSelected && (
                                                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                                </svg>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Floating Glassmorphic Action Bar */}
            {totalSelected > 0 && (
                <div className="fixed bottom-8 inset-x-0 flex justify-center z-50 pointer-events-none animate-[slide-up_0.5s_ease-out]">
                    <div className="bg-white/80 backdrop-blur-2xl border border-white shadow-[0_10px_40px_-10px_rgba(0,0,0,0.15)] rounded-full p-2.5 pl-4 sm:pl-6 flex items-center gap-4 sm:gap-8 pointer-events-auto transform transition-transform hover:scale-[1.01] hover:shadow-[0_20px_50px_-15px_rgba(99,102,241,0.25)]">

                        <div className="flex flex-col text-sm hidden sm:flex">
                            <span className="font-extrabold text-gray-900 tracking-tight text-base mb-0.5">₹{currentTotal.toLocaleString()}</span>
                            <span className="text-gray-500 font-medium text-xs uppercase tracking-wider">{totalSelected} Selected</span>
                        </div>

                        <div className="h-10 w-[1px] bg-gray-200 hidden sm:block"></div>

                        <div className="flex -space-x-4">
                            {allSelectedActs.slice(0, 4).map((act, idx) => {
                                const bgImg = ACTIVITY_IMAGES[Math.floor(Math.random() * ACTIVITY_IMAGES.length)];
                                return (
                                    <div key={idx} className="w-10 h-10 sm:w-12 sm:h-12 rounded-full border-2 border-white overflow-hidden bg-gray-200 shadow-md relative z-[1]">
                                        <img src={bgImg} className="w-full h-full object-cover" />
                                    </div>
                                )
                            })}
                            {totalSelected > 4 && (
                                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full border-2 border-white bg-indigo-50 flex items-center justify-center text-xs font-bold text-indigo-600 shadow-md relative z-[2]">
                                    +{totalSelected - 4}
                                </div>
                            )}
                        </div>

                        <button
                            onClick={handleGenerate}
                            disabled={generating}
                            className="bg-gray-900 hover:bg-black text-white px-6 sm:px-8 py-3.5 sm:py-4 rounded-full font-bold transition-all flex items-center gap-3 overflow-hidden group shadow-lg shadow-gray-900/20 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            <span className="relative z-10 leading-none">{generating ? 'Analyzing...' : 'Generate Packages'}</span>
                            {!generating && (
                                <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center group-hover:translate-x-1 transition-transform relative z-10">
                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                    </svg>
                                </span>
                            )}
                        </button>
                    </div>
                </div>
            )}

            <style dangerouslySetInnerHTML={{
                __html: `
        @keyframes bounce-in {
          0% { transform: scale(0); opacity: 0; }
          60% { transform: scale(1.1); opacity: 1; }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes slide-up {
          0% { transform: translateY(100%); opacity: 0; }
          100% { transform: translateY(0); opacity: 1; }
        }
      `}} />
        </div>
    );
}

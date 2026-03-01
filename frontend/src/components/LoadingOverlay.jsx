import React from 'react';

const LOADING_STEPS = [
    { icon: '🧠', label: 'Analysing your vibe…' },
    { icon: '🗺️', label: 'Finding matching destinations…' },
    { icon: '✈️', label: 'Checking live flight prices…' },
    { icon: '🏨', label: 'Verifying hotel availability…' },
    { icon: '✨', label: 'Crafting your personalised itinerary…' },
];

function SkeletonCard() {
    return (
        <div className="card-light p-5 flex flex-col gap-3">
            <div className="skeleton rounded-xl h-44 w-full" />
            <div className="skeleton h-5 w-3/4 rounded" />
            <div className="skeleton h-4 w-1/2 rounded" />
            <div className="flex gap-2 mt-2">
                <div className="skeleton h-6 w-16 rounded-full" />
                <div className="skeleton h-6 w-20 rounded-full" />
                <div className="skeleton h-6 w-14 rounded-full" />
            </div>
            <div className="skeleton h-4 w-full rounded mt-1" />
            <div className="skeleton h-4 w-5/6 rounded" />
            <div className="skeleton h-10 w-28 rounded-xl mt-2" />
        </div>
    );
}

export default function LoadingOverlay() {
    const [step, setStep] = React.useState(0);

    React.useEffect(() => {
        const timer = setInterval(() => {
            setStep(s => (s + 1) % LOADING_STEPS.length);
        }, 1200);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="w-full max-w-6xl mx-auto px-4 py-12 animate-fade-in">
            {/* Status header */}
            <div className="text-center mb-10">
                <div className="inline-flex items-center gap-3 bg-white border border-blue-100 px-6 py-3 rounded-2xl shadow-sm mb-6">
                    <span className="text-2xl">{LOADING_STEPS[step].icon}</span>
                    <span className="text-sm font-semibold text-gray-700 transition-all">{LOADING_STEPS[step].label}</span>
                    <div className="flex gap-1 ml-2">
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                    </div>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Building your perfect itinerary</h2>
                <p className="text-gray-500 text-sm">Checking live TBO prices and generating AI-curated routes…</p>
            </div>

            {/* Step progress bar */}
            <div className="flex items-center justify-center gap-2 mb-10">
                {LOADING_STEPS.map((s, i) => (
                    <div
                        key={i}
                        className={`h-1.5 rounded-full transition-all duration-500 ${i <= step ? 'bg-blue-500 w-8' : 'bg-gray-200 w-4'
                            }`}
                    />
                ))}
            </div>

            {/* Skeleton cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <SkeletonCard />
                <SkeletonCard />
                <div className="hidden md:block"><SkeletonCard /></div>
            </div>
        </div>
    );
}

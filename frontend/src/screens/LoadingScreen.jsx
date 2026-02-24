import { useState, useEffect } from 'react'

const STEPS = [
    {
        icon: '🔍',
        label: 'Analysing the visual feel of your photo...',
        sublabel: 'Running CLIP visual embeddings',
    },
    {
        icon: '🗺️',
        label: 'Scanning destinations within your budget...',
        sublabel: 'Searching ChromaDB vector database',
    },
    {
        icon: '✅',
        label: 'Confirming availability and prices...',
        sublabel: 'Checking TBO inventory',
    },
]

const STEP_DELAY_MS = 1800

export default function LoadingScreen({ uploadedPhoto }) {
    const [activeStep, setActiveStep] = useState(0)
    const [completedSteps, setCompletedSteps] = useState([])

    useEffect(() => {
        const timers = []

        STEPS.forEach((_, i) => {
            if (i === 0) {
                setActiveStep(0)
                return
            }
            const t = setTimeout(() => {
                setCompletedSteps(prev => [...prev, i - 1])
                setActiveStep(i)
            }, i * STEP_DELAY_MS)
            timers.push(t)
        })

        // Mark last step complete after delay
        const final = setTimeout(() => {
            setCompletedSteps(prev => [...prev, STEPS.length - 1])
        }, STEPS.length * STEP_DELAY_MS)
        timers.push(final)

        return () => timers.forEach(clearTimeout)
    }, [])

    return (
        <div className="min-h-screen flex flex-col items-center justify-center px-4">
            {/* Decorative blobs */}
            <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl animate-pulse-soft pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-ocean-500/8 rounded-full blur-3xl animate-pulse-soft pointer-events-none" style={{ animationDelay: '1s' }} />

            <div className="relative w-full max-w-md">
                {/* App name */}
                <div className="text-center mb-10 animate-fade-in">
                    <p className="text-white/40 text-sm uppercase tracking-widest font-medium">✈️ VibeTravel</p>
                </div>

                {/* Photo preview if available */}
                {uploadedPhoto && (
                    <div className="relative mb-8 animate-fade-in" style={{ animationDelay: '0.1s' }}>
                        <div className="relative mx-auto w-40 h-40 rounded-2xl overflow-hidden ring-2 ring-white/10 shadow-2xl">
                            <img src={uploadedPhoto} alt="Your inspiration" className="w-full h-full object-cover" />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                        </div>
                        {/* Scanning animation ring */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-44 h-44 rounded-2xl border-2 border-brand-400/50 animate-ping" />
                        </div>
                    </div>
                )}

                {/* Step list */}
                <div className="space-y-3">
                    {STEPS.map((step, i) => {
                        const isCompleted = completedSteps.includes(i)
                        const isActive = activeStep === i && !isCompleted
                        const isPending = i > activeStep

                        return (
                            <div
                                key={i}
                                className={`card p-4 transition-all duration-500 ${isActive
                                        ? 'border-brand-400/40 bg-brand-500/8'
                                        : isCompleted
                                            ? 'border-green-500/30 bg-green-500/5'
                                            : 'opacity-40'
                                    }`}
                                style={{
                                    animation: isActive || isCompleted ? 'fadeIn 0.4s ease-out forwards' : 'none',
                                }}
                            >
                                <div className="flex items-center gap-4">
                                    {/* Icon / spinner / check */}
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-300 ${isCompleted
                                            ? 'bg-green-500/20'
                                            : isActive
                                                ? 'bg-brand-500/20'
                                                : 'bg-white/5'
                                        }`}>
                                        {isCompleted ? (
                                            <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                            </svg>
                                        ) : isActive ? (
                                            <svg className="w-5 h-5 text-brand-400 animate-spin-slow" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                            </svg>
                                        ) : (
                                            <span className="text-lg opacity-60">{step.icon}</span>
                                        )}
                                    </div>

                                    {/* Labels */}
                                    <div>
                                        <p className={`text-sm font-medium transition-colors ${isCompleted ? 'text-green-300' : isActive ? 'text-white' : 'text-white/50'
                                            }`}>
                                            {step.label}
                                        </p>
                                        <p className={`text-xs mt-0.5 transition-colors ${isActive ? 'text-white/50' : 'text-white/25'
                                            }`}>
                                            {step.sublabel}
                                        </p>
                                    </div>
                                </div>

                                {/* Progress bar for active step */}
                                {isActive && (
                                    <div className="mt-3 h-0.5 bg-white/10 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-brand-500 to-orange-400 shimmer-bg rounded-full w-full" />
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>

                <p className="text-center text-white/25 text-xs mt-8 animate-pulse-soft">
                    This usually takes 3–5 seconds
                </p>
            </div>
        </div>
    )
}

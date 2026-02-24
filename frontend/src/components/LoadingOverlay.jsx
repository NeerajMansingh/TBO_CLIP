import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const STAGES = [
    "Extracting visual vectors...",
    "Mapping aesthetic signatures...",
    "Cross-referencing travel profiles...",
    "Pinging TBO Live API...",
    "Calculating expected pricing...",
    "Finalizing match logic..."
];

export default function LoadingOverlay() {
    const [stageIndex, setStageIndex] = useState(0);

    useEffect(() => {
        // Cycle through stages quickly to fake "complex thinking"
        const interval = setInterval(() => {
            setStageIndex(prev => {
                if (prev < STAGES.length - 1) return prev + 1;
                return prev;
            });
        }, 1200);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-950/80 backdrop-blur-xl transition-all duration-300">
            <div className="flex flex-col items-center max-w-md w-full p-8 rounded-3xl border border-gray-800/50 bg-gray-900/40 shadow-2xl relative overflow-hidden">
                {/* Ambient glow */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>

                <div className="relative z-10 flex flex-col items-center">
                    <Loader2 className="w-16 h-16 text-indigo-500 animate-spin mb-8" />

                    <div className="h-8 overflow-hidden relative w-full text-center">
                        <AnimatePresence mode="wait">
                            <motion.p
                                key={stageIndex}
                                initial={{ opacity: 0, y: 15 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -15 }}
                                transition={{ duration: 0.3 }}
                                className="text-gray-300 font-medium tracking-wide"
                            >
                                {STAGES[stageIndex]}
                            </motion.p>
                        </AnimatePresence>
                    </div>

                    {/* Progress bar visual */}
                    <div className="w-full h-1 bg-gray-800 rounded-full mt-6 overflow-hidden">
                        <motion.div
                            className="h-full bg-indigo-500"
                            initial={{ width: "5%" }}
                            animate={{ width: `${Math.min(((stageIndex + 1) / STAGES.length) * 100, 100)}%` }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

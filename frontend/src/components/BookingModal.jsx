import React, { useState, useEffect } from 'react';
import { Terminal, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function BookingModal({ dest, isOpen, onClose }) {
    const [logs, setLogs] = useState([]);
    const [status, setStatus] = useState('connecting'); // connecting | supplements | success | failure
    const [supplements, setSupplements] = useState([]);
    const [bookingRef, setBookingRef] = useState('');

    useEffect(() => {
        if (!isOpen) return;

        setLogs([]);
        setStatus('connecting');
        setSupplements([]);

        const sequence = async () => {
            const wait = (ms) => new Promise(r => setTimeout(r, ms));
            const addLog = (msg) => setLogs(p => [...p, msg]);

            await wait(500);
            addLog("> Initializing connection to TBO gateway...");
            await wait(800);
            addLog("> Authenticating API credentials...");
            await wait(600);
            addLog(`> Checking live inventory for ${dest?.name}...`);
            await wait(1200);

            // Simulate 10% chance of failure, 30% chance of supplements, 60% success
            const rand = Math.random();

            if (rand < 0.1) {
                addLog("> ERROR: Inventory locked by another agent.");
                addLog("> TBO Error Code: 0x8A4_INVF.");
                setStatus('failure');
            } else if (rand < 0.4) {
                addLog("> Mandatory supplements detected (City Tax/Resort Fee).");
                addLog("> Pausing for user acknowledgment...");
                setSupplements([
                    { id: 1, name: "City Environmental Tax", amount: 1540 },
                    { id: 2, name: "Resort Amenity Fee", amount: 2100 }
                ]);
                setStatus('supplements');
            } else {
                addLog("> Inventory confirmed. Securing block...");
                await wait(800);
                addLog("> Payment token validated.");
                await wait(600);
                addLog("> PNR generated successfully.");
                setBookingRef(`TBO-${Math.random().toString(36).substring(2, 10).toUpperCase()}`);
                setStatus('success');
            }
        };

        sequence();
    }, [isOpen, dest]);

    if (!isOpen) return null;

    const handleAcknowledge = () => {
        setStatus('success');
        setLogs(p => [...p, "> Supplements acknowledged. Resuming...", "> PNR generated successfully."]);
        setBookingRef(`TBO-${Math.random().toString(36).substring(2, 10).toUpperCase()}`);
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-gray-950/80 backdrop-blur-md pb-10">
            <div className="w-full max-w-lg bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col">

                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-950">
                    <h3 className="text-white font-bold flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                        TBO Live Gateway
                    </h3>
                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">✕</button>
                </div>

                {/* Content Body */}
                <div className="p-6 flex flex-col gap-6 max-h-[70vh] overflow-y-auto">

                    {/* Terminal Log View */}
                    <div className="bg-black/50 rounded-lg p-4 font-mono text-xs text-green-400 min-h-[120px] max-h-[200px] overflow-y-auto border border-gray-800">
                        {logs.map((log, i) => (
                            <div key={i} className="mb-1 leading-relaxed opacity-90">{log}</div>
                        ))}
                        {status === 'connecting' && <div className="animate-pulse">_</div>}
                    </div>

                    <AnimatePresence mode="wait">

                        {status === 'supplements' && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-xl"
                            >
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
                                    <div>
                                        <h4 className="text-yellow-500 font-bold mb-1">Mandatory Supplements</h4>
                                        <p className="text-xs text-yellow-500/80 mb-4">The hotel requires these taxes/fees to be paid at booking.</p>

                                        <div className="space-y-2 mb-4">
                                            {supplements.map(sup => (
                                                <div key={sup.id} className="flex justify-between text-sm text-gray-300 bg-gray-950/50 p-2 rounded">
                                                    <span>{sup.name}</span>
                                                    <span className="font-mono">₹{sup.amount}</span>
                                                </div>
                                            ))}
                                        </div>

                                        <button
                                            onClick={handleAcknowledge}
                                            className="w-full py-2.5 bg-yellow-500 hover:bg-yellow-400 text-yellow-950 font-bold rounded-lg transition-colors text-sm"
                                        >
                                            Acknowledge & Book Now
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {status === 'success' && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                                className="flex flex-col items-center justify-center p-6 bg-green-500/10 border border-green-500/20 rounded-xl text-center"
                            >
                                <CheckCircle2 className="w-12 h-12 text-green-500 mb-3" />
                                <h4 className="text-xl font-bold text-white mb-1">Booking Confirmed!</h4>
                                <p className="text-gray-400 text-sm mb-4">Your itinerary is secured.</p>

                                <div className="bg-gray-950 border border-gray-800 w-full p-3 rounded-lg mb-4">
                                    <span className="text-[10px] text-gray-500 uppercase tracking-widest block mb-1">Reference Code</span>
                                    <span className="text-2xl font-mono text-white font-bold tracking-wider">{bookingRef}</span>
                                </div>

                                <button onClick={onClose} className="btn-primary w-full">Done</button>
                            </motion.div>
                        )}

                        {status === 'failure' && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                                className="flex flex-col items-center justify-center p-6 bg-red-500/10 border border-red-500/20 rounded-xl text-center"
                            >
                                <XCircle className="w-12 h-12 text-red-500 mb-3" />
                                <h4 className="text-xl font-bold text-white mb-1">Booking Failed</h4>
                                <p className="text-gray-300 text-sm mb-4 max-w-xs">
                                    The selected inventory is no longer available.
                                </p>

                                <div className="text-xs text-gray-500 bg-gray-950 p-3 rounded border border-gray-800 mb-4">
                                    Initiating 120-second asynchronous fallback check loop. We will notify you if it opens up.
                                </div>

                                <button onClick={onClose} className="btn-secondary w-full">Return to Results</button>
                            </motion.div>
                        )}

                    </AnimatePresence>

                </div>
            </div>
        </div>
    );
}

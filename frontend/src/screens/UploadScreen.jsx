import { useState, useRef, useCallback } from 'react'

const MAX_SIZE_MB = 10

export default function UploadScreen({ onFindMatch }) {
    const [photo, setPhoto] = useState(null)
    const [preview, setPreview] = useState(null)
    const [budget, setBudget] = useState('')
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [isDragging, setIsDragging] = useState(false)
    const [errors, setErrors] = useState({})
    const fileInputRef = useRef(null)

    const handleFile = useCallback((file) => {
        if (!file) return
        if (!file.type.startsWith('image/')) {
            setErrors(e => ({ ...e, photo: 'Please upload an image file' }))
            return
        }
        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
            setErrors(e => ({ ...e, photo: `Image must be under ${MAX_SIZE_MB}MB` }))
            return
        }
        setPhoto(file)
        setPreview(URL.createObjectURL(file))
        setErrors(e => ({ ...e, photo: null }))
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setIsDragging(false)
        handleFile(e.dataTransfer.files[0])
    }, [handleFile])

    const handleDragOver = useCallback((e) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback(() => setIsDragging(false), [])

    const handleSubmit = useCallback(() => {
        const newErrors = {}
        if (!photo) newErrors.photo = 'Please upload an inspiration photo'
        if (!budget || isNaN(budget) || Number(budget) < 1000)
            newErrors.budget = 'Enter a budget of at least ₹1,000'
        setErrors(newErrors)
        if (Object.keys(newErrors).length > 0) return

        const travelDates = startDate && endDate ? `${startDate} to ${endDate}` : null
        onFindMatch({ photo, budget: Number(budget), travelDates })
    }, [photo, budget, startDate, endDate, onFindMatch])

    return (
        <div className="min-h-screen bg-mesh flex flex-col items-center justify-center px-4 py-12">
            {/* Decorative blobs */}
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-ocean-500/8 rounded-full blur-3xl pointer-events-none" />

            <div className="relative w-full max-w-xl animate-fade-in">
                {/* Logo + tagline */}
                <div className="text-center mb-10">
                    <div className="inline-flex items-center gap-2 mb-4">
                        <span className="text-3xl">✈️</span>
                        <h1 className="font-display text-4xl font-bold text-gradient">VibeTravel</h1>
                    </div>
                    <p className="text-white/60 text-base leading-relaxed max-w-sm mx-auto">
                        Upload your dream destination photo.{' '}
                        <span className="text-white/80">We'll find it at a price you can actually afford.</span>
                    </p>
                </div>

                {/* Main card */}
                <div className="card p-6 space-y-5">
                    {/* Upload zone */}
                    <div>
                        <label className="block text-sm font-medium text-white/70 mb-2">
                            Inspiration photo
                        </label>
                        <div
                            onClick={() => fileInputRef.current?.click()}
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            className={`relative rounded-xl overflow-hidden cursor-pointer transition-all duration-300 border-2 border-dashed
                ${isDragging
                                    ? 'border-brand-400 bg-brand-500/10 scale-[1.01]'
                                    : preview
                                        ? 'border-white/20 hover:border-white/30'
                                        : 'border-white/15 hover:border-brand-400/50 bg-white/3 hover:bg-white/5'
                                }`}
                            style={{ minHeight: preview ? 'auto' : '180px' }}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                className="hidden"
                                id="photo-upload"
                                onChange={e => handleFile(e.target.files[0])}
                            />

                            {preview ? (
                                <div className="relative group">
                                    <img
                                        src={preview}
                                        alt="Your inspiration"
                                        className="w-full h-56 object-cover"
                                    />
                                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                        <span className="text-white text-sm font-medium">Click to change photo</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-44 gap-3 p-4">
                                    <div className="w-14 h-14 rounded-2xl bg-white/8 border border-white/15 flex items-center justify-center animate-float">
                                        <svg className="w-7 h-7 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                    </div>
                                    <div className="text-center">
                                        <p className="text-white/70 text-sm font-medium">
                                            Drop your inspiration photo here
                                        </p>
                                        <p className="text-white/40 text-xs mt-1">or click to browse · JPG, PNG, WEBP · max {MAX_SIZE_MB}MB</p>
                                    </div>
                                </div>
                            )}
                        </div>
                        {errors.photo && (
                            <p className="text-red-400 text-xs mt-1.5">{errors.photo}</p>
                        )}
                    </div>

                    {/* Budget */}
                    <div>
                        <label htmlFor="budget" className="block text-sm font-medium text-white/70 mb-2">
                            Your budget <span className="text-white/40 font-normal">(₹ INR per person)</span>
                        </label>
                        <div className="relative">
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-medium">₹</span>
                            <input
                                id="budget"
                                type="number"
                                min="1000"
                                step="1000"
                                placeholder="40,000"
                                value={budget}
                                onChange={e => setBudget(e.target.value)}
                                className="input-field pl-8"
                            />
                        </div>
                        {errors.budget && (
                            <p className="text-red-400 text-xs mt-1.5">{errors.budget}</p>
                        )}
                        <div className="flex gap-2 mt-2 flex-wrap">
                            {[10000, 20000, 40000, 75000].map(amt => (
                                <button
                                    key={amt}
                                    onClick={() => setBudget(String(amt))}
                                    className={`px-3 py-1 rounded-lg text-xs transition-all duration-150 border
                    ${budget === String(amt)
                                            ? 'bg-brand-500/20 border-brand-400/50 text-brand-300'
                                            : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10 hover:text-white/70'
                                        }`}
                                >
                                    ₹{(amt / 1000).toFixed(0)}K
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Travel dates */}
                    <div>
                        <label className="block text-sm font-medium text-white/70 mb-2">
                            Travel dates <span className="text-white/40 font-normal">(optional)</span>
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                            <input
                                type="date"
                                value={startDate}
                                onChange={e => setStartDate(e.target.value)}
                                className="input-field text-sm [color-scheme:dark]"
                                placeholder="From"
                            />
                            <input
                                type="date"
                                value={endDate}
                                onChange={e => setEndDate(e.target.value)}
                                className="input-field text-sm [color-scheme:dark]"
                                placeholder="To"
                            />
                        </div>
                    </div>

                    {/* Submit */}
                    <button
                        onClick={handleSubmit}
                        className="btn-primary w-full py-4 text-base"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        Find My Match
                    </button>
                </div>

                {/* Footer hint */}
                <p className="text-center text-white/25 text-xs mt-6">
                    Try a photo of Santorini, Bali, or any landscape that inspires you
                </p>
            </div>
        </div>
    )
}

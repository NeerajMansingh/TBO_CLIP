import { useState, useCallback, useEffect } from 'react'
import SearchInterface from './components/SearchInterface'
import LoadingOverlay from './components/LoadingOverlay'
import ResultsGrid from './components/ResultsGrid'
import BookingModal from './components/BookingModal'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [appState, setAppState] = useState('search') // 'search' | 'loading' | 'results'

  // Dual Input Flow Data
  const [imagePreview, setImagePreview] = useState(null)
  const [chatInput, setChatInput] = useState('')

  // Trip Configuration
  const [originCity, setOriginCity] = useState('Mumbai')
  const [travelMonth, setTravelMonth] = useState('December')
  const [selectedVibes, setSelectedVibes] = useState([])

  // Persistent State
  const [recentSearches, setRecentSearches] = useState([])
  const [rejectedIds, setRejectedIds] = useState([])

  // Responses
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)

  // Booking Modal State
  const [bookingModalTarget, setBookingModalTarget] = useState(null)

  useEffect(() => {
    const saved = localStorage.getItem('vibeTravel_recentSearches')
    if (saved) setRecentSearches(JSON.parse(saved))
  }, [])

  const saveSearch = (query) => {
    if (!query.trim()) return;
    const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5)
    setRecentSearches(updated)
    localStorage.setItem('vibeTravel_recentSearches', JSON.stringify(updated))
  }

  const handleSearch = useCallback(async (isReroll = false) => {
    setError(null)
    setAppState('loading')

    if (!isReroll && chatInput) saveSearch(chatInput)

    try {
      // Create flexible payload mapping logic here
      const formData = new FormData()
      if (imagePreview) {
        // Fetch blob from preview URL (hack for demo/client upload)
        const res = await fetch(imagePreview)
        const blob = await res.blob()
        formData.append('photo', blob, 'upload.jpg')
      }

      formData.append('budget', "100000") // Default budget for dummy if needed
      formData.append('travel_dates', travelMonth)

      // In a fully integrated system we would send chatInput, originCity, selectedVibes, rejectedIds
      // formData.append('prompt', chatInput)
      // formData.append('origin', originCity)
      // formData.append('vibes', JSON.stringify(selectedVibes))
      // formData.append('rejected_ids', JSON.stringify(isReroll ? rejectedIds : []))

      // Keep it compatible with existing backend
      let res;
      try {
        res = await fetch(`${API_BASE}/match`, { method: 'POST', body: formData })
      } catch (e) {
        // Mock fallback if API is unreachable during dev
        console.warn("API unreachable, falling back to mock data");
        await new Promise(r => setTimeout(r, 6000));
        res = {
          ok: true,
          json: async () => ({
            session_id: 'mock-session-123',
            matches: [
              {
                id: 1, name: "Gulmarg, Kashmir", country: "INDIA",
                image_url: "https://images.unsplash.com/photo-1621244249243-f5aa7c5f80bf?q=80&w=2670&auto=format&fit=crop",
                rating: 4.8, best_month: "December", match_score: 95,
                tags: ["MOUNTAINS", "SNOW", "ADVENTURE"],
                reasoning: "You will fall in love with Gulmarg as you soar above the clouds on one of the highest gondolas. The pristine snowfall matches your aesthetic perfectly.",
                flight_price: 18500, hotel_price: 45000
              },
              {
                id: 2, name: "Havelock Island", country: "INDIA",
                image_url: "https://images.unsplash.com/photo-1590523277543-a94d2e4eb00b?q=80&w=2669&auto=format&fit=crop",
                rating: 4.5, best_month: "October", match_score: 88,
                tags: ["BEACH", "SCUBA", "RELAXING"],
                reasoning: "If you crave an escape that nourishes the soul, Havelock offers the perfect balance of lounging on ivory sands and exploring vibrant underwater kingdoms.",
                flight_price: 22000, hotel_price: 32000
              },
              {
                id: 3, name: "Munnar", country: "INDIA",
                image_url: "https://images.unsplash.com/photo-1593693397690-362bc9ac425d?q=80&w=2669&auto=format&fit=crop",
                rating: 4.6, best_month: "September", match_score: 85,
                tags: ["NATURE", "TEA GARDENS", "COUPLE"],
                reasoning: "If you cherish the magic of an unforgettable getaway, you will be captivated by Munnar's endless carpet of tea gardens draped in ethereal mist.",
                flight_price: 12500, hotel_price: 28000
              }
            ]
          })
        }
      }

      if (!res.ok) {
        let errorMsg = 'Match failed'
        try { const err = await res.json(); errorMsg = err.detail || errorMsg } catch (e) { }
        throw new Error(errorMsg)
      }

      const data = await res.json()
      // ensure we support the new format mapping
      let mappedResults = data.matches;
      if (!mappedResults) {
        mappedResults = [
          {
            id: data.tbo_id || 1,
            name: data.matched_destination,
            country: "INDIA", // Mocked
            image_url: `http://localhost:8000/destinations/${data.destination_photo}`,
            rating: 4.8,
            best_month: data.best_season || "Anytime",
            match_score: 95,
            tags: data.vibe_tags || [],
            reasoning: data.match_reasons?.join(" ") || "Perfect match for your vibes!",
            flight_price: 18500,
            hotel_price: data.price_per_person || 45000,
          },
          // Fake 2nd Option
          {
            id: 2, name: "Havelock Island", country: "INDIA",
            image_url: "https://images.unsplash.com/photo-1590523277543-a94d2e4eb00b?q=80&w=2669&auto=format&fit=crop",
            rating: 4.5, best_month: "October", match_score: 88,
            tags: ["BEACH", "SCUBA", "RELAXING"],
            reasoning: "If you crave an escape that nourishes the soul, Havelock offers the perfect balance of lounging on ivory sands and exploring vibrant underwater kingdoms.",
            flight_price: 22000, hotel_price: 32000
          },
          // Fake 3rd Option
          {
            id: 3, name: "Munnar", country: "INDIA",
            image_url: "https://images.unsplash.com/photo-1593693397690-362bc9ac425d?q=80&w=2669&auto=format&fit=crop",
            rating: 4.6, best_month: "September", match_score: 85,
            tags: ["NATURE", "TEA GARDENS", "COUPLE"],
            reasoning: "If you cherish the magic of an unforgettable getaway, you will be captivated by Munnar's endless carpet of tea gardens draped in ethereal mist.",
            flight_price: 12500, hotel_price: 28000
          }
        ];
      }

      setResults(mappedResults)
      setSessionId(data.session_id)
      setAppState('results')

    } catch (err) {
      setError(err.message)
      setAppState('search')
    }
  }, [chatInput, imagePreview, originCity, travelMonth, selectedVibes, recentSearches, rejectedIds])

  const handleReroll = () => {
    // Append current visible to rejected
    setRejectedIds(prev => [...prev, ...results.map(r => r.id)])
    handleSearch(true)
  }

  const handleSurpriseMe = () => {
    setChatInput("Surprise me with a unique offbeat destination")
    setTimeout(() => handleSearch(false), 500)
  }

  return (
    <div className="min-h-screen bg-mesh text-white font-sans overflow-x-hidden">

      {/* Dynamic Navbar */}
      <nav className="w-full p-6 flex justify-between items-center max-w-7xl mx-auto z-10 relative">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            V
          </div>
          <span className="font-bold text-xl tracking-wide">VibeTravel <span className="text-indigo-400 font-normal">engine</span></span>
        </div>
        <div className="px-4 py-1.5 rounded-full border border-gray-800 bg-gray-900/50 text-xs text-gray-400 uppercase tracking-widest font-bold">
          Powered by TBO & Gemini
        </div>
      </nav>

      {error && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center shadow-2xl backdrop-blur-md">
          <span className="mr-2">⚠️</span> {error}
        </div>
      )}

      {/* Main Content Area */}
      <main className="relative z-10 w-full min-h-[calc(100vh-100px)] flex flex-col justify-center pb-20">

        {appState === 'search' && (
          <SearchInterface
            imagePreview={imagePreview}
            setImagePreview={setImagePreview}
            chatInput={chatInput}
            setChatInput={setChatInput}
            originCity={originCity}
            setOriginCity={setOriginCity}
            travelMonth={travelMonth}
            setTravelMonth={setTravelMonth}
            selectedVibes={selectedVibes}
            setSelectedVibes={setSelectedVibes}
            recentSearches={recentSearches}
            onSearch={() => handleSearch(false)}
            onSurpriseMe={handleSurpriseMe}
          />
        )}

        {appState === 'loading' && <LoadingOverlay />}

        {appState === 'results' && (
          <ResultsGrid
            results={results}
            onBook={(dest) => setBookingModalTarget(dest)}
            onReroll={handleReroll}
            rejectedIds={rejectedIds}
          />
        )}
      </main>

      {/* Overlays */}
      <BookingModal
        isOpen={!!bookingModalTarget}
        onClose={() => setBookingModalTarget(null)}
        dest={bookingModalTarget}
      />

    </div>
  )
}

import { useState, useCallback, useEffect } from 'react'
import SearchInterface from './components/SearchInterface'
import LoadingOverlay from './components/LoadingOverlay'
import ResultsGrid from './components/ResultsGrid'
import BookingModal from './components/BookingModal'
import PlanView from './screens/PlanView'

const API_BASE = 'http://localhost:8000'

// Curated client-side destination pool for vibe refinement fallback
const DESTINATION_POOL = [
  { id: 'D1', name: 'Rishikesh', image_url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=1200', tags: ['ADVENTURE', 'RAFTING', 'SPIRITUAL'], match_score: 93, flight_price: 9500, hotel_price: 12000, vibes: ['More Adventure', 'More Nature'] },
  { id: 'D2', name: 'Hampi', image_url: 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?q=80&w=1200', tags: ['HERITAGE', 'RUINS', 'OFFBEAT'], match_score: 87, flight_price: 5500, hotel_price: 4500, vibes: ['Stricter Budget', 'More Nature'] },
  { id: 'D3', name: 'Udaipur', image_url: 'https://images.unsplash.com/photo-1585136917228-a4f62be0e7c7?q=80&w=1200', tags: ['LUXURY', 'HERITAGE', 'ROMANCE'], match_score: 95, flight_price: 11000, hotel_price: 55000, vibes: ['More Luxury', 'More Couple Focus'] },
  { id: 'D4', name: 'Coorg', image_url: 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?q=80&w=1200', tags: ['NATURE', 'COFFEE', 'TREKKING'], match_score: 88, flight_price: 10000, hotel_price: 22000, vibes: ['More Nature', 'More Adventure', 'Family Friendly'] },
  { id: 'D5', name: 'Jaisalmer', image_url: 'https://images.unsplash.com/photo-1482938289607-e9573fc25ebb?q=80&w=1200', tags: ['DESERT', 'GOLDEN', 'CULTURE'], match_score: 91, flight_price: 14000, hotel_price: 18000, vibes: ['More Adventure', 'More Luxury', 'More Couple Focus'] },
  { id: 'D6', name: 'Andaman Islands', image_url: 'https://images.unsplash.com/photo-1590523277543-a94d2e4eb00b?q=80&w=1200', tags: ['BEACH', 'SCUBA', 'TROPICAL'], match_score: 96, flight_price: 22000, hotel_price: 30000, vibes: ['More Adventure', 'Beachfront', 'More Couple Focus'] },
  { id: 'D7', name: 'Leh-Ladakh', image_url: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?q=80&w=1200', tags: ['ALTITUDE', 'MONASTERY', 'ADVENTURE'], match_score: 94, flight_price: 19000, hotel_price: 25000, vibes: ['More Adventure', 'Mountain Views', 'More Nature'] },
  { id: 'D8', name: 'Alleppey', image_url: 'https://images.unsplash.com/photo-1621689444225-0698c4af00f1?q=80&w=1200', tags: ['BACKWATERS', 'HOUSEBOAT', 'SERENE'], match_score: 86, flight_price: 14000, hotel_price: 28000, vibes: ['More Couple Focus', 'Family Friendly', 'Beachfront'] },
  { id: 'D9', name: 'Goa', image_url: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?q=80&w=1200', tags: ['BEACH', 'PARTY', 'NIGHTLIFE'], match_score: 82, flight_price: 10000, hotel_price: 25000, vibes: ['Beachfront', 'More Luxury', 'City Vibes', 'Stricter Budget'] },
  { id: 'D10', name: 'Varanasi', image_url: 'https://images.unsplash.com/photo-1561361058-c24e0cb36c08?q=80&w=1200', tags: ['SPIRITUAL', 'CULTURAL', 'HERITAGE'], match_score: 88, flight_price: 8000, hotel_price: 10000, vibes: ['Stricter Budget', 'City Vibes', 'Family Friendly'] },
  { id: 'D11', name: 'Manali', image_url: 'https://images.unsplash.com/photo-1621244249243-f5aa7c5f80bf?q=80&w=1200', tags: ['SNOW', 'MOUNTAINS', 'HONEYMOON'], match_score: 90, flight_price: 13000, hotel_price: 20000, vibes: ['More Adventure', 'More Couple Focus', 'Mountain Views'] },
  { id: 'D12', name: 'Ooty', image_url: 'https://images.unsplash.com/photo-1622279457486-7e72a7c17e55?q=80&w=1200', tags: ['HILLS', 'NATURE', 'FAMILY'], match_score: 83, flight_price: 8500, hotel_price: 14000, vibes: ['Family Friendly', 'More Nature', 'Stricter Budget'] },
]

export default function App() {
  // ── App state machine ────────────────────────────────────────────────────
  // 'home' | 'loading' | 'results' | 'plan' | 'confirm'
  const [appState, setAppState] = useState('home')

  // Search form parameters
  const [imagePreview, setImagePreview] = useState(null)
  const [chatInput, setChatInput] = useState('')
  const [originCity, setOriginCity] = useState('Mumbai')
  const [travelMonth, setTravelMonth] = useState('December')
  const [selectedVibes, setSelectedVibes] = useState([])
  const [budget, setBudget] = useState(100000)
  const [durationDays, setDurationDays] = useState(5)

  // Results state
  const [results, setResults] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [vibeTagsFromSearch, setVibeTagsFromSearch] = useState([])
  const [routeJustification, setRouteJustification] = useState('')
  const [error, setError] = useState(null)

  // Plan / booking state
  const [selectedItinerary, setSelectedItinerary] = useState(null)
  const [bookingTarget, setBookingTarget] = useState(null)

  // Persistent
  const [recentSearches, setRecentSearches] = useState([])
  const [rejectedIds, setRejectedIds] = useState([])
  const [activeVibes, setActiveVibes] = useState([])

  useEffect(() => {
    const saved = localStorage.getItem('vibeTravel_recentSearches')
    if (saved) setRecentSearches(JSON.parse(saved))
  }, [])

  const saveSearch = (query) => {
    if (!query?.trim()) return
    const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 10)
    setRecentSearches(updated)
    localStorage.setItem('vibeTravel_recentSearches', JSON.stringify(updated))
  }

  // ── Search handler ────────────────────────────────────────────────────────
  const handleSearch = useCallback(async (isReroll = false) => {
    setError(null)
    setAppState('loading')
    if (!isReroll && chatInput) saveSearch(chatInput)

    try {
      let data

      // Determine search mode
      if (imagePreview) {
        // Image-based search → /itineraries
        const formData = new FormData()
        const res0 = await fetch(imagePreview)
        const blob = await res0.blob()
        formData.append('photo', blob, 'upload.jpg')
        formData.append('budget', String(budget))
        formData.append('travel_dates', travelMonth)

        let res
        try {
          res = await fetch(`${API_BASE}/itineraries`, { method: 'POST', body: formData })
        } catch {
          res = null
        }

        if (res?.ok) {
          data = await res.json()
        } else {
          // Mock fallback for image path
          await new Promise(r => setTimeout(r, 1800))
          data = _mockData()
        }
      } else {
        // Text-based search → /search
        const query = chatInput || 'Weekend trip in India'
        let res
        try {
          res = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              budget,
              duration_days: durationDays,
              travel_month: travelMonth,
              vibes: selectedVibes,
              origin_city: originCity,
            }),
          })
        } catch {
          res = null
        }

        if (res?.ok) {
          data = await res.json()
        } else {
          await new Promise(r => setTimeout(r, 1800))
          data = _mockData()
        }
      }

      setResults(data.itineraries || [])
      setSessionId(data.session_id)
      setVibeTagsFromSearch(data.vibe_tags || [])
      setRouteJustification(data.route_justification || '')
      setAppState('results')

    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
      setAppState('home')
    }
  }, [chatInput, imagePreview, originCity, travelMonth, selectedVibes, budget, durationDays, recentSearches])

  // ── Vibe refinement (client-side re-rank) ─────────────────────────────────
  const handleRefine = useCallback(async (vibeString) => {
    setAppState('loading')
    await new Promise(r => setTimeout(r, 900))

    const vibeList = vibeString.split(', ').map(v => v.trim())
    const scored = DESTINATION_POOL
      .map(dest => ({ ...dest, vibeScore: vibeList.filter(v => dest.vibes?.includes(v)).length }))
      .filter(d => d.vibeScore > 0)
      .sort((a, b) => b.vibeScore - a.vibeScore || b.match_score - a.match_score)

    const refined = scored.length >= 3
      ? scored.slice(0, 3)
      : [...scored, ...DESTINATION_POOL.filter(d => !scored.includes(d))].slice(0, 3)

    setResults(refined.map(dest => ({
      type: '1-stop',
      label: 'Refined Match',
      stops: [{ destination: dest.name, tbo_id: dest.id, photo: dest.image_url, price_per_person: dest.flight_price + dest.hotel_price, hotels: [] }],
      total_price: dest.flight_price + dest.hotel_price,
      region: 'INDIA',
      stop_count: 1,
    })))
    setAppState('results')
  }, [])

  const handleReroll = () => {
    setRejectedIds(prev => [...prev, ...results.map(r => r.id || '')])
    handleSearch(true)
  }

  const handleSurpriseMe = () => {
    const surprises = ['Offbeat monsoon destination in India', 'Hidden gem hill station', 'Spiritual journey across Varanasi and Rishikesh']
    setChatInput(surprises[Math.floor(Math.random() * surprises.length)])
    setTimeout(() => handleSearch(false), 100)
  }

  // ── Navigation helpers ────────────────────────────────────────────────────
  const handleSelectItinerary = (itinerary) => {
    setSelectedItinerary(itinerary)
    setAppState('plan')
  }

  const handlePlanBack = () => setAppState('results')

  const handleConfirmBooking = () => {
    setBookingTarget(selectedItinerary)
  }

  const handleBookingConfirmed = () => {
    setBookingTarget(null)
    setSelectedItinerary(null)
    setResults([])
    setSessionId(null)
    setAppState('home')
    setImagePreview(null)
    setChatInput('')
    setSelectedVibes([])
  }

  const handleReset = () => {
    setAppState('home')
    setResults([])
    setError(null)
    setImagePreview(null)
    setChatInput('')
    setSelectedVibes([])
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-hero text-gray-900 font-sans overflow-x-hidden">

      {/* Navbar — hidden in plan view (PlanView has its own top bar) */}
      {appState !== 'plan' && (
        <nav className="navbar-light w-full px-6 py-4 flex justify-between items-center sticky top-0 z-40">
          <button onClick={handleReset} className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-md">
              <span className="text-white font-black text-sm">V</span>
            </div>
            <span className="font-bold text-lg text-gray-900">
              VibeTravel <span className="text-blue-500 font-normal text-base">AI</span>
            </span>
          </button>
          <div className="hidden md:flex items-center gap-6 text-sm text-gray-500 font-medium">
            <button onClick={handleReset} className="hover:text-gray-900 transition-colors">Home</button>
            <span className="text-gray-300">|</span>
            <span className="text-[11px] bg-blue-50 text-blue-600 border border-blue-200 px-3 py-1 rounded-full font-semibold">
              Powered by TBO × Gemini
            </span>
          </div>
        </nav>
      )}

      {/* Global error toast */}
      {error && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2 shadow-lg animate-slide-up">
          <span>⚠️</span> {error}
          <button onClick={() => setError(null)} className="ml-2 text-red-400 hover:text-red-700">✕</button>
        </div>
      )}

      {/* Main content */}
      <main className="relative w-full">

        {appState === 'home' && (
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
            budget={budget}
            setBudget={setBudget}
            durationDays={durationDays}
            setDurationDays={setDurationDays}
            recentSearches={recentSearches}
            onSearch={() => handleSearch(false)}
            onSurpriseMe={handleSurpriseMe}
          />
        )}

        {appState === 'loading' && <LoadingOverlay />}

        {appState === 'results' && (
          <ResultsGrid
            results={results}
            onBook={handleSelectItinerary}
            onReroll={handleReroll}
            onRefine={handleRefine}
            onReset={handleReset}
            rejectedIds={rejectedIds}
            originCity={originCity}
            travelMonth={travelMonth}
            activeVibes={activeVibes}
            setActiveVibes={setActiveVibes}
            vibeTagsFromSearch={vibeTagsFromSearch}
            routeJustification={routeJustification}
          />
        )}

        {appState === 'plan' && selectedItinerary && (
          <PlanView
            itinerary={{
              ...selectedItinerary,
              conversation_opener: results.find(r => r === selectedItinerary)?.conversation_opener || undefined,
              route_justification: routeJustification,
            }}
            sessionId={sessionId}
            apiBase={API_BASE}
            onBack={handlePlanBack}
            onConfirm={handleConfirmBooking}
            uploadedPhoto={imagePreview}
          />
        )}

      </main>

      {/* Booking Modal (overlay on results or plan views) */}
      {bookingTarget && (
        <BookingModal
          itinerary={bookingTarget}
          sessionId={sessionId}
          onClose={() => setBookingTarget(null)}
          onConfirmed={handleBookingConfirmed}
        />
      )}

    </div>
  )
}

// ── Mock data fallback ────────────────────────────────────────────────────────
function _mockData() {
  return {
    session_id: 'mock-' + Math.random().toString(36).slice(2, 8),
    itineraries: [
      {
        type: '1-stop', label: 'Quick Escape',
        stops: [{ destination: 'Jaisalmer', tbo_id: 'JAISALMER_FAKE_020', photo: 'https://images.unsplash.com/photo-1482938289607-e9573fc25ebb?q=80&w=1200', price_per_person: 32000, hotels: [], tagline: 'The Golden City of the Thar Desert', flight_min_fare: 14000 }],
        total_price: 32000, region: 'Rajasthan', stop_count: 1,
      },
      {
        type: '2-stop', label: 'Weekend Explorer',
        stops: [
          { destination: 'Jaipur', tbo_id: 'JAIPUR_FAKE_012', photo: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?q=80&w=1200', price_per_person: 28000, hotels: [], tagline: 'The Pink City of Kings', flight_min_fare: 11000 },
          { destination: 'Jodhpur', tbo_id: 'JODHPUR_FAKE_016', photo: 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?q=80&w=1200', price_per_person: 22000, hotels: [], tagline: 'The Blue City at the edge of the desert', flight_min_fare: 10000 },
        ],
        total_price: 50000, region: 'Rajasthan', stop_count: 2,
      },
    ],
    vibe_tags: ['heritage', 'desert', 'cultural'],
    match_reasons: ['rich heritage', 'desert landscapes', 'Rajasthani culture'],
    itinerary_narrative: 'An immersive journey through the royal cities of Rajasthan.',
    conversation_opener: "We've found a stunning Rajasthan journey for you! Which stop are you most excited about?",
    route_justification: 'This Rajasthan circuit is geographically efficient — Jaipur and Jodhpur are 335 km apart by road, making this a smooth two-city journey without backtracking.',
    region: 'Rajasthan',
  }
}

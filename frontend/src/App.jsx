import { useState, useCallback, useEffect } from 'react'
import SearchInterface from './components/SearchInterface'
import LoadingOverlay from './components/LoadingOverlay'
import ResultsGrid from './components/ResultsGrid'
import BookingModal from './components/BookingModal'

const API_BASE = 'http://localhost:8000'

// Curated destination pool for client-side vibe refinement
const DESTINATION_POOL = [
  { id: 'D1', name: 'Rishikesh', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2670&auto=format&fit=crop', tags: ['ADVENTURE', 'RAFTING', 'SPIRITUAL'], match_score: 93, reasoning: 'The Adventure Capital of India. Bungee jumping, white-water rafting and yoga on the banks of the Ganges.', flight_price: 9500, hotel_price: 12000, best_month: 'September', rating: 4.6, vibes: ['More Adventure', 'More Nature'] },
  { id: 'D2', name: 'Hampi', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?q=80&w=2666&auto=format&fit=crop', tags: ['HERITAGE', 'RUINS', 'OFFBEAT'], match_score: 87, reasoning: 'Ancient Vijayanagara Empire ruins scattered among dramatic boulder landscapes. Ultra budget-friendly with hostels from ₹500/night.', flight_price: 5500, hotel_price: 4500, best_month: 'February', rating: 4.5, vibes: ['Stricter Budget', 'More Nature'] },
  { id: 'D3', name: 'Udaipur', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1585136917228-a4f62be0e7c7?q=80&w=2670&auto=format&fit=crop', tags: ['LUXURY', 'HERITAGE', 'ROMANCE'], match_score: 95, reasoning: 'The City of Lakes. Palatial hotels on shimmering water, hand-embroidered Rajasthani textiles, and magical sunset boat rides.', flight_price: 11000, hotel_price: 55000, best_month: 'November', rating: 4.9, vibes: ['More Luxury', 'More Couple Focus'] },
  { id: 'D4', name: 'Coorg', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?q=80&w=2670&auto=format&fit=crop', tags: ['NATURE', 'COFFEE', 'TREKKING'], match_score: 88, reasoning: 'The Scotland of India. Misty coffee plantations, cascading waterfalls, and lush green hills perfect for family escapes.', flight_price: 10000, hotel_price: 22000, best_month: 'October', rating: 4.7, vibes: ['More Nature', 'More Adventure', 'Family Friendly'] },
  { id: 'D5', name: 'Jaisalmer', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1482938289607-e9573fc25ebb?q=80&w=2672&auto=format&fit=crop', tags: ['DESERT', 'GOLDEN', 'CULTURE'], match_score: 91, reasoning: 'The Golden City rising from the Thar Desert. Camel safaris at dusk and folk musicians in ancient sandstone havelis.', flight_price: 14000, hotel_price: 18000, best_month: 'December', rating: 4.8, vibes: ['More Adventure', 'More Luxury', 'More Couple Focus'] },
  { id: 'D6', name: 'Andaman Islands', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1590523277543-a94d2e4eb00b?q=80&w=2669&auto=format&fit=crop', tags: ['BEACH', 'SCUBA', 'TROPICAL'], match_score: 96, reasoning: 'Crystal-clear turquoise waters and pristine coral reefs. World-class SCUBA diving at Havelock Island.', flight_price: 22000, hotel_price: 30000, best_month: 'November', rating: 4.8, vibes: ['More Adventure', 'Beachfront', 'More Couple Focus'] },
  { id: 'D7', name: 'Leh-Ladakh', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?q=80&w=2670&auto=format&fit=crop', tags: ['ALTITUDE', 'MONASTERY', 'ADVENTURE'], match_score: 94, reasoning: 'The roof of the world. Dramatic high-altitude deserts, ancient monasteries and Pangong Lake at 14,000 ft.', flight_price: 19000, hotel_price: 25000, best_month: 'August', rating: 4.9, vibes: ['More Adventure', 'Mountain Views', 'More Nature'] },
  { id: 'D8', name: 'Alleppey', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1621689444225-0698c4af00f1?q=80&w=2670&auto=format&fit=crop', tags: ['BACKWATERS', 'HOUSEBOAT', 'SERENE'], match_score: 86, reasoning: 'The Venice of the East. Float through emerald Kerala backwaters on a traditional houseboat with your family or partner.', flight_price: 14000, hotel_price: 28000, best_month: 'August', rating: 4.7, vibes: ['More Couple Focus', 'Family Friendly', 'Beachfront'] },
  { id: 'D9', name: 'Goa', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?q=80&w=2674&auto=format&fit=crop', tags: ['BEACH', 'PARTY', 'NIGHTLIFE'], match_score: 82, reasoning: 'Sun-soaked beaches, world-class beach shacks and an electric nightlife scene. Great value for money.', flight_price: 10000, hotel_price: 25000, best_month: 'December', rating: 4.4, vibes: ['Beachfront', 'More Luxury', 'City Vibes', 'Stricter Budget'] },
  { id: 'D10', name: 'Varanasi', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1561361058-c24e0cb36c08?q=80&w=2684&auto=format&fit=crop', tags: ['SPIRITUAL', 'CULTURAL', 'HERITAGE'], match_score: 88, reasoning: 'One of the oldest living cities on Earth. The nightly Ganga Aarti ceremony is a once-in-a-lifetime spectacle.', flight_price: 8000, hotel_price: 10000, best_month: 'November', rating: 4.5, vibes: ['Stricter Budget', 'City Vibes', 'Family Friendly'] },
  { id: 'D11', name: 'Manali', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1621244249243-f5aa7c5f80bf?q=80&w=2670&auto=format&fit=crop', tags: ['SNOW', 'MOUNTAINS', 'HONEYMOON'], match_score: 90, reasoning: 'Snow-capped Himalayan peaks, apple orchards, and the iconic Rohtang Pass. Perfect for couples and thrill-seekers.', flight_price: 13000, hotel_price: 20000, best_month: 'January', rating: 4.6, vibes: ['More Adventure', 'More Couple Focus', 'Mountain Views'] },
  { id: 'D12', name: 'Ooty', country: 'INDIA', image_url: 'https://images.unsplash.com/photo-1622279457486-7e72a7c17e55?q=80&w=2670&auto=format&fit=crop', tags: ['HILLS', 'NATURE', 'FAMILY'], match_score: 83, reasoning: 'The Queen of Hill Stations. The Nilgiri Mountain Railway and fragrant eucalyptus forests make this the perfect family retreat.', flight_price: 8500, hotel_price: 14000, best_month: 'May', rating: 4.5, vibes: ['Family Friendly', 'More Nature', 'Stricter Budget'] },
]

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
  const [activeVibes, setActiveVibes] = useState([])

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
    const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 10)
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
            match_score: data.similarity_score ? Math.round(data.similarity_score * 100) : 62,
            tags: data.vibe_tags || [],
            reasoning: data.match_reasons?.join(" ") || "Perfect match for your vibes!",
            flight_price: 18500,
            hotel_price: data.price_per_person || 45000,
          },
          // Fake 2nd Option
          {
            id: 2, name: "Havelock Island", country: "INDIA",
            image_url: "https://images.unsplash.com/photo-1590523277543-a94d2e4eb00b?q=80&w=2669&auto=format&fit=crop",
            rating: 4.5, best_month: "October", match_score: 54,
            tags: ["BEACH", "SCUBA", "RELAXING"],
            reasoning: "If you crave an escape that nourishes the soul, Havelock offers the perfect balance of lounging on ivory sands and exploring vibrant underwater kingdoms.",
            flight_price: 22000, hotel_price: 32000
          },
          // Fake 3rd Option
          {
            id: 3, name: "Munnar", country: "INDIA",
            image_url: "https://images.unsplash.com/photo-1593693397690-362bc9ac425d?q=80&w=2669&auto=format&fit=crop",
            rating: 4.6, best_month: "September", match_score: 41,
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

  const handleRefine = async (vibeString) => {
    setAppState('loading')
    await new Promise(r => setTimeout(r, 1400)) // Simulate AI re-ranking

    const vibeList = vibeString.split(', ').map(v => v.trim())

    // Score each destination by how many selected vibes it matches
    const scored = DESTINATION_POOL
      .map(dest => ({
        ...dest,
        vibeScore: vibeList.filter(v => dest.vibes?.includes(v)).length
      }))
      .filter(d => d.vibeScore > 0)
      .sort((a, b) => b.vibeScore - a.vibeScore || b.match_score - a.match_score)

    const refined = scored.length >= 3
      ? scored.slice(0, 3)
      : [...scored, ...DESTINATION_POOL.filter(d => !scored.includes(d))].slice(0, 3)

    setResults(refined)
    setAppState('results')
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
            onRefine={handleRefine}
            rejectedIds={rejectedIds}
            originCity={originCity}
            travelMonth={travelMonth}
            activeVibes={activeVibes}
            setActiveVibes={setActiveVibes}
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

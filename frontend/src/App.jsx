import { useState, useCallback } from 'react'
import UploadScreen from './screens/UploadScreen'
import LoadingScreen from './screens/LoadingScreen'
import MatchChatScreen from './screens/MatchChatScreen'
import BookingScreen from './screens/BookingScreen'

const API_BASE = ''

export default function App() {
  const [screen, setScreen] = useState('upload') // 'upload' | 'loading' | 'match' | 'booking'
  const [matchData, setMatchData] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [uploadedPhoto, setUploadedPhoto] = useState(null)
  const [bookingData, setBookingData] = useState(null)
  const [error, setError] = useState(null)

  const handleFindMatch = useCallback(async ({ photo, budget, travelDates }) => {
    setError(null)
    setScreen('loading')
    setUploadedPhoto(URL.createObjectURL(photo))

    const formData = new FormData()
    formData.append('photo', photo)
    formData.append('budget', budget)
    if (travelDates) formData.append('travel_dates', travelDates)

    try {
      const res = await fetch(`${API_BASE}/match`, { method: 'POST', body: formData })
      if (!res.ok) {
        let errorMsg = 'Match failed'
        try {
          const err = await res.json()
          errorMsg = err.detail || errorMsg
        } catch (parseErr) {
          // If the response is not valid JSON (e.g. 500 Internal Server Error HTML)
          errorMsg = `Server error: ${res.status} ${res.statusText}`
        }
        throw new Error(errorMsg)
      }
      const data = await res.json()
      setMatchData(data)
      setSessionId(data.session_id)
      setScreen('match')
    } catch (err) {
      setError(err.message)
      setScreen('upload')
    }
  }, [])

  const handleSendMessage = useCallback(async (message) => {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
    })
    if (!res.ok) throw new Error('Chat failed')
    return res.json()
  }, [sessionId])

  const handleConfirm = useCallback(async () => {
    const res = await fetch(`${API_BASE}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    })
    if (!res.ok) throw new Error('Confirm failed')
    const data = await res.json()
    setBookingData(data)
    setScreen('booking')
  }, [sessionId])

  return (
    <div className="min-h-screen bg-mesh">
      {error && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl bg-red-500/20 border border-red-500/40 text-red-300 text-sm animate-fade-in">
          ⚠️ {error}
        </div>
      )}

      {screen === 'upload' && (
        <UploadScreen onFindMatch={handleFindMatch} />
      )}
      {screen === 'loading' && (
        <LoadingScreen uploadedPhoto={uploadedPhoto} />
      )}
      {screen === 'match' && matchData && (
        <MatchChatScreen
          matchData={matchData}
          uploadedPhoto={uploadedPhoto}
          onSendMessage={handleSendMessage}
          onConfirm={handleConfirm}
          apiBase={API_BASE}
        />
      )}
      {screen === 'booking' && bookingData && (
        <BookingScreen
          bookingData={bookingData}
          apiBase={API_BASE}
        />
      )}
    </div>
  )
}

/**
 * fallbackFlights.js — Fallback flight data when TBO API data is unavailable
 */

export const FALLBACK_FLIGHTS = {
    "Goa": { from: "DEL", to: "GOI", price: 6500, airline: "IndiGo", duration: "2h 30m" },
    "Jaipur": { from: "DEL", to: "JAI", price: 4500, airline: "IndiGo", duration: "1h 10m" },
    "Manali": { from: "DEL", to: "KUU", price: 5500, airline: "Alliance", duration: "1h 30m" },
    "Varanasi": { from: "DEL", to: "VNS", price: 5000, airline: "IndiGo", duration: "1h 40m" },
    "Andaman Islands": { from: "DEL", to: "IXZ", price: 12000, airline: "Air India", duration: "3h 45m" },
    "Udaipur": { from: "DEL", to: "UDR", price: 5500, airline: "IndiGo", duration: "1h 25m" },
    // Extended fallbacks for other destinations
    "Kovalam": { from: "DEL", to: "TRV", price: 7000, airline: "IndiGo", duration: "3h 00m" },
    "Jodhpur": { from: "DEL", to: "JDH", price: 5000, airline: "SpiceJet", duration: "1h 30m" },
    "Jaisalmer": { from: "DEL", to: "JSA", price: 6000, airline: "SpiceJet", duration: "1h 45m" },
    "Shimla": { from: "DEL", to: "SLV", price: 5000, airline: "Alliance", duration: "1h 15m" },
    "Darjeeling": { from: "DEL", to: "IXB", price: 7500, airline: "IndiGo", duration: "2h 15m" },
    "Rishikesh": { from: "DEL", to: "DED", price: 4000, airline: "SpiceJet", duration: "1h 00m" },
}

/**
 * Get flight data for a destination. Returns a default if unknown.
 */
export function getFlightData(destination) {
    return FALLBACK_FLIGHTS[destination] || { from: "DEL", to: "???", price: 8000, airline: "IndiGo", duration: "2h 00m" }
}

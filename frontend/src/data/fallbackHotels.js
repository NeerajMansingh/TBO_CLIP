/**
 * fallbackHotels.js — Fallback hotel data when TBO API is slow/missing
 */

export const FALLBACK_HOTELS = {
    "Goa": {
        budget: { name: "Zostel Goa", stars: 2, price_night: 1200, image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400" },
        midrange: { name: "Cidade de Goa", stars: 4, price_night: 4500, image: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400" },
        premium: { name: "Taj Holiday Village", stars: 5, price_night: 12000, image: "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400" },
    },
    "Jaipur": {
        budget: { name: "Zostel Jaipur", stars: 2, price_night: 900, image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400" },
        midrange: { name: "Hotel Sarang Palace", stars: 3, price_night: 3500, image: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400" },
        premium: { name: "Rambagh Palace", stars: 5, price_night: 25000, image: "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400" },
    },
    "Manali": {
        budget: { name: "Hosteller Manali", stars: 2, price_night: 800, image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400" },
        midrange: { name: "Johnson Lodge", stars: 3, price_night: 3000, image: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400" },
        premium: { name: "Span Resort & Spa", stars: 4, price_night: 8000, image: "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400" },
    },
    "Varanasi": {
        budget: { name: "Zostel Varanasi", stars: 2, price_night: 700, image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400" },
        midrange: { name: "BrijRama Palace", stars: 4, price_night: 5000, image: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400" },
        premium: { name: "Taj Nadesar Palace", stars: 5, price_night: 18000, image: "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400" },
    },
    "Andaman Islands": {
        budget: { name: "TSG Blue Resort", stars: 2, price_night: 1500, image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400" },
        midrange: { name: "SeaShell Havelock", stars: 3, price_night: 5500, image: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400" },
        premium: { name: "Taj Exotica", stars: 5, price_night: 15000, image: "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400" },
    },
    "Udaipur": {
        budget: { name: "Bunkyard Hostel", stars: 2, price_night: 800, image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400" },
        midrange: { name: "Amet Haveli", stars: 3, price_night: 4000, image: "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400" },
        premium: { name: "Oberoi Udaivilas", stars: 5, price_night: 30000, image: "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400" },
    },
}

/**
 * Get the best fallback hotel for a destination based on travel style.
 * @param {string} destination - Destination name
 * @param {number[]} hotelStars - Preferred star ratings from travel style
 * @returns {object} Hotel info object
 */
export function getFallbackHotel(destination, hotelStars = [3, 4]) {
    const hotels = FALLBACK_HOTELS[destination]
    if (!hotels) {
        return { name: "Standard Hotel", stars: 3, price_night: 3000, image: "" }
    }
    const maxStar = Math.max(...hotelStars)
    if (maxStar >= 5) return hotels.premium
    if (maxStar >= 3) return hotels.midrange
    return hotels.budget
}

/**
 * travelStyles.js — Travel Style Presets for VibeTravel
 */

export const TRAVEL_STYLES = [
    {
        id: "backpacker",
        label: "Backpacker",
        emoji: "🎒",
        tagline: "Maximum experiences, minimum spend",
        budget_multiplier: 0.6,
        hotel_stars: [1, 2, 3],
        transport: "shared",
        activities_per_day: 3,
        description: "Hostels, local transport, street food",
        color: "#26de81",
    },
    {
        id: "balanced",
        label: "Balanced Explorer",
        emoji: "🧳",
        tagline: "Best of both worlds",
        budget_multiplier: 1.0,
        hotel_stars: [3, 4],
        transport: "shared+private mix",
        activities_per_day: 2,
        description: "Mid-range hotels, mix of activities, some fine dining",
        color: "#4FC3F7",
    },
    {
        id: "comfort",
        label: "Comfort Traveller",
        emoji: "✈️",
        tagline: "Travel well, rest better",
        budget_multiplier: 1.5,
        hotel_stars: [4],
        transport: "private",
        activities_per_day: 2,
        description: "4-star hotels, private transfers, curated experiences",
        color: "#A55EEA",
    },
    {
        id: "luxury",
        label: "Luxury",
        emoji: "💎",
        tagline: "Only the finest",
        budget_multiplier: 2.5,
        hotel_stars: [5],
        transport: "private+premium",
        activities_per_day: 2,
        description: "5-star resorts, exclusive experiences, personal concierge",
        color: "#F7B731",
    },
]

/**
 * Given a budget, return which style should be recommended.
 * We pick the style whose multiplied cost is closest to 85% of budget (leaves buffer).
 */
export function getRecommendedStyle(budget) {
    const target = budget * 0.85
    let best = "balanced"
    let minDiff = Infinity
    for (const style of TRAVEL_STYLES) {
        const estimated = budget * style.budget_multiplier
        const diff = Math.abs(estimated - target)
        if (diff < minDiff && estimated <= budget * 1.2) {
            minDiff = diff
            best = style.id
        }
    }
    return best
}

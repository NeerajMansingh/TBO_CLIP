/**
 * vibeTagMap.js — Maps CLIP vibe tags to activity tags
 * Used to auto-pre-select "Top Picks" in ActivityDiscovery
 */

export const VIBE_TAG_MAP = {
    "beachy": ["beach", "water", "sunset"],
    "adventurous": ["thrill", "outdoor", "hiking"],
    "romantic": ["sunset", "romantic", "cruise"],
    "cultural": ["culture", "history", "architecture"],
    "foodie": ["food", "local"],
    "mountainous": ["nature", "hiking", "outdoor", "mountain"],
    "spiritual": ["culture", "history", "spiritual"],
    "luxury": ["exclusive", "fine-dining", "premium"],
    "peaceful": ["wellness", "nature", "beach"],
    "vibrant": ["nightlife", "music", "party"],
    "chill": ["nature", "sunset", "romantic"],
    "historic": ["history", "architecture", "culture"],
    "nature": ["nature", "outdoor", "hiking", "waterfall"],
    "urban": ["shopping", "nightlife", "food"],
    "wildlife": ["nature", "wildlife", "outdoor"],
    "desert": ["outdoor", "culture", "thrill"],
    "snowy": ["mountain", "outdoor", "thrill"],
    "forest": ["nature", "hiking", "outdoor"],
    "family-friendly": ["nature", "culture", "food"],
    "solo-traveler": ["thrill", "outdoor", "local"],
    "architecture": ["architecture", "history", "culture"],
}

/**
 * Given a list of CLIP vibe strings, return the merged set of relevant activity tags.
 */
export function getRelevantTags(vibes = []) {
    const tagSet = new Set()
    for (const vibe of vibes) {
        const key = vibe.toLowerCase().replace(/\s+/g, '')
        const mapped = VIBE_TAG_MAP[key] || VIBE_TAG_MAP[vibe.toLowerCase()]
        if (mapped) {
            mapped.forEach(t => tagSet.add(t))
        }
    }
    return [...tagSet]
}

/**
 * Score an activity against a list of relevant tags. Returns 0-1.
 */
export function vibeMatchScore(activity, relevantTags) {
    if (!relevantTags.length) return 0
    const matched = activity.tags.filter(t => relevantTags.includes(t)).length
    return matched / relevantTags.length
}

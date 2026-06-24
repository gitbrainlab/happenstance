/*
 * Inferred Happenstance data shapes from docs/events.json,
 * docs/restaurants.json, and docs/meta.json.
 *
 * interface Coordinates {
 *   lat: number;
 *   lng: number;
 * }
 *
 * interface Event {
 *   id: string;
 *   name: string;
 *   title?: string;
 *   category: string;
 *   date: string;
 *   time?: string;
 *   venue: string;
 *   location: string | Coordinates;
 *   coordinates?: Coordinates;
 *   coords?: Coordinates;
 *   url: string;
 *   source_url?: string;
 *   description?: string;
 *   duration_minutes?: number;
 *   tags?: string[];
 *   neighborhood?: string;
 *   _type?: "event";
 * }
 *
 * interface Restaurant {
 *   id: string;
 *   name: string;
 *   cuisine: string;
 *   address: string;
 *   location?: Coordinates;
 *   coords?: Coordinates;
 *   url: string;
 *   match_reason?: string;
 *   description?: string;
 *   rating?: number;
 *   price_level?: number;
 *   hours?: string | string[] | Record<string, string>;
 *   tags?: string[];
 *   neighborhood?: string;
 *   _type?: "restaurant";
 * }
 *
 * interface Pairing {
 *   event_id: string;
 *   restaurant_id: string;
 *   event: string;
 *   restaurant: string;
 *   score?: number;
 *   reason?: string;
 *   match_reason?: string;
 *   event_url?: string;
 *   restaurant_url?: string;
 *   event_date?: string;
 *   event_location?: string;
 *   distance_miles?: number;
 *   distance_km?: number;
 *   walk_minutes?: number;
 * }
 */

(() => {
  "use strict";

  const MAX_BLURB_WORDS = 40;

  const PREFERENCE_CHIPS = [
    {
      id: "art-culture",
      label: "Art & Culture",
      prompt: "art, theater, museums, ballet, galleries",
    },
    {
      id: "date-night",
      label: "Date night",
      prompt: "higher-rated, slower-paced evening stops",
    },
    {
      id: "family-teens",
      label: "Family with teens",
      prompt: "casual food and teen-friendly shows",
    },
    {
      id: "vegan-friendly",
      label: "Vegan-friendly",
      prompt: "records that explicitly mention vegan or vegetarian",
    },
    {
      id: "close-walk",
      label: "Close walk",
      prompt: "nearby places and short event-to-restaurant walks",
    },
    {
      id: "live-music",
      label: "Live music mood",
      prompt: "concerts, classical, rock, and music nights",
    },
  ];

  function generatePairingBlurb({ pairing = {}, event = {}, restaurant = {} } = {}) {
    const eventName = safeText(event.name || event.title || pairing.event, "This event");
    const restaurantName = safeText(restaurant.name || pairing.restaurant, "this spot");
    const venue = safeText(event.venue || pairing.event_location, "");
    const cuisine = safeText(restaurant.cuisine, "");
    const area = safeText(restaurant.neighborhood || event.neighborhood, "");
    const walk = Number(pairing.walk_minutes);
    const miles = Number(pairing.distance_miles);
    const reason = safeText(pairing.reason || pairing.match_reason, "");
    const category = safeText(event.category, "").toLowerCase();

    const intro = venue
      ? `${eventName} puts you at ${venue}`
      : `${eventName} gives you a clear anchor`;
    const dining = cuisine
      ? `${restaurantName} keeps the next stop ${cuisine.toLowerCase()}`
      : `${restaurantName} is the nearby next stop`;
    const place = area ? ` in ${area}` : "";
    const distance = Number.isFinite(walk) && walk <= 40
      ? `, about a ${walk}-minute walk.`
      : Number.isFinite(miles) && miles <= 5
        ? `, ${formatMiles(miles)} from the venue.`
        : ".";
    const vibe = vibeClause(category, cuisine, reason);

    return limitWords(`${intro}; ${dining}${place}${vibe}${distance}`, MAX_BLURB_WORDS);
  }

  function scoreItemForPreferences(item = {}, selected = [], context = {}) {
    return selected.reduce((total, id) => total + scorePreference(id, { item, context }), 0);
  }

  function scorePairingForPreferences(pairing = {}, event = {}, restaurant = {}, selected = []) {
    return selected.reduce((total, id) => total + scorePreference(id, { pairing, event, restaurant }), 0);
  }

  function matchingPreferenceLabels(item = {}, selected = [], context = {}) {
    return selected
      .filter((id) => scorePreference(id, { item, context }) > 0)
      .map((id) => PREFERENCE_CHIPS.find((chip) => chip.id === id))
      .filter(Boolean)
      .map((chip) => chip.label);
  }

  function matchingPairingPreferenceLabels(pairing = {}, event = {}, restaurant = {}, selected = []) {
    return selected
      .filter((id) => scorePreference(id, { pairing, event, restaurant }) > 0)
      .map((id) => PREFERENCE_CHIPS.find((chip) => chip.id === id))
      .filter(Boolean)
      .map((chip) => chip.label);
  }

  function wordCount(text) {
    return String(text || "").trim().split(/\s+/).filter(Boolean).length;
  }

  function scorePreference(id, payload) {
    const item = payload.item || {};
    const event = payload.event || (item._type === "event" ? item : {});
    const restaurant = payload.restaurant || (item._type === "restaurant" ? item : {});
    const pairing = payload.pairing || {};
    const context = payload.context || {};
    const eventText = searchableText(event);
    const restaurantText = searchableText(restaurant);
    const itemText = searchableText(item);
    const eventHour = eventStartHour(event);
    const rating = Number(restaurant.rating || item.rating || 0);
    const price = Number(restaurant.price_level || item.price_level || 0);
    const distanceMiles = Number(pairing.distance_miles ?? context.distanceMiles);

    if (id === "art-culture") {
      return (
        hasAny(eventText || itemText, ["art", "gallery", "museum", "theater", "theatre", "ballet", "exhibition"]) ? 12 : 0
      ) + (hasAny(restaurantText, ["wine", "bistro", "osteria", "cafe"]) ? 3 : 0);
    }

    if (id === "date-night") {
      return (
        (rating >= 4.6 ? 5 : 0) +
        (price >= 3 ? 4 : 0) +
        (eventHour >= 17 ? 3 : 0) +
        (hasAny(restaurantText, ["bistro", "osteria", "wine", "sushi", "fine dining", "cocktails"]) ? 4 : 0)
      );
    }

    if (id === "family-teens") {
      return (
        (hasAny(eventText || itemText, ["family", "free", "festival", "theater", "theatre", "concert"]) ? 6 : 0) +
        (price > 0 && price <= 2 ? 4 : 0) +
        (hasAny(restaurantText || itemText, ["pizza", "bbq", "bar-b-que", "mexican", "asian", "chinese", "american"]) ? 4 : 0)
      );
    }

    if (id === "vegan-friendly") {
      return hasAny(restaurantText || itemText, ["vegan", "vegetarian"]) ? 12 : 0;
    }

    if (id === "close-walk") {
      if (Number.isFinite(distanceMiles)) {
        if (distanceMiles <= 0.75) return 12;
        if (distanceMiles <= 1.5) return 8;
        if (distanceMiles <= 3) return 4;
      }
      return 0;
    }

    if (id === "live-music") {
      return hasAny(eventText || itemText, ["live music", "concert", "music", "rock", "classical", "jazz", "afrobeats"]) ? 12 : 0;
    }

    return 0;
  }

  function vibeClause(category, cuisine, reason) {
    if (/art|theater|theatre|museum|gallery|ballet/.test(`${category} ${reason}`.toLowerCase()) && cuisine) {
      return " without turning it into a production";
    }
    if (/live music|concert|music|rock|classical|jazz/.test(`${category} ${reason}`.toLowerCase()) && cuisine) {
      return " before or after the show";
    }
    return "";
  }

  function limitWords(text, maxWords) {
    const words = String(text || "").replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
    if (words.length <= maxWords) return words.join(" ");
    return `${words.slice(0, maxWords - 1).join(" ")}.`;
  }

  function searchableText(item) {
    return [
      item.name,
      item.title,
      item.category,
      item.cuisine,
      item.address,
      item.venue,
      item.location,
      item.neighborhood,
      item.description,
      item.match_reason,
      ...(Array.isArray(item.tags) ? item.tags : []),
    ]
      .filter((value) => value && typeof value !== "object")
      .join(" ")
      .toLowerCase();
  }

  function hasAny(text, needles) {
    return needles.some((needle) => String(text || "").includes(needle));
  }

  function eventStartHour(event) {
    const time = String(event.time || event.date || "");
    const match = time.match(/(?:T)?(\d{1,2}):(\d{2})/);
    return match ? Number(match[1]) : NaN;
  }

  function formatMiles(miles) {
    return `${miles.toFixed(miles < 10 ? 1 : 0)} mi`;
  }

  function safeText(value, fallback = "") {
    const text = value === null || value === undefined ? "" : String(value).trim();
    return text || fallback;
  }

  window.HappenstancePairingInsights = {
    PREFERENCE_CHIPS,
    generatePairingBlurb,
    matchingPairingPreferenceLabels,
    matchingPreferenceLabels,
    scoreItemForPreferences,
    scorePairingForPreferences,
    wordCount,
  };
})();

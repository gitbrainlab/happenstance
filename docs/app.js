/**
 * Happenstance v2 — app.js
 *
 * Major changes from v1:
 * - Bottom tab navigation (Explore / Timeline / Plan / Saved)
 * - Mobile-first dense list rows with compact/comfortable toggle
 * - Sticky filter panel with chip-based filters (open now, closing soon, nearby, price, rating)
 * - Inline bottom sheet for item detail (replaces full-page detail view)
 * - Plan view: multi-item itinerary builder with live distance, conflict detection,
 *   and pairing suggestions pulled from meta.json pairings data
 * - Timeline view: chronological display of events + restaurant hours across the week
 * - Saved view: localStorage-backed favorites with one-tap plan addition
 * - Pairing context shown lightly in Explore rows (max 2 pills, never dominates)
 * - Haversine distance calculation from simulated/real user location
 * - All state managed in a single `state` object; UI is a pure function of state
 */

(() => {
  "use strict";

  const STORAGE_KEYS = {
    saved: "hs_saved",
    density: "hs_density",
    view: "hs_view",
    target: "hs_target",
  };

  const KM_PER_MILE = 1.609344;
  const NEARBY_MILES = 1;

  const state = {
    view: "explore",
    filtersOpen: false,
    densityMode: "compact",
    filters: {
      openNow: false,
      closingSoon: false,
      nearby: false,
      price: null,
      minRating: null,
      type: "all",
      sortBy: "default",
    },
    searchQuery: "",
    targetQuery: "",
    targetAreaName: "",
    targetLocation: null,
    userLocation: null,
    data: {
      restaurants: [],
      events: [],
      pairings: [],
      clusters: [],
      targetAreas: [],
      meta: {},
      branding: {},
    },
    plan: [],
    saved: [],
    activeSheet: null,
    loading: true,
    error: null,
  };

  const els = {
    root: document.getElementById("view-root"),
    title: document.getElementById("app-title"),
    filterToggle: document.getElementById("filter-toggle"),
    tabs: Array.from(document.querySelectorAll("[data-view]")),
  };

  const dragState = {
    from: null,
    touchFrom: null,
    touchOver: null,
  };

  // DATA
  async function fetchAllData() {
    state.loading = true;
    state.error = null;
    render();

    try {
      const [restaurantsResp, eventsResp, configResp, metaResp] = await Promise.all([
        fetch("restaurants.json"),
        fetch("events.json"),
        fetch("config.json"),
        fetch("meta.json"),
      ]);

      [restaurantsResp, eventsResp, configResp, metaResp].forEach((resp) => {
        if (!resp.ok) throw new Error(`Could not load ${resp.url.split("/").pop()}`);
      });

      const [restaurantsRaw, eventsRaw, config, meta] = await Promise.all([
        restaurantsResp.json(),
        eventsResp.json(),
        configResp.json(),
        metaResp.json(),
      ]);

      const cleanRestaurants = stripMeta(asArray(restaurantsRaw));
      const cleanEvents = stripMeta(asArray(eventsRaw));
      const cleanMeta = meta && typeof meta === "object" ? meta : {};

      state.data.restaurants = cleanRestaurants.map(normalizeRestaurant);
      state.data.events = cleanEvents.map(normalizeEvent);
      state.data.pairings = asArray(cleanMeta.pairings);
      state.data.clusters = asArray(cleanMeta.clusters);
      state.data.targetAreas = asArray(cleanMeta.target_areas);
      state.data.meta = cleanMeta;
      state.data.branding = {
        ...(cleanMeta.branding || {}),
        ...((config && config.branding) || {}),
      };
      applyInitialTarget();
      state.loading = false;
      state.error = null;
      applyBranding();
      render();
      document.body.setAttribute("data-hs-ready", "1");
    } catch (err) {
      state.loading = false;
      state.error = err && err.message ? err.message : "Unable to load data";
      render();
      document.body.setAttribute("data-hs-ready", "error");
      console.error("Failed to load Happenstance data", err);
    }
  }

  function getItem(type, id) {
    const list = type === "event" ? state.data.events : state.data.restaurants;
    return list.find((item) => item.id === id) || null;
  }

  function getPairingsFor(type, id) {
    const item = getItem(type, id);
    if (!item) return [];

    return state.data.pairings.filter((pairing) => {
      if (type === "restaurant") {
        return (
          sameValue(pairing.restaurant_id, item.id) ||
          sameValue(pairing.restaurant, item.name) ||
          sameValue(pairing.restaurant_url, item.url)
        );
      }

      return (
        sameValue(pairing.event_id, item.id) ||
        sameValue(pairing.event, item.name) ||
        sameValue(pairing.event_url, item.url)
      );
    });
  }

  // LOCATION
  function requestLocation() {
    if (!navigator.geolocation) {
      state.userLocation = inferCityCenter();
      render();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        state.userLocation = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        };
        state.targetQuery = "Current location";
        state.targetAreaName = "Current location";
        render();
      },
      () => {
        state.userLocation = inferCityCenter();
        render();
      },
      { enableHighAccuracy: false, maximumAge: 300000, timeout: 5000 }
    );
  }

  function haversineKm(a, b) {
    if (!hasCoords(a) || !hasCoords(b)) return null;
    const earthRadiusKm = 6371;
    const dLat = toRadians(b.lat - a.lat);
    const dLng = toRadians(b.lng - a.lng);
    const lat1 = toRadians(a.lat);
    const lat2 = toRadians(b.lat);
    const h =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return earthRadiusKm * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  }

  function walkMinutes(km) {
    if (!Number.isFinite(km)) return null;
    return Math.max(1, Math.round((km / 5) * 60));
  }

  // FILTERING + SORTING
  function applyFilters(items) {
    const query = state.searchQuery.trim().toLowerCase();
    let filtered = items.filter(({ item, type }) => {
      if (state.filters.type !== "all" && state.filters.type !== `${type}s`) return false;
      if (query && !matchesSearch(item, query)) return false;
      if (state.filters.openNow && !isOpenNow(item)) return false;
      if (state.filters.closingSoon && !isClosingSoon(item)) return false;
      if (state.filters.price !== null && Number(item.price_level) !== state.filters.price) return false;
      if (state.filters.minRating !== null && Number(item.rating || 0) < state.filters.minRating) return false;
      if (state.filters.nearby) {
        const ref = referenceLocation();
        const km = ref ? haversineKm(ref, getCoords(item)) : null;
        if (!Number.isFinite(km) || kmToMiles(km) > NEARBY_MILES) return false;
      }
      return true;
    });

    filtered = filtered.slice();
    filtered.sort((a, b) => {
      if (state.filters.sortBy === "distance") {
        return sortNumber(distanceFor(a.item), distanceFor(b.item));
      }
      if (state.filters.sortBy === "closing") {
        return sortNumber(closingTimeValue(a.item), closingTimeValue(b.item));
      }
      if (state.filters.sortBy === "rating") {
        return sortNumber(Number(b.item.rating || 0), Number(a.item.rating || 0));
      }
      return defaultSortValue(a) - defaultSortValue(b) || a.item.name.localeCompare(b.item.name);
    });

    return filtered;
  }

  function isOpenNow(item) {
    if (item._type === "event") {
      const window = getTimeWindow(item, "event");
      const now = new Date();
      return Boolean(window && now >= window.open && now <= window.close);
    }

    const hours = parseHours(item.hours);
    if (!hours) return false;
    const now = new Date();
    return now >= hours.open && now <= hours.close;
  }

  function isClosingSoon(item, minutes = 60) {
    const window = getTimeWindow(item, item._type);
    if (!window) return false;
    const now = new Date();
    const diff = window.close.getTime() - now.getTime();
    return diff > 0 && diff <= minutes * 60000;
  }

  function parseHours(hoursField) {
    if (!hoursField) return null;

    if (Array.isArray(hoursField)) {
      const today = new Date().toLocaleDateString("en-US", { weekday: "long" }).toLowerCase();
      const todayHours = hoursField.find((entry) => String(entry).toLowerCase().includes(today));
      return parseHours(todayHours || hoursField[0]);
    }

    if (typeof hoursField === "object") {
      const directOpen = hoursField.open || hoursField.opens || hoursField.start || hoursField.from;
      const directClose = hoursField.close || hoursField.closes || hoursField.end || hoursField.to;
      if (directOpen && directClose) return makeHoursWindow(directOpen, directClose);

      const now = new Date();
      const dayNames = [
        now.toLocaleDateString("en-US", { weekday: "long" }).toLowerCase(),
        now.toLocaleDateString("en-US", { weekday: "short" }).toLowerCase(),
      ];
      const key = Object.keys(hoursField).find((name) => dayNames.includes(name.toLowerCase()));
      return key ? parseHours(hoursField[key]) : null;
    }

    const text = String(hoursField).trim();
    if (!text || /closed/i.test(text)) return null;
    const normalized = text.replace(/\u2013|\u2014|to/gi, "-");
    const range = normalized.match(/(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*-\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)/i);
    if (!range) return null;
    return makeHoursWindow(range[1], range[2]);
  }

  // PLAN
  function addToPlan(type, id) {
    addPlanItem(type, id);
    state.view = "plan";
    state.filtersOpen = false;
    state.activeSheet = null;
    render();
  }

  function addPlanItem(type, id) {
    if (!getItem(type, id)) return;
    const exists = state.plan.some((planItem) => planItem.type === type && planItem.id === id);
    if (!exists) state.plan.push({ type, id });
  }

  function removeFromPlan(index) {
    state.plan.splice(index, 1);
    render();
  }

  function reorderPlan(fromIndex, toIndex) {
    if (fromIndex === toIndex || fromIndex < 0 || toIndex < 0) return;
    if (fromIndex >= state.plan.length || toIndex >= state.plan.length) return;
    const [moved] = state.plan.splice(fromIndex, 1);
    state.plan.splice(toIndex, 0, moved);
    render();
  }

  function getPlanConflicts() {
    const conflicts = [];

    state.plan.forEach((planItem, index) => {
      const item = getItem(planItem.type, planItem.id);
      if (!item) return;
      if (renderStatus(item).kind === "closed") {
        conflicts.push({ index, reason: "Closed right now" });
      }

      const previous = index > 0 ? getItem(state.plan[index - 1].type, state.plan[index - 1].id) : null;
      if (previous && isClosingSoon(item)) {
        const km = haversineKm(getCoords(previous), getCoords(item));
        const walk = walkMinutes(km) || 0;
        const window = getTimeWindow(item, planItem.type);
        const buffer = window ? (window.close.getTime() - Date.now()) / 60000 - walk : Infinity;
        if (buffer < 15) conflicts.push({ index, reason: `Cutting it close - closes at ${formatTime(window.close)}` });
      }
    });

    for (let i = 0; i < state.plan.length - 1; i += 1) {
      const current = getItem(state.plan[i].type, state.plan[i].id);
      const next = getItem(state.plan[i + 1].type, state.plan[i + 1].id);
      if (!current || !next) continue;

      const currentWindow = getTimeWindow(current, state.plan[i].type);
      const nextWindow = getTimeWindow(next, state.plan[i + 1].type);
      const km = haversineKm(getCoords(current), getCoords(next));
      const walk = walkMinutes(km) || 0;
      if (currentWindow && nextWindow && currentWindow.close.getTime() + walk * 60000 > nextWindow.open.getTime()) {
        conflicts.push({ index: i + 1, reason: "Leaves no time to walk there" });
      }
    }

    return dedupeConflicts(conflicts);
  }

  function getPlanDistance() {
    let total = 0;
    let hasAny = false;
    for (let i = 0; i < state.plan.length - 1; i += 1) {
      const a = getItem(state.plan[i].type, state.plan[i].id);
      const b = getItem(state.plan[i + 1].type, state.plan[i + 1].id);
      const km = haversineKm(getCoords(a), getCoords(b));
      if (Number.isFinite(km)) {
        total += km;
        hasAny = true;
      }
    }
    return hasAny ? total : null;
  }

  function getPlanSuggestions() {
    if (state.plan.length === 0) return [];

    const planned = new Set(state.plan.map((planItem) => `${planItem.type}:${planItem.id}`));
    const candidates = [];
    const planPool = state.plan.slice().reverse();

    planPool.forEach((planItem) => {
      getPairingsFor(planItem.type, planItem.id).forEach((pairing) => {
        const next = getPairedItem(pairing, planItem.type);
        if (!next || planned.has(`${next.type}:${next.item.id}`)) return;
        candidates.push({
          type: next.type,
          item: next.item,
          reason: pairing.reason || pairing.match_reason || "Pairs well",
          score: Number(pairing.score || 0),
        });
      });
    });

    const seen = new Set();
    return candidates
      .sort((a, b) => b.score - a.score)
      .filter((candidate) => {
        const key = `${candidate.type}:${candidate.item.id}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .slice(0, 3);
  }

  // SAVED
  function addToSaved(type, id) {
    if (!getItem(type, id) || isSaved(type, id)) return;
    state.saved.push({ type, id });
    syncSavedToStorage();
  }

  function removeFromSaved(type, id) {
    state.saved = state.saved.filter((item) => item.type !== type || item.id !== id);
    syncSavedToStorage();
  }

  function isSaved(type, id) {
    return state.saved.some((item) => item.type === type && item.id === id);
  }

  function syncSavedToStorage() {
    localStorage.setItem(STORAGE_KEYS.saved, JSON.stringify(state.saved));
  }

  function loadSavedFromStorage() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEYS.saved) || "[]");
      state.saved = asArray(saved).filter((item) => item && item.type && item.id);
    } catch {
      state.saved = [];
    }
  }

  // RENDERING
  function render() {
    document.body.classList.toggle("filters-open", state.filtersOpen);
    document.body.classList.toggle("density-comfortable", state.densityMode === "comfortable");
    document.body.classList.toggle("sheet-open", Boolean(state.activeSheet));

    els.filterToggle.setAttribute("aria-expanded", String(state.filtersOpen));
    els.tabs.forEach((tab) => {
      const isActive = tab.dataset.view === state.view;
      tab.classList.toggle("active", isActive);
      if (isActive) tab.setAttribute("aria-current", "page");
      else tab.removeAttribute("aria-current");
    });

    if (state.loading) {
      els.root.innerHTML = `<div class="loading">Loading places and events...</div>`;
      renderSheet();
      return;
    }

    if (state.error) {
      els.root.innerHTML = `<div class="error"><strong>Could not load Happenstance</strong><p>${escapeHTML(state.error)}</p></div>`;
      renderSheet();
      return;
    }

    els.root.innerHTML = renderView();
    renderSheet();
  }

  function renderView() {
    if (state.view === "timeline") return renderTimeline();
    if (state.view === "plan") return renderPlan();
    if (state.view === "saved") return renderSaved();
    return renderExplore();
  }

  function renderExplore() {
    const rows = applyFilters(getUnifiedItems());
    const itemRows = rows.map(({ item, type }) => renderItemRow(item, type)).join("");
    return `
      ${renderFilterPanel()}
      <section aria-label="Explore">
        <div class="view-heading">
          <div>
            <h2>Explore</h2>
            <p>${rows.length} options · ${escapeHTML(targetLabel())} · ${escapeHTML(getUpdatedLabel())}</p>
          </div>
          <span class="status-badge status-neutral">${escapeHTML(state.filters.type)}</span>
        </div>
        ${renderClusterPanel()}
        <div class="item-list">
          ${itemRows || `<div class="empty"><strong>No matches</strong><p>Adjust filters or search terms.</p></div>`}
        </div>
      </section>
    `;
  }

  function renderTimeline() {
    const days = buildWeekTimelineDays();
    const slots = days.flatMap((day) => day.slots);
    if (slots.length === 0) {
      return `<div class="empty"><strong>No timeline items this week</strong><p>Events need dates, and restaurants need parseable hours.</p></div>`;
    }

    return `
      <section aria-label="Timeline">
        <div class="view-heading">
          <div>
            <h2>Timeline</h2>
            <p>Next seven days by local start time.</p>
          </div>
        </div>
        <div class="timeline">
          ${days.map(renderTimelineDay).join("")}
        </div>
      </section>
    `;
  }

  function renderPlan() {
    const livePlan = state.plan
      .map((planItem) => ({ ...planItem, item: getItem(planItem.type, planItem.id) }))
      .filter((planItem) => planItem.item);

    if (livePlan.length === 0) {
      return `
        <section class="plan" aria-label="Plan">
          <div class="empty">
            <strong>Your plan is empty.</strong>
            <p>Add restaurants and events from Explore.</p>
            <button class="large-add" type="button" data-action="change-tab" data-view-target="explore" aria-label="Explore">+</button>
          </div>
        </section>
      `;
    }

    const conflicts = getPlanConflicts();
    const suggestions = getPlanSuggestions();
    const conflictByIndex = new Map(conflicts.map((conflict) => [conflict.index, conflict.reason]));
    const planCards = livePlan
      .map((planItem, index) => {
        const connector = index < livePlan.length - 1 ? renderPlanConnector(planItem.item, livePlan[index + 1].item) : "";
        return `${renderPlanItem(planItem, index, conflictByIndex.get(index))}${connector}`;
      })
      .join("");

    return `
      <section class="plan" aria-label="Plan">
        <div class="plan-list">${planCards}</div>
        ${
          suggestions.length
            ? `<div class="suggestions">
                <h2>What pairs well next?</h2>
                <div class="suggestion-list">${suggestions.map(renderSuggestion).join("")}</div>
              </div>`
            : ""
        }
        <div class="plan-summary">${escapeHTML(renderPlanSummary(livePlan))}</div>
      </section>
    `;
  }

  function renderSaved() {
    const savedItems = state.saved
      .map((savedItem) => ({ type: savedItem.type, item: getItem(savedItem.type, savedItem.id) }))
      .filter(({ item }) => item);

    if (savedItems.length === 0) {
      return `<div class="empty"><strong>Nothing saved yet.</strong><p>Tap ♡ on any item.</p></div>`;
    }

    return `
      <section aria-label="Saved">
        <div class="view-heading">
          <div>
            <h2>Saved</h2>
            <p>${savedItems.length} saved item${savedItems.length === 1 ? "" : "s"}</p>
          </div>
        </div>
        <div class="item-list">
          ${savedItems.map(({ item, type }) => renderItemRow(item, type, { saved: true })).join("")}
        </div>
      </section>
    `;
  }

  function renderClusterPanel() {
    const clusters = getVisibleClusters();
    if (!clusters.length) return "";

    return `
      <section class="cluster-panel" aria-label="Opportunistic clusters">
        <div class="cluster-strip">
          ${clusters.map(renderClusterCard).join("")}
        </div>
      </section>
    `;
  }

  function renderClusterCard(cluster) {
    const events = asArray(cluster.event_ids).map((id) => getItem("event", id)).filter(Boolean);
    const restaurants = asArray(cluster.restaurant_ids).map((id) => getItem("restaurant", id)).filter(Boolean);
    const distance = renderClusterDistance(cluster);
    const firstEvent = events[0];
    const firstRestaurant = restaurants[0];
    const restaurantLinks = restaurants
      .slice(0, 3)
      .map((restaurant) => `
        <button class="cluster-link" type="button" data-action="open-sheet" data-type="restaurant" data-id="${escapeAttr(restaurant.id)}">
          ${escapeHTML(truncate(restaurant.name, 22))}
        </button>
      `)
      .join("");
    return `
      <article class="cluster-card">
        <div>
          <h3>${escapeHTML(cluster.title || `Head to ${cluster.area || "nearby"}`)}</h3>
          <p>${escapeHTML(cluster.reason || "Good event and dining density nearby.")}</p>
          <p>${escapeHTML([distance, firstEvent ? firstEvent.name : "", firstRestaurant ? `then ${firstRestaurant.name}` : ""].filter(Boolean).join(" · "))}</p>
          ${restaurantLinks ? `<div class="cluster-links" aria-label="Restaurant details">${restaurantLinks}</div>` : ""}
        </div>
        <button class="action-button primary" type="button" data-action="add-cluster-plan" data-cluster-id="${escapeAttr(cluster.id)}">Plan</button>
      </article>
    `;
  }

  function renderItemRow(item, type, options = {}) {
    const status = renderStatus(item);
    const meta = type === "restaurant" ? restaurantMeta(item) : eventMeta(item);
    const description = item.description || item.match_reason || (type === "event" ? formatEventDate(item) : "");
    const price = renderPriceLevel(item);
    const distance = renderDistance(item);
    const actions = options.saved
      ? `<div class="inline-actions">
          <button class="action-button primary" type="button" data-action="add-plan" data-type="${type}" data-id="${escapeAttr(item.id)}">Add</button>
          <button class="action-button danger" type="button" data-action="toggle-save" data-type="${type}" data-id="${escapeAttr(item.id)}">♥</button>
        </div>`
      : "";

    return `
      <article class="item-row ${status.kind === "closed" ? "is-closed" : ""}" role="button" tabindex="0" data-action="open-sheet" data-type="${type}" data-id="${escapeAttr(item.id)}">
        <div class="item-icon" aria-hidden="true">${type === "restaurant" ? "◌" : "◆"}</div>
        <div class="item-main">
          <div class="item-title-line">
            <span class="item-title">${escapeHTML(item.name)}</span>
            ${price ? `<span class="item-price">${escapeHTML(price)}</span>` : ""}
          </div>
          <div class="item-meta-line">${escapeHTML(meta)}</div>
          <div class="item-description">${escapeHTML(description || "Details pending")}</div>
          ${renderPairingPills(item, type)}
        </div>
        <div class="item-aside">
          ${distance ? `<span class="distance">${escapeHTML(distance)}</span>` : ""}
          ${renderOpenStatus(item)}
          ${actions}
        </div>
      </article>
    `;
  }

  function renderItemSheet(item, type) {
    const pairings = getPairingsFor(type, item.id);
    const address = type === "restaurant" ? item.address : item.venue;
    const description = item.description || item.match_reason || "No description available yet.";
    const tags = asArray(item.tags);
    const saved = isSaved(type, item.id);
    const hours = type === "restaurant" ? formatHours(item.hours) : formatEventDate(item);

    return `
      <div class="sheet-handle" aria-hidden="true"></div>
      <div class="sheet-header">
        <div>
          <h2>${escapeHTML(item.name)}</h2>
          <p class="item-meta-line">${escapeHTML(type === "restaurant" ? restaurantMeta(item) : eventMeta(item))}</p>
        </div>
        <button class="action-button" type="button" data-action="close-sheet" aria-label="Close">×</button>
      </div>
      <div class="sheet-actions">
        <button class="action-button primary" type="button" data-action="add-plan" data-type="${type}" data-id="${escapeAttr(item.id)}">Add to Plan</button>
        <button class="action-button" type="button" data-action="toggle-save" data-type="${type}" data-id="${escapeAttr(item.id)}">${saved ? "♥ Saved" : "♡ Save"}</button>
      </div>
      <section class="sheet-section">
        <h3>Status</h3>
        ${renderOpenStatus(item)}
        ${renderDistance(item) ? `<p>${escapeHTML(renderDistance(item))} away</p>` : ""}
      </section>
      <section class="sheet-section">
        <h3>Details</h3>
        <p>${escapeHTML(description)}</p>
      </section>
      ${
        address
          ? `<section class="sheet-section">
              <h3>${type === "restaurant" ? "Address" : "Venue"}</h3>
              <p><a href="${escapeAttr(mapUrlFor(item, address))}" target="_blank" rel="noopener">${escapeHTML(address)}</a></p>
            </section>`
          : ""
      }
      ${
        hours
          ? `<section class="sheet-section">
              <h3>${type === "restaurant" ? "Hours" : "When"}</h3>
              <p>${escapeHTML(hours)}</p>
            </section>`
          : ""
      }
      ${
        tags.length
          ? `<section class="sheet-section">
              <h3>Tags</h3>
              <ul class="tag-list">${tags.map((tag) => `<li class="tag">${escapeHTML(tag)}</li>`).join("")}</ul>
            </section>`
          : ""
      }
      <section class="sheet-section">
        <h3>Pairings</h3>
        ${
          pairings.length
            ? `<ul class="pairing-list">${pairings.map((pairing) => renderPairingDetail(pairing, type)).join("")}</ul>`
            : `<p>No pairing suggestions yet.</p>`
        }
      </section>
    `;
  }

  function renderPlanItem(planItem, index, conflictReason) {
    const item = planItem.item || getItem(planItem.type, planItem.id);
    if (!item) return "";

    return `
      <article class="plan-card ${conflictReason ? "conflict" : ""}" draggable="true" data-plan-index="${index}">
        <div class="plan-card-header">
          <span aria-hidden="true">${planItem.type === "restaurant" ? "◌" : "◆"}</span>
          <div>
            <h3>${escapeHTML(item.name)}</h3>
            <p>${escapeHTML(planItem.type === "restaurant" ? restaurantMeta(item) : eventMeta(item))}</p>
          </div>
          <div class="plan-card-actions">
            ${renderOpenStatus(item)}
            <button class="action-button" type="button" data-action="open-sheet" data-type="${planItem.type}" data-id="${escapeAttr(item.id)}">Details</button>
            <button class="action-button danger" type="button" data-action="remove-plan" data-index="${index}" aria-label="Remove">×</button>
          </div>
        </div>
        ${conflictReason ? `<p class="conflict-text">${escapeHTML(conflictReason)}</p>` : ""}
      </article>
    `;
  }

  function renderPairingPills(item, type) {
    const pills = getPairingsFor(type, item.id)
      .map((pairing) => getPairedItem(pairing, type))
      .filter(Boolean)
      .slice(0, 2)
      .map(({ item: paired }) => `<span class="pairing-pill">→ ${escapeHTML(truncate(paired.name, 20))}</span>`)
      .join("");

    return pills ? `<div class="row-pairings">${pills}</div>` : "";
  }

  function renderOpenStatus(item) {
    const status = renderStatus(item);
    return `<span class="status-badge status-${status.kind}">${escapeHTML(status.label)}</span>`;
  }

  function renderDistance(item) {
    const ref = referenceLocation();
    const km = ref ? haversineKm(ref, getCoords(item)) : null;
    return Number.isFinite(km) ? formatMiles(kmToMiles(km)) : "";
  }

  function renderPriceLevel(item) {
    if (item.price) return String(item.price);
    const level = Number(item.price_level);
    if (!Number.isFinite(level) || level <= 0) return "";
    return "$".repeat(Math.min(4, Math.max(1, level)));
  }

  // UI EVENTS
  function handleTabChange(view) {
    state.view = view;
    state.filtersOpen = false;
    state.activeSheet = null;
    localStorage.setItem(STORAGE_KEYS.view, view);
    render();
  }

  function handleFilterToggle() {
    state.filtersOpen = !state.filtersOpen;
    render();
  }

  function handleFilterChange(key, value) {
    if (key === "price") {
      state.filters.price = state.filters.price === value ? null : value;
    } else if (key === "minRating") {
      state.filters.minRating = state.filters.minRating === value ? null : value;
    } else if (key === "type") {
      state.filters.type = value;
    } else if (key === "sortBy") {
      state.filters.sortBy = value;
    } else {
      state.filters[key] = !state.filters[key];
    }

    if (key === "nearby" && state.filters.nearby && !referenceLocation()) requestLocation();
    render();
  }

  function handleItemTap(type, id) {
    state.activeSheet = { type, id };
    render();
  }

  function handleSheetClose() {
    state.activeSheet = null;
    render();
  }

  function handleAddToPlan(type, id) {
    addToPlan(type, id);
  }

  function handleAddToSaved(type, id) {
    if (isSaved(type, id)) removeFromSaved(type, id);
    else addToSaved(type, id);
    render();
  }

  function handleDensityToggle() {
    state.densityMode = state.densityMode === "compact" ? "comfortable" : "compact";
    localStorage.setItem(STORAGE_KEYS.density, state.densityMode);
    render();
  }

  function handleSearchInput(query) {
    state.searchQuery = query;
    render();
  }

  function handleTargetInput(query) {
    state.targetQuery = query;
  }

  function handleTargetApply(query = state.targetQuery) {
    const resolved = resolveTarget(query);
    state.targetQuery = query.trim();
    state.targetLocation = resolved ? resolved.center : state.targetLocation;
    state.targetAreaName = resolved ? resolved.name : state.targetQuery;
    state.userLocation = null;
    if (resolved) state.filters.sortBy = "distance";
    localStorage.setItem(STORAGE_KEYS.target, state.targetQuery);
    render();
  }

  function handleAddClusterToPlan(clusterId) {
    const cluster = state.data.clusters.find((item) => item.id === clusterId);
    if (!cluster) return;
    const event = asArray(cluster.event_ids).map((id) => getItem("event", id)).filter(Boolean)[0];
    const restaurant = asArray(cluster.restaurant_ids).map((id) => getItem("restaurant", id)).filter(Boolean)[0];
    if (restaurant && event) {
      const eventWindow = getTimeWindow(event, "event");
      if (eventWindow && eventWindow.open.getHours() >= 17) {
        addPlanItem("restaurant", restaurant.id);
        addPlanItem("event", event.id);
      } else {
        addPlanItem("event", event.id);
        addPlanItem("restaurant", restaurant.id);
      }
    } else if (event) {
      addPlanItem("event", event.id);
    } else if (restaurant) {
      addPlanItem("restaurant", restaurant.id);
    }
    state.view = "plan";
    state.filtersOpen = false;
    state.activeSheet = null;
    render();
  }

  // NORMALIZATION + HELPERS
  function normalizeRestaurant(item, index) {
    const name = safeText(item.name || item.title, "Untitled restaurant");
    const id = String(item.id || slugify(`${name}-${item.address || item.url || index}`));
    const coords = normalizeCoords(item.location || item.coords || item.coordinates);
    return {
      ...item,
      _type: "restaurant",
      id,
      name,
      cuisine: safeText(item.cuisine, "Restaurant"),
      address: safeText(item.address || (typeof item.location === "string" ? item.location : ""), ""),
      neighborhood: safeText(item.neighborhood || neighborhoodFromAddress(item.address), ""),
      description: safeText(item.description || item.match_reason, ""),
      coords,
    };
  }

  function normalizeEvent(item, index) {
    const name = safeText(item.name || item.title, "Untitled event");
    const date = safeText(item.date || item.start_time || item.starts_at, "");
    const venue = safeText(item.venue || (typeof item.location === "string" ? item.location : item.address), "");
    const id = String(item.id || slugify(`${name}-${date}-${venue || item.url || index}`));
    const locationCandidate = item.location && typeof item.location === "object" ? item.location : item.coords || item.coordinates;
    const coords = normalizeCoords(locationCandidate);
    return {
      ...item,
      _type: "event",
      id,
      name,
      venue,
      category: safeText(item.category, "Event"),
      description: safeText(item.description || item.match_reason, ""),
      time: safeText(item.time || extractTime(date), ""),
      coords,
    };
  }

  function applyInitialTarget() {
    const storedTarget = localStorage.getItem(STORAGE_KEYS.target) || "";
    const defaultCenter = normalizeCoords(state.data.meta.search && state.data.meta.search.center);
    if (storedTarget) {
      const resolved = resolveTarget(storedTarget);
      state.targetQuery = storedTarget;
      state.targetLocation = resolved ? resolved.center : defaultCenter;
      state.targetAreaName = resolved ? resolved.name : storedTarget;
      return;
    }

    const defaultArea = state.data.meta.search && state.data.meta.search.target_area;
    state.targetQuery = defaultArea || "";
    state.targetAreaName = defaultArea || "Default area";
    state.targetLocation = defaultCenter;
  }

  function resolveTarget(query) {
    const text = String(query || "").trim();
    if (!text) return null;
    const lower = text.toLowerCase();
    const coordMatch = text.match(/^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/);
    if (coordMatch) {
      return {
        name: "Custom point",
        center: { lat: Number(coordMatch[1]), lng: Number(coordMatch[2]) },
      };
    }

    for (const area of state.data.targetAreas) {
      const names = [area.id, area.name, ...(area.aliases || []), ...(area.zips || [])]
        .filter(Boolean)
        .map((value) => String(value).trim().toLowerCase());
      if (names.includes(lower) || names.some((name) => lower.includes(name))) {
        const center = normalizeCoords(area.center);
        if (center) return { name: area.name || text, center };
      }
    }

    const byNeighborhood = [...state.data.restaurants, ...state.data.events].find((item) => {
      return [item.neighborhood, item.address, item.venue].filter(Boolean).some((value) => String(value).toLowerCase().includes(lower));
    });
    if (byNeighborhood && getCoords(byNeighborhood)) {
      return { name: text, center: getCoords(byNeighborhood) };
    }

    return null;
  }

  function renderFilterPanel() {
    const chips = [
      { label: "Open Now", key: "openNow", active: state.filters.openNow },
      { label: "Closing Soon", key: "closingSoon", active: state.filters.closingSoon },
      { label: "Nearby", key: "nearby", active: state.filters.nearby },
      { label: "⭐ 4+", key: "minRating", value: 4, active: state.filters.minRating === 4 },
      { label: "$ Only", key: "price", value: 1, active: state.filters.price === 1 },
      { label: "$$ Only", key: "price", value: 2, active: state.filters.price === 2 },
      { label: "$$$ Only", key: "price", value: 3, active: state.filters.price === 3 },
      { label: "All", key: "type", value: "all", active: state.filters.type === "all" },
      { label: "Restaurants", key: "type", value: "restaurants", active: state.filters.type === "restaurants" },
      { label: "Events", key: "type", value: "events", active: state.filters.type === "events" },
    ];

    return `
      <div class="filter-panel">
        <div class="filter-search">
          <input type="search" value="${escapeAttr(state.searchQuery)}" placeholder="Search food, event, place" data-action="search" aria-label="Search" />
          <select data-action="sort" aria-label="Sort">
            ${[
              ["default", "Default"],
              ["distance", "Distance"],
              ["closing", "Closing Time"],
              ["rating", "Rating"],
            ]
              .map(([value, label]) => `<option value="${value}" ${state.filters.sortBy === value ? "selected" : ""}>${label}</option>`)
              .join("")}
          </select>
          <button type="button" data-action="density">${state.densityMode === "comfortable" ? "Comfortable" : "Compact"}</button>
        </div>
        <div class="target-search">
          <input type="search" value="${escapeAttr(state.targetQuery)}" placeholder="ZIP or target area" data-action="target-input" aria-label="Target ZIP or area" />
          <button type="button" data-action="apply-target">Apply</button>
          <button type="button" data-action="use-location">GPS</button>
        </div>
        <div class="filter-chips">
          ${state.data.targetAreas
            .slice(0, 6)
            .map((area) => `<button class="chip ${state.targetAreaName === area.name ? "active" : ""}" type="button" data-action="target-chip" data-target="${escapeAttr(area.name)}">${escapeHTML(area.name)}</button>`)
            .join("")}
          ${chips
            .map(
              (chip) =>
                `<button class="chip ${chip.active ? "active" : ""}" type="button" data-action="filter" data-key="${chip.key}" data-value="${escapeAttr(chip.value ?? "")}">${escapeHTML(chip.label)}</button>`
            )
            .join("")}
        </div>
      </div>
    `;
  }

  function renderSheet() {
    let backdrop = document.querySelector(".sheet-backdrop");
    let sheet = document.querySelector(".bottom-sheet");

    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.className = "sheet-backdrop";
      backdrop.dataset.action = "close-sheet";
      document.body.appendChild(backdrop);
    }

    if (!sheet) {
      sheet = document.createElement("aside");
      sheet.className = "bottom-sheet";
      sheet.setAttribute("aria-modal", "true");
      sheet.setAttribute("role", "dialog");
      document.body.appendChild(sheet);
    }

    if (!state.activeSheet) {
      sheet.innerHTML = "";
      return;
    }

    const item = getItem(state.activeSheet.type, state.activeSheet.id);
    sheet.innerHTML = item ? renderItemSheet(item, state.activeSheet.type) : "";
  }

  function renderStatus(item) {
    if (item._type === "event") {
      const window = getTimeWindow(item, "event");
      if (!window) return { kind: "neutral", label: "Time n/a" };
      const now = new Date();
      const startsSoon = window.open.getTime() - now.getTime() <= 60 * 60000 && window.open > now;
      if (now > window.close) return { kind: "closed", label: "Past" };
      if (now >= window.open && now <= window.close) return { kind: "open", label: "Live" };
      if (startsSoon) return { kind: "closing", label: "Soon" };
      return { kind: "neutral", label: "Upcoming" };
    }

    const hours = parseHours(item.hours);
    if (!hours) return { kind: "neutral", label: "Hours n/a" };
    if (isClosingSoon(item)) return { kind: "closing", label: "Closing" };
    if (isOpenNow(item)) return { kind: "open", label: "Open" };
    return { kind: "closed", label: "Closed" };
  }

  function renderPairingDetail(pairing, fromType) {
    const paired = getPairedItem(pairing, fromType);
    const name = paired ? paired.item.name : fromType === "restaurant" ? pairing.event : pairing.restaurant;
    const reason = pairing.reason || pairing.match_reason || "Pairs well";
    const walk = pairing.walk_minutes ? ` · ${pairing.walk_minutes} min walk` : "";
    return `<li class="tag">→ ${escapeHTML(name || "Suggestion")}: ${escapeHTML(reason)}${escapeHTML(walk)}</li>`;
  }

  function renderTimelineSlot(slot) {
    return `
      <button class="timeline-slot ${slot.type}" type="button" data-action="open-sheet" data-type="${slot.type}" data-id="${escapeAttr(slot.item.id)}">
        <span aria-hidden="true">${slot.type === "restaurant" ? "◌" : "◆"}</span>
        <span>${escapeHTML(slot.item.name)}</span>
        <span class="timeline-duration">${escapeHTML(slot.duration)}</span>
      </button>
    `;
  }

  function renderTimelineDay(day) {
    const dateLabel = day.date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
    const countLabel = `${day.slots.length} item${day.slots.length === 1 ? "" : "s"}`;
    return `
      <section class="timeline-day" aria-label="${escapeAttr(dateLabel)}">
        <div class="timeline-day-header">
          <h3>${escapeHTML(dateLabel)}</h3>
          <span>${escapeHTML(countLabel)}</span>
        </div>
        <div class="timeline-stack">
          ${
            day.slots.length
              ? day.slots.map(renderTimelineSlot).join("")
              : `<div class="timeline-empty">No scheduled items</div>`
          }
        </div>
      </section>
    `;
  }

  function renderPlanConnector(current, next) {
    const km = haversineKm(getCoords(current), getCoords(next));
    if (!Number.isFinite(km)) return `<div class="connector">Walk time unavailable</div>`;
    const minutes = walkMinutes(km);
    const miles = kmToMiles(km);
    const warning = miles > 2 ? " ⚠️ consider a ride" : "";
    return `<div class="connector">${minutes} min · ${formatMiles(miles)}${warning}</div>`;
  }

  function renderSuggestion(suggestion) {
    return `
      <article class="suggestion-card">
        <span aria-hidden="true">${suggestion.type === "restaurant" ? "◌" : "◆"}</span>
        <div>
          <h3>${escapeHTML(suggestion.item.name)}</h3>
          <p>${escapeHTML(suggestion.reason)}</p>
        </div>
        <button class="action-button primary" type="button" data-action="add-plan" data-type="${suggestion.type}" data-id="${escapeAttr(suggestion.item.id)}">Add</button>
      </article>
    `;
  }

  function renderPlanSummary(livePlan) {
    const totalKm = getPlanDistance();
    const totalWalk = Number.isFinite(totalKm) ? `${walkMinutes(totalKm)} min walk` : "walk time pending";
    const windows = livePlan
      .map((planItem) => getTimeWindow(planItem.item, planItem.type))
      .filter(Boolean)
      .sort((a, b) => a.open - b.open);
    const range = windows.length ? `${formatTime(windows[0].open)} → ${formatTime(windows[windows.length - 1].close)}` : "timing pending";
    return `${livePlan.length} item${livePlan.length === 1 ? "" : "s"} · ${totalWalk} · ${range}`;
  }

  function buildWeekTimelineDays() {
    const start = startOfLocalDay(new Date());
    const days = Array.from({ length: 7 }, (_, index) => ({
      date: addDays(start, index),
      slots: [],
    }));
    const end = addDays(start, days.length);

    const restaurantSlots = state.data.restaurants.flatMap((item) => {
      const hours = parseHours(item.hours);
      if (!hours) return [];
      return days.map((day) => {
        const open = copyTimeToDay(day.date, hours.open);
        const close = copyTimeToDay(day.date, hours.close);
        if (close <= open) close.setDate(close.getDate() + 1);
        return {
          type: "restaurant",
          item,
          start: open,
          duration: `${formatTime(open)}-${formatTime(close)}`,
        };
      });
    });

    const eventSlots = state.data.events
      .map((item) => {
        const window = getTimeWindow(item, "event");
        if (!window || window.open < start || window.open >= end) return null;
        return {
          type: "event",
          item,
          start: window.open,
          duration: item.duration_minutes ? `${item.duration_minutes} min` : displayTimeForEvent(item),
        };
      })
      .filter(Boolean);

    [...restaurantSlots, ...eventSlots]
      .sort((a, b) => a.start - b.start || a.item.name.localeCompare(b.item.name))
      .forEach((slot) => {
        const index = Math.round((startOfLocalDay(slot.start) - start) / 86400000);
        if (days[index]) days[index].slots.push(slot);
      });

    return days;
  }

  function getUnifiedItems() {
    return [
      ...state.data.restaurants.map((item) => ({ type: "restaurant", item })),
      ...state.data.events.map((item) => ({ type: "event", item })),
    ];
  }

  function getVisibleClusters() {
    const ref = referenceLocation();
    return state.data.clusters
      .map((cluster) => {
        const center = normalizeCoords(cluster.center);
        const km = ref && center ? haversineKm(ref, center) : null;
        const targetMatch = state.targetAreaName && String(cluster.area || "").toLowerCase().includes(state.targetAreaName.toLowerCase());
        const proximityBoost = Number.isFinite(km) ? Math.max(0, 30 - km) : 0;
        return { ...cluster, _distanceKm: km, _rank: Number(cluster.score || 0) + proximityBoost + (targetMatch ? 40 : 0) };
      })
      .sort((a, b) => {
        const distanceSort = sortNumber(a._distanceKm, b._distanceKm);
        if (distanceSort !== 0 && state.filters.sortBy === "distance") return distanceSort;
        return Number(b._rank || 0) - Number(a._rank || 0) || sortNumber(new Date(a.starts_at).getTime(), new Date(b.starts_at).getTime());
      })
      .slice(0, 4);
  }

  function renderClusterDistance(cluster) {
    if (Number.isFinite(cluster._distanceKm)) return `${formatMiles(kmToMiles(cluster._distanceKm))} from ${targetLabel()}`;
    if (Number.isFinite(cluster.distance_miles_from_target)) return `${formatMiles(Number(cluster.distance_miles_from_target))} from target`;
    if (Number.isFinite(cluster.distance_km_from_target)) return `${formatMiles(kmToMiles(Number(cluster.distance_km_from_target)))} from target`;
    return "";
  }

  function referenceLocation() {
    return state.userLocation || state.targetLocation || normalizeCoords(state.data.meta.search && state.data.meta.search.center);
  }

  function targetLabel() {
    return state.userLocation ? "current location" : state.targetAreaName || state.targetQuery || "default area";
  }

  function getPairedItem(pairing, fromType) {
    if (fromType === "restaurant") {
      const item =
        getItem("event", pairing.event_id) ||
        state.data.events.find((event) => sameValue(event.name, pairing.event) || sameValue(event.url, pairing.event_url));
      return item ? { type: "event", item } : null;
    }

    const item =
      getItem("restaurant", pairing.restaurant_id) ||
      state.data.restaurants.find((restaurant) => sameValue(restaurant.name, pairing.restaurant) || sameValue(restaurant.url, pairing.restaurant_url));
    return item ? { type: "restaurant", item } : null;
  }

  function getTimeWindow(item, type) {
    if (!item) return null;
    if (type === "restaurant") return parseHours(item.hours);
    const start = eventDate(item);
    if (!start) return null;
    const duration = Number(item.duration_minutes || 120);
    return { open: start, close: new Date(start.getTime() + duration * 60000) };
  }

  function eventDate(item) {
    if (!item || !item.date) return null;
    const datePart = String(item.date).slice(0, 10);
    const timePart = item.time || extractTime(item.date) || "00:00";
    const parsed = datePart ? new Date(`${datePart}T${timePart}:00`) : new Date(item.date);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function makeHoursWindow(openText, closeText) {
    const open = parseTime(openText);
    const close = parseTime(closeText);
    if (!open || !close) return null;
    if (close <= open) close.setDate(close.getDate() + 1);
    return { open, close };
  }

  function parseTime(value) {
    const text = String(value || "").trim().toLowerCase();
    const match = text.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/);
    if (!match) return null;
    let hour = Number(match[1]);
    const minute = Number(match[2] || 0);
    const period = match[3];

    if (period === "pm" && hour < 12) hour += 12;
    if (period === "am" && hour === 12) hour = 0;
    if (hour > 23 || minute > 59) return null;

    const date = new Date();
    date.setHours(hour, minute, 0, 0);
    return date;
  }

  function inferCityCenter() {
    const meta = state.data.meta || {};
    const candidates = [meta.center, meta.city_center, meta.location, meta.search && meta.search.center];
    const direct = candidates.map(normalizeCoords).find(Boolean);
    if (direct) return direct;

    const coords = [...state.data.restaurants, ...state.data.events].map(getCoords).filter(hasCoords);
    if (!coords.length) return null;
    return {
      lat: coords.reduce((sum, coord) => sum + coord.lat, 0) / coords.length,
      lng: coords.reduce((sum, coord) => sum + coord.lng, 0) / coords.length,
    };
  }

  function applyBranding() {
    const branding = state.data.branding || {};
    if (branding.title) els.title.textContent = branding.title;
    if (branding.accent_color) document.documentElement.style.setProperty("--color-accent", branding.accent_color);
  }

  function stripMeta(items) {
    return items.filter((item) => !(item && typeof item === "object" && item._meta));
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function safeText(value, fallback) {
    const text = value === null || value === undefined ? "" : String(value).trim();
    return text || fallback;
  }

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]
    ));
  }

  function escapeAttr(value) {
    return escapeHTML(value);
  }

  function slugify(value) {
    return String(value)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80);
  }

  function sameValue(a, b) {
    return a !== undefined && b !== undefined && String(a).trim().toLowerCase() === String(b).trim().toLowerCase();
  }

  function normalizeCoords(value) {
    if (!value || typeof value !== "object") return null;
    const lat = Number(value.lat ?? value.latitude);
    const lng = Number(value.lng ?? value.lon ?? value.longitude);
    return Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null;
  }

  function getCoords(item) {
    return item && (item.coords || normalizeCoords(item.location) || normalizeCoords(item.coordinates));
  }

  function hasCoords(value) {
    return Boolean(value && Number.isFinite(Number(value.lat)) && Number.isFinite(Number(value.lng)));
  }

  function toRadians(value) {
    return (value * Math.PI) / 180;
  }

  function sortNumber(a, b) {
    const aa = Number.isFinite(a) ? a : Infinity;
    const bb = Number.isFinite(b) ? b : Infinity;
    return aa - bb;
  }

  function distanceFor(item) {
    const ref = referenceLocation();
    const km = ref ? haversineKm(ref, getCoords(item)) : null;
    return Number.isFinite(km) ? km : Infinity;
  }

  function kmToMiles(km) {
    return km / KM_PER_MILE;
  }

  function formatMiles(miles) {
    if (!Number.isFinite(miles)) return "";
    return `${miles.toFixed(miles < 10 ? 1 : 0)} mi`;
  }

  function closingTimeValue(item) {
    const window = getTimeWindow(item, item._type);
    return window ? window.close.getTime() : Infinity;
  }

  function defaultSortValue(row) {
    if (row.type === "event") {
      const date = eventDate(row.item);
      return date ? date.getTime() : Date.now() + 999999999;
    }
    return Date.now() + 999999999 + state.data.restaurants.indexOf(row.item);
  }

  function matchesSearch(item, query) {
    return [
      item.name,
      item.cuisine,
      item.category,
      item.address,
      item.venue,
      item.description,
      ...(asArray(item.tags)),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(query);
  }

  function restaurantMeta(item) {
    return [item.cuisine, item.neighborhood || cityFromAddress(item.address), item.rating ? `⭐ ${item.rating}` : ""]
      .filter(Boolean)
      .join(" · ");
  }

  function eventMeta(item) {
    return [item.category, item.venue, displayTimeForEvent(item)].filter(Boolean).join(" · ");
  }

  function cityFromAddress(address) {
    const parts = String(address || "").split(",").map((part) => part.trim()).filter(Boolean);
    return parts.length > 1 ? parts[parts.length - 2].replace(/\s+[A-Z]{2}$/, "") : "";
  }

  function neighborhoodFromAddress(address) {
    return cityFromAddress(address);
  }

  function truncate(value, length) {
    const text = String(value || "");
    return text.length > length ? `${text.slice(0, length - 1)}…` : text;
  }

  function getUpdatedLabel() {
    if (!state.data.meta.generated_at) return "updated recently";
    const date = new Date(state.data.meta.generated_at);
    return Number.isNaN(date.getTime()) ? "updated recently" : `updated ${date.toLocaleDateString()}`;
  }

  function formatHours(hours) {
    if (!hours) return "";
    if (typeof hours === "string") return hours;
    const parsed = parseHours(hours);
    return parsed ? `${formatTime(parsed.open)}-${formatTime(parsed.close)}` : "";
  }

  function formatEventDate(item) {
    const datePart = String(item.date || "").slice(0, 10);
    const date = datePart ? new Date(`${datePart}T00:00:00`) : null;
    const dateLabel = date && !Number.isNaN(date.getTime())
      ? date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })
      : "";
    return [dateLabel, displayTimeForEvent(item)].filter(Boolean).join(" · ");
  }

  function displayTimeForEvent(item) {
    return item.time ? formatTimeString(item.time) : "";
  }

  function extractTime(value) {
    const match = String(value || "").match(/T(\d{2}:\d{2})/);
    return match ? match[1] : "";
  }

  function startOfLocalDay(date) {
    const copy = new Date(date);
    copy.setHours(0, 0, 0, 0);
    return copy;
  }

  function addDays(date, days) {
    const copy = new Date(date);
    copy.setDate(copy.getDate() + days);
    return copy;
  }

  function copyTimeToDay(day, time) {
    const copy = new Date(day);
    copy.setHours(time.getHours(), time.getMinutes(), 0, 0);
    return copy;
  }

  function formatTimeString(value) {
    const [hourText, minuteText] = String(value).split(":");
    const hour = Number(hourText);
    const minute = Number(minuteText || 0);
    if (!Number.isFinite(hour) || !Number.isFinite(minute)) return "";
    const date = new Date();
    date.setHours(hour, minute, 0, 0);
    return formatTime(date);
  }

  function formatTime(date) {
    if (!date || Number.isNaN(date.getTime())) return "";
    return date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  }

  function formatHour(hour) {
    const date = new Date();
    date.setHours(hour, 0, 0, 0);
    return date.toLocaleTimeString("en-US", { hour: "numeric" });
  }

  function timelineOrder(hour) {
    return hour < 5 ? hour + 24 : hour;
  }

  function mapUrlFor(item, address) {
    return item.url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address || item.name)}`;
  }

  function dedupeConflicts(conflicts) {
    const seen = new Set();
    return conflicts.filter((conflict) => {
      const key = `${conflict.index}:${conflict.reason}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function readPreferences() {
    const storedView = localStorage.getItem(STORAGE_KEYS.view);
    const storedDensity = localStorage.getItem(STORAGE_KEYS.density);
    if (["explore", "timeline", "plan", "saved"].includes(storedView)) state.view = storedView;
    if (["compact", "comfortable"].includes(storedDensity)) state.densityMode = storedDensity;
  }

  function bindEvents() {
    els.filterToggle.addEventListener("click", handleFilterToggle);

    document.addEventListener("click", (event) => {
      const target = event.target.closest("[data-action]");
      if (!target) return;

      const action = target.dataset.action;
      if (action === "open-sheet") handleItemTap(target.dataset.type, target.dataset.id);
      if (action === "close-sheet") handleSheetClose();
      if (action === "add-plan") handleAddToPlan(target.dataset.type, target.dataset.id);
      if (action === "toggle-save") handleAddToSaved(target.dataset.type, target.dataset.id);
      if (action === "remove-plan") removeFromPlan(Number(target.dataset.index));
      if (action === "density") handleDensityToggle();
      if (action === "change-tab") handleTabChange(target.dataset.viewTarget);
      if (action === "apply-target") handleTargetApply();
      if (action === "use-location") requestLocation();
      if (action === "target-chip") handleTargetApply(target.dataset.target || "");
      if (action === "add-cluster-plan") handleAddClusterToPlan(target.dataset.clusterId);
      if (action === "filter") {
        const rawValue = target.dataset.value;
        const value = rawValue === "" ? undefined : Number.isNaN(Number(rawValue)) ? rawValue : Number(rawValue);
        handleFilterChange(target.dataset.key, value);
      }
    });

    document.addEventListener("input", (event) => {
      if (event.target.matches('[data-action="search"]')) handleSearchInput(event.target.value);
      if (event.target.matches('[data-action="target-input"]')) handleTargetInput(event.target.value);
    });

    document.addEventListener("keydown", (event) => {
      if (event.target.matches('[data-action="target-input"]') && event.key === "Enter") {
        event.preventDefault();
        handleTargetApply(event.target.value);
      }
    });

    document.addEventListener("change", (event) => {
      if (event.target.matches('[data-action="sort"]')) handleFilterChange("sortBy", event.target.value);
    });

    document.addEventListener("keydown", (event) => {
      const row = event.target.closest('.item-row[role="button"]');
      if (!row || (event.key !== "Enter" && event.key !== " ")) return;
      event.preventDefault();
      handleItemTap(row.dataset.type, row.dataset.id);
    });

    els.tabs.forEach((tab) => tab.addEventListener("click", () => handleTabChange(tab.dataset.view)));

    document.addEventListener("dragstart", (event) => {
      const card = event.target.closest("[data-plan-index]");
      if (!card) return;
      dragState.from = Number(card.dataset.planIndex);
      card.classList.add("dragging");
      event.dataTransfer.effectAllowed = "move";
    });

    document.addEventListener("dragend", (event) => {
      const card = event.target.closest("[data-plan-index]");
      if (card) card.classList.remove("dragging");
      dragState.from = null;
    });

    document.addEventListener("dragover", (event) => {
      if (dragState.from === null) return;
      if (event.target.closest("[data-plan-index]")) event.preventDefault();
    });

    document.addEventListener("drop", (event) => {
      const card = event.target.closest("[data-plan-index]");
      if (!card || dragState.from === null) return;
      event.preventDefault();
      reorderPlan(dragState.from, Number(card.dataset.planIndex));
      dragState.from = null;
    });

    document.addEventListener("touchstart", (event) => {
      const card = event.target.closest("[data-plan-index]");
      if (!card) return;
      dragState.touchFrom = Number(card.dataset.planIndex);
      dragState.touchOver = dragState.touchFrom;
    }, { passive: true });

    document.addEventListener("touchmove", (event) => {
      if (dragState.touchFrom === null) return;
      const touch = event.touches[0];
      const element = document.elementFromPoint(touch.clientX, touch.clientY);
      const card = element && element.closest("[data-plan-index]");
      if (card) dragState.touchOver = Number(card.dataset.planIndex);
    }, { passive: true });

    document.addEventListener("touchend", () => {
      if (dragState.touchFrom !== null && dragState.touchOver !== null) {
        reorderPlan(dragState.touchFrom, dragState.touchOver);
      }
      dragState.touchFrom = null;
      dragState.touchOver = null;
    });
  }

  readPreferences();
  loadSavedFromStorage();
  bindEvents();
  fetchAllData();
})();

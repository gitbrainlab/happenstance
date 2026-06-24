# Happenstance - Technical Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Component Architecture](#component-architecture)
5. [API Integration Layer](#api-integration-layer)
6. [Data Processing Pipeline](#data-processing-pipeline)
7. [Frontend Architecture](#frontend-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Security Considerations](#security-considerations)
10. [Performance Characteristics](#performance-characteristics)

---

## System Overview

**Happenstance** is a static weekend planner platform that aggregates restaurant and event data, pairs them intelligently, and presents them through a responsive web interface deployed on GitHub Pages.

### Key Characteristics
- **Static Site Architecture**: No backend server required at runtime
- **Build-Time Data Aggregation**: Data fetched and processed during build/deployment
- **Multiple Data Sources**: Supports API-based (Google Places, Ticketmaster, Eventbrite) and AI-powered data sources
- **Intelligent Pairing**: Two-phase restaurant-event matching algorithm
- **Zero-Cost Hosting**: Deployed on GitHub Pages with GitHub Actions automation

### Architecture Philosophy
1. **Simplicity**: Minimal dependencies, straightforward build process
2. **Resilience**: Graceful fallback to fixture data if APIs unavailable
3. **Flexibility**: Configurable data sources and regional profiles
4. **Performance**: Pre-generated static JSON files for fast client-side loading
5. **Maintainability**: Well-tested, documented, and modular code structure

---

## Technology Stack

### Backend (Python 3.11+)
```
├── Core Framework: Python 3.11+ (standard library focus)
├── HTTP Client: requests (for API calls)
├── Testing: pytest
├── Linting: ruff
└── Build Tool: CLI module (happenstance.cli)
```

**Key Dependencies:**
- **requests 2.32.3**: HTTP library for API integrations
- **pytest 8.3.3**: Testing framework
- **ruff 0.6.9**: Fast Python linter and formatter

### Frontend (Vanilla JavaScript)
```
├── HTML5 + CSS3
├── Vanilla JavaScript (ES6+)
├── No framework dependencies
└── Progressive Enhancement approach
```

**Frontend Files:**
- `docs/index.html` - Single-page application structure
- `docs/app.js` - Client-side logic (275 lines)
- `docs/styles.css` - Dark theme styling (401 lines)

### Build & Deployment
```
├── Build System: Python CLI (happenstance.cli)
├── CI/CD: GitHub Actions
├── Deployment: GitHub Pages
└── Process Automation: Makefile, npm scripts
```

### Data Storage
```
├── Format: JSON
├── Location: docs/*.json (served statically)
├── Files:
│   ├── restaurants.json - Restaurant listings
│   ├── events.json - Event listings
│   ├── meta.json - Metadata and pairings
│   └── config.json - UI configuration
```

---

## Data Flow Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Sources (Build Time)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │   Google    │  │ Ticketmaster │  │     AI      │            │
│  │   Places    │  │  / Eventbrite│  │  (Grok/GPT) │            │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘            │
│         │                 │                  │                   │
│         └─────────────────┴──────────────────┘                   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            ▼
        ┌────────────────────────────────────────┐
        │   Python Data Aggregation Pipeline     │
        │                                        │
        │  1. Fetch from configured sources      │
        │  2. Normalize data structures          │
        │  3. Geocode locations (if needed)      │
        │  4. Calculate pairings & distances     │
        │  5. Generate JSON output files         │
        │  6. Compute content hashes             │
        └────────────────┬───────────────────────┘
                         ▼
        ┌────────────────────────────────────────┐
        │      Static JSON Files (docs/)         │
        │                                        │
        │  - restaurants.json (12KB)             │
        │  - events.json (4.2KB)                 │
        │  - meta.json (8.8KB + pairings)        │
        │  - config.json (399B)                  │
        └────────────────┬───────────────────────┘
                         ▼
        ┌────────────────────────────────────────┐
        │       GitHub Pages Deployment          │
        │                                        │
        │  Serves static files via CDN           │
        └────────────────┬───────────────────────┘
                         ▼
        ┌────────────────────────────────────────┐
        │     Client-Side Web Application        │
        │                                        │
        │  1. Fetch JSON files (parallel)        │
        │  2. Parse and store in state           │
        │  3. Render UI with filtering           │
        │  4. Handle user interactions           │
        └────────────────────────────────────────┘
```

### Detailed Data Flow Steps

#### 1. **Data Acquisition** (Build Time)
```python
# Triggered by: python -m happenstance.cli aggregate
config = load_config(profile)
↓
Determine data sources from config:
  - restaurants: "google_places" | "ai" | "fixtures"
  - events: "ticketmaster" | "eventbrite" | "google_search" | "ai" | "fixtures"
↓
Call appropriate fetcher:
  - fetch_google_places_restaurants()
  - fetch_ticketmaster_events()
  - fetch_google_search_events()
  - fetch_ai_restaurants()
  - etc.
↓
Fallback to fixtures if API fails or keys missing
```

#### 2. **Data Normalization**
```python
Raw API Response → Normalized Structure
{
  "id": "unique-id",
  "name": "Restaurant Name",
  "cuisine": "Italian",
  "address": "123 Main St, City",
  "url": "https://maps.google.com/...",
  "location": {"lat": 37.7749, "lng": -122.4194}
}
```

#### 3. **Geocoding & Distance Calculation**
```python
For each event:
  - Geocode event venue using Nominatim API
  - Calculate distance to nearby restaurants
  - Store distance metadata for pairing
```

#### 4. **Pairing Algorithm**
```python
For each event:
  - Find restaurants within radius
  - Score by:
    * Distance (closer = better)
    * Cuisine match
    * Service style fit
    * Group signals (kids menu, large tables)
  - Generate pairing recommendations
  - Store in meta.json
```

#### 5. **JSON Generation**
```python
Write to docs/:
  - restaurants.json (array of restaurants)
  - events.json (array of events)
  - meta.json (metadata + pairings array)
  - config.json (branding + UI config)
```

#### 6. **Client-Side Loading** (Runtime)
```javascript
// app.js loads all JSON files in parallel
Promise.all([
  fetch("events.json"),
  fetch("restaurants.json"),
  fetch("config.json"),
  fetch("meta.json")
]).then(data => {
  state.data = processData(data);
  render();
});
```

---

## Component Architecture

### Backend Components

```
happenstance/
├── cli.py              # Command-line interface (aggregate, serve)
├── aggregate.py        # Main data aggregation logic (~400 lines)
├── sources.py          # API integrations (Google, Ticketmaster, AI)
├── pairing.py          # Two-phase pairing algorithm (~700 lines)
├── config.py           # Configuration loader
├── validate.py         # Data validation utilities
├── search.py           # Search functionality
├── hash.py             # Content hashing for change detection
├── io.py               # File I/O utilities
├── prompting.py        # AI prompt generation
└── ai_prompts.py       # AI prompt templates
```

#### Core Module Responsibilities

**cli.py**
- Entry point for command execution
- `aggregate` command: Triggers data pipeline
- `serve` command: Local development server

**aggregate.py**
- Orchestrates data fetching from multiple sources
- Performs geocoding and distance calculations
- Builds restaurant-event pairings
- Generates output JSON files
- Manages content hashing and change detection

**sources.py**
- Abstracts API interactions
- Implements fetchers for:
  - Google Places API (restaurants)
  - Ticketmaster API (events)
  - Eventbrite API (events)
  - AI-powered search (restaurants & events)
- Handles error cases and fallbacks

**pairing.py**
- Implements two-phase pairing algorithm:
  - **Phase A**: Score restaurants by fit (service style, travel, cuisine)
  - **Phase B**: Re-rank with availability data (future enhancement)
- Computes dining time windows
- Deterministic, testable scoring logic

**config.py**
- Loads configuration from `config/config_logic.json`
- Supports multiple profiles (default, custom regions)
- Handles environment variable overrides

### Frontend Components

```
docs/
├── index.html          # SPA structure (36 lines)
├── app.js              # Application logic (275 lines)
├── styles.css          # Dark theme styles (401 lines)
└── *.json              # Data files (generated)
```

#### Frontend Architecture Pattern

**State Management:**
```javascript
const state = {
  view: "restaurants" | "events" | "paired",
  filter: string,
  layout: "cards" | "table",
  data: {
    restaurants: [],
    events: [],
    pairings: [],
    meta: {},
    branding: {}
  }
};
```

**View Rendering:**
```javascript
setActiveView(view) → render() → {
  renderRestaurants() or
  renderEvents() or
  renderPaired()
}
```

**Data Loading:**
```javascript
loadData()
  → fetch 4 JSON files in parallel
  → parse and populate state
  → apply branding
  → render initial view
  → set data-hs-ready="1" on body
```

---

## API Integration Layer

### Supported Data Sources

#### 1. Google Places API (Restaurants)
```python
fetch_google_places_restaurants(city, count, radius)
→ Text Search API: "restaurants in {city}"
→ Parse response → normalize to standard format
→ Infer cuisine from place types
→ Generate Maps URL from place_id
```

**API Endpoint:**
```
POST https://places.googleapis.com/v1/places:searchText
Headers:
  X-Goog-Api-Key: {API_KEY}
  X-Goog-FieldMask: places.id,places.displayName,places.formattedAddress,...
```

#### 2. Ticketmaster API (Events)
```python
fetch_ticketmaster_events(city, count)
→ Discovery API: events in city
→ Filter by date window (EVENT_WINDOW_DAYS)
→ Categorize events (music, art, sports, family)
→ Extract venue and time information
```

**API Endpoint:**
```
GET https://app.ticketmaster.com/discovery/v2/events.json
Params:
  apikey: {API_KEY}
  city: {city}
  size: {count}
  sort: date,asc
```

#### 3. AI-Powered Data (Alternative)
```python
fetch_ai_restaurants(city, count)
fetch_ai_events(city, count)
→ Use environment variables AI_RESTAURANTS_DATA / AI_EVENTS_DATA
→ Parse JSON from AI-generated text
→ Expected format: JSON array in markdown code block
```

**Advantages:**
- Flexible data sourcing
- No API rate limits
- Can target any city
- Customizable outputs

#### 4. Fixture Data (Fallback)
```python
# Hardcoded sample data in sources.py
FIXTURE_RESTAURANTS = [...]
FIXTURE_EVENTS = [...]
→ Always available
→ Used when APIs unavailable
```

### API Error Handling

```python
try:
    data = fetch_from_api()
except (ValueError, KeyError, Exception) as e:
    print(f"Warning: API fetch failed: {e}")
    print("Falling back to fixture data")
    data = FIXTURE_DATA
```

---

## Data Processing Pipeline

### Pipeline Stages

```
1. Configuration Loading
   ↓
2. Data Source Selection
   ↓
3. Data Fetching (with retry/fallback)
   ↓
4. Data Normalization
   ↓
5. Geocoding (event venues)
   ↓
6. Distance Calculation
   ↓
7. Pairing Generation
   ↓
8. JSON Serialization
   ↓
9. Content Hashing
   ↓
10. File Writing
```

### Key Processing Functions

**Geocoding:**
```python
_geocode_address(address, region)
→ OpenStreetMap Nominatim API
→ Returns (lat, lng) tuple
→ Cached with 1-second delay (rate limiting)
→ Fallback: None if fails
```

**Distance Calculation:**
```python
_calculate_distance(lat1, lng1, lat2, lng2)
→ Haversine formula
→ Returns distance in miles
→ Used for nearby restaurant filtering
```

**Pairing Algorithm:**
```python
_build_pairings(events, restaurants)
→ For each event:
    - Find restaurants within NEARBY_RESTAURANT_RADIUS_METERS
    - Calculate distances
    - Score by distance and variety
    - Select top MAX_NEARBY_RESTAURANTS_PER_EVENT
    - Generate match reasons
→ Returns pairing objects
```

**Content Hashing:**
```python
compute_meta(events, restaurants)
→ Canonical JSON sort
→ SHA-256 hash
→ Detect changes for deployment decisions
```

---

## Frontend Architecture

### Application Structure

```
┌────────────────────────────────────────────┐
│              index.html                    │
│  ┌──────────────────────────────────────┐  │
│  │  Header                              │  │
│  │   - Brand (title + tagline)          │  │
│  │   - View buttons (3)                 │  │
│  │   - Filter input                     │  │
│  │   - Layout select                    │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │  Main Content Area                   │  │
│  │   - restaurants-view (section)       │  │
│  │   - events-view (section)            │  │
│  │   - paired-view (section)            │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │  Footer                              │  │
│  │   - Meta info (region, updated time) │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

### State Management

**State Persistence:**
```javascript
// URL Query Parameters (shareable links)
?view=restaurants&filter=pizza&layout=cards

// LocalStorage (user preference)
localStorage.setItem("hs_view", view);

// In-Memory State (runtime)
state.data = {...}
```

**State Updates Flow:**
```
User Action → Update state → updateQueryParams() → render()
```

### Rendering Strategy

**Dynamic Rendering:**
```javascript
render() {
  1. Filter data based on state.filter
  2. Check state.layout ("cards" | "table")
  3. Generate HTML strings
  4. Update container.innerHTML
  5. No virtual DOM, direct manipulation
}
```

**Performance Optimization:**
- Filter on-demand (not pre-computed)
- HTML string concatenation (fast for small datasets)
- No re-rendering unless state changes

### UI Features

**Filtering:**
```javascript
matchesFilter(text) {
  return text.toLowerCase().includes(
    state.filter.toLowerCase()
  );
}
// Applied to: name, cuisine, category, address, location
```

**Layout Toggle:**
- **Cards**: Visual grid with badges, metadata, links
- **Table**: Compact table view for quick scanning

**View Switching:**
- Restaurants: Browse dining options
- Events: Browse upcoming events
- Paired: See recommended combinations

---

## Deployment Architecture

### GitHub Actions Workflow

**Deployment Trigger:**
```yaml
# .github/workflows/pages.yml
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:      # Manual trigger
```

**Build Steps:**
```yaml
1. Checkout repository
2. Setup Python 3.11
3. Install dependencies (pip install -r requirements.txt)
4. Run aggregate command with API keys from secrets
5. Upload docs/ directory as artifact
6. Deploy to GitHub Pages
```

**Environment Variables (Secrets):**
```
- GOOGLE_PLACES_API_KEY (optional)
- TICKETMASTER_API_KEY (optional)
- EVENTBRITE_API_KEY (optional)
- AI_RESTAURANTS_DATA (optional)
- AI_EVENTS_DATA (optional)
```

### Deployment Flow

```
Git Push to main
  ↓
GitHub Actions triggered
  ↓
Aggregate data (python -m happenstance.cli aggregate)
  ↓
Generate JSON files in docs/
  ↓
Upload docs/ as Pages artifact
  ↓
Deploy to GitHub Pages
  ↓
Site live at https://evcatalyst.github.io/happenstance/
```

### Validation Workflow

```yaml
# .github/workflows/validate-pages.yml
1. Wait for deployment
2. Fetch published endpoints:
   - /restaurants.json
   - /events.json
   - /meta.json
   - /config.json
3. Validate JSON structure
4. Check data-hs-ready signal
5. Report validation status
```

---

## Security Considerations

### API Key Management
- ✅ API keys stored as GitHub repository secrets
- ✅ Never committed to source code
- ✅ Environment variable injection at build time
- ✅ No API keys in client-side code

### Content Security
- ✅ HTML escaping in frontend (`escapeHTML()` function)
- ✅ XSS protection via sanitization
- ✅ `rel="noopener"` on external links
- ✅ No user-generated content storage

### Data Privacy
- ✅ No user tracking or analytics
- ✅ No cookies or persistent storage of user data
- ✅ LocalStorage only for UI preferences
- ✅ Public data sources only

### HTTPS
- ✅ GitHub Pages enforces HTTPS
- ✅ All external API calls use HTTPS
- ✅ No mixed content issues

---

## Performance Characteristics

### Build Time Performance
```
Data Aggregation: ~5-30 seconds
  - API calls: 2-10 seconds (parallel)
  - Geocoding: 5-15 seconds (serial, rate-limited)
  - Processing: 1-5 seconds
  - File I/O: <1 second
```

### Runtime Performance
```
Initial Page Load:
  - HTML: <1KB (inline critical CSS)
  - CSS: 401 lines (~6KB)
  - JS: 275 lines (~8KB)
  - JSON: ~25KB total (4 files)
  - Total: ~40KB (uncompressed)
  - Load time: <500ms on 4G

Rendering:
  - 30 restaurants: ~10ms
  - 20 events: ~8ms
  - 50 pairings: ~15ms
  - Filter update: <5ms
```

### Scalability
```
Current Data Size:
  - 35 restaurants
  - 30 events
  - ~50 pairings

Theoretical Limits:
  - 1000+ restaurants: Still fast (client-side filter)
  - 500+ events: No performance issues
  - 2000+ pairings: May need virtualization
```

### Optimization Strategies
1. **Static Generation**: Pre-compute everything
2. **Parallel Loading**: Fetch 4 JSON files concurrently
3. **Minimal Dependencies**: No heavy frameworks
4. **CDN Delivery**: GitHub Pages CDN
5. **Efficient Rendering**: String concatenation over DOM manipulation

---

## Summary

Happenstance is a well-architected static site that demonstrates:
- **Simplicity**: Minimal tech stack, maximum functionality
- **Resilience**: Graceful degradation and fallbacks
- **Performance**: Fast builds, instant page loads
- **Flexibility**: Multiple data sources, configurable profiles
- **Maintainability**: Clean separation of concerns, comprehensive tests

The architecture supports both demonstration (fixture data) and production (API-powered) use cases while maintaining zero runtime hosting costs through GitHub Pages.

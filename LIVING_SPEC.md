# Astrology Bot for Poe — Living Spec

This document tracks the implementation progress of the Astrology Bot project for the Poe platform.

---

## Project Overview

A natal chart calculation and interpretation bot for Poe that:
- Calculates birth charts using Swiss Ephemeris (pyswisseph)
- Renders interactive SVG chart wheels in the Canvas UI
- Provides LLM-powered astrological interpretations via Claude
- Supports transit overlays for comparing natal charts with current planetary positions

---

## Architecture

```
┌─────────────────────────────────────────────┐
│             Poe Platform                    │
│  ┌─────────────────────────────────────┐    │
│  │           Canvas App                 │    │
│  │  ┌───────────┐  ┌────────────────┐  │    │
│  │  │ Birth Data │  │  Chart Wheel   │  │    │
│  │  │   Form     │  │  (SVG render)  │  │    │
│  │  └─────┬─────┘  └───────▲────────┘  │    │
│  │        │                 │           │    │
│  │        │    ┌────────────┴────┐      │    │
│  │        │    │  Chat / Analysis │      │    │
│  │        │    │     Panel        │      │    │
│  │        │    └────────────┬────┘      │    │
│  └────────┼─────────────────┼───────────┘    │
│           │  postMessage     │               │
│           ▼                  ▼               │
│  ┌─────────────────────────────────────┐     │
│  │        Server Bot (Modal)           │     │
│  │  ┌──────────────┐ ┌──────────────┐  │     │
│  │  │  Ephemeris    │ │  LLM-Powered │  │     │
│  │  │  Calculator   │ │  Interpreter │  │     │
│  │  │  (pyswisseph) │ │  (via Poe)   │  │     │
│  │  └──────────────┘ └──────────────┘  │     │
│  └─────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

---

## Implementation Progress

### Phase 1: Core Bot Infrastructure (HIGH PRIORITY) ✅

- [x] Create living spec document
- [x] Install required dependencies
  - `pyswisseph` (Swiss Ephemeris)
  - `timezonefinder` (Lat/lng → timezone)
  - `geopy` (City geocoding)
- [x] Create `chart_engine.py` with:
  - Planet position calculations
  - House calculations (Placidus system)
  - Aspect calculations
  - Geocoding with timezone resolution
- [x] Create `astrology_bot.py` with:
  - FastAPI Poe bot implementation
  - JSON protocol for Canvas communication
  - LLM interpretation streaming
- [x] Update `requirements.txt`

### Phase 2: Canvas Frontend (HIGH PRIORITY) ✅

- [x] Create `canvas/` directory structure:
  - `index.html` - Main entry point (includes CSS & JS inline)
- [x] Implement birth data form
- [x] Implement SVG chart wheel renderer with:
  - 12 sign divisions with glyphs
  - House cusps (1-12)
  - Planet positions with glyphs
  - Aspect lines
- [x] Implement chat panel for streaming interpretations
- [x] Follow-up Q&A functionality

### Phase 3: Integration & Testing (MEDIUM PRIORITY) 🔄

- [x] Test chart calculation locally with hardcoded data
- [ ] Test Canvas ↔ Bot communication protocol
- [ ] Deploy to Modal
- [ ] Register bot in Poe Creator Dashboard
- [ ] Upload Canvas app to Poe
- [ ] End-to-end testing on Poe platform

### Phase 4: Advanced Features (LOW PRIORITY)

- [x] Transit overlay mode (rendered, needs UI polish)
- [ ] Aspect table display
- [ ] Synastry (comparison of two charts)
- [ ] Dark/light theme toggle
- [ ] Share as image (SVG → PNG export)
- [x] Follow-up Q&A with chart context

---

## External Work Required (Outside This Repo)

1. **Poe Creator Dashboard Setup:**
   - Create a new Server Bot in Poe Creator
   - Configure bot settings (name, avatar, description)
   - Set the server endpoint URL after Modal deployment
   - Synchronize bot settings after deployment

2. **Canvas App Registration:**
   - Upload Canvas app files (index.html, etc.) to Poe
   - Link Canvas app to the server bot
   - Configure Canvas dimensions and settings

3. **Modal Account Setup:**
   - Ensure Modal is installed and authenticated
   - Set up POE_ACCESS_KEY environment variable

4. **Swiss Ephemeris Data Files:**
   - Download ephemeris files (optional - pyswisseph includes basic data)
   - For higher accuracy, download full ephemeris from astro.com
   - Configure `swe.set_ephe_path()` if using external files

---

## Response Protocol

The server bot sends **both** structured chart JSON and streamed interpretation text through the same response channel:

**Step 1:** Bot yields structured JSON:
```json
{
  "type": "chart_result",
  "chart": {
    "planets": {...},
    "houses": {...},
    "ascendant": {...},
    "midheaven": {...},
    "aspects": [...],
    "meta": {...}
  }
}
```

**Step 2:** Subsequent yields are streamed interpretation text from Claude

**Canvas Handling:**
```javascript
let buffer = "";
let chartRendered = false;

function handleBotChunk(text) {
  buffer += text;
  
  if (!chartRendered && buffer.includes("\n---\n")) {
    const [jsonPart, rest] = buffer.split("\n---\n");
    const chartData = JSON.parse(jsonPart);
    renderChartWheel(chartData.chart);
    chartRendered = true;
    buffer = rest || "";
  }
  
  if (chartRendered) {
    appendToChatPanel(buffer);
    buffer = "";
  }
}
```

---

## Key Dependencies

```
fastapi-poe>=0.0.46
pyswisseph>=2.10.0
timezonefinder>=6.2.0
geopy>=2.4.0
```

---

## Build Order

1. Get `calculate_chart()` working locally with hardcoded test data
2. Wire it into a minimal `fastapi_poe` server bot — verify it responds
3. Build the Canvas form → send birth data → receive chart JSON
4. Render the SVG chart wheel
5. Add the LLM interpretation streaming
6. Polish UI, add transit mode, etc.

---

## Last Updated

2026-02-08

## Status

✅ Phase 1-2 Complete | 🔄 Phase 3 Ready for Testing

## Next Steps

1. Set up Modal account and credentials
2. Deploy bot: `modal deploy astrology_bot.py`
3. Register in Poe Creator Dashboard
4. Upload Canvas app
5. Test end-to-end

## Files Created

- `astrology_bot.py` - Main server bot
- `chart_engine.py` - Swiss Ephemeris calculations
- `canvas/index.html` - Canvas frontend (single file)
- `setup_ephe.py` - Helper to download ephemeris files
- `ephe/` - Swiss Ephemeris data files
- `requirements.txt` - Updated dependencies

# Astrology Bot for Poe — Architecture Overview

---

## Project Overview

A natal chart calculation and interpretation bot for Poe that:
- Calculates birth charts using Swiss Ephemeris (pyswisseph)
- Renders interactive SVG chart wheels in the Canvas UI
- Provides LLM-powered astrological interpretations
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

## Features

### Core Features
- **Accurate Chart Calculation**: Swiss Ephemeris (pyswisseph) for precise planetary positions
- **Interactive Canvas App**: Beautiful SVG chart wheel with dark/light themes
- **LLM Interpretations**: Streaming astrological readings from Claude, GPT, Gemini, and other Poe models
- **Multiple House Systems**: Placidus, Whole Sign, Equal, Koch, Regiomontanus, Campanus, Porphyry
- **Tropical & Sidereal Zodiacs**: Includes Lahiri, Fagan-Bradley, Raman, Krishnamurti ayanamsas
- **Transit Overlays**: Compare current planetary positions to natal chart
- **Follow-up Q&A**: Ask questions about your chart with full context
- **Export Options**: Download as PNG, PDF, or Markdown

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

**Step 2:** Subsequent yields are streamed interpretation text from the LLM

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

## Project Structure

```
poe-astrology-bot/
├── astrology_bot.py       # Main FastAPI bot (fastapi_poe)
├── chart_engine.py        # Swiss Ephemeris chart calculations
├── setup_ephe.py          # Downloads ephemeris data files
├── canvas/
│   └── index.html         # Canvas app (form + SVG wheel rendering)
├── ephe/                  # Swiss Ephemeris data files
├── requirements.txt       # Python dependencies
├── .env.example           # Configuration template
├── README.md              # Project documentation
└── LICENSE                # MIT License
```

---

## Deployment

1. Set up Modal account and credentials
2. Deploy bot: `modal deploy astrology_bot.py`
3. Register in Poe Creator Dashboard
4. Upload Canvas app (`canvas/index.html`)
5. Configure environment variables:
   - `POE_ACCESS_KEY`: Your bot's access key
   - `POE_BOT_NAME`: Your bot's name
   - `POE_MODEL`: Default model (e.g., `Claude-Sonnet-4.6`)

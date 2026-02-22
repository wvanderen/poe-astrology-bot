# Poe Astrology Bot

A natal chart calculation and interpretation bot for the [Poe platform](https://poe.com). Features a rich Canvas app frontend with interactive SVG chart wheels and LLM-powered interpretations.

## Features

- **Accurate Chart Calculation**: Uses Swiss Ephemeris (pyswisseph) for precise planetary positions
- **Interactive Canvas App**: Beautiful SVG chart wheel with dark/light themes
- **LLM Interpretations**: Streaming astrological readings from Claude, GPT, Gemini, and other Poe models
- **Multiple House Systems**: Placidus, Whole Sign, Equal, Koch, Regiomontanus, Campanus, Porphyry
- **Tropical & Sidereal Zodiacs**: Includes Lahiri, Fagan-Bradley, Raman, Krishnamurti ayanamsas
- **Transit Overlays**: Compare current planetary positions to natal chart
- **Follow-up Q&A**: Ask questions about your chart with full context
- **Export Options**: Download as PNG, PDF, or Markdown

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Canvas App     │────▶│  Astrology Bot  │────▶│  LLM (Poe API)   │
│  (index.html)   │     │  (FastAPI)      │     │  (Claude/GPT/etc)│
└─────────────────┘     └────────┬────────┘     └──────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Chart Engine   │
                        │  (pyswisseph)   │
                        └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- [Modal](https://modal.com) account for deployment
- Poe bot access key (optional for local dev)

### Setup

1. **Clone and install dependencies:**
   ```bash
   git clone <repo-url>
   cd poe-astrology-bot
   pip install -r requirements.txt
   ```

2. **Download Swiss Ephemeris data:**
   ```bash
   python setup_ephe.py
   ```

3. **Run locally:**
   ```bash
   uvicorn astrology_bot:fastapi_app --reload
   ```

### Deploy to Modal

```bash
modal deploy astrology_bot.py
```

### Configure Poe Bot

1. Go to [Poe Creator Dashboard](https://poe.com/create_bot)
2. Create a new Server Bot
3. Set the endpoint to your Modal URL
4. Upload `canvas/index.html` as the Canvas app
5. Set environment variables:
   - `POE_ACCESS_KEY`: Your bot's access key
   - `POE_BOT_NAME`: Your bot's name
   - `POE_MODEL`: Default model (e.g., `Claude-Sonnet-4.6`)

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
├── .env.example          # Configuration template
└── LIVING_SPEC.md        # Detailed architecture notes
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POE_ACCESS_KEY` | Bot access key from Poe | None |
| `POE_BOT_NAME` | Bot name on Poe | None |
| `POE_MODEL` | Default LLM for interpretations | `Kimi-K2.5` |

### Chart Options

The Canvas app supports:

- **House Systems**: Placidus, Whole Sign, Equal, Koch, Regiomontanus, Campanus, Porphyry
- **Zodiac Type**: Tropical (Western) or Sidereal (Vedic)
- **Sidereal Ayanamsas**: Lahiri, Fagan-Bradley, Raman, Krishnamurti, Jyotish
- **Interpretation Models**: Claude, GPT, Gemini, Kimi, and more

## API Protocol

The bot communicates with the Canvas app via JSON messages:

### Birth Data Request
```json
{
  "type": "birth_data",
  "date": "1992-10-28",
  "time": "22:30",
  "city": "Austin, TX",
  "house_system": "placidus",
  "zodiac_type": "tropical",
  "model": "Claude-Sonnet-4.6"
}
```

### Chart Response
```json
{
  "type": "chart_result",
  "chart": {
    "planets": {"Sun": {"sign": "Scorpio", "degree": 5.24}, ...},
    "houses": {"1st": {"sign": "Aquarius", "degree": 12.3}, ...},
    "aspects": [{"planet1": "Sun", "planet2": "Moon", "aspect": "trine", "orb": 2.1}, ...],
    "ascendant": {"sign": "Aquarius", "degree": 12.3},
    "midheaven": {"sign": "Scorpio", "degree": 8.45}
  }
}
```

## Dependencies

- **fastapi-poe**: Poe bot framework
- **pyswisseph**: Swiss Ephemeris bindings
- **timezonefinder**: Timezone lookup from coordinates
- **geopy**: Geocoding (city name to coordinates)

## License

MIT

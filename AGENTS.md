# Poe Astrology Bot - Agent Workspace

## Project Overview

Astrology bot for Poe platform with Canvas app frontend. Calculates natal charts using Swiss Ephemeris and provides LLM-powered interpretations.

## Key Commands

### Task Management (td)
```bash
# View status
td status

# List all tasks
td list

# Start working on a task
td start <task-id>
```

### Running the Bot
```bash
# Local development
uvicorn astrology_bot:app --reload

# Deploy to Modal
modal deploy
```

## Project Structure

```
poe-astrology-bot/
├── astrology_bot.py       # Main FastAPI bot (fastapi_poe)
├── chart_engine.py       # Swiss Ephemeris chart calculations
├── canvas/              # Canvas app (HTML/JS/CSS)
│   └── index.html     # Chart form + SVG wheel rendering
├── ephe/               # Swiss Ephemeris data files
├── requirements.txt      # Python dependencies
├── .env.example         # Configuration template
└── .todos/             # TD database
```

## Current Focus

### Priority 1: Poe Job Application (Monday deadline!)
- ✅ Portfolio project: Working bot with Canvas app
- td-53cccf: Visual Revamp of Chart (in review)
- td-2e4c42: Allow model selection
- td-5127d4: Allow initial context + follow-up questions
- td-162085: Add aspect tables to canvas

### Next: Resume + Cover Letter
- td-b759b5 (in clawd): Fine tune resume
- td-fc50a9 (in clawd): Write cover letter

## External Dependencies

### Interpretation Oracle
Located in separate repo: `/home/lem/dev/astrology-oracle`

- Standalone microservice for interpretation retrieval
- Uses Pinecone vector DB + OpenAI embeddings
- Integrates with bot via HTTP API
- See `td-57dfe5`: Integrate oracle with astrology bot

### Deployment
Target: Modal (Python-native, auto-scaling)

## Notes

- Chart calculation: pyswisseph + Swiss Ephemeris
- Canvas: HTML/JS app that polls for bot responses
- House systems: Whole sign (default), configurable
- Zodiac: Tropical (default), configurable
- LLM: Claude for interpretations (can select other models)

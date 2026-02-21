# Interpretation Oracle - Vector DB Requirements

**Epic:** td-77df6f "Interpretation Oracle - Vector DB"
**Status:** Planning
**Target MVP:** Planetary positions (transits and houses as follow-ups)
**Timeline:** Parallel with portfolio project for Monday submission

---

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────┐
│   Astrology Bot (fastapi_poe)    │
│   ────────────────────────────────  │
│   Receives birth data from Canvas   │
└────────┬────────────────────────────┘
         │ HTTP API call
         ▼
┌─────────────────────────────────────┐
│   Interpretation Oracle Service    │
│   (Standalone Microservice)        │
│   ────────────────────────────────  │
│   • FastAPI                      │
│   • Pinecone Vector DB           │
│   • OpenAI Embeddings            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Pinecone Cloud Vector Store     │
│   ────────────────────────────────  │
│   • Semantic search               │
│   • Relevance ranking             │
│   • Metadata filtering            │
└─────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|---------|-----------|
| **Vector DB** | Pinecone (hosted) | Easy setup, great API, callable from Poe server, scales well |
| **Tech Stack** | Python + FastAPI | Consistent with existing bot, async support |
| **Architecture** | Standalone microservice | Modular, deployable independently, reusable across projects |
| **API Pattern** | HTTP REST (async) | Simple, testable, with fallback to LLM-only |
| **MVP Scope** | Planetary positions (7 planets × 12 signs) | Proof of concept, expandable later |

---

## Data Model

### Interpretation Document Structure

```json
{
  "id": "interpretation_sun_aries_arroyo",
  "text": "With Sun in Aries, you are a natural leader...",
  "metadata": {
    "planet": "Sun",
    "sign": "Aries",
    "source": "arroyo",
    "source_title": "Astrology, Karma, and Transformation",
    "type": "natal_planet",
    "tags": ["leadership", "action", "initiation"]
  },
  "embedding": [0.123, 0.456, ...] // generated at ingest
}
```

### MVP Scope: Planetary Positions

**Planets (7):**
- Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn

**Signs (12):**
- Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces

**Total combinations for MVP:** 84 interpretations minimum (7 × 12)

**Future expansions:**
- Transits: 7 transit planets × 12 signs × 7 natal planets = 588 combinations
- Houses: 12 house positions × 7 planets = 84 combinations
- Aspects: 5 aspect types × planet combinations = 1000+ combinations

---

## Task Breakdown

### 1. Setup & Infrastructure (td-89a5ee)

**Deliverables:**
- Pinecone account created
- Index configured (dimension: 1536 for OpenAI embeddings)
- API keys stored in `.env`
- Basic insert/query operations tested

**Configuration:**
```bash
# .env
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
PINECONE_INDEX_NAME=astrology-interpretations
OPENAI_API_KEY=...  # for embeddings
```

---

### 2. Data Curation (td-1e936b)

**Deliverables:**
- Curated interpretation texts in JSON/CSV format
- 84 interpretations minimum (7 planets × 12 signs)
- Source attribution documented
- Consistent formatting

**Format Example:**
```json
[
  {
    "planet": "Sun",
    "sign": "Aries",
    "text": "With Sun in Aries, you are a natural leader...",
    "source": "Arroyo",
    "source_title": "Astrology, Karma, and Transformation",
    "tags": ["leadership", "action", "pioneering"]
  },
  // ... 83 more
]
```

**Curated Sources (MVP):**
- 1-2 modern sources (e.g., Arroyo, Tarnas)
- Focused on planetary positions only
- Psychological, warm, accessible tone

**Data Ingestion (Future):**
- Web scraping from astrology sites (with permission)
- OCR from public domain books (Lilly, Bonatti)
- Manual transcription for high-quality sources

---

### 3. Data Ingestion Pipeline (td-93e91b)

**Deliverables:**
- Python script: `ingest_interpretations.py`
- Reads JSON/CSV source files
- Generates embeddings via OpenAI API
- Batch inserts into Pinecone with metadata
- Handles updates/replacements
- Error handling and logging

**Script Interface:**
```bash
python ingest_interpretations.py \
  --source data/interpretations.json \
  --pinecone-index astrology-interpretations \
  --batch-size 50
```

**Flow:**
1. Load source file
2. For each interpretation:
   - Generate text embedding (OpenAI `text-embedding-ada-002`)
   - Prepare vector + metadata payload
   - Insert into Pinecone
3. Log successes/failures
4. Report final count

---

### 4. Query API (td-3da1fc)

**Deliverables:**
- FastAPI service with endpoint
- Endpoint: `POST /query`
- Request: chart data + optional context
- Response: ranked interpretations with relevance scores

**API Contract:**

```python
# Request
POST /query
{
  "chart_data": {
    "planets": {
      "Sun": {"sign": "Aries", "degree": 12.5},
      "Moon": {"sign": "Scorpio", "degree": 22.3},
      // ...
    },
    "ascendant": {"sign": "Leo"},
    "transits": {
      "Sun": {"sign": "Pisces"},  // if provided
    }
  },
  "context": {
    "focus": ["natal", "transits"],  // optional
    "sources": ["arroyo"],  // optional filter
    "max_results": 5  // optional
  }
}

# Response
{
  "interpretations": [
    {
      "text": "With Sun in Aries, you are a natural leader...",
      "metadata": {
        "planet": "Sun",
        "sign": "Aries",
        "source": "arroyo",
        "type": "natal_planet"
      },
      "score": 0.87
    },
    // ... more results
  ]
}
```

**Query Logic:**
1. Extract planetary placements from chart
2. Build semantic query for each placement
3. Query Pinecone with metadata filters (planet/sign)
4. Aggregate results, rank by relevance
5. Return top N with attribution

---

### 5. Deployment (td-0aa6b0)

**Deliverables:**
- Oracle service deployed (Railway/Fly.io/Modal)
- Environment variables configured
- Health check endpoint (`GET /health`)
- Logging enabled
- Deployment documented

**Deployment Options:**

| Platform | Pros | Cons |
|----------|-------|-------|
| **Railway** | Easy, auto-deploy, PostgreSQL included | Limited free tier |
| **Fly.io** | Fast, scalable, global regions | Requires Dockerfile setup |
| **Modal** | Serverless, Python-native, auto-scale | Cold starts on first request |

**Recommended:** **Modal** (fastest to get running, Python-native, scales well for sporadic traffic)

**Health Check:**
```python
GET /health
{
  "status": "ok",
  "pinecone": "connected",
  "index": "astrology-interpretations",
  "document_count": 84
}
```

---

### 6. Bot Integration (td-57dfe5)

**Deliverables:**
- Astrology bot updated to call oracle API
- Oracle context injected into LLM prompt
- Error handling with fallback to LLM-only
- Request timeout handling

**Integration Flow:**
```python
async def get_interpretation(self, chart: dict, request: fp.QueryRequest):
    # Try oracle first
    try:
        oracle_response = await call_oracle_api(chart)
        interpretations = oracle_response["interpretations"]
        # Inject into LLM prompt
        prompt = self.build_interpretation_prompt(chart, interpretations)
    except (TimeoutError, APIError):
        # Fallback to LLM-only
        interpretations = []
        prompt = self.build_interpretation_prompt(chart)

    # Stream from LLM
    async for msg in fp.stream_request(new_request, poe_model, access_key):
        yield msg
```

**Prompt Enhancement:**
```
Original:
"You are an expert Western astrologer. Analyze this chart..."

Enhanced:
"You are an expert Western astrologer. Analyze this chart with
reference to these classical and modern interpretations:

**Relevant Interpretations:**
• [source: Arroyo] With Sun in Aries, you are a natural leader...
• [source: Tarnas] Moon in Scorpio brings emotional depth...

Now provide your interpretation, informed by these sources..."
```

---

### 7. Testing & Validation (td-90c6db)

**Deliverables:**
- Test suite with sample charts
- Quality baseline documented
- Edge cases identified
- A/B test: LLM with vs without oracle

**Test Cases:**
- Known charts (celebrity births)
- Edge cases (extreme lat/long, timezones)
- Oracle unavailable (fallback behavior)
- Partial chart data (missing time)
- Multiple requests (concurrent)

**Quality Metrics:**
- Relevance of returned interpretations (human-rated)
- LLM response quality (with vs without oracle)
- Response time (oracle adds ~100-200ms)
- Error rate (< 1%)

---

### 8. Documentation (td-165a7e)

**Deliverables:**
- `INTERPRETATION_ORACLE.md` (this file)
- `API_REFERENCE.md` (endpoint documentation)
- `DEPLOYMENT.md` (setup + deploy guide)
- Code comments and docstrings
- README section on oracle usage

**Reusability Examples:**
```python
# Daily Digest
from oracle import query_interpretations
daily_chart = get_chart_for_day()
insights = query_interpretations(daily_chart, focus=["transits"])

# Catalyst
ritual_chart = get_ritual_chart(user_id, date)
insights = query_interpretations(ritual_chart)
```

---

## API Reference

### Endpoints

#### `POST /query`

Query interpretations for a chart.

**Request:**
```json
{
  "chart_data": {
    "planets": { ... },
    "ascendant": { ... },
    "transits": { ... }  // optional
  },
  "context": {
    "focus": ["natal"],
    "sources": ["arroyo"],
    "max_results": 5
  }
}
```

**Response:**
```json
{
  "interpretations": [
    {
      "text": "...",
      "metadata": { ... },
      "score": 0.87
    }
  ],
  "total_results": 5,
  "query_time_ms": 145
}
```

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "pinecone": "connected",
  "index": "astrology-interpretations",
  "document_count": 84
}
```

---

## Dependencies

### Python Packages

```
fastapi>=0.104.0
uvicorn>=0.24.0
pinecone-client>=2.2.4
openai>=1.3.0
pydantic>=2.5.0
python-dotenv>=1.0.0
httpx>=0.25.0
```

### External Services

- **Pinecone:** Vector DB hosting
- **OpenAI:** Embedding generation (text-embedding-ada-002)
- **Hosting:** Railway/Fly.io/Modal (deployment)

---

## Timeline & Milestones

### Week 1: Setup + Ingestion
- [ ] Set up Pinecone and generate embeddings
- [ ] Curate MVP data (84 interpretations)
- [ ] Build ingestion pipeline
- [ ] Load data into Pinecone

### Week 2: API + Integration
- [ ] Build query API
- [ ] Deploy service
- [ ] Integrate with astrology bot
- [ ] Test with sample charts

### Week 3: Expansion (if needed)
- [ ] Add transits support
- [ ] Add house positions
- [ ] Expand interpretation sources
- [ ] A/B testing and optimization

---

## Decisions (Answered)

1. **✅ Deployment platform:** **Modal** - already used for poe-astrology-bot, perfect fit
2. **✅ Fallback strategy:** **LLM-only response with warning** - if oracle fails, continue with standard LLM interpretation and show warning to user
3. **✅ Embedding model:** **No preference** - either `text-embedding-ada-002` or `text-embedding-3-small` is fine

---

## Open Questions

1. **Batch size for ingest:** 50 (default) or larger for speed?
2. **Interpretation attribution:** Show source names (Arroyo, etc.) or aggregate without attribution?

---

## Success Criteria

- [ ] Oracle API returns relevant interpretations for test charts
- [ ] Integration with astrology bot successful (LLM uses oracle context)
- [ ] Service deployed and accessible
- [ ] Fallback to LLM-only works when oracle is unavailable
- [ ] Response time < 500ms for oracle query
- [ ] Documentation complete for reusability
- [ ] Ready to demonstrate with portfolio project for Monday submission

---

**Created:** 2026-02-21
**Status:** Ready to implement
**Next:** Start with td-89a5ee "Set up Pinecone vector DB"

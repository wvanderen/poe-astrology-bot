"""

Astrology Bot for Poe

A natal chart calculation and interpretation bot that:
1. Receives birth data from Canvas app
2. Calculates astrological chart using Swiss Ephemeris
3. Returns chart JSON for Canvas rendering
4. Streams LLM-powered interpretation from Claude

"""

from __future__ import annotations

import json
import os
import re
from typing import AsyncIterable

import fastapi_poe as fp
from modal import App, Image, asgi_app

from chart_engine import calculate_chart, calculate_transits


def parse_plain_text_birth_data(text: str) -> dict | None:
    """
    Parse plain text birth data input.

    Supports formats like:
    - "1992-10-28, 22:30, Lexington, KY"
    - "1992-10-28 22:30 Lexington, KY"
    - "October 28, 1992, 10:30 PM, Paris, France"

    Returns dict with date, time, city or None if parsing fails.
    """
    text = text.strip()

    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2}/\d{1,2}/\d{4})",
        r"(\d{1,2}-\d{1,2}-\d{4})",
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
    ]

    time_patterns = [
        r"(\d{1,2}:\d{2})",
        r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))",
        r"(\d{1,2}\s*(?:AM|PM|am|pm))",
    ]

    date_match = None
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_match = match.group(1)
            break

    if not date_match:
        return None

    time_match = None
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            time_match = match.group(1)
            break

    if not time_match:
        return None

    remaining = text
    remaining = re.sub(re.escape(date_match), "", remaining, count=1)
    remaining = re.sub(re.escape(time_match), "", remaining, count=1)

    city_match = re.search(
        r"([A-Za-z][A-Za-z\s]+,\s*[A-Za-z]{2,}(?:\s+[A-Za-z]+)?)", remaining
    )
    if city_match:
        city = city_match.group(1).strip()
    else:
        city = remaining.strip(" ,;-:")

    city = re.sub(r"\s+", " ", city).strip()

    if len(city) < 2:
        return None

    parsed_date = normalize_date(date_match)
    parsed_time = normalize_time(time_match)

    if not parsed_date or not parsed_time:
        return None

    return {
        "date": parsed_date,
        "time": parsed_time,
        "city": city,
    }


def normalize_date(date_str: str) -> str | None:
    """Convert various date formats to YYYY-MM-DD."""
    months = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
    }

    if re.match(r"\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", date_str)
    if match:
        return f"{match.group(3)}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"

    match = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})$", date_str)
    if match:
        return f"{match.group(3)}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"

    for month_name, month_num in months.items():
        match = re.search(
            rf"({month_name})\s+(\d{{1,2}}),?\s+(\d{{4}})", date_str, re.IGNORECASE
        )
        if match:
            day = match.group(2).zfill(2)
            year = match.group(3)
            return f"{year}-{month_num}-{day}"

    return None


def normalize_time(time_str: str) -> str | None:
    """Convert various time formats to HH:MM (24-hour)."""
    time_str = time_str.strip()

    match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?$", time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = match.group(2)
        am_pm = match.group(3)

        if am_pm:
            am_pm = am_pm.upper()
            if am_pm == "PM" and hour != 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0

        return f"{hour:02d}:{minute}"

    match = re.match(r"(\d{1,2})\s*(AM|PM)$", time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        am_pm = match.group(2).upper()

        if am_pm == "PM" and hour != 12:
            hour += 12
        elif am_pm == "AM" and hour == 12:
            hour = 0

        return f"{hour:02d}:00"

    return None


# Configuration
bot_access_key = os.getenv("POE_ACCESS_KEY")
bot_name = os.getenv("POE_BOT_NAME", "")
poe_model = os.getenv("POE_MODEL", "Kimi-K2.5")


class AstrologyBot(fp.PoeBot):
    """
    Astrology natal chart bot.

    Handles both chart calculation and LLM interpretation.
    """

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        """
        Main response handler.

        Protocol:
        1. Parse incoming message for birth data JSON
        2. Calculate chart
        3. Yield chart JSON for Canvas rendering
        4. Stream LLM interpretation
        """
        last_message = request.query[-1].content

        # Try to parse structured birth data from Canvas
        try:
            data = json.loads(last_message)

            if data.get("type") == "birth_data":
                # Calculate natal chart
                chart = calculate_chart(
                    date=data["date"],
                    time=data["time"],
                    city=data["city"],
                    house_system=data.get("house_system", "placidus"),
                    zodiac_type=data.get("zodiac_type", "tropical"),
                    sidereal_mode=data.get("sidereal_mode", "lahiri"),
                )

                # Check for transit date
                transit_data = data.get("transit_date")
                if transit_data:
                    transits = calculate_transits(chart, transit_data)
                    chart["transits"] = transits

                # Send chart JSON for Canvas rendering (with delimiter)
                chart_json = json.dumps(
                    {
                        "type": "chart_result",
                        "chart": chart,
                    }
                )
                yield fp.PartialResponse(text=chart_json + "\n---\n")

                # Stream the interpretation
                async for chunk in self.get_interpretation(chart, request):
                    yield chunk
                return

            elif data.get("type") == "follow_up":
                # Handle follow-up questions with chart context
                chart_data = data.get("chart_data")
                question = data.get("question", "")
                async for chunk in self.get_follow_up_response(
                    chart_data, question, request
                ):
                    yield chunk
                return

        except (json.JSONDecodeError, KeyError, ValueError):
            pass

        birth_data = parse_plain_text_birth_data(last_message)
        if birth_data:
            chart = calculate_chart(
                date=birth_data["date"],
                time=birth_data["time"],
                city=birth_data["city"],
            )

            chart_json = json.dumps(
                {
                    "type": "chart_result",
                    "chart": chart,
                }
            )
            yield fp.PartialResponse(text=chart_json + "\n---\n")

            async for chunk in self.get_interpretation(chart, request):
                yield chunk
            return

        yield fp.PartialResponse(
            text="Welcome to the Astrology Bot! 🌟\n\n"
            "I can calculate your natal birth chart and provide detailed astrological interpretations. "
            "Please use the birth data form to enter your details.\n\n"
            "I need:\n"
            "• Birth date (YYYY-MM-DD)\n"
            "• Birth time (HH:MM, 24-hour format)\n"
            "• Birth city (e.g., 'Austin, TX' or 'Paris, France')\n\n"
            "Or just send: `1992-10-28, 22:30, Lexington, KY`"
        )

    async def get_interpretation(
        self, chart: dict, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        """
        Get LLM interpretation of the chart using Claude.

        Args:
            chart: The calculated chart data
            request: The original query request (for access_key)

        Yields:
            PartialResponse chunks from the LLM
        """
        prompt = self.build_interpretation_prompt(chart)

        # Create a new request with the interpretation prompt
        # We need to create a new QueryRequest with just the prompt
        new_request = fp.QueryRequest(
            version=request.version,
            type=request.type,
            query=[fp.ProtocolMessage(role="user", content=prompt)],
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            access_key=request.access_key,
        )

        # Stream from Claude
        try:
            async for msg in fp.stream_request(
                new_request,
                poe_model,
                request.access_key,
            ):
                yield msg
        except Exception as e:
            yield fp.PartialResponse(
                text=f"\n\n*[Error getting interpretation: {str(e)}]*"
            )

    async def get_follow_up_response(
        self, chart_data: dict, question: str, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        """
        Handle follow-up questions about a chart.

        Args:
            chart_data: The chart context
            question: The follow-up question
            request: The original query request

        Yields:
            PartialResponse chunks from the LLM
        """
        prompt = f"""You are an expert Western astrologer. The user has asked a follow-up question about their natal chart.

Chart Data:
{json.dumps(chart_data, indent=2)}

User's Question: {question}

Provide a thoughtful, specific answer based on the chart data. Be warm and insightful while staying grounded in the actual astrological placements."""

        # Create a new request with the follow-up prompt
        new_request = fp.QueryRequest(
            version=request.version,
            type=request.type,
            query=[fp.ProtocolMessage(role="user", content=prompt)],
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            access_key=request.access_key,
        )

        try:
            async for msg in fp.stream_request(
                new_request,
                poe_model,
                request.access_key,
            ):
                yield msg
        except Exception as e:
            yield fp.PartialResponse(text=f"\n\n*[Error: {str(e)}]*")

    def build_interpretation_prompt(self, chart: dict) -> str:
        """
        Build the interpretation prompt for the LLM.

        Args:
            chart: The calculated chart data

        Returns:
            Formatted prompt string
        """
        # Format planets section
        planets_text = "\n".join(
            [
                f"  • {name}: {data['sign']} at {data['degree']}°"
                for name, data in chart["planets"].items()
            ]
        )

        # Format houses section
        houses_text = "\n".join(
            [
                f"  • {house}: {data['sign']} at {data['degree']}°"
                for house, data in chart["houses"].items()
            ]
        )

        # Format aspects section (top 10 by tightest orb)
        aspects = chart.get("aspects", [])
        aspects_sorted = sorted(aspects, key=lambda x: x["orb"])[:10]
        aspects_text = "\n".join(
            [
                f"  • {a['planet1']} {a['aspect']} {a['planet2']} (orb: {a['orb']}°)"
                for a in aspects_sorted
            ]
        )

        # Check for transits
        transits_text = ""
        if "transits" in chart:
            transits = chart["transits"]
            transit_aspects = transits.get("transit_aspects", [])
            transits_sorted = sorted(transit_aspects, key=lambda x: x["orb"])[:5]
            transits_text = "\n\n**Current Transits:**\n" + "\n".join(
                [
                    f"  • {t['transit_planet']} {t['aspect']} your {t['natal_planet']} (orb: {t['orb']}°)"
                    for t in transits_sorted
                ]
            )

        return f"""You are an expert Western astrologer with deep knowledge of natal chart interpretation. Provide a warm, nuanced, psychologically insightful reading.

**Birth Information:**
• Date: {chart["meta"]["date"]}
• Time: {chart["meta"]["time"]}
• Location: {chart["meta"]["city"]}

**Key Placements:**
• Sun Sign: {chart["planets"]["Sun"]["sign"]}
• Moon Sign: {chart["planets"]["Moon"]["sign"]}
• Ascendant (Rising): {chart["ascendant"]["sign"]}
• Midheaven: {chart["midheaven"]["sign"]}

**All Planetary Positions:**
{planets_text}

**House Cusps:**
{houses_text}

**Major Aspects (top 10):**
{aspects_text}{transits_text}

**Instructions:**
Provide a structured reading covering:
1. **The Big Three** - Brief overview of Sun, Moon, and Rising combination
2. **Sun Placement** - Core identity, vitality, life purpose
3. **Moon Placement** - Emotional nature, needs, instincts
4. **Ascendant** - Outer personality, first impressions, approach to life
5. **Key Planetary Placements** - Mercury, Venus, Mars, and any notable placements
6. **Major Aspects** - Interpret the most significant aspects (tightest orbs)
7. **House Emphases** - Any notable house patterns

Be specific to these exact placements. Avoid generic filler. Use warm, accessible language while maintaining astrological depth. Format with clear headers using **bold**."""


# Modal deployment configuration
REQUIREMENTS = [
    "fastapi-poe>=0.0.46",
    "pyswisseph>=2.10.0",
    "timezonefinder>=6.2.0",
    "geopy>=2.4.0",
]

# Include ephemeris files in the image
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .env(
        {
            "PYTHONPATH": "/root",
            "SE_EPHE_PATH": "/app/ephe",
        }
    )
    .add_local_file("chart_engine.py", "/root/chart_engine.py")
    .add_local_dir("ephe", "/app/ephe")
)

if bot_access_key:
    image = image.env({"POE_ACCESS_KEY": bot_access_key})
if bot_name:
    image = image.env({"POE_BOT_NAME": bot_name})
if poe_model != "Kimi-K2.5":
    image = image.env({"POE_MODEL": poe_model})

app = App("astrology-bot-poe")


@app.function(image=image)
@asgi_app()
def fastapi_app():
    bot = AstrologyBot()
    poe_app = fp.make_app(
        bot,
        access_key=bot_access_key,
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name),
    )
    return poe_app

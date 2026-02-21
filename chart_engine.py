"""

Chart calculation engine using Swiss Ephemeris.

This module handles all astrological calculations including:
- Planet positions
- House calculations (Placidus system)
- Aspect calculations
- Geocoding and timezone resolution

"""

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Tuple, Any

import os
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Set ephemeris path if available
_ephe_path = os.path.join(os.path.dirname(__file__), "ephe")
if os.path.exists(_ephe_path):
    swe.set_ephe_path(_ephe_path)


# Planet mapping to Swiss Ephemeris IDs
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "North Node": swe.MEAN_NODE,
    "Chiron": swe.CHIRON,
}

# Zodiac signs in order
SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

# Aspect definitions: (name, angle, orb)
ASPECT_DEFINITIONS = [
    ("conjunction", 0, 8),
    ("sextile", 60, 6),
    ("square", 90, 7),
    ("trine", 120, 8),
    ("opposition", 180, 8),
]

# House system codes for Swiss Ephemeris
HOUSE_SYSTEMS = {
    "placidus": b"P",
    "koch": b"K",
    "whole_sign": b"W",
    "equal": b"E",
    "regiomontanus": b"R",
    "campanus": b"C",
    "porphyry": b"O",
    "morinus": b"M",
}

# Sidereal modes for Swiss Ephemeris
SIDEREAL_MODES = {
    "fagan_bradley": swe.SIDM_FAGAN_BRADLEY,
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "j2000": swe.SIDM_J2000,
    "jyotish": swe.SIDM_J2000,
}


def longitude_to_sign(longitude: float) -> Dict[str, Any]:
    """
    Convert longitude to zodiac sign position.

    Args:
        longitude: Longitude in degrees (0-360)

    Returns:
        Dict with sign name, degree in sign, and original longitude
    """
    sign_index = int(longitude // 30)
    degree = longitude % 30
    return {
        "sign": SIGNS[sign_index],
        "degree": round(degree, 2),
        "longitude": round(longitude, 4),
    }


def geocode_city(city: str) -> Tuple[float, float, str]:
    """
    Geocode a city name to coordinates and timezone.

    Args:
        city: City name (e.g., "Austin, TX" or "Paris, France")

    Returns:
        Tuple of (latitude, longitude, timezone_name)

    Raises:
        ValueError: If city cannot be geocoded
    """
    import inspect
    from geopy.adapters import URLLibAdapter
    from geopy.geocoders import Nominatim

    # Use URLLibAdapter to ensure synchronous operation
    geolocator = Nominatim(
        user_agent="astro-poe-bot",
        adapter_factory=URLLibAdapter,
    )
    location = geolocator.geocode(city)

    # Handle potential coroutine
    if inspect.isawaitable(location):
        raise RuntimeError(
            "Geocoding returned a coroutine. Expected synchronous result."
        )

    if not location:
        raise ValueError(f"Could not geocode city: {city}")

    tf = TimezoneFinder()
    timezone = tf.timezone_at(lat=location.latitude, lng=location.longitude)

    if not timezone:
        raise ValueError(f"Could not determine timezone for: {city}")

    return location.latitude, location.longitude, timezone


def to_julian_day(dt: datetime) -> float:
    """
    Convert datetime to Julian Day.

    Args:
        dt: Datetime object

    Returns:
        Julian Day number
    """
    return swe.julday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour + dt.minute / 60.0 + dt.second / 3600.0,
    )


def calculate_planets(
    jd: float, sidereal_mode: int | None = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate positions of all planets.

    Args:
        jd: Julian Day
        sidereal_mode: Optional sidereal mode constant from swe

    Returns:
        Dict mapping planet names to their positions
    """
    planets = {}

    flags = 0
    if sidereal_mode is not None:
        swe.set_sid_mode(sidereal_mode)
        flags = swe.FLG_SIDEREAL

    for name, planet_id in PLANETS.items():
        result, _ = swe.calc_ut(jd, planet_id, flags)
        planets[name] = longitude_to_sign(result[0])

    return planets


def calculate_houses(
    jd: float,
    lat: float,
    lon: float,
    house_system: bytes = b"P",
    sidereal_mode: int | None = None,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    """
    Calculate house cusps.

    Args:
        jd: Julian Day
        lat: Latitude
        lon: Longitude
        house_system: House system code (default: Placidus b"P")
        sidereal_mode: Optional sidereal mode constant from swe

    Returns:
        Tuple of (houses_dict, ascendant, midheaven)
    """
    flags = 0
    if sidereal_mode is not None:
        swe.set_sid_mode(sidereal_mode)
        flags = swe.FLG_SIDEREAL

    houses, ascmc = swe.houses_ex(jd, lat, lon, house_system, flags)

    # House cusps (12 houses)
    house_cusps = {f"House {i + 1}": longitude_to_sign(h) for i, h in enumerate(houses)}

    # Ascendant is ascmc[0], Midheaven is ascmc[1]
    ascendant = longitude_to_sign(ascmc[0])
    midheaven = longitude_to_sign(ascmc[1])

    return house_cusps, ascendant, midheaven


def calculate_aspects(planets: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate aspects between planets.

    Args:
        planets: Dict of planet positions

    Returns:
        List of aspect dictionaries
    """
    aspects = []
    planet_names = list(planets.keys())

    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i + 1 :]:
            lon1 = planets[p1]["longitude"]
            lon2 = planets[p2]["longitude"]

            # Calculate angular difference
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            # Check for aspects
            for aspect_name, angle, orb in ASPECT_DEFINITIONS:
                if abs(diff - angle) <= orb:
                    aspects.append(
                        {
                            "planet1": p1,
                            "planet2": p2,
                            "aspect": aspect_name,
                            "angle": angle,
                            "orb": round(abs(diff - angle), 2),
                        }
                    )

    return aspects


def calculate_chart(
    date: str,
    time: str,
    city: str,
    house_system: str = "placidus",
    zodiac_type: str = "tropical",
    sidereal_mode: str = "lahiri",
) -> Dict[str, Any]:
    """
    Calculate a complete natal chart.

    Args:
        date: Date string in format "YYYY-MM-DD"
        time: Time string in format "HH:MM" (24-hour)
        city: City name for geocoding
        house_system: House system name (placidus, koch, whole_sign, equal, etc.)
        zodiac_type: "tropical" or "sidereal"
        sidereal_mode: Sidereal ayanamsa mode (lahiri, fagan_bradley, raman, etc.)

    Returns:
        Complete chart data including planets, houses, aspects, and metadata

    Raises:
        ValueError: If date/time format is invalid or city cannot be geocoded
    """
    # Geocode the city
    lat, lon, tz_name = geocode_city(city)

    # Parse date and time with timezone
    local_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(tz_name)
    )

    # Convert to UTC for calculations
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    # Convert to Julian Day
    jd = to_julian_day(utc_dt)

    # Determine sidereal mode
    sid_mode = None
    if zodiac_type == "sidereal":
        sid_mode = SIDEREAL_MODES.get(sidereal_mode, swe.SIDM_LAHIRI)

    # Get house system code
    house_sys_code = HOUSE_SYSTEMS.get(house_system, b"P")

    # Calculate chart components
    planets = calculate_planets(jd, sid_mode)
    houses, ascendant, midheaven = calculate_houses(
        jd, lat, lon, house_sys_code, sid_mode
    )
    aspects = calculate_aspects(planets)

    return {
        "planets": planets,
        "houses": houses,
        "ascendant": ascendant,
        "midheaven": midheaven,
        "aspects": aspects,
        "meta": {
            "date": date,
            "time": time,
            "city": city,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "timezone": tz_name,
            "utc_datetime": utc_dt.isoformat(),
            "julian_day": jd,
            "house_system": house_system,
            "zodiac_type": zodiac_type,
            "sidereal_mode": sidereal_mode if zodiac_type == "sidereal" else None,
        },
    }


def calculate_transits(
    natal_chart: Dict[str, Any], transit_date: str, transit_time: str = "12:00"
) -> Dict[str, Any]:
    """
    Calculate transit positions for a given date.

    Args:
        natal_chart: The natal chart to compare against
        transit_date: Date string in format "YYYY-MM-DD"
        transit_time: Time string in format "HH:MM"

    Returns:
        Transit chart data with natal comparison
    """
    # Use natal chart location for transits
    lat = natal_chart["meta"]["latitude"]
    lon = natal_chart["meta"]["longitude"]
    tz_name = natal_chart["meta"]["timezone"]

    # Parse transit datetime
    local_dt = datetime.strptime(
        f"{transit_date} {transit_time}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    jd = to_julian_day(utc_dt)

    # Calculate transit planet positions
    transit_planets = calculate_planets(jd)

    # Calculate transits to natal planets
    transit_aspects = []
    for transit_name, transit_data in transit_planets.items():
        for natal_name, natal_data in natal_chart["planets"].items():
            lon1 = transit_data["longitude"]
            lon2 = natal_data["longitude"]

            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            # Check for aspects (slightly wider orbs for transits)
            for aspect_name, angle, orb in ASPECT_DEFINITIONS:
                if abs(diff - angle) <= orb:
                    transit_aspects.append(
                        {
                            "transit_planet": transit_name,
                            "natal_planet": natal_name,
                            "aspect": aspect_name,
                            "angle": angle,
                            "orb": round(abs(diff - angle), 2),
                        }
                    )

    return {
        "transit_planets": transit_planets,
        "transit_aspects": transit_aspects,
        "meta": {
            "date": transit_date,
            "time": transit_time,
            "timezone": tz_name,
            "julian_day": jd,
        },
    }


# Test function for local development
if __name__ == "__main__":
    # Test with a sample chart
    test_chart = calculate_chart(date="1990-03-15", time="14:30", city="Austin, TX")

    import json

    print("Natal Chart Test:")
    print(json.dumps(test_chart, indent=2))

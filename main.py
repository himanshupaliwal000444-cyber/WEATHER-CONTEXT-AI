"""
Weather Context AI — FastAPI Backend (Enhanced)
================================================
Hybrid architecture:
- Rule-based alerts for immediate deterministic safety (health, farming, lifestyle)
- Google Gemini LLM for synthesis advisory and interactive weather chat assistant
- SQLite cache for fast responses and API savings
"""

import os
import time
import json
import sqlite3
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai

# ──────────────────────────────────────────────
#  Configuration & Initialization
# ──────────────────────────────────────────────
load_dotenv()

WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
GEMINI_MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"]

CACHE_TTL_SECONDS = 30 * 60  # 30 minutes
DB_PATH = Path(__file__).parent / "cache.db"

# Initialize Google GenAI client if key is available
genai_client: Optional[genai.Client] = None
if GEMINI_API_KEY:
    try:
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to init GenAI client: {e}")

# ──────────────────────────────────────────────
#  SQLite Cache Helpers
# ──────────────────────────────────────────────
def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_cache (
            cache_key  TEXT PRIMARY KEY,
            response   TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def cache_get(key: str) -> Optional[str]:
    conn = _get_db()
    row = conn.execute(
        "SELECT response, created_at FROM llm_cache WHERE cache_key = ?", (key,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    response, created_at = row
    if time.time() - created_at > CACHE_TTL_SECONDS:
        conn2 = _get_db()
        conn2.execute("DELETE FROM llm_cache WHERE cache_key = ?", (key,))
        conn2.commit()
        conn2.close()
        return None
    return response


def cache_set(key: str, response: str) -> None:
    conn = _get_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO llm_cache (cache_key, response, created_at)
        VALUES (?, ?, ?)
        """,
        (key, response, time.time()),
    )
    conn.commit()
    conn.close()


def make_cache_key(identifier: str) -> str:
    norm = identifier.strip().lower()
    return hashlib.md5(norm.encode()).hexdigest()


# ──────────────────────────────────────────────
#  Deterministic Rule Engine
# ──────────────────────────────────────────────
def run_rule_engine(weather: dict) -> list[dict]:
    alerts: list[dict] = []

    current = weather.get("current", {})
    forecast_day = {}
    if weather.get("forecast", {}).get("forecastday"):
        forecast_day = weather["forecast"]["forecastday"][0].get("day", {})

    # Air Quality rules
    aqi_data = current.get("air_quality", {})
    us_epa = aqi_data.get("us-epa-index", 0)
    pm25 = aqi_data.get("pm2_5", 0)
    pm10 = aqi_data.get("pm10", 0)

    if us_epa >= 5:
        alerts.append({
            "type": "warning",
            "category": "health",
            "icon": "☣️",
            "title": "Hazardous Air Pollution",
            "message": f"Hazardous air quality (EPA Index {us_epa}). Stay indoors. High-efficiency N95 masks mandatory outdoors.",
        })
    elif us_epa >= 4:
        alerts.append({
            "type": "warning",
            "category": "health",
            "icon": "😷",
            "title": "Very Unhealthy Air",
            "message": f"Very unhealthy air (EPA Index {us_epa}). Wear an N95 mask outside and avoid outdoor cardio/exercise.",
        })
    elif us_epa >= 3:
        alerts.append({
            "type": "caution",
            "category": "health",
            "icon": "⚠️",
            "title": "Unhealthy for Sensitive Groups",
            "message": f"Unhealthy air quality (EPA Index {us_epa}). Asthmatic individuals and elders should limit outdoor stay.",
        })
    elif us_epa >= 2:
        alerts.append({
            "type": "info",
            "category": "health",
            "icon": "💨",
            "title": "Moderate Air Quality",
            "message": "Moderate air quality. Sensitive people should watch for irritation during prolonged exertion.",
        })

    if pm25 > 35:
        alerts.append({
            "type": "caution",
            "category": "health",
            "icon": "🫁",
            "title": "Elevated PM2.5",
            "message": f"Fine particulate PM2.5 is high at {pm25:.1f} µg/m³. Close windows during peak traffic hours.",
        })

    # UV Index
    uv = current.get("uv", 0)
    if uv >= 11:
        alerts.append({
            "type": "warning",
            "category": "health",
            "icon": "☀️",
            "title": "Extreme Solar Radiation",
            "message": f"Extreme UV index ({uv}). Stay shaded between 10 AM – 4 PM. Apply SPF 50+ sunscreen.",
        })
    elif uv >= 8:
        alerts.append({
            "type": "caution",
            "category": "health",
            "icon": "🧴",
            "title": "Very High UV",
            "message": f"Very high UV index ({uv}). Wear protective hat, UV-blocking sunglasses, and SPF 30+ sunscreen.",
        })
    elif uv >= 6:
        alerts.append({
            "type": "info",
            "category": "lifestyle",
            "icon": "🕶️",
            "title": "High UV Levels",
            "message": f"High UV index ({uv}). Sun protection recommended for outdoor activities.",
        })

    # Temperature
    temp_c = current.get("temp_c", 20)
    feelslike_c = current.get("feelslike_c", temp_c)

    if temp_c >= 42:
        alerts.append({
            "type": "warning",
            "category": "health",
            "icon": "🔥",
            "title": "Extreme Heatwave",
            "message": f"Extreme heat alert ({temp_c}°C, feels like {feelslike_c}°C). Heat exhaustion & stroke danger. Hydrate with electrolytes.",
        })
    elif temp_c >= 38:
        alerts.append({
            "type": "caution",
            "category": "health",
            "icon": "🌡️",
            "title": "Intense Heat",
            "message": f"Very hot conditions ({temp_c}°C). Drink water frequently and avoid heavy midday manual labor.",
        })
    elif temp_c <= 0:
        alerts.append({
            "type": "warning",
            "category": "lifestyle",
            "icon": "🥶",
            "title": "Freezing Freeze Warning",
            "message": f"Freezing temperatures ({temp_c}°C). Black ice danger on roads. Wear thermal insulated layers.",
        })
    elif temp_c <= 5:
        alerts.append({
            "type": "caution",
            "category": "lifestyle",
            "icon": "🧥",
            "title": "Chilly Weather",
            "message": f"Cold weather ({temp_c}°C, feels like {feelslike_c}°C). Wear warm woolen layers when commuting.",
        })

    # Rain & Precipitation
    rain_chance = forecast_day.get("daily_chance_of_rain", 0)
    rain_mm = forecast_day.get("totalprecip_mm", 0)

    if rain_chance > 80:
        alerts.append({
            "type": "warning",
            "category": "lifestyle",
            "icon": "🌧️",
            "title": "Heavy Downpour Expected",
            "message": f"Heavy rain virtually guaranteed ({rain_chance}% chance, ~{rain_mm:.1f} mm). Carry umbrellas and expect transit delays.",
        })
    elif rain_chance > 50:
        alerts.append({
            "type": "caution",
            "category": "lifestyle",
            "icon": "🌂",
            "title": "Rain Shower Alert",
            "message": f"Precipitation likely today ({rain_chance}% chance). Keep waterproof rainwear handy.",
        })

    # Agriculture: Pesticide & Spraying
    wind_kph = current.get("wind_kph", 0)
    humidity = current.get("humidity", 0)

    if rain_chance > 60:
        alerts.append({
            "type": "warning",
            "category": "agriculture",
            "icon": "🚫",
            "title": "Cancel Chemical Spraying",
            "message": f"Postpone pesticide and fertilizer spraying — high rain probability ({rain_chance}%). Rain will wash chemicals into soil runoff.",
        })
    elif wind_kph > 25:
        alerts.append({
            "type": "caution",
            "category": "agriculture",
            "icon": "💨",
            "title": "Chemical Drift Risk",
            "message": f"Gusty winds ({wind_kph:.0f} km/h). Delay spray application to prevent toxic chemical drift to unintended fields.",
        })
    else:
        if rain_chance < 30 and wind_kph < 15:
            alerts.append({
                "type": "info",
                "category": "agriculture",
                "icon": "🌱",
                "title": "Optimal Spray Window",
                "message": "Favorable spraying conditions: Low precipitation risk and gentle wind velocity.",
            })

    # Agriculture: Irrigation
    if humidity < 30 and rain_chance < 20:
        alerts.append({
            "type": "caution",
            "category": "agriculture",
            "icon": "💧",
            "title": "Dry Soil / Irrigate Needed",
            "message": f"Low relative humidity ({humidity}%) with zero rain forecast. Soil moisture evapotranspiration is rapid — irrigate crops.",
        })
    elif rain_mm > 15:
        alerts.append({
            "type": "info",
            "category": "agriculture",
            "icon": "🌾",
            "title": "Skip Irrigation",
            "message": f"Natural precipitation adequate (~{rain_mm:.0f} mm). Turn off electric tube-wells and drip systems to conserve energy.",
        })

    # Agriculture: Frost
    min_temp = forecast_day.get("mintemp_c", temp_c)
    if min_temp <= 2:
        alerts.append({
            "type": "warning",
            "category": "agriculture",
            "icon": "❄️",
            "title": "Frost & Crop Cold Damage",
            "message": f"Frost risk tonight (low of {min_temp}°C). Cover horticultural nurseries or smoke orchards to prevent freeze burn.",
        })

    # Lifestyle: Wind & Visibility
    if wind_kph > 50:
        alerts.append({
            "type": "warning",
            "category": "lifestyle",
            "icon": "🌪️",
            "title": "High Wind Hazard",
            "message": f"Gale-force gusts ({wind_kph:.0f} km/h). Anchor loose patio equipment. Watch for falling tree branches.",
        })
    elif wind_kph > 30:
        alerts.append({
            "type": "caution",
            "category": "lifestyle",
            "icon": "🌬️",
            "title": "Breezy Conditions",
            "message": f"Strong breeze ({wind_kph:.0f} km/h). Two-wheeler riders should exercise caution on highways.",
        })

    vis_km = current.get("vis_km", 10)
    if vis_km < 1:
        alerts.append({
            "type": "warning",
            "category": "lifestyle",
            "icon": "🌫️",
            "title": "Dense Fog / Low Visibility",
            "message": f"Critical low visibility ({vis_km} km). Turn on amber fog lights and reduce driving speeds drastically.",
        })
    elif vis_km < 4:
        alerts.append({
            "type": "caution",
            "category": "lifestyle",
            "icon": "🌁",
            "title": "Hazy Visibility",
            "message": f"Moderate haze ({vis_km} km visibility). Keep low-beam headlights active.",
        })

    return alerts


# ──────────────────────────────────────────────
#  Gemini AI Calling Helpers
# ──────────────────────────────────────────────
def call_gemini(prompt: str) -> str:
    """Helper to query Gemini using the latest available flash models with fallback."""
    if not genai_client:
        return "AI advisory unavailable: Gemini API key not configured."

    last_error = None
    for model_name in GEMINI_MODELS:
        try:
            response = genai_client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            last_error = e
            continue

    return f"AI advisory temporarily unavailable ({type(last_error).__name__ if last_error else 'Unknown'})."


async def generate_ai_advisory(weather: dict, location_name: str) -> str:
    current = weather.get("current", {})
    forecast_day = {}
    if weather.get("forecast", {}).get("forecastday"):
        forecast_day = weather["forecast"]["forecastday"][0].get("day", {})
    aqi = current.get("air_quality", {})

    data_summary = (
        f"Location: {location_name}\n"
        f"Temperature: {current.get('temp_c')}°C (feels like {current.get('feelslike_c')}°C)\n"
        f"Weather Condition: {current.get('condition', {}).get('text')}\n"
        f"Humidity: {current.get('humidity')}%\n"
        f"Wind: {current.get('wind_kph')} km/h ({current.get('wind_dir')})\n"
        f"UV Index: {current.get('uv')}\n"
        f"Air Quality (US EPA Index): {aqi.get('us-epa-index')} | PM2.5: {aqi.get('pm2_5')} | PM10: {aqi.get('pm10')}\n"
        f"Rain Chance: {forecast_day.get('daily_chance_of_rain')}%\n"
        f"Expected Rainfall: {forecast_day.get('totalprecip_mm')} mm\n"
        f"High: {forecast_day.get('maxtemp_c')}°C, Low: {forecast_day.get('mintemp_c')}°C\n"
    )

    prompt = (
        "You are an expert AI meteorological advisor specializing in Health, Agriculture, and Lifestyle.\n"
        "Analyze the following weather metrics and write an engaging, high-value 2-sentence qualitative advisory:\n"
        "- Sentence 1: Practical health & agricultural guidance (air quality precautions, crop spraying/irrigation timing).\n"
        "- Sentence 2: Daily lifestyle & clothing recommendation (what to wear, commuting safety, outdoor activity feasibility).\n"
        "Format: Exactly two concise, punchy sentences. Include relevant emojis.\n\n"
        f"--- METRICS ---\n{data_summary}\n--- END METRICS ---"
    )

    return call_gemini(prompt)


# ──────────────────────────────────────────────
#  FastAPI App
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_db()
    yield

app = FastAPI(
    title="Weather Context AI",
    description="Intelligent AI-driven contextual weather analysis for Health, Agriculture & Lifestyle",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/weather")
async def get_weather(
    q: Optional[str] = Query(None, description="City name or 'lat,lon' string"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude"),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="Longitude"),
):
    if not WEATHERAPI_KEY:
        raise HTTPException(status_code=500, detail="WEATHERAPI_KEY not configured in .env.")

    # Determine query string for WeatherAPI
    if q and q.strip():
        query_val = q.strip()
    elif lat is not None and lon is not None:
        query_val = f"{lat},{lon}"
    else:
        raise HTTPException(status_code=400, detail="Please provide either 'q' (city name) or 'lat' and 'lon'.")

    # Fetch from WeatherAPI
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(
                f"{WEATHERAPI_BASE}/forecast.json",
                params={
                    "key": WEATHERAPI_KEY,
                    "q": query_val,
                    "days": 1,
                    "aqi": "yes",
                    "alerts": "no",
                },
            )
            if resp.status_code == 400:
                raise HTTPException(status_code=404, detail="Location not found. Please try another city.")
            resp.raise_for_status()
            weather = resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather service error: {str(e)}")

    # Deterministic Rule Engine
    alerts = run_rule_engine(weather)

    # Cache & AI Advisory
    loc_name = weather.get("location", {}).get("name", query_val)
    country = weather.get("location", {}).get("country", "")
    cache_key = make_cache_key(f"{loc_name}:{country}")

    ai_text = cache_get(cache_key)
    if not ai_text:
        ai_text = await generate_ai_advisory(weather, f"{loc_name}, {country}")
        if not ai_text.startswith("AI advisory temporarily unavailable"):
            cache_set(cache_key, ai_text)

    # Build response
    current = weather.get("current", {})
    location = weather.get("location", {})
    forecast_day = {}
    if weather.get("forecast", {}).get("forecastday"):
        forecast_day = weather["forecast"]["forecastday"][0].get("day", {})
    aqi_data = current.get("air_quality", {})

    return {
        "location": {
            "name": location.get("name", ""),
            "region": location.get("region", ""),
            "country": location.get("country", ""),
            "localtime": location.get("localtime", ""),
            "lat": location.get("lat"),
            "lon": location.get("lon"),
        },
        "current": {
            "temp_c": current.get("temp_c"),
            "feelslike_c": current.get("feelslike_c"),
            "condition": current.get("condition", {}).get("text", ""),
            "condition_icon": current.get("condition", {}).get("icon", ""),
            "humidity": current.get("humidity"),
            "wind_kph": current.get("wind_kph"),
            "wind_dir": current.get("wind_dir", ""),
            "uv": current.get("uv"),
            "vis_km": current.get("vis_km"),
            "pressure_mb": current.get("pressure_mb"),
        },
        "air_quality": {
            "us_epa_index": aqi_data.get("us-epa-index", 1),
            "pm2_5": round(aqi_data.get("pm2_5", 0), 1),
            "pm10": round(aqi_data.get("pm10", 0), 1),
            "co": round(aqi_data.get("co", 0), 1),
            "no2": round(aqi_data.get("no2", 0), 1),
            "o3": round(aqi_data.get("o3", 0), 1),
        },
        "forecast": {
            "maxtemp_c": forecast_day.get("maxtemp_c"),
            "mintemp_c": forecast_day.get("mintemp_c"),
            "rain_chance": forecast_day.get("daily_chance_of_rain", 0),
            "totalprecip_mm": forecast_day.get("totalprecip_mm", 0),
            "snow_chance": forecast_day.get("daily_chance_of_snow", 0),
            "avghumidity": forecast_day.get("avghumidity", 0),
        },
        "alerts": alerts,
        "ai_advisory": ai_text,
    }


# ──────────────────────────────────────────────
#  Interactive Weather AI Chat Endpoint
# ──────────────────────────────────────────────
class ChatMessage(BaseModel):
    message: str
    weather_context: Optional[dict] = None


@app.post("/api/chat")
async def chat_weather(payload: ChatMessage):
    """
    Real-time interactive chat with Aero the Weather AI.
    Answers user questions tailored to health, agriculture, and lifestyle
    with context from the currently viewed location.
    """
    user_msg = payload.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    ctx_str = "No specific location weather loaded yet."
    if payload.weather_context:
        ctx = payload.weather_context
        loc = ctx.get("location", {})
        cur = ctx.get("current", {})
        aqi = ctx.get("air_quality", {})
        fc = ctx.get("forecast", {})
        ctx_str = (
            f"Location: {loc.get('name')}, {loc.get('country')}\n"
            f"Temperature: {cur.get('temp_c')}°C (Feels: {cur.get('feelslike_c')}°C), Condition: {cur.get('condition')}\n"
            f"Humidity: {cur.get('humidity')}%, Wind: {cur.get('wind_kph')} km/h {cur.get('wind_dir')}, UV: {cur.get('uv')}\n"
            f"Air Quality: EPA Index {aqi.get('us_epa_index')}, PM2.5: {aqi.get('pm2_5')} µg/m³\n"
            f"Forecast: Rain Chance {fc.get('rain_chance')}%, High/Low: {fc.get('maxtemp_c')}°C / {fc.get('mintemp_c')}°C\n"
        )

    system_prompt = (
        "You are Aero, an intelligent, friendly AI Weather & Environmental Companion.\n"
        "Your mission is to provide helpful, actionable, scientific, and warm qualitative guidance for:\n"
        "1. Health & Wellness (asthma precautions, heatstroke prevention, UV safety, air pollution defense)\n"
        "2. Agriculture & Gardening (irrigation windows, pesticide spraying feasibility, frost protection)\n"
        "3. Daily Lifestyle & Commute (clothing advice, umbrella needs, road safety, exercise planning)\n\n"
        f"CURRENT REAL-TIME WEATHER CONTEXT:\n{ctx_str}\n\n"
        "Guidelines:\n"
        "- Answer the user's question directly, clearly, and concisely (2 to 4 sentences or bullet points).\n"
        "- Incorporate numbers from the context when relevant (e.g. mention the exact rain %, UV index, or AQI).\n"
        "- Use friendly emojis.\n\n"
        f"User Question: {user_msg}\n\n"
        "Aero's Response:"
    )

    answer = call_gemini(system_prompt)
    return {"reply": answer}


# ──────────────────────────────────────────────
#  Static File Serving
# ──────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))
